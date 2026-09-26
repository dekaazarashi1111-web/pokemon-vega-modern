# PR16 Issue19: Collection学習owner配布

状態 `PASS_COLLECTION_GIFTS_LEARNING_SCOPE`。学習owner限定受入 17/17、定義全体18件中1件は既存方針で保留。Actions終端 `True`。

source `cc160e5b9127a0acd32ddd65def74438c9b6a852` / run `36121122707`。候補 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91` / 33554432 bytes。ROM/runtime/原本方針は変更しない。

## 範囲と保留

受付はNPC/objectではなく通常A入力のBGイベント。legacy `COLLECTION_NPC_INITIAL_MOVES_SAVE_CONTINUE` / `npc_script` はschema互換名でありNPC同定を意味しない。

固定form2と研究タマゴ15。初期party、開始場所と向き、全unlock、未受領ownerはfixture。実BG受付のroot/menu/page/選択、配布、原本初期技/PP、通常Save、fresh-core Continue、再訪取消を検証。ストーリー到達・研究ランク獲得・研究タマゴ孵化は含まない。7host書込APIを拒否し、getterはguard区間間の読み取り補助として分離。

ギザみみピチュー1281は `EXCLUDED_REMAKE_FORM_IDENTITY_ONLY` / `IDENTITY_ONLY_NO_REPLACEMENT` / payloadなし。自動fallback禁止・既存4技保持を優先し、通常ピチューの技流用や空4技を成功期待値にしていない。この配布初期技は未受入。初回run36110983368はこの期待値境界で停止、native/host0。旧22unit成功原本を継承し再実行しない。

| case | species | level | egg | 原本4技 | 実測run |
| --- | ---: | ---: | ---: | --- | ---: |
| fixed-form-1254 | 1254 | 50 | 0 | [60, 62, 199, 492] | 36119380600 |
| fixed-form-1390 | 1390 | 50 | 0 | [184, 408, 44, 530] | 36119380600 |
| research-egg-1201 | 1201 | 1 | 1 | [33, 39, 0, 0] | 36119380600 |
| research-egg-1204 | 1204 | 1 | 1 | [10, 111, 0, 0] | 36121122707 |
| research-egg-1206 | 1206 | 1 | 1 | [39, 181, 0, 0] | 36121122707 |
| research-egg-1208 | 1208 | 1 | 1 | [28, 232, 0, 0] | 36121122707 |
| research-egg-1210 | 1210 | 1 | 1 | [45, 252, 0, 0] | 36121122707 |
| research-egg-1212 | 1212 | 1 | 1 | [33, 111, 0, 0] | 36121122707 |
| research-egg-1215 | 1215 | 1 | 1 | [1, 139, 0, 0] | 36121122707 |
| research-egg-1394 | 1394 | 1 | 1 | [33, 45, 0, 0] | 36121122707 |
| research-egg-1396 | 1396 | 1 | 1 | [33, 174, 0, 0] | 36121122707 |
| research-egg-1407 | 1407 | 1 | 1 | [33, 43, 0, 0] | 36121122707 |
| research-egg-1410 | 1410 | 1 | 1 | [33, 181, 0, 0] | 36121122707 |
| research-egg-1414 | 1414 | 1 | 1 | [33, 55, 189, 232] | 36121122707 |
| research-egg-1415 | 1415 | 1 | 1 | [43, 52, 0, 0] | 36121122707 |
| research-egg-1417 | 1417 | 1 | 1 | [33, 268, 0, 0] | 36121122707 |
| research-egg-1425 | 1425 | 1 | 1 | [10, 43, 0, 0] | 36121122707 |

未成功学習owner `[]`。全party200byte/元party100byte、owner CRC/claim bit、4技/PP/PP Ups/HP/egg getter、frame/counterをraw textで照合。固定claim保持は確認するが、二重受取の実選択は含まない。

今回新scope-unit 0、旧unit実行 0、host compile 1、native 14。受入済み自然配布/孵化3・EXP/Bag/egg8/旧野生/ARM/Wikiは再実行しない。

## 次

Issue19: Collection学習owner17経路の通常配布・原本初期技・Save/fresh Continueは保存受入から再実行しない。ギザみみピチュー1281は既存EXCLUDED_REMAKE_FORM_IDENTITY_ONLYにより技の自動補完/通常ピチュー流用禁止、配布初期技の受入保留。未受入の研究タマゴ孵化後のform/技保持、釣り/隠し野生の特殊技順を続ける。全Issue19/release/active baseline切替は未完。

## 観測原本の適用範囲

run36119380600の固定2件と研究1201はheadless実測の機械的受入。保存画像9枚は単色のため画面受入に使わない。1201は先頭cursorと一覧表示が同frameになる誤拒否を、raw menu/frameを追加照合して原本再検証した。失敗run/原本は成功へ書き換えていない。この3件を再実行せず、残りだけ描画初期化後の別controller identityで実行する。画像の非単色検査と意味内容の目視確認を区別する。

## 終端確定と再開境界

学習owner17/17の配布・初期4技/PP・通常Save・fresh-core Continue・再訪取消を限定受入。うち14件の42画像は保存ZIPと全フレームhashを照合して目視記録へ結合。先行3件の黒画像9枚は除外したまま。原本1281、ストーリー獲得、研究タマゴ孵化、特殊野生、Issue19全体、releaseはこの受入に含めない。

この17件や旧受入を理由なく再実行しない。状態JSONの次作業は特殊野生と研究タマゴ孵化の未受入経路。今回の機械実測入口は `scripts/pr16_collection_gift_observation.py`、終端確定は `scripts/pr16_collection_closeout.py`。直接旧18件driverを再実行しない。
