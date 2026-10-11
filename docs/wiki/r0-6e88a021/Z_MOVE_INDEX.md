# 専用Z31登録と汎用Z/Max

**固定レビュー版 R0** — SHA-256 `6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2` / 33554432 bytes / CRC32 `00F31AF7`。

[入口](README.md) · [証拠区分と制限](LIMITATIONS.md) · [提案記入](OWNER_PROPOSALS.md)

ROM数値・文字列は旧候補読取＋5段階非変更範囲の継承。全機能の新native受入ではありません。

汎用Zと一般Maxの数値・source投影は各[技ページ](MOVE_INDEX.md)に全件掲載。専用Zの対応byteと効果handler/併用/解除受入を分離します。

| 対象種族ID | 道具 | 元技 | 専用Zと個別証拠 |
| --- | --- | --- | --- |
| [1203: ライチュウ](pokemon/1203.md) | [812: アロライZ](items/812.md) | [85: 10まんボルト](moves/85.md) | [ZーMove 39](z/0.md) |
| [1122: ジュナイパー](pokemon/1122.md) | [813: ジュナイパーZ](items/813.md) | [686: かげぬい](moves/686.md) | [ZーMove 43](z/1.md) |
| [483: イーブイ](pokemon/483.md) | [814: イーブイZ](items/814.md) | [745: とっておき](moves/745.md) | [ZーMove 40](z/2.md) |
| [1125: ガオガエン](pokemon/1125.md) | [815: ガオガエンZ](items/815.md) | [656: DDラリアット](moves/656.md) | [ZーMove 44](z/3.md) |
| [1182: ジャラランガ](pokemon/1182.md) | [816: ジャラランガZ](items/816.md) | [655: スケイルノイズ](moves/655.md) | [ZーMove 48](z/4.md) |
| [1190: ルナアーラ](pokemon/1190.md) | [817: ルナアーラZ](items/817.md) | [669: シャドーレイ](moves/669.md) | [ZーMove 51](z/5.md) |
| [1261: ネクロズマ](pokemon/1261.md) | [817: ルナアーラZ](items/817.md) | [669: シャドーレイ](moves/669.md) | [ZーMove 51](z/6.md) |
| [1143: ルガルガン](pokemon/1143.md) | [818: ルガルガンZ](items/818.md) | [407: ストーンエッジ](moves/407.md) | [ZーMove 46](z/7.md) |
| [1227: ルガルガン](pokemon/1227.md) | [818: ルガルガンZ](items/818.md) | [407: ストーンエッジ](moves/407.md) | [ZーMove 46](z/8.md) |
| [1263: ルガルガン](pokemon/1263.md) | [818: ルガルガンZ](items/818.md) | [407: ストーンエッジ](moves/407.md) | [ZーMove 46](z/9.md) |
| [1200: マーシャドー](pokemon/1200.md) | [819: マーシャドーZ](items/819.md) | [684: シャドースチール](moves/684.md) | [ZーMove 53](z/10.md) |
| [151: ミュウ](pokemon/151.md) | [820: ミュウZ](items/820.md) | [94: サイコキネシス](moves/94.md) | [ZーMove 42](z/11.md) |
| [1176: ミミッキュ](pokemon/1176.md) | [821: ミミッキュZ](items/821.md) | [545: じゃれつく](moves/545.md) | [ZーMove 47](z/12.md) |
| [1253: ミミッキュ](pokemon/1253.md) | [821: ミミッキュZ](items/821.md) | [545: じゃれつく](moves/545.md) | [ZーMove 47](z/13.md) |
| [25: ピカチュウ](pokemon/25.md) | [822: ピカチュウZ](items/822.md) | [344: ボルテッカー](moves/344.md) | [ZーMove 37](z/14.md) |
| [1274: ピカチュウ](pokemon/1274.md) | [823: サトピカZ](items/823.md) | [85: 10まんボルト](moves/85.md) | [ZーMove 38](z/15.md) |
| [1275: ピカチュウ](pokemon/1275.md) | [823: サトピカZ](items/823.md) | [85: 10まんボルト](moves/85.md) | [ZーMove 38](z/16.md) |
| [1276: ピカチュウ](pokemon/1276.md) | [823: サトピカZ](items/823.md) | [85: 10まんボルト](moves/85.md) | [ZーMove 38](z/17.md) |
| [1277: ピカチュウ](pokemon/1277.md) | [823: サトピカZ](items/823.md) | [85: 10まんボルト](moves/85.md) | [ZーMove 38](z/18.md) |
| [1278: ピカチュウ](pokemon/1278.md) | [823: サトピカZ](items/823.md) | [85: 10まんボルト](moves/85.md) | [ZーMove 38](z/19.md) |
| [1279: ピカチュウ](pokemon/1279.md) | [823: サトピカZ](items/823.md) | [85: 10まんボルト](moves/85.md) | [ZーMove 38](z/20.md) |
| [1280: ピカチュウ](pokemon/1280.md) | [823: サトピカZ](items/823.md) | [85: 10まんボルト](moves/85.md) | [ZーMove 38](z/21.md) |
| [1128: アシレーヌ](pokemon/1128.md) | [824: アシレーヌZ](items/824.md) | [683: うたかたのアリア](moves/683.md) | [ZーMove 45](z/22.md) |
| [491: カビゴン](pokemon/491.md) | [825: カビゴンZ](items/825.md) | [386: ギガインパクト](moves/386.md) | [ZーMove 41](z/23.md) |
| [1189: ソルガレオ](pokemon/1189.md) | [826: ソルガレオZ](items/826.md) | [690: メテオドライブ](moves/690.md) | [ZーMove 50](z/24.md) |
| [1260: ネクロズマ](pokemon/1260.md) | [826: ソルガレオZ](items/826.md) | [690: メテオドライブ](moves/690.md) | [ZーMove 50](z/25.md) |
| [1183: カプ・コケコ](pokemon/1183.md) | [827: カプZ](items/827.md) | [671: しぜんのいかり](moves/671.md) | [ZーMove 49](z/26.md) |
| [1185: カプ・ブルル](pokemon/1185.md) | [827: カプZ](items/827.md) | [671: しぜんのいかり](moves/671.md) | [ZーMove 49](z/27.md) |
| [1184: カプ・テテフ](pokemon/1184.md) | [827: カプZ](items/827.md) | [671: しぜんのいかり](moves/671.md) | [ZーMove 49](z/28.md) |
| [1186: カプ・レヒレ](pokemon/1186.md) | [827: カプZ](items/827.md) | [671: しぜんのいかり](moves/671.md) | [ZーMove 49](z/29.md) |
| [1262: ネクロズマ](pokemon/1262.md) | [746: ウルトラネクロZ](items/746.md) | [733: フォトンゲイザー](moves/733.md) | [ZーMove 52](z/30.md) |
