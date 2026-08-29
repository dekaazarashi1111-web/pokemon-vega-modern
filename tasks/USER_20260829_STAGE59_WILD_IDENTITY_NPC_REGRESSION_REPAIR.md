# USER-20260829-STAGE59-WILD-IDENTITY-NPC-REGRESSION-REPAIR

## 目的

Stage58完全workspaceと軽量Stage59診断bundleを比較し、繰り返し報告される野生個体のSpecies／default nickname不整合と、NPC／menu診断の信頼性を修復する。推測patchではなく、exact-ROMの生成入口・通常入力・既存QA saveで再現可能な契約を追加する。

## 入力

- Stage58 ROM: 33,554,432 bytes、SHA-256 `501c3fdda825abfb167bc62da63c189671fa2f026d7b866001fbfbac36700a0c`
- Stage58標準QA save: 131,072 bytes、SHA-256 `f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb`
- clean FireRed JPN Rev.0: 16,777,216 bytes、SHA-256 `1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486`
- ユーザー提供の軽量Stage59診断bundleとStage58完全workspace。原本ZIP、ROM、saveは変更・Git追跡しない。

## 調査結果

- 軽量bundleの`stage59_source_changes.patch`は0 byteで、source修正を含まない。buildはclean ROM不足で失敗し、完全workspace内のmGBA／Stage58 ROM／QA saveを発見できていなかった。
- `npc_save_static_audit.json`は全byte `0xFF`の旧Stage56 saveを対象にし、script label解決結果も空だった。そのため`unresolved_labels=1588`やoverlap 260は有効なruntime defect件数ではない。
- Stage57はCollection Supply内のSpecies書換え3 callsiteを原子的Species＋default nickname同期へ修正し、地上／水上生成をwrapしていた。一方、釣りと隠し／scanner生成には共通の最終canonical-name postconditionがなかった。
- 従来のRoute505自然遭遇66回はSpecies／levelを確認していたが、自然生成個体のcanonical nicknameを件数契約として検査していなかった。
- Stage58 exact ROMと標準QA saveでは、非Collection 9 menu＋Collection 14 hostのopen／cursor／A／B／field復帰を再現できた。常時発生するNPC menu不具合は観測できなかったため、NPC scriptへの推測変更は行わない。

## 実装

- Stage59 runtimeで地上／水上、釣り、隠し／scannerの3生成入口をwrapし、成功時のenemy party default nicknameを現在Speciesのcanonical名へ同期する。
- 地上／水上はStage57の既存初期技同期を保持する。釣り／隠しは研究profile等の特殊技を壊さないため、Speciesと4 move slotを変えず名前だけ同期する。
- 3 hookをexpected bytes付きで置換し、Collection Supplyの原子的Species callsite 3件を継承確認する。
- Route505 runnerへ自然遭遇のcanonical nickname検査と独立counterを追加する。通常は従来どおり66回、focused gateは`S57_ROUTE505_ENCOUNTER_TARGET`で縮小可能にする。
- 全1620 Speciesの破損名復元、3生成方式、自然歩行／戦闘／逃走、fresh／QA-save menuをStage59 exact ROMへ固定する。

## 完了条件

- Stage59 build／checkがbyte決定的で、declared span外変更0、allocator overlap 0。
- Stage58差分BPSとclean直接BPSがStage59 exact ROMへ完全往復する。
- 全1620 Speciesでcanonical nicknameへ復元し、Speciesと4 move slotを保持する。
- 地上／水上96、釣り96、隠し1の計193生成でSpecies範囲・戻り値・canonical nicknameを確認する。
- Route505の通常入力から野生戦闘へ入り、party／battle identity、逃走、field復帰を確認する。
- fresh saveとStage58標準QA saveの双方で、10 menu callsite、非Collection 9 overlay、Collection 14 hostを全件確認する。
- ROM／saveを配布artifactへ含めず、source差分、BPS、metadata、監査、検証証跡だけを渡す。
