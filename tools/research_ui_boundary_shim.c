/* 限定host seam。engine serviceだけをstubにし、製品callbackは無改変。 */
#define RESEARCH_EXPORT(name)
static u8 storage[2050], before[2050];
static ResearchEconomyVolatileState state;
static struct Task tasks[NUM_TASKS];
static u16 special;
#define G_LEDGER (storage + 1)
#define G_OWNER (G_LEDGER + RESEARCH_ECONOMY_OWNER_OFFSET)
#define G_VOLATILE (&state)
#define G_TASKS tasks
#define G_SPECIAL_RESULT (&special)
static ResearchEconomyShopConfig gResearchEconomyShop[23];
static const u8 gResearchEconomyBalancePrefix[] = {'R','P',':',0xFF};
static const u8 gResearchEconomyDigitGlyphs[] = {'0','1','2','3','4','5','6','7','8','9'};
static const u8 gResearchEconomyTextNext[] = {'N',0xFF};
static const u8 gResearchEconomyTextCancel[] = {'C',0xFF};
static const u8 sEmptyText[] = {0xFF};
static u8 row_text[23][2];
static unsigned created, destroyed, opened, removed, enabled, resumed, sounds, purchase_calls;
static unsigned frame_clears, bg_copies, cursor_rows, rendered_rows;
static u16 purchase_index, purchase_confirmed, purchase_result;
static s8 choice;
static u8 idle = 1, kanto = 1, task_fail, window_fail, eligible[23];
static void (*callback)(u8);
static u16 read_u16(const volatile u8 *);
static u8 ensure_save_idle(void) { return idle; }
static u8 kanto_access(void) { return kanto; }
static u8 unlock_satisfied(u8 kind) { assert(kind < 23); return eligible[kind]; }
static u16 owner_u16(u32 offset) { return read_u16(G_OWNER + offset); }
/* SaveInitNewのV2分岐以外へstubを誤適用したら停止。 */
u32 ResearchEconomy_SaveValidate(const void *p, u32 n) { (void)p; (void)n; abort(); }
static u8 create_task(void (*fn)(u8), u8 priority) {
    assert(priority == 0x50); ++created;
    if (task_fail) return NUM_TASKS;
    assert(callback == NULL); callback = fn; tasks[3].is_active = 1; return 3;
}
static void destroy_task(u8 id) { assert(id == 3 && tasks[id].is_active); ++destroyed; tasks[id].is_active = 0; callback = NULL; }
static u16 add_window(const struct WindowTemplate *t) {
    assert(t->bg == 0 && t->tilemap_left == 8 && t->tilemap_top == 0 && t->width == 21);
    assert(t->palette_num == 15 && t->base_block == 0x100);
    assert(t->height >= 6 && t->height <= 16);
    ++opened; rendered_rows = 0;
    return window_fail ? WINDOW_INVALID : 4;
}
static void remove_window(u8 id) { assert(id == 4); ++removed; }
static void window_pair(u8 id, u8 value) { assert(id == 4); (void)value; }
static void window_single(u8 id) { assert(id == 4); }
static void clear_frame(u8 id, u8 value) { assert(id == 4 && value == 0); ++frame_clears; }
static void copy_bg(u8 id) { assert(id == 0); ++bg_copies; }
static u16 base_tile(void) { return 0x100; }
static void print_text(u8 id, u8 font, const u8 *text, u8 x, u8 y, u8 speed, void *cb) {
    assert(id == 4 && font == 2 && x == 8 && speed == 0 && cb == NULL);
    if (y == 1) { assert(text == state.balance_text); return; }
    assert(y == 17 + rendered_rows * 16); ++rendered_rows;
    if (text != gResearchEconomyTextNext && text != gResearchEconomyTextCancel && text != sEmptyText)
        assert(text[0] < 23 && text[1] == 0xFF);
}
static u8 init_cursor(u8 id, u8 font, u8 x, u8 y, u8 dy, u8 rows, u8 initial) {
    assert(id == 4 && font == 2 && x == 0 && y == 17 && dy == 16 && initial == 0);
    assert(rows == rendered_rows && rows >= 2 && rows <= 6); cursor_rows = rows; return 0;
}
static s8 menu_input(void) { return choice; }
static void enable_context(void) { ++enabled; }
static void resume_context(void) { ++resumed; }
static void sound(u16 value) { assert(value == SE_SELECT); ++sounds; }
u16 ResearchEconomy_PurchaseByIndex(u16 index, u16 confirmed) { ++purchase_calls; purchase_index = index; purchase_confirmed = confirmed; return purchase_result; }
#define FN_CREATE_TASK create_task
#define FN_DESTROY_TASK destroy_task
#define FN_ADD_WINDOW add_window
#define FN_REMOVE_WINDOW remove_window
#define FN_CLEAR_STD_WINDOW_FRAME clear_frame
#define FN_SCHEDULE_BG_COPY copy_bg
#define FN_GET_STD_WINDOW_BASE_TILE base_tile
#define FN_FILL_WINDOW_PIXEL_BUFFER window_pair
#define FN_DRAW_STD_WINDOW_FRAME window_pair
#define FN_PUT_WINDOW_TILEMAP window_single
#define FN_ADD_TEXT_PRINTER print_text
#define FN_MENU_INIT_CURSOR init_cursor
#define FN_COPY_WINDOW_TO_VRAM window_pair
#define FN_MENU_PROCESS_INPUT menu_input
#define FN_ENABLE_BOTH_SCRIPT_CONTEXTS resume_context
#define FN_SCRIPT_CONTEXT2_ENABLE enable_context
#define FN_PLAY_SE sound

