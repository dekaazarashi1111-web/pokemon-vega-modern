#include "qol_b.h"

#define QOL_B_SPECIAL_VAR_RESULT ((volatile uint16_t *)(uintptr_t)0x02037004u)
#define QOL_B_RUNTIME_MARKER 0x0B17u
#define QOL_B_SET_WARP_DESTINATION ((void (*)(int8_t, int8_t, int8_t, int8_t, int8_t))(uintptr_t)0x08054C4Du)
#define QOL_B_WARP_INTO_MAP ((void (*)(void))(uintptr_t)0x08054C39u)
#define QOL_B_RESET_INITIAL_AVATAR ((void (*)(void))(uintptr_t)0x080552A5u)
#define QOL_B_SET_MAIN_CALLBACK2 ((void (*)(void (*)(void)))(uintptr_t)0x08000545u)
#define QOL_B_CB2_LOAD_MAP ((void (*)(void))(uintptr_t)0x08055FDDu)
#define QOL_B_FIELD_CALLBACK (*(void (**)(void))(uintptr_t)0x03005060u)
#define QOL_B_DEFAULT_WARP_EXIT ((void (*)(void))(uintptr_t)0x0807D695u)

static void clear_mon(QolBMon *mon)
{
    size_t index;
    mon->species_id = 0;
    mon->name_key = 0;
    mon->ability_id = 0;
    mon->held_item = 0;
    for (index = 0; index < QOL_B_MOVE_COUNT; ++index) {
        mon->moves[index] = 0;
        mon->pp[index] = 0;
    }
    mon->type1 = 0;
    mon->type2 = 0;
    mon->flags = 0;
    mon->item_flags = 0;
}

static void copy_mon(QolBMon *destination, const QolBMon *source)
{
    size_t index;
    destination->species_id = source->species_id;
    destination->name_key = source->name_key;
    destination->ability_id = source->ability_id;
    destination->held_item = source->held_item;
    for (index = 0; index < QOL_B_MOVE_COUNT; ++index) {
        destination->moves[index] = source->moves[index];
        destination->pp[index] = source->pp[index];
    }
    destination->type1 = source->type1;
    destination->type2 = source->type2;
    destination->flags = source->flags;
    destination->item_flags = source->item_flags;
}

static uint8_t selected(uint32_t mask, size_t index)
{
    return (uint8_t)((mask >> index) & 1u);
}

static uint8_t valid_box_count(size_t count)
{
    return (uint8_t)(count <= QOL_B_BOX_CAPACITY);
}

size_t QolB_Search(const QolBMon *box, size_t count,
                   const QolBFilter *filter, uint8_t *matches,
                   size_t match_capacity)
{
    size_t index;
    size_t written = 0;
    if (box == NULL || filter == NULL || matches == NULL
        || !valid_box_count(count)) {
        return 0;
    }
    for (index = 0; index < count; ++index) {
        const QolBMon *mon = &box[index];
        uint8_t match = (uint8_t)(mon->species_id != 0);
        if (match && filter->use_name && mon->name_key != filter->name_key)
            match = 0;
        if (match && filter->use_ability && mon->ability_id != filter->ability_id)
            match = 0;
        if (match && filter->use_type
            && mon->type1 != filter->type_id && mon->type2 != filter->type_id)
            match = 0;
        if (match) {
            if (written >= match_capacity)
                return written;
            matches[written++] = (uint8_t)index;
        }
    }
    return written;
}

QolBStatus QolB_MoveSelected(QolBMon *source, size_t source_count,
                             QolBMon *destination, size_t destination_count,
                             uint32_t selection_mask, uint8_t cancelled)
{
    size_t index;
    size_t selected_count = 0;
    size_t free_count = 0;
    if (cancelled)
        return QOL_B_ERR_CANCELLED;
    if (source == NULL || destination == NULL || source == destination
        || !valid_box_count(source_count) || !valid_box_count(destination_count))
        return QOL_B_ERR_ARGUMENT;
    for (index = 0; index < source_count; ++index) {
        if (selected(selection_mask, index) && source[index].species_id != 0)
            ++selected_count;
    }
    if (selected_count == 0)
        return QOL_B_ERR_EMPTY_SELECTION;
    for (index = 0; index < destination_count; ++index) {
        if (destination[index].species_id == 0)
            ++free_count;
    }
    if (free_count < selected_count)
        return QOL_B_ERR_CAPACITY;

    for (index = 0; index < source_count; ++index) {
        size_t destination_index;
        if (!selected(selection_mask, index) || source[index].species_id == 0)
            continue;
        for (destination_index = 0; destination_index < destination_count;
             ++destination_index) {
            if (destination[destination_index].species_id == 0) {
                copy_mon(&destination[destination_index], &source[index]);
                clear_mon(&source[index]);
                break;
            }
        }
    }
    return QOL_B_OK;
}

