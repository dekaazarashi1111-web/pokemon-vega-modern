# Issue19 Eternal採用差分とhost owner gate

正本: `content/modernization/pr16_learnset_floette_checkpoint.json`。原本抽出と採用差分は別runで受入済み。旧payload checkpointを上書きしない。

## 完了した範囲
固定ZIPの `legendsza:0670.05`、Eternal1029の37経路（level13、進化時1、TM23）だけを明示採用。P01 apply=falseは履歴のまま保持する。贈呈種族・場所・level50・一度限りflag・既存個体4技は変更しない。進化時ムーンフォース546をlevel0や贈呈初期技へ平坦化しない。Side Change/placeholder/追加overlayは0。

親128352経路・親binaryは変更/再生成せず、計128389経路として別arenaの差分を構成。全15039 indexのうち1029の9枠だけを置換し、残る15030枠は同一byte。machine23経路の11件は受入catalogへ対応し、12件は不足技archiveへ隔離する。archiveへの記載は実供給の受入ではない。Tutorは容量64のうち親で観測済み54slotだけを扱い、欠けた10slotを創作しない。

## 実装と検証
`tools/pr16_learnset_floette.py` が明示裁定を検証して差分/複合index/owner policyを生成する。`src/modernization/pr16_learnset_owner.c` は1483学習owner、31非戦闘identity、157戦闘持越しを区別する。未知入力は拒否し、base種へfallbackしない。進化前持越し/姿条件は専用consumer未接続を返す。通常egg/shared egg/特殊孵化の条件を満たしたとみなすAPIではない。個体・技・PP・saveへの書込口はない。

新44試験、独立2プロセスの全hash、ローカル/Actions一致、原本から別実装で算出した差分全byte、実owner policyを使うhost Cの1671×9=15039 query、入力byte/mtime不変を受入。ROM/mGBA/nativeの実行はこの受入に含まれない。受入済み原本/旧54試験/孵化照合は再実行していない。

## 再開時の注意
親artifactの既存poolと新artifactの `floette.*.bin` は別arena。`resolve_owner` の `arena` とspanを明示使用する。旧 `pr16_learnset_payload_checkpoint.json` に残る1029採用待ちは過去の親状態であり、今の未完ではない。配置前成果をinstall_ready=trueへ変更してはならない。

## 次の未完
ゲーム側callsiteへowner gateと専用条件consumerを接続し、ROMの割当/pointer/容量、archive12技を含む物理供給を検証する。旧 `docs/wiki/p08-candidate-46487d98/**` は上書きせず、新ROMの別Wikiを作成する。Eternal新規贈呈/既存個体の4技保全・該当学習/進化/孵化/姿変化など、変更影響だけをnativeで受入する。Issue19全体、merge、release、active baseline切替は未完/未実施。
