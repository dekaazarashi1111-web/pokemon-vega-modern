# ChatGPTの固定再開入口

対象はPR #16 / `codex/modernization-followup-20260908`。毎回リモート最新HEADとPR状態を確認し、そのrefを読む。過去SHAへ戻さない。

## 正本と現在地

1. [AGENTS.md](AGENTS.md) の安全・検証・Git規約。
2. [固定状態JSON](content/modernization/pr16_wiki_first_execution_plan.json) の next_action と owner_execution_plan。
3. [Wiki R0.1の完了証拠と入口](docs/PR16_WIKI_READABILITY_STATUS_JA.md)。
4. [閲覧改善の範囲/完成条件](docs/PR16_WIKI_READABILITY_PRIORITY_JA.md) と [継続する長期方針](docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md)。

R0.1は別出力として実装・限定検証・パッケージ生成/展開確認・公開・実物提示受領まで完了。旧R0は不変。成功済みの生成/28試験/nativeを変更影響なしに再実行しない。実在入口/公開commit/ZIP hashはwiki_readabilityに保持する。


## 次の未完作業

現在の next_action は SAVE_CAPACITY_SELECTED_MAP_ASSET_READER。正しいARM Tileset ABI（callback+0x10/属性+0x14）と保存した実map lookup/descriptor候補から、0x0880FA64の実asset extentとcaller/read全4byteを限定して閉じる。旧0件原本はABI不整合の履歴であり不存在証明ではない。今回のlookup/probe/32試験、旧LZ探索/30試験を無変更再走しない。正式789/85・選定残6・安全容量0。窓外跨り/間接参照/退役移管/heap/controller/局所Saveは未完。 固定JSONのread_pathsを使う。

所有者が閲覧版で案を検討する間も、実作業セッションでは保存容量→CI整合→追加機構の技術確認を継続する。未承認バランス案や新メガ/Gmax/Zの対象・性能は決めない。無人バックグラウンド実行の約束ではない。

## 毎回の終了

同じ状態JSONと固定引継ぎMDへ実完了・根拠・残件・最新Actions・具体nextを保存する。両ログはappend-only、同taskを重複しない。限定検証と最終index private guardの結果を区別し、全体CI greenを推測しない。小さな単親通常commitを明示許可された同branchへ非force反映し、push前後HEAD/対象blobを照合する。原本ROM/Save101と受入証拠を保持。全クリ対象外（PASSではない）、保存安全性は必須。merge・draft解除・公開release・active baseline切替は別許可なしに実行しない。
