# 現在のプレイ基準ROM

最終更新: 2026-09-07

この文書は、ユーザーが現在遊ぶROMと、そのROMに対する実機操作・不具合修正の基準を一つに固定する正本である。
新しいstageや候補ROMが生成されていても、ユーザーが明示的に切り替えるまでは本書のROMを使う。
ROM identityの機械可読正本は`config/active_play_baseline.json`とし、本書と同じ変更で更新する。
方針は`LATEST_EXPLICITLY_ADOPTED`であり、ディスク上やGit履歴上の最大Stageを自動採用しない。

## 現在の基準

- 呼称: Stage62 NPC配置整合性修復版
- ローカルROM: `build/stages/62_npc_placement_integrity_repair.gba`
- サイズ: 33,554,432 bytes
- SHA-256: `d97a0d4a6cd6f8f77a1503a5ac6d473b0e94c4892e3d5a94098497ce35cb6e6f`
- CRC32: `73E4FB73`
- ROM内容checkpoint: Stage61 runtime hotfixを継承し、既存NPC 2,830体をimmutable化してStage61が変更した既存316体／77 mapとruntime座標operand 2件を原典へ復元し、明示追加NPC 11体だけを安全な場所へ再配置した。
- iPad配置記録: 2026-09-04（Stage61と別名で同一SHAのROMを配置し、通常プレイsaveをStage62 basenameへbyte同一で引継ぎ）
- 採用記録: 2026-09-07（ユーザーがStage62と今後の明示採用最新版をプレイ基準に指定）
- 状態: ユーザー指定の現行プレイ基準。strict全owner／全会話branch監査完了版ではない。

このROMとStage61から引き継いだ通常プレイsaveはiPadのRetroArch/mGBAへ配置済みである。
以後iPad上で進んだStage62通常プレイsaveを現行saveとして扱い、ユーザーの明示依頼なしにテストsaveで上書きしない。
端末固有の配置先は記録せず、必要時に`docs/IPAD_RETROARCH_MGBA_SAVE_PLACEMENT.md`どおりlive設定から解決する。

## このROMを使う依頼

別セッションでも、次の依頼は明示がない限りすべて機械可読正本が固定する上記SHAのStage62を対象にする。

- Codex対戦
- 対戦後の任意報酬
- WindowsカタログからのPokémon・アイテム送付
- Box 14とWindows間の固有個体移動
- 通常プレイ中に見つかったバグの再現・解析・修正
- iPadへのROM再配置、または現行saveを使う確認

過去Stage、別SHA、未採用の新しい候補ROMを実機操作の対象へ自動選択しない。
ローカルROMが見つからない、またはSHAが一致しない場合は、別ROMで代用せず不一致を報告する。

## Codex対戦・送付の開始条件

`vega-codex-battle`を使う実機セッションでは、最初にread-onlyで次を実行する。

```bash
vega-codex-battle doctor --json
vega-codex-battle session guide --json
vega-codex-battle match status --json
```

ROM identity、runtime、save状態が一致した時だけwriteへ進む。導入済みCLIのprotocolは
機械可読正本を使って上記Stage62のsize／SHA-256／CRC32へ再固定する。
固定filenameではなくCLIが読むprotocolのROM identityを正とする。

現行ROMへCLIを再導入する時は次を使う。installerは`config/active_play_baseline.json`を検証し、
ROMのsize／SHA-256／CRC32とStage番号をprotocolへ再固定してから配置する。
検証用override以外ではROM pathやStage番号を個別指定せず、古いROM identityを手編集しない。

```bash
bash scripts/install_vega_codex_battle_cli.sh
```

- 通常フィールドでのアイテム／Pokémon送付は`bank status`を確認して`bank item`／`bank mon`を使う。
- 対戦結果に紐づく報酬は`reward status`が現在matchの`OPEN`を示す時だけ送る。
- 固有個体の退避／復帰はBox 14を使い、`vault status`確認後に`vault deposit`／`vault withdraw`を使う。
- 各write直前に公開状態を再読し、save、bag、party、box、pendingを手編集しない。

詳細手順は次を正とする。

- `docs/CODEX_BATTLE_OPERATOR_JA.md`
- `docs/WINDOWS_BATTLE_CATALOG_JA.md`
- `docs/WINDOWS_BOX14_VAULT_JA.md`
- インストール済み`vega-codex-battle` skill

## バグ修正時の扱い

1. まず機械可読正本が固定する現行ROMと、ユーザーの現行save／レポート／再現位置を対象にする。
2. 原因候補を絞るためのread-only調査とfocused検証を先に行う。strict全件監査は、ユーザーが依頼した場合だけ再開する。
3. 修正版は別候補として生成し、ユーザーが採用するまでは本書の基準ROMを差し替えない。
4. iPad配置が必要ならROMだけかsave同伴かを依頼どおり扱う。saveを扱う時は配置手順の停止・hash・原子的確定条件を守る。
5. ユーザーが修正版への切替を確認した時だけ、本書のパス、SHA-256、CRC32、checkpoint、配置記録を同じ作業で更新する。

現行候補の重大系gateではcrash、softlock、save corruption、progression blockageは0だった。
一方、strict全件監査は`DEFERRED_AUDIT`であり、進行中taskの完了を意味しない。

## 直前の基準

2026-09-07までの現行基準はStage61 `build/stages/61_critical_release_candidate.gba`、
SHA-256 `734541807df91ca6f82211b57e0a56e6af6c1c70ec46b9f89cd6a89b3f701f3b`、
CRC32 `232D05EA`だった。Stage62の固定入力、差分監査、Stage61 Wikiの再現用identityとして
この記録を保持するが、現在の実機操作対象には使わない。
