#pragma once
// Host-side stand-ins so the Flipper UI code can be rendered on a PC.
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#define UNUSED(x) (void)(x)
#define COUNT_OF(x) (sizeof(x) / sizeof((x)[0]))
typedef struct FuriMutex FuriMutex;
typedef struct FuriMessageQueue FuriMessageQueue;
typedef struct FuriTimer FuriTimer;
typedef struct FuriStreamBuffer FuriStreamBuffer;
typedef enum { FuriWaitForever = 0xFFFFFFFF } FuriWait;
extern uint32_t sim_tick;
static inline uint32_t furi_get_tick(void) { return sim_tick; }
static inline int furi_mutex_acquire(FuriMutex* m, uint32_t t) { (void)m; (void)t; return 0; }
static inline int furi_mutex_release(FuriMutex* m) { (void)m; return 0; }
size_t strlcpy(char* dst, const char* src, size_t size);
