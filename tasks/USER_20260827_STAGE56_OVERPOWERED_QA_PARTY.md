# USER-20260827-STAGE56-OVERPOWERED-QA-PARTY — Stage56標準QA手持ちを更新する

- Status: `IN_PROGRESS`
- Lane: `qa/save/codex-battle/ipad`
- Depends on: `USER-20260827-STAGE56-TEST-READY-SAVE`
- Queue ID: `USER-20260827-STAGE56-OVERPOWERED-QA-PARTY`
- Baseline: Stage 56 / ROM SHA-256 `9309c073798dc363174458ebcb75bf3f1e86d475dcd129b74875d5a6bb875778`

## 目的

今後の標準QAセーブの手持ちを、先頭のミュウツーを含むLv.100の強力な6体へ更新する。全員を攻撃技4つとし、ダブルバトルを素早く確認できる全体攻撃も持たせる。既存のCodex受付前、序盤取得済み、全個体服従という進行状態は維持する。

## 受入条件

- [ ] 標準profileと生成器のpartyが、先頭のミュウツー＋強力な5体、全員Lv.100になる。
- [ ] 全24技が攻撃技で、各個体がダブルバトル向けの複数対象技を1つ以上持つ。
- [ ] 生成した131,072-byte saveが既存Stage56 ROMで読み込める。
- [ ] iPadの同名Stage56 saveを停止状態で更新し、size／SHA-256／read-back一致を確認する。実機プレイ／人手承認は要求しない。
- [ ] focused verification、ログ、version記録、task完了commitを残す。
