# PR16 Issue19: 研究タマゴ孵化後のform・技保持

状態 `PASS_RESEARCH_HATCH_SCOPED`。限定受入 15/15。Actions終端 `True`。

source `258a0afc2be9c3428e2a0671bb151551e5c96fe2` / run `36145839263`。候補 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91` / 33554432 bytes、ROM変更0。

## 観測境界

通常配布17件を再実行せず、その保存原本のcontinued party200byte/Collection owner512byteを新開始fixtureへ結合。これは元saveから連続再開した証明ではない。開始map/queueもfixture。原本50cycle等・技・PP・個体identityは変更せず、通常方向キーによる全歩行、実孵化callback/ニックネーム取消、form/技順/PP保持、native孵化登録Save1回、通常Save1回、fresh-core Continue後party200byteを検証する。

7host書込API拒否・3guard区間。getterは区間外の読取り補助。同行個体の自然ななつき度/チェックサム変化は許容し、identity/技/HPは保持する。story/研究rank/連続配布からの到達・全Issue19・releaseは未受入。1281の原本除外方針を変更しない。

| case | 原本4技 | cycle | 実歩数 | 実測run |
| --- | --- | ---: | ---: | ---: |
| research-egg-1201 | [33, 39, 0, 0] | 50 | 13055 | 36138860612 |
| research-egg-1204 | [10, 111, 0, 0] | 50 | 13055 | 36138860612 |
| research-egg-1206 | [39, 181, 0, 0] | 50 | 13055 | 36138860612 |
| research-egg-1208 | [28, 232, 0, 0] | 50 | 13055 | 36138860612 |
| research-egg-1210 | [45, 252, 0, 0] | 50 | 13055 | 36138860612 |
| research-egg-1212 | [33, 111, 0, 0] | 50 | 13055 | 36145839263 |
| research-egg-1215 | [1, 139, 0, 0] | 50 | 13055 | 36145839263 |
| research-egg-1394 | [33, 45, 0, 0] | 50 | 13055 | 36145839263 |
| research-egg-1396 | [33, 174, 0, 0] | 50 | 13055 | 36145839263 |
| research-egg-1407 | [33, 43, 0, 0] | 50 | 13055 | 36145839263 |
| research-egg-1410 | [33, 181, 0, 0] | 50 | 13055 | 36145839263 |
| research-egg-1414 | [33, 55, 189, 232] | 50 | 13055 | 36145839263 |
| research-egg-1415 | [43, 52, 0, 0] | 50 | 13055 | 36145839263 |
| research-egg-1417 | [33, 268, 0, 0] | 50 | 13055 | 36145839263 |
| research-egg-1425 | [10, 43, 0, 0] | 50 | 13055 | 36145839263 |

未成功 `[]`。原実測matrix runの新unit23、host compile10、native10。旧配布/孵化/EXP/Bag/egg8/旧野生/ARM/Wiki再実行0。

## 次

Issue19: 研究タマゴ15種の保存個体fixtureからの実歩行・孵化後form/技・Save/fresh Continueを再実行しない。通常配布17件も保存受入を維持。次は未受入の釣り/隠し野生の特殊技順。1281は非学習ownerの既存方針で未受入。全供給/Issue19/release/active baseline切替は未完。

## 15件の終端確定

保存原本の5件と独立worker10件を限定受入。元run36138860612のcancelled/RUNNING/push skippedは改称していない。元runの終了時seed mtime検査完了や未保存の進行中caseの不存在は主張しない。成功した復元runとmatrix全12job・22artifact・全member・成果commitの直接親/祖先を照合した。終端専用runは新境界unitのみで、native/旧32・30・23unit/host/ARM/ROM変更/受入済み再実行0。

30画面は保存原本hashと非黒画面を確認。form/技UIの視覚受入、元saveから連続した配布→孵化、ストーリー到達は主張しない。元配布17件と研究孵化15件は変更影響がない限り再実行しない。

## 次の特殊野生調査を重複しないための引継ぎ

ソース調査のみ・native受入0・ROM変更0。Stage59のidentity正規化はreset_wild_moves=0。一方、研究経済adapterはFN_MOVE_FISHING/FN_MOVE_HIDDENへ委譲し、V4 adapterはQOL生成後にApplyWildInitialMovesを呼ぶ。QOL apply_research_profileはCreateMon後にタマゴ技を第4枠へ置く。外側のStage59だけ、または旧V4だけを根拠に不具合/保持を確定しない。次は候補ROMの実hook/delegateと生成→特殊技設定→再初期化順を限定観測する。正確な読取範囲とsource hashは固定状態JSONのlearnset_special_wild_next_probe/read_ranges・source_bindingsに保存。

1281 identity-only/自動fallback禁止、Issue19全体未完、release_ready=false、PR未merge、active baseline不変。
