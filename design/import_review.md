# import_review.md

## 結論

受領した設計資料は次の優先順位で使う。

1. `vega_modern_codex_playbook`: 再現ビルド基盤、T00〜T18のDAG、検証雛形。
2. `vega_cfru_integration_audit`: パッチ競合の一次証跡と監査ツール。
3. `VEGA_CFRU_DPE_統合設計_V2_二地方生態版`: トーホク＋カントーの完成像・進行・生態・イベントに関するactive review資料。
4. `VEGA_CFRU_DPE_統合設計` V1: V2の来歴確認専用。新規判断には使わない。

完成目標は、FireRed日本版Rev.0からVegaを再生成し、公開ソースのDPE-JP/CFRU-JPをVega互換で移植し、元FireRedのカントー本土を新規名前空間へ復元して、トーホクと自由往復できる32 MiB ROMを再現ビルドすることである。最終配布物はROMを含まない単一差分パッチとする。

## V2の完全性と位置付け

- ZIP: 465,121 bytes、SHA-256 `fb7c542a50aaec7ae25af70cdb100f4c71effb5e9ddc4f09c6365f79fa76cd06`。
- 展開49ファイル。`manifest.json` 47件と `MANIFEST.sha256` 47件は相互一致し、size/hash 47/47 PASS。
- 付属設計検査は59/59 PASS。ただし検査コードは同梱されず、件数・空欄・参照整合中心であり、ROM動作、hook、SaveBlock、マップ接続を保証しない。
- package statusは `design-specification-only`。V2のCSVをそのままgenerator入力へ昇格しない。
- V2記載のDPE基準 `520937c...` は来歴として扱い、実装はD-005の最新固定pin `10ff98c...` を正とする。

## V2で採用する二地方設計

- 公式1025種、541進化系統、541系統×2地方＝1,082行の入手導線。
- トーホク49生態地点はVega既存野生枠を直接置換せず、条件付きoverlay、DexNav、時間帯、大量発生へ追加する。
- カントー47生態地点は元FireRedの景観・施設を使い、原作系統35〜60%を残しつつポストゲーム用に再構成する。
- 初回殿堂入り後、連絡船でクチバへ到着し、その後はトーホクと常時往復可能にする。
- カントーの8認定章はVegaバッジと分離する。
- NPC再利用26件、重要アイテム置換24件、追加イベント34件、特殊個体125種の共有捕獲状態を設計入力にする。
- カントー原作のstory flag、badge、trainer、item、warp、varは再利用せず `KANTO_*` へ変換する。

V2の「47地点」は生態・進行上の論理地点であり、全建物・階層を含むraw map数ではない。カントー復元の物理scopeはT11でclean BPRJ Rev.0とpokefireredから全資産inventoryを作り、V2キーとのcrosswalkを生成して確定する。ナナシマはV2本体のscope外である。

## V2にも残る意味課題

V2はV1の複数CSVをbyte同一で引き継いでおり、付属59検査が次を検出していない。

1. `進化条件変換マスター.csv` にID以外が同一の余剰23行・21群が残る。
2. 進化表にfrom/toフォームキーがなく、同じ全国番号を使うリージョン進化を区別できない。
3. Vega保護台帳の公式205件は全国番号が `276.0` のような小数文字列で、整数文字列の他CSVと直接joinできない。
4. `じばのコア`、`コケのコア`、`こおりのコア`、`フィールドコア` 等、進化表が参照する救済道具の一部が道具入手マスターにない。
5. フォーム509行は分類方針であり、統合後Form ID・数値flag・具体配置の実装台帳ではない。
6. 技・特性・道具・hookはTEMPLATE中心、Species 1206行は未割当、SaveBlock offsetも未確定。
7. Z／ダイマックス／テラは機能profileで任意P2だが、後半イベントとQAの一部が前提にしている。v1.0必須scopeを別ADRで決める必要がある。
8. V2は新規ゲーム必須を標準とし、旧Vega save移行を試みる現行方針との最終判断が未確定。

T12で型正規化、フォームキー追加、意味重複解消、全参照整合validatorを実装してから `manifests/` / `content/` へ昇格する。

## 競合監査から継続する技術方針

単体監査パッケージの `MANIFEST.sha256` は15/15 PASS。主要事実は次のとおり。

- Vega IPS変更量: 3,782,136 byte。
- Factory UPS変更量: 14,680,526 byte。
- 直接重複: 269 ranges / 775 byte。
- 技名・技データpointer関連: 169 ranges / 533 byte（68.774%）。
- clean ROMによる厳密比較: `SAME_TARGET=191`、`DIFFERENT_TARGET=584`。

したがってFactory UPSは参照専用とし、パッチを重ねず公開ソースからMove、battle、Speciesの順で移植する。

## 資料の優先順位

矛盾時は次の順で判断する。

1. `AGENTS.md` の運用・安全規則。
2. `design/decisions.md` の採択済みADR。
3. `design/tasks_next.md`、`tasks/task_graph.json`、選択タスクの `tasks/T*.md`。
4. `MASTER_PLAN.md` と `docs/` の現行技術方針。
5. `audit_seed/` と生成監査の測定証拠。
6. V2二地方設計のactive review資料。
7. V1来歴資料。

測定証拠が仕様と矛盾する場合は、黙って片方を採らずADRを追加して解決する。