static QolBStatus validate_item_transaction(const QolBMon *box, size_t count,
                                            uint32_t selection_mask,
                                            size_t bag_count,
                                            size_t bag_capacity,
                                            uint8_t release,
                                            size_t *item_count)
{
    size_t index;
    size_t chosen = 0;
    size_t held = 0;
    if (box == NULL || item_count == NULL || !valid_box_count(count)
        || bag_count > bag_capacity)
        return QOL_B_ERR_ARGUMENT;
    for (index = 0; index < count; ++index) {
        const QolBMon *mon = &box[index];
        if (!selected(selection_mask, index) || mon->species_id == 0)
            continue;
        ++chosen;
        if (release && (mon->flags & (QOL_B_MON_EGG | QOL_B_MON_NO_RELEASE)))
            return QOL_B_ERR_FORBIDDEN_MON;
        if (mon->held_item != 0) {
            if (mon->item_flags & (QOL_B_ITEM_MAIL | QOL_B_ITEM_KEY))
                return QOL_B_ERR_FORBIDDEN_ITEM;
            ++held;
        }
    }
    if (chosen == 0)
        return QOL_B_ERR_EMPTY_SELECTION;
    if (bag_capacity - bag_count < held)
        return QOL_B_ERR_CAPACITY;
    *item_count = held;
    return QOL_B_OK;
}

QolBStatus QolB_ReleaseSelected(QolBMon *box, size_t count,
                                uint32_t selection_mask, uint16_t *bag_items,
                                size_t *bag_count, size_t bag_capacity,
                                uint8_t cancelled)
{
    size_t index;
    size_t held;
    QolBStatus status;
    if (cancelled)
        return QOL_B_ERR_CANCELLED;
    if (bag_count == NULL || (bag_capacity != 0 && bag_items == NULL))
        return QOL_B_ERR_ARGUMENT;
    status = validate_item_transaction(box, count, selection_mask, *bag_count,
                                       bag_capacity, 1, &held);
    if (status != QOL_B_OK)
        return status;
    (void)held;
    for (index = 0; index < count; ++index) {
        if (!selected(selection_mask, index) || box[index].species_id == 0)
            continue;
        if (box[index].held_item != 0)
            bag_items[(*bag_count)++] = box[index].held_item;
        clear_mon(&box[index]);
    }
    return QOL_B_OK;
}

QolBStatus QolB_TakeHeldItems(QolBMon *box, size_t count,
                              uint32_t selection_mask, uint16_t *bag_items,
                              size_t *bag_count, size_t bag_capacity,
                              uint8_t cancelled)
{
    size_t index;
    size_t held;
    QolBStatus status;
    if (cancelled)
        return QOL_B_ERR_CANCELLED;
    if (bag_count == NULL || (bag_capacity != 0 && bag_items == NULL))
        return QOL_B_ERR_ARGUMENT;
    status = validate_item_transaction(box, count, selection_mask, *bag_count,
                                       bag_capacity, 0, &held);
    if (status != QOL_B_OK)
        return status;
    if (held == 0)
        return QOL_B_ERR_EMPTY_SELECTION;
    for (index = 0; index < count; ++index) {
        if (!selected(selection_mask, index) || box[index].species_id == 0
            || box[index].held_item == 0)
            continue;
        bag_items[(*bag_count)++] = box[index].held_item;
        box[index].held_item = 0;
        box[index].item_flags = 0;
    }
    return QOL_B_OK;
}

