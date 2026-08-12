# T16 — Populate encounters trainers and items

- Lane: `content`
- Depends on: `T12, T14, T15`

## Objective

Populate both Tohoku and Kanto with the expanded roster while preserving Vega encounters, a sensible dual-region curve, and complete evolution access.

## Execute

1. Assign biome and level-band metadata to each wild-enabled map.
2. Populate land/water/rock-smash/fishing tables using symbolic species keys.
3. Populate regular trainers, gym trainers, bosses, and optional rematches.
4. Set moves, held items, abilities, and AI profiles appropriate to progression.
5. Place field items, hidden items, evolution items, TMs, and gym rewards.
6. Generate first-availability, duplicate-role, level-curve, type-distribution, and evolution-access reports.
7. Run automatic balance lint, then perform at least one human pass for each city/route batch.
8. Populate Tohoku's 49 logical overlay locations and Kanto's 47 logical ecology locations from normalized V2 data.
9. Verify all 541 families have both regional routes and all 125 special species share one capture key across regions.
10. カントーのLv.68〜100を `FIXED_HIGH_LEVEL_OPTIONAL` として生成し、party平均による動的scalingを入れない。
11. 初回到着の警告、強制戦闘なしの安全地帯、無料帰還を検査し、強力な店売り・報酬・重要道具は専用進行条件でgateする。
12. 経験アメ、孵化道具、mint、特性道具、王冠、努力値reset、まるいおまもりを、落とし物、調査、再戦、gym、dungeon、BP、questへsymbolic keyで配置する。
13. XS/S/M/L/XLの反復供給、無制限店売り、銀/金王冠、特性パッチが `docs/QOL_POLICY.md` の最初の入手時期より前へ漏れない経済reportを生成する。
14. T12 schemaの `field_pc_allowed` を両地方の町・通常道路へtrueで明示配置し、gym、dungeon、league、event専用mapはfalseにする。未設定falseに依存せず、両地方から代表town/routeと全禁止contextをreportする。
15. `manifests/tohoku_items.csv` と `manifests/qol_rewards.csv` のheader、unique key、symbolic reference、unlock/repeatabilityを `scripts/validate_manifests.py` または専用validatorへ登録する。
16. V2由来を含む新規eventはゲーム上の効果を維持しつつ `SIMPLE_EVENT` を優先し、既存NPC/端末、短い会話、標準battle/item/flag/warpへ正規化する。専用演出は既存asset再利用でも成立しない必須eventだけに限定する。
17. Factoryの初級/中級/上級/特殊/Vega/Mix rental pool、trainer、AI、rule、BP reward/shopを生成する。Mixの基本抽選比率は公式70%、Vega固有25%、特別枠5%とし、rental rowへspecies/form、nature、IV/EV、item、4 moves、ability、Gmax可否、Tera typeを明示する。
18. BP shopの初期balanceをmanifest化する。XS=1、S=2、進化石=3、かわらずのいし=4、あかいいと=12、power系=8、mint=8、特性カプセル=16、M=4、こだわり系=24、銀冠=32、特性パッチ=64、金冠=128、XL=12 BPを起点とし、T15のstory gateと `docs/QOL_POLICY.md` のfirst-availabilityを優先してlintする。
19. Trial初回報酬をXS×5、S×2、BP 3、反復報酬をBP 1〜2と木の実/ballを起点にmanifest化する。施設外NPC用には、おまかせ8、生息地15、タイプ25、希少50 BPを起点とする遭遇credit/poolを配置する。3/7/14/21連勝では段階credit、49連勝では一度限りの特殊event key、100連勝では一度限りの非伝説色違い記念枠を付与する。
20. 反復遭遇poolへ伝説・幻・battle専用formを入れず、全poolを進行gateし、通常探索の入手経路も残す。未捕獲を最大10回の内部再抽選で優先し、該当なしなら重複を許可する。tier別level/IV保証/隠れ特性率を明示する。報酬戦ではEXP/EV/賞金/野生所持品の盗難・持出し/drop/DexNav chainを無効化し、捕獲時だけ通常のcaught stateを更新する。
21. 既存の釣り、虫取り、採掘、写真、生態調査、ゲームコーナー等で利用可能な完了hookだけを調査point/arcade coin供給へ接続する。存在しない活動のために新規ミニゲーム、map、UIを作らず、未実装hookは明示的にDEFERする。

## Required outputs

- `manifests/kanto_encounters.csv`
- `manifests/kanto_trainers.csv`
- `manifests/kanto_items.csv`
- `manifests/tohoku_items.csv`
- `manifests/qol_rewards.csv`
- `manifests/facility_modes.csv`
- `manifests/facility_rentals.csv`
- `manifests/facility_trainers.csv`
- `manifests/facility_rewards.csv`
- `manifests/reward_encounters.csv`
- `reports/generated/kanto_content_audit.md`

## Acceptance gates

- [ ] Every referenced key resolves.
- [ ] No required evolution item is permanently unobtainable.
- [ ] No trainer has invalid move/item/species combinations.
- [ ] Level curve has no unexplained extreme jumps; Kanto's declared fixed high-level optional policy is reported as intentional rather than silently ignored.
- [ ] Tohoku fallback tables preserve every original Vega slot and rare encounter when overlays are disabled.
- [ ] V2 logical locations resolve to the imported physical map graph.
- [ ] 早期配置には推奨レベル警告があり、post-HoF限定個体・報酬は殿堂入り前に解禁されない。
- [ ] 必須育成機能は永久入手不能にならず、強い育成道具の反復供給は指定進行境界を守る。
- [ ] Tohoku/Kanto双方で代表town/routeのfield PCが有効、全gym/dungeon/league/event専用mapが無効になり、未分類map一覧が0になる。
- [ ] 新規Tohoku/QOL manifestのheader、unique key、全symbolic referenceをvalidatorが検査する。
- [ ] 新規eventの専用UI/cutscene/minigame依存が0で、例外は根拠と再利用不能理由をreportに列挙する。
- [ ] 全rental/trainer rowが合法で、pool比率、Lv.50補正、rule/AI/gimmick eligibilityを再現可能に生成できる。
- [ ] BP価格と初回入手時期に矛盾がなく、遭遇credit、節目報酬、一度限りkey、反復poolの禁止種をvalidatorが検査する。
- [ ] ランダム捕獲は施設外の `SIMPLE_EVENT` NPCだけから起動し、専用capture map/UI用contentを生成しない。
- [ ] 採用した既存ミニゲームhookはexactly-onceでpointを付与し、未採用/未実装hookは架空の供給経路として生成されない。

## Finish

1. Run task-specific acceptance checks, then run the platform default verify once as defined by `AGENTS.md`.
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T16 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T16:`.
5. If another task is READY, continue without waiting for approval.
