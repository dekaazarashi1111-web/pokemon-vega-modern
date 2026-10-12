/* Script callnativeはr0をLastResultへコピーしない。専用の結果slotへ返す。
 * pending所有API以外の施設状態、効果bit、party、saveには書き込まない。
 * linkerは実sp072/FacilityRuntimeと共通の0x02037004へこのsymbolを解決する。
 */
#include "circus_admission.h"

extern volatile cfru_u16 VegaCircusScriptResult;

void VegaCircusAdmissionSelectScript(void)
{
    VegaCircusScriptResult = (cfru_u16)VegaCircusAdmissionSelectPending();
}