uint8_t QolB_FieldPcAllowed(uint8_t feature_unlocked,
                            uint8_t map_schema_allowed,
                            uint8_t context_flags)
{
    const uint8_t forbidden = QOL_B_FIELD_BATTLE | QOL_B_FIELD_SCRIPT
        | QOL_B_FIELD_GYM | QOL_B_FIELD_DUNGEON | QOL_B_FIELD_LEAGUE
        | QOL_B_FIELD_EVENT;
    return (uint8_t)(feature_unlocked && map_schema_allowed
                     && (context_flags & forbidden) == 0);
}

QolBStatus QolB_RelearnMove(QolBMon *mon, uint8_t move_slot,
                            uint16_t move_id, uint8_t initial_pp,
                            const uint16_t *relearn_pool, size_t pool_count,
                            uint8_t feature_unlocked, uint8_t cancelled)
{
    size_t index;
    if (cancelled)
        return QOL_B_ERR_CANCELLED;
    if (!feature_unlocked)
        return QOL_B_ERR_NOT_UNLOCKED;
    if (mon == NULL || relearn_pool == NULL || mon->species_id == 0
        || move_slot >= QOL_B_MOVE_COUNT || move_id == 0 || initial_pp == 0)
        return QOL_B_ERR_ARGUMENT;
    for (index = 0; index < pool_count; ++index) {
        if (relearn_pool[index] == move_id) {
            mon->moves[move_slot] = move_id;
            mon->pp[move_slot] = initial_pp;
            return QOL_B_OK;
        }
    }
    return QOL_B_ERR_MOVE_NOT_IN_POOL;
}

QolBStatus QolB_EggBasketAdvance(QolBEggBasket *basket, uint16_t steps,
                                 uint8_t parents_registered,
                                 uint8_t parents_compatible,
                                 uint8_t map_allowed,
                                 uint16_t generated_species)
{
    uint32_t total;
    uint32_t checks;
    if (basket == NULL)
        return QOL_B_ERR_ARGUMENT;
    if (!basket->enabled)
        return QOL_B_ERR_NOT_UNLOCKED;
    total = (uint32_t)basket->step_counter + steps;
    checks = total / 256u;
    basket->step_counter = (uint16_t)(total % 256u);
    while (checks-- != 0) {
        if (!parents_registered || !parents_compatible || !map_allowed
            || generated_species == 0)
            continue;
        if (basket->queue_count >= QOL_B_EGG_QUEUE_CAPACITY)
            return QOL_B_ERR_CAPACITY;
        basket->eggs[basket->queue_count++] = generated_species;
    }
    return QOL_B_OK;
}

uint8_t QolB_AutoBattleAllowed(uint8_t feature_unlocked,
                               uint8_t battle_context,
                               uint8_t lead_can_battle,
                               uint8_t cancelled)
{
    const uint8_t forbidden = QOL_B_BATTLE_TRAINER | QOL_B_BATTLE_STATIC
        | QOL_B_BATTLE_STORY | QOL_B_BATTLE_SHINY;
    return (uint8_t)(feature_unlocked && !cancelled && lead_can_battle
                     && (battle_context & QOL_B_BATTLE_RANDOM_WILD)
                     && (battle_context & forbidden) == 0);
}

uint16_t QolB_RuntimeProbe(void)
{
    *QOL_B_SPECIAL_VAR_RESULT = QOL_B_RUNTIME_MARKER;
    return QOL_B_RUNTIME_MARKER;
}

static void warp_and_load(int8_t group, int8_t map, int8_t warp_id,
                          int8_t x, int8_t y)
{
    QOL_B_SET_WARP_DESTINATION(group, map, warp_id, x, y);
    QOL_B_RESET_INITIAL_AVATAR();
    QOL_B_WARP_INTO_MAP();
    QOL_B_FIELD_CALLBACK = QOL_B_DEFAULT_WARP_EXIT;
    QOL_B_SET_MAIN_CALLBACK2(QOL_B_CB2_LOAD_MAP);
}

void QolB_PortalWarp(void)
{
    warp_and_load(96, 5, -1, 20, 20);
}

void QolB_ReturnWarp(void)
{
    warp_and_load(4, 0, -1, 8, 5);
}
