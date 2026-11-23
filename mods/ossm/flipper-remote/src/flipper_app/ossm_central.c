// BLE central (GATT client) for the OSSM app, built only on what the
// flipper-ble-scanner firmware exports to apps:
//   furi_hal_bt_start_scan / furi_hal_bt_stop_scan   (observer role)
//   furi_hal_bt_hci_command                          (raw HCI / ACI commands)
//   ble_event_dispatcher_register_svc_handler        (raw HCI events)
// No firmware change of our own is needed.
//
// Commands are sent from the app thread only: hci_send_req waits for its own
// command status event, so calling it from the BLE event thread would hang.
// Events are parsed from raw bytes so the app needs no BLE stack headers.

#include "ossm_central.h"

#include <furi.h>
#include <furi_hal_bt.h>
#include <furi_ble/event_dispatcher.h>
#include <string.h>

#define TAG "OssmCentral"

// HCI opcodes: ogf << 10 | ocf. ACI vendor commands use ogf 0x3F.
#define OP_DISCONNECT          0x0406 // HCI Disconnect
#define OP_READ_RSSI           0x1405 // HCI Read RSSI
#define OP_CREATE_CONNECTION   0xFC9C // aci_gap_create_connection
#define OP_TERMINATE_GAP_PROC  0xFC9D // aci_gap_terminate_gap_proc
#define OP_EXCHANGE_CONFIG     0xFD0B // aci_gatt_exchange_config (MTU)
#define OP_DISC_CHAR_BY_UUID   0xFD16 // aci_gatt_disc_char_by_uuid
#define OP_READ_LONG_CHAR      0xFD1A // aci_gatt_read_long_char_value
#define OP_WRITE_CHAR_VALUE    0xFD1C // aci_gatt_write_char_value
#define OP_WRITE_CHAR_DESC     0xFD21 // aci_gatt_write_char_desc
#define OP_WRITE_WITHOUT_RESP  0xFD23 // aci_gatt_write_without_resp

#define GAP_DIRECT_CONNECTION_ESTABLISHMENT_PROC 0x40

// HCI events
#define EVT_DISCONNECTION_COMPLETE 0x05
#define EVT_LE_META                0x3E
#define EVT_VENDOR                 0xFF
#define SUBEVT_CONNECTION_COMPLETE 0x01
#define SUBEVT_ADVERTISING_REPORT  0x02
#define SUBEVT_ENH_CONN_COMPLETE   0x0A
#define ROLE_CENTRAL               0x00

// ACI vendor event codes (GATT client)
#define VS_GATT_PROC_TIMEOUT    0x0C02
#define VS_ATT_EXCHANGE_MTU     0x0C03
#define VS_ATT_READ_RESP        0x0C07
#define VS_ATT_READ_BLOB_RESP   0x0C08
#define VS_GATT_NOTIFICATION    0x0C0F
#define VS_GATT_PROC_COMPLETE   0x0C10
#define VS_GATT_ERROR_RESP      0x0C11
#define VS_GATT_DISC_CHAR_UUID  0x0C12

#define BLE_STATUS_OK 0x00

// 0.625 ms units
#define SCAN_INTERVAL 0x0050 // 50 ms
#define SCAN_WINDOW   0x0030 // 30 ms
// 1.25 ms units
#define CONN_INTERVAL_MIN 24 // 30 ms
#define CONN_INTERVAL_MAX 40 // 50 ms
// 10 ms units
#define SUPERVISION_TIMEOUT 400 // 4 s

typedef struct {
    GapSvcEventHandler* handler;
    OssmCentralCallback callback;
    void* context;
    volatile bool scanning;
    volatile bool connecting;
    volatile bool connected;
    volatile uint16_t conn_handle;
} OssmCentral;

static OssmCentral central;

static inline uint16_t rd16(const uint8_t* p) {
    return p[0] | (p[1] << 8);
}

static inline void wr16(uint8_t* p, uint16_t v) {
    p[0] = v & 0xFF;
    p[1] = v >> 8;
}

static void emit(OssmCentralEvent* event) {
    if(central.callback) central.callback(event, central.context);
}

