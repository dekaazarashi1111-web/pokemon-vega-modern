# current_state.md

最終更新: 2026-08-12

## 現在地

- マイルストーン: Gate A完了 / 上流再現・完全監査・schema設計へ移行。
- ユーザー提供の4 ZIP、3 ROM、IPS、UPSをGit管理外へ取り込み、原本とのSHA-256一致を確認済み。
- 4 ZIPは破損・パストラバーサルなし。プレイブック基盤、競合監査、V1来歴資料、V2二地方設計資料を役割別に配置済み。
- clean ROMはBPRJ01 Rev.00、CRC32 `3B2056E9`。IPS/UPSから個別生成した参照ROMは提供済み2 ROMとbyte一致。
- 厳密競合結果は775 byte中、同値191、異値584。単純なパッチ結合はNO-GO。
- 上流pinは2026-08-12時点のGitHub既定ブランチHEADへ固定する。
- T00成果としてportableな `state/source-lock.json`、preflight、参照ROM、exact auditを生成済み。同一条件の2回目quickstartでcache reuseを確認済み。
- `VEGA_CFRU_DPE_統合設計_V2_二地方生態版` をactive review資料に切替済み。V1は来歴保存専用。
- 元FireRedのカントーを新規 `KANTO_*` 名前空間へ複製し、殿堂入り後にトーホクと常時往復できる二地方構成は実現可能と判定。V2の47地点は生態設計単位であり、raw map総数ではないためT11で全建物・階層・warpとのcrosswalkを生成する。
- ブロッカーなし。

## 次の正本タスク

`design/tasks_next.md` と `python3 scripts/taskctl.py next` を正とする。T00完了後のREADY候補はT01、T02、T12である。

次の並列候補:

- T01: DPE-JP/CFRU-JP上流ビルド再現。
- T02: ROM/RAM/SaveBlock/IDの完全監査。
- T12: 記号コンテンツschemaとgenerator。

T11（カントーimporter）はT02完了後に開始する。

## 固定済み方針

- Vega本編を母体とし、Factory UPSは参照専用にする。
- Vega Move ID 0〜511と既存Species IDを固定する。
- 追加IDはmanifestから生成する。
- カントーは殿堂入り後の別名前空間として復活させる。
- カントー本土とトーホクは連絡船で双方向移動可能にする。ナナシマはV2本体のscope外。
- V2の統合設計CSVはreview状態であり、進化重複、フォームキー、ID型、道具参照を修正するまで実装正本にしない。

## 再開時の確認先

1. `AGENTS.md`
2. このファイル
3. `design/agent_context_map.md`
4. `design/tasks_next.md`
5. READYになった `tasks/T*.md`

入力詳細は `design/import_inventory.md`、資料評価は `design/import_review.md`、採択済み判断は `design/decisions.md` を参照する。
