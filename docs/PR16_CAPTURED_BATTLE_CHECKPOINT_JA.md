# PR16 自然捕獲個体の実戦接続 — 2026-09-11

**自然捕獲→通常保存/再開→次の自然遭遇→実メニュー交代→技使用→離脱→再保存/第3コア再開を、新規2件6コアで受入済み。製品全体・道具取得から装備/戦闘・実Circus入場は未完了です。**

最新入口: `content/modernization/p08_remaining_work.json`、受入原本照合: `content/modernization/pr16_captured_battle_acceptance.json`。

## 今回の新規run

run `34577360374`、実行HEAD `1c8b61e9f9f156c541adb984cd38309611b50030`。候補はショップ表示修正版 `e630f7f199194fb4b531ff3a561da866902aea200770a832aec5c276e1636267`、33554432 bytes、CRC32 `BFB089F9`。この作業でROMの追加変更はありません。

洞窟1/113と1/118の2ケースとも、最初から新しいプロセスで実歩行→自然遭遇→Bagでの捕獲を行いました。シビルドンはそれぞれLv80/Lv99。自然生成時と捕獲後のpersonalityが一致し、通常保存後に旧コアを破棄して第2コアでContinueしています。

その後、どちらも18歩の通常歩行で次の自然遭遇を起こし、戦闘の「ポケモン」→2匹目→「いれかえる」を実入力。対象は保存して再開した捕獲個体で、生成済みの別個体へ差し替えていません。party index1、species411、捕獲時personality、4技とPP、nativeに割り当てられた通常特性26を照合しました。

実際の技選択で技ID9のPPが15→14になり、通常の行動選択へ戻ってから「にげる」で離脱。個体同一性と減ったPPの保持、在庫不変、2回目の通常保存を確認。さらに第2コアを破棄し、第3コアで通常Continueして手持ち200 bytes・全在庫・保存番号が一致しました。最初の捕獲から最後の再開まで7種類のhost書込み禁止を維持し、各拒否も実行しています。

この受入は**捕獲した通常個体を実戦へつなぐ経路**です。相手は自然生成で、技の命中・ダメージ・全特性の効果試験やメガ進化を一括受入したものではありません。開始位置・Lv100先頭個体・1個のマスターボール・記憶ポケットはfixtureです。石/リング等の通常取得と装備から戦闘までの接続は引き続き未受入です。

## 新旧件数と原本を混同しない

先行run `34575955233` は捕獲・保存までの2件4コアとして、その原本とfalseだった戦闘受入を変更せず保持します。今回のrunは同じ2つのマップケースを拡張して**新たに実行した2件6コア**です。先行の4コアを今回の6コアへ足さず、4種類の独立した取得経路が増えたとも数えません。

地形解析run `34575014339` は静的0エミュレータ実行。旧ショップ・P03/P06/P07原本も今回の新規件数へ加えません。P06の内外true、1073追加/499保持、ロトム/繁殖/共有技等の成功を維持します。

## 永続保存と再検査

`content/modernization/pr16_captured_battle_evidence/34577360374/original.zip` と `actions.json` にGit追跡。ZIPは306904 bytes、SHA-256 `7880bc04b85d0d0a6e681138b879a7af3818c31dc85d9289650d9b60aa119d0c`。ROM/saveは含みません。

Actions全step/実行HEAD、生成した実controllerの全バイト、32入力ソース、raw stdout/stderr/process、先行と一致する実ROM遭遇表、7書込み拒否、24画像を照合しています。最初の12画像は先行の確認済み画面と同じハッシュ。追加12画像で手持ち選択/交代/戦闘/離脱/再開を確認し、表示崩れは見られませんでした。画像だけでデータ保持を判定しません。

実行runの対象テスト44件、保存時の既存分を含む対象テスト125件。保存・原本再検査は新しいエミュレータ実行ではありません。現在ビューの両生成経路にも接続しており、捕獲だけの旧記録には `historical_capture_only` と後継受入への参照を付けています。

```sh
python3 scripts/pr16_captured_battle_checkpoint.py
python3 scripts/pr16_natural_capture_checkpoint.py
python3 scripts/pr16_refresh_current_view.py
python3 scripts/record_modernization_final_acceptance.py
python3 scripts/record_modernization_p03_forgetting.py
```

## 次の具体的な残件

`NATURAL_CAPTURE_GEAR` は、自然捕獲や捕獲個体の通常戦闘を未確認へ戻さず、実取得した道具の装備から戦闘への接続を進めます。既存のショップ11件22コアは取得/表示/保存の成功として保持。リング/BP/ボール等のfixture境界を隠した全取得の合格や、全6種の自然取得を実行したという主張はしません。

`PHYSICAL_CIRCUS_ADMISSION` は実受付→入場→特性抑制。P03/P07は残る採用済み消費経路と既存原本の対応。P08は同一候補の影響回帰・clean ROM全工程独立2回・配布パッチ・セーブ保護付き導入/戻し方。`full_p03_acceptance` / `full_p05_acceptance` / `full_p07_acceptance` / `release_ready` はfalseのままです。

publicと殿堂入り後/無料わざメモリーは承認済み。Stage62・実プレイsave・旧原本・公開範囲・履歴を変更せず、同じPR #16を未マージで維持しています。今回コードにユーザーの手動パッチ適用は不要です。
