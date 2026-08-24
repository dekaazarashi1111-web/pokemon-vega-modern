# USER-20260824-STAGE49-INTERACTION-OWNERSHIP-REPAIR — Stage 49のinteraction ownerを再構築する

- Lane: `maps/events/field/battle/qa/release`
- Depends on: `USER-20260824-STAGE48-WORLD-ITEM-RECOVERY`、`T20`、`T26`〜`T30`
- Queue ID: `USER-20260824-STAGE49-INTERACTION-OWNERSHIP-REPAIR`
- Baseline: Stage 49 / ROM SHA-256 `780504cda0884bf53ed88f30fce18cbb54985740162210cb4724df0c6570ef5a`

## 再現対象

1. map上の通常trainer NPCが、視線検知／接触から正しい個別trainer戦へ入らない。会話文字列、trainer名、party、戦闘後復帰も破損する。
2. ヒスイシティを含む一部NPCが無反応である。
3. 落ち物、いあいぎりの木、map上のitem等が固有処理を行わず「カントーへようこそ」と表示する。
4. ヒスイシティの低レベルRaid hostが「てごろな レイドです」と表示後にfieldへ復帰せず進行不能になる。
5. 知恵の洞窟で、逃走後に方向転換／1歩だけで野生再遭遇し、fieldを離脱しにくい。
6. 511番水道（ユーザー報告時は551番水道）の草むらで野生が一切出現しない。
7. map trainerの視線／検知座標が本来より1マスずれ、見える範囲と実際のbattle開始位置が一致しない。
8. `あくのはどう`等のひるみ追加効果が体感上100%発動している可能性がある。

`きあいのタスキ`と特性runtimeは現時点のユーザー再確認では改善しているため、修正対象へ戻さず
Stage49の正しい挙動を回帰保護する。

## 原因仮説

Stage49のworld recoveryが、物理eventの見た目／source roleだけでinteractionを分類し、
一般NPC、field move、item、sign、trainer、既存project-owned proxyのowner境界を保持していない。
構造pointer検査だけでは、scriptの終端、戻り、状態遷移、transactionを証明できていない。

## 受入条件

- [x] Stage49が変更した全map eventをobject／bg単位で列挙し、ownerとinteraction種別を一意に分類する。
- [x] 全通常trainer objectについて、個別trainer command、trainer名、party、post battle scriptをexact-ROMの1,302 encounterで確認する。
- [x] trainerの方向、見える範囲、battle開始座標を元の実マス数へ戻し、東北／カントーの双方で横方向を含むoff-by-oneを0件にする。
- [x] Vega、T20、Trainer ChangeKit、T26〜T30の既存script pointerとCodex受付を許可なく置換しない。
- [x] 一般会話、回復、店、看板、落ち物、hidden item、いあいぎり／いわくだき等field objectを別ownerにする。
- [x] 一律「カントーへようこそ」scriptへ到達するfield objectを0件にする。
- [x] ヒスイシティを含む無効script NPCを実scriptへ接続し、会話後にfield入力へ戻す。
- [x] 設計未完のStage49低レベルRaid host 6件を撤回し、会話後停止経路を0件にする。
- [x] Codex対戦受付をStage48からbyte不変で保持し、iPad用save地点とexact-ROM回帰対象にする。
- [x] item取得、取得済み、bag満杯、いあいぎり／いわくだき、通常NPC会話をfinite transactionとして確認する。
- [x] 知恵の洞窟で逃走後の方向転換だけでは再遭遇せず、歩行ごとのencounter cadenceと猶予を正常化する。
- [x] 511番水道の草むらへ独立land ownerを設定し、species／levelを物理mapへ束縛する。
- [x] `あくのはどう`の仕様20%を4,096回標本で確認し、100%固定でないこと、Inner Focusと行動済み無効を維持する。
- [x] Stage49で改善済みの特性反映とFocus Sash満タン時1回発動・消費・非満タン不発を回帰させない。
- [x] 全425東北mapのland／water／rock／fishing ownerを物理map単位で照合し、旧`(0,0)`後続17 headerは到達不能legacy orphanとして分離する。
- [x] 全678 map graph、全trainer、既存story／T20 event、save ABIを回帰不変にする。
- [x] Stage50 ROM、差分／clean直接BPS、metadata、reportを再生成し、mGBA 2 processとprivate guardをPASSする。
- [x] iPadへStage50 ROMと互換セーブを別名配置し、旧Stage49を上書きしない。
- [x] `design/run_log.md`、`design/version_log.md`、`design/current_state.md`、task状態、commitを完了する。
