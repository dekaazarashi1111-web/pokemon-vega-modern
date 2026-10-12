# PR16 自然捕獲・通常保存の受入 — 2026-09-11

**2つの洞窟での自然歩行→シビルドンの捕獲→通常保存→別コアContinueは、新規2件4コア成功。製品全体、道具の通常入手と戦闘接続、Circus入場は未完了です。**

## 実行した経路と原本

実run `34575955233`、実行HEAD `68f9459630a2bf7215c58f12cb0557f57f15c6ff`。候補はショップ表示修正版 `e630f7f199194fb4b531ff3a561da866902aea200770a832aec5c276e1636267`、33554432 bytes、CRC32 `BFB089F9`。今回はROM変更なしです。

マップ1/113では313歩・15遭遇でLv80のシビルドン、1/118では202歩・9遭遇でLv99のシビルドンに遭遇しました。対象外の14件/8件は実際の「にげる」で離脱しています。遭遇ログの全種族・レベルを、その座標で最初に参照される実ROMの地上遭遇表と照合。乱数・野生個体・遭遇関数を試験側から操作していません。

戦闘中の実Bag→マスターボール選択→使用で捕獲。自然生成個体と捕獲個体のpersonalityを照合し、ボール1個の消費、他の在庫不変、手持ち200 bytes、通常Start保存、旧コア破棄後の別コアContinue、手持ち・在庫・保存番号の保持まで検査しました。最初の歩行から保存再開まで、7種類のhost書込みAPIを禁止し、その拒否試験も実行済みです。

**開始位置、Lv100の先頭個体、1個のマスターボール、記憶されたボールポケットはfixtureです。** 先頭個体やボールの通常入手、捕獲後個体を戦闘へ出すこと、メガストーン取得と装備を通した一連の経路までは合格としていません。`gear_acquisition_accepted` / `battle_connection_accepted` / `full_p05_acceptance` / `release_ready` はfalseです。

画面原本12枚を確認しました。自然遭遇時の種族/レベル、ボール一覧/使用選択、捕獲後/再開後の背景を確認し、今回の画面にショップのような破損は見られません。1/118の暗さは開始時からあり、捕獲後と再開後で一致しています。画像ハッシュはcheckpointのIMAGESに固定。画面だけで個体保持を判定せず、データ照合も必須です。

地形解析run `34575014339` / HEAD `df5cad6e68e80053bec5eedc13d34c35f36c0c56` は、独立した静的根拠として保持します。こちらはエミュレータ0件で、捕獲2件に加算しません。ショップ修正版の既存成功や親候補のP03/P06/P07成功も、新規件数には加えません。

## 永続保存と再開

`content/modernization/pr16_natural_capture_evidence/<run>/original.zip` と `actions.json` に、上の2runをGit追跡しています。SHA-256・ZIP CRC/安全性・Actions全step・実行HEAD・実ソース・raw stdout/stderr/process・拒否記録・画像を照合して `content/modernization/pr16_natural_capture_acceptance.json` を生成します。原本にはROM/saveを含みません。

再検査は `python3 scripts/pr16_natural_capture_checkpoint.py`、現在ビューは `python3 scripts/pr16_refresh_current_view.py`。最終受入・P03忘却の両生成経路にも接続済みです。捕獲実行runの対象テスト34件、保存時の新旧対象テスト106件。保存/再検査を新しいROM実行とは数えません。

再開入口は `p08_remaining_work.json` の `NATURAL_CAPTURE_GEAR`。自然捕獲を未確認へ戻さず、取得個体の実戦投入・道具の通常入手/装備と戦闘接続へ進んでください。実Circus受付/入場、P03/P07の残る採用経路対応、同一候補への影響回帰、clean ROM全工程独立2回、配布パッチ/導入戻し方も残ります。

publicと無料わざメモリーの承認、P06の内外true、親候補の既存原本を保持。Stage62・実プレイsave・旧原本・公開範囲・履歴を変更せず、PR #16は未マージです。
