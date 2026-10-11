# ChatGPTの固定再開入口

対象はPR #16 / `codex/modernization-followup-20260908`。毎回リモート最新HEADとPR状態を確認し、そのrefを読む。過去SHAへ戻さない。

## 正本と現在地

1. [AGENTS.md](AGENTS.md) の安全・検証・Git規約。
2. [固定状態JSON](content/modernization/pr16_wiki_first_execution_plan.json) の next_action と owner_execution_plan。
3. [Wiki R0.1の完了証拠と入口](docs/PR16_WIKI_READABILITY_STATUS_JA.md)。
4. [閲覧改善の範囲/完成条件](docs/PR16_WIKI_READABILITY_PRIORITY_JA.md) と [継続する長期方針](docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md)。

R0.1は別出力として実装・限定検証・パッケージ生成/展開確認・公開・実物提示受領まで完了。旧R0は不変。成功済みの生成/28試験/nativeを変更影響なしに再実行しない。実在入口/公開commit/ZIP hashはwiki_readabilityに保持する。


## 次の未完作業

現在の next_action は SAVE_CAPACITY_NEXT_SELECTED_ORIGIN_BINDING。対象0x086C51BFの4byteを、実子機ARM callerからSWI11が消費する条件付きLZ77 tokenとして正式型登録。旧788/86のreference-chainを原本のまま継承し、1件だけ追加して789/85、選定窓の残り7→6。他の未知85行/選定6行は完全不変。新25型差分試験PASS。新native/候補復元/旧受入再走0、安全容量0。 次の選定窓origin 0x0880FA64を保存symbol近傍から固定asset/現候補の実consumerへ限定的に結ぶ。残る選定窓6行・正式789分類/85未知・安全容量0。Berryの親13profile/子機entry/LZ native/25 reader試験/25型差分試験は変更影響がない限り再走しない。全874scan/窓最適化は再走不要。旧owner退役・移管、窓外跨りread/間接参照、heap/controller、局所Save/fresh Continueは未完。 固定JSONのread_pathsを使う。

所有者が閲覧版で案を検討する間も、実作業セッションでは保存容量→CI整合→追加機構の技術確認を継続する。未承認バランス案や新メガ/Gmax/Zの対象・性能は決めない。無人バックグラウンド実行の約束ではない。

## 毎回の終了

同じ状態JSONと固定引継ぎMDへ実完了・根拠・残件・最新Actions・具体nextを保存する。両ログはappend-only、同taskを重複しない。限定検証と最終index private guardの結果を区別し、全体CI greenを推測しない。小さな単親通常commitを明示許可された同branchへ非force反映し、push前後HEAD/対象blobを照合する。原本ROM/Save101と受入証拠を保持。全クリ対象外（PASSではない）、保存安全性は必須。merge・draft解除・公開release・active baseline切替は別許可なしに実行しない。
