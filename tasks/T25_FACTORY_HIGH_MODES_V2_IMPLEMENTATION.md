# T25 — Integrate Factory High Modes V2

- Lane: `content/engine/save/ui/qa`
- Depends on: `T24`

## 目的

ChatGPT Pro返却済みのFactory High Modes V2を、T24のStage 41へproduction統合する。
既存Factory Trialの挙動を保持しながら24 mode、28 unlock requirement、248 rental set、
55 opponent profile、16 reward、28 dialogueを通常Factory入口へ接続し、Stage 42で全high modeを完成させる。

## 固定入力

### baseline

- T24の正規出力 `build/stages/41_reward_encounters_v2.gba` とmetadata。
- identityはT24完了commitとmetadataに記録されたsize/hashを正とする。
- T24がDONEかつworktreeがその完了commitを含むことを確認してから開始する。
- Stage 37向け物理値はStage 41のFactory runtime/save/UIから再解決する。

### 返却済み設計

- 原本: `userfile/imports/Pokemon-Vega_FACTORY-HIGH-MODES-V2_IMPLEMENTATION-READY.zip`
- ZIP SHA-256: `7e79616dea664f670b8985fe89d23e066df2751225b5a8ee078035b4bb2b9830`
- ZIP size: 30,203 bytes、13 entries
- validation fingerprint: `c48d69f2a64cda65f2a97a2382ddb8bb4dbc66437302a87e3da669428dc20fe1`
- validator結果: PASS、open question 0、warning/error 0
- canonical rows: modes 24、requirements 28、rental sets 248、opponent profiles 55、
  rewards 16、dialogue 28、batch 7
- validator: `templates/chatgpt_pro_design_packets/tools/validate_submission.py`
- packet root: `dist/chatgpt_pro_design_packets/unpacked/Pokemon-Vega_CHATGPT-PRO_FACTORY-HIGH-MODES-V2_INPUT_20260820/`

## 固定仕様

- save mode slotは `0..23`。既存16 slotを同じ意味で保持し、8 slotだけを追加する。
- slot 0 Trialは現行exact oracleを維持する。3戦、完走9 BP、600-byte party snapshot、
  戦間交換・全回復・退出時exact restoreを変えない。
- Trial 4、Standard 4、Full 9、Master 7の計24 modeを設計表どおり実装する。
- high modeは7戦round、49/100 milestone、single/double、NPC partner local、random、Little、
  Monotype、OU、Camomons、Unrestricted/UBER preset、GS、Region Mix、Ultimateを含む。
- Ultimateはchallenge開始時にMega/Z/Tera/Dynamaxのうち設計上許可された1つを固定し、
  1 battle・1 side最大1 gimmickを守る。mode間や通常battle/Mirage/Raidへstateを漏らさない。
- rental 248行、profile 55行から決定的に相手・候補を生成する。有限fallbackを持ち、条件不成立時の
  無限loop、reset再抽選、同一challenge内のrerollを禁止する。
- active challenge中のreset/reloadはresumeせずforfeitとして入場前partyをexact restoreする。
  round境界の明示retireだけがstreakを保存する。
- `reward_pending` はlow 3 bit battle index、high 5 bit mode slot。
  markerはlow 3 bit base、bit 3..5 gimmick、bit 6 UBER、bit 7 zeroという返却契約を守る。
  現行save layoutと衝突する場合は意味を変えずversioned migrationで解決する。
- reward 16行、49/100既存claim、BP、T24 Factory milestone credit hookを同一transaction境界で接続する。
- T21 Mirageのparty/gimmick/record/virtual item stateを共有しない。

## 実行

1. T24 Stage 41、ZIP、private guardのidentityを確認する。
2. 共通validatorをpacket rootと展開結果に対して再実行し、fingerprintと全row countを照合する。
3. 現行Factory Trial、24 save slot、party snapshot、BP/reward、UI、battle hookをrooted監査する。
4. 24 mode、28 requirement、248 rental、55 profile、16 reward、28 dialogue、7 batchを正規化する。
5. mode dispatcher、unlock/UI、deterministic generator、partner/double、gimmick、reward transactionを実装する。
6. reset/forfeit/retire/完走/敗北/cancelのcleanupを単一ownerへ集約する。
7. expected-byte付き差分でStage 42を生成し、save/RAM/hook/allocator overlapを検査する。
8. host exhaustive matrix、exact-ROM representative/all-boundary mGBA、clean rebuild、BPS往復を検証する。

## 必須成果物

- `content/factory_high_modes_v2/**`
- `config/factory_high_modes_v2.json`
- `overlays/factory_high_modes_v2/**`
- `scripts/build_factory_high_modes_v2.py`
- `scripts/rebuild_factory_high_modes_v2_from_clean.py`
- `tools/mgba_factory_high_modes_v2_smoke.c`
- `tests/test_factory_high_modes_v2.py`
- `reports/generated/factory_high_modes_v2_{audit,coverage}.json`
- `build/stages/42_factory_high_modes_v2.gba`（Git管理外）
- Stage 41→42 BPS、clean→Stage 42 BPS、mode matrix、mGBA、clean rebuild証跡（Git管理外）

## 受入条件

- [ ] T24 Stage 41とZIP identityが一致し、private原本を変更・追跡しない。
- [ ] 24 mode、28 requirement、248 rental、55 profile、16 reward、28 dialogue、7 batchを欠落・重複0でcompileする。
- [ ] 既存16 slotの意味とslot 0 Trialの3戦/9 BP/600-byte snapshot挙動がbyte・runtime回帰で一致する。
- [ ] 新規8 slotと全unlock条件が正しく、未解禁modeへUI/script/save改変で侵入できない。
- [ ] 全modeのparty size、level、battle format、partner、gimmick、ban/rental ruleが設計表と一致する。
- [ ] generatorが全seedで有限終了し、fallback、anti-reroll、reset再現性を満たす。
- [ ] reset/reloadはforfeit exact restore、明示retireだけがround境界streakを保存する。
- [ ] 16 reward、BP、49/100 claim、T24 credit hookがatomicで、二重付与・先行claimが0。
- [ ] Factory stateがMirage/Raid/通常battleへ漏れず、1 battle・1 side最大1 gimmickを守る。
- [ ] T00〜T24、QOL、event、Mirage、Move、Research、Reward encounter、Raidの回帰がPASSする。
- [ ] changed byte declared span、ROM/RAM/save/UI/hook overlap 0、clean rebuild/BPS/mGBAがPASSする。

## 禁止する完了判定

- Trialを別仕様へ置換する、24 modeの一部だけを接続する、debug menuだけを入口にする実装をしない。
- opponent/rental生成を無制限retryにしない。
- active challengeをreset後に中途resumeさせない。
- host-side matrix、CSV、fixtureだけでDONEにしない。

## 完了

1. task固有build/check、mode matrix、mGBA、clean rebuildをPASSする。
2. `design/run_log.md`と`design/version_log.md`へ証跡を追記する。
3. `python3 scripts/taskctl.py done T25 --summary "Factory High Modes V2をStage42へproduction統合"`を実行する。
4. task graph、private guard、`git diff --check`をPASSし、意図した差分だけをstageする。
5. `T25:`で始まるcommitを作る。pushしない。
