# PR16 Issue19: 研究タマゴ孵化後のform・技保持

状態 `PARTIAL_RESEARCH_HATCH_RECOVERED_AFTER_TIMEOUT`。限定受入 5/15。Actions終端 `False`。

source `e12eda4098837fcd434194e3da713f2837209450` / run `36138860612`。候補 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91` / 33554432 bytes、ROM変更0。

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

未成功 `['research-egg-1212', 'research-egg-1215', 'research-egg-1394', 'research-egg-1396', 'research-egg-1407', 'research-egg-1410', 'research-egg-1414', 'research-egg-1415', 'research-egg-1417', 'research-egg-1425']`。今回新unit32、host compile1、native5。旧配布/孵化/EXP/Bag/egg8/旧野生/ARM/Wiki再実行0。

## 次

研究孵化checkpointの失敗原本を確認し、未成功caseの境界だけ修復。受入済み配布/孵化/旧検証を再実行しない。

## 45分中断からの原本復元

原本run36138860612はcancelled、原本verificationのstatusはRUNNINGのまま保存。record/guard/artifact uploadは成功、pushはskipped。独立復元runでZIP全体digest・完全集合・source/compiled/protected binding・5caseの保存rawを照合し、元verificationを改作せず別checkpointへ投影した。欠けたfinallyのproof/screenshot indexは復元値と明示する。元run末尾のseed mtime等の一括検査完了は主張しない。未保存の進行中caseの不存在も主張しない。

5件はいずれも原本50cycle、実歩数13055。正常孵化・form/初期技/PP保持・通常Save・fresh Continueを機械的に確認。10画面はフィールド復帰を目視し、個体のform/技UIの視覚受入とは区別した。保存成功5件と旧32unitは再実行していない。

研究孵化の保存成功5件と32unitは再実行しない。残り10件を1case/workerの独立Actionsで並列測定し、集約jobだけが記録・非force pushする。50cycle/実歩数/既存C・候補ROMは変更しない。15件完了後に特殊野生へ。