static bool hci(uint16_t opcode, const void* params, uint8_t len) {
    uint8_t status = furi_hal_bt_hci_command(opcode, params, len, NULL, 0);
    if(status != BLE_STATUS_OK) FURI_LOG_D(TAG, "cmd %04X -> %02X", opcode, status);
    return status == BLE_STATUS_OK;
}

// LE Advertising Report: Num_Reports, then for each report
// Event_Type, Address_Type, Address[6], Length, Data[Length], RSSI.
static void handle_adv_report(const uint8_t* p, uint8_t total_len) {
    uint8_t num = p[0];
    size_t off = 1;
    for(uint8_t i = 0; i < num; i++) {
        if(off + 9 > total_len) return;
        OssmCentralEvent event = {.type = OssmCentralEventTypeAdvReport};
        event.adv_type = p[off];
        event.addr_type = p[off + 1];
        memcpy(event.addr, &p[off + 2], 6);
        event.data_len = p[off + 8];
        if(off + 9 + event.data_len + 1 > total_len) return;
        event.data = &p[off + 9];
        event.rssi = (int8_t)p[off + 9 + event.data_len];
        off += 10 + event.data_len;
        emit(&event);
    }
}

static BleEventAckStatus central_event_handler(void* packet, void* context) {
    UNUSED(context);
    // hci_uart_pckt: type(1), then hci_event_pckt: evt(1), plen(1), data[plen]
    const uint8_t* raw = packet;
    const uint8_t evt = raw[1];
    const uint8_t plen = raw[2];
    const uint8_t* d = &raw[3];

    switch(evt) {
    case EVT_DISCONNECTION_COMPLETE: {
        // Status(1) Connection_Handle(2) Reason(1)
        if(plen < 4) break;
        if(central.connected && rd16(&d[1]) == central.conn_handle) {
            central.connected = false;
            OssmCentralEvent event = {.type = OssmCentralEventTypeDisconnected, .status = d[3]};
            emit(&event);
            return BleEventAckFlowEnable; // not the phone link: keep it from gap
        }
    } break;

    case EVT_LE_META: {
        if(plen < 1) break;
        const uint8_t sub = d[0];
        const uint8_t* m = &d[1];
        if(sub == SUBEVT_ADVERTISING_REPORT) {
            if(central.scanning) {
                handle_adv_report(m, plen - 1);
                return BleEventAckFlowEnable;
            }
        } else if(sub == SUBEVT_CONNECTION_COMPLETE || sub == SUBEVT_ENH_CONN_COMPLETE) {
            // Status(1) Connection_Handle(2) Role(1) Peer_Address_Type(1) Peer_Address(6)
            if(plen < 12) break;
            const uint8_t status = m[0];
            if(status != 0) {
                // A failed connect is ours: gap.c would take it for a phone link.
                if(!central.connecting) break;
                central.connecting = false;
                OssmCentralEvent event = {
                    .type = OssmCentralEventTypeConnectFailed, .status = status};
                emit(&event);
                return BleEventAckFlowEnable;
            }
            if(m[3] != ROLE_CENTRAL) break; // someone connected to us
            central.connecting = false;
            central.conn_handle = rd16(&m[1]);
            central.connected = true;
            OssmCentralEvent event = {
                .type = OssmCentralEventTypeConnected,
                .handle = central.conn_handle,
                .addr_type = m[4],
            };
            memcpy(event.addr, &m[5], 6);
            emit(&event);
            return BleEventAckFlowEnable;
        } else if(central.connected && plen >= 3 && rd16(&m[1]) == central.conn_handle) {
            // Connection update, PHY update, data length change for our link.
            // Subevents 0x03, 0x07, 0x0C carry Status(1) then Connection_Handle.
            if(sub == 0x03 || sub == 0x07 || sub == 0x0C) return BleEventAckFlowEnable;
        }
    } break;

    case EVT_VENDOR: {
        if(plen < 4) break;
        const uint16_t ecode = rd16(&d[0]);
        const uint8_t* v = &d[2];
        const uint8_t vlen = plen - 2;
        // Every GATT client event starts with Connection_Handle.
        if((ecode & 0xFF00) != 0x0C00) break;
        if(!central.connected || rd16(&v[0]) != central.conn_handle) break;

        OssmCentralEvent event = {0};
        switch(ecode) {
        case VS_ATT_EXCHANGE_MTU: // conn(2) Server_RX_MTU(2)
            if(vlen < 4) return BleEventAckFlowEnable;
            event.type = OssmCentralEventTypeMtu;
            event.handle = rd16(&v[2]);
            break;
        case VS_GATT_DISC_CHAR_UUID: // conn(2) attr(2) len(1) Properties(1) Value_Handle(2) UUID
            if(vlen < 8 || v[4] < 3) return BleEventAckFlowEnable;
            event.type = OssmCentralEventTypeCharFound;
            event.properties = v[5];
            event.handle = rd16(&v[6]);
            break;
        case VS_GATT_NOTIFICATION: // conn(2) attr(2) len(1) value
            if(vlen < 5) return BleEventAckFlowEnable;
            event.type = OssmCentralEventTypeNotification;
            event.handle = rd16(&v[2]);
            event.data_len = MIN(v[4], vlen - 5);
            event.data = &v[5];
            break;
        case VS_ATT_READ_RESP:
        case VS_ATT_READ_BLOB_RESP: // conn(2) len(1) value
            if(vlen < 3) return BleEventAckFlowEnable;
            event.type = OssmCentralEventTypeReadData;
            event.data_len = MIN(v[2], vlen - 3);
            event.data = &v[3];
            break;
        case VS_GATT_ERROR_RESP: // conn(2) Req_Opcode(1) attr(2) Error_Code(1)
            if(vlen < 6) return BleEventAckFlowEnable;
            event.type = OssmCentralEventTypeGattError;
            event.handle = rd16(&v[3]);
            event.status = v[5];
            break;
        case VS_GATT_PROC_COMPLETE: // conn(2) Error_Code(1)
            event.type = OssmCentralEventTypeProcComplete;
            event.status = vlen >= 3 ? v[2] : 0;
            break;
        case VS_GATT_PROC_TIMEOUT:
            event.type = OssmCentralEventTypeProcComplete;
            event.status = 0xFF;
            break;
        default:
            return BleEventNotAck;
        }
        emit(&event);
        return BleEventAckFlowEnable;
    } break;

    default:
        break;
    }
    return BleEventNotAck;
}

