/* 私有RAM isolated probe用。controller本体・ROM hook・保存ownerを変更しない。
 * ARM ABIの初期化と結果の整数化のみ。callback本体はnative側trusted model。
 * 住所とmetadata契約はmgba_pr16_dex_hof_controller.cと対で使う。 */
#include <stddef.h>
#include <stdint.h>
#include "overlays/hof_journal/hof_transaction.h"

#define HPC_WORK 0x02008000u
#define HPC_SECTOR 0x02010000u
#define HPC_HOF 0x02012000u
#define HPC_OPS 0x02018000u
#define HPC_RESULTS 0x02018100u

/* 既存ROMの命令を書き換えず、実行前にnative側が捕捉するThumb sentinel。 */
#define HPC_READ 0x08000101u
#define HPC_ERASE 0x08000111u
#define HPC_PROGRAM 0x08000121u
#define HPC_SELECT 0x08000131u
#define HPC_VALIDATE 0x08000141u
#define HPC_PREPARE 0x08000151u

_Static_assert(sizeof(uintptr_t)==4,"ARM32 probe only");
_Static_assert(sizeof(HT_Workspace)<=0x8000u,"workspace bound");
_Static_assert(sizeof(HT_Ops)<=0x100u,"ops bound");
_Static_assert(sizeof(HT_Main)<=32u,"main descriptor bound");

int HPC_Init(void)
{
 HT_Workspace *w=(HT_Workspace *)(uintptr_t)HPC_WORK;
 HT_Ops *o=(HT_Ops *)(uintptr_t)HPC_OPS;
 uint32_t *out=(uint32_t *)(uintptr_t)HPC_RESULTS;
 unsigned i;
 for(i=0;i<sizeof(*w);i++)((uint8_t *)w)[i]=0;
 for(i=0;i<sizeof(*o);i++)((uint8_t *)o)[i]=0;
 w->sector=(uint8_t *)(uintptr_t)HPC_SECTOR;
 w->hof=(uint8_t *)(uintptr_t)HPC_HOF;
 for(i=0;i<HT_SECTOR_SIZE;i++)w->sector[i]=0;
 for(i=0;i<HJ_PAYLOAD;i++)w->hof[i]=0;
 o->user=0;
 o->read_sector=(int (*)(void *,unsigned,uint8_t *))(uintptr_t)HPC_READ;
 o->erase_sector=(int (*)(void *,unsigned))(uintptr_t)HPC_ERASE;
 o->program_byte=(int (*)(void *,unsigned,unsigned,uint8_t))(uintptr_t)HPC_PROGRAM;
 o->select_main=(int (*)(void *,HT_Main *,uint8_t *))(uintptr_t)HPC_SELECT;
 o->validate_main_sector=(int (*)(void *,const HT_Main *,unsigned,const uint8_t *))(uintptr_t)HPC_VALIDATE;
 o->prepare_main_sector=(int (*)(void *,const HT_Main *,const HT_Main *,unsigned,const uint8_t *,uint8_t *))(uintptr_t)HPC_PREPARE;
 /* native側のsizeof(pointer)や構造体paddingをARMへ持ち込まない。 */
 out[0]=0x48504331u;
 out[1]=(uint32_t)sizeof(*w);
 out[2]=(uint32_t)sizeof(*o);
 out[3]=(uint32_t)sizeof(HT_Main);
 out[4]=(uint32_t)offsetof(HT_Main,counter);
 out[5]=(uint32_t)offsetof(HT_Main,base);
 out[6]=(uint32_t)offsetof(HT_Main,first);
 out[7]=(uint32_t)offsetof(HT_Workspace,result);
 out[8]=(uint32_t)offsetof(HT_Result,main);
 out[9]=(uint32_t)sizeof(HT_Result);
 out[10]=(uint32_t)offsetof(HT_Workspace,journal);
 out[11]=(uint32_t)offsetof(HT_Workspace,selected_journal);
 return 0;
}

int HPC_ReadResult(void)
{
 const HT_Workspace *w=(const HT_Workspace *)(uintptr_t)HPC_WORK;
 uint32_t *out=(uint32_t *)(uintptr_t)(HPC_RESULTS+64u);
 /* tools/pr16_hof_controller_host.c:HC_Result先頭9整数と同じ順序。 */
 out[0]=w->result.main.counter;
 out[1]=w->result.main.base;
 out[2]=w->result.main.first;
 out[3]=w->result.has_hof;
 out[4]=w->result.has_journal;
 out[5]=w->result.pending;
 out[6]=w->result.route;
 out[7]=(uint32_t)w->result.epoch;
 out[8]=(uint32_t)(w->result.epoch>>32);
 return 0;
}
