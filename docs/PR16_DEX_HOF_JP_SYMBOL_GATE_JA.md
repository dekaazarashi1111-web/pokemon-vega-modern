# 日本語symbolの住所・長さ分離

## 再構成した範囲

2026-10-07、固定HEAD `8a7c82babf017ae1518b4a81c96d101e5c7faffd` から未commitだった日本語symbol gateを再構成した。過去に報告された30試験や未commit blobを今回の証拠として流用しない。

`40Cakes/pokebot-gen3@3bd0b70c82a723161fa2e311c20029cf7d6ead33` の公開loaderは、言語別YAMLで住所を置換した時に元symbolの長さを継承する。FireRedの固定英語symbol50,097件、言語patch181label、日本語住所143labelを全文照合した。このうち112labelの非zero長は英語由来であり、日本語serializerの終端ではない。空のpatchファイルは固定された正規入力で、取得漏れと区別する。

## 実装

- 全4公開sourceをcommit・path・size・SHA-256・実Git blobへ固定する。
- loaderはASTで住所のみ置換する代入を照合し、取得した外部Pythonを実行しない。
- symbolとYAMLを全文解析し、未対応文法・重複言語・未知入力・改変byteを拒否する。
- 日本語住所、継承された英語長、日本語EOS込みextentを別fieldにする。住所差、隣接symbol、呼出側が付け足した長さから日本語extentを作らない。
- 既存95未知全fieldを独立した固定hashへ結び、対象3件を未知のまま保存する。新ROM window・型region・分類追加は0。

正本結果は `content/modernization/pr16_dex_hof_jp_symbol_gate_checkpoint.json`。専用source-only Actionsは固定公開sourceを再照合し、focused testsと全checkoutの固定再開bindingを検証する。ROM再生成・旧native・旧分類suiteは実行せず、private inputを取得しない。

## 次工程

083DDEE1/083DE02B/083DE6ABについて、固定した日本語symbolまたは生成crosswalkから両側label、EOS込みserializer extent、現実literal/table cell、consumer APIを結ぶ。住所のみのcrosswalkは候補探索に限る。未解決のaddress conflictや英語順序から推定したlabelを採用しない。必要範囲が独立に閉じるまで未知を保持する。

分類779/95、全親証拠、133曲/50asset、115owner/52保存owner、正式ROM/Save101は不変。旧egg15118byte保護・安全容量0を維持する。単一controller6528の本番配線とシオウ通常回復・保存・cold Continueは未完。
