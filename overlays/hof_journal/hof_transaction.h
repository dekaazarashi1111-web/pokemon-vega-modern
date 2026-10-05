/* 128 KiB実geometry用controller。ROM配置/既存owner接続の受入は別途必要。 */
#ifndef VEGA_HOF_TRANSACTION_H
#define VEGA_HOF_TRANSACTION_H
#include <stdint.h>
#include "hof_journal.h"

#define HT_SECTOR_SIZE 4096u
#define HT_MAIN_SECTORS 14u
#define HT_FLASH_SECTORS 32u
#define HT_JOURNAL_OFFSET 0xEC0u

/* callbackは成功時1、失敗時0。controller実行中の再入/並行saveは禁止。 */
typedef struct {
 uint32_t counter;
 uint8_t base;                 /* 0又は14、counter parityと一致 */
 uint8_t first;                /* logical0のbank内physical位置 */
} HT_Main;

typedef struct {
 void *user;
 int (*read_sector)(void *user, unsigned sector, uint8_t out[HT_SECTOR_SIZE]);
 int (*erase_sector)(void *user, unsigned sector);
 int (*program_byte)(void *user, unsigned sector, unsigned offset, uint8_t value);
 /* 既存S61E/MDXを含む完全main選択。新journalの不正で旧bankへfallbackしない。
  * flash変更禁止。sectorは作業用。selectorは両bank/世代曖昧性も解決する。 */
 int (*select_main)(void *user, HT_Main *out, uint8_t sector[HT_SECTOR_SIZE]);
 /* 選択済/生成済sectorに既存owner検証を追加する。stock footer等はC側でも検査。
  * 全世代/複数sectorにまたがる検証はselect_main側にも必要。flash変更禁止。 */
 int (*validate_main_sector)(void *user, const HT_Main *main, unsigned logical_id,
                             const uint8_t image[HT_SECTOR_SIZE]);
 /* 既存writerがsourceからwhole4096byte画像を生成。targetは正確な後継世代。
  * journal==NULLは304byte zero、それ以外はjournal256+zero48をlogical4へ継承。
  * target位置はcontroller所有。flash変更禁止、同一引数で必ず同一画像。
  * commit/normalは全14画像を先に検証しSHAを保存。書込時再生成してSHAを照合。 */
 int (*prepare_main_sector)(void *user, const HT_Main *source, const HT_Main *target,
                            unsigned logical_id, const uint8_t *journal,
                            uint8_t out[HT_SECTOR_SIZE]);
} HT_Ops;

enum {
 HT_OK=0, HT_ERR_ARGUMENT=-1, HT_ERR_IO=-2, HT_ERR_MAIN=-3,
 HT_ERR_JOURNAL=-4, HT_ERR_HOF=-5, HT_ERR_AMBIGUOUS=-6,
 HT_ERR_PENDING=-7, HT_ERR_TRANSITION=-8, HT_ERR_READBACK=-9,
 HT_ERR_PREPARE=-10, HT_ERR_ABSENCE=-11, HT_ERR_CHANGED=-12
};
enum {
 HT_ROUTE_FIXED=0, HT_ROUTE_FIXED_OLD=1, HT_ROUTE_INVERSE=2,
 HT_ROUTE_SCRATCH=3, HT_ROUTE_INITIAL_ABSENCE=4,
 HT_ROUTE_LEGACY_UNCLASSIFIED=5
};

typedef struct {
 HT_Main main;
 uint64_t epoch;               /* selected tokenが無ければ0 */
 uint8_t source_sha[32];        /* selected mainのphysical順全14*4096byte */
 uint8_t hof_sha[32];           /* resolved HOF。absence時はcanonical zeroのSHA */
 uint8_t has_hof, has_journal, pending, route, pending_first;
} HT_Result;

/* SHA streaming stateもcaller所有。大きなstack/static mutable領域を持たない。 */
typedef struct {
 uint32_t h[8], words[16], bytes;
 uint8_t block[64];
 unsigned used;
} HT_SHA256;

typedef struct {
 /* 実サイズ以上・相互非重複のcaller RAM。全callbackがこの領域を破壊しては
  * ならない（引数で明示された出力領域のみ可）。workspace本体とも非重複。 */
 uint8_t *sector;              /* HT_SECTOR_SIZE */
 uint8_t *hof;                 /* HJ_PAYLOAD */
 HT_Result result;            /* 成功時だけ有効、resolved payloadはhofに置く */
 uint8_t selected_journal[HJ_SIZE], journal[HJ_SIZE];
 uint8_t prepared_sha[HT_MAIN_SECTORS][32];
 uint8_t aux_sha[32], old_sha[32], new_sha[32];
 HT_SHA256 sha;
} HT_Workspace;

/* read-only。既存selector→source全SHA→journal→legacyHOF footer/全SHA。
 * pending INITIALのabsenceは既にCRC/source結合されたintentからのみ復元する。
 * journal無しの破損legacy HOFは「absence確定」ではなくUNCLASSIFIEDを返す。 */
int HT_Resolve(const HT_Ops *ops, HT_Workspace *work);
/* pendingを物理rollbackし、復元/erase readback後にだけjournalをretireする。 */
int HT_Recover(const HT_Ops *ops, HT_Workspace *work);
/* nextは7936byteでwork本体/sector/hofのいずれとも重複不可。実行中不変。
 * pendingなら書かずHT_ERR_PENDING。INITIALは明示的なhas-records/loader owner
 * のabsence確認を意味するverified_absence==1のみ許す。破損だけでは許可しない。
 * 全sectorはerase検証→FF8以外program→全像SHA readback→FF8 program→
 * 全像SHA readback。selected main全14とaux30/31は不変。並行writerは禁止。 */
int HT_Commit(const HT_Ops *ops, HT_Workspace *work,
              const uint8_t next[HJ_PAYLOAD], unsigned kind, unsigned slot,
              int verified_absence);
/* 通常save/clone用。pending解決が成功した後にだけprepare callbackを呼び、
 * journal/tokenをそのまま継承する。全14sectorを書きlogical13を最後commit。 */
int HT_Normal(const HT_Ops *ops, HT_Workspace *work);
#endif
