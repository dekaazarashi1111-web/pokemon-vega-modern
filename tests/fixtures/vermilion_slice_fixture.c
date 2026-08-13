#include "../../src/kanto/vermilion/vermilion_slice.h"

#include <stdio.h>
#include <string.h>

#define CHECK(expr) do { if (!(expr)) { fprintf(stderr, "FAIL:%d:%s\n", __LINE__, #expr); return 1; } } while (0)

typedef struct Flash { VegaModernSaveData active; int fail_next; } Flash;

static int Persist(const VegaModernSaveData *data, size_t size, void *context)
{
    Flash *flash = context;
    if (size != sizeof(flash->active) || flash->fail_next) {
        flash->fail_next = 0;
        return 0;
    }
    memcpy(&flash->active, data, size);
    return 1;
}

static VegaWarpAnchor Anchor(uint8_t group, uint8_t map)
{
    VegaWarpAnchor result = {group, map, 0, 1, 4, 4};
    return result;
}

int main(void)
{
    VegaModernSaveData save;
    VegaModernSaveData before;
    VegaVermilionRuntime runtime = {0};
    Flash flash = {0};
    unsigned result;

    VegaSaveInitNew(&save, 1);
    flash.active = save;
    CHECK(!VegaVermilionCanUnlock(&save, &runtime));
    runtime.shiou_badge_flag = 1;
    CHECK(!VegaVermilionCanUnlock(&save, &runtime));
    runtime.dh_clear_flag = 1;
    CHECK(VegaVermilionCanUnlock(&save, &runtime));
    CHECK(VegaVermilionLatchTravel(&save, &runtime, Persist, &flash) == VEGA_SAVE_OK);
    CHECK(save.kanto_travel_unlocked && !save.vega_hall_of_fame && !runtime.national_dex);

    runtime.warning_accepted = 1;
    flash.fail_next = 1;
    before = save;
    CHECK(VegaVermilionEnter(&save, &runtime, Anchor(4, 0), Anchor(96, 5), Persist, &flash)
          == VEGA_SAVE_PERSIST_FAILED);
    CHECK(memcmp(&before, &save, sizeof(save)) == 0);
    CHECK(VegaVermilionEnter(&save, &runtime, Anchor(4, 0), Anchor(96, 5), Persist, &flash)
          == VEGA_SAVE_OK);
    CHECK(save.current_region == VEGA_REGION_KANTO && save.kanto_visited);
    CHECK(save.heal_anchor[VEGA_REGION_KANTO].map_group == 96);
    for (result = VEGA_SHIP_DECLINED; result <= VEGA_SHIP_QUIT; ++result)
        CHECK(VegaVermilionApplyShipResult(&save, (VegaShipBattleResult)result));
    CHECK(VegaVermilionResolveWhiteout(&save, Persist, &flash) == VEGA_SAVE_OK);
    CHECK(save.current_region == VEGA_REGION_KANTO);
    CHECK(VegaVermilionReturn(&save, Persist, &flash) == VEGA_SAVE_OK);
    CHECK(save.current_region == VEGA_REGION_TOHOKU && save.kanto_travel_unlocked);

    save.kanto_certifications = 0x01;
    CHECK(!VegaVermilionGymAvailable(&save));
    save.kanto_certifications = 0x03;
    CHECK(VegaVermilionGymAvailable(&save));
    CHECK(!VegaVermilionGymAdjustVoltage(&runtime, 0, 1));
    CHECK(!VegaVermilionGymAdjustVoltage(&runtime, 0, 2));
    CHECK(!VegaVermilionGymAdjustVoltage(&runtime, 1, 1));
    CHECK(VegaVermilionGymAdjustVoltage(&runtime, 2, 3));
    CHECK(VegaVermilionGymClaimReward(&save, &runtime));
    CHECK((save.kanto_certifications & 0x07) == 0x07);
    CHECK(!VegaVermilionGymClaimReward(&save, &runtime));
    CHECK(VegaVermilionSafeRouteIsClear(&runtime));
    puts("vermilion slice fixture: PASS");
    return 0;
}
