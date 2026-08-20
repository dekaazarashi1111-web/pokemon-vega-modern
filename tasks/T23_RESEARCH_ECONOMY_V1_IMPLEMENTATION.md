# T23 — Integrate Research Economy V1

- Lane: `content/engine/save/maps/qa`
- Depends on: `T22`

## 目的

ChatGPT Pro返却済みのResearch Economy V1を、T22のStage 39へproduction統合する。
研究ポイント、6活動、7 rank、23 shop item、9 NPC binding、35会話を通常field入力・save・
各activity hookへ接続し、Stage 40で独立した研究経済として成立させる。

## 固定入力

### baseline

- T22の正規出力 `build/stages/39_move_distribution_v4.gba` とmetadata。
- identityはT22完了commitとmetadataに記録されたsize/hashを正とする。
- T22がDONEかつworktreeがその完了commitを含むことを確認してから開始する。
- Stage 38以前の物理addressやStage 37同梱catalogをStage 39へ盲用しない。

### 返却済み設計

- 原本: `userfile/imports/Pokemon-Vega_RESEARCH-ECONOMY-V1_IMPLEMENTATION-READY.zip`
- ZIP SHA-256: `0cd2a68535f5543da919a6502a21321adb826dbff37d356b0cacfc697c7367de`
- ZIP size: 21,503 bytes、12 entries
- validation fingerprint: `2ea4497307af6aece808fd9a98158561c7c87e83cd4748b2e6d3ab8c4aa27a8b`
- validator結果: PASS、open question 0、warning/error 0
- canonical rows: activities 6、currency 1、ranks 7、shop 23、NPC binding 9、dialogue 35、batch 7
- validator: `templates/chatgpt_pro_design_packets/tools/validate_submission.py`
- packet root: `dist/chatgpt_pro_design_packets/unpacked/Pokemon-Vega_CHATGPT-PRO_RESEARCH-ECONOMY-V1_INPUT_20260820/`

ZIPは読取専用とし、同梱設計書・CSV・batch・open questionをすべて確認する。

## 固定仕様

- 通貨は `CURRENCY_KEY_RESEARCH_POINT`、ownerは `OWNER_KEY_RESEARCH_ECONOMY_V1`。
  U16、上限9,999で、BP、Reward credit、コイン、Mirage仮想itemと相互変換・aliasしない。
- 研究日はRTCではなくactive play 60分で進む。時計のないemulatorでも決定的に進行する。
- 6 activityを設計どおり実装する。反復hookは釣り `4 / day cap 24`、生態研究
  `10 / cap 50`、ゲームコーナー `3 / cap 18`。虫・採掘・写真のsimple eventは各 `8 / 10 / 6`。
- rank閾値は `0, 80, 240, 520, 900, 1400, 2200`。解禁・一度限りclaimを同じtransactionで扱う。
- shop 23行、host 9行、dialogue 35行、batch 7行をstable keyのままcompileする。
- 既存T08 Research encounter stateと本経済ledgerをaliasしない。既存slotを流用する場合もowner・version・
  migrationを明示し、Reward encounterやRaidのpending transactionを上書きしない。
- save ABIは現行Stage 39を再監査する。設計案の64 byteはT08 `reserved_v1_tail`からのみ確保し、
  T21がMirage journalに使用する40-byte state、Factory snapshot/ledger、T20 stateを侵食しない。
- modern save v1→v2はzero-extend、外側checksumを含めて原子的に移行する。保存失敗時は残高・claim・
  daily cap・rankを一括rollbackする。
- physical NPC/map bindingはStage 39のobject上限、collision、既存T20/T21 hostを再監査して決める。

## 実行

1. T22 Stage 39、ZIP、private guardのidentityを確認する。
2. 共通validatorをpacket rootと展開結果に対して再実行し、fingerprint・行数・open question 0を照合する。
3. Stage 39のsave ledger、currency service、activity hook、候補map/NPCをrooted監査する。
4. 6 activity、7 rank、23 shop、9 host、35 dialogueをcanonical dataへ正規化する。
5. versioned research ledgerとmigration、atomic transaction、daily timer/capを実装する。
6. 通常field NPC、釣り、生態、ゲームコーナー、simple event、shopへproduction接続する。
7. expected-byte付き差分でStage 40を生成し、全shared owner overlapを検査する。
8. focused test、mGBA quick/full、old/new save、clean rebuild、BPS往復を検証する。

## 必須成果物

- `content/research_economy_v1/**`
- `config/research_economy_v1.json`
- `overlays/research_economy_v1/**`
- `scripts/build_research_economy_v1.py`
- `scripts/rebuild_research_economy_v1_from_clean.py`
- `tools/mgba_research_economy_v1_smoke.c`
- `tests/test_research_economy_v1.py`
- `reports/generated/research_economy_v1_{audit,coverage}.json`
- `build/stages/40_research_economy_v1.gba`（Git管理外）
- Stage 39→40 BPS、clean→Stage 40 BPS、mGBA、migration、clean rebuild証跡（Git管理外）

## 受入条件

- [ ] T22 Stage 39とZIP identityが一致し、private原本を変更・追跡しない。
- [ ] 6 activity、1 currency、7 rank、23 shop、9 host、35 dialogue、7 batchを欠落・重複0でcompileする。
- [ ] 研究ポイントがU16/9,999上限で動き、BP・credit・コイン・Mirageとowner/stateを共有しない。
- [ ] active play 60分の研究日、各daily cap、境界直前/直後、save/reloadが固定仕様どおりになる。
- [ ] 7 rankと23 shopの解禁・購入・不足・満杯・cancel・一度限りclaimがatomicに動く。
- [ ] old save migration、新規save、checksum failure、transaction中resetが欠損・二重付与なしでPASSする。
- [ ] 9 NPCの通常入力から全activity/shop/dialogueへ到達でき、object/collision/host競合が0。
- [ ] T00〜T22、T20 event、T21 Mirage、Factory、Raid、既存Research encounterの回帰がPASSする。
- [ ] changed byteがdeclared span内で、ROM/RAM/save/map/hook overlapが0。
- [ ] Stage 40のclean rebuild、BPS往復、mGBA quick/full独立2 processがPASSする。

## 禁止する完了判定

- balanceの再設計、RTC必須化、既存通貨への相乗りをしない。
- host-side model、CSV、debug menuだけでDONEにしない。
- Stage 37のhost addressやsave offsetをStage 39へ無監査でコピーしない。

## 完了

1. task固有build/check、focused tests、save migration、mGBA、clean rebuildをPASSする。
2. `design/run_log.md`と`design/version_log.md`へ証跡を追記する。
3. `python3 scripts/taskctl.py done T23 --summary "Research Economy V1をStage40へproduction統合"`を実行する。
4. task graph、private guard、`git diff --check`をPASSし、意図した差分だけをstageする。
5. `T23:`で始まるcommitを作る。pushしない。