bool ossm_central_is_supported(void) {
    return furi_hal_bt_is_alive() && furi_hal_bt_get_radio_stack() == FuriHalBtStackFull;
}

bool ossm_central_acquire(OssmCentralCallback callback, void* context) {
    furi_check(callback);
    if(!ossm_central_is_supported()) return false;
    if(central.handler) return false; // single user
    central.callback = callback;
    central.context = context;
    central.scanning = false;
    central.connecting = false;
    central.connected = false;
    central.handler = ble_event_dispatcher_register_svc_handler(central_event_handler, &central);
    return central.handler != NULL;
}

void ossm_central_release(void) {
    if(!central.handler) return;
    ossm_central_scan_stop();
    ossm_central_connect_cancel();
    if(central.connected) {
        ossm_central_disconnect();
        // Wait for the disconnection event before unregistering, or gap.c
        // takes it for the phone link going down.
        for(int i = 0; i < 100 && central.connected; i++)
            furi_delay_ms(10);
        central.connected = false;
    }
    ble_event_dispatcher_unregister_svc_handler(central.handler);
    central.handler = NULL;
    central.callback = NULL;
    central.context = NULL;
}

bool ossm_central_scan_start(bool active) {
    if(!central.handler || central.scanning) return false;
    central.scanning = true; // set first: reports can arrive before the call returns
    uint8_t status = furi_hal_bt_start_scan(SCAN_INTERVAL, SCAN_WINDOW, active);
    if(status != BLE_STATUS_OK) {
        FURI_LOG_E(TAG, "Scan start failed: %02X", status);
        central.scanning = false;
        return false;
    }
    return true;
}

