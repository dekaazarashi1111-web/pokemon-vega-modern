# T30 — Box 14とWindows固有個体庫を双方向exact移動へ接続する

- Lane: `engine/save/tooling/qa`
- Depends on: `T29`

## 目的

GBA側のBox 14をWindows PCとの専用搬送箱として扱う。`vault deposit`はBox 14の全個体を
owner-only Windows個体庫へ完全保存した後だけGBAから削除し、`vault withdraw`は選択した在庫を
Box 14へ通常saveした後だけWindows在庫から減算する。Stage 47以降のROMでも同じversioned
protocolとBoxPokemon ABI fingerprintを使い、特定ROM filenameへ固定しない。

## 固定入力

- T29 Stage 46 ROM、metadata、protocol、symbols、Windows catalog CLI。
- 固定CFRU-JPの80-byte `BoxPokemon` ABI、通常PC storage API、Box 14の30枠。
- T19のPC複数選択・一括処理、通常save、失敗rollback。

## 固定仕様

- 対象はBox 14（0始まりbox 13）の30枠だけ。手持ち、Box 1〜13、bag、mailbox外領域をhostから
  読み書きしない。預け入れ・引き出し・catalog生成はmap／NPC位置を問わず、通常fieldでPC UI／script／
  battleが閉じている時に受理する。対戦後報酬はresult windowだけを条件にし、NPC位置を条件にしない。
- 個体はCFRUの展開済み80-byte `BoxPokemon`原本をslot番号とCRC付きで搬送し、personality、OT ID／名前／性別、
  nickname、language、marking、species/form、held item、EXP、friendship、moves／PP Up、EV／IV、
  contest、Pokerus、met data、ball、ability、nature、shiny、ribbon、egg、Tera等の保存済み全bitを保持する。
- `deposit`はBox 14 snapshotをWindows側owner-only pending transactionへatomic保存・fsyncした後、
  各slotのraw CRCをROMへcommitする。ROMはslotを再照合し、held itemをbagへ戻さず個体と一緒に削除して
  1slot単位で通常saveする。中断時はWindows batchの完了bitと実slotを照合し、未完了slotから再開する。
- `withdraw`はWindows在庫をpendingにしてから宣言済み80-byte input spanへ1体ずつ置き、ROMが空きBox 14
  slotへexact bytesを通常saveしたことを再読取で確認してからWindows在庫を減算する。途中失敗は
  最初の未確定個体で停止し、同じtransactionを再開して重複・消失へ収束させない。
- Box 14の穴、0／1／6／30体、同一raw個体、タマゴ、持ち物、色違い、nickname、特殊formを扱う。
  mail本文など80-byte外の関連状態が必要な個体は全体無変更で明示拒否する。
- Windows個体庫はraw bytesをJSONへ直接埋めず、owner-only data directoryにversioned manifestとbinary blobを
  atomic配置する。各個体へ安定vault ID、source ROM/protocol、ABI fingerprint、SHA-256、元slot、deposit時刻を持つ。
- 後続ROMはprotocolのBoxPokemon size／ABI fingerprint／Species・Item namespace互換が一致する時だけ
  同じWindows在庫を使用する。不一致は無変更で拒否し、強制変換やhost側save編集を行わない。

## 必須成果物

- `config/windows_box14_vault.json`
- `overlays/windows_box14_vault/**`
- `scripts/build_windows_box14_vault.py`
- `tools/mgba_windows_box14_vault_smoke.c`
- `tests/test_windows_box14_vault.py`
- `docs/WINDOWS_BOX14_VAULT_JA.md`
- `generated/runtime/windows_box14_vault_protocol.json`
- `reports/generated/windows_box14_vault_{audit,coverage}.json`
- `build/stages/47_windows_box14_vault.gba`（Git管理外）

## 受入条件

- [x] T29 Stage 46 exact baselineからStage 47を決定的にbuild/checkできる。
- [x] 実ROMでBox 14の0／1／6／30体と穴あき配置をWindowsへdepositし、全80 byte・順序・hashが一致する。
- [x] Windows永続化前、ROM削除前後、通常save中、応答喪失、process再起動の各中断点で再開し、重複0・消失0になる。
- [x] withdraw 1／6／30体、Box 14容量不足、同一raw個体、別ROM ABI、破損blobを検査し、確定分だけ在庫を減算する。
- [x] held itemを含む全bitが往復byte一致し、deposit時にbagへ複製されない。mail関連個体は全体無変更拒否する。
- [x] host writeはversioned mailbox requestと宣言済み128-byte transfer spanだけ、host readは同じBox 14 export spanだけである。
- [x] T27対戦、T28報酬、T29 template生成、通常PC/save、Box 1〜13が不変で、ROM/RAM/save/hook overlapが0である。
- [x] 現在Box 14の約6体を実iPadでdepositし、Windows manifest/blob一致とGBA側空を確認する。withdrawのexact復元とreloadは同じStage 47 ROMのmGBA／host自動検査で確認し、実iPadはWindows保管状態で止める。

## 完了

1. task固有build/check、host unit、exact-ROM mGBA quick、実iPad約6体depositをPASSする。
2. `design/current_state.md`、`design/run_log.md`、`design/version_log.md`へ日本語で追記する。
3. `python3 scripts/taskctl.py done T30 --summary "Box 14とWindows固有個体庫をStage47へ統合"`を実行する。
4. task graph、private guard、`git diff --check`をPASSし、意図した差分だけをstageする。
5. `T30:`で始まるcommitを作る。pushしない。
