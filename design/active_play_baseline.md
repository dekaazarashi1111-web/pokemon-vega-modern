# 現在のプレイ基準ROM

最終更新: 2026-09-03

この文書は、ユーザーが現在遊ぶROMと、そのROMに対する実機操作・不具合修正の基準を一つに固定する正本である。
新しいstageや候補ROMが生成されていても、ユーザーが明示的に切り替えるまでは本書のROMを使う。

## 現在の基準

- 呼称: Stage61 Vega会話復元・外来生態率調整・Codex CLI復旧版
- ローカルROM: `build/stages/61_critical_release_candidate.gba`
- サイズ: 33,554,432 bytes
- SHA-256: `60b83b8c50e54c3af42daa23b9d82e96c1b769d816ce28ef8bfda1d5005aff0e`
- CRC32: `F6ECC7F0`
- ROM内容checkpoint: 本基準更新と同じ作業（起動直後のCodex runtime初期化入口を復旧）
- iPad配置記録: 2026-09-03（同一SHAのROMだけを配置、save 57件不変）
- 状態: ユーザー指定の現行プレイ基準。strict全件監査完了版ではない。

このROMはiPadのRetroArch/mGBAへ配置済みである。配置時にはsaveを生成・転送・変更していない。
以後iPad上で進んだ通常プレイsaveを現行saveとして扱い、ユーザーの明示依頼なしにテストsaveで上書きしない。
端末固有の配置先は記録せず、必要時に`docs/IPAD_RETROARCH_MGBA_SAVE_PLACEMENT.md`どおりlive設定から解決する。

## このROMを使う依頼

別セッションでも、次の依頼は明示がない限りすべて上記SHAのStage61を対象にする。

- Codex対戦
- 対戦後の任意報酬
- WindowsカタログからのPokémon・アイテム送付
- Box 14とWindows間の固有個体移動
- 通常プレイ中に見つかったバグの再現・解析・修正
- iPadへのROM再配置、または現行saveを使う確認

古いStage45／46／47／60や、別SHAのStage61を実機操作の対象へ自動選択しない。
ローカルROMが見つからない、またはSHAが一致しない場合は、別ROMで代用せず不一致を報告する。

## Codex対戦・送付の開始条件

`vega-codex-battle`を使う実機セッションでは、最初にread-onlyで次を実行する。

```bash
vega-codex-battle doctor --json
vega-codex-battle session guide --json
vega-codex-battle match status --json
```

ROM identity、runtime、save状態が一致した時だけwriteへ進む。2026-09-03時点の導入済みCLIは
`vega-codex-battle 2.5.1`であるが、固定filenameではなくCLIが読むprotocolのROM identityを正とする。

現行ROMへCLIを再導入する時は次を使う。installerは指定ROMのsize／SHA-256／CRC32とStage番号を
protocolへ再固定してから配置するため、Stage47の古いROM identityを手編集しない。

```bash
VEGA_CODEX_BATTLE_ROM_SOURCE="$PWD/build/stages/61_critical_release_candidate.gba" \
VEGA_CODEX_BATTLE_STAGE=61 \
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

1. まず上記SHAのStage61と、ユーザーの現行save／レポート／再現位置を対象にする。
2. 原因候補を絞るためのread-only調査とfocused検証を先に行う。strict全件監査は、ユーザーが依頼した場合だけ再開する。
3. 修正版は別候補として生成し、ユーザーが採用するまでは本書の基準ROMを差し替えない。
4. iPad配置が必要ならROMだけかsave同伴かを依頼どおり扱う。saveを扱う時は配置手順の停止・hash・原子的確定条件を守る。
5. ユーザーが修正版への切替を確認した時だけ、本書のパス、SHA-256、CRC32、checkpoint、配置記録を同じ作業で更新する。

現行候補の重大系gateではcrash、softlock、save corruption、progression blockageは0だった。
一方、strict全件監査は`DEFERRED_AUDIT`であり、進行中taskの完了を意味しない。
