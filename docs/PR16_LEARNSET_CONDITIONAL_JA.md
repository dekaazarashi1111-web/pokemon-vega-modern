# Issue19: 条件consumerの接続（作業中）

USER-20260922-LEARNSET-CONDITIONAL。起点はea5bb85eb1f2fc8b04ddb30818d34fcf75b51a8f、受入済み初期技/通常level-up候補e168c06f。

## 実装checkpoint

既存PLR1を変更せず、親/Floetteの受入済み10poolを全byteコピーするPLC1を追加。1671 ownerのうち1483学習owner、188保全ownerを区別する。egg/進化/思い出し/shared egg/tutorは5列に分離し、owner/consumerタグ、境界、move ID、上位tutor bitを検査する。

進化候補を先に通知し、進化後levelに一致する通常技を続ける。思い出しは進化技・該当level以下・思い出し専用技を重複排除し、既存4技を除外する。容量不足時は出力を部分更新しない。元のarchive、姿変化、進化前持越し、条件付き孵化を自動付与経路にしない。

追加した合成境界41試験はローカルPASS。PLC1は115282 bytes、direct egg4356/進化342/思い出し295/shared egg5027/既存tutor互換740bit。これは候補読取層の検証であり、ゲームcallsite/新ROM/実操作E2Eの受入ではない。

## 次の区切り

実際の保存hook/ABIを照合して条件consumerを接続し、追加host/ARM/ROM検証を記録する。旧受入30試験・通常level-up probe・原本収集は再実行しない。新Wikiと影響操作E2Eはその後。最終記録時に固定引継ぎMD/JSONとappend-only両ログを同期する。merge/release/baseline切替は行わない。
