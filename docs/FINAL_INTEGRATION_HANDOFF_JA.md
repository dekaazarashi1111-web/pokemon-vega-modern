# PR #16 最終統合・受入・引き渡し

## 判定

**製品完成ではない。** 一つのStage84候補の生成・7領域回帰・採用済みP06の新候補上の観測・工程受入への接続・正逆パッチ生成を完了した。未受入のnative経路、P07採用行、archive economy、clean ROMからの最終再生成、公開済み原本の保護問題が残る。full_p03/p05/p06/p07、release_readyはfalseを保持する。

現在の入口は `content/modernization/p08_remaining_work.json`。元の要求、対象機能、合格条件、成功証拠／再開点はこの一覧と `p08_final_candidate_acceptance.json` へ接続する。Stage77/81の古い未完了一覧を現在の残件へ再輸入しない。

開始HEAD: `72ff2e57f3f8cb2654c22d836597e89bfa5b009d`。
実ROM検証HEAD: `4d7365c7144cdda3ee15fca7c5cb365c87e7621d`。
成功run: `34477344071`。candidate、7 domain、merge、原本保管jobの計10jobが成功。最後の保管jobにはZIPのgitignore漏れがあったため、引き渡しjobで原本を明示stageし、`git ls-files --error-unmatch` で追跡状態も検査する。実ROM試験の成功と原本の永続保管の成立は別々に確認する。

## 固定した候補

|項目|値|
|---|---|
|Stage|84（統合候補、リリース未承認）|
|size|33,554,432 bytes|
|SHA-256|`55cf145e7dd1c8e2568fe9c733b597f8c4bc3d31b7d6fa233a7b4821d1b62c3b`|
|CRC32|`5D95817C`|
|plan fingerprint|`9cdfdd8fa5c0177e8f2278ebadc1e51647fdc6b184339939cd27c973d02745d4`|

Stage80→既存のStage81 PP修復→Stage82 archive UI修復→Stage83採用P06→Stage84空き技PP修復を、固定済みrecipeで合成する。Stage84そのものへ新しいROM差分は加えていない。Stage83との差はMOVE_NONEのPPを35から0にする1byte。既存のStage84技忘れ12件の原本は同じ候補SHAの成功である。

P06はジバクン（stable species 220）の通常特性1をふしぎなまもり→のろわれボディ、通常特性2をかげふみ→おみとおし、カモナイツ（373）の攻撃75→45。計2種・3field・3byte。ID、隠れ特性、習得表、save ABIを変更していない。

## 受入の対応

P06旧原本run `34444010444` / artifact `10138991421` / 原本SHA `2a9c4fcc3663c92a7ba0a0be0bf6da1f570bd0200ce9afcdfef3598875a97d08` を独立再検証した。旧8件を新候補の成功に改称していない。

新runではStage84上で既存個体4件＋新規個体4件、計8 process／24 coreを新規実行。保存slot、独立能力値計算、通常アメによる再計算、通常保存、別coreのContinue、100byte個体一致を確認した。7種のhost書込API禁止を物理的な負例で確認している。採用特性の戦闘効果そのもの・適用される工程UI受入まで成功したとは扱わない。

7領域（P02、Mega shop、Floette、P03、Mega runtime、battle policy、P05）は同一Stage84を新規実行し、既存validatorを維持したまま結果を統合した。P03などのdirect-call境界はそのまま明記されている。7領域PASSを、通常捕獲や施設受付を含む全経路PASSとは読み替えない。

既存のbirth/hatch 8件、capacity 3件、Mega 42件、relearner 46件、forgetting 12件を保持する。前4群はStage82上の原本として保持し、新候補上のnative成功と自動的に同一視しない。変更影響の対象を特定して必要な再実行だけを足す。新たな全組合せ試験を受入条件にはしていない。

## 仕様判断

### P07 双方向技配布

照合した要求は `07_extra_learnsets.txt`「今回の依頼」1～5、`Vega_8工程_実行指示集.md` 工程7、repositoryの `p07_layered_learnset_contract.json`、P06採用元2文書、Libraryの `vega_stage61_competitive_audit_20260904.md` §6～7である。

**確定できた仕様**: 通常種→ベガ技、ベガ種→通常技は別レイヤー。P03の原作基準を上書きせず、対象species/form・move・経路・時期・制限・意図を明示する。進化前持ち越しと直接習得、孵化と共有タマゴを区別する。供給・料金・解禁・UI・キャンセルを接続する。所持済み4技やtrainer/facility手持ちを一括変更しない。

**資料だけで未確定**: 具体的な採用行と習得方法・時期。監査の「通常1技／注目2技」「高影響1または中影響2」「役割別上限」は提案であり、別監査の点数案とも一つの採用表にはなっていない。カモナイツには「つるぎのまいを外すか、はねやすめを外す」という選択肢がある。旧ROMの過剰配布の集計を採用表に転用しない。表が空だから要求なし／不要、とは判断していない。

