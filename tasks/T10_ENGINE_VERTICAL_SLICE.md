# T10 — Complete engine vertical slice

- Lane: `qa`
- Depends on: `T04, T05, T06, T07, T08, T09`

## Objective

Prove the integrated engine and the QOL-A core end-to-end before importing large Kanto content. QOL-B remains release scope but is integrated in T17 so it does not delay T13.

## Execute

1. Choose one appended species absent from Vega.
2. Choose one appended move, ability, held item, and evolution method.
3. Add a temporary debug gift or test map script that grants the species and item.
4. Test wild encounter, trainer battle, capture, level-up, move use, ability activation, item effect, evolution, Dex registration, save, restart, and load.
5. Run Vega baseline regression checkpoints.
6. Remove or guard debug-only access behind a build define.
7. Freeze engine manifest schema after the vertical slice passes.
8. Register the selected species through one Tohoku overlay fixture and prove that disabled/failed overlay selection returns the byte-equivalent original Vega encounter result.
9. `config/feature_matrix.csv` に `TEXT_SPEED=INSTANT`、`HATCH_MODE=FAST`、ダッシュ/自転車の速度目標、QOL-Aのrelease既定値を固定する。
10. ダッシュの同一路程をVega比25%以上、自転車を50%以上短時間化し、歩数、遭遇、孵化、毒、接触/座標event、warp、段差を各tileで1回だけ処理する。
11. field/battle文章を次の描画機会で即時表示し、変数、色、改ページ、選択肢、明示wait、効果音とscript同期順を維持する。
12. 経験アメ5種の共通callbackを既存数量選択UIへ接続し、`x1/x5/x10/すべて` を栄養drink、ハネ、ふしぎなアメ、テラピース、coin、努力値reset用品へ再利用する。専用画面は作らない。
13. 全体学習装置、現代孵化、SV式王冠、mint/特性道具、IV/EV表示、タマゴPC/queueを同じ継続saveで通す。
14. 最小Factory縦切りとして、Lv.50 rental候補6体から3体を既存party/list/Yes-No UIで選び、single 3v3を3連戦し、勝利後の1体交換、連勝/BP、敗北・辞退・退出後の元party/持ち物完全復元まで通す。rental/対戦相手は図鑑のseenだけを更新しcaughtを更新しない。専用record画面は作らず標準messageで表示する。
15. debug用の施設外NPCから遭遇credit 1回を使用し、容量確認、支払い、固定pool抽選、通常scripted wild battleの即時開始、逃走後の同一個体再挑戦、捕獲成功による保留消去を通す。
16. T06所有の既存Vega IDだけを使うsynthetic trainer fixtureで、`AI_SEMI_SMART`、`AI_FULL_SMART` single、`AI_FULL_SMART` doubleを各1戦通し、技評価、交代、設置/積み、double連携、trainer itemとbattle後saveを検証する。production trainer rowはT12/T16までbindしない。
17. T02で特定したTM-use hookへ `TM_REUSE_LICENSE` adapterを接続し、synthetic flagの直前はTMを1個消費、直後は同じTMを消費せず再利用でき、save/load後も境界が維持されることを通す。
18. Mirage synthetic戦で相手の仮想held itemを盗む・交換するmoveを実行し、勝利/敗北/辞退後にplayer party/bagへ残らないことを通す。
19. T02で特定したencounter/DexNav hookへsynthetic `table_profile=NORMAL|RESEARCH` selectorを接続する。NORMALは元tableへbyte-equivalentに戻り、RESEARCHは入力されたlevel/IV/ability/egg move/held item/shiny policyを適用してsave/load後も選択状態を保つ。production rowはT12/T15/T16までbindしない。
20. 既存mapのdebug NPCからsynthetic 4-star `RAID_HIGH_DIFFICULTY` を1戦起動し、partner、shield、勝敗、捕獲、報酬、終了後flag clearを標準message/Yes-Noと既存battle UIだけで通す。

## Required outputs

- `reports/generated/engine_vertical_slice.md`
- `tests/fixtures/engine_slice.json`
- `config/feature_matrix.csv`
- `reports/generated/qol_vertical_slice.md`
- `tests/fixtures/qol_slice.json`
- `tests/fixtures/qol_movement_courses.json`
- `tests/fixtures/factory_trial.json`
- `tests/fixtures/reward_encounter.json`
- `tests/fixtures/trainer_ai_slice.json`
- `tests/fixtures/research_encounter_slice.json`
- `tests/fixtures/raid_slice.json`

## Acceptance gates

- [ ] All selected new elements work in one continuous save.
- [ ] Vega baseline smoke tests pass.
- [ ] No debug code is active in release config.
- [ ] Manifest schemas are versioned.
- [ ] The Tohoku overlay adds content without replacing an original Vega slot or 1% encounter.
- [ ] QOL-Aの全機能がrelease configで有効になり、`docs/QOL_POLICY.md` の既定値と一致する。
- [ ] 経験アメは100/800/3000/10000/30000を選択個体だけへ加算し、EV、他party、level途中の技習得・進化を誤らない。
- [ ] 即時文章と高速移動がVegaのscript/battle順、tile event、warp、saveを壊さない。
- [ ] QOL-Aの表示・設定は既存UI部品だけで操作でき、新規full-screen UIや専用演出assetを必要としない。
- [ ] 3連戦Factory trialは新規full-screen UIなしで完走でき、交換・敗北・辞退・save/resetの全出口で元party/HP/PP/status/持ち物が完全復元される。
- [ ] 施設外NPCは標準message/list/Yes-Noから通常捕獲戦を即時起動し、専用捕獲mapやcutsceneを必要としない。
- [ ] `AI_SEMI_SMART` / `AI_FULL_SMART` のsingle/double synthetic縦切りが同じsaveで完走し、固定CFRU knowledge model、通常Vega battle、save、RNGを破損しない。
- [ ] TM license境界の消費/再利用とMirage仮想item隔離が、既存UIだけの継続saveでPASSする。
- [ ] Synthetic NORMAL/RESEARCH selectorが同一map/seedでprofileだけを切り替え、NORMAL fallback、RESEARCH品質入力、save/loadを壊さない。
- [ ] Synthetic Raidは専用map/full-screen UIなしで完走し、終了後に通常battle/gimmick/saveへ一時stateを残さない。

## Finish

1. タスク固有のacceptance checkだけを実行する。WSLではrepository全体のdefault verifyを実行しない。
2. Update reports, `design/run_log.md`, and `design/version_log.md`.
3. Mark the task done with `python3 scripts/taskctl.py done T10 --summary "..."`.
4. Stage the intended task/state/log changes, run `python3 scripts/validate_task_graph.py` and `python3 scripts/guard_private_files.py` against the final index, then commit with a message beginning `T10:`.
5. If another task is READY, continue without waiting for approval.
