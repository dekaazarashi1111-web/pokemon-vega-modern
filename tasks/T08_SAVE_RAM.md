# T08 — Resolve RAM and save compatibility

- Lane: `qa`
- Depends on: `T02, T03`

## Objective

Allocate CFRU/DPE state safely and define an explicit save compatibility policy.

## Execute

1. Merge RAM ownership maps and identify simultaneous-lifetime conflicts.
2. Move CFRU temporary state or Vega state as needed using named symbols instead of raw addresses.
3. Inventory Vega save sectors/blocks and CFRU save expansion changes.
4. Implement a save version marker and migration entry point.
5. Attempt direct Vega save compatibility first; implement one-time migration if practical.
6. Add save round-trip test fixtures and corrupted-version rejection.
7. Document whether old Vega saves are supported.
8. Allocate and test National Dex 1025 state, research rank, eight Kanto certifications, region/rotation/retry state, and 125 shared special-capture states.
9. `KANTO_TRAVEL_UNLOCKED`、`KANTO_VISITED`、`VEGA_HALL_OF_FAME`、認定章、現在地方、地方別heal/return anchor、初回警告確認をそれぞれ独立保存する。
10. 既存save移行では、早期checkpointまたは殿堂入りを満たすsaveに渡航権を1回だけ付与し、逆戻りさせない。
11. Escape/Teleport/dynamic warp/whiteoutが地方別anchorを使い、不正値時はクチバterminalまたはVega渡航元港へfail-safe復帰することを検証する。
12. `TEXT_SPEED`、孵化演出mode、全体学習装置ON/OFF、`natureMint`、Hyper Training 6能力bit、最大5個の預かりタマゴqueueをallocateする。badge等から導出できるQOL解禁条件は重複保存しない。
13. 新規saveとQOL fieldを持たない移行saveには `TEXT_SPEED=INSTANT`、`HATCH_MODE=FAST` を設定し、取得済み1個目badgeに応じて全体学習装置を既定ONにする。
14. Battle Factory用のBP、mode別current/best streak、一度限り報酬、unlock、施設中断marker、元party/HP/PP/status/持ち物backupを再配置し、入場前または復元完了後のどちらかへatomicに復旧できるようにする。
15. 施設外NPCのtyped遭遇creditと、支払い済みの保留遭遇1件を保存する。保留にはpool、species/form/level、personality、nature、IV、ability、shiny、Tera、generator version/fingerprint、validを持たせ、global RNGやgenerator更新後も同じ個体を再構成する。逃走・撃破・全滅・reset後も無償再挑戦でき、捕獲成功時だけ保留を消す。
16. 通貨/credit減算と保留遭遇生成を1 transactionとして既存save routineでbattle開始前に永続化する。save失敗時は減算と保留をrollbackして戦闘を開始せず、成功後のresetでは同じ保留へ戻す。
17. T02で採用したBP、調査point、arcade coinのowner、bit幅、上限、migrationをsave台帳へ登録する。arcade coinは監査で安全なら既存coin caseへmapし、そうでなければ名前付き新規fieldへ置く。獲得hookがない通貨は割当を予約せずDEFERする。
18. Mirageのcurrent/best record、段階reward claimと通貨ownerをFactoryから分離して台帳化する。T06のbattle-local仮想itemはsave対象に含めない。
19. `LEAGUE_I_CLEARED` と `LEAGUE_II_CLEARED` を既存安全flagまたは名前付き新規fieldへ割り当て、早期Kantoで認定章4個を取得済みでも強化LeagueをI→II→Finalの順に進める。
20. 地方別 `ENCOUNTER_TABLE_PROFILE=NORMAL|RESEARCH` を保存し、新規/移行saveと不正値はNORMALへ戻す。profile切替は元Vegaのwild tableや捕獲flagを変更しない。
21. Raidのshared capture key、一度限りreward claim、bonus tier unlock、進行中/retry markerをversioned ledgerへ割り当てる。125件の共有特殊捕獲stateと同じspecies/formを二重所有せず、捕獲・報酬・再挑戦を別field/transactionとして複製不能にする。

## Required outputs

- `config/ram_layout.csv`
- `config/save_layout.csv`
- `overlays/save_migration/`
- `reports/generated/save_compatibility.md`
- `tests/test_save_layout.py`
- `tests/test_facility_save.py`

## Acceptance gates

- [ ] No overlapping live RAM owners.
- [ ] New save data survives save/load and checksum validation.
- [ ] Unsupported old saves fail clearly rather than silently corrupting.
- [ ] Policy is documented and tested.
- [ ] Dual-region travel and shared capture state survive save/load without modifying Vega badges.
- [ ] 殿堂入り前のKanto内save/load/reset/heal/whiteoutで渡航権と帰還路が保持される。
- [ ] Kanto field permitや認定章はTohokuのHM/badge/story flagを変更しない。
- [ ] 育成・設定stateはparty↔PC、進化、save/load/reset後も保持され、タマゴqueueと個体dataに消失・複製がない。
- [ ] 施設中のsave/reset/中断/全滅から元partyと全付随stateをbyte-equivalentに一度だけ復元し、BP/連勝/一度限り報酬を複製しない。
- [ ] 保留遭遇は再起動後も再抽選されず、一度に1件だけ存在し、捕獲成功以外でcreditを二重消費しない。
- [ ] 支払いtransactionはflash確定前に戦闘へ入らず、save失敗・電断fixtureでも残高と保留が片方だけ更新された状態にならない。
- [ ] 有効通貨は上限、underflow、save/load、migrationを通り、DEFER通貨は表示・獲得・消費経路を持たない。
- [ ] MirageとFactoryのrecord/reward/currencyが相互更新されず、battle-local仮想itemがsaveへ永続化されない。
- [ ] League I/II clear stateがsave/load/migration後も保持され、未クリア段階を飛び越えない。
- [ ] 地方別NORMAL/RESEARCH profileがround-tripし、新規/移行/不正値はNORMAL、Raidのcapture/reward/retry/bonus tierはreset・migration後も重複claimされない。

## Finish

1. タスク固有のacceptance checkだけを実行する。WSLではrepository全体のdefault verifyを実行しない。
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T08 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T08:`.
5. If another task is READY, continue without waiting for approval.
