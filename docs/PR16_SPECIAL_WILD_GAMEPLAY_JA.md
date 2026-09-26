# 特殊野生: 通常操作検証

特殊野生の通常UI準備: PASS_SAVED_CANDIDATE_UI_INPUT_BINDING_NOT_GAMEPLAY。直接7process/8callは保持。通常取得/捕獲/保存は未受入。

Issue19: 保存済み0205af9b候補と特殊野生UI準備checkpointを再利用し、map3/38の通常釣竿・map3/63のスキャナーから特殊個体捕獲→通常Save→fresh Continueを検証する。地形/道具bindingは実取得受入ではない。7host書込み禁止、開始fixtureと観測を分離し、旧直接7process/8call・旧受入・ARMは再実行しない。

候補 `0205af9bd2d92b1b3303195ab0cc84e5ea0f3de390ade15d9f8ce42a6dcdd1a0`。保存8byte recipeのみ適用し、全候補hash/rollbackを照合する。地形のbehaviorは数値観測であり、釣り可否/到達成功を推測しない。

開始map/party/item/flag/RNGはfixture。通常釣竿/スキャナーUI→特殊個体捕獲→通常Save/fresh Continueは別native証拠が必要。map3/19の130行は改作しない。

run `36218655601` / source `8660fe70f4354333cf7647186663cacafa04451b`。失敗: `None`。