選択肢A: 明示した最小whitelistを採用する。行には `species/form key, move key, route, timing, restrictions, supply/cost/unlock, rationale` を揃える。
選択肢B: 監査提案をより広い配布計画へ具体化したうえで、その行を採用する。
**推奨A**。P03原作基準と既存Vega非対象習得を維持し、採用された独自差分だけを追加する。監査提案から無断で全種配布・技削除・追加弱体化はしない。

### archive economy

該当箇所: `config/modernization_p03_stage74_supply.json` の `runtime.unlock` / `runtime.economy`。現実装は殿堂入りflag `0x082C`、わざメモリー347から、料金0、`PROVISIONAL_REPLACEABLE`。P03実行指示は供給を必要とする一方、大きな解禁・価格変更には確認を要求している。暫定実装を自動的に正式採用とは扱わない。

選択肢A: 現在の「殿堂入り後・わざメモリー・無料」を正式採用する。
選択肢B: 解禁条件、通貨、価格、供給NPC/場所を指定して置換する。
**推奨A**。既に検証した経路を保ち、追加の経済設計を発生させない。承認前に価格や解禁を変更しない。承認後もStage74の原本は不変とし、現在の採用判断を別レイヤーへ記録する。

P06の監査194行はすべて採用された変更ではない。採用済み3項目以外は明示採用まで保留であり、全194行の調整や全組合せ試験を完成条件に追加しない。

## 再現と確認

固定GitHub toolchainは `infra/toolchain_manifest.json` と `infra/setup_github_actions.sh` に従う。実行は同じPR branch。ROM/save原本は公開artifactへ入れない。

```sh
bash infra/setup_github_actions.sh --install
python3 scripts/modernization_final_integration.py prepare
python3 scripts/modernization_final_integration.py plan
python3 scripts/modernization_final_integration.py package .local/my-stage84-handoff
python3 scripts/run_modernization_stage82_github_domain.py prepare
python3 scripts/run_modernization_p06_decided_e2e.py --candidate-stage 84 --output-directory .local/my-p06-stage84 --jobs 4
python3 scripts/record_modernization_final_acceptance.py
```

domain再実行は `modernization_final_integration.py run-domain --domain <id> --output-directory .local/<owned-directory>`、検査は `validate-domain`。全手順の実例は `.github/workflows/modernization-final-integration.yml`。

**この再現経路の入力は固定Stage80である。clean ROMからの全工程再生成が成立したとは報告していない。** P08原指示のclean ROM起点2回再生成とclean-to-final配布パッチは未完了。既存のprivate-runtime/full-unit bridgeも今回依頼したが、最終HEADでの全unit成功を確認するまでは完了条件を閉じない。

## 成果物と導入・戻し方

配布するのは4個のBPS、各SHA/入力/出力を持つmanifest、適用器、説明、SHA256SUMSのみ。ROM・save・秘密入力は含めない。`stage80-to-stage84.bps` と `stage83-to-stage84.bps` は指定SHAの開発候補専用で、Stage62／clean ROMには使えない。

まずエミュレータを通常保存して完全終了し、現在遊んでいるROMとそのバッテリーsaveを**組で別フォルダにコピー**し、各SHA-256を記録する。ステートsaveだけをバックアップにしない。同期アプリの上書きにも注意する。今回の候補は未承認なので、本番プレイへ切り替えず、検証専用フォルダとsaveの複製だけを使用する。

パッチ展開先で、既存ファイルを指定しない新しい出力名を使う。Python 3.10以上を使用する。

```sh
python3 apply_modernization_stage84_patch.py --patch stage80-to-stage84.bps --source /absolute/path/to/copied-stage80.gba --output /absolute/path/to/test-folder/stage84.gba
```

適用器はpatch/source/target SHA-256を全照合し、既存出力、save拡張子、symlink、hardlinkを拒否する。saveへアクセスしない。Stage62のパスへ出力しない。

戻す場合はエミュレータを完全終了し、バックアップした元ROMと**対応する変更前saveの組**へ戻す。新候補側のsaveを元のsaveへ上書きしない。逆BPSは開発ROM byteをStage80/83へ戻すもので、save内の進行・習得を巻き戻すものではない。逆パッチも新しい出力先にのみ適用する。ROMの異なるステートsaveをロードしない。

## 保護と再開点

repositoryは実査時public。GitはStage78 ROM、Stage80 ROM、テストseed saveの3ファイルを既に追跡しており、全index guardはFAIL。新規追加対象だけのguard成功と区別する。公開範囲変更・原本削除・履歴改変は実行していない。対応方法は所有者の明示承認が必要。Stage62、実プレイsave、active_play_baseline、PR mergeは変更していない。

再開は `p08_remaining_work.json` の各 `resume` から行う。優先は、既存成功を保持したP03進化/フォーム習得のnative保存経路、P05通常取得から戦闘と実施設受付、P06採用特性の戦闘効果・適用UIの受入。P07/料金の未決判断に依存しない。Circusの前回source auditは限定した資料群であり、実施設が存在しないことの証明ではない。

新しいROM変更が必要になった場合は候補SHAを改めて固定し、影響する検査を実行する。この文書のStage84成功を別ROMの成功へ改称しない。PR #16を継続し、別PRや別セッションで同じ実装を重複させない。
