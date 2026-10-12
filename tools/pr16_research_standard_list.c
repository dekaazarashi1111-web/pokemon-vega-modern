/* 受付専用の標準リスト。保存領域・既存research volatileを所有しない。 */
typedef unsigned char u8;
typedef signed char s8;
typedef unsigned short u16;
typedef signed short s16;
typedef unsigned int u32;
struct SL_TaskState { void (*func)(u8); u8 active, prev, next, priority; s16 data[16]; };
struct SL_Window { u8 bg, left, top, width, height, palette; u16 base; };
#ifdef SL_HOST_TEST
extern struct SL_TaskState sl_tasks[16];
extern volatile u16 sl_result;
#define TASKS sl_tasks
#define RESULT sl_result
#else
_Static_assert(sizeof(struct SL_TaskState) == 40, "task ABI");
_Static_assert(sizeof(struct SL_Window) == 8, "window ABI");
#define TASKS ((volatile struct SL_TaskState *)0x030050D0u)
#define RESULT (*(volatile u16 *)0x02037004u)
#endif
extern u8 SL_CreateTask(void (*)(u8), u8);
extern void SL_DestroyTask(u8);
extern u16 SL_AddWindow(const struct SL_Window *);
extern void SL_RemoveWindow(u8);
extern void SL_CopyWindow(u8, u8);
extern void SL_PutWindow(u8);
extern void SL_FillWindow(u8, u8);
extern void SL_Print(u8, u8, const u8 *, u8, u8, u8, void *);
extern void SL_Schedule(u8);
extern void SL_DrawFrame(u8, u8);
extern void SL_ClearFrame(u8, u8);
extern void SL_LoadFrame(u8, u16, u8);
extern u16 SL_BaseTile(void);
extern u8 SL_Cursor(u8, u8, u8, u8, u8, u8, u8);
extern s8 SL_Input(void);
extern void SL_Sound(u16);
extern void SL_Suspend(void);
extern void SL_Resume(void);
#include "pr16_research_standard_list_rows.h"
enum { SL_BUSY = 0xffff, SL_ERROR = 0xfffd, SL_CANCEL = 2 };

/* 状態は当該taskのwindowとdebounceだけ。終了時は所有資源を一度だけ解放。 */
__attribute__((used, noinline))
void SL_Task(u8 id)
{
    s8 choice;
    u8 window;
    if (id >= 16 || !TASKS[id].active || TASKS[id].func != SL_Task)
        return;
    if (TASKS[id].data[1] > 0) { --TASKS[id].data[1]; return; }
    choice = SL_Input();
    if (choice == -2) return;
    window = (u8)TASKS[id].data[0];
    if (window != 255) {
        SL_ClearFrame(window, 0);
        SL_RemoveWindow(window);
        SL_Schedule(0);
        TASKS[id].data[0] = 255;
    }
    SL_DestroyTask(id);
    SL_Sound(5);
    RESULT = choice == -1 ? SL_CANCEL : (choice >= 0 && choice <= 2 ? (u16)choice : SL_ERROR);
    SL_Resume();
}

__attribute__((section(".text.SL_Open"), used, noinline))
void SL_Open(void)
{
    struct SL_Window w;
    u8 id, i;
    u16 window;
    RESULT = SL_ERROR;
    for (i = 0; i < 16; ++i)
        if (TASKS[i].active && TASKS[i].func == SL_Task) return;
    id = SL_CreateTask(SL_Task, 0x50);
    if (id >= 16) return;
    TASKS[id].data[0] = 255;
    TASKS[id].data[1] = 2; /* 会話終了に使ったAを新リストへ漏らさない。 */
    /* freestanding ARMで暗黙memcpyを発生させない。 */
    w.bg = 0; w.left = 9; w.top = 1; w.width = 20; w.height = 6; w.palette = 15;
    /* 0x214..0x21c are frame tiles, not menu pixel storage. */
    w.base = 0x280;
    window = SL_AddWindow(&w);
    if (window >= 255) { SL_DestroyTask(id); return; }
    TASKS[id].data[0] = (s16)window;
    SL_LoadFrame((u8)window, SL_BaseTile(), 0xe0);
    SL_FillWindow((u8)window, 0x11);
    SL_DrawFrame((u8)window, 0);
    SL_PutWindow((u8)window);
    for (i = 0; i < 3; ++i)
        SL_Print((u8)window, 2, SL_ROWS[i], 8, (u8)(1 + i * 16), 0, (void *)0);
    SL_Cursor((u8)window, 2, 0, 1, 16, 3, 0);
    SL_CopyWindow((u8)window, 3);
    SL_Schedule(0);
    RESULT = SL_BUSY;
    SL_Suspend();
}
