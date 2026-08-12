# decisions.md（追記のみ）

重要な設計判断、根拠、代替案、影響タスクを記録する。既存項目は削除・書換えず、後続ADRで置き換える。

## 2026-08-12 — D-001: パッチ重ね当てではなくソース移植

- 決定: Factory UPSをVegaへ直接適用せず、Vegaを母体にDPE-JP/CFRU-JP公開ソースを移植する。
- 根拠: 両パッチは269区間・775 byteを直接二重変更し、厳密比較では584 byteが異なる最終値になる。直接競合外にもhook、repoint、RAM、SaveBlock、ID依存がある。
- 却下: IPS/UPSの順次適用、checksum無効化、重複byteだけの片側優先。
- 影響: T00〜T10、T17、T18。

## 2026-08-12 — D-002: Vega既存IDをcanonicalとして固定

- 決定: Vega既存のSpecies IDとMove ID 0〜511を移動しない。追加IDはmanifestへ登録し、生成物だけが数値を参照する。
- 根拠: Vegaのストーリー、トレーナー、野生、進化、イベント参照を一括で壊さず、CFRU/DPE側を対応表で適応できる。
- 影響: T02、T04、T05、T07、T09、T12、T16。

## 2026-08-12 — D-003: カントーは殿堂入り後の別名前空間

- 決定: 原作FireRedのカントーをVegaクリア後の地方として復活させ、Map/Trainer/Flag/Varを `KANTO_*` 名前空間で新規割当する。最初の縦切り入口はクチバ港とする。
- 根拠: Vega本編の進行状態を維持しつつ、原作地形・NPC配置・ジム構造を再利用できる。
- 影響: T11、T13〜T17。

## 2026-08-12 — D-004: 地形を活用し、グローバル状態は再定義

- 決定: カントーの地形、NPC座標、ジム構造は活用できるが、原作ストーリー依存script、badge、trainer、item、warp、flag、varはVega向けに再定義する。
- 根拠: FireRedのグローバル状態を復元するとVegaの同一ID・イベントと衝突するため。
- 影響: T11、T13〜T16。

## 2026-08-12 — D-005: 2026-08-12時点のGitHub HEADを上流pinに採用

- 決定: CFRU-JP `e24a16fe39e27ae162faf5b78596d1f3df18489d`、DPE-JP `10ff98c85ebf37ab5cb39a41b6e9b50f06efb19e`、pret/pokefirered `c75f352304d529f6ba92d4f74b9cf8b5c3810788` を固定する。
- 根拠: 各リポジトリの既定ブランチHEADをGitHubへ直接照会した結果。DPE設計CSVの旧基準 `520937c0959e2a1be57771d1dfee9f6fee806c7e` は現HEADの1コミット前で、差分は `src/Back_Pic_Coords_Table.c` の1行のみだった。
- 代替: 設計CSVの旧DPE pinを実装pinに使う案。最新版を望むユーザー方針により不採用。
- 影響: T00〜T02、T07、T09、T12。

## 2026-08-12 — D-006: タスク状態の正本を一本化

- 決定: `design/tasks_next.md` を唯一の状態正本、`tasks/task_graph.json` を依存関係正本、`tasks/T*.md` を完了条件正本とする。`state/task_status.json` は生成ミラーにする。
- 根拠: プレイブックと既存運用の二重状態更新によるdriftを防ぐため。
- 影響: 全タスク、`scripts/taskctl.py`、検証。

## 2026-08-12 — D-007: 受領した統合設計データはreview状態から開始

- 決定: `design/imported/VEGA_CFRU_DPE_統合設計/**` は受領時点の不変参照とし、個別レビュー・修正後にmanifestや実装用データへ昇格する。
- 根拠: パッケージ整合性はPASSしたが、フォームを区別できない進化条件、意味重複、全国番号の小数文字列、救済道具の参照欠落などが独立監査で見つかった。
- 影響: T02、T05、T07、T09、T12、T16。

## 2026-08-12 — D-008: 効率化はキャッシュ・並列化・生成で行う

- 決定: 入力hash・source commit・tool versionが同一の成果は再利用し、独立作業をファイル所有権付きで並列化し、ID/表はgeneratorで作る。検証ゲートは省略しない。
- 根拠: 長期開発での重複解析、セッション再開コスト、手作業の転記ミスを抑えるため。
- 影響: 全タスク。

## 2026-08-12 — D-009: V2二地方生態版を設計の優先資料にする

- 決定: `design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/**` を、完成像・進行・二地方生態・イベント設計のactive review資料とする。V1は来歴保存専用にする。
- 根拠: V2はトーホク49地点、カントー47地点、541系統×2地方、追加イベント34件を定義し、JSON/SHA manifest 47/47が一致した。
- 制約: V2は設計仕様書であり、進化重複、フォーム識別、ID型、道具参照、未確定templateをT12等で解消するまでCSVを実装正本にしない。上流実装pinはV2記載の旧DPE commitではなくD-005を正とする。
- 置換: D-007の対象範囲をV2へ拡張し、V1を新規判断に使わない。
- 影響: T02、T05、T07、T08〜T17。

## 2026-08-12 — D-010: 元FireRedからカントー本土を復元し二地方を往復可能にする

- 決定: clean BPRJ Rev.0と固定済みpokefireredを原資産として、カントー本土の地形・建物・接続・NPC座標・ジム構造を新規 `KANTO_*` 名前空間へ複製する。初回殿堂入り後にクチバへ到着し、トーホクへ常時帰還できる双方向移動を必須にする。
- 根拠: Vegaに上書きされた原FireRed IDへ戻すより、新規Map/Flag/Var/Trainer/ItemFlagへ変換する方がVega本編を保護し、二地方を同居させられる。
- 制約: 原作ストーリー状態は再利用しない。V2の47地点は生態設計単位であり、全建物・階層を含むraw map scopeはT11で別途確定する。ナナシマはV2本体では予約に留める。
- 影響: T02、T08、T11〜T17。

