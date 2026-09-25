# PR16 Issue19: 研究タマゴ孵化後のform・技保持

状態 `PASS_RESEARCH_HATCH_SCOPED`。限定受入 15/15。Actions終端 `False`。

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

未成功 `[]`。今回新unit23、host compile10、native10。旧配布/孵化/EXP/Bag/egg8/旧野生/ARM/Wiki再実行0。

## 次

15研究孵化の保存成功native/旧unit/host/ARMを再実行せず、Actions/artifact終端だけ照合。

## 独立workerと集約記録

先行5件はcancelled runの保存PASS原本から復元したまま再実行0。残10件だけを1case/workerで実行。C/fixture/原本50cycle・歩数・通常操作/Save検証は変更せず、原本32unitを継承。各workerのsource/compiled/protected、raw、ZIP/画像を集約jobで照合し、集約jobだけが同branchへpushする。15件の機械的結果が揃っても、run全体の終了と成果commit/artifact照合まではActions終端未確定。
