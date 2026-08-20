# T22 — Integrate Move Distribution V4

- Lane: `engine/content/qa`
- Depends on: `T21`

## 目的

ChatGPT Pro返却済みのMove Distribution V4を、T21完了済みStage 38へproduction統合する。
返却CSVを参考表のまま置かず、level-up、egg、TM/tutor、form、野生生成、わざメモリー、
預かり屋の実consumerへ接続し、全対象Speciesの習得経路をStage 39実ROMで成立させる。

このタスクは返却済みbalanceを再設計するタスクではない。設計ZIPは読取専用の固定入力とし、
物理address、table容量、既存consumerはStage 38からexpected-byte付きで再解決する。

## 固定入力

### 現行baseline

- ROM-producing commit: `8532929dadf188c24779dbc01bea38e5e90ed162`
- ROM: `build/stages/38_mirage_production.gba`
- ROM SHA-256: `f66c4823e50d9db86a7c5ef07436558dd4c25c2f41ee3a94e413eadc4a37d941`
- ROM size: 33,554,432 bytes
- metadata: `build/stages/38_mirage_production.json`
- metadata SHA-256: `da027d40dda9ebc0f54f1e217d4442369ab41ebb8d2956b24e844355e2fb2b77`

Stage 38のT00〜T21、既存trainer 1,302戦・6,490 member、QOL 35機能、T20 event 76件、
T21 Mirage 28戦を回帰不変条件とする。入力identityが異なる場合は推測でrebaseしない。

### 返却済み設計

- 原本: `userfile/imports/Pokemon-Vega_MOVE-DISTRIBUTION-V4_IMPLEMENTATION-READY.zip`
- ZIP SHA-256: `4022cd6e1358f58dffc5ebc38b756166f0a1072f948af6934298f65bd82678b2`
- ZIP size: 395,446 bytes、11 entries
- validation fingerprint: `d0e014e49beb339668ce3531b8fe6871c793a063f2bff1c8d2b97898f81d02a9`
- validator結果: PASS、open question 0、warning/error 0
- canonical rows: level-up 28,274、egg 8,219、TM/tutor 2,799、form 509、
  wild initial 1,206、source coverage 1,206
- validator: `templates/chatgpt_pro_design_packets/tools/validate_submission.py`
- packet root: `dist/chatgpt_pro_design_packets/unpacked/Pokemon-Vega_CHATGPT-PRO_MOVE-DISTRIBUTION-V4_INPUT_20260820/`

ZIPを直接編集・再圧縮しない。作業時はGit管理外へ展開し、11 entryをすべて読んでから正規化する。

## 固定仕様

- level-upとeggは最終表でありdeltaではない。level-up 28,274行、egg 8,219行を欠落なくcompileする。
- 既存level-up行は完全重複の正規化を除いて維持し、設計上の追加2,600行を反映する。
- TM/tutorは16-byte LSB-first bitsetへの `0 -> 1` 追加2,799件だけを適用し、既存bitを除去しない。
- form 509行はbase/formの正当性、技ID、解禁、重複を検証し、form固有consumerへ接続する。
- wild initial 1,206行は新規に生成する野生個体だけへ適用する。既存party/box/save個体の技を
  load時やmap遷移時に書き換えない。
- Vega既存Species/Move IDとT04/T07 canonical IDを固定する。EGG sentinelと追加Species境界を
  現行manifestへ再照合し、行番号をSpecies IDとして盲用しない。
- わざメモリー、預かり屋、孵化、TM/tutor UI、野生生成、trainer/facility party生成で同じ
  canonical表を参照させ、consumer別の複製表を正本にしない。
- T21 Mirage、Factory、Raid、Reward encounter fixtureに野生初期技overrideを漏らさない。

## 実行

1. ZIP/Stage 38 identityとprivate guardを確認し、安全な一時領域へZIPを展開する。
2. 共通validatorをpacket rootと展開結果に対して再実行し、上記fingerprintと行数を照合する。
3. Stage 38のlevel-up、egg、TM/tutor、form、wild initial tableと全consumerをrooted監査する。
4. 返却CSVをstable symbolic keyからcanonical numeric IDへ解決し、未解決・重複・違法値をfail-closedにする。
5. 最終tableを決定的にserializeし、必要なrepoint/runtime adapterを中央allocator経由で配置する。
6. わざメモリー、預かり屋、孵化、TM/tutor、野生生成のproduction入口へ接続する。
7. expected-byte付き差分をStage 38へ適用してStage 39を生成する。
8. focused test、exact-ROM mGBA quick/full、clean rebuild、Stage 38差分BPSとclean直接BPSを検証する。

## 必須成果物

- `content/move_distribution_v4/**`
- `config/move_distribution_v4.json`
- `overlays/move_distribution_v4/**`
- `scripts/build_move_distribution_v4.py`
- `scripts/rebuild_move_distribution_v4_from_clean.py`
- `tools/mgba_move_distribution_v4_smoke.c`
- `tests/test_move_distribution_v4.py`
- `reports/generated/move_distribution_v4_{audit,coverage}.json`
- `build/stages/39_move_distribution_v4.gba`（Git管理外）
- Stage 38→39 BPS、clean→Stage 39 BPS、mGBA quick/full、clean rebuild証跡（Git管理外）

既存builderを再利用する場合も上記名の薄いadapterと同等の機械可読証跡を用意する。
host-only fixture、未接続CSV、手編集ROMは成果物としない。

## 受入条件

- [ ] Stage 38とZIPのsize/hash/fingerprintが固定値に一致し、原本ZIP・ROM・saveを変更しない。
- [ ] level-up 28,274、egg 8,219、TM/tutor追加2,799、form 509、wild initial/source 1,206を欠落・重複0でcompileする。
- [ ] 全Species/Move/form参照がcanonical IDへ解決し、Vega既存ID変更、EGG衝突、範囲外参照が0。
- [ ] TM/tutorは既存許可を一件も除去せず、指定された0→1だけが変化する。
- [ ] わざメモリー、預かり屋、孵化、TM/tutor UIが新表を通常入力から参照する。
- [ ] 新規野生だけが指定初期技を持ち、既存save個体、trainer、Factory、Mirage、Raidへ漏れない。
- [ ] changed byteがdeclared span内で、ROM/RAM/save/hook overlapが0。
- [ ] T00〜T21、trainer、QOL、event、Mirageの回帰がPASSする。
- [ ] Stage 39をclean FireRed日本版Rev.0から決定的に再構築でき、2種類のBPSが完全往復する。
- [ ] mGBA quick/fullの独立2 processがwarnings/errors 0で同じresult identityを返す。

## 禁止する完了判定

- CSVのcopy、schema変換、host-side集計だけでDONEにしない。
- Stage 37向け物理addressをStage 38へ無監査で適用しない。
- 返却済みbalance、Species/Move ID、既存習得行を都合よく再設計しない。
- private ZIPの内容をGitへそのまま追加しない。

## 完了

1. task固有build/check、focused tests、mGBA quick/full、clean rebuildをPASSする。
2. `design/run_log.md`と`design/version_log.md`へ証跡を追記する。
3. `python3 scripts/taskctl.py done T22 --summary "Move Distribution V4をStage39へproduction統合"`を実行する。
4. 意図した差分だけをstageし、task graph、private guard、`git diff --check`をPASSする。
5. `T22:`で始まるcommitを作る。pushしない。
