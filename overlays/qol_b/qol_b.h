#ifndef VEGA_QOL_B_H
#define VEGA_QOL_B_H

#include <stddef.h>
#include <stdint.h>

#define QOL_B_BOX_CAPACITY 30u
#define QOL_B_MOVE_COUNT 4u
#define QOL_B_EGG_QUEUE_CAPACITY 5u

enum QolBMonFlags {
    QOL_B_MON_EGG = 1u << 0,
    QOL_B_MON_NO_RELEASE = 1u << 1,
    QOL_B_MON_SHINY = 1u << 2,
    QOL_B_MON_STATIC_ENCOUNTER = 1u << 3,
    QOL_B_MON_STORY_ENCOUNTER = 1u << 4,
};

enum QolBItemFlags {
    QOL_B_ITEM_MAIL = 1u << 0,
    QOL_B_ITEM_KEY = 1u << 1,
};

enum QolBFieldContext {
    QOL_B_FIELD_BATTLE = 1u << 0,
    QOL_B_FIELD_SCRIPT = 1u << 1,
    QOL_B_FIELD_GYM = 1u << 2,
    QOL_B_FIELD_DUNGEON = 1u << 3,
    QOL_B_FIELD_LEAGUE = 1u << 4,
    QOL_B_FIELD_EVENT = 1u << 5,
};

enum QolBBattleContext {
    QOL_B_BATTLE_RANDOM_WILD = 1u << 0,
    QOL_B_BATTLE_TRAINER = 1u << 1,
    QOL_B_BATTLE_STATIC = 1u << 2,
    QOL_B_BATTLE_STORY = 1u << 3,
    QOL_B_BATTLE_SHINY = 1u << 4,
};

typedef enum QolBStatus {
    QOL_B_OK = 0,
    QOL_B_ERR_ARGUMENT = 1,
    QOL_B_ERR_EMPTY_SELECTION = 2,
    QOL_B_ERR_CAPACITY = 3,
    QOL_B_ERR_FORBIDDEN_MON = 4,
    QOL_B_ERR_FORBIDDEN_ITEM = 5,
    QOL_B_ERR_NOT_UNLOCKED = 6,
    QOL_B_ERR_NOT_ALLOWED = 7,
    QOL_B_ERR_MOVE_NOT_IN_POOL = 8,
    QOL_B_ERR_CANCELLED = 9,
} QolBStatus;

typedef struct QolBMon {
    uint16_t species_id;
    uint16_t name_key;
    uint16_t ability_id;
    uint16_t held_item;
    uint16_t moves[QOL_B_MOVE_COUNT];
    uint8_t pp[QOL_B_MOVE_COUNT];
    uint8_t type1;
    uint8_t type2;
    uint8_t flags;
    uint8_t item_flags;
} QolBMon;

typedef struct QolBFilter {
    uint16_t name_key;
    uint16_t ability_id;
    uint8_t type_id;
    uint8_t use_name;
    uint8_t use_ability;
    uint8_t use_type;
} QolBFilter;

typedef struct QolBEggBasket {
    uint16_t step_counter;
    uint16_t eggs[QOL_B_EGG_QUEUE_CAPACITY];
    uint8_t queue_count;
    uint8_t enabled;
} QolBEggBasket;

size_t QolB_Search(const QolBMon *box, size_t count,
                   const QolBFilter *filter, uint8_t *matches,
                   size_t match_capacity);

QolBStatus QolB_MoveSelected(QolBMon *source, size_t source_count,
                             QolBMon *destination, size_t destination_count,
                             uint32_t selection_mask, uint8_t cancelled);

QolBStatus QolB_ReleaseSelected(QolBMon *box, size_t count,
                                uint32_t selection_mask, uint16_t *bag_items,
                                size_t *bag_count, size_t bag_capacity,
                                uint8_t cancelled);

QolBStatus QolB_TakeHeldItems(QolBMon *box, size_t count,
                              uint32_t selection_mask, uint16_t *bag_items,
                              size_t *bag_count, size_t bag_capacity,
                              uint8_t cancelled);

uint8_t QolB_FieldPcAllowed(uint8_t feature_unlocked,
                            uint8_t map_schema_allowed,
                            uint8_t context_flags);

QolBStatus QolB_RelearnMove(QolBMon *mon, uint8_t move_slot,
                            uint16_t move_id, uint8_t initial_pp,
                            const uint16_t *relearn_pool, size_t pool_count,
                            uint8_t feature_unlocked, uint8_t cancelled);

QolBStatus QolB_EggBasketAdvance(QolBEggBasket *basket, uint16_t steps,
                                 uint8_t parents_registered,
                                 uint8_t parents_compatible,
                                 uint8_t map_allowed,
                                 uint16_t generated_species);

uint8_t QolB_AutoBattleAllowed(uint8_t feature_unlocked,
                               uint8_t battle_context,
                               uint8_t lead_can_battle,
                               uint8_t cancelled);

/* Script-callable ROM probe. The T17 portal invokes this through callnative;
 * it writes a deterministic marker to VAR_RESULT's fixed CFRU-JP ABI address. */
uint16_t QolB_RuntimeProbe(void);

/* Event-script adapters used by the bidirectional Vega/Kanto portal. */
void QolB_PortalWarp(void);
void QolB_ReturnWarp(void);

#endif
