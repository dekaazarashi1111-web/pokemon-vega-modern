/* weather12 initAll tableの4byteだけから呼ぶ。旧LOSS/Factory/readkeys/Saveは不変。 */
#include "circus_drought.h"
#include "circus_drought_addresses.h"
#include "../save_migration/save_migration.h"
#define READ8(a) (*(const volatile uint8_t *)(uintptr_t)(a))
#define READ32(a) (*(const volatile uint32_t *)(uintptr_t)(a))
#define NATIVE(a) ((void (*)(void))(uintptr_t)(a))
__attribute__((used, noinline, externally_visible))
void CircusDroughtInitAll(void)
{
    volatile uint8_t *w = (volatile uint8_t *)(uintptr_t)0x02037E68u;
    const volatile VegaFactoryState *f = &gVegaModernSaveData->factory;
    CircusDroughtContext c;
    c.armed = 0u;
    c.ledger_valid = 0u;
    c.circus = (uint8_t)((READ32(0x02022AACu) & 0x04000000u) != 0u);
    c.marker = f->marker;
    c.snapshot = f->snapshot_valid;
    c.count = f->party_count;
    c.outcome = READ8(0x02023DEAu);
    c.weather = w[0x6D0];
    c.next_weather = w[0x6D1];
    c.ready = w[0x6C8];
    c.graphics_loaded = w[0x6C6];
    c.callback = READ32(0x03003134u);
    c.script = READ32(0x03000EB8u);
    if (c.circus == 1u && c.outcome == 1u && c.callback == 0x08055E75u) {
        c.armed = (uint8_t)((int (*)(void))(uintptr_t)CIRCUS_DROUGHT_ARMED)();
        c.ledger_valid = (uint8_t)(VegaSaveValidate(gVegaModernSaveData, VEGA_SAVE_LEDGER_SIZE) == VEGA_SAVE_OK);
    }
    CircusDroughtInitialize(&c, w, NATIVE(0x0807AD09u), NATIVE(0x0807ACD5u), NATIVE(0x0807AD39u));
}
