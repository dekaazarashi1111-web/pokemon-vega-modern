/* 実ROM allocatorのread-only admission。runtime接続/排他/heap-readyは別証明。 */
#ifndef VEGA_HOF_HEAP_H
#define VEGA_HOF_HEAP_H
#include <stdint.h>

#define HH_HEADER_BYTES 16u
#define HH_MAGIC 0xA3A3u
#define HH_ARENA_BYTES 13352u
#define HH_RAW_BYTES 13359u
#define HH_ROUNDED_BYTES 13360u
#define HH_ALIGNMENT 8u
#define HH_ROOT_POINTER 0x03000A38u
#define HH_SIZE_POINTER 0x03000A3Cu
#define HH_ALLOC_ENTRY 0x0800295Du
#define HH_FREE_ENTRY 0x08002A09u
#define HH_INIT_ENTRY 0x08002B81u
#define HH_RELOCATION_ENTRY 0x0804B85Cu

enum {
 HH_OK=0, HH_ERR_ARGUMENT=-1, HH_ERR_GEOMETRY=-2,
 HH_ERR_CHAIN=-3, HH_ERR_OOM=-4, HH_ERR_OWNERSHIP=-5
};

typedef struct {
 uint32_t block, raw, arena;
 uint32_t payload;            /* admission前のfree size / 所有検査時のlive size */
 uint32_t allocated;          /* 実allocatorが保持するsize。余り<=31なら全block */
 uint32_t split_block, split_payload; /* split無し/所有検査では0 */
 uint32_t largest_free, free_bytes, blocks; /* 全chainの観測値 */
} HH_Plan;

/* heapはrootに対応する連続size byteの読取り可能な写像。outと非重複。
 * 実機ではvolatileのroot/sizeを読み、同一heapでadmission→Allocを排他的に
 * 行うこと。snapshot/過去の成功は後続Allocの許可にならない。
 * 16byte header: u16 used(0/1), u16 magic, u32 size, u32 prev, u32 next。
 * root.prev==root、末尾next==root。通常blockは物理順/prevを相互検証する。
 * 各範囲/4byte整列/端までの完全被覆/全magic/隣接free無しを検証する。
 * allocator scratch 02020004..0202000Fとheapの重複を拒否する。
 * HH_OK時だけout有効。不成功時はoutをzero化（out alias等の引数不正を除く）。
 * 本関数はheap変更、Alloc、Free、Flash書込み、fixed RAM占有を行わない。
 */
int HH_Admit(const volatile uint8_t *heap,uint32_t root,uint32_t size,HH_Plan *out);
/* rawはAllocが返した未調整pointer。8byte整列後arenaを渡してはならない。
 * 全chainを再検査し、十分なused=1 blockの正確なpayload開始のみ許す。
 * 成功だけでFreeを許さない。root/sizeの同一性と排他/lifetimeも必要。 */
int HH_CheckOwned(const volatile uint8_t *heap,uint32_t root,uint32_t size,
                  uint32_t raw,HH_Plan *out);
#endif
