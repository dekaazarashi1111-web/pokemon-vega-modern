/* 128 KiB保存用rollback journal。ROMへの配置/接続は別の受入が必要。 */
#ifndef VEGA_HOF_JOURNAL_H
#define VEGA_HOF_JOURNAL_H
#include <stdint.h>
#define HJ_SIZE 256u
#define HJ_PAYLOAD 7936u
#define HJ_TEAM 120u
#define HJ_TEAMS 50u
#define HJ_TAIL 6000u
#define HJ_APPEND 1u
#define HJ_SHIFT 2u
#define HJ_INITIAL 3u
/* バッファの全サイズ、差分、非wrap epochを先に検査。失敗時out不変。 */
int HJ_Build(uint8_t out[HJ_SIZE], const uint8_t old[HJ_PAYLOAD],
 const uint8_t next[HJ_PAYLOAD], uint32_t counter, uint64_t epoch,
 const uint8_t old_sha[32], const uint8_t new_sha[32], const uint8_t source_sha[32],
 unsigned kind, unsigned slot);
int HJ_Validate(const uint8_t journal[HJ_SIZE]);
/* SHA照合は呼出側必須。CRCはjournal破損検出でありpayload認証の代用ではない。 */
int HJ_Rollback(uint8_t out[HJ_PAYLOAD], const uint8_t next[HJ_PAYLOAD],
 const uint8_t journal[HJ_SIZE]);
#endif