void ossm_central_scan_stop(void) {
    if(!central.scanning) return;
    central.scanning = false;
    furi_hal_bt_stop_scan();
}

bool ossm_central_connect(const uint8_t addr[6], uint8_t addr_type) {
    if(!central.handler || central.connected || central.connecting) return false;
    uint8_t p[24];
    wr16(&p[0], SCAN_INTERVAL);
    wr16(&p[2], SCAN_WINDOW);
    p[4] = addr_type;
    memcpy(&p[5], addr, 6);
    p[11] = 0; // own address type: public
    wr16(&p[12], CONN_INTERVAL_MIN);
    wr16(&p[14], CONN_INTERVAL_MAX);
    wr16(&p[16], 0); // latency
    wr16(&p[18], SUPERVISION_TIMEOUT);
    wr16(&p[20], 0); // min CE length
    wr16(&p[22], 0); // max CE length
    central.connecting = true;
    if(!hci(OP_CREATE_CONNECTION, p, sizeof(p))) {
        central.connecting = false;
        return false;
    }
    return true;
}

void ossm_central_connect_cancel(void) {
    if(!central.connecting) return;
    central.connecting = false;
    uint8_t proc = GAP_DIRECT_CONNECTION_ESTABLISHMENT_PROC;
    hci(OP_TERMINATE_GAP_PROC, &proc, 1);
}

bool ossm_central_disconnect(void) {
    if(!central.connected) return false;
    uint8_t p[3];
    wr16(&p[0], central.conn_handle);
    p[2] = 0x13; // remote user terminated connection
    return hci(OP_DISCONNECT, p, sizeof(p));
}

bool ossm_central_is_connected(void) {
    return central.connected;
}

bool ossm_central_get_rssi(int8_t* rssi) {
    if(!central.connected) return false;
    uint8_t p[2];
    wr16(p, central.conn_handle);
    uint8_t resp[4] = {0}; // Status, Connection_Handle(2), RSSI
    if(furi_hal_bt_hci_command(OP_READ_RSSI, p, sizeof(p), resp, sizeof(resp)) != BLE_STATUS_OK)
        return false;
    *rssi = (int8_t)resp[3];
    return true;
}

bool ossm_central_exchange_mtu(void) {
    if(!central.connected) return false;
    uint8_t p[2];
    wr16(p, central.conn_handle);
    return hci(OP_EXCHANGE_CONFIG, p, sizeof(p));
}

bool ossm_central_discover_char(const uint8_t uuid128[16]) {
    if(!central.connected) return false;
    uint8_t p[23];
    wr16(&p[0], central.conn_handle);
    wr16(&p[2], 0x0001);
    wr16(&p[4], 0xFFFF);
    p[6] = 0x02; // 128-bit UUID
    memcpy(&p[7], uuid128, 16);
    return hci(OP_DISC_CHAR_BY_UUID, p, sizeof(p));
}

bool ossm_central_read(uint16_t value_handle) {
    if(!central.connected) return false;
    uint8_t p[6];
    wr16(&p[0], central.conn_handle);
    wr16(&p[2], value_handle);
    wr16(&p[4], 0); // offset
    return hci(OP_READ_LONG_CHAR, p, sizeof(p));
}

bool ossm_central_write(uint16_t value_handle, const uint8_t* data, uint8_t len, bool response) {
    if(!central.connected) return false;
    uint8_t p[5 + 244];
    if(len > sizeof(p) - 5) return false;
    wr16(&p[0], central.conn_handle);
    wr16(&p[2], value_handle);
    p[4] = len;
    memcpy(&p[5], data, len);
    return hci(response ? OP_WRITE_CHAR_VALUE : OP_WRITE_WITHOUT_RESP, p, 5 + len);
}

bool ossm_central_subscribe(uint16_t cccd_handle, bool enable) {
    if(!central.connected) return false;
    uint8_t p[7];
    wr16(&p[0], central.conn_handle);
    wr16(&p[2], cccd_handle);
    p[4] = 2;
    wr16(&p[5], enable ? 0x0001 : 0x0000);
    return hci(OP_WRITE_CHAR_DESC, p, sizeof(p));
}
