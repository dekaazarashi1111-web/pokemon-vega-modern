#ifndef MODERNIZATION_MEGA_SHOP_H
#define MODERNIZATION_MEGA_SHOP_H

#include <stdint.h>

#define MODERNIZATION_MEGA_SHOP_ABI_VERSION 0xA168u
#define MODERNIZATION_MEGA_SHOP_ENTRY_COUNT 45u
#define MODERNIZATION_MEGA_SHOP_ITEM_FIRST 999u
#define MODERNIZATION_MEGA_SHOP_ITEM_LAST 1043u
#define MODERNIZATION_MEGA_SHOP_CLAIM_FLAG_FIRST 0x14A0u
#define MODERNIZATION_MEGA_SHOP_CLAIM_FLAG_LAST 0x14CCu

typedef enum ModernizationMegaShopResult {
    MEGA_SHOP_RESULT_SUCCESS = 0,
    MEGA_SHOP_RESULT_CANCELLED = 2,
    MEGA_SHOP_RESULT_LOCKED = 3,
    MEGA_SHOP_RESULT_INVALID_SELECTION = 5,
    MEGA_SHOP_RESULT_BUSY = 9,
    MEGA_SHOP_RESULT_PERSIST_FAILED = 13,
    MEGA_SHOP_RESULT_INSUFFICIENT_BP = 14,
    MEGA_SHOP_RESULT_BAG_FULL = 15,
    MEGA_SHOP_RESULT_ENGINE_REJECTED = 16,
    MEGA_SHOP_RESULT_ALREADY_CLAIMED = 17,
    MEGA_SHOP_RESULT_ALL_CLAIMED = 18
} ModernizationMegaShopResult;

uint16_t MegaShop_Probe(void);
uint16_t MegaShop_EnsureSave(void);
uint16_t MegaShop_GetBalance(void);
uint16_t MegaShop_IsUnlocked(uint16_t catalog_index);
uint16_t MegaShop_IsClaimed(uint16_t catalog_index);
uint16_t MegaShop_PurchaseByIndex(uint16_t catalog_index);
uint16_t MegaShop_PurchaseSelected(void);
uint16_t MegaShop_Open(void);
void MegaShop_PostMenu(void);

#endif /* MODERNIZATION_MEGA_SHOP_H */
