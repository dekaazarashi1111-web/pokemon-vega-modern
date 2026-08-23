# タスク一覧

Codexは `task_graph.json` の依存関係と `../design/tasks_next.md` の状態から、再開対象、推奨PRIMARY、その他の依存READY候補を判定します。PRIMARYは強制順ではありません。リポジトリrootで `python3 scripts/taskctl.py plan` を実行すると全waveを表示できます。`state/task_status.json` は `scripts/taskctl.py` が同期する互換ミラーであり、手編集しません。

| ID | Task | Lane | Depends |
|---|---|---|---|
| [T00](T00_BOOTSTRAP.md) | Bootstrap and pin inputs | platform | — |
| [T01](T01_UPSTREAM_REPRO.md) | Reproduce upstream DPE/CFRU builds | engine | T00 |
| [T02](T02_EXACT_AUDIT.md) | Exact ROM/RAM/save/ID audit | qa | T00 |
| [T03](T03_VEGA_HARNESS.md) | Create rebuildable Vega module harness | engine | T01, T02 |
| [T04](T04_MOVE_PORT.md) | Port Vega Move IDs into CFRU model | engine | T03 |
| [T05](T05_ID_SPACES.md) | Unify Type Ability Item ID spaces | engine | T02, T03 |
| [T06](T06_BATTLE_CORE.md) | Port CFRU battle core | engine | T04, T05 |
| [T07](T07_SPECIES_PORT.md) | Port DPE Species while freezing Vega IDs | engine | T03, T04, T05 |
| [T08](T08_SAVE_RAM.md) | Resolve RAM and save compatibility | qa | T02, T03 |
| [T09](T09_GRAPHICS_DEX_EVOLUTION.md) | Port graphics cries dex evolution learnsets | engine | T07, T08 |
| [T10](T10_ENGINE_VERTICAL_SLICE.md) | Complete engine vertical slice | qa | T04, T05, T06, T07, T08, T09 |
| [T11](T11_KANTO_IMPORTER.md) | Build Kanto map importer | maps | T00, T02 |
| [T12](T12_CONTENT_SCHEMA.md) | Build symbolic content schema and generators | content | T00 |
| [T13](T13_VERMILION_SLICE.md) | Implement Vermilion early-access vertical slice | maps | T10, T11, T12 |
| [T14](T14_FULL_KANTO_IMPORT.md) | Import selected full Kanto map set | maps | T11, T13 |
| [T15](T15_POSTGAME_PROGRESSION.md) | Implement dual-phase Kanto progression | content | T13, T14 |
| [T16](T16_CONTENT_POPULATION.md) | Populate encounters trainers and items | content | T12, T14, T15 |
| [T17](T17_REGRESSION.md) | Integrate QOL-B and run regression/playtest gates | qa/engine | T10, T13, T16 |
| [T18](T18_RELEASE.md) | Create reproducible release pipeline | platform | T17 |
| [T19](T19_QOL_PRODUCTION_COMPLETION.md) | Complete production QOL integration | engine/ui/save/qa | T18 |
| [T20](T20_EVENT_DESIGN_IMPLEMENTATION.md) | Integrate implementation-ready event design | maps/content/engine/save/qa | T19 |
| [T21](T21_MIRAGE_PRODUCTION_RUNTIME.md) | Connect Mirage modernization to production runtime | maps/content/engine/save/qa | T20 |
| [T22](T22_MOVE_DISTRIBUTION_V4_IMPLEMENTATION.md) | Integrate Move Distribution V4 | engine/content/qa | T21 |
| [T23](T23_RESEARCH_ECONOMY_V1_IMPLEMENTATION.md) | Integrate Research Economy V1 | content/engine/save/maps/qa | T22 |
| [T24](T24_REWARD_ENCOUNTERS_V2_IMPLEMENTATION.md) | Integrate Reward Encounters V2 | content/engine/save/maps/qa | T23 |
| [T25](T25_FACTORY_HIGH_MODES_V2_IMPLEMENTATION.md) | Integrate Factory High Modes V2 | content/engine/save/ui/qa | T24 |
| [T26](T26_CODEX_BATTLE_BRIDGE.md) | Codex対戦ブリッジをStage 43で実証する | platform/tooling/engine/qa | T25 |
| [T27](T27_CODEX_BATTLE_RUNTIME.md) | Codex操作6→3対戦をStage 44へproduction統合する | engine/ui/content/tooling/qa | T26 |
| [T28](T28_CODEX_BATTLE_REWARDS_RELEASE.md) | 任意報酬とiPad最終ゲートをStage 45で完成させる | engine/save/tooling/release/qa | T27 |
| [T29](T29_WINDOWS_BATTLE_CATALOG.md) | Windows対戦カタログをNPC前の一括生成導線へ接続する | engine/save/tooling/qa | T28 |
