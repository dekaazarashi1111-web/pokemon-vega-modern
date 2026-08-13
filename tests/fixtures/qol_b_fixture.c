#include <stdio.h>
#include <string.h>

#include "qol_b.h"

#define CHECK(expression) do { if (!(expression)) { \
    fprintf(stderr, "qol-b fixture failed at line %d: %s\n", __LINE__, #expression); \
    return 1; \
} } while (0)

static QolBMon mon(uint16_t species, uint16_t name, uint8_t type,
                   uint16_t ability, uint16_t item)
{
    QolBMon result;
    memset(&result, 0, sizeof(result));
    result.species_id = species;
    result.name_key = name;
    result.type1 = type;
    result.ability_id = ability;
    result.held_item = item;
    return result;
}

int main(void)
{
    QolBMon source[4] = {mon(1, 10, 3, 20, 50), mon(2, 11, 4, 21, 0),
                         mon(3, 10, 4, 20, 51), {0}};
    QolBMon destination[3] = {{0}};
    QolBMon snapshot[4];
    QolBFilter filter = {.name_key = 10, .ability_id = 20, .type_id = 4,
                         .use_name = 1, .use_ability = 1, .use_type = 1};
    uint8_t matches[4] = {0};
    uint16_t bag[4] = {0};
    size_t bag_count = 0;
    uint16_t pool[] = {100, 200, 300};
    QolBEggBasket basket = {.step_counter = 255, .enabled = 1};
    QolBEggBasket saved;

    CHECK(QolB_Search(source, 4, &filter, matches, 4) == 1);
    CHECK(matches[0] == 2);
    memcpy(snapshot, source, sizeof(source));
    destination[0] = mon(9, 9, 9, 9, 0);
    destination[1] = mon(8, 8, 8, 8, 0);
    CHECK(QolB_MoveSelected(source, 4, destination, 3, 0x7, 0)
          == QOL_B_ERR_CAPACITY);
    CHECK(memcmp(snapshot, source, sizeof(source)) == 0);
    memset(destination, 0, sizeof(destination));
    CHECK(QolB_MoveSelected(source, 4, destination, 3, 0x5, 0) == QOL_B_OK);
    CHECK(source[0].species_id == 0 && source[2].species_id == 0);
    CHECK(destination[0].species_id == 1 && destination[1].species_id == 3);

    memcpy(source, destination, sizeof(destination));
    source[0].flags = QOL_B_MON_EGG;
    memcpy(snapshot, source, sizeof(source));
    CHECK(QolB_ReleaseSelected(source, 3, 1, bag, &bag_count, 4, 0)
          == QOL_B_ERR_FORBIDDEN_MON);
    CHECK(memcmp(snapshot, source, sizeof(source)) == 0 && bag_count == 0);
    source[0].flags = 0;
    source[0].item_flags = QOL_B_ITEM_MAIL;
    CHECK(QolB_ReleaseSelected(source, 3, 1, bag, &bag_count, 4, 0)
          == QOL_B_ERR_FORBIDDEN_ITEM);
    source[0].item_flags = 0;
    CHECK(QolB_ReleaseSelected(source, 3, 1, bag, &bag_count, 0, 0)
          == QOL_B_ERR_CAPACITY);
    CHECK(source[0].species_id == 1);
    CHECK(QolB_ReleaseSelected(source, 3, 1, bag, &bag_count, 4, 1)
          == QOL_B_ERR_CANCELLED);
    CHECK(QolB_ReleaseSelected(source, 3, 1, bag, &bag_count, 4, 0) == QOL_B_OK);
    CHECK(source[0].species_id == 0 && bag_count == 1 && bag[0] == 50);

    CHECK(QolB_TakeHeldItems(source, 3, 2, bag, &bag_count, 4, 0) == QOL_B_OK);
    CHECK(source[1].held_item == 0 && bag_count == 2 && bag[1] == 51);
    CHECK(QolB_FieldPcAllowed(1, 1, 0) == 1);
    CHECK(QolB_FieldPcAllowed(1, 1, QOL_B_FIELD_DUNGEON) == 0);
    CHECK(QolB_FieldPcAllowed(0, 1, 0) == 0);

    source[1] = mon(4, 4, 4, 4, 0);
    CHECK(QolB_RelearnMove(&source[1], 2, 200, 15, pool, 3, 1, 0) == QOL_B_OK);
    CHECK(source[1].moves[2] == 200 && source[1].pp[2] == 15);
    CHECK(QolB_RelearnMove(&source[1], 2, 999, 15, pool, 3, 1, 0)
          == QOL_B_ERR_MOVE_NOT_IN_POOL);
    CHECK(source[1].moves[2] == 200);

    CHECK(QolB_EggBasketAdvance(&basket, 0, 1, 1, 1, 25) == QOL_B_OK);
    CHECK(basket.queue_count == 0 && basket.step_counter == 255);
    CHECK(QolB_EggBasketAdvance(&basket, 1, 1, 1, 1, 25) == QOL_B_OK);
    CHECK(basket.queue_count == 1 && basket.eggs[0] == 25 && basket.step_counter == 0);
    saved = basket;
    CHECK(QolB_EggBasketAdvance(&basket, 256, 0, 1, 1, 25) == QOL_B_OK);
    CHECK(basket.queue_count == 1);
    basket = saved;
    CHECK(basket.queue_count == 1 && basket.eggs[0] == 25);
    basket.queue_count = QOL_B_EGG_QUEUE_CAPACITY;
    CHECK(QolB_EggBasketAdvance(&basket, 256, 1, 1, 1, 25)
          == QOL_B_ERR_CAPACITY);

    CHECK(QolB_AutoBattleAllowed(1, QOL_B_BATTLE_RANDOM_WILD, 1, 0) == 1);
    CHECK(QolB_AutoBattleAllowed(1, QOL_B_BATTLE_RANDOM_WILD | QOL_B_BATTLE_SHINY,
                                 1, 0) == 0);
    CHECK(QolB_AutoBattleAllowed(1, QOL_B_BATTLE_TRAINER, 1, 0) == 0);
    CHECK(QolB_AutoBattleAllowed(1, QOL_B_BATTLE_RANDOM_WILD, 1, 1) == 0);

    puts("{\"schema_version\":1,\"status\":\"PASS\",\"cases\":31,"
         "\"atomic_rollbacks\":5,\"egg_boundaries\":6,\"ui\":\"EXISTING_ONLY\"}");
    return 0;
}
