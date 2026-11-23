/**
 * @file ossm_central.h
 * BLE central (GATT client) for the app, built on the raw HCI access that the
 * flipper-ble-scanner firmware exports (furi_hal_bt_hci_command,
 * furi_hal_bt_start_scan) on top of ST's "Full" radio stack.
 *
 * On stock firmware (Light stack, peripheral only) ossm_central_is_supported()
 * returns false.
 *
 * Model: one outgoing connection at a time, alongside the Flipper's normal
 * peripheral role. Every call is asynchronous and must be made from an app
 * thread. Results arrive through the callback, which runs on the BLE event
 * thread: copy what you need and return quickly. Event data pointers are only
 * valid during the callback.
 *
 * Only one GATT procedure (discover, read, write with response, subscribe,
 * MTU exchange) can run at a time; each ends with
 * OssmCentralEventTypeProcComplete. Writes without response are not
 * procedures and can be sent at any time while connected.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    OssmCentralEventTypeAdvReport, /**< addr, addr_type, rssi, adv_type, data */
    OssmCentralEventTypeConnected, /**< conn_handle */
    OssmCentralEventTypeConnectFailed, /**< status */
    OssmCentralEventTypeDisconnected, /**< status = reason */
    OssmCentralEventTypeMtu, /**< handle = negotiated server RX MTU */
    OssmCentralEventTypeCharFound, /**< handle = value handle, properties */
    OssmCentralEventTypeNotification, /**< handle = attribute, data */
    OssmCentralEventTypeReadData, /**< data = next chunk of a (long) read */
    OssmCentralEventTypeGattError, /**< handle = attribute, status = ATT error */
    OssmCentralEventTypeProcComplete, /**< status = 0 on success */
} OssmCentralEventType;

typedef struct {
    OssmCentralEventType type;
    uint8_t addr[6];
    uint8_t addr_type;
    uint8_t adv_type;
    int8_t rssi;
    uint8_t status;
    uint8_t properties;
    uint16_t handle;
    uint8_t data_len;
    const uint8_t* data;
} OssmCentralEvent;

typedef void (*OssmCentralCallback)(const OssmCentralEvent* event, void* context);

/** True when the co-processor runs a stack with the central role. */
bool ossm_central_is_supported(void);

/** Start receiving events. Must be balanced with ossm_central_release(). */
bool ossm_central_acquire(OssmCentralCallback callback, void* context);

/** Stop scanning, drop the connection and stop receiving events. */
void ossm_central_release(void);

/** Start scanning. Active scanning also returns scan responses. */
bool ossm_central_scan_start(bool active);

void ossm_central_scan_stop(void);

/** Connect to a peer found while scanning. Stop the scan first. */
bool ossm_central_connect(const uint8_t addr[6], uint8_t addr_type);

void ossm_central_connect_cancel(void);

bool ossm_central_disconnect(void);

bool ossm_central_is_connected(void);

/** Signal strength of the current connection, in dBm. */
bool ossm_central_get_rssi(int8_t* rssi);

/** Ask for a bigger ATT MTU. Ends with Mtu then ProcComplete. */
bool ossm_central_exchange_mtu(void);

/** Find characteristics with a 128-bit UUID (little-endian, as on air).
 * Sends CharFound for each match, then ProcComplete. */
bool ossm_central_discover_char(const uint8_t uuid128[16]);

/** Read a value of any length. Sends ReadData chunks, then ProcComplete. */
bool ossm_central_read(uint16_t value_handle);

/** Write a value. With response it is a procedure (ProcComplete). Without
 * response it returns false when the TX pool is full: try again later. */
bool ossm_central_write(uint16_t value_handle, const uint8_t* data, uint8_t len, bool response);

/** Write the CCCD to turn notifications on or off. Ends with ProcComplete. */
bool ossm_central_subscribe(uint16_t cccd_handle, bool enable);

#ifdef __cplusplus
}
#endif
