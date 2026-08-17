#ifndef VEGA_BP_SHOP_RUNTIME_H
#define VEGA_BP_SHOP_RUNTIME_H

#include <stdint.h>

#define VEGA_BP_SHOP_VOLATILE_STATE_ADDRESS 0x0203ED40u
#define VEGA_BP_SHOP_VOLATILE_STATE_BYTES 128u
#define VEGA_BP_SHOP_ABI_VERSION 0xB927u

/* Script-visible results.  9 is shared with the established asynchronous host ABI. */
typedef enum BpShopResult {
    BP_SHOP_RESULT_SUCCESS = 0,
    BP_SHOP_RESULT_CANCELLED = 2,
    BP_SHOP_RESULT_LOCKED = 3,
    BP_SHOP_RESULT_INVALID_SELECTION = 5,
    BP_SHOP_RESULT_BUSY = 9,
    BP_SHOP_RESULT_PERSIST_FAILED = 13,
    BP_SHOP_RESULT_INSUFFICIENT_BP = 14,
    BP_SHOP_RESULT_BAG_FULL = 15,
    BP_SHOP_RESULT_ENGINE_REJECTED = 16
} BpShopResult;

uint16_t BpShop_Probe(void);
uint16_t BpShop_EnsureSave(void);
uint16_t BpShop_GetBalance(void);
uint16_t BpShop_IsItemUnlocked(uint16_t catalog_index);
uint16_t BpShop_PurchaseByIndex(uint16_t catalog_index);
uint16_t BpShop_PurchaseSelected(void);
uint16_t BpShop_Open(void);
void BpShop_PostMenu(void);

#endif /* VEGA_BP_SHOP_RUNTIME_H */
