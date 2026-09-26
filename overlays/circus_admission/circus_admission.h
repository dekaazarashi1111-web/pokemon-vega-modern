#ifndef VEGA_CIRCUS_ADMISSION_H
#define VEGA_CIRCUS_ADMISSION_H

#include "../cfru/integration.h"

enum {
    VEGA_CIRCUS_FACILITY_NUMBER = 3,
    VEGA_CIRCUS_STATE_NUMBER = 0,
    VEGA_CIRCUS_ADMISSION_REJECTED = 0,
    VEGA_CIRCUS_ADMISSION_SELECTED = 1
};

/* 受付で用意した未消費の施設commandだけをCircusへ切り替える。
 * 返値は接続準備の成否。実入場・効果抽選・戦闘の受入を意味しない。
 * 呼出元は失敗時に既存の取消/party復帰経路へ戻ること。
 */
cfru_u8 VegaCircusAdmissionSelectPending(void);

#endif