/* CANONICAL_FUNCTIONS */

static u32 independent_checksum(const u8 *bytes) {
    u32 hash = 2166136261u;
    for (unsigned i = 0; i < 2048; ++i) { hash ^= (i >= 8 && i < 12) ? 0 : bytes[i]; hash *= 16777619u; }
    return hash;
}
static void setup(void) {
    memset(storage, 0xA5, sizeof(storage)); memset(&state, 0, sizeof(state));
    reset_volatile_state(); ResearchEconomy_SaveInitNew(G_LEDGER, 0);
    for (unsigned i = 0; i < 23; ++i) { eligible[i] = 1; row_text[i][0] = (u8)i; row_text[i][1] = 0xFF; gResearchEconomyShop[i].unlock_kind = (u8)i; gResearchEconomyShop[i].row_text = row_text[i]; }
    memcpy(before, storage, sizeof(storage));
}
static void assert_storage_unchanged(void) { assert(memcmp(storage, before, sizeof(storage)) == 0); }
static void open_ok(void) {
    assert(ResearchEconomy_OpenShop() == RESEARCH_RESULT_BUSY);
    assert(callback != NULL && state.menu_active == 1 && state.window_id == 4);
    assert(state.selected_catalog == 0xFFFF && state.last_result == RESEARCH_RESULT_BUSY && special == RESEARCH_RESULT_BUSY);
    assert(created == 1 && enabled == 1 && resumed == 0 && purchase_calls == 0);
    assert(cursor_rows == (state.eligible_count > 5 ? 6u : (unsigned)state.eligible_count + 1u));
}
static void input(s8 value) { assert(callback != NULL); choice = value; callback(3); }
static void closed(u16 selected, u16 result) {
    assert(state.menu_active == 0 && state.window_id == 0xFF && state.selected_catalog == selected);
    assert(state.last_result == result && special == result && callback == NULL);
    assert(destroyed == 1 && resumed == 1 && sounds == 1 && frame_clears == removed);
    special = 0x7777; ResearchEconomy_PostShopMenu(); assert(special == result);
    assert_storage_unchanged();
}
static void new_game(unsigned badge) {
    u8 expected[2048] = {0};
    memset(storage, 0xA5, sizeof(storage));
    ResearchEconomy_SaveInitNew(G_LEDGER, (u8)badge);
    expected[0] = 'V'; expected[1] = 'G'; expected[2] = 'S'; expected[3] = '1'; expected[4] = 2; expected[7] = 8;
    expected[29] = 1; expected[30] = (u8)(badge != 0);
    expected[0x73F] = 1; expected[0x740] = 64; expected[0x745] = 1; expected[0x763] = 1;
    u32 hash = independent_checksum(expected);
    for (unsigned i = 0; i < 4; ++i) expected[8 + i] = (u8)(hash >> (8 * i));
    assert(memcmp(G_LEDGER, expected, 2048) == 0);
    assert(storage[0] == 0xA5 && storage[2049] == 0xA5);
    ResearchEconomy_SaveInitNew(G_LEDGER, (u8)badge); assert(memcmp(G_LEDGER, expected, 2048) == 0);
    assert(purchase_calls == 0 && created == 0);
}
int main(int argc, char **argv) {
    assert(argc == 2); setup(); const char *mode = argv[1];
    if (strncmp(mode, "init-", 5) == 0 && strcmp(mode, "init-null") != 0) { new_game((unsigned)strtoul(mode + 5, NULL, 10)); }
    else if (strcmp(mode, "init-null") == 0) { ResearchEconomy_SaveInitNew(NULL, 1); assert_storage_unchanged(); }
    else if (strcmp(mode, "post-unset") == 0) { ResearchEconomy_PostShopMenu(); assert(special == RESEARCH_RESULT_CANCELLED); assert_storage_unchanged(); }
    else if (strcmp(mode, "purchase-unselected") == 0) { assert(ResearchEconomy_PurchaseSelected() == RESEARCH_RESULT_INVALID); assert(purchase_calls == 0); assert_storage_unchanged(); }
    else if (strcmp(mode, "save-blocked") == 0 || strcmp(mode, "kanto-locked") == 0 || strcmp(mode, "empty") == 0) {
        u16 expected = RESEARCH_RESULT_LOCKED;
        if (strcmp(mode, "save-blocked") == 0) { idle = 0; expected = RESEARCH_RESULT_CORRUPT_SAVE; }
        if (strcmp(mode, "kanto-locked") == 0) kanto = 0;
        if (strcmp(mode, "empty") == 0) memset(eligible, 0, sizeof(eligible));
        assert(ResearchEconomy_OpenShop() == expected); assert(created == 0 && enabled == 0 && purchase_calls == 0); assert_storage_unchanged();
    } else if (strcmp(mode, "task-fail") == 0 || strcmp(mode, "window-fail") == 0) {
        task_fail = strcmp(mode, "task-fail") == 0; window_fail = !task_fail;
        assert(ResearchEconomy_OpenShop() == RESEARCH_RESULT_ENGINE_REJECTED);
        assert(created == 1 && destroyed == (unsigned)window_fail && enabled == 0 && resumed == 0 && callback == NULL);
        assert(state.menu_active == 0 && state.selected_catalog == 0xFFFF && state.window_id == 0xFF); assert_storage_unchanged();
    } else if (strncmp(mode, "select-", 7) == 0) {
        unsigned index = (unsigned)strtoul(mode + 7, NULL, 10); assert(index < 23); open_ok();
        for (unsigned i = 0; i < index / 5; ++i) { input(5); assert(state.page == i + 1 && resumed == 0 && purchase_calls == 0); }
        input((s8)(index % 5)); closed((u16)index, RESEARCH_RESULT_SELECTED);
        assert(removed == index / 5 + 1 && opened == removed);
        purchase_result = RESEARCH_RESULT_PERSIST_FAILED; assert(ResearchEconomy_PurchaseSelected() == purchase_result);
        assert(purchase_calls == 1 && purchase_index == index && purchase_confirmed == 1); assert_storage_unchanged();
    } else {
        if (strcmp(mode, "filtered") == 0) { memset(eligible, 0, sizeof(eligible)); eligible[2] = eligible[8] = eligible[22] = 1; }
        if (strcmp(mode, "fallback-text") == 0) gResearchEconomyShop[0].row_text = NULL;
        if (strcmp(mode, "balance-9999") == 0) { write_u16(G_OWNER + OWNER_BALANCE, 9999); memcpy(before, storage, sizeof(storage)); }
        open_ok();
        if (strcmp(mode, "nothing") == 0) { input(MENU_NOTHING); assert(state.menu_active && destroyed == 0 && resumed == 0); input(MENU_B); closed(0xFFFF, RESEARCH_RESULT_CANCELLED); }
        else if (strcmp(mode, "b-cancel") == 0 || strcmp(mode, "fallback-text") == 0 || strcmp(mode, "balance-9999") == 0) {
            if (strcmp(mode, "balance-9999") == 0) assert(memcmp(state.balance_text, "RP:9999\xFF", 8) == 0);
            input(MENU_B); closed(0xFFFF, RESEARCH_RESULT_CANCELLED);
            assert(ResearchEconomy_PurchaseSelected() == RESEARCH_RESULT_INVALID && purchase_calls == 0);
        } else if (strcmp(mode, "negative") == 0) { input(-3); closed(0xFFFF, RESEARCH_RESULT_CANCELLED); }
        else if (strcmp(mode, "invalid-row") == 0) { input(6); closed(0xFFFF, RESEARCH_RESULT_INVALID); }
        else if (strcmp(mode, "last-cancel") == 0) { for (unsigned i = 0; i < 4; ++i) input(5); assert(state.page == 4 && cursor_rows == 4); input(3); closed(0xFFFF, RESEARCH_RESULT_CANCELLED); assert(opened == 5 && removed == 5); }
        else if (strcmp(mode, "next-window-fail") == 0) { window_fail = 1; input(5); closed(0xFFFF, RESEARCH_RESULT_ENGINE_REJECTED); assert(opened == 2 && removed == 1); }
        else if (strcmp(mode, "filtered") == 0) { assert(state.eligible_count == 3 && state.eligible[0] == 2 && state.eligible[1] == 8 && state.eligible[2] == 22); input(2); closed(22, RESEARCH_RESULT_SELECTED); }
        else if (strcmp(mode, "balance-zero") == 0) { assert(memcmp(state.balance_text, "RP:0\xFF", 5) == 0); input(MENU_B); closed(0xFFFF, RESEARCH_RESULT_CANCELLED); }
        else { fprintf(stderr, "unknown case\n"); return 2; }
    }
    puts("PASS_CANONICAL_HOST_BOUNDARY_NOT_NATIVE"); return 0;
}
