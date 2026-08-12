# T06 — Port CFRU battle core

- Lane: `engine`
- Depends on: `T04, T05`

## Objective

Run the CFRU battle engine on top of Vega without replacing Vega story/map content.

## Execute

1. Start from the minimal CFRU config, not the full Factory config.
2. Port battle hooks category by category: setup, turn order, move execution, abilities, items, UI, AI, animations.
3. For each hook, assert expected Vega bytes and adapt the containing Vega function if it diverged.
4. Relocate inserted code/data into allocator-owned extension sections.
5. Disable optional systems that are not required for the first vertical slice.
6. Add battle-script command table validation and bounded disassembly snapshots.
7. Run smoke tests after each hook category and keep bisectable commits.
8. 全体学習装置ON/OFF、mint補正、特性slot、SV式Hyper Trainingの実効IV=31を入力として受けるbattle/stat accessorを作る。save fieldとsummary UIへの接続はT08/T09後のT10で行う。
9. 経験アメはbattle分配を通さず選択個体だけを処理できる境界を作る。
10. CFRUのBattle Factory battle-side coreをallocator管理領域へ移植し、既存Vega種だけのsynthetic fixtureでLv.50 rental生成、facility battle flag、single 3v3、double 4v4、NPC partner multi、random、Little/Monotype/Unrestricted/OU/Uber/Camomons/GSのrule dispatchを検証する。link multiはrelease scope外とする。候補6→3、交換、連戦session、記録、図鑑、party復元はT08/T09後のT10で統合する。
11. 施設戦ではEXP、EV、なつき度、孵化歩数、捕獲、賞金、恒久的な道具消費/持出しを無効化するbattle境界を作る。
12. 標準、Mega、Z、Dynamax、Teraを別modeとして隔離し、Ultimateは入場時に1方式だけを選ぶ。複数ギミックの無条件同時使用を許可しない。
13. T01で固定したCFRU `src/Battle_AI/**` とAI hook/cache invalidationを一体で移植し、active bit mapping `AI_BASIC=1`、`AI_SEMI_SMART=3`、`AI_FULL_SMART=5` を同じcoreの名前付きprofileとしてVega trainer rowから選択できるadapterを作る。
14. 固定CFRU-JPの既定knowledge model、role prediction、評価ruleを維持し、未公開情報を遮断する独自AIや探索engineを追加しない。T02のknowledge監査結果と実build configを一致させる。
15. 固定seed fixtureでKO/2HKO、無効技回避、最適交代、hazard設置/除去、積み、回復、pivot、weather/field、trainer item、Mega/Z/Dynamax/Teraを検証する。doubleはtarget選択、味方巻込み回避、Protect/Wide Guard/Tailwind/Trick Room/Follow Me/Helping Hand連携を検証する。
16. `VAR_GAME_DIFFICULTY` による一律Hard/Expert化、`FLAG_SCALE_TRAINER_LEVELS`、party連動level scaleをrelease configへ入れない。decision直前のglobal RNG stateをfixtureで固定し、cache staleとT01で固定した性能閾値を計測する。
17. 既存Vega speciesだけのfixtureでnature、IV/EV spread、ability slot、item、4 movesを受け取るtrainer-build adapterを用意する。固定configで無効な `TRAINERS_WITH_EVS` と実際のspread index条件を監査し、安全に有効化してmappingを検証するか、同等のgenerated/runtime adapterを明示実装する。
18. `mechanic_policy` のruntime enum/interfaceを定義し、通常trainer戦でもMega/Z/Dynamax/Teraの非選択方式をbattle開始時にside単位で無効化して、1戦1方式・1回だけを強制する。T12はcontent rowをこのinterfaceへ解決する。
19. Mirage相手のheld itemをbattle-local仮想値として生成し、盗難・交換・消費・全battle出口でplayer party/bag/saveへ持ち出せない境界を実装する。
20. 固定CFRUのRaid battle coreをVega adapterへ接続し、boss/partner/shield/end/captureを既存battle UIで動かす。通常storyでは無効、`RAID_HIGH_DIFFICULTY` modeだけ例外的にDynamaxを固定許可し、他gimmickと同時使用させない。

## Required outputs

- `overlays/cfru/`
- `config/cfru_vega_minimal.h`
- `reports/generated/battle_hook_matrix.csv`
- `reports/generated/battle_core_smoke.md`
- `reports/generated/facility_core_smoke.md`
- `reports/generated/trainer_ai_smoke.md`

## Acceptance gates

- [ ] Vega normal wild and trainer battles complete.
- [ ] Core status, priority, multi-target, switching, fainting, experience, and capture paths work.
- [ ] No unclassified hook overwrites Vega code.
- [ ] Optional feature disablement is explicit, not accidental.
- [ ] 全体学習装置、mint、特性slot、Hyper Trainingの各入力fixtureに対してbattle/stat accessorが正しい結果を返し、経験アメは他partyへ分配されない。save・summaryとの一致はT10で検証する。
- [ ] Synthetic fixtureのrental生成、facility flag、rule dispatch、各battle形式が通常Vega戦と独立して動き、施設中の成長・捕獲・道具変化をbattle結果へ出力しない。
- [ ] 各ギミックmodeは相互排他的で、mode終了時に一時battle stateが全て破棄される。
- [ ] `AI_BASIC` / `AI_SEMI_SMART` / `AI_FULL_SMART` の全profileが同じ固定CFRU coreを使い、single/doubleの決定論fixtureで期待するmove/switch/target/gimmickを選ぶ。
- [ ] Knowledge modelはT02の監査結果と一致し、AI cache/historyはswitch/faint/form/item/state変化で正しく無効化される。
- [ ] AI判断はT01で固定したworst-case性能閾値内で完了し、global difficultyや動的level scaleを有効化しない。
- [ ] Trainer-build adapterが指定nature/IV/EV/ability/item/movesを再現し、未指定rowは元Vega生成値を変えない。
- [ ] 通常trainer戦の全mechanic policyでside全体の複数gimmick使用が起きず、Mirageの仮想itemは全終了経路で永続stateへ漏れない。
- [ ] Synthetic high-difficulty Raidが既存battle UIで完走し、通常wild/trainer battleへRaid flag/stateを漏らさず、Raid以外の複数gimmickを許可しない。

## Finish

1. Run task-specific acceptance checks, then run the platform default verify once as defined by `AGENTS.md`.
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T06 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T06:`.
5. If another task is READY, continue without waiting for approval.
