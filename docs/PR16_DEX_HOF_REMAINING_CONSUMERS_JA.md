# 737親からの実consumer最小型batch

対象は同branchの0641候補にある旧egg874参照。前Summary checkpointの737分類/137未知を独立の親として固定し、実登録callbackまたはtableと具体的consumer経路が閉じる最小窓だけを追加する。

## 受入の境界

- 実constructorのstore、dispatcherのload、有限state/文字列消費を命令意味から結ぶ。
- opaque ABI境界のscalar条件と、その時点で必要なlive RAM射影を明示する。自然playで全条件が常に成立するとは主張しない。
- 4byteの未知word全体を包含する必要最小型だけを分類する。関数名やアドレス範囲だけの分類、hit targetを指す実pointerだと決め付ける分類は行わない。
- 旧独立最終source reviewは未実施を保持する。新しいsourceのみ検査する。

## 新しい3つのconsumer根

1. RFU: hit `0x080FC36B` を包含する `0x080FC36A/6byte`。実LinkLeader constructor `0x080FCBE8` のcallback storeから、同じlman登録を読むmanager/watcher、parameter writer、LDR/BX、完全なBLと次branchへ接続する。後のmanager呼出・wireless出力は有限の明示条件であり、自然通信成功を主張しない。
2. Fame Checker: hit `0x0812DAEF` を包含する `0x0812DAEE/6byte`。実constructor `0x0812CB94` のAllocZeroed36/store/登録、main dispatcher、setup0..6、16record列挙のperson writer、6sprite loopから完全なBLへ接続する。API外側のItemMenu呼出やBLの復帰は未証明。
3. Credits: `0x083E263E/4byte` と `0x083E2767/4byte`。special421の実slotからconstructor/store/main登録、script index0..33の実producer、title/names table、現installed printer hook、実LDRBへ接続する。隣接2文字列を跨ぐ第1窓とnames内の第2窓を、3文字列94byte・EOSを含む実消費で覆う。default font pointer、成功allocation、map/mon/fade/window/glyphの有限条件は外部効果の証明ではない。

これらは新scopeの必要最小型候補であり、現0641での正式測定結果は専用checkpointを正本とする。旧06c5診断結果だけでは分類を昇格しない。

## 次の未結合根

- Helpの `0x0841B41A` と `0x0841B44C` は実table `0x0841B780` / consumer `0x0812BE18` までの限定調査。Help拡張hookとcontext/topic producerの合成は未完で、新分類に含めない。
- Creditsの `0x083E239B/24C3/2563/258F` はalign paddingを跨ぎ、今回の文字列readだけでは全4byteを覆わないため未知のまま。
- GPU `0x080A006F` の外側登録root、`0x08118D03` の外側callerとdata+0x13 writerは未特定のまま。名前や近傍から補完しない。

## 保存する証拠

619原本と全12親namespaceを23個の独立入力から復元し、118changes/108witness、全874hitのidentityと、旧737 accepted/残unknownの全fieldを保持する。旧証拠の複製は新deltaに入れない。全133曲/50assetと新consumer窓の役割交差を再照合する。

## 容量と未完

unknown最大access、間接参照完全性、退役、owner移管が未証明の間は旧egg15118byte全域を保護し、安全容量は0。115actual owner、52save owner、残804byteを保持する。controller既測定6528byteは未配線で、heap13352をstock保存退避53300入口へ跨がせない。

正式ROM・Save101は変更しない。全体図鑑修復、シオウの通常回復・保存・独立coldContinueは未完。無変更の旧suite/nativeは再走しない。全雑魚ごとのcheckpointも行わない。

## 測定と公開

新sourceの専用試験を先に検査し、閉じられる根を一回の現0641再構築へまとめる。source/最小address-size-SHA/textのみを公開する。ROM断片/rawhex/ROM/runtime/入力save/runner/credentialは成果に含めない。閉じた非空success setの全size/SHA/LFをcommit前とupload前に検査し、hidden/symlink/未知fileを拒否する。