## 2026-08-12 — D-011: カントーをVega中盤から任意解禁する

- 決定: カントーへの渡航はVega初回殿堂入りを必要とせず、シオウの3個目バッジ取得後、アーシア島D・Hビルの初回攻略完了を概念条件として恒久解禁する。実装はT02で確定するVega実flagから一度だけ `KANTO_TRAVEL_UNLOCKED` を設定し、以後の渡航でVega進行flagを再判定しない。既存の殿堂入り済みsaveには移行時に渡航権を付与する。
- 二段階進行: 早期解禁後はクチバ、初期回廊、高レベル生態、要求認定章数0〜4のジム・調査を任意攻略できる。Vega殿堂入りは後半認定章、カントーリーグ、終盤伝説、二地方共鳴だけを解禁する。
- 難易度: V2のLv.68〜100の固定帯を維持し、動的party scalingは使わない。高レベル個体の捕獲・持ち帰りによる戦力面のsequence breakは、任意ルートの報酬として許容する。Vegaの物語・warp・HM・重要道具flagを飛ばす進行sequence breakは禁止する。
- 安全条件: 初回乗船前に推奨Lv.65以上の警告を出す。船上戦は任意・勝敗不問とし、クチバのPC/回復と帰還船までに強制戦闘やfield move要求を置かない。クチバからの無料帰還は認定章、所持金、RTC、story flagに依存させない。
- 状態分離: `KANTO_TRAVEL_UNLOCKED`、`KANTO_VISITED`、`KANTO_CERT_*`、`KANTO_STORY_*`、`VEGA_HALL_OF_FAME` を別状態にし、Kantoのfield permitはTohokuのHM判定を変更しない。
- 置換: D-003とD-010の「殿堂入り後に解禁」という時期だけを本決定で置き換える。別名前空間、clean BPRJからの復元方式、常時帰還は維持する。V2受領原本は編集せず、T12の正規化層で殿堂入り前提をoverrideする。
- 影響: T02、T08、T12〜T17、リリース回帰。

## 2026-08-12 — D-012: 現代育成と高速操作QOLをrelease scopeにする

- 決定: `docs/QOL_POLICY.md` のQOL-A/QOL-Bを全て実装対象にする。文章は既定 `INSTANT`、ダッシュはVega比25%以上、自転車は50%以上の移動時間短縮を受入条件とする。現代式孵化、経験アメ、複数使用、IV/EV表示、全体学習装置、タマゴPC/queue、mint、特性道具、SV式Hyper Training、PC検索・一括操作、field PC、タマゴバスケット、自動戦闘を含む。
- 既定値: ジャッジは最初から利用可能でタマゴIVも数値表示する。王冠は元IVを書き換えず「きたえた！」を別保存する。孵化演出は既定FAST、技思い出しは2個目badge後から無料、まるいおまもりは100種捕獲またはカントー預かり屋questの早い方で解禁する。
- 実装順: T01/T02で固定upstreamとVega hookを実証し、T05〜T10でQOL-Aを統合、T12/T15/T16で解禁と供給、T17の全回帰前にQOL-Bを統合し、T18で配布説明を完成させる。最初のカントー縦切りを高度PC改造で待たせず、DAGは変更しない。
- 根拠: 育成の反復作業と移動・文章待ちを大幅に減らし、二地方・1025種規模でも遊びやすくするため。添付内で分岐していた案は、SV準拠と利便性を優先して上記へ固定した。
- 影響: T01、T02、T05、T06、T08〜T10、T12、T15〜T18。

## 2026-08-12 — D-013: READYタスクの先頭順は推奨にする

- 決定: 正本IN_PROGRESSは1件、DAG依存は維持するが、依存READY候補の先頭以外も `taskctl.py start` で開始できる。`PRIMARY` は推奨、`PARALLEL_PREP` は他のREADY候補として扱う。
- 根拠: toolchainや長時間buildを待つ間にT02/T12など独立タスクを正本化でき、固定順による遊休をなくせる。Git上の状態一貫性は単一IN_PROGRESS、依存、task commitで維持できる。
- 検証: 反復中は対象test、タスク完了時は標準ゲートを内包する既定verifyを1回実行し、同じsuiteの直列二重実行を避ける。
- 置換: D-006の正本構造とD-008の効率原則は維持し、`design/tasks_next.md` の並びを強制開始順としていた運用だけを置き換える。
- 影響: 全タスク、`scripts/taskctl.py`、再開prompt、並列運用。

## 2026-08-12 — D-014: UI追加と新規イベント演出を最小化する

- 決定: 採用済み機能は維持するが、新しいfull-screen UI、独自window、装飾asset、長いcutscene、minigame、多段questを原則作らない。既存summary/PC/list/数量選択/技思い出し/Options、既存NPC/端末と標準script commandを薄いadapterで再利用する。
- UI: IV/EVは既存情報欄のcompact切替、複数使用は既存数量選択、PC高度機能は標準list/文字入力/SELECT marker、field PCは既存PC画面、自動戦闘は簡単な既存menu commandで実装する。
- イベント: QOL解禁と追加イベントは `SIMPLE_EVENT` を既定とし、短い会話、条件check、flag、標準reward/battle/warpだけで完了させる。元Vega/FireRedの既存gym puzzleや地形仕掛けは再利用する。
- 根拠: UI・演出制作をcritical pathから外し、機能、二地方化、再現性へ実装時間を集中するため。
- 影響: T09、T10、T12、T15〜T17、content生成、release UI。
