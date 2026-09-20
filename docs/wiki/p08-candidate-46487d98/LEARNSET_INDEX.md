# 習得経路・P07履歴照合

候補 SHA-256 `46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38` / 33554432 bytes / CRC32 `CC068B4A`。

[Wiki入口](README.md)

同じ技の複数経路を保持します。build_learnable_preservationは保持履歴であり、その経路から直接教えられるという意味ではありません。

| 経路 | 行数 |
| --- | --- |
| 保持履歴（直接習得ではない） | 2223 |
| 条件付きタマゴ | 4 |
| タマゴ | 6298 |
| レベルアップ | 25841 |
| TM/HM互換 | 41568 |
| TMアーカイブ | 26296 |
| わざメモリー | 295 |
| 共有タマゴ技 | 5027 |
| 教え技互換 | 7289 |
| 教え技アーカイブ | 369 |

## P07原本行の現在候補照合

levelは同じlevel、machine/tutorは同じslotまで一致した場合だけ原条件ありとします。履歴側のorderは記録しつつ、level技の表示順移動を習得条件変更と混同しません。

| group | 原本行 | 同じ技あり | 元routeあり | 元条件あり | 保持履歴あり |
| --- | --- | --- | --- | --- | --- |
| official_to_vega_legacy_preservation | 499 | 499 | 499 | 499 | 0 |
| vega_to_official_historical_adoption | 1073 | 1073 | 1073 | 1073 | 0 |

| group | Species | 技 | 元route / 条件 | 元CSV / 行 | 元条件一致 | 現在のteaching route | 保持履歴 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| official_to_vega_legacy_preservation | [10: スバメ](pokemon/10.md) | [457: かっくう](moves/457.md) | {"level":"13","order":"5","route":"level_up"} | level_up_final.csv:180 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [11: オオスバメ](pokemon/11.md) | [457: かっくう](moves/457.md) | {"level":"13","order":"8","route":"level_up"} | level_up_final.csv:200 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [12: リオル](pokemon/12.md) | [451: ダブルショット](moves/451.md) | {"level":"15","order":"7","route":"level_up"} | level_up_final.csv:220 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [12: リオル](pokemon/12.md) | [450: マグナムパンチ](moves/450.md) | {"level":"55","order":"13","route":"level_up"} | level_up_final.csv:226 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [13: ルカリオ](pokemon/13.md) | [463: さいみんはどう](moves/463.md) | {"level":"1","order":"3","route":"level_up"} | level_up_final.csv:229 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [13: ルカリオ](pokemon/13.md) | [451: ダブルショット](moves/451.md) | {"level":"15","order":"10","route":"level_up"} | level_up_final.csv:236 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [14: デルビル](pokemon/14.md) | [477: ダークロアー](moves/477.md) | {"level":"13","order":"5","route":"level_up"} | level_up_final.csv:255 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [15: ヘルガー](pokemon/15.md) | [477: ダークロアー](moves/477.md) | {"level":"13","order":"8","route":"level_up"} | level_up_final.csv:275 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [15: ヘルガー](pokemon/15.md) | [431: いかりのほのお](moves/431.md) | {"level":"65","order":"23","route":"level_up"} | level_up_final.csv:290 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [16: ディグダ](pokemon/16.md) | [454: もぐる](moves/454.md) | {"level":"23","order":"8","route":"level_up"} | level_up_final.csv:298 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [17: ダグトリオ](pokemon/17.md) | [454: もぐる](moves/454.md) | {"level":"23","order":"12","route":"level_up"} | level_up_final.csv:317 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [18: トゲピー](pokemon/18.md) | [429: めまわし](moves/429.md) | {"level":"53","order":"16","route":"level_up"} | level_up_final.csv:341 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [19: トゲチック](pokemon/19.md) | [429: めまわし](moves/429.md) | {"level":"53","order":"21","route":"level_up"} | level_up_final.csv:362 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [25: ピカチュウ](pokemon/25.md) | [438: メガショック](moves/438.md) | {"level":"34","order":"11","route":"level_up"} | level_up_final.csv:442 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [28: エアームド](pokemon/28.md) | [361: メタルブラスト](moves/361.md) | {"level":"57","order":"21","route":"level_up"} | level_up_final.csv:492 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [35: ブイゼル](pokemon/35.md) | [433: スプラッシュ](moves/433.md) | {"level":"51","order":"15","route":"level_up"} | level_up_final.csv:598 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [36: フローゼル](pokemon/36.md) | [446: スターフリーズ](moves/446.md) | {"level":"61","order":"20","route":"level_up"} | level_up_final.csv:618 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [39: クヌギダマ](pokemon/39.md) | [427: ダブルスピン](moves/427.md) | {"level":"9","order":"4","route":"level_up"} | level_up_final.csv:661 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [39: クヌギダマ](pokemon/39.md) | [487: しゅうげき](moves/487.md) | {"level":"42","order":"15","route":"level_up"} | level_up_final.csv:672 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [40: フォレトス](pokemon/40.md) | [427: ダブルスピン](moves/427.md) | {"level":"1","order":"5","route":"level_up"} | level_up_final.csv:678 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [40: フォレトス](pokemon/40.md) | [427: ダブルスピン](moves/427.md) | {"level":"9","order":"7","route":"level_up"} | level_up_final.csv:680 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [40: フォレトス](pokemon/40.md) | [487: しゅうげき](moves/487.md) | {"level":"50","order":"20","route":"level_up"} | level_up_final.csv:693 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [40: フォレトス](pokemon/40.md) | [440: たいでん](moves/440.md) | {"level":"60","order":"23","route":"level_up"} | level_up_final.csv:696 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [40: フォレトス](pokemon/40.md) | [361: メタルブラスト](moves/361.md) | {"level":"70","order":"25","route":"level_up"} | level_up_final.csv:698 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [41: シェルダー](pokemon/41.md) | [433: スプラッシュ](moves/433.md) | {"level":"49","order":"15","route":"level_up"} | level_up_final.csv:713 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [42: パルシェン](pokemon/42.md) | [448: アイスバーン](moves/448.md) | {"level":"1","order":"2","route":"level_up"} | level_up_final.csv:718 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [48: エビワラー](pokemon/48.md) | [460: サイコパンチ](moves/460.md) | {"level":"21","order":"10","route":"level_up"} | level_up_final.csv:808 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [49: カポエラー](pokemon/49.md) | [427: ダブルスピン](moves/427.md) | {"level":"24","order":"8","route":"level_up"} | level_up_final.csv:826 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [52: アブソル](pokemon/52.md) | [476: ダークカッター](moves/476.md) | {"level":"25","order":"8","route":"level_up"} | level_up_final.csv:879 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [54: キリンリキ](pokemon/54.md) | [464: じゅうりょくは](moves/464.md) | {"level":"28","order":"12","route":"level_up"} | level_up_final.csv:925 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [58: コイル](pokemon/58.md) | [482: じりょくせん](moves/482.md) | {"level":"54","order":"16","route":"level_up"} | level_up_final.csv:1001 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [59: レアコイル](pokemon/59.md) | [482: じりょくせん](moves/482.md) | {"level":"60","order":"20","route":"level_up"} | level_up_final.csv:1022 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [60: ジバコイル](pokemon/60.md) | [440: たいでん](moves/440.md) | {"level":"30","order":"13","route":"level_up"} | level_up_final.csv:1036 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [60: ジバコイル](pokemon/60.md) | [482: じりょくせん](moves/482.md) | {"level":"60","order":"21","route":"level_up"} | level_up_final.csv:1044 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [60: ジバコイル](pokemon/60.md) | [481: ジオインパクト](moves/481.md) | {"level":"66","order":"23","route":"level_up"} | level_up_final.csv:1046 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [61: ヒトデマン](pokemon/61.md) | [427: ダブルスピン](moves/427.md) | {"level":"10","order":"5","route":"level_up"} | level_up_final.csv:1051 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [61: ヒトデマン](pokemon/61.md) | [357: スターダスト](moves/357.md) | {"level":"55","order":"16","route":"level_up"} | level_up_final.csv:1062 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [62: スターミー](pokemon/62.md) | [464: じゅうりょくは](moves/464.md) | {"level":"33","order":"7","route":"level_up"} | level_up_final.csv:1070 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [62: スターミー](pokemon/62.md) | [446: スターフリーズ](moves/446.md) | {"level":"55","order":"13","route":"level_up"} | level_up_final.csv:1076 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [63: ゴース](pokemon/63.md) | [356: ソウルブレイク](moves/356.md) | {"level":"22","order":"9","route":"level_up"} | level_up_final.csv:1085 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [63: ゴース](pokemon/63.md) | [359: のりうつる](moves/359.md) | {"level":"43","order":"18","route":"level_up"} | level_up_final.csv:1094 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [64: ゴースト](pokemon/64.md) | [356: ソウルブレイク](moves/356.md) | {"level":"22","order":"9","route":"level_up"} | level_up_final.csv:1104 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [64: ゴースト](pokemon/64.md) | [359: のりうつる](moves/359.md) | {"level":"55","order":"20","route":"level_up"} | level_up_final.csv:1115 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [65: ゲンガー](pokemon/65.md) | [471: たたり](moves/471.md) | {"level":"1","order":"1","route":"level_up"} | level_up_final.csv:1117 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [65: ゲンガー](pokemon/65.md) | [356: ソウルブレイク](moves/356.md) | {"level":"22","order":"11","route":"level_up"} | level_up_final.csv:1127 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [65: ゲンガー](pokemon/65.md) | [470: ソウルバイト](moves/470.md) | {"level":"38","order":"15","route":"level_up"} | level_up_final.csv:1131 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [65: ゲンガー](pokemon/65.md) | [359: のりうつる](moves/359.md) | {"level":"63","order":"22","route":"level_up"} | level_up_final.csv:1138 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [66: タマタマ](pokemon/66.md) | [445: げんわくごな](moves/445.md) | {"level":"25","order":"11","route":"level_up"} | level_up_final.csv:1150 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [66: タマタマ](pokemon/66.md) | [461: サイコバーン](moves/461.md) | {"level":"55","order":"18","route":"level_up"} | level_up_final.csv:1157 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [67: ナッシー](pokemon/67.md) | [444: だいせいちょう](moves/444.md) | {"level":"29","order":"7","route":"level_up"} | level_up_final.csv:1164 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [71: サイホーン](pokemon/71.md) | [456: すなかぜ](moves/456.md) | {"level":"34","order":"12","route":"level_up"} | level_up_final.csv:1243 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [71: サイホーン](pokemon/71.md) | [425: げきとつ](moves/425.md) | {"level":"74","order":"19","route":"level_up"} | level_up_final.csv:1250 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [72: サイドン](pokemon/72.md) | [456: すなかぜ](moves/456.md) | {"level":"34","order":"10","route":"level_up"} | level_up_final.csv:1260 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [72: サイドン](pokemon/72.md) | [425: げきとつ](moves/425.md) | {"level":"80","order":"21","route":"level_up"} | level_up_final.csv:1271 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [73: ドサイドン](pokemon/73.md) | [456: すなかぜ](moves/456.md) | {"level":"34","order":"11","route":"level_up"} | level_up_final.csv:1282 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [73: ドサイドン](pokemon/73.md) | [425: げきとつ](moves/425.md) | {"level":"80","order":"21","route":"level_up"} | level_up_final.csv:1292 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [74: トロピウス](pokemon/74.md) | [441: おいしげる](moves/441.md) | {"level":"51","order":"15","route":"level_up"} | level_up_final.csv:1308 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [74: トロピウス](pokemon/74.md) | [458: ハリケーン](moves/458.md) | {"level":"67","order":"18","route":"level_up"} | level_up_final.csv:1311 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [75: ポリゴン](pokemon/75.md) | [465: バグノイズ](moves/465.md) | {"level":"62","order":"17","route":"level_up"} | level_up_final.csv:1329 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [76: ポリゴン2](pokemon/76.md) | [465: バグノイズ](moves/465.md) | {"level":"62","order":"17","route":"level_up"} | level_up_final.csv:1347 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [77: ポリゴンZ](pokemon/77.md) | [465: バグノイズ](moves/465.md) | {"level":"62","order":"18","route":"level_up"} | level_up_final.csv:1367 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [85: ユキカブリ](pokemon/85.md) | [442: リーフガード](moves/442.md) | {"level":"34","order":"12","route":"level_up"} | level_up_final.csv:1518 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [85: ユキカブリ](pokemon/85.md) | [448: アイスバーン](moves/448.md) | {"level":"39","order":"13","route":"level_up"} | level_up_final.csv:1519 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [86: ユキノオー](pokemon/86.md) | [442: リーフガード](moves/442.md) | {"level":"34","order":"14","route":"level_up"} | level_up_final.csv:1538 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [86: ユキノオー](pokemon/86.md) | [448: アイスバーン](moves/448.md) | {"level":"39","order":"17","route":"level_up"} | level_up_final.csv:1541 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [92: ミルタンク](pokemon/92.md) | [426: スピンテール](moves/426.md) | {"level":"35","order":"13","route":"level_up"} | level_up_final.csv:1649 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [92: ミルタンク](pokemon/92.md) | [467: いわころがり](moves/467.md) | {"level":"48","order":"15","route":"level_up"} | level_up_final.csv:1651 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [93: ツボツボ](pokemon/93.md) | [430: おおあくび](moves/430.md) | {"level":"1","order":"2","route":"level_up"} | level_up_final.csv:1655 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [109: ホーホー](pokemon/109.md) | [428: おんち](moves/428.md) | {"level":"41","order":"16","route":"level_up"} | level_up_final.csv:1970 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [109: ホーホー](pokemon/109.md) | [458: ハリケーン](moves/458.md) | {"level":"53","order":"20","route":"level_up"} | level_up_final.csv:1974 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [110: ヨルノズク](pokemon/110.md) | [428: おんち](moves/428.md) | {"level":"47","order":"16","route":"level_up"} | level_up_final.csv:1991 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [110: ヨルノズク](pokemon/110.md) | [458: ハリケーン](moves/458.md) | {"level":"62","order":"22","route":"level_up"} | level_up_final.csv:1997 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [113: エレブー](pokemon/113.md) | [436: ギガスパーク](moves/436.md) | {"level":"62","order":"15","route":"level_up"} | level_up_final.csv:2048 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [114: エレキブル](pokemon/114.md) | [439: マッハボルト](moves/439.md) | {"level":"21","order":"9","route":"level_up"} | level_up_final.csv:2058 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [114: エレキブル](pokemon/114.md) | [436: ギガスパーク](moves/436.md) | {"level":"62","order":"17","route":"level_up"} | level_up_final.csv:2066 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [116: ブーバー](pokemon/116.md) | [431: いかりのほのお](moves/431.md) | {"level":"62","order":"15","route":"level_up"} | level_up_final.csv:2098 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [117: ブーバーン](pokemon/117.md) | [431: いかりのほのお](moves/431.md) | {"level":"62","order":"18","route":"level_up"} | level_up_final.csv:2117 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [119: リリーラ](pokemon/119.md) | [355: グランボールダ](moves/355.md) | {"level":"67","order":"17","route":"level_up"} | level_up_final.csv:2154 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [120: ユレイドル](pokemon/120.md) | [469: げんしのいぶき](moves/469.md) | {"level":"33","order":"11","route":"level_up"} | level_up_final.csv:2165 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [123: プテラ](pokemon/123.md) | [456: すなかぜ](moves/456.md) | {"level":"53","order":"17","route":"level_up"} | level_up_final.csv:2228 | True | &#91;"egg","level_up"&#93; | False |
| official_to_vega_legacy_preservation | [124: ヨーギラス](pokemon/124.md) | [469: げんしのいぶき](moves/469.md) | {"level":"19","order":"7","route":"level_up"} | level_up_final.csv:2239 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [124: ヨーギラス](pokemon/124.md) | [355: グランボールダ](moves/355.md) | {"level":"50","order":"16","route":"level_up"} | level_up_final.csv:2248 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [125: サナギラス](pokemon/125.md) | [355: グランボールダ](moves/355.md) | {"level":"60","order":"17","route":"level_up"} | level_up_final.csv:2266 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [126: バンギラス](pokemon/126.md) | [474: ふくしゅう](moves/474.md) | {"level":"34","order":"14","route":"level_up"} | level_up_final.csv:2281 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [126: バンギラス](pokemon/126.md) | [475: ダークリゾルブ](moves/475.md) | {"level":"63","order":"21","route":"level_up"} | level_up_final.csv:2288 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [128: メタング](pokemon/128.md) | [440: たいでん](moves/440.md) | {"level":"1","order":"1","route":"level_up"} | level_up_final.csv:2296 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [129: メタグロス](pokemon/129.md) | [440: たいでん](moves/440.md) | {"level":"1","order":"1","route":"level_up"} | level_up_final.csv:2313 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [129: メタグロス](pokemon/129.md) | [361: メタルブラスト](moves/361.md) | {"level":"71","order":"18","route":"level_up"} | level_up_final.csv:2330 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [130: フカマル](pokemon/130.md) | [454: もぐる](moves/454.md) | {"level":"37","order":"13","route":"level_up"} | level_up_final.csv:2343 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [136: フリーザー](pokemon/136.md) | [448: アイスバーン](moves/448.md) | {"level":"71","order":"15","route":"level_up"} | level_up_final.csv:2441 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [137: サンダー](pokemon/137.md) | [438: メガショック](moves/438.md) | {"level":"78","order":"15","route":"level_up"} | level_up_final.csv:2459 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [138: ファイヤー](pokemon/138.md) | [457: かっくう](moves/457.md) | {"level":"1","order":"1","route":"level_up"} | level_up_final.csv:2462 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [138: ファイヤー](pokemon/138.md) | [431: いかりのほのお](moves/431.md) | {"level":"78","order":"16","route":"level_up"} | level_up_final.csv:2477 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [141: スイクン](pokemon/141.md) | [448: アイスバーン](moves/448.md) | {"level":"57","order":"12","route":"level_up"} | level_up_final.csv:2523 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [145: ディアルガ](pokemon/145.md) | [481: ジオインパクト](moves/481.md) | {"level":"42","order":"12","route":"level_up"} | level_up_final.csv:2594 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [145: ディアルガ](pokemon/145.md) | [361: メタルブラスト](moves/361.md) | {"level":"50","order":"14","route":"level_up"} | level_up_final.csv:2596 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [146: パルキア](pokemon/146.md) | [434: だいこうずい](moves/434.md) | {"level":"50","order":"14","route":"level_up"} | level_up_final.csv:2613 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [147: ダークライ](pokemon/147.md) | [475: ダークリゾルブ](moves/475.md) | {"level":"95","order":"16","route":"level_up"} | level_up_final.csv:2631 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [148: ルギア](pokemon/148.md) | [434: だいこうずい](moves/434.md) | {"level":"50","order":"11","route":"level_up"} | level_up_final.csv:2642 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [150: ミュウツー](pokemon/150.md) | [464: じゅうりょくは](moves/464.md) | {"level":"29","order":"8","route":"level_up"} | level_up_final.csv:2676 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [150: ミュウツー](pokemon/150.md) | [459: サイコバレット](moves/459.md) | {"level":"93","order":"18","route":"level_up"} | level_up_final.csv:2686 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [150: ミュウツー](pokemon/150.md) | [461: サイコバーン](moves/461.md) | {"level":"100","order":"19","route":"level_up"} | level_up_final.csv:2687 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [151: ミュウ](pokemon/151.md) | [461: サイコバーン](moves/461.md) | {"level":"70","order":"12","route":"level_up"} | level_up_final.csv:2699 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [152: フシギダネ](pokemon/152.md) | [443: ポイズンリーフ](moves/443.md) | {"level":"25","order":"12","route":"level_up"} | level_up_final.csv:2714 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [153: フシギソウ](pokemon/153.md) | [443: ポイズンリーフ](moves/443.md) | {"level":"28","order":"12","route":"level_up"} | level_up_final.csv:2732 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [153: フシギソウ](pokemon/153.md) | [444: だいせいちょう](moves/444.md) | {"level":"44","order":"18","route":"level_up"} | level_up_final.csv:2738 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [154: フシギバナ](pokemon/154.md) | [452: きけんなどくそ](moves/452.md) | {"level":"1","order":"2","route":"level_up"} | level_up_final.csv:2742 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [154: フシギバナ](pokemon/154.md) | [443: ポイズンリーフ](moves/443.md) | {"level":"28","order":"16","route":"level_up"} | level_up_final.csv:2756 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [154: フシギバナ](pokemon/154.md) | [444: だいせいちょう](moves/444.md) | {"level":"53","order":"23","route":"level_up"} | level_up_final.csv:2763 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [158: ゼニガメ](pokemon/158.md) | [433: スプラッシュ](moves/433.md) | {"level":"40","order":"15","route":"level_up"} | level_up_final.csv:2832 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [159: カメール](pokemon/159.md) | [433: スプラッシュ](moves/433.md) | {"level":"48","order":"18","route":"level_up"} | level_up_final.csv:2850 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [175: パチリス](pokemon/175.md) | [439: マッハボルト](moves/439.md) | {"level":"5","order":"3","route":"level_up"} | level_up_final.csv:3126 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [175: パチリス](pokemon/175.md) | [440: たいでん](moves/440.md) | {"level":"25","order":"9","route":"level_up"} | level_up_final.csv:3132 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [185: ルージュラ](pokemon/185.md) | [449: こおりのキッス](moves/449.md) | {"level":"33","order":"13","route":"level_up"} | level_up_final.csv:3301 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [185: ルージュラ](pokemon/185.md) | [448: アイスバーン](moves/448.md) | {"level":"49","order":"18","route":"level_up"} | level_up_final.csv:3306 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [193: ペラップ](pokemon/193.md) | [428: おんち](moves/428.md) | {"level":"25","order":"10","route":"level_up"} | level_up_final.csv:3443 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [193: ペラップ](pokemon/193.md) | [458: ハリケーン](moves/458.md) | {"level":"53","order":"19","route":"level_up"} | level_up_final.csv:3452 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [198: レディバ](pokemon/198.md) | [487: しゅうげき](moves/487.md) | {"level":"33","order":"14","route":"level_up"} | level_up_final.csv:3540 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [199: レディアン](pokemon/199.md) | [487: しゅうげき](moves/487.md) | {"level":"41","order":"14","route":"level_up"} | level_up_final.csv:3558 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [201: アンノーン](pokemon/201.md) | [462: めざめぬパワー](moves/462.md) | {"level":"1","order":"2","route":"level_up"} | level_up_final.csv:3592 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [203: ケンタロス](pokemon/203.md) | [425: げきとつ](moves/425.md) | {"level":"62","order":"16","route":"level_up"} | level_up_final.csv:3626 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [204: ルナトーン](pokemon/204.md) | [461: サイコバーン](moves/461.md) | {"level":"1","order":"1","route":"level_up"} | level_up_final.csv:3628 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [204: ルナトーン](pokemon/204.md) | [355: グランボールダ](moves/355.md) | {"level":"55","order":"18","route":"level_up"} | level_up_final.csv:3645 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [205: ソルロック](pokemon/205.md) | [355: グランボールダ](moves/355.md) | {"level":"55","order":"18","route":"level_up"} | level_up_final.csv:3664 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [210: テッポウオ](pokemon/210.md) | [453: どくえんまく](moves/453.md) | {"level":"29","order":"9","route":"level_up"} | level_up_final.csv:3743 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [210: テッポウオ](pokemon/210.md) | [433: スプラッシュ](moves/433.md) | {"level":"45","order":"13","route":"level_up"} | level_up_final.csv:3747 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [211: オクタン](pokemon/211.md) | [453: どくえんまく](moves/453.md) | {"level":"31","order":"13","route":"level_up"} | level_up_final.csv:3761 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [211: オクタン](pokemon/211.md) | [433: スプラッシュ](moves/433.md) | {"level":"55","order":"20","route":"level_up"} | level_up_final.csv:3768 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [212: メノクラゲ](pokemon/212.md) | [452: きけんなどくそ](moves/452.md) | {"level":"54","order":"17","route":"level_up"} | level_up_final.csv:3786 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [213: ドククラゲ](pokemon/213.md) | [452: きけんなどくそ](moves/452.md) | {"level":"61","order":"20","route":"level_up"} | level_up_final.csv:3806 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [223: ビリリダマ](pokemon/223.md) | [440: たいでん](moves/440.md) | {"level":"40","order":"14","route":"level_up"} | level_up_final.csv:3977 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [224: マルマイン](pokemon/224.md) | [440: たいでん](moves/440.md) | {"level":"46","order":"15","route":"level_up"} | level_up_final.csv:3995 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [226: ヤミカラス](pokemon/226.md) | [477: ダークロアー](moves/477.md) | {"level":"25","order":"8","route":"level_up"} | level_up_final.csv:4018 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [226: ヤミカラス](pokemon/226.md) | [474: ふくしゅう](moves/474.md) | {"level":"55","order":"15","route":"level_up"} | level_up_final.csv:4025 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [227: ドンカラス](pokemon/227.md) | [458: ハリケーン](moves/458.md) | {"level":"1","order":"1","route":"level_up"} | level_up_final.csv:4028 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [227: ドンカラス](pokemon/227.md) | [470: ソウルバイト](moves/470.md) | {"level":"1","order":"2","route":"level_up"} | level_up_final.csv:4029 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [227: ドンカラス](pokemon/227.md) | [476: ダークカッター](moves/476.md) | {"level":"25","order":"7","route":"level_up"} | level_up_final.csv:4034 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [227: ドンカラス](pokemon/227.md) | [475: ダークリゾルブ](moves/475.md) | {"level":"75","order":"16","route":"level_up"} | level_up_final.csv:4043 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [228: ゴニョニョ](pokemon/228.md) | [428: おんち](moves/428.md) | {"level":"35","order":"10","route":"level_up"} | level_up_final.csv:4053 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [228: ゴニョニョ](pokemon/228.md) | [465: バグノイズ](moves/465.md) | {"level":"45","order":"12","route":"level_up"} | level_up_final.csv:4055 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [229: ドゴーム](pokemon/229.md) | [428: おんち](moves/428.md) | {"level":"39","order":"14","route":"level_up"} | level_up_final.csv:4072 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [229: ドゴーム](pokemon/229.md) | [465: バグノイズ](moves/465.md) | {"level":"51","order":"16","route":"level_up"} | level_up_final.csv:4074 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [230: バクオング](pokemon/230.md) | [428: おんち](moves/428.md) | {"level":"39","order":"16","route":"level_up"} | level_up_final.csv:4093 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [230: バクオング](pokemon/230.md) | [465: バグノイズ](moves/465.md) | {"level":"55","order":"20","route":"level_up"} | level_up_final.csv:4097 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [231: クラブ](pokemon/231.md) | [433: スプラッシュ](moves/433.md) | {"level":"49","order":"18","route":"level_up"} | level_up_final.csv:4118 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [232: キングラー](pokemon/232.md) | [433: スプラッシュ](moves/433.md) | {"level":"63","order":"21","route":"level_up"} | level_up_final.csv:4139 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [247: ニューラ](pokemon/247.md) | [509: ダークスナイプ](moves/509.md) | {"level":"55","order":"18","route":"level_up"} | level_up_final.csv:4439 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [248: マニューラ](pokemon/248.md) | [451: ダブルショット](moves/451.md) | {"level":"1","order":"2","route":"level_up"} | level_up_final.csv:4441 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [248: マニューラ](pokemon/248.md) | [447: つららパンチ](moves/447.md) | {"level":"1","order":"3","route":"level_up"} | level_up_final.csv:4442 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [248: マニューラ](pokemon/248.md) | [474: ふくしゅう](moves/474.md) | {"level":"37","order":"15","route":"level_up"} | level_up_final.csv:4454 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [249: キノココ](pokemon/249.md) | [443: ポイズンリーフ](moves/443.md) | {"level":"33","order":"9","route":"level_up"} | level_up_final.csv:4469 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [249: キノココ](pokemon/249.md) | [445: げんわくごな](moves/445.md) | {"level":"41","order":"11","route":"level_up"} | level_up_final.csv:4471 | True | &#91;"egg","level_up"&#93; | False |
| official_to_vega_legacy_preservation | [249: キノココ](pokemon/249.md) | [441: おいしげる](moves/441.md) | {"level":"49","order":"13","route":"level_up"} | level_up_final.csv:4473 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [250: キノガッサ](pokemon/250.md) | [442: リーフガード](moves/442.md) | {"level":"41","order":"18","route":"level_up"} | level_up_final.csv:4492 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [255: ストライク](pokemon/255.md) | [466: かくらんひこう](moves/466.md) | {"level":"53","order":"19","route":"level_up"} | level_up_final.csv:4591 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [278: ヤミラミ](pokemon/278.md) | [509: ダークスナイプ](moves/509.md) | {"level":"39","order":"15","route":"level_up"} | level_up_final.csv:4748 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [278: ヤミラミ](pokemon/278.md) | [478: ダークハンド](moves/478.md) | {"level":"50","order":"18","route":"level_up"} | level_up_final.csv:4751 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [280: クチート](pokemon/280.md) | [480: メタルニッパー](moves/480.md) | {"level":"46","order":"15","route":"level_up"} | level_up_final.csv:4798 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [280: クチート](pokemon/280.md) | [361: メタルブラスト](moves/361.md) | {"level":"61","order":"20","route":"level_up"} | level_up_final.csv:4803 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [283: ハッサム](pokemon/283.md) | [480: メタルニッパー](moves/480.md) | {"level":"49","order":"16","route":"level_up"} | level_up_final.csv:4865 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [283: ハッサム](pokemon/283.md) | [466: かくらんひこう](moves/466.md) | {"level":"53","order":"17","route":"level_up"} | level_up_final.csv:4866 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [284: カイロス](pokemon/284.md) | [487: しゅうげき](moves/487.md) | {"level":"52","order":"17","route":"level_up"} | level_up_final.csv:4885 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [286: アーボ](pokemon/286.md) | [470: ソウルバイト](moves/470.md) | {"level":"33","order":"12","route":"level_up"} | level_up_final.csv:4920 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [287: アーボック](pokemon/287.md) | [470: ソウルバイト](moves/470.md) | {"level":"36","order":"18","route":"level_up"} | level_up_final.csv:4943 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [289: ドガース](pokemon/289.md) | [453: どくえんまく](moves/453.md) | {"level":"19","order":"7","route":"level_up"} | level_up_final.csv:4985 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [289: ドガース](pokemon/289.md) | [452: きけんなどくそ](moves/452.md) | {"level":"60","order":"16","route":"level_up"} | level_up_final.csv:4994 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [290: マタドガス](pokemon/290.md) | [453: どくえんまく](moves/453.md) | {"level":"19","order":"8","route":"level_up"} | level_up_final.csv:5002 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [290: マタドガス](pokemon/290.md) | [452: きけんなどくそ](moves/452.md) | {"level":"66","order":"19","route":"level_up"} | level_up_final.csv:5013 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [292: ヨマワル](pokemon/292.md) | [472: ライフダウン](moves/472.md) | {"level":"25","order":"8","route":"level_up"} | level_up_final.csv:5044 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [292: ヨマワル](pokemon/292.md) | [470: ソウルバイト](moves/470.md) | {"level":"41","order":"12","route":"level_up"} | level_up_final.csv:5048 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [292: ヨマワル](pokemon/292.md) | [359: のりうつる](moves/359.md) | {"level":"49","order":"14","route":"level_up"} | level_up_final.csv:5050 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [293: サマヨール](pokemon/293.md) | [478: ダークハンド](moves/478.md) | {"level":"1","order":"4","route":"level_up"} | level_up_final.csv:5055 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [293: サマヨール](pokemon/293.md) | [472: ライフダウン](moves/472.md) | {"level":"25","order":"14","route":"level_up"} | level_up_final.csv:5065 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [293: サマヨール](pokemon/293.md) | [470: ソウルバイト](moves/470.md) | {"level":"45","order":"20","route":"level_up"} | level_up_final.csv:5071 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [293: サマヨール](pokemon/293.md) | [359: のりうつる](moves/359.md) | {"level":"57","order":"22","route":"level_up"} | level_up_final.csv:5073 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [294: ヨノワール](pokemon/294.md) | [478: ダークハンド](moves/478.md) | {"level":"1","order":"4","route":"level_up"} | level_up_final.csv:5078 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [294: ヨノワール](pokemon/294.md) | [472: ライフダウン](moves/472.md) | {"level":"25","order":"14","route":"level_up"} | level_up_final.csv:5088 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [294: ヨノワール](pokemon/294.md) | [470: ソウルバイト](moves/470.md) | {"level":"45","order":"19","route":"level_up"} | level_up_final.csv:5093 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [294: ヨノワール](pokemon/294.md) | [474: ふくしゅう](moves/474.md) | {"level":"48","order":"20","route":"level_up"} | level_up_final.csv:5094 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [294: ヨノワール](pokemon/294.md) | [359: のりうつる](moves/359.md) | {"level":"57","order":"22","route":"level_up"} | level_up_final.csv:5096 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [295: ベロリンガ](pokemon/295.md) | [426: スピンテール](moves/426.md) | {"level":"37","order":"12","route":"level_up"} | level_up_final.csv:5110 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [295: ベロリンガ](pokemon/295.md) | [357: スターダスト](moves/357.md) | {"level":"57","order":"17","route":"level_up"} | level_up_final.csv:5115 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [295: ベロリンガ](pokemon/295.md) | [425: げきとつ](moves/425.md) | {"level":"61","order":"18","route":"level_up"} | level_up_final.csv:5116 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [296: ベロベルト](pokemon/296.md) | [429: めまわし](moves/429.md) | {"level":"33","order":"10","route":"level_up"} | level_up_final.csv:5126 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [296: ベロベルト](pokemon/296.md) | [426: スピンテール](moves/426.md) | {"level":"37","order":"11","route":"level_up"} | level_up_final.csv:5127 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [296: ベロベルト](pokemon/296.md) | [357: スターダスト](moves/357.md) | {"level":"57","order":"18","route":"level_up"} | level_up_final.csv:5134 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [296: ベロベルト](pokemon/296.md) | [425: げきとつ](moves/425.md) | {"level":"61","order":"19","route":"level_up"} | level_up_final.csv:5135 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [296: ベロベルト](pokemon/296.md) | [430: おおあくび](moves/430.md) | {"level":"64","order":"20","route":"level_up"} | level_up_final.csv:5136 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [297: イトマル](pokemon/297.md) | [356: ソウルブレイク](moves/356.md) | {"level":"26","order":"10","route":"level_up"} | level_up_final.csv:5146 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [297: イトマル](pokemon/297.md) | [452: きけんなどくそ](moves/452.md) | {"level":"47","order":"18","route":"level_up"} | level_up_final.csv:5154 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [297: イトマル](pokemon/297.md) | [487: しゅうげき](moves/487.md) | {"level":"50","order":"19","route":"level_up"} | level_up_final.csv:5155 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [298: アリアドス](pokemon/298.md) | [356: ソウルブレイク](moves/356.md) | {"level":"28","order":"13","route":"level_up"} | level_up_final.csv:5168 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [298: アリアドス](pokemon/298.md) | [470: ソウルバイト](moves/470.md) | {"level":"41","order":"17","route":"level_up"} | level_up_final.csv:5172 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [298: アリアドス](pokemon/298.md) | [487: しゅうげき](moves/487.md) | {"level":"59","order":"24","route":"level_up"} | level_up_final.csv:5179 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [299: バチュル](pokemon/299.md) | [439: マッハボルト](moves/439.md) | {"level":"23","order":"10","route":"level_up"} | level_up_final.csv:5189 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [299: バチュル](pokemon/299.md) | [440: たいでん](moves/440.md) | {"level":"29","order":"13","route":"level_up"} | level_up_final.csv:5192 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [299: バチュル](pokemon/299.md) | [438: メガショック](moves/438.md) | {"level":"40","order":"17","route":"level_up"} | level_up_final.csv:5196 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [300: デンチュラ](pokemon/300.md) | [439: マッハボルト](moves/439.md) | {"level":"23","order":"10","route":"level_up"} | level_up_final.csv:5209 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [300: デンチュラ](pokemon/300.md) | [440: たいでん](moves/440.md) | {"level":"29","order":"12","route":"level_up"} | level_up_final.csv:5211 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [301: ツチニン](pokemon/301.md) | [455: サンドソニック](moves/455.md) | {"level":"51","order":"15","route":"level_up"} | level_up_final.csv:5234 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [301: ツチニン](pokemon/301.md) | [454: もぐる](moves/454.md) | {"level":"59","order":"16","route":"level_up"} | level_up_final.csv:5235 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [301: ツチニン](pokemon/301.md) | [487: しゅうげき](moves/487.md) | {"level":"67","order":"17","route":"level_up"} | level_up_final.csv:5236 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [302: テッカニン](pokemon/302.md) | [466: かくらんひこう](moves/466.md) | {"level":"59","order":"22","route":"level_up"} | level_up_final.csv:5258 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [302: テッカニン](pokemon/302.md) | [487: しゅうげき](moves/487.md) | {"level":"67","order":"23","route":"level_up"} | level_up_final.csv:5259 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [303: ヌケニン](pokemon/303.md) | [474: ふくしゅう](moves/474.md) | {"level":"51","order":"15","route":"level_up"} | level_up_final.csv:5274 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [303: ヌケニン](pokemon/303.md) | [487: しゅうげき](moves/487.md) | {"level":"67","order":"18","route":"level_up"} | level_up_final.csv:5277 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [308: パッチール](pokemon/308.md) | [477: ダークロアー](moves/477.md) | {"level":"1","order":"2","route":"level_up"} | level_up_final.csv:5358 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [308: パッチール](pokemon/308.md) | [429: めまわし](moves/429.md) | {"level":"10","order":"4","route":"level_up"} | level_up_final.csv:5360 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [308: パッチール](pokemon/308.md) | [450: マグナムパンチ](moves/450.md) | {"level":"32","order":"11","route":"level_up"} | level_up_final.csv:5367 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [308: パッチール](pokemon/308.md) | [478: ダークハンド](moves/478.md) | {"level":"59","order":"17","route":"level_up"} | level_up_final.csv:5373 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [308: パッチール](pokemon/308.md) | [425: げきとつ](moves/425.md) | {"level":"64","order":"18","route":"level_up"} | level_up_final.csv:5374 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [309: ジーランス](pokemon/309.md) | [355: グランボールダ](moves/355.md) | {"level":"78","order":"19","route":"level_up"} | level_up_final.csv:5393 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [313: カゲボウズ](pokemon/313.md) | [479: おいつめる](moves/479.md) | {"level":"28","order":"10","route":"level_up"} | level_up_final.csv:5468 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [313: カゲボウズ](pokemon/313.md) | [429: めまわし](moves/429.md) | {"level":"31","order":"11","route":"level_up"} | level_up_final.csv:5469 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [313: カゲボウズ](pokemon/313.md) | [472: ライフダウン](moves/472.md) | {"level":"35","order":"12","route":"level_up"} | level_up_final.csv:5470 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [313: カゲボウズ](pokemon/313.md) | [470: ソウルバイト](moves/470.md) | {"level":"46","order":"15","route":"level_up"} | level_up_final.csv:5473 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [313: カゲボウズ](pokemon/313.md) | [359: のりうつる](moves/359.md) | {"level":"53","order":"17","route":"level_up"} | level_up_final.csv:5475 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [314: ジュペッタ](pokemon/314.md) | [479: おいつめる](moves/479.md) | {"level":"28","order":"11","route":"level_up"} | level_up_final.csv:5487 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [314: ジュペッタ](pokemon/314.md) | [429: めまわし](moves/429.md) | {"level":"31","order":"12","route":"level_up"} | level_up_final.csv:5488 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [314: ジュペッタ](pokemon/314.md) | [472: ライフダウン](moves/472.md) | {"level":"35","order":"13","route":"level_up"} | level_up_final.csv:5489 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [314: ジュペッタ](pokemon/314.md) | [478: ダークハンド](moves/478.md) | {"level":"37","order":"14","route":"level_up"} | level_up_final.csv:5490 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [314: ジュペッタ](pokemon/314.md) | [470: ソウルバイト](moves/470.md) | {"level":"49","order":"17","route":"level_up"} | level_up_final.csv:5493 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [314: ジュペッタ](pokemon/314.md) | [359: のりうつる](moves/359.md) | {"level":"58","order":"19","route":"level_up"} | level_up_final.csv:5495 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [315: ラルトス](pokemon/315.md) | [463: さいみんはどう](moves/463.md) | {"level":"23","order":"7","route":"level_up"} | level_up_final.csv:5504 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [315: ラルトス](pokemon/315.md) | [464: じゅうりょくは](moves/464.md) | {"level":"56","order":"17","route":"level_up"} | level_up_final.csv:5514 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [316: キルリア](pokemon/316.md) | [463: さいみんはどう](moves/463.md) | {"level":"25","order":"10","route":"level_up"} | level_up_final.csv:5524 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [316: キルリア](pokemon/316.md) | [464: じゅうりょくは](moves/464.md) | {"level":"67","order":"21","route":"level_up"} | level_up_final.csv:5535 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [317: イシズマイ](pokemon/317.md) | [487: しゅうげき](moves/487.md) | {"level":"41","order":"18","route":"level_up"} | level_up_final.csv:5553 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [317: イシズマイ](pokemon/317.md) | [355: グランボールダ](moves/355.md) | {"level":"47","order":"20","route":"level_up"} | level_up_final.csv:5555 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [318: サボネア](pokemon/318.md) | [441: おいしげる](moves/441.md) | {"level":"45","order":"14","route":"level_up"} | level_up_final.csv:5569 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [318: サボネア](pokemon/318.md) | [475: ダークリゾルブ](moves/475.md) | {"level":"53","order":"16","route":"level_up"} | level_up_final.csv:5571 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [319: ノクタス](pokemon/319.md) | [441: おいしげる](moves/441.md) | {"level":"53","order":"19","route":"level_up"} | level_up_final.csv:5591 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [319: ノクタス](pokemon/319.md) | [475: ダークリゾルブ](moves/475.md) | {"level":"65","order":"22","route":"level_up"} | level_up_final.csv:5594 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [321: イノムー](pokemon/321.md) | [469: げんしのいぶき](moves/469.md) | {"level":"20","order":"10","route":"level_up"} | level_up_final.csv:5627 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [321: イノムー](pokemon/321.md) | [446: スターフリーズ](moves/446.md) | {"level":"62","order":"23","route":"level_up"} | level_up_final.csv:5640 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [322: サーナイト](pokemon/322.md) | [463: さいみんはどう](moves/463.md) | {"level":"25","order":"11","route":"level_up"} | level_up_final.csv:5651 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [322: サーナイト](pokemon/322.md) | [461: サイコバーン](moves/461.md) | {"level":"85","order":"23","route":"level_up"} | level_up_final.csv:5663 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [324: ラプラス](pokemon/324.md) | [434: だいこうずい](moves/434.md) | {"level":"55","order":"18","route":"level_up"} | level_up_final.csv:5702 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [325: ドレディア](pokemon/325.md) | [444: だいせいちょう](moves/444.md) | {"level":"46","order":"8","route":"level_up"} | level_up_final.csv:5711 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [331: ドラピオン](pokemon/331.md) | [476: ダークカッター](moves/476.md) | {"level":"28","order":"12","route":"level_up"} | level_up_final.csv:5822 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [331: ドラピオン](pokemon/331.md) | [454: もぐる](moves/454.md) | {"level":"56","order":"19","route":"level_up"} | level_up_final.csv:5829 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [332: マスキッパ](pokemon/332.md) | [441: おいしげる](moves/441.md) | {"level":"57","order":"17","route":"level_up"} | level_up_final.csv:5848 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [340: ウリムー](pokemon/340.md) | [446: スターフリーズ](moves/446.md) | {"level":"52","order":"16","route":"level_up"} | level_up_final.csv:6012 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [341: ノコッチ](pokemon/341.md) | [454: もぐる](moves/454.md) | {"level":"36","order":"12","route":"level_up"} | level_up_final.csv:6024 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [343: カモネギ](pokemon/343.md) | [456: すなかぜ](moves/456.md) | {"level":"37","order":"17","route":"level_up"} | level_up_final.csv:6074 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [343: カモネギ](pokemon/343.md) | [466: かくらんひこう](moves/466.md) | {"level":"43","order":"19","route":"level_up"} | level_up_final.csv:6076 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [346: コータス](pokemon/346.md) | [453: どくえんまく](moves/453.md) | {"level":"23","order":"8","route":"level_up"} | level_up_final.csv:6128 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [348: ラブカス](pokemon/348.md) | [430: おおあくび](moves/430.md) | {"level":"59","order":"16","route":"level_up"} | level_up_final.csv:6181 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [351: マンムー](pokemon/351.md) | [469: げんしのいぶき](moves/469.md) | {"level":"20","order":"10","route":"level_up"} | level_up_final.csv:6230 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [351: マンムー](pokemon/351.md) | [446: スターフリーズ](moves/446.md) | {"level":"62","order":"23","route":"level_up"} | level_up_final.csv:6243 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [352: マッギョ](pokemon/352.md) | [454: もぐる](moves/454.md) | {"level":"30","order":"10","route":"level_up"} | level_up_final.csv:6253 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [354: フリージオ](pokemon/354.md) | [448: アイスバーン](moves/448.md) | {"level":"49","order":"16","route":"level_up"} | level_up_final.csv:6300 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [355: エルレイド](pokemon/355.md) | [463: さいみんはどう](moves/463.md) | {"level":"25","order":"12","route":"level_up"} | level_up_final.csv:6317 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [355: エルレイド](pokemon/355.md) | [459: サイコバレット](moves/459.md) | {"level":"67","order":"25","route":"level_up"} | level_up_final.csv:6330 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [359: ギアル](pokemon/359.md) | [427: ダブルスピン](moves/427.md) | {"level":"11","order":"5","route":"level_up"} | level_up_final.csv:6397 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [359: ギアル](pokemon/359.md) | [440: たいでん](moves/440.md) | {"level":"31","order":"9","route":"level_up"} | level_up_final.csv:6401 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [361: ナットレイ](pokemon/361.md) | [442: リーフガード](moves/442.md) | {"level":"21","order":"10","route":"level_up"} | level_up_final.csv:6435 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [361: ナットレイ](pokemon/361.md) | [441: おいしげる](moves/441.md) | {"level":"53","order":"20","route":"level_up"} | level_up_final.csv:6445 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [363: イシツブテ](pokemon/363.md) | [355: グランボールダ](moves/355.md) | {"level":"50","order":"19","route":"level_up"} | level_up_final.csv:6471 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [365: ラッキー](pokemon/365.md) | [425: げきとつ](moves/425.md) | {"level":"54","order":"19","route":"level_up"} | level_up_final.csv:6497 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [366: ハピナス](pokemon/366.md) | [425: げきとつ](moves/425.md) | {"level":"54","order":"20","route":"level_up"} | level_up_final.csv:6517 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [367: ゴローン](pokemon/367.md) | [355: グランボールダ](moves/355.md) | {"level":"64","order":"21","route":"level_up"} | level_up_final.csv:6538 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [368: ゴローニャ](pokemon/368.md) | [355: グランボールダ](moves/355.md) | {"level":"64","order":"20","route":"level_up"} | level_up_final.csv:6558 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [368: ゴローニャ](pokemon/368.md) | [425: げきとつ](moves/425.md) | {"level":"69","order":"21","route":"level_up"} | level_up_final.csv:6559 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [369: シビビール](pokemon/369.md) | [439: マッハボルト](moves/439.md) | {"level":"19","order":"6","route":"level_up"} | level_up_final.csv:6565 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [370: サンド](pokemon/370.md) | [454: もぐる](moves/454.md) | {"level":"31","order":"13","route":"level_up"} | level_up_final.csv:6588 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [370: サンド](pokemon/370.md) | [467: いわころがり](moves/467.md) | {"level":"39","order":"16","route":"level_up"} | level_up_final.csv:6591 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [371: サンドパン](pokemon/371.md) | [454: もぐる](moves/454.md) | {"level":"34","order":"14","route":"level_up"} | level_up_final.csv:6606 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [371: サンドパン](pokemon/371.md) | [467: いわころがり](moves/467.md) | {"level":"45","order":"17","route":"level_up"} | level_up_final.csv:6609 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [374: ズルッグ](pokemon/374.md) | [479: おいつめる](moves/479.md) | {"level":"23","order":"10","route":"level_up"} | level_up_final.csv:6666 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [374: ズルッグ](pokemon/374.md) | [474: ふくしゅう](moves/474.md) | {"level":"27","order":"12","route":"level_up"} | level_up_final.csv:6668 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [375: ズルズキン](pokemon/375.md) | [479: おいつめる](moves/479.md) | {"level":"23","order":"11","route":"level_up"} | level_up_final.csv:6687 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [375: ズルズキン](pokemon/375.md) | [474: ふくしゅう](moves/474.md) | {"level":"27","order":"12","route":"level_up"} | level_up_final.csv:6688 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [377: イワパレス](pokemon/377.md) | [355: グランボールダ](moves/355.md) | {"level":"59","order":"22","route":"level_up"} | level_up_final.csv:6726 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [378: テッシード](pokemon/378.md) | [442: リーフガード](moves/442.md) | {"level":"21","order":"9","route":"level_up"} | level_up_final.csv:6735 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [378: テッシード](pokemon/378.md) | [441: おいしげる](moves/441.md) | {"level":"47","order":"15","route":"level_up"} | level_up_final.csv:6741 | True | &#91;"egg","level_up"&#93; | False |
| official_to_vega_legacy_preservation | [379: ギギギアル](pokemon/379.md) | [427: ダブルスピン](moves/427.md) | {"level":"1","order":"4","route":"level_up"} | level_up_final.csv:6747 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [379: ギギギアル](pokemon/379.md) | [427: ダブルスピン](moves/427.md) | {"level":"11","order":"7","route":"level_up"} | level_up_final.csv:6750 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [379: ギギギアル](pokemon/379.md) | [440: たいでん](moves/440.md) | {"level":"31","order":"11","route":"level_up"} | level_up_final.csv:6754 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [379: ギギギアル](pokemon/379.md) | [438: メガショック](moves/438.md) | {"level":"38","order":"13","route":"level_up"} | level_up_final.csv:6756 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [379: ギギギアル](pokemon/379.md) | [481: ジオインパクト](moves/481.md) | {"level":"49","order":"17","route":"level_up"} | level_up_final.csv:6760 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [379: ギギギアル](pokemon/379.md) | [436: ギガスパーク](moves/436.md) | {"level":"66","order":"22","route":"level_up"} | level_up_final.csv:6765 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [379: ギギギアル](pokemon/379.md) | [361: メタルブラスト](moves/361.md) | {"level":"72","order":"23","route":"level_up"} | level_up_final.csv:6766 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [380: ギギアル](pokemon/380.md) | [427: ダブルスピン](moves/427.md) | {"level":"1","order":"4","route":"level_up"} | level_up_final.csv:6770 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [380: ギギアル](pokemon/380.md) | [427: ダブルスピン](moves/427.md) | {"level":"11","order":"7","route":"level_up"} | level_up_final.csv:6773 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [380: ギギアル](pokemon/380.md) | [440: たいでん](moves/440.md) | {"level":"31","order":"12","route":"level_up"} | level_up_final.csv:6778 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [380: ギギアル](pokemon/380.md) | [438: メガショック](moves/438.md) | {"level":"38","order":"14","route":"level_up"} | level_up_final.csv:6780 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [380: ギギアル](pokemon/380.md) | [436: ギガスパーク](moves/436.md) | {"level":"60","order":"21","route":"level_up"} | level_up_final.csv:6787 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [381: チュリネ](pokemon/381.md) | [445: げんわくごな](moves/445.md) | {"level":"37","order":"13","route":"level_up"} | level_up_final.csv:6801 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [395: コジョフー](pokemon/395.md) | [451: ダブルショット](moves/451.md) | {"level":"17","order":"7","route":"level_up"} | level_up_final.csv:7086 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [396: コジョンド](pokemon/396.md) | [451: ダブルショット](moves/451.md) | {"level":"17","order":"8","route":"level_up"} | level_up_final.csv:7106 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [396: コジョンド](pokemon/396.md) | [450: マグナムパンチ](moves/450.md) | {"level":"37","order":"13","route":"level_up"} | level_up_final.csv:7111 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [397: メグロコ](pokemon/397.md) | [479: おいつめる](moves/479.md) | {"level":"19","order":"8","route":"level_up"} | level_up_final.csv:7127 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [397: メグロコ](pokemon/397.md) | [474: ふくしゅう](moves/474.md) | {"level":"37","order":"15","route":"level_up"} | level_up_final.csv:7134 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [398: ワルビル](pokemon/398.md) | [479: おいつめる](moves/479.md) | {"level":"19","order":"10","route":"level_up"} | level_up_final.csv:7147 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [398: ワルビル](pokemon/398.md) | [474: ふくしゅう](moves/474.md) | {"level":"40","order":"17","route":"level_up"} | level_up_final.csv:7154 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [399: ワルビアル](pokemon/399.md) | [479: おいつめる](moves/479.md) | {"level":"19","order":"10","route":"level_up"} | level_up_final.csv:7168 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [399: ワルビアル](pokemon/399.md) | [474: ふくしゅう](moves/474.md) | {"level":"42","order":"16","route":"level_up"} | level_up_final.csv:7174 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [403: ヒードラン](pokemon/403.md) | [357: スターダスト](moves/357.md) | {"level":"50","order":"12","route":"level_up"} | level_up_final.csv:7250 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [403: ヒードラン](pokemon/403.md) | [481: ジオインパクト](moves/481.md) | {"level":"85","order":"18","route":"level_up"} | level_up_final.csv:7256 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [403: ヒードラン](pokemon/403.md) | [418: マグマアクセル](moves/418.md) | {"level":"99","order":"20","route":"level_up"} | level_up_final.csv:7258 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [404: フィオネ](pokemon/404.md) | [449: こおりのキッス](moves/449.md) | {"level":"69","order":"12","route":"level_up"} | level_up_final.csv:7270 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [404: フィオネ](pokemon/404.md) | [434: だいこうずい](moves/434.md) | {"level":"91","order":"15","route":"level_up"} | level_up_final.csv:7273 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [405: マナフィ](pokemon/405.md) | [449: こおりのキッス](moves/449.md) | {"level":"69","order":"13","route":"level_up"} | level_up_final.csv:7286 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [405: マナフィ](pokemon/405.md) | [434: だいこうずい](moves/434.md) | {"level":"91","order":"16","route":"level_up"} | level_up_final.csv:7289 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [407: ラティアス](pokemon/407.md) | [461: サイコバーン](moves/461.md) | {"level":"65","order":"18","route":"level_up"} | level_up_final.csv:7326 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [408: ラティオス](pokemon/408.md) | [461: サイコバーン](moves/461.md) | {"level":"65","order":"18","route":"level_up"} | level_up_final.csv:7348 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [411: シビルドン](pokemon/411.md) | [440: たいでん](moves/440.md) | {"level":"1","order":"1","route":"level_up"} | level_up_final.csv:7394 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [411: シビルドン](pokemon/411.md) | [470: ソウルバイト](moves/470.md) | {"level":"49","order":"10","route":"level_up"} | level_up_final.csv:7403 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [411: シビルドン](pokemon/411.md) | [436: ギガスパーク](moves/436.md) | {"level":"69","order":"12","route":"level_up"} | level_up_final.csv:7405 | True | &#91;"level_up"&#93; | False |
| official_to_vega_legacy_preservation | [10: スバメ](pokemon/10.md) | [466: かくらんひこう](moves/466.md) | {"order":"9","route":"egg"} | egg_moves_final.csv:93 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [12: リオル](pokemon/12.md) | [464: じゅうりょくは](moves/464.md) | {"order":"12","route":"egg"} | egg_moves_final.csv:124 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [14: デルビル](pokemon/14.md) | [470: ソウルバイト](moves/470.md) | {"order":"12","route":"egg"} | egg_moves_final.csv:152 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [14: デルビル](pokemon/14.md) | [474: ふくしゅう](moves/474.md) | {"order":"19","route":"egg"} | egg_moves_final.csv:159 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [16: ディグダ](pokemon/16.md) | [481: ジオインパクト](moves/481.md) | {"order":"11","route":"egg"} | egg_moves_final.csv:176 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [18: トゲピー](pokemon/18.md) | [466: かくらんひこう](moves/466.md) | {"order":"7","route":"egg"} | egg_moves_final.csv:196 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [18: トゲピー](pokemon/18.md) | [461: サイコバーン](moves/461.md) | {"order":"11","route":"egg"} | egg_moves_final.csv:200 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [24: ピチュー](pokemon/24.md) | [440: たいでん](moves/440.md) | {"order":"20","route":"egg"} | egg_moves_final.csv:273 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [28: エアームド](pokemon/28.md) | [466: かくらんひこう](moves/466.md) | {"order":"5","route":"egg"} | egg_moves_final.csv:293 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [28: エアームド](pokemon/28.md) | [457: かっくう](moves/457.md) | {"order":"7","route":"egg"} | egg_moves_final.csv:295 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [28: エアームド](pokemon/28.md) | [456: すなかぜ](moves/456.md) | {"order":"13","route":"egg"} | egg_moves_final.csv:301 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [29: ニドラン♀](pokemon/29.md) | [448: アイスバーン](moves/448.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:314 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [29: ニドラン♀](pokemon/29.md) | [425: げきとつ](moves/425.md) | {"order":"10","route":"egg"} | egg_moves_final.csv:323 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [32: ニドラン♂](pokemon/32.md) | [448: アイスバーン](moves/448.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:343 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [32: ニドラン♂](pokemon/32.md) | [425: げきとつ](moves/425.md) | {"order":"8","route":"egg"} | egg_moves_final.csv:350 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [35: ブイゼル](pokemon/35.md) | [357: スターダスト](moves/357.md) | {"order":"13","route":"egg"} | egg_moves_final.csv:383 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [39: クヌギダマ](pokemon/39.md) | [467: いわころがり](moves/467.md) | {"order":"3","route":"egg"} | egg_moves_final.csv:424 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [41: シェルダー](pokemon/41.md) | [469: げんしのいぶき](moves/469.md) | {"order":"5","route":"egg"} | egg_moves_final.csv:452 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [41: シェルダー](pokemon/41.md) | [446: スターフリーズ](moves/446.md) | {"order":"9","route":"egg"} | egg_moves_final.csv:456 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [41: シェルダー](pokemon/41.md) | [474: ふくしゅう](moves/474.md) | {"order":"17","route":"egg"} | egg_moves_final.csv:464 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [52: アブソル](pokemon/52.md) | [477: ダークロアー](moves/477.md) | {"order":"15","route":"egg"} | egg_moves_final.csv:565 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [52: アブソル](pokemon/52.md) | [509: ダークスナイプ](moves/509.md) | {"order":"22","route":"egg"} | egg_moves_final.csv:572 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [52: アブソル](pokemon/52.md) | [474: ふくしゅう](moves/474.md) | {"order":"27","route":"egg"} | egg_moves_final.csv:577 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [54: キリンリキ](pokemon/54.md) | [461: サイコバーン](moves/461.md) | {"order":"6","route":"egg"} | egg_moves_final.csv:592 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [63: ゴース](pokemon/63.md) | [452: きけんなどくそ](moves/452.md) | {"order":"7","route":"egg"} | egg_moves_final.csv:663 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [63: ゴース](pokemon/63.md) | [470: ソウルバイト](moves/470.md) | {"order":"10","route":"egg"} | egg_moves_final.csv:666 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [63: ゴース](pokemon/63.md) | [461: サイコバーン](moves/461.md) | {"order":"13","route":"egg"} | egg_moves_final.csv:669 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [63: ゴース](pokemon/63.md) | [463: さいみんはどう](moves/463.md) | {"order":"14","route":"egg"} | egg_moves_final.csv:670 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [63: ゴース](pokemon/63.md) | [474: ふくしゅう](moves/474.md) | {"order":"21","route":"egg"} | egg_moves_final.csv:677 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [63: ゴース](pokemon/63.md) | [472: ライフダウン](moves/472.md) | {"order":"27","route":"egg"} | egg_moves_final.csv:683 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [66: タマタマ](pokemon/66.md) | [428: おんち](moves/428.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:692 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [66: タマタマ](pokemon/66.md) | [464: じゅうりょくは](moves/464.md) | {"order":"11","route":"egg"} | egg_moves_final.csv:701 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [71: サイホーン](pokemon/71.md) | [448: アイスバーン](moves/448.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:771 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [71: サイホーン](pokemon/71.md) | [355: グランボールダ](moves/355.md) | {"order":"12","route":"egg"} | egg_moves_final.csv:781 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [71: サイホーン](pokemon/71.md) | [455: サンドソニック](moves/455.md) | {"order":"16","route":"egg"} | egg_moves_final.csv:785 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [74: トロピウス](pokemon/74.md) | [469: げんしのいぶき](moves/469.md) | {"order":"4","route":"egg"} | egg_moves_final.csv:807 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [74: トロピウス](pokemon/74.md) | [456: すなかぜ](moves/456.md) | {"order":"9","route":"egg"} | egg_moves_final.csv:812 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [74: トロピウス](pokemon/74.md) | [444: だいせいちょう](moves/444.md) | {"order":"11","route":"egg"} | egg_moves_final.csv:814 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [78: タマザラシ](pokemon/78.md) | [448: アイスバーン](moves/448.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:833 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [78: タマザラシ](pokemon/78.md) | [434: だいこうずい](moves/434.md) | {"order":"12","route":"egg"} | egg_moves_final.csv:843 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [85: ユキカブリ](pokemon/85.md) | [441: おいしげる](moves/441.md) | {"order":"3","route":"egg"} | egg_moves_final.csv:915 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [85: ユキカブリ](pokemon/85.md) | [469: げんしのいぶき](moves/469.md) | {"order":"5","route":"egg"} | egg_moves_final.csv:917 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [85: ユキカブリ](pokemon/85.md) | [447: つららパンチ](moves/447.md) | {"order":"15","route":"egg"} | egg_moves_final.csv:927 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [92: ミルタンク](pokemon/92.md) | [429: めまわし](moves/429.md) | {"order":"29","route":"egg"} | egg_moves_final.csv:1019 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [93: ツボツボ](pokemon/93.md) | [467: いわころがり](moves/467.md) | {"order":"4","route":"egg"} | egg_moves_final.csv:1027 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [93: ツボツボ](pokemon/93.md) | [355: グランボールダ](moves/355.md) | {"order":"5","route":"egg"} | egg_moves_final.csv:1028 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [93: ツボツボ](pokemon/93.md) | [487: しゅうげき](moves/487.md) | {"order":"7","route":"egg"} | egg_moves_final.csv:1030 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [109: ホーホー](pokemon/109.md) | [466: かくらんひこう](moves/466.md) | {"order":"6","route":"egg"} | egg_moves_final.csv:1257 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [109: ホーホー](pokemon/109.md) | [457: かっくう](moves/457.md) | {"order":"7","route":"egg"} | egg_moves_final.csv:1258 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [109: ホーホー](pokemon/109.md) | [487: しゅうげき](moves/487.md) | {"order":"13","route":"egg"} | egg_moves_final.csv:1264 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [109: ホーホー](pokemon/109.md) | [429: めまわし](moves/429.md) | {"order":"25","route":"egg"} | egg_moves_final.csv:1276 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [112: エレキッド](pokemon/112.md) | [355: グランボールダ](moves/355.md) | {"order":"7","route":"egg"} | egg_moves_final.csv:1316 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [112: エレキッド](pokemon/112.md) | [450: マグナムパンチ](moves/450.md) | {"order":"17","route":"egg"} | egg_moves_final.csv:1326 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [112: エレキッド](pokemon/112.md) | [429: めまわし](moves/429.md) | {"order":"19","route":"egg"} | egg_moves_final.csv:1328 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [115: ブビィ](pokemon/115.md) | [481: ジオインパクト](moves/481.md) | {"order":"10","route":"egg"} | egg_moves_final.csv:1344 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [115: ブビィ](pokemon/115.md) | [450: マグナムパンチ](moves/450.md) | {"order":"20","route":"egg"} | egg_moves_final.csv:1354 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [115: ブビィ](pokemon/115.md) | [429: めまわし](moves/429.md) | {"order":"23","route":"egg"} | egg_moves_final.csv:1357 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [118: ガルーラ](pokemon/118.md) | [426: スピンテール](moves/426.md) | {"order":"22","route":"egg"} | egg_moves_final.csv:1381 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [119: リリーラ](pokemon/119.md) | [452: きけんなどくそ](moves/452.md) | {"order":"4","route":"egg"} | egg_moves_final.csv:1399 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [119: リリーラ](pokemon/119.md) | [469: げんしのいぶき](moves/469.md) | {"order":"6","route":"egg"} | egg_moves_final.csv:1401 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [123: プテラ](pokemon/123.md) | [466: かくらんひこう](moves/466.md) | {"order":"5","route":"egg"} | egg_moves_final.csv:1449 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [123: プテラ](pokemon/123.md) | [470: ソウルバイト](moves/470.md) | {"order":"6","route":"egg"} | egg_moves_final.csv:1450 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [123: プテラ](pokemon/123.md) | [469: げんしのいぶき](moves/469.md) | {"order":"8","route":"egg"} | egg_moves_final.csv:1452 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [123: プテラ](pokemon/123.md) | [487: しゅうげき](moves/487.md) | {"order":"10","route":"egg"} | egg_moves_final.csv:1454 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [123: プテラ](pokemon/123.md) | [456: すなかぜ](moves/456.md) | {"order":"13","route":"egg"} | egg_moves_final.csv:1457 | True | &#91;"egg","level_up"&#93; | False |
| official_to_vega_legacy_preservation | [123: プテラ](pokemon/123.md) | [361: メタルブラスト](moves/361.md) | {"order":"22","route":"egg"} | egg_moves_final.csv:1466 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [124: ヨーギラス](pokemon/124.md) | [470: ソウルバイト](moves/470.md) | {"order":"7","route":"egg"} | egg_moves_final.csv:1475 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [124: ヨーギラス](pokemon/124.md) | [425: げきとつ](moves/425.md) | {"order":"8","route":"egg"} | egg_moves_final.csv:1476 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [124: ヨーギラス](pokemon/124.md) | [455: サンドソニック](moves/455.md) | {"order":"11","route":"egg"} | egg_moves_final.csv:1479 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [124: ヨーギラス](pokemon/124.md) | [481: ジオインパクト](moves/481.md) | {"order":"12","route":"egg"} | egg_moves_final.csv:1480 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [130: フカマル](pokemon/130.md) | [481: ジオインパクト](moves/481.md) | {"order":"8","route":"egg"} | egg_moves_final.csv:1509 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [130: フカマル](pokemon/130.md) | [456: すなかぜ](moves/456.md) | {"order":"13","route":"egg"} | egg_moves_final.csv:1514 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [152: フシギダネ](pokemon/152.md) | [445: げんわくごな](moves/445.md) | {"order":"5","route":"egg"} | egg_moves_final.csv:1568 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [155: ヒトカゲ](pokemon/155.md) | [426: スピンテール](moves/426.md) | {"order":"12","route":"egg"} | egg_moves_final.csv:1604 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [158: ゼニガメ](pokemon/158.md) | [447: つららパンチ](moves/447.md) | {"order":"16","route":"egg"} | egg_moves_final.csv:1637 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [175: パチリス](pokemon/175.md) | [428: おんち](moves/428.md) | {"order":"7","route":"egg"} | egg_moves_final.csv:1802 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [175: パチリス](pokemon/175.md) | [429: めまわし](moves/429.md) | {"order":"23","route":"egg"} | egg_moves_final.csv:1818 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [184: ムチュール](pokemon/184.md) | [461: サイコバーン](moves/461.md) | {"order":"7","route":"egg"} | egg_moves_final.csv:1929 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [184: ムチュール](pokemon/184.md) | [462: めざめぬパワー](moves/462.md) | {"order":"17","route":"egg"} | egg_moves_final.csv:1939 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [193: ペラップ](pokemon/193.md) | [466: かくらんひこう](moves/466.md) | {"order":"6","route":"egg"} | egg_moves_final.csv:2022 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [193: ペラップ](pokemon/193.md) | [487: しゅうげき](moves/487.md) | {"order":"11","route":"egg"} | egg_moves_final.csv:2027 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [193: ペラップ](pokemon/193.md) | [476: ダークカッター](moves/476.md) | {"order":"12","route":"egg"} | egg_moves_final.csv:2028 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [198: レディバ](pokemon/198.md) | [466: かくらんひこう](moves/466.md) | {"order":"8","route":"egg"} | egg_moves_final.csv:2139 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [198: レディバ](pokemon/198.md) | [456: すなかぜ](moves/456.md) | {"order":"15","route":"egg"} | egg_moves_final.csv:2146 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [198: レディバ](pokemon/198.md) | [450: マグナムパンチ](moves/450.md) | {"order":"22","route":"egg"} | egg_moves_final.csv:2153 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [212: メノクラゲ](pokemon/212.md) | [433: スプラッシュ](moves/433.md) | {"order":"11","route":"egg"} | egg_moves_final.csv:2238 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [226: ヤミカラス](pokemon/226.md) | [466: かくらんひこう](moves/466.md) | {"order":"8","route":"egg"} | egg_moves_final.csv:2414 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [226: ヤミカラス](pokemon/226.md) | [457: かっくう](moves/457.md) | {"order":"10","route":"egg"} | egg_moves_final.csv:2416 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [226: ヤミカラス](pokemon/226.md) | [463: さいみんはどう](moves/463.md) | {"order":"13","route":"egg"} | egg_moves_final.csv:2419 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [226: ヤミカラス](pokemon/226.md) | [456: すなかぜ](moves/456.md) | {"order":"15","route":"egg"} | egg_moves_final.csv:2421 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [228: ゴニョニョ](pokemon/228.md) | [470: ソウルバイト](moves/470.md) | {"order":"15","route":"egg"} | egg_moves_final.csv:2452 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [231: クラブ](pokemon/231.md) | [448: アイスバーン](moves/448.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2474 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [231: クラブ](pokemon/231.md) | [434: だいこうずい](moves/434.md) | {"order":"12","route":"egg"} | egg_moves_final.csv:2485 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [247: ニューラ](pokemon/247.md) | [448: アイスバーン](moves/448.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2652 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [247: ニューラ](pokemon/247.md) | [449: こおりのキッス](moves/449.md) | {"order":"11","route":"egg"} | egg_moves_final.csv:2662 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [247: ニューラ](pokemon/247.md) | [446: スターフリーズ](moves/446.md) | {"order":"14","route":"egg"} | egg_moves_final.csv:2665 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [249: キノココ](pokemon/249.md) | [445: げんわくごな](moves/445.md) | {"order":"11","route":"egg"} | egg_moves_final.csv:2694 | True | &#91;"egg","level_up"&#93; | False |
| official_to_vega_legacy_preservation | [278: ヤミラミ](pokemon/278.md) | [479: おいつめる](moves/479.md) | {"order":"5","route":"egg"} | egg_moves_final.csv:2748 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [278: ヤミラミ](pokemon/278.md) | [357: スターダスト](moves/357.md) | {"order":"13","route":"egg"} | egg_moves_final.csv:2756 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [278: ヤミラミ](pokemon/278.md) | [356: ソウルブレイク](moves/356.md) | {"order":"14","route":"egg"} | egg_moves_final.csv:2757 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [278: ヤミラミ](pokemon/278.md) | [475: ダークリゾルブ](moves/475.md) | {"order":"15","route":"egg"} | egg_moves_final.csv:2758 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [278: ヤミラミ](pokemon/278.md) | [450: マグナムパンチ](moves/450.md) | {"order":"24","route":"egg"} | egg_moves_final.csv:2767 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [278: ヤミラミ](pokemon/278.md) | [454: もぐる](moves/454.md) | {"order":"27","route":"egg"} | egg_moves_final.csv:2770 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [280: クチート](pokemon/280.md) | [470: ソウルバイト](moves/470.md) | {"order":"12","route":"egg"} | egg_moves_final.csv:2790 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [280: クチート](pokemon/280.md) | [449: こおりのキッス](moves/449.md) | {"order":"14","route":"egg"} | egg_moves_final.csv:2792 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [280: クチート](pokemon/280.md) | [487: しゅうげき](moves/487.md) | {"order":"17","route":"egg"} | egg_moves_final.csv:2795 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [284: カイロス](pokemon/284.md) | [355: グランボールダ](moves/355.md) | {"order":"8","route":"egg"} | egg_moves_final.csv:2848 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [284: カイロス](pokemon/284.md) | [455: サンドソニック](moves/455.md) | {"order":"9","route":"egg"} | egg_moves_final.csv:2849 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [284: カイロス](pokemon/284.md) | [454: もぐる](moves/454.md) | {"order":"22","route":"egg"} | egg_moves_final.csv:2862 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [286: アーボ](pokemon/286.md) | [481: ジオインパクト](moves/481.md) | {"order":"11","route":"egg"} | egg_moves_final.csv:2875 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [286: アーボ](pokemon/286.md) | [359: のりうつる](moves/359.md) | {"order":"19","route":"egg"} | egg_moves_final.csv:2883 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [286: アーボ](pokemon/286.md) | [474: ふくしゅう](moves/474.md) | {"order":"20","route":"egg"} | egg_moves_final.csv:2884 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [289: ドガース](pokemon/289.md) | [467: いわころがり](moves/467.md) | {"order":"4","route":"egg"} | egg_moves_final.csv:2898 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [289: ドガース](pokemon/289.md) | [436: ギガスパーク](moves/436.md) | {"order":"9","route":"egg"} | egg_moves_final.csv:2903 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [289: ドガース](pokemon/289.md) | [459: サイコバレット](moves/459.md) | {"order":"13","route":"egg"} | egg_moves_final.csv:2907 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [289: ドガース](pokemon/289.md) | [356: ソウルブレイク](moves/356.md) | {"order":"14","route":"egg"} | egg_moves_final.csv:2908 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [289: ドガース](pokemon/289.md) | [509: ダークスナイプ](moves/509.md) | {"order":"18","route":"egg"} | egg_moves_final.csv:2912 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [292: ヨマワル](pokemon/292.md) | [448: アイスバーン](moves/448.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2924 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [292: ヨマワル](pokemon/292.md) | [479: おいつめる](moves/479.md) | {"order":"7","route":"egg"} | egg_moves_final.csv:2930 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [292: ヨマワル](pokemon/292.md) | [463: さいみんはどう](moves/463.md) | {"order":"12","route":"egg"} | egg_moves_final.csv:2935 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [292: ヨマワル](pokemon/292.md) | [464: じゅうりょくは](moves/464.md) | {"order":"14","route":"egg"} | egg_moves_final.csv:2937 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [292: ヨマワル](pokemon/292.md) | [471: たたり](moves/471.md) | {"order":"16","route":"egg"} | egg_moves_final.csv:2939 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [292: ヨマワル](pokemon/292.md) | [509: ダークスナイプ](moves/509.md) | {"order":"24","route":"egg"} | egg_moves_final.csv:2947 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [295: ベロリンガ](pokemon/295.md) | [448: アイスバーン](moves/448.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2955 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [295: ベロリンガ](pokemon/295.md) | [433: スプラッシュ](moves/433.md) | {"order":"18","route":"egg"} | egg_moves_final.csv:2972 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [297: イトマル](pokemon/297.md) | [475: ダークリゾルブ](moves/475.md) | {"order":"11","route":"egg"} | egg_moves_final.csv:3004 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [299: バチュル](pokemon/299.md) | [452: きけんなどくそ](moves/452.md) | {"order":"8","route":"egg"} | egg_moves_final.csv:3027 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [299: バチュル](pokemon/299.md) | [487: しゅうげき](moves/487.md) | {"order":"11","route":"egg"} | egg_moves_final.csv:3030 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [308: パッチール](pokemon/308.md) | [461: サイコバーン](moves/461.md) | {"order":"17","route":"egg"} | egg_moves_final.csv:3149 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [308: パッチール](pokemon/308.md) | [464: じゅうりょくは](moves/464.md) | {"order":"19","route":"egg"} | egg_moves_final.csv:3151 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [309: ジーランス](pokemon/309.md) | [425: げきとつ](moves/425.md) | {"order":"7","route":"egg"} | egg_moves_final.csv:3178 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [309: ジーランス](pokemon/309.md) | [446: スターフリーズ](moves/446.md) | {"order":"14","route":"egg"} | egg_moves_final.csv:3185 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [309: ジーランス](pokemon/309.md) | [433: スプラッシュ](moves/433.md) | {"order":"15","route":"egg"} | egg_moves_final.csv:3186 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [313: カゲボウズ](pokemon/313.md) | [436: ギガスパーク](moves/436.md) | {"order":"10","route":"egg"} | egg_moves_final.csv:3244 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [313: カゲボウズ](pokemon/313.md) | [356: ソウルブレイク](moves/356.md) | {"order":"13","route":"egg"} | egg_moves_final.csv:3247 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [313: カゲボウズ](pokemon/313.md) | [471: たたり](moves/471.md) | {"order":"15","route":"egg"} | egg_moves_final.csv:3249 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [313: カゲボウズ](pokemon/313.md) | [474: ふくしゅう](moves/474.md) | {"order":"21","route":"egg"} | egg_moves_final.csv:3255 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [317: イシズマイ](pokemon/317.md) | [456: すなかぜ](moves/456.md) | {"order":"12","route":"egg"} | egg_moves_final.csv:3306 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [318: サボネア](pokemon/318.md) | [479: おいつめる](moves/479.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:3319 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [318: サボネア](pokemon/318.md) | [474: ふくしゅう](moves/474.md) | {"order":"20","route":"egg"} | egg_moves_final.csv:3337 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [318: サボネア](pokemon/318.md) | [450: マグナムパンチ](moves/450.md) | {"order":"22","route":"egg"} | egg_moves_final.csv:3339 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [318: サボネア](pokemon/318.md) | [442: リーフガード](moves/442.md) | {"order":"26","route":"egg"} | egg_moves_final.csv:3343 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [330: スコルピ](pokemon/330.md) | [470: ソウルバイト](moves/470.md) | {"order":"8","route":"egg"} | egg_moves_final.csv:3432 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [330: スコルピ](pokemon/330.md) | [487: しゅうげき](moves/487.md) | {"order":"10","route":"egg"} | egg_moves_final.csv:3434 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [330: スコルピ](pokemon/330.md) | [475: ダークリゾルブ](moves/475.md) | {"order":"17","route":"egg"} | egg_moves_final.csv:3441 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [330: スコルピ](pokemon/330.md) | [474: ふくしゅう](moves/474.md) | {"order":"28","route":"egg"} | egg_moves_final.csv:3452 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [332: マスキッパ](pokemon/332.md) | [470: ソウルバイト](moves/470.md) | {"order":"3","route":"egg"} | egg_moves_final.csv:3466 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [332: マスキッパ](pokemon/332.md) | [445: げんわくごな](moves/445.md) | {"order":"4","route":"egg"} | egg_moves_final.csv:3467 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [332: マスキッパ](pokemon/332.md) | [444: だいせいちょう](moves/444.md) | {"order":"9","route":"egg"} | egg_moves_final.csv:3472 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [340: ウリムー](pokemon/340.md) | [448: アイスバーン](moves/448.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:3569 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [341: ノコッチ](pokemon/341.md) | [470: ソウルバイト](moves/470.md) | {"order":"13","route":"egg"} | egg_moves_final.csv:3610 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [341: ノコッチ](pokemon/341.md) | [487: しゅうげき](moves/487.md) | {"order":"18","route":"egg"} | egg_moves_final.csv:3615 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [343: カモネギ](pokemon/343.md) | [457: かっくう](moves/457.md) | {"order":"5","route":"egg"} | egg_moves_final.csv:3635 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [343: カモネギ](pokemon/343.md) | [487: しゅうげき](moves/487.md) | {"order":"10","route":"egg"} | egg_moves_final.csv:3640 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [343: カモネギ](pokemon/343.md) | [426: スピンテール](moves/426.md) | {"order":"12","route":"egg"} | egg_moves_final.csv:3642 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [343: カモネギ](pokemon/343.md) | [509: ダークスナイプ](moves/509.md) | {"order":"16","route":"egg"} | egg_moves_final.csv:3646 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [343: カモネギ](pokemon/343.md) | [458: ハリケーン](moves/458.md) | {"order":"22","route":"egg"} | egg_moves_final.csv:3652 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [346: コータス](pokemon/346.md) | [467: いわころがり](moves/467.md) | {"order":"3","route":"egg"} | egg_moves_final.csv:3696 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [346: コータス](pokemon/346.md) | [469: げんしのいぶき](moves/469.md) | {"order":"6","route":"egg"} | egg_moves_final.csv:3699 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [346: コータス](pokemon/346.md) | [455: サンドソニック](moves/455.md) | {"order":"9","route":"egg"} | egg_moves_final.csv:3702 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [346: コータス](pokemon/346.md) | [427: ダブルスピン](moves/427.md) | {"order":"16","route":"egg"} | egg_moves_final.csv:3709 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [346: コータス](pokemon/346.md) | [454: もぐる](moves/454.md) | {"order":"23","route":"egg"} | egg_moves_final.csv:3716 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [352: マッギョ](pokemon/352.md) | [440: たいでん](moves/440.md) | {"order":"15","route":"egg"} | egg_moves_final.csv:3758 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [352: マッギョ](pokemon/352.md) | [439: マッハボルト](moves/439.md) | {"order":"25","route":"egg"} | egg_moves_final.csv:3768 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [363: イシツブテ](pokemon/363.md) | [467: いわころがり](moves/467.md) | {"order":"3","route":"egg"} | egg_moves_final.csv:3813 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [363: イシツブテ](pokemon/363.md) | [474: ふくしゅう](moves/474.md) | {"order":"23","route":"egg"} | egg_moves_final.csv:3833 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [363: イシツブテ](pokemon/363.md) | [450: マグナムパンチ](moves/450.md) | {"order":"26","route":"egg"} | egg_moves_final.csv:3836 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [364: ピンプク](pokemon/364.md) | [461: サイコバーン](moves/461.md) | {"order":"12","route":"egg"} | egg_moves_final.csv:3852 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [364: ピンプク](pokemon/364.md) | [464: じゅうりょくは](moves/464.md) | {"order":"16","route":"egg"} | egg_moves_final.csv:3856 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [364: ピンプク](pokemon/364.md) | [357: スターダスト](moves/357.md) | {"order":"19","route":"egg"} | egg_moves_final.csv:3859 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [370: サンド](pokemon/370.md) | [427: ダブルスピン](moves/427.md) | {"order":"14","route":"egg"} | egg_moves_final.csv:3900 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [374: ズルッグ](pokemon/374.md) | [450: マグナムパンチ](moves/450.md) | {"order":"25","route":"egg"} | egg_moves_final.csv:3943 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [376: デリバード](pokemon/376.md) | [457: かっくう](moves/457.md) | {"order":"6","route":"egg"} | egg_moves_final.csv:3956 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [376: デリバード](pokemon/376.md) | [466: かくらんひこう](moves/466.md) | {"order":"7","route":"egg"} | egg_moves_final.csv:3957 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [376: デリバード](pokemon/376.md) | [447: つららパンチ](moves/447.md) | {"order":"18","route":"egg"} | egg_moves_final.csv:3968 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [378: テッシード](pokemon/378.md) | [467: いわころがり](moves/467.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3982 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [378: テッシード](pokemon/378.md) | [441: おいしげる](moves/441.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:3983 | True | &#91;"egg","level_up"&#93; | False |
| official_to_vega_legacy_preservation | [378: テッシード](pokemon/378.md) | [425: げきとつ](moves/425.md) | {"order":"4","route":"egg"} | egg_moves_final.csv:3985 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [378: テッシード](pokemon/378.md) | [481: ジオインパクト](moves/481.md) | {"order":"5","route":"egg"} | egg_moves_final.csv:3986 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [378: テッシード](pokemon/378.md) | [357: スターダスト](moves/357.md) | {"order":"8","route":"egg"} | egg_moves_final.csv:3989 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [378: テッシード](pokemon/378.md) | [361: メタルブラスト](moves/361.md) | {"order":"19","route":"egg"} | egg_moves_final.csv:4000 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [381: チュリネ](pokemon/381.md) | [428: おんち](moves/428.md) | {"order":"7","route":"egg"} | egg_moves_final.csv:4015 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [381: チュリネ](pokemon/381.md) | [452: きけんなどくそ](moves/452.md) | {"order":"9","route":"egg"} | egg_moves_final.csv:4017 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [381: チュリネ](pokemon/381.md) | [469: げんしのいぶき](moves/469.md) | {"order":"11","route":"egg"} | egg_moves_final.csv:4019 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [381: チュリネ](pokemon/381.md) | [463: さいみんはどう](moves/463.md) | {"order":"14","route":"egg"} | egg_moves_final.csv:4022 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [397: メグロコ](pokemon/397.md) | [470: ソウルバイト](moves/470.md) | {"order":"8","route":"egg"} | egg_moves_final.csv:4339 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [397: メグロコ](pokemon/397.md) | [355: グランボールダ](moves/355.md) | {"order":"9","route":"egg"} | egg_moves_final.csv:4340 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [397: メグロコ](pokemon/397.md) | [426: スピンテール](moves/426.md) | {"order":"14","route":"egg"} | egg_moves_final.csv:4345 | True | &#91;"egg"&#93; | False |
| official_to_vega_legacy_preservation | [397: メグロコ](pokemon/397.md) | [454: もぐる](moves/454.md) | {"order":"23","route":"egg"} | egg_moves_final.csv:4354 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [2: リーティン](pokemon/2.md) | [73: やどりぎのタネ](moves/73.md) | {"level":"28","order":"11","route":"level_up"} | level_up_final.csv:27 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [2: リーティン](pokemon/2.md) | [202: ギガドレイン](moves/202.md) | {"level":"30","order":"12","route":"level_up"} | level_up_final.csv:28 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [3: リーテイル](pokemon/3.md) | [202: ギガドレイン](moves/202.md) | {"level":"36","order":"17","route":"level_up"} | level_up_final.csv:51 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [3: リーテイル](pokemon/3.md) | [73: やどりぎのタネ](moves/73.md) | {"level":"38","order":"18","route":"level_up"} | level_up_final.csv:52 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [3: リーテイル](pokemon/3.md) | [397: ラスターカノン](moves/397.md) | {"level":"56","order":"22","route":"level_up"} | level_up_final.csv:56 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [4: ファマー](pokemon/4.md) | [261: おにび](moves/261.md) | {"level":"23","order":"9","route":"level_up"} | level_up_final.csv:67 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [5: ファイマー](pokemon/5.md) | [261: おにび](moves/261.md) | {"level":"28","order":"10","route":"level_up"} | level_up_final.csv:84 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [6: ファマイン](pokemon/6.md) | [515: ニトロチャージ](moves/515.md) | {"level":"28","order":"14","route":"level_up"} | level_up_final.csv:105 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [6: ファマイン](pokemon/6.md) | [53: かえんほうしゃ](moves/53.md) | {"level":"43","order":"19","route":"level_up"} | level_up_final.csv:110 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [6: ファマイン](pokemon/6.md) | [261: おにび](moves/261.md) | {"level":"48","order":"20","route":"level_up"} | level_up_final.csv:111 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [6: ファマイン](pokemon/6.md) | [370: つじぎり](moves/370.md) | {"level":"56","order":"23","route":"level_up"} | level_up_final.csv:114 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [7: アクタシ](pokemon/7.md) | [411: アクアジェット](moves/411.md) | {"level":"13","order":"6","route":"level_up"} | level_up_final.csv:122 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [7: アクタシ](pokemon/7.md) | [352: みずのはどう](moves/352.md) | {"level":"19","order":"8","route":"level_up"} | level_up_final.csv:124 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [8: レクオレ](pokemon/8.md) | [667: アクアブレイク](moves/667.md) | {"level":"30","order":"11","route":"level_up"} | level_up_final.csv:143 | True | &#91;"level_up","machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [8: レクオレ](pokemon/8.md) | [57: なみのり](moves/57.md) | {"level":"30","order":"12","route":"level_up"} | level_up_final.csv:144 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [9: タテボーシ](pokemon/9.md) | [240: あまごい](moves/240.md) | {"level":"38","order":"18","route":"level_up"} | level_up_final.csv:168 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [9: タテボーシ](pokemon/9.md) | [579: サイコショック](moves/579.md) | {"level":"48","order":"20","route":"level_up"} | level_up_final.csv:170 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [9: タテボーシ](pokemon/9.md) | [56: ハイドロポンプ](moves/56.md) | {"level":"52","order":"22","route":"level_up"} | level_up_final.csv:172 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [9: タテボーシ](pokemon/9.md) | [347: めいそう](moves/347.md) | {"level":"56","order":"23","route":"level_up"} | level_up_final.csv:173 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [21: フロン](pokemon/21.md) | [73: やどりぎのタネ](moves/73.md) | {"level":"16","order":"6","route":"level_up"} | level_up_final.csv:376 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [21: フロン](pokemon/21.md) | [72: メガドレイン](moves/72.md) | {"level":"18","order":"7","route":"level_up"} | level_up_final.csv:377 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [22: フロルル](pokemon/22.md) | [73: やどりぎのタネ](moves/73.md) | {"level":"28","order":"10","route":"level_up"} | level_up_final.csv:395 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [22: フロルル](pokemon/22.md) | [202: ギガドレイン](moves/202.md) | {"level":"30","order":"12","route":"level_up"} | level_up_final.csv:397 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [23: フローリア](pokemon/23.md) | [382: エナジーボール](moves/382.md) | {"level":"36","order":"14","route":"level_up"} | level_up_final.csv:416 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [23: フローリア](pokemon/23.md) | [73: やどりぎのタネ](moves/73.md) | {"level":"38","order":"16","route":"level_up"} | level_up_final.csv:418 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [23: フローリア](pokemon/23.md) | [579: サイコショック](moves/579.md) | {"level":"48","order":"18","route":"level_up"} | level_up_final.csv:420 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [23: フローリア](pokemon/23.md) | [347: めいそう](moves/347.md) | {"level":"56","order":"20","route":"level_up"} | level_up_final.csv:422 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [27: ゴリチュウ](pokemon/27.md) | [86: でんじは](moves/86.md) | {"level":"38","order":"12","route":"level_up"} | level_up_final.csv:467 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [27: ゴリチュウ](pokemon/27.md) | [363: インファイト](moves/363.md) | {"level":"56","order":"16","route":"level_up"} | level_up_final.csv:471 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [37: ララベリー](pokemon/37.md) | [73: やどりぎのタネ](moves/73.md) | {"level":"16","order":"7","route":"level_up"} | level_up_final.csv:625 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [38: セラーナ](pokemon/38.md) | [382: エナジーボール](moves/382.md) | {"level":"36","order":"15","route":"level_up"} | level_up_final.csv:649 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [38: セラーナ](pokemon/38.md) | [73: やどりぎのタネ](moves/73.md) | {"level":"38","order":"16","route":"level_up"} | level_up_final.csv:650 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [38: セラーナ](pokemon/38.md) | [579: サイコショック](moves/579.md) | {"level":"48","order":"19","route":"level_up"} | level_up_final.csv:653 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [38: セラーナ](pokemon/38.md) | [347: めいそう](moves/347.md) | {"level":"56","order":"22","route":"level_up"} | level_up_final.csv:656 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [43: マホース](pokemon/43.md) | [29: ずつき](moves/29.md) | {"level":"16","order":"5","route":"level_up"} | level_up_final.csv:735 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [43: マホース](pokemon/43.md) | [227: アンコール](moves/227.md) | {"level":"16","order":"6","route":"level_up"} | level_up_final.csv:736 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [44: ペガーン](pokemon/44.md) | [227: アンコール](moves/227.md) | {"level":"28","order":"7","route":"level_up"} | level_up_final.csv:753 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [44: ペガーン](pokemon/44.md) | [34: のしかかり](moves/34.md) | {"level":"30","order":"8","route":"level_up"} | level_up_final.csv:754 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [44: ペガーン](pokemon/44.md) | [65: ドリルくちばし](moves/65.md) | {"level":"36","order":"10","route":"level_up"} | level_up_final.csv:756 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [44: ペガーン](pokemon/44.md) | [554: おいかぜ](moves/554.md) | {"level":"44","order":"11","route":"level_up"} | level_up_final.csv:757 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [45: ユニサス](pokemon/45.md) | [227: アンコール](moves/227.md) | {"level":"38","order":"8","route":"level_up"} | level_up_final.csv:768 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [45: ユニサス](pokemon/45.md) | [38: すてみタックル](moves/38.md) | {"level":"49","order":"10","route":"level_up"} | level_up_final.csv:770 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [45: ユニサス](pokemon/45.md) | [383: ブレイブバード](moves/383.md) | {"level":"50","order":"11","route":"level_up"} | level_up_final.csv:771 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [45: ユニサス](pokemon/45.md) | [554: おいかぜ](moves/554.md) | {"level":"56","order":"13","route":"level_up"} | level_up_final.csv:773 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [50: ライノス](pokemon/50.md) | [189: どろかけ](moves/189.md) | {"level":"8","order":"4","route":"level_up"} | level_up_final.csv:839 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [50: ライノス](pokemon/50.md) | [532: ドラゴンテール](moves/532.md) | {"level":"24","order":"9","route":"level_up"} | level_up_final.csv:844 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [50: ライノス](pokemon/50.md) | [349: りゅうのまい](moves/349.md) | {"level":"50","order":"16","route":"level_up"} | level_up_final.csv:851 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [51: メタゲラス](pokemon/51.md) | [89: じしん](moves/89.md) | {"level":"48","order":"15","route":"level_up"} | level_up_final.csv:867 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [51: メタゲラス](pokemon/51.md) | [603: ヘビーボンバー](moves/603.md) | {"level":"50","order":"17","route":"level_up"} | level_up_final.csv:869 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [53: ディザソル](pokemon/53.md) | [282: はたきおとす](moves/282.md) | {"level":"28","order":"14","route":"level_up"} | level_up_final.csv:903 | True | &#91;"level_up","machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [55: フォリキー](pokemon/55.md) | [579: サイコショック](moves/579.md) | {"level":"28","order":"13","route":"level_up"} | level_up_final.csv:945 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [56: バーニン](pokemon/56.md) | [579: サイコショック](moves/579.md) | {"level":"28","order":"10","route":"level_up"} | level_up_final.csv:962 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [56: バーニン](pokemon/56.md) | [347: めいそう](moves/347.md) | {"level":"50","order":"16","route":"level_up"} | level_up_final.csv:968 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [56: バーニン](pokemon/56.md) | [261: おにび](moves/261.md) | {"level":"56","order":"18","route":"level_up"} | level_up_final.csv:970 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [57: ファントマ](pokemon/57.md) | [579: サイコショック](moves/579.md) | {"level":"28","order":"6","route":"level_up"} | level_up_final.csv:976 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [57: ファントマ](pokemon/57.md) | [247: シャドーボール](moves/247.md) | {"level":"48","order":"12","route":"level_up"} | level_up_final.csv:982 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [57: ファントマ](pokemon/57.md) | [347: めいそう](moves/347.md) | {"level":"50","order":"13","route":"level_up"} | level_up_final.csv:983 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [68: テディ](pokemon/68.md) | [29: ずつき](moves/29.md) | {"level":"16","order":"7","route":"level_up"} | level_up_final.csv:1177 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [68: テディ](pokemon/68.md) | [227: アンコール](moves/227.md) | {"level":"16","order":"8","route":"level_up"} | level_up_final.csv:1178 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [69: ググズリー](pokemon/69.md) | [227: アンコール](moves/227.md) | {"level":"28","order":"13","route":"level_up"} | level_up_final.csv:1201 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [69: ググズリー](pokemon/69.md) | [34: のしかかり](moves/34.md) | {"level":"30","order":"14","route":"level_up"} | level_up_final.csv:1202 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [69: ググズリー](pokemon/69.md) | [370: つじぎり](moves/370.md) | {"level":"36","order":"18","route":"level_up"} | level_up_final.csv:1206 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [70: ハンタマ](pokemon/70.md) | [282: はたきおとす](moves/282.md) | {"level":"28","order":"9","route":"level_up"} | level_up_final.csv:1220 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [70: ハンタマ](pokemon/70.md) | [269: ちょうはつ](moves/269.md) | {"level":"38","order":"12","route":"level_up"} | level_up_final.csv:1223 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [70: ハンタマ](pokemon/70.md) | [796: ポルターガイスト](moves/796.md) | {"level":"52","order":"16","route":"level_up"} | level_up_final.csv:1227 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [70: ハンタマ](pokemon/70.md) | [261: おにび](moves/261.md) | {"level":"56","order":"18","route":"level_up"} | level_up_final.csv:1229 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [81: ダンゴロウ](pokemon/81.md) | [411: アクアジェット](moves/411.md) | {"level":"13","order":"6","route":"level_up"} | level_up_final.csv:1435 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [81: ダンゴロウ](pokemon/81.md) | [352: みずのはどう](moves/352.md) | {"level":"19","order":"9","route":"level_up"} | level_up_final.csv:1438 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [82: マルマジロ](pokemon/82.md) | [127: たきのぼり](moves/127.md) | {"level":"32","order":"15","route":"level_up"} | level_up_final.csv:1461 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [82: マルマジロ](pokemon/82.md) | [240: あまごい](moves/240.md) | {"level":"38","order":"17","route":"level_up"} | level_up_final.csv:1463 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [82: マルマジロ](pokemon/82.md) | [603: ヘビーボンバー](moves/603.md) | {"level":"50","order":"20","route":"level_up"} | level_up_final.csv:1466 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [83: アロフィー](pokemon/83.md) | [240: あまごい](moves/240.md) | {"level":"26","order":"8","route":"level_up"} | level_up_final.csv:1477 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [84: リーフィス](pokemon/84.md) | [240: あまごい](moves/240.md) | {"level":"38","order":"14","route":"level_up"} | level_up_final.csv:1498 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [84: リーフィス](pokemon/84.md) | [382: エナジーボール](moves/382.md) | {"level":"48","order":"18","route":"level_up"} | level_up_final.csv:1502 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [84: リーフィス](pokemon/84.md) | [56: ハイドロポンプ](moves/56.md) | {"level":"52","order":"19","route":"level_up"} | level_up_final.csv:1503 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [87: ユカリア](pokemon/87.md) | [93: ねんりき](moves/93.md) | {"level":"8","order":"4","route":"level_up"} | level_up_final.csv:1550 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [87: ユカリア](pokemon/87.md) | [347: めいそう](moves/347.md) | {"level":"50","order":"14","route":"level_up"} | level_up_final.csv:1560 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [88: ネクロシア](pokemon/88.md) | [579: サイコショック](moves/579.md) | {"level":"28","order":"12","route":"level_up"} | level_up_final.csv:1574 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [88: ネクロシア](pokemon/88.md) | [247: シャドーボール](moves/247.md) | {"level":"48","order":"18","route":"level_up"} | level_up_final.csv:1580 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [88: ネクロシア](pokemon/88.md) | [347: めいそう](moves/347.md) | {"level":"50","order":"20","route":"level_up"} | level_up_final.csv:1582 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [88: ネクロシア](pokemon/88.md) | [261: おにび](moves/261.md) | {"level":"56","order":"22","route":"level_up"} | level_up_final.csv:1584 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [89: カプリン](pokemon/89.md) | [93: ねんりき](moves/93.md) | {"level":"8","order":"4","route":"level_up"} | level_up_final.csv:1589 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [89: カプリン](pokemon/89.md) | [347: めいそう](moves/347.md) | {"level":"50","order":"13","route":"level_up"} | level_up_final.csv:1598 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [90: ゴートン](pokemon/90.md) | [94: サイコキネシス](moves/94.md) | {"level":"30","order":"10","route":"level_up"} | level_up_final.csv:1609 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [90: ゴートン](pokemon/90.md) | [347: めいそう](moves/347.md) | {"level":"50","order":"14","route":"level_up"} | level_up_final.csv:1613 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [91: バフォット](pokemon/91.md) | [282: はたきおとす](moves/282.md) | {"level":"28","order":"11","route":"level_up"} | level_up_final.csv:1626 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [91: バフォット](pokemon/91.md) | [269: ちょうはつ](moves/269.md) | {"level":"38","order":"15","route":"level_up"} | level_up_final.csv:1630 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [91: バフォット](pokemon/91.md) | [675: サイコファング](moves/675.md) | {"level":"48","order":"17","route":"level_up"} | level_up_final.csv:1632 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [91: バフォット](pokemon/91.md) | [347: めいそう](moves/347.md) | {"level":"56","order":"19","route":"level_up"} | level_up_final.csv:1634 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [95: ゴルドー](pokemon/95.md) | [65: ドリルくちばし](moves/65.md) | {"level":"30","order":"11","route":"level_up"} | level_up_final.csv:1699 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [95: ゴルドー](pokemon/95.md) | [405: アイアンヘッド](moves/405.md) | {"level":"36","order":"14","route":"level_up"} | level_up_final.csv:1702 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [95: ゴルドー](pokemon/95.md) | [554: おいかぜ](moves/554.md) | {"level":"38","order":"15","route":"level_up"} | level_up_final.csv:1703 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [95: ゴルドー](pokemon/95.md) | [334: てっぺき](moves/334.md) | {"level":"50","order":"19","route":"level_up"} | level_up_final.csv:1707 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [96: フィニクス](pokemon/96.md) | [261: おにび](moves/261.md) | {"level":"38","order":"15","route":"level_up"} | level_up_final.csv:1723 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [96: フィニクス](pokemon/96.md) | [518: ぼうふう](moves/518.md) | {"level":"50","order":"19","route":"level_up"} | level_up_final.csv:1727 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [96: フィニクス](pokemon/96.md) | [126: だいもんじ](moves/126.md) | {"level":"54","order":"21","route":"level_up"} | level_up_final.csv:1729 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [96: フィニクス](pokemon/96.md) | [554: おいかぜ](moves/554.md) | {"level":"56","order":"22","route":"level_up"} | level_up_final.csv:1730 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [97: クロッチ](pokemon/97.md) | [29: ずつき](moves/29.md) | {"level":"16","order":"7","route":"level_up"} | level_up_final.csv:1739 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [97: クロッチ](pokemon/97.md) | [227: アンコール](moves/227.md) | {"level":"16","order":"8","route":"level_up"} | level_up_final.csv:1740 | True | &#91;"egg","level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [97: クロッチ](pokemon/97.md) | [44: かみつく](moves/44.md) | {"level":"24","order":"11","route":"level_up"} | level_up_final.csv:1743 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [97: クロッチ](pokemon/97.md) | [269: ちょうはつ](moves/269.md) | {"level":"32","order":"14","route":"level_up"} | level_up_final.csv:1746 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [98: コクジャク](pokemon/98.md) | [227: アンコール](moves/227.md) | {"level":"28","order":"13","route":"level_up"} | level_up_final.csv:1764 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [98: コクジャク](pokemon/98.md) | [34: のしかかり](moves/34.md) | {"level":"30","order":"15","route":"level_up"} | level_up_final.csv:1766 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [98: コクジャク](pokemon/98.md) | [65: ドリルくちばし](moves/65.md) | {"level":"36","order":"17","route":"level_up"} | level_up_final.csv:1768 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [98: コクジャク](pokemon/98.md) | [554: おいかぜ](moves/554.md) | {"level":"44","order":"19","route":"level_up"} | level_up_final.csv:1770 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [99: シャミネ](pokemon/99.md) | [227: アンコール](moves/227.md) | {"level":"38","order":"13","route":"level_up"} | level_up_final.csv:1787 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [99: シャミネ](pokemon/99.md) | [38: すてみタックル](moves/38.md) | {"level":"49","order":"16","route":"level_up"} | level_up_final.csv:1790 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [99: シャミネ](pokemon/99.md) | [383: ブレイブバード](moves/383.md) | {"level":"50","order":"17","route":"level_up"} | level_up_final.csv:1791 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [99: シャミネ](pokemon/99.md) | [554: おいかぜ](moves/554.md) | {"level":"56","order":"20","route":"level_up"} | level_up_final.csv:1794 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [100: コーシャン](pokemon/100.md) | [188: ヘドロばくだん](moves/188.md) | {"level":"36","order":"13","route":"level_up"} | level_up_final.csv:1807 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [100: コーシャン](pokemon/100.md) | [92: どくどく](moves/92.md) | {"level":"38","order":"15","route":"level_up"} | level_up_final.csv:1809 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [100: コーシャン](pokemon/100.md) | [551: どくびし](moves/551.md) | {"level":"48","order":"17","route":"level_up"} | level_up_final.csv:1811 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [101: プラズン](pokemon/101.md) | [488: アシッドボム](moves/488.md) | {"level":"12","order":"5","route":"level_up"} | level_up_final.csv:1820 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [101: プラズン](pokemon/101.md) | [92: どくどく](moves/92.md) | {"level":"26","order":"9","route":"level_up"} | level_up_final.csv:1824 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [102: ボルトック](pokemon/102.md) | [505: ヘドロウェーブ](moves/505.md) | {"level":"38","order":"8","route":"level_up"} | level_up_final.csv:1840 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [102: ボルトック](pokemon/102.md) | [92: どくどく](moves/92.md) | {"level":"38","order":"9","route":"level_up"} | level_up_final.csv:1841 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [102: ボルトック](pokemon/102.md) | [86: でんじは](moves/86.md) | {"level":"56","order":"12","route":"level_up"} | level_up_final.csv:1844 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [102: ボルトック](pokemon/102.md) | [87: かみなり](moves/87.md) | {"level":"58","order":"14","route":"level_up"} | level_up_final.csv:1846 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [104: テペトラー](pokemon/104.md) | [56: ハイドロポンプ](moves/56.md) | {"level":"52","order":"16","route":"level_up"} | level_up_final.csv:1878 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [104: テペトラー](pokemon/104.md) | [126: だいもんじ](moves/126.md) | {"level":"54","order":"17","route":"level_up"} | level_up_final.csv:1879 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [104: テペトラー](pokemon/104.md) | [261: おにび](moves/261.md) | {"level":"56","order":"19","route":"level_up"} | level_up_final.csv:1881 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [105: ロップル](pokemon/105.md) | [667: アクアブレイク](moves/667.md) | {"level":"38","order":"11","route":"level_up"} | level_up_final.csv:1894 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [105: ロップル](pokemon/105.md) | [57: なみのり](moves/57.md) | {"level":"38","order":"12","route":"level_up"} | level_up_final.csv:1895 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [105: ロップル](pokemon/105.md) | [240: あまごい](moves/240.md) | {"level":"48","order":"15","route":"level_up"} | level_up_final.csv:1898 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [105: ロップル](pokemon/105.md) | [65: ドリルくちばし](moves/65.md) | {"level":"56","order":"18","route":"level_up"} | level_up_final.csv:1901 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [106: オタクン](pokemon/106.md) | [93: ねんりき](moves/93.md) | {"level":"8","order":"5","route":"level_up"} | level_up_final.csv:1908 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [106: オタクン](pokemon/106.md) | [347: めいそう](moves/347.md) | {"level":"50","order":"15","route":"level_up"} | level_up_final.csv:1918 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [107: ネラー](pokemon/107.md) | [94: サイコキネシス](moves/94.md) | {"level":"30","order":"10","route":"level_up"} | level_up_final.csv:1930 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [107: ネラー](pokemon/107.md) | [347: めいそう](moves/347.md) | {"level":"50","order":"15","route":"level_up"} | level_up_final.csv:1935 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [108: ニートン](pokemon/108.md) | [579: サイコショック](moves/579.md) | {"level":"28","order":"9","route":"level_up"} | level_up_final.csv:1946 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [108: ニートン](pokemon/108.md) | [347: めいそう](moves/347.md) | {"level":"50","order":"15","route":"level_up"} | level_up_final.csv:1952 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [111: ハクタクン](pokemon/111.md) | [201: すなあらし](moves/201.md) | {"level":"38","order":"13","route":"level_up"} | level_up_final.csv:2011 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [111: ハクタクン](pokemon/111.md) | [89: じしん](moves/89.md) | {"level":"48","order":"16","route":"level_up"} | level_up_final.csv:2014 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [121: スミロドン](pokemon/121.md) | [1034: ゆきげしき](moves/1034.md) | {"level":"48","order":"13","route":"level_up"} | level_up_final.csv:2188 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [121: スミロドン](pokemon/121.md) | [59: ふぶき](moves/59.md) | {"level":"53","order":"16","route":"level_up"} | level_up_final.csv:2191 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [122: マカドゥス](pokemon/122.md) | [550: ステルスロック](moves/550.md) | {"level":"38","order":"13","route":"level_up"} | level_up_final.csv:2204 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [122: マカドゥス](pokemon/122.md) | [787: メテオビーム](moves/787.md) | {"level":"45","order":"16","route":"level_up"} | level_up_final.csv:2207 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [122: マカドゥス](pokemon/122.md) | [87: かみなり](moves/87.md) | {"level":"58","order":"19","route":"level_up"} | level_up_final.csv:2210 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [133: タツゴン](pokemon/133.md) | [532: ドラゴンテール](moves/532.md) | {"level":"18","order":"6","route":"level_up"} | level_up_final.csv:2384 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [134: ラグーン](pokemon/134.md) | [337: ドラゴンクロー](moves/337.md) | {"level":"30","order":"10","route":"level_up"} | level_up_final.csv:2401 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [134: ラグーン](pokemon/134.md) | [240: あまごい](moves/240.md) | {"level":"44","order":"13","route":"level_up"} | level_up_final.csv:2404 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [134: ラグーン](pokemon/134.md) | [667: アクアブレイク](moves/667.md) | {"level":"45","order":"14","route":"level_up"} | level_up_final.csv:2405 | True | &#91;"level_up","machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [135: ドラドーン](pokemon/135.md) | [667: アクアブレイク](moves/667.md) | {"level":"56","order":"16","route":"level_up"} | level_up_final.csv:2424 | True | &#91;"level_up","machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [142: ライラプス](pokemon/142.md) | [1014: アイススピナー](moves/1014.md) | {"level":"38","order":"7","route":"level_up"} | level_up_final.csv:2535 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [142: ライラプス](pokemon/142.md) | [58: れいとうビーム](moves/58.md) | {"level":"38","order":"8","route":"level_up"} | level_up_final.csv:2536 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [142: ライラプス](pokemon/142.md) | [1034: ゆきげしき](moves/1034.md) | {"level":"50","order":"11","route":"level_up"} | level_up_final.csv:2539 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [142: ライラプス](pokemon/142.md) | [370: つじぎり](moves/370.md) | {"level":"56","order":"12","route":"level_up"} | level_up_final.csv:2540 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [143: ガニメデ](pokemon/143.md) | [1034: ゆきげしき](moves/1034.md) | {"level":"48","order":"8","route":"level_up"} | level_up_final.csv:2554 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [143: ガニメデ](pokemon/143.md) | [59: ふぶき](moves/59.md) | {"level":"53","order":"10","route":"level_up"} | level_up_final.csv:2556 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [143: ガニメデ](pokemon/143.md) | [86: でんじは](moves/86.md) | {"level":"56","order":"11","route":"level_up"} | level_up_final.csv:2557 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [143: ガニメデ](pokemon/143.md) | [87: かみなり](moves/87.md) | {"level":"58","order":"13","route":"level_up"} | level_up_final.csv:2559 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [144: ネメア](pokemon/144.md) | [515: ニトロチャージ](moves/515.md) | {"level":"28","order":"6","route":"level_up"} | level_up_final.csv:2570 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [144: ネメア](pokemon/144.md) | [53: かえんほうしゃ](moves/53.md) | {"level":"43","order":"9","route":"level_up"} | level_up_final.csv:2573 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [144: ネメア](pokemon/144.md) | [261: おにび](moves/261.md) | {"level":"48","order":"10","route":"level_up"} | level_up_final.csv:2574 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [144: ネメア](pokemon/144.md) | [370: つじぎり](moves/370.md) | {"level":"56","order":"12","route":"level_up"} | level_up_final.csv:2576 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [161: バジール](pokemon/161.md) | [488: アシッドボム](moves/488.md) | {"level":"24","order":"9","route":"level_up"} | level_up_final.csv:2882 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [161: バジール](pokemon/161.md) | [92: どくどく](moves/92.md) | {"level":"33","order":"13","route":"level_up"} | level_up_final.csv:2886 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [162: バジルス](pokemon/162.md) | [188: ヘドロばくだん](moves/188.md) | {"level":"36","order":"13","route":"level_up"} | level_up_final.csv:2902 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [162: バジルス](pokemon/162.md) | [92: どくどく](moves/92.md) | {"level":"44","order":"16","route":"level_up"} | level_up_final.csv:2905 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [163: バジリール](pokemon/163.md) | [202: ギガドレイン](moves/202.md) | {"level":"36","order":"17","route":"level_up"} | level_up_final.csv:2924 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [163: バジリール](pokemon/163.md) | [235: こうごうせい](moves/235.md) | {"level":"48","order":"20","route":"level_up"} | level_up_final.csv:2927 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [163: バジリール](pokemon/163.md) | [188: ヘドロばくだん](moves/188.md) | {"level":"56","order":"22","route":"level_up"} | level_up_final.csv:2929 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [164: コマシシ](pokemon/164.md) | [261: おにび](moves/261.md) | {"level":"23","order":"8","route":"level_up"} | level_up_final.csv:2938 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [165: コマレオ](pokemon/165.md) | [261: おにび](moves/261.md) | {"level":"28","order":"10","route":"level_up"} | level_up_final.csv:2954 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [166: コマレオン](pokemon/166.md) | [261: おにび](moves/261.md) | {"level":"38","order":"16","route":"level_up"} | level_up_final.csv:2976 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [166: コマレオン](pokemon/166.md) | [363: インファイト](moves/363.md) | {"level":"56","order":"20","route":"level_up"} | level_up_final.csv:2980 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [166: コマレオン](pokemon/166.md) | [339: ビルドアップ](moves/339.md) | {"level":"56","order":"21","route":"level_up"} | level_up_final.csv:2981 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [168: ボウソウオ](pokemon/168.md) | [667: アクアブレイク](moves/667.md) | {"level":"30","order":"10","route":"level_up"} | level_up_final.csv:3005 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [168: ボウソウオ](pokemon/168.md) | [57: なみのり](moves/57.md) | {"level":"30","order":"11","route":"level_up"} | level_up_final.csv:3006 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [169: バクソウオ](pokemon/169.md) | [240: あまごい](moves/240.md) | {"level":"38","order":"15","route":"level_up"} | level_up_final.csv:3027 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [169: バクソウオ](pokemon/169.md) | [579: サイコショック](moves/579.md) | {"level":"48","order":"18","route":"level_up"} | level_up_final.csv:3030 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [169: バクソウオ](pokemon/169.md) | [56: ハイドロポンプ](moves/56.md) | {"level":"52","order":"19","route":"level_up"} | level_up_final.csv:3031 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [169: バクソウオ](pokemon/169.md) | [347: めいそう](moves/347.md) | {"level":"56","order":"21","route":"level_up"} | level_up_final.csv:3033 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [170: チェキラ](pokemon/170.md) | [29: ずつき](moves/29.md) | {"level":"16","order":"7","route":"level_up"} | level_up_final.csv:3042 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [170: チェキラ](pokemon/170.md) | [227: アンコール](moves/227.md) | {"level":"16","order":"8","route":"level_up"} | level_up_final.csv:3043 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [171: チェキッド](pokemon/171.md) | [227: アンコール](moves/227.md) | {"level":"28","order":"10","route":"level_up"} | level_up_final.csv:3061 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [172: チェキラス](pokemon/172.md) | [227: アンコール](moves/227.md) | {"level":"38","order":"12","route":"level_up"} | level_up_final.csv:3080 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [172: チェキラス](pokemon/172.md) | [38: すてみタックル](moves/38.md) | {"level":"49","order":"15","route":"level_up"} | level_up_final.csv:3083 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [173: リバード](pokemon/173.md) | [29: ずつき](moves/29.md) | {"level":"16","order":"5","route":"level_up"} | level_up_final.csv:3091 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [173: リバード](pokemon/173.md) | [227: アンコール](moves/227.md) | {"level":"16","order":"6","route":"level_up"} | level_up_final.csv:3092 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [173: リバード](pokemon/173.md) | [17: つばさでうつ](moves/17.md) | {"level":"24","order":"9","route":"level_up"} | level_up_final.csv:3095 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [173: リバード](pokemon/173.md) | [554: おいかぜ](moves/554.md) | {"level":"41","order":"14","route":"level_up"} | level_up_final.csv:3100 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [174: ララミンゴ](pokemon/174.md) | [65: ドリルくちばし](moves/65.md) | {"level":"35","order":"10","route":"level_up"} | level_up_final.csv:3114 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [174: ララミンゴ](pokemon/174.md) | [373: エアスラッシュ](moves/373.md) | {"level":"41","order":"12","route":"level_up"} | level_up_final.csv:3116 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [174: ララミンゴ](pokemon/174.md) | [554: おいかぜ](moves/554.md) | {"level":"48","order":"14","route":"level_up"} | level_up_final.csv:3118 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [174: ララミンゴ](pokemon/174.md) | [667: アクアブレイク](moves/667.md) | {"level":"56","order":"16","route":"level_up"} | level_up_final.csv:3120 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [176: パチリック](pokemon/176.md) | [240: あまごい](moves/240.md) | {"level":"38","order":"15","route":"level_up"} | level_up_final.csv:3153 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [176: パチリック](pokemon/176.md) | [56: ハイドロポンプ](moves/56.md) | {"level":"52","order":"18","route":"level_up"} | level_up_final.csv:3156 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [177: パンプリー](pokemon/177.md) | [261: おにび](moves/261.md) | {"level":"23","order":"8","route":"level_up"} | level_up_final.csv:3166 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [178: パンプッチ](pokemon/178.md) | [526: たたりめ](moves/526.md) | {"level":"28","order":"12","route":"level_up"} | level_up_final.csv:3185 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [178: パンプッチ](pokemon/178.md) | [261: おにび](moves/261.md) | {"level":"38","order":"14","route":"level_up"} | level_up_final.csv:3187 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [178: パンプッチ](pokemon/178.md) | [194: みちづれ](moves/194.md) | {"level":"50","order":"17","route":"level_up"} | level_up_final.csv:3190 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [178: パンプッチ](pokemon/178.md) | [202: ギガドレイン](moves/202.md) | {"level":"56","order":"19","route":"level_up"} | level_up_final.csv:3192 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [180: ルナバイン](pokemon/180.md) | [579: サイコショック](moves/579.md) | {"level":"28","order":"11","route":"level_up"} | level_up_final.csv:3219 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [180: ルナバイン](pokemon/180.md) | [606: イカサマ](moves/606.md) | {"level":"48","order":"17","route":"level_up"} | level_up_final.csv:3225 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [180: ルナバイン](pokemon/180.md) | [269: ちょうはつ](moves/269.md) | {"level":"56","order":"20","route":"level_up"} | level_up_final.csv:3228 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [181: ウソギー](pokemon/181.md) | [411: アクアジェット](moves/411.md) | {"level":"13","order":"5","route":"level_up"} | level_up_final.csv:3235 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [181: ウソギー](pokemon/181.md) | [352: みずのはどう](moves/352.md) | {"level":"19","order":"7","route":"level_up"} | level_up_final.csv:3237 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [182: ウソドロ](pokemon/182.md) | [127: たきのぼり](moves/127.md) | {"level":"32","order":"12","route":"level_up"} | level_up_final.csv:3258 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [182: ウソドロ](pokemon/182.md) | [240: あまごい](moves/240.md) | {"level":"38","order":"14","route":"level_up"} | level_up_final.csv:3260 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [182: ウソドロ](pokemon/182.md) | [282: はたきおとす](moves/282.md) | {"level":"48","order":"17","route":"level_up"} | level_up_final.csv:3263 | True | &#91;"level_up","machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [186: レジュリア](pokemon/186.md) | [1034: ゆきげしき](moves/1034.md) | {"level":"48","order":"17","route":"level_up"} | level_up_final.csv:3326 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [187: タダヌキ](pokemon/187.md) | [29: ずつき](moves/29.md) | {"level":"16","order":"6","route":"level_up"} | level_up_final.csv:3335 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [187: タダヌキ](pokemon/187.md) | [227: アンコール](moves/227.md) | {"level":"16","order":"7","route":"level_up"} | level_up_final.csv:3336 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [188: オオムジナ](pokemon/188.md) | [227: アンコール](moves/227.md) | {"level":"38","order":"13","route":"level_up"} | level_up_final.csv:3356 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [188: オオムジナ](pokemon/188.md) | [38: すてみタックル](moves/38.md) | {"level":"49","order":"16","route":"level_up"} | level_up_final.csv:3359 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [189: ポコキング](pokemon/189.md) | [227: アンコール](moves/227.md) | {"level":"38","order":"15","route":"level_up"} | level_up_final.csv:3375 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [189: ポコキング](pokemon/189.md) | [38: すてみタックル](moves/38.md) | {"level":"49","order":"17","route":"level_up"} | level_up_final.csv:3377 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [190: アスイーツ](pokemon/190.md) | [1034: ゆきげしき](moves/1034.md) | {"level":"48","order":"14","route":"level_up"} | level_up_final.csv:3393 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [191: コユキムシ](pokemon/191.md) | [196: こごえるかぜ](moves/196.md) | {"level":"13","order":"6","route":"level_up"} | level_up_final.csv:3402 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [191: コユキムシ](pokemon/191.md) | [1034: ゆきげしき](moves/1034.md) | {"level":"26","order":"10","route":"level_up"} | level_up_final.csv:3406 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [192: ユキタテハ](pokemon/192.md) | [1034: ゆきげしき](moves/1034.md) | {"level":"48","order":"16","route":"level_up"} | level_up_final.csv:3428 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [192: ユキタテハ](pokemon/192.md) | [672: かふんだんご](moves/672.md) | {"level":"48","order":"17","route":"level_up"} | level_up_final.csv:3429 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [192: ユキタテハ](pokemon/192.md) | [562: ねばねばネット](moves/562.md) | {"level":"56","order":"19","route":"level_up"} | level_up_final.csv:3431 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [194: オオペラー](pokemon/194.md) | [65: ドリルくちばし](moves/65.md) | {"level":"35","order":"16","route":"level_up"} | level_up_final.csv:3468 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [194: オオペラー](pokemon/194.md) | [373: エアスラッシュ](moves/373.md) | {"level":"41","order":"19","route":"level_up"} | level_up_final.csv:3471 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [194: オオペラー](pokemon/194.md) | [554: おいかぜ](moves/554.md) | {"level":"48","order":"22","route":"level_up"} | level_up_final.csv:3474 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [195: オリバー](pokemon/195.md) | [579: サイコショック](moves/579.md) | {"level":"28","order":"8","route":"level_up"} | level_up_final.csv:3484 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [195: オリバー](pokemon/195.md) | [347: めいそう](moves/347.md) | {"level":"50","order":"13","route":"level_up"} | level_up_final.csv:3489 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [196: ランペルン](pokemon/196.md) | [247: シャドーボール](moves/247.md) | {"level":"38","order":"10","route":"level_up"} | level_up_final.csv:3502 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [196: ランペルン](pokemon/196.md) | [261: おにび](moves/261.md) | {"level":"38","order":"11","route":"level_up"} | level_up_final.csv:3503 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [196: ランペルン](pokemon/196.md) | [579: サイコショック](moves/579.md) | {"level":"48","order":"14","route":"level_up"} | level_up_final.csv:3506 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [196: ランペルン](pokemon/196.md) | [347: めいそう](moves/347.md) | {"level":"56","order":"16","route":"level_up"} | level_up_final.csv:3508 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [197: キーボン](pokemon/197.md) | [247: シャドーボール](moves/247.md) | {"level":"38","order":"10","route":"level_up"} | level_up_final.csv:3520 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [197: キーボン](pokemon/197.md) | [261: おにび](moves/261.md) | {"level":"38","order":"11","route":"level_up"} | level_up_final.csv:3521 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [200: レディバル](pokemon/200.md) | [562: ねばねばネット](moves/562.md) | {"level":"38","order":"20","route":"level_up"} | level_up_final.csv:3584 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [200: レディバル](pokemon/200.md) | [224: メガホーン](moves/224.md) | {"level":"45","order":"22","route":"level_up"} | level_up_final.csv:3586 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [200: レディバル](pokemon/200.md) | [339: ビルドアップ](moves/339.md) | {"level":"56","order":"24","route":"level_up"} | level_up_final.csv:3588 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [202: ケンタル](pokemon/202.md) | [227: アンコール](moves/227.md) | {"level":"38","order":"11","route":"level_up"} | level_up_final.csv:3605 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [206: アスリスク](pokemon/206.md) | [247: シャドーボール](moves/247.md) | {"level":"38","order":"14","route":"level_up"} | level_up_final.csv:3679 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [206: アスリスク](pokemon/206.md) | [261: おにび](moves/261.md) | {"level":"38","order":"15","route":"level_up"} | level_up_final.csv:3680 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [207: プラネム](pokemon/207.md) | [579: サイコショック](moves/579.md) | {"level":"28","order":"6","route":"level_up"} | level_up_final.csv:3690 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [207: プラネム](pokemon/207.md) | [347: めいそう](moves/347.md) | {"level":"50","order":"10","route":"level_up"} | level_up_final.csv:3694 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [208: モドラ](pokemon/208.md) | [532: ドラゴンテール](moves/532.md) | {"level":"18","order":"7","route":"level_up"} | level_up_final.csv:3703 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [208: モドラ](pokemon/208.md) | [349: りゅうのまい](moves/349.md) | {"level":"50","order":"16","route":"level_up"} | level_up_final.csv:3712 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [209: コモラゴン](pokemon/209.md) | [363: インファイト](moves/363.md) | {"level":"56","order":"18","route":"level_up"} | level_up_final.csv:3731 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [209: コモラゴン](pokemon/209.md) | [339: ビルドアップ](moves/339.md) | {"level":"56","order":"19","route":"level_up"} | level_up_final.csv:3732 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [214: ヤミクラゲ](pokemon/214.md) | [127: たきのぼり](moves/127.md) | {"level":"32","order":"8","route":"level_up"} | level_up_final.csv:3814 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [214: ヤミクラゲ](pokemon/214.md) | [240: あまごい](moves/240.md) | {"level":"38","order":"10","route":"level_up"} | level_up_final.csv:3816 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [214: ヤミクラゲ](pokemon/214.md) | [282: はたきおとす](moves/282.md) | {"level":"48","order":"12","route":"level_up"} | level_up_final.csv:3818 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [215: コイナリ](pokemon/215.md) | [261: おにび](moves/261.md) | {"level":"23","order":"9","route":"level_up"} | level_up_final.csv:3828 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [216: オオイナリ](pokemon/216.md) | [261: おにび](moves/261.md) | {"level":"38","order":"16","route":"level_up"} | level_up_final.csv:3854 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [216: オオイナリ](pokemon/216.md) | [126: だいもんじ](moves/126.md) | {"level":"54","order":"21","route":"level_up"} | level_up_final.csv:3859 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [217: キャンペル](pokemon/217.md) | [310: おどろかす](moves/310.md) | {"level":"8","order":"5","route":"level_up"} | level_up_final.csv:3866 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [218: ホムロソク](pokemon/218.md) | [126: だいもんじ](moves/126.md) | {"level":"54","order":"16","route":"level_up"} | level_up_final.csv:3895 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [219: ガレキダマ](pokemon/219.md) | [246: げんしのちから](moves/246.md) | {"level":"20","order":"7","route":"level_up"} | level_up_final.csv:3904 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [219: ガレキダマ](pokemon/219.md) | [392: かげうち](moves/392.md) | {"level":"24","order":"9","route":"level_up"} | level_up_final.csv:3906 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [219: ガレキダマ](pokemon/219.md) | [310: おどろかす](moves/310.md) | {"level":"32","order":"12","route":"level_up"} | level_up_final.csv:3909 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [220: ジバクン](pokemon/220.md) | [550: ステルスロック](moves/550.md) | {"level":"38","order":"9","route":"level_up"} | level_up_final.csv:3927 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [220: ジバクン](pokemon/220.md) | [407: ストーンエッジ](moves/407.md) | {"level":"49","order":"10","route":"level_up"} | level_up_final.csv:3928 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [220: ジバクン](pokemon/220.md) | [796: ポルターガイスト](moves/796.md) | {"level":"52","order":"11","route":"level_up"} | level_up_final.csv:3929 | True | &#91;"level_up","machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [220: ジバクン](pokemon/220.md) | [261: おにび](moves/261.md) | {"level":"56","order":"12","route":"level_up"} | level_up_final.csv:3930 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [221: ワラコゾウ](pokemon/221.md) | [189: どろかけ](moves/189.md) | {"level":"8","order":"5","route":"level_up"} | level_up_final.csv:3935 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [221: ワラコゾウ](pokemon/221.md) | [201: すなあらし](moves/201.md) | {"level":"26","order":"10","route":"level_up"} | level_up_final.csv:3940 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [222: ワラガシラ](pokemon/222.md) | [201: すなあらし](moves/201.md) | {"level":"38","order":"11","route":"level_up"} | level_up_final.csv:3958 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [222: ワラガシラ](pokemon/222.md) | [89: じしん](moves/89.md) | {"level":"48","order":"13","route":"level_up"} | level_up_final.csv:3960 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [222: ワラガシラ](pokemon/222.md) | [383: ブレイブバード](moves/383.md) | {"level":"50","order":"14","route":"level_up"} | level_up_final.csv:3961 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [222: ワラガシラ](pokemon/222.md) | [554: おいかぜ](moves/554.md) | {"level":"56","order":"16","route":"level_up"} | level_up_final.csv:3963 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [225: ドルマイン](pokemon/225.md) | [603: ヘビーボンバー](moves/603.md) | {"level":"38","order":"8","route":"level_up"} | level_up_final.csv:4006 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [225: ドルマイン](pokemon/225.md) | [334: てっぺき](moves/334.md) | {"level":"50","order":"9","route":"level_up"} | level_up_final.csv:4007 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [233: プカスカ](pokemon/233.md) | [84: でんきショック](moves/84.md) | {"level":"8","order":"5","route":"level_up"} | level_up_final.csv:4144 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [233: プカスカ](pokemon/233.md) | [86: でんじは](moves/86.md) | {"level":"16","order":"8","route":"level_up"} | level_up_final.csv:4147 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [233: プカスカ](pokemon/233.md) | [554: おいかぜ](moves/554.md) | {"level":"41","order":"17","route":"level_up"} | level_up_final.csv:4156 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [234: スモーガス](pokemon/234.md) | [86: でんじは](moves/86.md) | {"level":"38","order":"16","route":"level_up"} | level_up_final.csv:4174 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [234: スモーガス](pokemon/234.md) | [87: かみなり](moves/87.md) | {"level":"58","order":"22","route":"level_up"} | level_up_final.csv:4180 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [235: ココロン](pokemon/235.md) | [73: やどりぎのタネ](moves/73.md) | {"level":"16","order":"8","route":"level_up"} | level_up_final.csv:4188 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [235: ココロン](pokemon/235.md) | [72: メガドレイン](moves/72.md) | {"level":"18","order":"9","route":"level_up"} | level_up_final.csv:4189 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [236: カモドック](pokemon/236.md) | [382: エナジーボール](moves/382.md) | {"level":"36","order":"12","route":"level_up"} | level_up_final.csv:4211 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [236: カモドック](pokemon/236.md) | [73: やどりぎのタネ](moves/73.md) | {"level":"38","order":"13","route":"level_up"} | level_up_final.csv:4212 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [237: トノッパー](pokemon/237.md) | [411: アクアジェット](moves/411.md) | {"level":"13","order":"5","route":"level_up"} | level_up_final.csv:4223 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [237: トノッパー](pokemon/237.md) | [352: みずのはどう](moves/352.md) | {"level":"19","order":"7","route":"level_up"} | level_up_final.csv:4225 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [238: ガルラーダ](pokemon/238.md) | [127: たきのぼり](moves/127.md) | {"level":"32","order":"10","route":"level_up"} | level_up_final.csv:4247 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [238: ガルラーダ](pokemon/238.md) | [240: あまごい](moves/240.md) | {"level":"38","order":"13","route":"level_up"} | level_up_final.csv:4250 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [238: ガルラーダ](pokemon/238.md) | [363: インファイト](moves/363.md) | {"level":"56","order":"20","route":"level_up"} | level_up_final.csv:4257 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [238: ガルラーダ](pokemon/238.md) | [339: ビルドアップ](moves/339.md) | {"level":"56","order":"21","route":"level_up"} | level_up_final.csv:4258 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [239: ハサーガ](pokemon/239.md) | [339: ビルドアップ](moves/339.md) | {"level":"50","order":"15","route":"level_up"} | level_up_final.csv:4273 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [239: ハサーガ](pokemon/239.md) | [603: ヘビーボンバー](moves/603.md) | {"level":"50","order":"16","route":"level_up"} | level_up_final.csv:4274 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [239: ハサーガ](pokemon/239.md) | [363: インファイト](moves/363.md) | {"level":"56","order":"20","route":"level_up"} | level_up_final.csv:4278 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [239: ハサーガ](pokemon/239.md) | [334: てっぺき](moves/334.md) | {"level":"56","order":"21","route":"level_up"} | level_up_final.csv:4279 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [240: アメクジ](pokemon/240.md) | [411: アクアジェット](moves/411.md) | {"level":"13","order":"6","route":"level_up"} | level_up_final.csv:4285 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [241: アメリシア](pokemon/241.md) | [240: あまごい](moves/240.md) | {"level":"38","order":"15","route":"level_up"} | level_up_final.csv:4310 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [241: アメリシア](pokemon/241.md) | [505: ヘドロウェーブ](moves/505.md) | {"level":"48","order":"18","route":"level_up"} | level_up_final.csv:4313 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [241: アメリシア](pokemon/241.md) | [56: ハイドロポンプ](moves/56.md) | {"level":"52","order":"20","route":"level_up"} | level_up_final.csv:4315 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [241: アメリシア](pokemon/241.md) | [92: どくどく](moves/92.md) | {"level":"56","order":"21","route":"level_up"} | level_up_final.csv:4316 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [242: カララン](pokemon/242.md) | [29: ずつき](moves/29.md) | {"level":"16","order":"7","route":"level_up"} | level_up_final.csv:4325 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [242: カララン](pokemon/242.md) | [129: スピードスター](moves/129.md) | {"level":"16","order":"8","route":"level_up"} | level_up_final.csv:4326 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [242: カララン](pokemon/242.md) | [75: はっぱカッター](moves/75.md) | {"level":"24","order":"11","route":"level_up"} | level_up_final.csv:4329 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [242: カララン](pokemon/242.md) | [72: メガドレイン](moves/72.md) | {"level":"32","order":"14","route":"level_up"} | level_up_final.csv:4332 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [243: カンカーン](pokemon/243.md) | [304: ハイパーボイス](moves/304.md) | {"level":"38","order":"15","route":"level_up"} | level_up_final.csv:4352 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [243: カンカーン](pokemon/243.md) | [227: アンコール](moves/227.md) | {"level":"38","order":"16","route":"level_up"} | level_up_final.csv:4353 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [243: カンカーン](pokemon/243.md) | [281: あくび](moves/281.md) | {"level":"48","order":"19","route":"level_up"} | level_up_final.csv:4356 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [243: カンカーン](pokemon/243.md) | [202: ギガドレイン](moves/202.md) | {"level":"56","order":"21","route":"level_up"} | level_up_final.csv:4358 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [244: クラウン](pokemon/244.md) | [29: ずつき](moves/29.md) | {"level":"16","order":"7","route":"level_up"} | level_up_final.csv:4367 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [244: クラウン](pokemon/244.md) | [227: アンコール](moves/227.md) | {"level":"16","order":"8","route":"level_up"} | level_up_final.csv:4368 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [245: テイルーン](pokemon/245.md) | [227: アンコール](moves/227.md) | {"level":"38","order":"15","route":"level_up"} | level_up_final.csv:4393 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [245: テイルーン](pokemon/245.md) | [518: ぼうふう](moves/518.md) | {"level":"50","order":"18","route":"level_up"} | level_up_final.csv:4396 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [245: テイルーン](pokemon/245.md) | [555: ばくおんぱ](moves/555.md) | {"level":"55","order":"20","route":"level_up"} | level_up_final.csv:4398 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [245: テイルーン](pokemon/245.md) | [554: おいかぜ](moves/554.md) | {"level":"56","order":"21","route":"level_up"} | level_up_final.csv:4399 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [246: モグルトン](pokemon/246.md) | [227: アンコール](moves/227.md) | {"level":"38","order":"12","route":"level_up"} | level_up_final.csv:4414 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [246: モグルトン](pokemon/246.md) | [38: すてみタックル](moves/38.md) | {"level":"49","order":"15","route":"level_up"} | level_up_final.csv:4417 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [251: ラクチャン](pokemon/251.md) | [29: ずつき](moves/29.md) | {"level":"16","order":"3","route":"level_up"} | level_up_final.csv:4500 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [251: ラクチャン](pokemon/251.md) | [227: アンコール](moves/227.md) | {"level":"16","order":"4","route":"level_up"} | level_up_final.csv:4501 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [277: ドゴン](pokemon/277.md) | [227: アンコール](moves/227.md) | {"level":"38","order":"13","route":"level_up"} | level_up_final.csv:4724 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [277: ドゴン](pokemon/277.md) | [38: すてみタックル](moves/38.md) | {"level":"49","order":"17","route":"level_up"} | level_up_final.csv:4728 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [277: ドゴン](pokemon/277.md) | [339: ビルドアップ](moves/339.md) | {"level":"56","order":"19","route":"level_up"} | level_up_final.csv:4730 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [279: トコヤミ](pokemon/279.md) | [282: はたきおとす](moves/282.md) | {"level":"28","order":"14","route":"level_up"} | level_up_final.csv:4768 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [279: トコヤミ](pokemon/279.md) | [269: ちょうはつ](moves/269.md) | {"level":"38","order":"19","route":"level_up"} | level_up_final.csv:4773 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [279: トコヤミ](pokemon/279.md) | [383: ブレイブバード](moves/383.md) | {"level":"50","order":"24","route":"level_up"} | level_up_final.csv:4778 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [279: トコヤミ](pokemon/279.md) | [554: おいかぜ](moves/554.md) | {"level":"56","order":"26","route":"level_up"} | level_up_final.csv:4780 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [281: クチールス](pokemon/281.md) | [499: つららおとし](moves/499.md) | {"level":"38","order":"17","route":"level_up"} | level_up_final.csv:4820 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [281: クチールス](pokemon/281.md) | [1034: ゆきげしき](moves/1034.md) | {"level":"48","order":"20","route":"level_up"} | level_up_final.csv:4823 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [281: クチールス](pokemon/281.md) | [282: はたきおとす](moves/282.md) | {"level":"48","order":"21","route":"level_up"} | level_up_final.csv:4824 | True | &#91;"level_up","machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [281: クチールス](pokemon/281.md) | [269: ちょうはつ](moves/269.md) | {"level":"56","order":"26","route":"level_up"} | level_up_final.csv:4829 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [285: ガッツロス](pokemon/285.md) | [339: ビルドアップ](moves/339.md) | {"level":"50","order":"15","route":"level_up"} | level_up_final.csv:4903 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [285: ガッツロス](pokemon/285.md) | [363: インファイト](moves/363.md) | {"level":"56","order":"18","route":"level_up"} | level_up_final.csv:4906 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [288: アーボスク](pokemon/288.md) | [92: どくどく](moves/92.md) | {"level":"38","order":"20","route":"level_up"} | level_up_final.csv:4969 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [288: アーボスク](pokemon/288.md) | [282: はたきおとす](moves/282.md) | {"level":"48","order":"24","route":"level_up"} | level_up_final.csv:4973 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [288: アーボスク](pokemon/288.md) | [404: ダストシュート](moves/404.md) | {"level":"50","order":"25","route":"level_up"} | level_up_final.csv:4974 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [288: アーボスク](pokemon/288.md) | [269: ちょうはつ](moves/269.md) | {"level":"56","order":"27","route":"level_up"} | level_up_final.csv:4976 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [291: モアドガス](pokemon/291.md) | [261: おにび](moves/261.md) | {"level":"56","order":"21","route":"level_up"} | level_up_final.csv:5034 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [304: マグッピ](pokemon/304.md) | [411: アクアジェット](moves/411.md) | {"level":"13","order":"6","route":"level_up"} | level_up_final.csv:5283 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [305: ベタデーム](pokemon/305.md) | [667: アクアブレイク](moves/667.md) | {"level":"38","order":"10","route":"level_up"} | level_up_final.csv:5304 | True | &#91;"level_up","machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [305: ベタデーム](pokemon/305.md) | [57: なみのり](moves/57.md) | {"level":"38","order":"11","route":"level_up"} | level_up_final.csv:5305 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [307: ボンバット](pokemon/307.md) | [92: どくどく](moves/92.md) | {"level":"38","order":"11","route":"level_up"} | level_up_final.csv:5345 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [307: ボンバット](pokemon/307.md) | [404: ダストシュート](moves/404.md) | {"level":"50","order":"15","route":"level_up"} | level_up_final.csv:5349 | True | &#91;"egg","level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [307: ボンバット](pokemon/307.md) | [383: ブレイブバード](moves/383.md) | {"level":"50","order":"16","route":"level_up"} | level_up_final.csv:5350 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [307: ボンバット](pokemon/307.md) | [554: おいかぜ](moves/554.md) | {"level":"56","order":"18","route":"level_up"} | level_up_final.csv:5352 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [310: ダンカンス](pokemon/310.md) | [29: ずつき](moves/29.md) | {"level":"16","order":"10","route":"level_up"} | level_up_final.csv:5403 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [310: ダンカンス](pokemon/310.md) | [129: スピードスター](moves/129.md) | {"level":"16","order":"11","route":"level_up"} | level_up_final.csv:5404 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [310: ダンカンス](pokemon/310.md) | [75: はっぱカッター](moves/75.md) | {"level":"24","order":"13","route":"level_up"} | level_up_final.csv:5406 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [310: ダンカンス](pokemon/310.md) | [72: メガドレイン](moves/72.md) | {"level":"32","order":"15","route":"level_up"} | level_up_final.csv:5408 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [311: ドサーモン](pokemon/311.md) | [127: たきのぼり](moves/127.md) | {"level":"48","order":"16","route":"level_up"} | level_up_final.csv:5434 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [311: ドサーモン](pokemon/311.md) | [339: ビルドアップ](moves/339.md) | {"level":"50","order":"18","route":"level_up"} | level_up_final.csv:5436 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [311: ドサーモン](pokemon/311.md) | [363: インファイト](moves/363.md) | {"level":"56","order":"20","route":"level_up"} | level_up_final.csv:5438 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [312: テッケン](pokemon/312.md) | [249: いわくだき](moves/249.md) | {"level":"8","order":"5","route":"level_up"} | level_up_final.csv:5445 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [320: ヒョウカク](pokemon/320.md) | [86: でんじは](moves/86.md) | {"level":"38","order":"13","route":"level_up"} | level_up_final.csv:5608 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [320: ヒョウカク](pokemon/320.md) | [1034: ゆきげしき](moves/1034.md) | {"level":"56","order":"18","route":"level_up"} | level_up_final.csv:5613 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [320: ヒョウカク](pokemon/320.md) | [87: かみなり](moves/87.md) | {"level":"58","order":"19","route":"level_up"} | level_up_final.csv:5614 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [323: プレシオン](pokemon/323.md) | [227: アンコール](moves/227.md) | {"level":"38","order":"14","route":"level_up"} | level_up_final.csv:5677 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [323: プレシオン](pokemon/323.md) | [56: ハイドロポンプ](moves/56.md) | {"level":"52","order":"17","route":"level_up"} | level_up_final.csv:5680 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [323: プレシオン](pokemon/323.md) | [555: ばくおんぱ](moves/555.md) | {"level":"55","order":"19","route":"level_up"} | level_up_final.csv:5682 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [323: プレシオン](pokemon/323.md) | [240: あまごい](moves/240.md) | {"level":"56","order":"20","route":"level_up"} | level_up_final.csv:5683 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [326: メルリコ](pokemon/326.md) | [411: アクアジェット](moves/411.md) | {"level":"13","order":"6","route":"level_up"} | level_up_final.csv:5718 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [326: メルリコ](pokemon/326.md) | [352: みずのはどう](moves/352.md) | {"level":"19","order":"8","route":"level_up"} | level_up_final.csv:5720 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [327: サムラダケ](pokemon/327.md) | [202: ギガドレイン](moves/202.md) | {"level":"36","order":"12","route":"level_up"} | level_up_final.csv:5742 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [327: サムラダケ](pokemon/327.md) | [73: やどりぎのタネ](moves/73.md) | {"level":"38","order":"13","route":"level_up"} | level_up_final.csv:5743 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [327: サムラダケ](pokemon/327.md) | [235: こうごうせい](moves/235.md) | {"level":"48","order":"17","route":"level_up"} | level_up_final.csv:5747 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [328: ブレイドン](pokemon/328.md) | [280: かわらわり](moves/280.md) | {"level":"24","order":"10","route":"level_up"} | level_up_final.csv:5759 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [328: ブレイドン](pokemon/328.md) | [339: ビルドアップ](moves/339.md) | {"level":"50","order":"17","route":"level_up"} | level_up_final.csv:5766 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [329: ブレイオー](pokemon/329.md) | [339: ビルドアップ](moves/339.md) | {"level":"50","order":"16","route":"level_up"} | level_up_final.csv:5786 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [329: ブレイオー](pokemon/329.md) | [603: ヘビーボンバー](moves/603.md) | {"level":"50","order":"17","route":"level_up"} | level_up_final.csv:5787 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [329: ブレイオー](pokemon/329.md) | [363: インファイト](moves/363.md) | {"level":"56","order":"19","route":"level_up"} | level_up_final.csv:5789 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [329: ブレイオー](pokemon/329.md) | [334: てっぺき](moves/334.md) | {"level":"56","order":"20","route":"level_up"} | level_up_final.csv:5790 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [333: アルデッパ](pokemon/333.md) | [495: じならし](moves/495.md) | {"level":"28","order":"10","route":"level_up"} | level_up_final.csv:5858 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [333: アルデッパ](pokemon/333.md) | [384: だいちのちから](moves/384.md) | {"level":"38","order":"16","route":"level_up"} | level_up_final.csv:5864 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [333: アルデッパ](pokemon/333.md) | [201: すなあらし](moves/201.md) | {"level":"48","order":"18","route":"level_up"} | level_up_final.csv:5866 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [333: アルデッパ](pokemon/333.md) | [515: ニトロチャージ](moves/515.md) | {"level":"56","order":"21","route":"level_up"} | level_up_final.csv:5869 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [334: ゴキブロス](pokemon/334.md) | [535: むしくい](moves/535.md) | {"level":"15","order":"7","route":"level_up"} | level_up_final.csv:5877 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [334: ゴキブロス](pokemon/334.md) | [44: かみつく](moves/44.md) | {"level":"24","order":"10","route":"level_up"} | level_up_final.csv:5880 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [334: ゴキブロス](pokemon/334.md) | [562: ねばねばネット](moves/562.md) | {"level":"26","order":"11","route":"level_up"} | level_up_final.csv:5881 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [334: ゴキブロス](pokemon/334.md) | [269: ちょうはつ](moves/269.md) | {"level":"32","order":"13","route":"level_up"} | level_up_final.csv:5883 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [335: ビビッドン](pokemon/335.md) | [240: あまごい](moves/240.md) | {"level":"38","order":"18","route":"level_up"} | level_up_final.csv:5908 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [335: ビビッドン](pokemon/335.md) | [56: ハイドロポンプ](moves/56.md) | {"level":"52","order":"23","route":"level_up"} | level_up_final.csv:5913 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [335: ビビッドン](pokemon/335.md) | [86: でんじは](moves/86.md) | {"level":"56","order":"26","route":"level_up"} | level_up_final.csv:5916 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [336: ドルン](pokemon/336.md) | [86: でんじは](moves/86.md) | {"level":"38","order":"11","route":"level_up"} | level_up_final.csv:5928 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [336: ドルン](pokemon/336.md) | [87: かみなり](moves/87.md) | {"level":"58","order":"17","route":"level_up"} | level_up_final.csv:5934 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [337: バーネッコ](pokemon/337.md) | [261: おにび](moves/261.md) | {"level":"38","order":"14","route":"level_up"} | level_up_final.csv:5949 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [337: バーネッコ](pokemon/337.md) | [364: フレアドライブ](moves/364.md) | {"level":"56","order":"18","route":"level_up"} | level_up_final.csv:5953 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [338: コケゾー](pokemon/338.md) | [73: やどりぎのタネ](moves/73.md) | {"level":"16","order":"6","route":"level_up"} | level_up_final.csv:5962 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [339: オンネット](pokemon/339.md) | [269: ちょうはつ](moves/269.md) | {"level":"38","order":"17","route":"level_up"} | level_up_final.csv:5990 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [342: ノコウテイ](pokemon/342.md) | [227: アンコール](moves/227.md) | {"level":"38","order":"15","route":"level_up"} | level_up_final.csv:6046 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [342: ノコウテイ](pokemon/342.md) | [38: すてみタックル](moves/38.md) | {"level":"49","order":"21","route":"level_up"} | level_up_final.csv:6052 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [344: カミギリー](pokemon/344.md) | [562: ねばねばネット](moves/562.md) | {"level":"38","order":"14","route":"level_up"} | level_up_final.csv:6094 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [344: カミギリー](pokemon/344.md) | [224: メガホーン](moves/224.md) | {"level":"45","order":"16","route":"level_up"} | level_up_final.csv:6096 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [344: カミギリー](pokemon/344.md) | [603: ヘビーボンバー](moves/603.md) | {"level":"50","order":"18","route":"level_up"} | level_up_final.csv:6098 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [344: カミギリー](pokemon/344.md) | [334: てっぺき](moves/334.md) | {"level":"56","order":"21","route":"level_up"} | level_up_final.csv:6101 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [345: レファン](pokemon/345.md) | [29: ずつき](moves/29.md) | {"level":"16","order":"7","route":"level_up"} | level_up_final.csv:6109 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [345: レファン](pokemon/345.md) | [227: アンコール](moves/227.md) | {"level":"16","order":"8","route":"level_up"} | level_up_final.csv:6110 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [347: ストータス](pokemon/347.md) | [65: ドリルくちばし](moves/65.md) | {"level":"35","order":"14","route":"level_up"} | level_up_final.csv:6154 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [347: ストータス](pokemon/347.md) | [373: エアスラッシュ](moves/373.md) | {"level":"41","order":"17","route":"level_up"} | level_up_final.csv:6157 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [347: ストータス](pokemon/347.md) | [554: おいかぜ](moves/554.md) | {"level":"48","order":"20","route":"level_up"} | level_up_final.csv:6160 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [349: ラブリン](pokemon/349.md) | [29: ずつき](moves/29.md) | {"level":"16","order":"7","route":"level_up"} | level_up_final.csv:6188 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [349: ラブリン](pokemon/349.md) | [227: アンコール](moves/227.md) | {"level":"16","order":"8","route":"level_up"} | level_up_final.csv:6189 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [350: オールガ](pokemon/350.md) | [86: でんじは](moves/86.md) | {"level":"38","order":"13","route":"level_up"} | level_up_final.csv:6212 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [350: オールガ](pokemon/350.md) | [87: かみなり](moves/87.md) | {"level":"58","order":"18","route":"level_up"} | level_up_final.csv:6217 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [353: ヒカリゴケ](pokemon/353.md) | [382: エナジーボール](moves/382.md) | {"level":"36","order":"18","route":"level_up"} | level_up_final.csv:6278 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [353: ヒカリゴケ](pokemon/353.md) | [73: やどりぎのタネ](moves/73.md) | {"level":"38","order":"19","route":"level_up"} | level_up_final.csv:6279 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [356: セルディー](pokemon/356.md) | [1034: ゆきげしき](moves/1034.md) | {"level":"48","order":"19","route":"level_up"} | level_up_final.csv:6349 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [356: セルディー](pokemon/356.md) | [59: ふぶき](moves/59.md) | {"level":"53","order":"21","route":"level_up"} | level_up_final.csv:6351 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [357: コゴボー](pokemon/357.md) | [52: ひのこ](moves/52.md) | {"level":"8","order":"5","route":"level_up"} | level_up_final.csv:6358 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [357: コゴボー](pokemon/357.md) | [261: おにび](moves/261.md) | {"level":"23","order":"9","route":"level_up"} | level_up_final.csv:6362 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [358: ガネーシャ](pokemon/358.md) | [201: すなあらし](moves/201.md) | {"level":"38","order":"15","route":"level_up"} | level_up_final.csv:6385 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [358: ガネーシャ](pokemon/358.md) | [89: じしん](moves/89.md) | {"level":"48","order":"19","route":"level_up"} | level_up_final.csv:6389 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [360: プレゼンタ](pokemon/360.md) | [1034: ゆきげしき](moves/1034.md) | {"level":"48","order":"11","route":"level_up"} | level_up_final.csv:6421 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [373: カモナイツ](pokemon/373.md) | [554: おいかぜ](moves/554.md) | {"level":"41","order":"18","route":"level_up"} | level_up_final.csv:6650 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [373: カモナイツ](pokemon/373.md) | [339: ビルドアップ](moves/339.md) | {"level":"56","order":"21","route":"level_up"} | level_up_final.csv:6653 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [382: キルギシア](pokemon/382.md) | [44: かみつく](moves/44.md) | {"level":"9","order":"8","route":"level_up"} | level_up_final.csv:6813 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [382: キルギシア](pokemon/382.md) | [269: ちょうはつ](moves/269.md) | {"level":"22","order":"13","route":"level_up"} | level_up_final.csv:6818 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [382: キルギシア](pokemon/382.md) | [232: メタルクロー](moves/232.md) | {"level":"24","order":"15","route":"level_up"} | level_up_final.csv:6820 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [382: キルギシア](pokemon/382.md) | [334: てっぺき](moves/334.md) | {"level":"50","order":"24","route":"level_up"} | level_up_final.csv:6829 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [383: シルドール](pokemon/383.md) | [282: はたきおとす](moves/282.md) | {"level":"28","order":"14","route":"level_up"} | level_up_final.csv:6845 | True | &#91;"level_up","machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [383: シルドール](pokemon/383.md) | [269: ちょうはつ](moves/269.md) | {"level":"38","order":"17","route":"level_up"} | level_up_final.csv:6848 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [383: シルドール](pokemon/383.md) | [603: ヘビーボンバー](moves/603.md) | {"level":"50","order":"22","route":"level_up"} | level_up_final.csv:6853 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [383: シルドール](pokemon/383.md) | [334: てっぺき](moves/334.md) | {"level":"56","order":"24","route":"level_up"} | level_up_final.csv:6855 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [384: セルシィ](pokemon/384.md) | [196: こごえるかぜ](moves/196.md) | {"level":"13","order":"6","route":"level_up"} | level_up_final.csv:6864 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [384: セルシィ](pokemon/384.md) | [1034: ゆきげしき](moves/1034.md) | {"level":"26","order":"10","route":"level_up"} | level_up_final.csv:6868 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [385: テルテン](pokemon/385.md) | [227: アンコール](moves/227.md) | {"level":"38","order":"11","route":"level_up"} | level_up_final.csv:6887 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [385: テルテン](pokemon/385.md) | [555: ばくおんぱ](moves/555.md) | {"level":"55","order":"18","route":"level_up"} | level_up_final.csv:6894 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [386: ワークロ](pokemon/386.md) | [44: かみつく](moves/44.md) | {"level":"9","order":"5","route":"level_up"} | level_up_final.csv:6902 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [386: ワークロ](pokemon/386.md) | [269: ちょうはつ](moves/269.md) | {"level":"22","order":"9","route":"level_up"} | level_up_final.csv:6906 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [386: ワークロ](pokemon/386.md) | [17: つばさでうつ](moves/17.md) | {"level":"24","order":"11","route":"level_up"} | level_up_final.csv:6908 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [386: ワークロ](pokemon/386.md) | [554: おいかぜ](moves/554.md) | {"level":"41","order":"17","route":"level_up"} | level_up_final.csv:6914 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [387: アリンセス](pokemon/387.md) | [672: かふんだんご](moves/672.md) | {"level":"28","order":"10","route":"level_up"} | level_up_final.csv:6929 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [387: アリンセス](pokemon/387.md) | [562: ねばねばネット](moves/562.md) | {"level":"38","order":"16","route":"level_up"} | level_up_final.csv:6935 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [388: ティオルス](pokemon/388.md) | [532: ドラゴンテール](moves/532.md) | {"level":"18","order":"7","route":"level_up"} | level_up_final.csv:6948 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [388: ティオルス](pokemon/388.md) | [349: りゅうのまい](moves/349.md) | {"level":"50","order":"16","route":"level_up"} | level_up_final.csv:6957 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [389: プテリクス](pokemon/389.md) | [337: ドラゴンクロー](moves/337.md) | {"level":"30","order":"13","route":"level_up"} | level_up_final.csv:6971 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [389: プテリクス](pokemon/389.md) | [65: ドリルくちばし](moves/65.md) | {"level":"36","order":"15","route":"level_up"} | level_up_final.csv:6973 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [389: プテリクス](pokemon/389.md) | [554: おいかぜ](moves/554.md) | {"level":"44","order":"19","route":"level_up"} | level_up_final.csv:6977 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [389: プテリクス](pokemon/389.md) | [349: りゅうのまい](moves/349.md) | {"level":"50","order":"21","route":"level_up"} | level_up_final.csv:6979 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [390: ティラノス](pokemon/390.md) | [349: りゅうのまい](moves/349.md) | {"level":"50","order":"17","route":"level_up"} | level_up_final.csv:6998 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [390: ティラノス](pokemon/390.md) | [200: げきりん](moves/200.md) | {"level":"62","order":"21","route":"level_up"} | level_up_final.csv:7002 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [391: ブレイバー](pokemon/391.md) | [249: いわくだき](moves/249.md) | {"level":"8","order":"4","route":"level_up"} | level_up_final.csv:7006 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [391: ブレイバー](pokemon/391.md) | [339: ビルドアップ](moves/339.md) | {"level":"50","order":"15","route":"level_up"} | level_up_final.csv:7017 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [392: ヤマネツ](pokemon/392.md) | [382: エナジーボール](moves/382.md) | {"level":"36","order":"13","route":"level_up"} | level_up_final.csv:7032 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [392: ヤマネツ](pokemon/392.md) | [73: やどりぎのタネ](moves/73.md) | {"level":"38","order":"14","route":"level_up"} | level_up_final.csv:7033 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [393: ヒササビ](pokemon/393.md) | [86: でんじは](moves/86.md) | {"level":"38","order":"14","route":"level_up"} | level_up_final.csv:7052 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [393: ヒササビ](pokemon/393.md) | [518: ぼうふう](moves/518.md) | {"level":"50","order":"18","route":"level_up"} | level_up_final.csv:7056 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [393: ヒササビ](pokemon/393.md) | [554: おいかぜ](moves/554.md) | {"level":"56","order":"20","route":"level_up"} | level_up_final.csv:7058 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [393: ヒササビ](pokemon/393.md) | [87: かみなり](moves/87.md) | {"level":"58","order":"22","route":"level_up"} | level_up_final.csv:7060 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [394: シャーモン](pokemon/394.md) | [249: いわくだき](moves/249.md) | {"level":"8","order":"5","route":"level_up"} | level_up_final.csv:7066 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [394: シャーモン](pokemon/394.md) | [339: ビルドアップ](moves/339.md) | {"level":"50","order":"15","route":"level_up"} | level_up_final.csv:7076 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [400: ロイツァー](pokemon/400.md) | [411: アクアジェット](moves/411.md) | {"level":"13","order":"5","route":"level_up"} | level_up_final.csv:7184 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [400: ロイツァー](pokemon/400.md) | [352: みずのはどう](moves/352.md) | {"level":"19","order":"7","route":"level_up"} | level_up_final.csv:7186 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [401: ガタノア](pokemon/401.md) | [57: なみのり](moves/57.md) | {"level":"30","order":"8","route":"level_up"} | level_up_final.csv:7206 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [401: ガタノア](pokemon/401.md) | [240: あまごい](moves/240.md) | {"level":"37","order":"10","route":"level_up"} | level_up_final.csv:7208 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [401: ガタノア](pokemon/401.md) | [94: サイコキネシス](moves/94.md) | {"level":"44","order":"12","route":"level_up"} | level_up_final.csv:7210 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [401: ガタノア](pokemon/401.md) | [347: めいそう](moves/347.md) | {"level":"50","order":"14","route":"level_up"} | level_up_final.csv:7212 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [402: テツカブリ](pokemon/402.md) | [127: たきのぼり](moves/127.md) | {"level":"32","order":"7","route":"level_up"} | level_up_final.csv:7226 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [402: テツカブリ](pokemon/402.md) | [240: あまごい](moves/240.md) | {"level":"38","order":"9","route":"level_up"} | level_up_final.csv:7228 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [402: テツカブリ](pokemon/402.md) | [603: ヘビーボンバー](moves/603.md) | {"level":"50","order":"12","route":"level_up"} | level_up_final.csv:7231 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [402: テツカブリ](pokemon/402.md) | [334: てっぺき](moves/334.md) | {"level":"56","order":"13","route":"level_up"} | level_up_final.csv:7232 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [406: オルディナ](pokemon/406.md) | [44: かみつく](moves/44.md) | {"level":"9","order":"3","route":"level_up"} | level_up_final.csv:7292 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [406: オルディナ](pokemon/406.md) | [269: ちょうはつ](moves/269.md) | {"level":"22","order":"7","route":"level_up"} | level_up_final.csv:7296 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [409: オルマリア](pokemon/409.md) | [606: イカサマ](moves/606.md) | {"level":"38","order":"8","route":"level_up"} | level_up_final.csv:7360 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [409: オルマリア](pokemon/409.md) | [269: ちょうはつ](moves/269.md) | {"level":"38","order":"9","route":"level_up"} | level_up_final.csv:7361 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [410: アスフィア](pokemon/410.md) | [370: つじぎり](moves/370.md) | {"level":"35","order":"9","route":"level_up"} | level_up_final.csv:7380 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [410: アスフィア](pokemon/410.md) | [369: あくのはどう](moves/369.md) | {"level":"44","order":"12","route":"level_up"} | level_up_final.csv:7383 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [410: アスフィア](pokemon/410.md) | [269: ちょうはつ](moves/269.md) | {"level":"48","order":"13","route":"level_up"} | level_up_final.csv:7384 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [410: アスフィア](pokemon/410.md) | [337: ドラゴンクロー](moves/337.md) | {"level":"56","order":"15","route":"level_up"} | level_up_final.csv:7386 | True | &#91;"level_up"&#93; | False |
| vega_to_official_historical_adoption | [1: リープン](pokemon/1.md) | [235: こうごうせい](moves/235.md) | {"order":"25","route":"egg"} | egg_moves_final.csv:26 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [2: リーティン](pokemon/2.md) | [235: こうごうせい](moves/235.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:27 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [3: リーテイル](pokemon/3.md) | [235: こうごうせい](moves/235.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:28 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [3: リーテイル](pokemon/3.md) | [763: ボディプレス](moves/763.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:29 | True | &#91;"egg","machine"&#93; | False |
| vega_to_official_historical_adoption | [5: ファイマー](pokemon/5.md) | [241: にほんばれ](moves/241.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:52 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [6: ファマイン](pokemon/6.md) | [241: にほんばれ](moves/241.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:53 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [6: ファマイン](pokemon/6.md) | [387: わるだくみ](moves/387.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:54 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [7: アクタシ](pokemon/7.md) | [710: アクアリング](moves/710.md) | {"order":"27","route":"egg"} | egg_moves_final.csv:81 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [8: レクオレ](pokemon/8.md) | [710: アクアリング](moves/710.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:82 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [9: タテボーシ](pokemon/9.md) | [710: アクアリング](moves/710.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:83 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [9: タテボーシ](pokemon/9.md) | [113: ひかりのかべ](moves/113.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:84 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [21: フロン](pokemon/21.md) | [235: こうごうせい](moves/235.md) | {"order":"23","route":"egg"} | egg_moves_final.csv:250 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [22: フロルル](pokemon/22.md) | [235: こうごうせい](moves/235.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:251 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [23: フローリア](pokemon/23.md) | [235: こうごうせい](moves/235.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:252 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [23: フローリア](pokemon/23.md) | [113: ひかりのかべ](moves/113.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:253 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [27: ゴリチュウ](pokemon/27.md) | [268: じゅうでん](moves/268.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:287 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [27: ゴリチュウ](pokemon/27.md) | [197: みきり](moves/197.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:288 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [37: ララベリー](pokemon/37.md) | [235: こうごうせい](moves/235.md) | {"order":"25","route":"egg"} | egg_moves_final.csv:419 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [38: セラーナ](pokemon/38.md) | [235: こうごうせい](moves/235.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:420 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [38: セラーナ](pokemon/38.md) | [113: ひかりのかべ](moves/113.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:421 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [43: マホース](pokemon/43.md) | [281: あくび](moves/281.md) | {"order":"27","route":"egg"} | egg_moves_final.csv:499 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [44: ペガーン](pokemon/44.md) | [281: あくび](moves/281.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:500 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [44: ペガーン](pokemon/44.md) | [483: はねやすめ](moves/483.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:501 | True | &#91;"egg","tutor"&#93; | False |
| vega_to_official_historical_adoption | [45: ユニサス](pokemon/45.md) | [281: あくび](moves/281.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:502 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [45: ユニサス](pokemon/45.md) | [483: はねやすめ](moves/483.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:503 | True | &#91;"egg","tutor"&#93; | False |
| vega_to_official_historical_adoption | [50: ライノス](pokemon/50.md) | [191: まきびし](moves/191.md) | {"order":"26","route":"egg"} | egg_moves_final.csv:548 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [51: メタゲラス](pokemon/51.md) | [191: まきびし](moves/191.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:549 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [51: メタゲラス](pokemon/51.md) | [763: ボディプレス](moves/763.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:550 | True | &#91;"egg","tutor"&#93; | False |
| vega_to_official_historical_adoption | [53: ディザソル](pokemon/53.md) | [387: わるだくみ](moves/387.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:586 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [55: フォリキー](pokemon/55.md) | [113: ひかりのかべ](moves/113.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:618 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [56: バーニン](pokemon/56.md) | [113: ひかりのかべ](moves/113.md) | {"order":"27","route":"egg"} | egg_moves_final.csv:645 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [57: ファントマ](pokemon/57.md) | [113: ひかりのかべ](moves/113.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:646 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [57: ファントマ](pokemon/57.md) | [194: みちづれ](moves/194.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:647 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [68: テディ](pokemon/68.md) | [281: あくび](moves/281.md) | {"order":"28","route":"egg"} | egg_moves_final.csv:742 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [69: ググズリー](pokemon/69.md) | [281: あくび](moves/281.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:743 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [69: ググズリー](pokemon/69.md) | [387: わるだくみ](moves/387.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:744 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [70: ハンタマ](pokemon/70.md) | [387: わるだくみ](moves/387.md) | {"order":"25","route":"egg"} | egg_moves_final.csv:769 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [81: ダンゴロウ](pokemon/81.md) | [710: アクアリング](moves/710.md) | {"order":"22","route":"egg"} | egg_moves_final.csv:884 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [82: マルマジロ](pokemon/82.md) | [710: アクアリング](moves/710.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:885 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [82: マルマジロ](pokemon/82.md) | [763: ボディプレス](moves/763.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:886 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [83: アロフィー](pokemon/83.md) | [710: アクアリング](moves/710.md) | {"order":"23","route":"egg"} | egg_moves_final.csv:909 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [83: アロフィー](pokemon/83.md) | [235: こうごうせい](moves/235.md) | {"order":"24","route":"egg"} | egg_moves_final.csv:910 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [84: リーフィス](pokemon/84.md) | [710: アクアリング](moves/710.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:911 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [84: リーフィス](pokemon/84.md) | [235: こうごうせい](moves/235.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:912 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [87: ユカリア](pokemon/87.md) | [113: ひかりのかべ](moves/113.md) | {"order":"22","route":"egg"} | egg_moves_final.csv:962 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [88: ネクロシア](pokemon/88.md) | [113: ひかりのかべ](moves/113.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:963 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [88: ネクロシア](pokemon/88.md) | [194: みちづれ](moves/194.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:964 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [89: カプリン](pokemon/89.md) | [113: ひかりのかべ](moves/113.md) | {"order":"23","route":"egg"} | egg_moves_final.csv:987 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [90: ゴートン](pokemon/90.md) | [113: ひかりのかべ](moves/113.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:988 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [91: バフォット](pokemon/91.md) | [387: わるだくみ](moves/387.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:989 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [91: バフォット](pokemon/91.md) | [113: ひかりのかべ](moves/113.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:990 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [94: バードン](pokemon/94.md) | [483: はねやすめ](moves/483.md) | {"order":"22","route":"egg"} | egg_moves_final.csv:1066 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [95: ゴルドー](pokemon/95.md) | [483: はねやすめ](moves/483.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1067 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [95: ゴルドー](pokemon/95.md) | [763: ボディプレス](moves/763.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:1068 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [96: フィニクス](pokemon/96.md) | [241: にほんばれ](moves/241.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1069 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [96: フィニクス](pokemon/96.md) | [483: はねやすめ](moves/483.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:1070 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [97: クロッチ](pokemon/97.md) | [281: あくび](moves/281.md) | {"order":"29","route":"egg"} | egg_moves_final.csv:1099 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [98: コクジャク](pokemon/98.md) | [281: あくび](moves/281.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1100 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [98: コクジャク](pokemon/98.md) | [483: はねやすめ](moves/483.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:1101 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [99: シャミネ](pokemon/99.md) | [281: あくび](moves/281.md) | {"order":"26","route":"egg"} | egg_moves_final.csv:1127 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [99: シャミネ](pokemon/99.md) | [483: はねやすめ](moves/483.md) | {"order":"27","route":"egg"} | egg_moves_final.csv:1128 | True | &#91;"egg","tutor"&#93; | False |
| vega_to_official_historical_adoption | [100: コーシャン](pokemon/100.md) | [551: どくびし](moves/551.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1129 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [101: プラズン](pokemon/101.md) | [551: どくびし](moves/551.md) | {"order":"31","route":"egg"} | egg_moves_final.csv:1160 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [101: プラズン](pokemon/101.md) | [268: じゅうでん](moves/268.md) | {"order":"32","route":"egg"} | egg_moves_final.csv:1161 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [102: ボルトック](pokemon/102.md) | [551: どくびし](moves/551.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1162 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [102: ボルトック](pokemon/102.md) | [268: じゅうでん](moves/268.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:1163 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [103: カワラベ](pokemon/103.md) | [710: アクアリング](moves/710.md) | {"order":"23","route":"egg"} | egg_moves_final.csv:1186 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [104: テペトラー](pokemon/104.md) | [710: アクアリング](moves/710.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1187 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [104: テペトラー](pokemon/104.md) | [241: にほんばれ](moves/241.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:1188 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [105: ロップル](pokemon/105.md) | [710: アクアリング](moves/710.md) | {"order":"28","route":"egg"} | egg_moves_final.csv:1216 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [105: ロップル](pokemon/105.md) | [483: はねやすめ](moves/483.md) | {"order":"29","route":"egg"} | egg_moves_final.csv:1217 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [106: オタクン](pokemon/106.md) | [113: ひかりのかべ](moves/113.md) | {"order":"32","route":"egg"} | egg_moves_final.csv:1249 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [107: ネラー](pokemon/107.md) | [113: ひかりのかべ](moves/113.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1250 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [108: ニートン](pokemon/108.md) | [113: ひかりのかべ](moves/113.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1251 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [111: ハクタクン](pokemon/111.md) | [191: まきびし](moves/191.md) | {"order":"28","route":"egg"} | egg_moves_final.csv:1309 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [121: スミロドン](pokemon/121.md) | [650: オーロラベール](moves/650.md) | {"order":"23","route":"egg"} | egg_moves_final.csv:1442 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [122: マカドゥス](pokemon/122.md) | [201: すなあらし](moves/201.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1443 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [122: マカドゥス](pokemon/122.md) | [268: じゅうでん](moves/268.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:1444 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [134: ラグーン](pokemon/134.md) | [184: こわいかお](moves/184.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1554 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [134: ラグーン](pokemon/134.md) | [710: アクアリング](moves/710.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:1555 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [135: ドラドーン](pokemon/135.md) | [184: こわいかお](moves/184.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1556 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [135: ドラドーン](pokemon/135.md) | [710: アクアリング](moves/710.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:1557 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [142: ライラプス](pokemon/142.md) | [650: オーロラベール](moves/650.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1558 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [142: ライラプス](pokemon/142.md) | [387: わるだくみ](moves/387.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:1559 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [143: ガニメデ](pokemon/143.md) | [650: オーロラベール](moves/650.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1560 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [143: ガニメデ](pokemon/143.md) | [268: じゅうでん](moves/268.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:1561 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [144: ネメア](pokemon/144.md) | [241: にほんばれ](moves/241.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1562 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [144: ネメア](pokemon/144.md) | [387: わるだくみ](moves/387.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:1563 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [161: バジール](pokemon/161.md) | [551: どくびし](moves/551.md) | {"order":"26","route":"egg"} | egg_moves_final.csv:1676 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [162: バジルス](pokemon/162.md) | [235: こうごうせい](moves/235.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1677 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [162: バジルス](pokemon/162.md) | [551: どくびし](moves/551.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:1678 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [163: バジリール](pokemon/163.md) | [235: こうごうせい](moves/235.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1679 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [163: バジリール](pokemon/163.md) | [551: どくびし](moves/551.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:1680 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [165: コマレオ](pokemon/165.md) | [241: にほんばれ](moves/241.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1703 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [166: コマレオン](pokemon/166.md) | [241: にほんばれ](moves/241.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1704 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [166: コマレオン](pokemon/166.md) | [197: みきり](moves/197.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:1705 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [167: トッコウオ](pokemon/167.md) | [710: アクアリング](moves/710.md) | {"order":"23","route":"egg"} | egg_moves_final.csv:1728 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [168: ボウソウオ](pokemon/168.md) | [710: アクアリング](moves/710.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1729 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [169: バクソウオ](pokemon/169.md) | [710: アクアリング](moves/710.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1730 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [169: バクソウオ](pokemon/169.md) | [113: ひかりのかべ](moves/113.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:1731 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [170: チェキラ](pokemon/170.md) | [281: あくび](moves/281.md) | {"order":"35","route":"egg"} | egg_moves_final.csv:1766 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [171: チェキッド](pokemon/171.md) | [281: あくび](moves/281.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1767 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [172: チェキラス](pokemon/172.md) | [281: あくび](moves/281.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1768 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [173: リバード](pokemon/173.md) | [281: あくび](moves/281.md) | {"order":"24","route":"egg"} | egg_moves_final.csv:1792 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [173: リバード](pokemon/173.md) | [483: はねやすめ](moves/483.md) | {"order":"25","route":"egg"} | egg_moves_final.csv:1793 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [174: ララミンゴ](pokemon/174.md) | [483: はねやすめ](moves/483.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1794 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [174: ララミンゴ](pokemon/174.md) | [710: アクアリング](moves/710.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:1795 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [176: パチリック](pokemon/176.md) | [710: アクアリング](moves/710.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1824 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [176: パチリック](pokemon/176.md) | [268: じゅうでん](moves/268.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:1825 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [177: パンプリー](pokemon/177.md) | [194: みちづれ](moves/194.md) | {"order":"31","route":"egg"} | egg_moves_final.csv:1856 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [178: パンプッチ](pokemon/178.md) | [194: みちづれ](moves/194.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1857 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [178: パンプッチ](pokemon/178.md) | [235: こうごうせい](moves/235.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:1858 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [179: ルナビット](pokemon/179.md) | [113: ひかりのかべ](moves/113.md) | {"order":"29","route":"egg"} | egg_moves_final.csv:1887 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [180: ルナバイン](pokemon/180.md) | [113: ひかりのかべ](moves/113.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1888 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [180: ルナバイン](pokemon/180.md) | [387: わるだくみ](moves/387.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:1889 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [181: ウソギー](pokemon/181.md) | [710: アクアリング](moves/710.md) | {"order":"30","route":"egg"} | egg_moves_final.csv:1919 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [182: ウソドロ](pokemon/182.md) | [710: アクアリング](moves/710.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1920 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [182: ウソドロ](pokemon/182.md) | [387: わるだくみ](moves/387.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:1921 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [186: レジュリア](pokemon/186.md) | [650: オーロラベール](moves/650.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1952 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [187: タダヌキ](pokemon/187.md) | [281: あくび](moves/281.md) | {"order":"28","route":"egg"} | egg_moves_final.csv:1980 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [188: オオムジナ](pokemon/188.md) | [281: あくび](moves/281.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1981 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [189: ポコキング](pokemon/189.md) | [281: あくび](moves/281.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1982 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [190: アスイーツ](pokemon/190.md) | [650: オーロラベール](moves/650.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:1983 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [191: コユキムシ](pokemon/191.md) | [650: オーロラベール](moves/650.md) | {"order":"31","route":"egg"} | egg_moves_final.csv:2014 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [192: ユキタテハ](pokemon/192.md) | [650: オーロラベール](moves/650.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2015 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [192: ユキタテハ](pokemon/192.md) | [81: いとをはく](moves/81.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:2016 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [194: オオペラー](pokemon/194.md) | [483: はねやすめ](moves/483.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2042 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [196: ランペルン](pokemon/196.md) | [194: みちづれ](moves/194.md) | {"order":"30","route":"egg"} | egg_moves_final.csv:2101 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [197: キーボン](pokemon/197.md) | [194: みちづれ](moves/194.md) | {"order":"30","route":"egg"} | egg_moves_final.csv:2131 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [200: レディバル](pokemon/200.md) | [81: いとをはく](moves/81.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2161 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [200: レディバル](pokemon/200.md) | [197: みきり](moves/197.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:2162 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [202: ケンタル](pokemon/202.md) | [281: あくび](moves/281.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2164 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [206: アスリスク](pokemon/206.md) | [194: みちづれ](moves/194.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2170 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [207: プラネム](pokemon/207.md) | [113: ひかりのかべ](moves/113.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2171 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [208: モドラ](pokemon/208.md) | [184: こわいかお](moves/184.md) | {"order":"29","route":"egg"} | egg_moves_final.csv:2200 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [209: コモラゴン](pokemon/209.md) | [184: こわいかお](moves/184.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2201 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [209: コモラゴン](pokemon/209.md) | [197: みきり](moves/197.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:2202 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [214: ヤミクラゲ](pokemon/214.md) | [710: アクアリング](moves/710.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2256 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [214: ヤミクラゲ](pokemon/214.md) | [387: わるだくみ](moves/387.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:2257 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [216: オオイナリ](pokemon/216.md) | [241: にほんばれ](moves/241.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2283 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [217: キャンペル](pokemon/217.md) | [194: みちづれ](moves/194.md) | {"order":"29","route":"egg"} | egg_moves_final.csv:2312 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [218: ホムロソク](pokemon/218.md) | [194: みちづれ](moves/194.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2313 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [218: ホムロソク](pokemon/218.md) | [241: にほんばれ](moves/241.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:2314 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [219: ガレキダマ](pokemon/219.md) | [194: みちづれ](moves/194.md) | {"order":"24","route":"egg"} | egg_moves_final.csv:2338 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [220: ジバクン](pokemon/220.md) | [201: すなあらし](moves/201.md) | {"order":"31","route":"egg"} | egg_moves_final.csv:2369 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [220: ジバクン](pokemon/220.md) | [194: みちづれ](moves/194.md) | {"order":"32","route":"egg"} | egg_moves_final.csv:2370 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [221: ワラコゾウ](pokemon/221.md) | [191: まきびし](moves/191.md) | {"order":"31","route":"egg"} | egg_moves_final.csv:2401 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [222: ワラガシラ](pokemon/222.md) | [191: まきびし](moves/191.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2402 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [222: ワラガシラ](pokemon/222.md) | [483: はねやすめ](moves/483.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:2403 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [225: ドルマイン](pokemon/225.md) | [763: ボディプレス](moves/763.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2406 | True | &#91;"egg","machine"&#93; | False |
| vega_to_official_historical_adoption | [233: プカスカ](pokemon/233.md) | [268: じゅうでん](moves/268.md) | {"order":"24","route":"egg"} | egg_moves_final.csv:2523 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [233: プカスカ](pokemon/233.md) | [483: はねやすめ](moves/483.md) | {"order":"25","route":"egg"} | egg_moves_final.csv:2524 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [234: スモーガス](pokemon/234.md) | [268: じゅうでん](moves/268.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2525 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [234: スモーガス](pokemon/234.md) | [551: どくびし](moves/551.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:2526 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [235: ココロン](pokemon/235.md) | [235: こうごうせい](moves/235.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2527 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [236: カモドック](pokemon/236.md) | [235: こうごうせい](moves/235.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2528 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [237: トノッパー](pokemon/237.md) | [710: アクアリング](moves/710.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2529 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [238: ガルラーダ](pokemon/238.md) | [710: アクアリング](moves/710.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2530 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [238: ガルラーダ](pokemon/238.md) | [197: みきり](moves/197.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:2531 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [239: ハサーガ](pokemon/239.md) | [197: みきり](moves/197.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2532 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [239: ハサーガ](pokemon/239.md) | [763: ボディプレス](moves/763.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:2533 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [240: アメクジ](pokemon/240.md) | [710: アクアリング](moves/710.md) | {"order":"28","route":"egg"} | egg_moves_final.csv:2561 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [241: アメリシア](pokemon/241.md) | [710: アクアリング](moves/710.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2562 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [241: アメリシア](pokemon/241.md) | [551: どくびし](moves/551.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:2563 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [242: カララン](pokemon/242.md) | [235: こうごうせい](moves/235.md) | {"order":"26","route":"egg"} | egg_moves_final.csv:2589 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [243: カンカーン](pokemon/243.md) | [281: あくび](moves/281.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2590 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [243: カンカーン](pokemon/243.md) | [235: こうごうせい](moves/235.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:2591 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [244: クラウン](pokemon/244.md) | [281: あくび](moves/281.md) | {"order":"29","route":"egg"} | egg_moves_final.csv:2620 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [245: テイルーン](pokemon/245.md) | [281: あくび](moves/281.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2621 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [245: テイルーン](pokemon/245.md) | [483: はねやすめ](moves/483.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:2622 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [246: モグルトン](pokemon/246.md) | [281: あくび](moves/281.md) | {"order":"28","route":"egg"} | egg_moves_final.csv:2650 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [246: モグルトン](pokemon/246.md) | [191: まきびし](moves/191.md) | {"order":"29","route":"egg"} | egg_moves_final.csv:2651 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [251: ラクチャン](pokemon/251.md) | [281: あくび](moves/281.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2715 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [277: ドゴン](pokemon/277.md) | [281: あくび](moves/281.md) | {"order":"25","route":"egg"} | egg_moves_final.csv:2742 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [277: ドゴン](pokemon/277.md) | [197: みきり](moves/197.md) | {"order":"26","route":"egg"} | egg_moves_final.csv:2743 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [279: トコヤミ](pokemon/279.md) | [387: わるだくみ](moves/387.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2777 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [279: トコヤミ](pokemon/279.md) | [483: はねやすめ](moves/483.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:2778 | True | &#91;"egg","tutor"&#93; | False |
| vega_to_official_historical_adoption | [281: クチールス](pokemon/281.md) | [650: オーロラベール](moves/650.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2814 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [281: クチールス](pokemon/281.md) | [387: わるだくみ](moves/387.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:2815 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [285: ガッツロス](pokemon/285.md) | [197: みきり](moves/197.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2864 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [288: アーボスク](pokemon/288.md) | [551: どくびし](moves/551.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2893 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [288: アーボスク](pokemon/288.md) | [387: わるだくみ](moves/387.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:2894 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [291: モアドガス](pokemon/291.md) | [551: どくびし](moves/551.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:2922 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [291: モアドガス](pokemon/291.md) | [241: にほんばれ](moves/241.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:2923 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [304: マグッピ](pokemon/304.md) | [710: アクアリング](moves/710.md) | {"order":"31","route":"egg"} | egg_moves_final.csv:3099 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [305: ベタデーム](pokemon/305.md) | [710: アクアリング](moves/710.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3100 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [306: テッコンボ](pokemon/306.md) | [197: みきり](moves/197.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3101 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [307: ボンバット](pokemon/307.md) | [551: どくびし](moves/551.md) | {"order":"30","route":"egg"} | egg_moves_final.csv:3131 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [307: ボンバット](pokemon/307.md) | [483: はねやすめ](moves/483.md) | {"order":"31","route":"egg"} | egg_moves_final.csv:3132 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [310: ダンカンス](pokemon/310.md) | [281: あくび](moves/281.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3203 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [310: ダンカンス](pokemon/310.md) | [235: こうごうせい](moves/235.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:3204 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [311: ドサーモン](pokemon/311.md) | [197: みきり](moves/197.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3205 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [311: ドサーモン](pokemon/311.md) | [710: アクアリング](moves/710.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:3206 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [312: テッケン](pokemon/312.md) | [197: みきり](moves/197.md) | {"order":"28","route":"egg"} | egg_moves_final.csv:3234 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [320: ヒョウカク](pokemon/320.md) | [268: じゅうでん](moves/268.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3348 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [320: ヒョウカク](pokemon/320.md) | [650: オーロラベール](moves/650.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:3349 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [323: プレシオン](pokemon/323.md) | [281: あくび](moves/281.md) | {"order":"34","route":"egg"} | egg_moves_final.csv:3387 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [323: プレシオン](pokemon/323.md) | [710: アクアリング](moves/710.md) | {"order":"35","route":"egg"} | egg_moves_final.csv:3388 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [326: メルリコ](pokemon/326.md) | [710: アクアリング](moves/710.md) | {"order":"29","route":"egg"} | egg_moves_final.csv:3420 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [327: サムラダケ](pokemon/327.md) | [235: こうごうせい](moves/235.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3421 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [328: ブレイドン](pokemon/328.md) | [197: みきり](moves/197.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3422 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [329: ブレイオー](pokemon/329.md) | [197: みきり](moves/197.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3423 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [329: ブレイオー](pokemon/329.md) | [763: ボディプレス](moves/763.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:3424 | True | &#91;"egg","machine"&#93; | False |
| vega_to_official_historical_adoption | [333: アルデッパ](pokemon/333.md) | [191: まきびし](moves/191.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3486 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [333: アルデッパ](pokemon/333.md) | [241: にほんばれ](moves/241.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:3487 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [334: ゴキブロス](pokemon/334.md) | [387: わるだくみ](moves/387.md) | {"order":"27","route":"egg"} | egg_moves_final.csv:3514 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [335: ビビッドン](pokemon/335.md) | [710: アクアリング](moves/710.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3515 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [335: ビビッドン](pokemon/335.md) | [268: じゅうでん](moves/268.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:3516 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [336: ドルン](pokemon/336.md) | [268: じゅうでん](moves/268.md) | {"order":"27","route":"egg"} | egg_moves_final.csv:3543 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [337: バーネッコ](pokemon/337.md) | [241: にほんばれ](moves/241.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3544 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [338: コケゾー](pokemon/338.md) | [235: こうごうせい](moves/235.md) | {"order":"22","route":"egg"} | egg_moves_final.csv:3566 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [339: オンネット](pokemon/339.md) | [387: わるだくみ](moves/387.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3567 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [342: ノコウテイ](pokemon/342.md) | [281: あくび](moves/281.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3630 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [344: カミギリー](pokemon/344.md) | [81: いとをはく](moves/81.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3660 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [344: カミギリー](pokemon/344.md) | [763: ボディプレス](moves/763.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:3661 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [345: レファン](pokemon/345.md) | [281: あくび](moves/281.md) | {"order":"32","route":"egg"} | egg_moves_final.csv:3693 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [347: ストータス](pokemon/347.md) | [483: はねやすめ](moves/483.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3718 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [349: ラブリン](pokemon/349.md) | [281: あくび](moves/281.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3740 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [350: オールガ](pokemon/350.md) | [268: じゅうでん](moves/268.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3741 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [353: ヒカリゴケ](pokemon/353.md) | [235: こうごうせい](moves/235.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3773 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [353: ヒカリゴケ](pokemon/353.md) | [268: じゅうでん](moves/268.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:3774 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [356: セルディー](pokemon/356.md) | [650: オーロラベール](moves/650.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3778 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [358: ガネーシャ](pokemon/358.md) | [191: まきびし](moves/191.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3805 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [360: プレゼンタ](pokemon/360.md) | [650: オーロラベール](moves/650.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3807 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [372: サンドリル](pokemon/372.md) | [191: まきびし](moves/191.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3916 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [373: カモナイツ](pokemon/373.md) | [483: はねやすめ](moves/483.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:3917 | True | &#91;"egg","tutor"&#93; | False |
| vega_to_official_historical_adoption | [373: カモナイツ](pokemon/373.md) | [197: みきり](moves/197.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:3918 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [382: キルギシア](pokemon/382.md) | [387: わるだくみ](moves/387.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:4034 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [382: キルギシア](pokemon/382.md) | [763: ボディプレス](moves/763.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:4035 | True | &#91;"egg","machine"&#93; | False |
| vega_to_official_historical_adoption | [383: シルドール](pokemon/383.md) | [387: わるだくみ](moves/387.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:4036 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [383: シルドール](pokemon/383.md) | [763: ボディプレス](moves/763.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:4037 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [384: セルシィ](pokemon/384.md) | [650: オーロラベール](moves/650.md) | {"order":"31","route":"egg"} | egg_moves_final.csv:4068 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [385: テルテン](pokemon/385.md) | [281: あくび](moves/281.md) | {"order":"29","route":"egg"} | egg_moves_final.csv:4097 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [386: ワークロ](pokemon/386.md) | [387: わるだくみ](moves/387.md) | {"order":"29","route":"egg"} | egg_moves_final.csv:4126 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [386: ワークロ](pokemon/386.md) | [483: はねやすめ](moves/483.md) | {"order":"30","route":"egg"} | egg_moves_final.csv:4127 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [387: アリンセス](pokemon/387.md) | [81: いとをはく](moves/81.md) | {"order":"29","route":"egg"} | egg_moves_final.csv:4156 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [388: ティオルス](pokemon/388.md) | [184: こわいかお](moves/184.md) | {"order":"26","route":"egg"} | egg_moves_final.csv:4182 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [389: プテリクス](pokemon/389.md) | [184: こわいかお](moves/184.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:4183 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [389: プテリクス](pokemon/389.md) | [483: はねやすめ](moves/483.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:4184 | True | &#91;"egg","level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [390: ティラノス](pokemon/390.md) | [184: こわいかお](moves/184.md) | {"order":"37","route":"egg"} | egg_moves_final.csv:4221 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [391: ブレイバー](pokemon/391.md) | [197: みきり](moves/197.md) | {"order":"32","route":"egg"} | egg_moves_final.csv:4253 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [392: ヤマネツ](pokemon/392.md) | [235: こうごうせい](moves/235.md) | {"order":"26","route":"egg"} | egg_moves_final.csv:4279 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [393: ヒササビ](pokemon/393.md) | [268: じゅうでん](moves/268.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:4280 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [393: ヒササビ](pokemon/393.md) | [483: はねやすめ](moves/483.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:4281 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [394: シャーモン](pokemon/394.md) | [197: みきり](moves/197.md) | {"order":"22","route":"egg"} | egg_moves_final.csv:4303 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [400: ロイツァー](pokemon/400.md) | [710: アクアリング](moves/710.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:4362 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [401: ガタノア](pokemon/401.md) | [710: アクアリング](moves/710.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:4363 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [401: ガタノア](pokemon/401.md) | [113: ひかりのかべ](moves/113.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:4364 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [402: テツカブリ](pokemon/402.md) | [710: アクアリング](moves/710.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:4365 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [402: テツカブリ](pokemon/402.md) | [763: ボディプレス](moves/763.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:4366 | True | &#91;"egg","tutor"&#93; | False |
| vega_to_official_historical_adoption | [406: オルディナ](pokemon/406.md) | [387: わるだくみ](moves/387.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:4367 | True | &#91;"egg","level_up"&#93; | False |
| vega_to_official_historical_adoption | [409: オルマリア](pokemon/409.md) | [387: わるだくみ](moves/387.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:4368 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [410: アスフィア](pokemon/410.md) | [387: わるだくみ](moves/387.md) | {"order":"1","route":"egg"} | egg_moves_final.csv:4369 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [410: アスフィア](pokemon/410.md) | [184: こわいかお](moves/184.md) | {"order":"2","route":"egg"} | egg_moves_final.csv:4370 | True | &#91;"egg"&#93; | False |
| vega_to_official_historical_adoption | [1: リープン](pokemon/1.md) | [408: くさむすび](moves/408.md) | {"compatible":"true","route":"machine","slot_key":"TM_071","slot_no":"71","slot_type":"TM"} | tm_tutor_changes.csv:2 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [1: リープン](pokemon/1.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:3 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [2: リーティン](pokemon/2.md) | [408: くさむすび](moves/408.md) | {"compatible":"true","route":"machine","slot_key":"TM_071","slot_no":"71","slot_type":"TM"} | tm_tutor_changes.csv:4 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [2: リーティン](pokemon/2.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:5 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [3: リーテイル](pokemon/3.md) | [408: くさむすび](moves/408.md) | {"compatible":"true","route":"machine","slot_key":"TM_071","slot_no":"71","slot_type":"TM"} | tm_tutor_changes.csv:6 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [3: リーテイル](pokemon/3.md) | [405: アイアンヘッド](moves/405.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_014","slot_no":"14","slot_type":"TUTOR"} | tm_tutor_changes.csv:7 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [3: リーテイル](pokemon/3.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:8 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [4: ファマー](pokemon/4.md) | [53: かえんほうしゃ](moves/53.md) | {"compatible":"true","route":"machine","slot_key":"TM_092","slot_no":"92","slot_type":"TM"} | tm_tutor_changes.csv:9 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [4: ファマー](pokemon/4.md) | [257: ねっぷう](moves/257.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_016","slot_no":"16","slot_type":"TUTOR"} | tm_tutor_changes.csv:10 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [5: ファイマー](pokemon/5.md) | [257: ねっぷう](moves/257.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_016","slot_no":"16","slot_type":"TUTOR"} | tm_tutor_changes.csv:11 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [6: ファマイン](pokemon/6.md) | [520: バークアウト](moves/520.md) | {"compatible":"true","route":"machine","slot_key":"TM_066","slot_no":"66","slot_type":"TM"} | tm_tutor_changes.csv:12 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [6: ファマイン](pokemon/6.md) | [53: かえんほうしゃ](moves/53.md) | {"compatible":"true","route":"machine","slot_key":"TM_092","slot_no":"92","slot_type":"TM"} | tm_tutor_changes.csv:13 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [6: ファマイン](pokemon/6.md) | [282: はたきおとす](moves/282.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_006","slot_no":"6","slot_type":"TUTOR"} | tm_tutor_changes.csv:14 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [6: ファマイン](pokemon/6.md) | [257: ねっぷう](moves/257.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_016","slot_no":"16","slot_type":"TUTOR"} | tm_tutor_changes.csv:15 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [7: アクタシ](pokemon/7.md) | [667: アクアブレイク](moves/667.md) | {"compatible":"true","route":"machine","slot_key":"TM_082","slot_no":"82","slot_type":"TM"} | tm_tutor_changes.csv:16 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [7: アクタシ](pokemon/7.md) | [799: クイックターン](moves/799.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_060","slot_no":"60","slot_type":"TUTOR"} | tm_tutor_changes.csv:17 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [8: レクオレ](pokemon/8.md) | [667: アクアブレイク](moves/667.md) | {"compatible":"true","route":"machine","slot_key":"TM_082","slot_no":"82","slot_type":"TM"} | tm_tutor_changes.csv:18 | True | &#91;"level_up","machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [8: レクオレ](pokemon/8.md) | [799: クイックターン](moves/799.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_060","slot_no":"60","slot_type":"TUTOR"} | tm_tutor_changes.csv:19 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [9: タテボーシ](pokemon/9.md) | [579: サイコショック](moves/579.md) | {"compatible":"true","route":"machine","slot_key":"TM_075","slot_no":"75","slot_type":"TM"} | tm_tutor_changes.csv:20 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [9: タテボーシ](pokemon/9.md) | [271: トリック](moves/271.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_008","slot_no":"8","slot_type":"TUTOR"} | tm_tutor_changes.csv:21 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [9: タテボーシ](pokemon/9.md) | [799: クイックターン](moves/799.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_060","slot_no":"60","slot_type":"TUTOR"} | tm_tutor_changes.csv:22 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [21: フロン](pokemon/21.md) | [408: くさむすび](moves/408.md) | {"compatible":"true","route":"machine","slot_key":"TM_071","slot_no":"71","slot_type":"TM"} | tm_tutor_changes.csv:43 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [21: フロン](pokemon/21.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:44 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [22: フロルル](pokemon/22.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:45 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [23: フローリア](pokemon/23.md) | [408: くさむすび](moves/408.md) | {"compatible":"true","route":"machine","slot_key":"TM_071","slot_no":"71","slot_type":"TM"} | tm_tutor_changes.csv:46 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [23: フローリア](pokemon/23.md) | [579: サイコショック](moves/579.md) | {"compatible":"true","route":"machine","slot_key":"TM_075","slot_no":"75","slot_type":"TM"} | tm_tutor_changes.csv:47 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [23: フローリア](pokemon/23.md) | [271: トリック](moves/271.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_008","slot_no":"8","slot_type":"TUTOR"} | tm_tutor_changes.csv:48 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [23: フローリア](pokemon/23.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:49 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [27: ゴリチュウ](pokemon/27.md) | [531: ボルトチェンジ](moves/531.md) | {"compatible":"true","route":"machine","slot_key":"TM_063","slot_no":"63","slot_type":"TM"} | tm_tutor_changes.csv:55 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [27: ゴリチュウ](pokemon/27.md) | [379: ドレインパンチ](moves/379.md) | {"compatible":"true","route":"machine","slot_key":"TM_074","slot_no":"74","slot_type":"TM"} | tm_tutor_changes.csv:56 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [37: ララベリー](pokemon/37.md) | [408: くさむすび](moves/408.md) | {"compatible":"true","route":"machine","slot_key":"TM_071","slot_no":"71","slot_type":"TM"} | tm_tutor_changes.csv:74 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [37: ララベリー](pokemon/37.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:75 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [38: セラーナ](pokemon/38.md) | [408: くさむすび](moves/408.md) | {"compatible":"true","route":"machine","slot_key":"TM_071","slot_no":"71","slot_type":"TM"} | tm_tutor_changes.csv:76 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [38: セラーナ](pokemon/38.md) | [579: サイコショック](moves/579.md) | {"compatible":"true","route":"machine","slot_key":"TM_075","slot_no":"75","slot_type":"TM"} | tm_tutor_changes.csv:77 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [38: セラーナ](pokemon/38.md) | [271: トリック](moves/271.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_008","slot_no":"8","slot_type":"TUTOR"} | tm_tutor_changes.csv:78 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [38: セラーナ](pokemon/38.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:79 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [43: マホース](pokemon/43.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:85 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [43: マホース](pokemon/43.md) | [270: てだすけ](moves/270.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_009","slot_no":"9","slot_type":"TUTOR"} | tm_tutor_changes.csv:86 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [44: ペガーン](pokemon/44.md) | [528: アクロバット](moves/528.md) | {"compatible":"true","route":"machine","slot_key":"TM_069","slot_no":"69","slot_type":"TM"} | tm_tutor_changes.csv:87 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [45: ユニサス](pokemon/45.md) | [528: アクロバット](moves/528.md) | {"compatible":"true","route":"machine","slot_key":"TM_069","slot_no":"69","slot_type":"TM"} | tm_tutor_changes.csv:88 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [45: ユニサス](pokemon/45.md) | [270: てだすけ](moves/270.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_009","slot_no":"9","slot_type":"TUTOR"} | tm_tutor_changes.csv:89 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [50: ライノス](pokemon/50.md) | [495: じならし](moves/495.md) | {"compatible":"true","route":"machine","slot_key":"TM_065","slot_no":"65","slot_type":"TM"} | tm_tutor_changes.csv:95 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [50: ライノス](pokemon/50.md) | [771: ワイドブレイカー](moves/771.md) | {"compatible":"true","route":"machine","slot_key":"TM_103","slot_no":"103","slot_type":"TM"} | tm_tutor_changes.csv:96 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [50: ライノス](pokemon/50.md) | [399: りゅうせいぐん](moves/399.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_001","slot_no":"1","slot_type":"TUTOR"} | tm_tutor_changes.csv:97 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [51: メタゲラス](pokemon/51.md) | [495: じならし](moves/495.md) | {"compatible":"true","route":"machine","slot_key":"TM_065","slot_no":"65","slot_type":"TM"} | tm_tutor_changes.csv:98 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [51: メタゲラス](pokemon/51.md) | [405: アイアンヘッド](moves/405.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_014","slot_no":"14","slot_type":"TUTOR"} | tm_tutor_changes.csv:99 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [53: ディザソル](pokemon/53.md) | [520: バークアウト](moves/520.md) | {"compatible":"true","route":"machine","slot_key":"TM_066","slot_no":"66","slot_type":"TM"} | tm_tutor_changes.csv:102 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [55: フォリキー](pokemon/55.md) | [579: サイコショック](moves/579.md) | {"compatible":"true","route":"machine","slot_key":"TM_075","slot_no":"75","slot_type":"TM"} | tm_tutor_changes.csv:106 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [55: フォリキー](pokemon/55.md) | [271: トリック](moves/271.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_008","slot_no":"8","slot_type":"TUTOR"} | tm_tutor_changes.csv:107 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [56: バーニン](pokemon/56.md) | [579: サイコショック](moves/579.md) | {"compatible":"true","route":"machine","slot_key":"TM_075","slot_no":"75","slot_type":"TM"} | tm_tutor_changes.csv:108 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [56: バーニン](pokemon/56.md) | [53: かえんほうしゃ](moves/53.md) | {"compatible":"true","route":"machine","slot_key":"TM_092","slot_no":"92","slot_type":"TM"} | tm_tutor_changes.csv:109 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [56: バーニン](pokemon/56.md) | [271: トリック](moves/271.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_008","slot_no":"8","slot_type":"TUTOR"} | tm_tutor_changes.csv:110 | True | &#91;"egg","tutor"&#93; | False |
| vega_to_official_historical_adoption | [56: バーニン](pokemon/56.md) | [257: ねっぷう](moves/257.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_016","slot_no":"16","slot_type":"TUTOR"} | tm_tutor_changes.csv:111 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [57: ファントマ](pokemon/57.md) | [391: シャドークロー](moves/391.md) | {"compatible":"true","route":"machine","slot_key":"TM_011","slot_no":"11","slot_type":"TM"} | tm_tutor_changes.csv:112 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [57: ファントマ](pokemon/57.md) | [579: サイコショック](moves/579.md) | {"compatible":"true","route":"machine","slot_key":"TM_075","slot_no":"75","slot_type":"TM"} | tm_tutor_changes.csv:113 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [57: ファントマ](pokemon/57.md) | [271: トリック](moves/271.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_008","slot_no":"8","slot_type":"TUTOR"} | tm_tutor_changes.csv:114 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [68: テディ](pokemon/68.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:137 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [68: テディ](pokemon/68.md) | [270: てだすけ](moves/270.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_009","slot_no":"9","slot_type":"TUTOR"} | tm_tutor_changes.csv:138 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [69: ググズリー](pokemon/69.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:139 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [69: ググズリー](pokemon/69.md) | [520: バークアウト](moves/520.md) | {"compatible":"true","route":"machine","slot_key":"TM_066","slot_no":"66","slot_type":"TM"} | tm_tutor_changes.csv:140 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [69: ググズリー](pokemon/69.md) | [282: はたきおとす](moves/282.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_006","slot_no":"6","slot_type":"TUTOR"} | tm_tutor_changes.csv:141 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [69: ググズリー](pokemon/69.md) | [270: てだすけ](moves/270.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_009","slot_no":"9","slot_type":"TUTOR"} | tm_tutor_changes.csv:142 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [70: ハンタマ](pokemon/70.md) | [391: シャドークロー](moves/391.md) | {"compatible":"true","route":"machine","slot_key":"TM_011","slot_no":"11","slot_type":"TM"} | tm_tutor_changes.csv:143 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [70: ハンタマ](pokemon/70.md) | [520: バークアウト](moves/520.md) | {"compatible":"true","route":"machine","slot_key":"TM_066","slot_no":"66","slot_type":"TM"} | tm_tutor_changes.csv:144 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [70: ハンタマ](pokemon/70.md) | [796: ポルターガイスト](moves/796.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_054","slot_no":"54","slot_type":"TUTOR"} | tm_tutor_changes.csv:145 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [81: ダンゴロウ](pokemon/81.md) | [667: アクアブレイク](moves/667.md) | {"compatible":"true","route":"machine","slot_key":"TM_082","slot_no":"82","slot_type":"TM"} | tm_tutor_changes.csv:168 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [81: ダンゴロウ](pokemon/81.md) | [799: クイックターン](moves/799.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_060","slot_no":"60","slot_type":"TUTOR"} | tm_tutor_changes.csv:169 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [82: マルマジロ](pokemon/82.md) | [667: アクアブレイク](moves/667.md) | {"compatible":"true","route":"machine","slot_key":"TM_082","slot_no":"82","slot_type":"TM"} | tm_tutor_changes.csv:170 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [82: マルマジロ](pokemon/82.md) | [405: アイアンヘッド](moves/405.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_014","slot_no":"14","slot_type":"TUTOR"} | tm_tutor_changes.csv:171 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [82: マルマジロ](pokemon/82.md) | [799: クイックターン](moves/799.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_060","slot_no":"60","slot_type":"TUTOR"} | tm_tutor_changes.csv:172 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [83: アロフィー](pokemon/83.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:173 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [83: アロフィー](pokemon/83.md) | [799: クイックターン](moves/799.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_060","slot_no":"60","slot_type":"TUTOR"} | tm_tutor_changes.csv:174 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [84: リーフィス](pokemon/84.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:175 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [87: ユカリア](pokemon/87.md) | [579: サイコショック](moves/579.md) | {"compatible":"true","route":"machine","slot_key":"TM_075","slot_no":"75","slot_type":"TM"} | tm_tutor_changes.csv:183 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [87: ユカリア](pokemon/87.md) | [271: トリック](moves/271.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_008","slot_no":"8","slot_type":"TUTOR"} | tm_tutor_changes.csv:184 | True | &#91;"egg","tutor"&#93; | False |
| vega_to_official_historical_adoption | [88: ネクロシア](pokemon/88.md) | [391: シャドークロー](moves/391.md) | {"compatible":"true","route":"machine","slot_key":"TM_011","slot_no":"11","slot_type":"TM"} | tm_tutor_changes.csv:185 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [88: ネクロシア](pokemon/88.md) | [796: ポルターガイスト](moves/796.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_054","slot_no":"54","slot_type":"TUTOR"} | tm_tutor_changes.csv:186 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [89: カプリン](pokemon/89.md) | [579: サイコショック](moves/579.md) | {"compatible":"true","route":"machine","slot_key":"TM_075","slot_no":"75","slot_type":"TM"} | tm_tutor_changes.csv:187 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [90: ゴートン](pokemon/90.md) | [579: サイコショック](moves/579.md) | {"compatible":"true","route":"machine","slot_key":"TM_075","slot_no":"75","slot_type":"TM"} | tm_tutor_changes.csv:188 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [91: バフォット](pokemon/91.md) | [520: バークアウト](moves/520.md) | {"compatible":"true","route":"machine","slot_key":"TM_066","slot_no":"66","slot_type":"TM"} | tm_tutor_changes.csv:189 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [91: バフォット](pokemon/91.md) | [579: サイコショック](moves/579.md) | {"compatible":"true","route":"machine","slot_key":"TM_075","slot_no":"75","slot_type":"TM"} | tm_tutor_changes.csv:190 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [91: バフォット](pokemon/91.md) | [271: トリック](moves/271.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_008","slot_no":"8","slot_type":"TUTOR"} | tm_tutor_changes.csv:191 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [94: バードン](pokemon/94.md) | [554: おいかぜ](moves/554.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_007","slot_no":"7","slot_type":"TUTOR"} | tm_tutor_changes.csv:198 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [95: ゴルドー](pokemon/95.md) | [528: アクロバット](moves/528.md) | {"compatible":"true","route":"machine","slot_key":"TM_069","slot_no":"69","slot_type":"TM"} | tm_tutor_changes.csv:199 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [95: ゴルドー](pokemon/95.md) | [554: おいかぜ](moves/554.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_007","slot_no":"7","slot_type":"TUTOR"} | tm_tutor_changes.csv:200 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [95: ゴルドー](pokemon/95.md) | [405: アイアンヘッド](moves/405.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_014","slot_no":"14","slot_type":"TUTOR"} | tm_tutor_changes.csv:201 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [96: フィニクス](pokemon/96.md) | [528: アクロバット](moves/528.md) | {"compatible":"true","route":"machine","slot_key":"TM_069","slot_no":"69","slot_type":"TM"} | tm_tutor_changes.csv:202 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [96: フィニクス](pokemon/96.md) | [257: ねっぷう](moves/257.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_016","slot_no":"16","slot_type":"TUTOR"} | tm_tutor_changes.csv:203 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [97: クロッチ](pokemon/97.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:204 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [97: クロッチ](pokemon/97.md) | [520: バークアウト](moves/520.md) | {"compatible":"true","route":"machine","slot_key":"TM_066","slot_no":"66","slot_type":"TM"} | tm_tutor_changes.csv:205 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [98: コクジャク](pokemon/98.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:206 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [98: コクジャク](pokemon/98.md) | [528: アクロバット](moves/528.md) | {"compatible":"true","route":"machine","slot_key":"TM_069","slot_no":"69","slot_type":"TM"} | tm_tutor_changes.csv:207 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [98: コクジャク](pokemon/98.md) | [554: おいかぜ](moves/554.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_007","slot_no":"7","slot_type":"TUTOR"} | tm_tutor_changes.csv:208 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [99: シャミネ](pokemon/99.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:209 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [99: シャミネ](pokemon/99.md) | [528: アクロバット](moves/528.md) | {"compatible":"true","route":"machine","slot_key":"TM_069","slot_no":"69","slot_type":"TM"} | tm_tutor_changes.csv:210 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [99: シャミネ](pokemon/99.md) | [554: おいかぜ](moves/554.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_007","slot_no":"7","slot_type":"TUTOR"} | tm_tutor_changes.csv:211 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [99: シャミネ](pokemon/99.md) | [270: てだすけ](moves/270.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_009","slot_no":"9","slot_type":"TUTOR"} | tm_tutor_changes.csv:212 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [100: コーシャン](pokemon/100.md) | [522: ベノムショック](moves/522.md) | {"compatible":"true","route":"machine","slot_key":"TM_070","slot_no":"70","slot_type":"TM"} | tm_tutor_changes.csv:213 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [101: プラズン](pokemon/101.md) | [531: ボルトチェンジ](moves/531.md) | {"compatible":"true","route":"machine","slot_key":"TM_063","slot_no":"63","slot_type":"TM"} | tm_tutor_changes.csv:214 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [101: プラズン](pokemon/101.md) | [404: ダストシュート](moves/404.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_020","slot_no":"20","slot_type":"TUTOR"} | tm_tutor_changes.csv:215 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [101: プラズン](pokemon/101.md) | [489: エレキネット](moves/489.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_029","slot_no":"29","slot_type":"TUTOR"} | tm_tutor_changes.csv:216 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [102: ボルトック](pokemon/102.md) | [531: ボルトチェンジ](moves/531.md) | {"compatible":"true","route":"machine","slot_key":"TM_063","slot_no":"63","slot_type":"TM"} | tm_tutor_changes.csv:217 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [102: ボルトック](pokemon/102.md) | [522: ベノムショック](moves/522.md) | {"compatible":"true","route":"machine","slot_key":"TM_070","slot_no":"70","slot_type":"TM"} | tm_tutor_changes.csv:218 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [102: ボルトック](pokemon/102.md) | [404: ダストシュート](moves/404.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_020","slot_no":"20","slot_type":"TUTOR"} | tm_tutor_changes.csv:219 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [102: ボルトック](pokemon/102.md) | [489: エレキネット](moves/489.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_029","slot_no":"29","slot_type":"TUTOR"} | tm_tutor_changes.csv:220 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [103: カワラベ](pokemon/103.md) | [667: アクアブレイク](moves/667.md) | {"compatible":"true","route":"machine","slot_key":"TM_082","slot_no":"82","slot_type":"TM"} | tm_tutor_changes.csv:221 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [104: テペトラー](pokemon/104.md) | [53: かえんほうしゃ](moves/53.md) | {"compatible":"true","route":"machine","slot_key":"TM_092","slot_no":"92","slot_type":"TM"} | tm_tutor_changes.csv:222 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [104: テペトラー](pokemon/104.md) | [257: ねっぷう](moves/257.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_016","slot_no":"16","slot_type":"TUTOR"} | tm_tutor_changes.csv:223 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [105: ロップル](pokemon/105.md) | [554: おいかぜ](moves/554.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_007","slot_no":"7","slot_type":"TUTOR"} | tm_tutor_changes.csv:224 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [106: オタクン](pokemon/106.md) | [579: サイコショック](moves/579.md) | {"compatible":"true","route":"machine","slot_key":"TM_075","slot_no":"75","slot_type":"TM"} | tm_tutor_changes.csv:225 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [106: オタクン](pokemon/106.md) | [271: トリック](moves/271.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_008","slot_no":"8","slot_type":"TUTOR"} | tm_tutor_changes.csv:226 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [107: ネラー](pokemon/107.md) | [579: サイコショック](moves/579.md) | {"compatible":"true","route":"machine","slot_key":"TM_075","slot_no":"75","slot_type":"TM"} | tm_tutor_changes.csv:227 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [107: ネラー](pokemon/107.md) | [271: トリック](moves/271.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_008","slot_no":"8","slot_type":"TUTOR"} | tm_tutor_changes.csv:228 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [108: ニートン](pokemon/108.md) | [579: サイコショック](moves/579.md) | {"compatible":"true","route":"machine","slot_key":"TM_075","slot_no":"75","slot_type":"TM"} | tm_tutor_changes.csv:229 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [108: ニートン](pokemon/108.md) | [271: トリック](moves/271.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_008","slot_no":"8","slot_type":"TUTOR"} | tm_tutor_changes.csv:230 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [111: ハクタクン](pokemon/111.md) | [495: じならし](moves/495.md) | {"compatible":"true","route":"machine","slot_key":"TM_065","slot_no":"65","slot_type":"TM"} | tm_tutor_changes.csv:237 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [111: ハクタクン](pokemon/111.md) | [802: ねっさのだいち](moves/802.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_051","slot_no":"51","slot_type":"TUTOR"} | tm_tutor_changes.csv:238 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [121: スミロドン](pokemon/121.md) | [800: トリプルアクセル](moves/800.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_052","slot_no":"52","slot_type":"TUTOR"} | tm_tutor_changes.csv:258 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [122: マカドゥス](pokemon/122.md) | [550: ステルスロック](moves/550.md) | {"compatible":"true","route":"machine","slot_key":"TM_061","slot_no":"61","slot_type":"TM"} | tm_tutor_changes.csv:259 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [122: マカドゥス](pokemon/122.md) | [531: ボルトチェンジ](moves/531.md) | {"compatible":"true","route":"machine","slot_key":"TM_063","slot_no":"63","slot_type":"TM"} | tm_tutor_changes.csv:260 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [122: マカドゥス](pokemon/122.md) | [489: エレキネット](moves/489.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_029","slot_no":"29","slot_type":"TUTOR"} | tm_tutor_changes.csv:261 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [122: マカドゥス](pokemon/122.md) | [787: メテオビーム](moves/787.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_047","slot_no":"47","slot_type":"TUTOR"} | tm_tutor_changes.csv:262 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [133: タツゴン](pokemon/133.md) | [771: ワイドブレイカー](moves/771.md) | {"compatible":"true","route":"machine","slot_key":"TM_103","slot_no":"103","slot_type":"TM"} | tm_tutor_changes.csv:300 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [133: タツゴン](pokemon/133.md) | [399: りゅうせいぐん](moves/399.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_001","slot_no":"1","slot_type":"TUTOR"} | tm_tutor_changes.csv:301 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [134: ラグーン](pokemon/134.md) | [667: アクアブレイク](moves/667.md) | {"compatible":"true","route":"machine","slot_key":"TM_082","slot_no":"82","slot_type":"TM"} | tm_tutor_changes.csv:302 | True | &#91;"level_up","machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [134: ラグーン](pokemon/134.md) | [771: ワイドブレイカー](moves/771.md) | {"compatible":"true","route":"machine","slot_key":"TM_103","slot_no":"103","slot_type":"TM"} | tm_tutor_changes.csv:303 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [135: ドラドーン](pokemon/135.md) | [667: アクアブレイク](moves/667.md) | {"compatible":"true","route":"machine","slot_key":"TM_082","slot_no":"82","slot_type":"TM"} | tm_tutor_changes.csv:304 | True | &#91;"level_up","machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [135: ドラドーン](pokemon/135.md) | [771: ワイドブレイカー](moves/771.md) | {"compatible":"true","route":"machine","slot_key":"TM_103","slot_no":"103","slot_type":"TM"} | tm_tutor_changes.csv:305 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [142: ライラプス](pokemon/142.md) | [520: バークアウト](moves/520.md) | {"compatible":"true","route":"machine","slot_key":"TM_066","slot_no":"66","slot_type":"TM"} | tm_tutor_changes.csv:322 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [142: ライラプス](pokemon/142.md) | [282: はたきおとす](moves/282.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_006","slot_no":"6","slot_type":"TUTOR"} | tm_tutor_changes.csv:323 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [142: ライラプス](pokemon/142.md) | [800: トリプルアクセル](moves/800.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_052","slot_no":"52","slot_type":"TUTOR"} | tm_tutor_changes.csv:324 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [143: ガニメデ](pokemon/143.md) | [531: ボルトチェンジ](moves/531.md) | {"compatible":"true","route":"machine","slot_key":"TM_063","slot_no":"63","slot_type":"TM"} | tm_tutor_changes.csv:325 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [144: ネメア](pokemon/144.md) | [520: バークアウト](moves/520.md) | {"compatible":"true","route":"machine","slot_key":"TM_066","slot_no":"66","slot_type":"TM"} | tm_tutor_changes.csv:326 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [144: ネメア](pokemon/144.md) | [53: かえんほうしゃ](moves/53.md) | {"compatible":"true","route":"machine","slot_key":"TM_092","slot_no":"92","slot_type":"TM"} | tm_tutor_changes.csv:327 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [144: ネメア](pokemon/144.md) | [282: はたきおとす](moves/282.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_006","slot_no":"6","slot_type":"TUTOR"} | tm_tutor_changes.csv:328 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [144: ネメア](pokemon/144.md) | [257: ねっぷう](moves/257.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_016","slot_no":"16","slot_type":"TUTOR"} | tm_tutor_changes.csv:329 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [161: バジール](pokemon/161.md) | [408: くさむすび](moves/408.md) | {"compatible":"true","route":"machine","slot_key":"TM_071","slot_no":"71","slot_type":"TM"} | tm_tutor_changes.csv:365 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [161: バジール](pokemon/161.md) | [404: ダストシュート](moves/404.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_020","slot_no":"20","slot_type":"TUTOR"} | tm_tutor_changes.csv:366 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [161: バジール](pokemon/161.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:367 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [162: バジルス](pokemon/162.md) | [408: くさむすび](moves/408.md) | {"compatible":"true","route":"machine","slot_key":"TM_071","slot_no":"71","slot_type":"TM"} | tm_tutor_changes.csv:368 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [162: バジルス](pokemon/162.md) | [404: ダストシュート](moves/404.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_020","slot_no":"20","slot_type":"TUTOR"} | tm_tutor_changes.csv:369 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [162: バジルス](pokemon/162.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:370 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [163: バジリール](pokemon/163.md) | [408: くさむすび](moves/408.md) | {"compatible":"true","route":"machine","slot_key":"TM_071","slot_no":"71","slot_type":"TM"} | tm_tutor_changes.csv:371 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [163: バジリール](pokemon/163.md) | [404: ダストシュート](moves/404.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_020","slot_no":"20","slot_type":"TUTOR"} | tm_tutor_changes.csv:372 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [163: バジリール](pokemon/163.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:373 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [164: コマシシ](pokemon/164.md) | [53: かえんほうしゃ](moves/53.md) | {"compatible":"true","route":"machine","slot_key":"TM_092","slot_no":"92","slot_type":"TM"} | tm_tutor_changes.csv:374 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [164: コマシシ](pokemon/164.md) | [257: ねっぷう](moves/257.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_016","slot_no":"16","slot_type":"TUTOR"} | tm_tutor_changes.csv:375 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [165: コマレオ](pokemon/165.md) | [53: かえんほうしゃ](moves/53.md) | {"compatible":"true","route":"machine","slot_key":"TM_092","slot_no":"92","slot_type":"TM"} | tm_tutor_changes.csv:376 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [165: コマレオ](pokemon/165.md) | [257: ねっぷう](moves/257.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_016","slot_no":"16","slot_type":"TUTOR"} | tm_tutor_changes.csv:377 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [166: コマレオン](pokemon/166.md) | [379: ドレインパンチ](moves/379.md) | {"compatible":"true","route":"machine","slot_key":"TM_074","slot_no":"74","slot_type":"TM"} | tm_tutor_changes.csv:378 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [166: コマレオン](pokemon/166.md) | [53: かえんほうしゃ](moves/53.md) | {"compatible":"true","route":"machine","slot_key":"TM_092","slot_no":"92","slot_type":"TM"} | tm_tutor_changes.csv:379 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [166: コマレオン](pokemon/166.md) | [257: ねっぷう](moves/257.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_016","slot_no":"16","slot_type":"TUTOR"} | tm_tutor_changes.csv:380 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [166: コマレオン](pokemon/166.md) | [798: コーチング](moves/798.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_056","slot_no":"56","slot_type":"TUTOR"} | tm_tutor_changes.csv:381 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [167: トッコウオ](pokemon/167.md) | [799: クイックターン](moves/799.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_060","slot_no":"60","slot_type":"TUTOR"} | tm_tutor_changes.csv:382 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [168: ボウソウオ](pokemon/168.md) | [667: アクアブレイク](moves/667.md) | {"compatible":"true","route":"machine","slot_key":"TM_082","slot_no":"82","slot_type":"TM"} | tm_tutor_changes.csv:383 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [168: ボウソウオ](pokemon/168.md) | [799: クイックターン](moves/799.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_060","slot_no":"60","slot_type":"TUTOR"} | tm_tutor_changes.csv:384 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [169: バクソウオ](pokemon/169.md) | [667: アクアブレイク](moves/667.md) | {"compatible":"true","route":"machine","slot_key":"TM_082","slot_no":"82","slot_type":"TM"} | tm_tutor_changes.csv:385 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [169: バクソウオ](pokemon/169.md) | [271: トリック](moves/271.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_008","slot_no":"8","slot_type":"TUTOR"} | tm_tutor_changes.csv:386 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [169: バクソウオ](pokemon/169.md) | [799: クイックターン](moves/799.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_060","slot_no":"60","slot_type":"TUTOR"} | tm_tutor_changes.csv:387 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [170: チェキラ](pokemon/170.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:388 | True | &#91;"egg","machine"&#93; | False |
| vega_to_official_historical_adoption | [170: チェキラ](pokemon/170.md) | [270: てだすけ](moves/270.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_009","slot_no":"9","slot_type":"TUTOR"} | tm_tutor_changes.csv:389 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [171: チェキッド](pokemon/171.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:390 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [171: チェキッド](pokemon/171.md) | [270: てだすけ](moves/270.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_009","slot_no":"9","slot_type":"TUTOR"} | tm_tutor_changes.csv:391 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [172: チェキラス](pokemon/172.md) | [270: てだすけ](moves/270.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_009","slot_no":"9","slot_type":"TUTOR"} | tm_tutor_changes.csv:392 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [173: リバード](pokemon/173.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:393 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [173: リバード](pokemon/173.md) | [528: アクロバット](moves/528.md) | {"compatible":"true","route":"machine","slot_key":"TM_069","slot_no":"69","slot_type":"TM"} | tm_tutor_changes.csv:394 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [173: リバード](pokemon/173.md) | [554: おいかぜ](moves/554.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_007","slot_no":"7","slot_type":"TUTOR"} | tm_tutor_changes.csv:395 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [173: リバード](pokemon/173.md) | [270: てだすけ](moves/270.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_009","slot_no":"9","slot_type":"TUTOR"} | tm_tutor_changes.csv:396 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [174: ララミンゴ](pokemon/174.md) | [554: おいかぜ](moves/554.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_007","slot_no":"7","slot_type":"TUTOR"} | tm_tutor_changes.csv:397 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [176: パチリック](pokemon/176.md) | [531: ボルトチェンジ](moves/531.md) | {"compatible":"true","route":"machine","slot_key":"TM_063","slot_no":"63","slot_type":"TM"} | tm_tutor_changes.csv:399 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [177: パンプリー](pokemon/177.md) | [391: シャドークロー](moves/391.md) | {"compatible":"true","route":"machine","slot_key":"TM_011","slot_no":"11","slot_type":"TM"} | tm_tutor_changes.csv:400 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [178: パンプッチ](pokemon/178.md) | [408: くさむすび](moves/408.md) | {"compatible":"true","route":"machine","slot_key":"TM_071","slot_no":"71","slot_type":"TM"} | tm_tutor_changes.csv:401 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [178: パンプッチ](pokemon/178.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:402 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [179: ルナビット](pokemon/179.md) | [579: サイコショック](moves/579.md) | {"compatible":"true","route":"machine","slot_key":"TM_075","slot_no":"75","slot_type":"TM"} | tm_tutor_changes.csv:403 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [179: ルナビット](pokemon/179.md) | [271: トリック](moves/271.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_008","slot_no":"8","slot_type":"TUTOR"} | tm_tutor_changes.csv:404 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [180: ルナバイン](pokemon/180.md) | [520: バークアウト](moves/520.md) | {"compatible":"true","route":"machine","slot_key":"TM_066","slot_no":"66","slot_type":"TM"} | tm_tutor_changes.csv:405 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [180: ルナバイン](pokemon/180.md) | [282: はたきおとす](moves/282.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_006","slot_no":"6","slot_type":"TUTOR"} | tm_tutor_changes.csv:406 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [180: ルナバイン](pokemon/180.md) | [271: トリック](moves/271.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_008","slot_no":"8","slot_type":"TUTOR"} | tm_tutor_changes.csv:407 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [181: ウソギー](pokemon/181.md) | [667: アクアブレイク](moves/667.md) | {"compatible":"true","route":"machine","slot_key":"TM_082","slot_no":"82","slot_type":"TM"} | tm_tutor_changes.csv:408 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [182: ウソドロ](pokemon/182.md) | [520: バークアウト](moves/520.md) | {"compatible":"true","route":"machine","slot_key":"TM_066","slot_no":"66","slot_type":"TM"} | tm_tutor_changes.csv:409 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [182: ウソドロ](pokemon/182.md) | [282: はたきおとす](moves/282.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_006","slot_no":"6","slot_type":"TUTOR"} | tm_tutor_changes.csv:410 | True | &#91;"level_up","machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [186: レジュリア](pokemon/186.md) | [800: トリプルアクセル](moves/800.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_052","slot_no":"52","slot_type":"TUTOR"} | tm_tutor_changes.csv:418 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [187: タダヌキ](pokemon/187.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:419 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [187: タダヌキ](pokemon/187.md) | [270: てだすけ](moves/270.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_009","slot_no":"9","slot_type":"TUTOR"} | tm_tutor_changes.csv:420 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [188: オオムジナ](pokemon/188.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:421 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [188: オオムジナ](pokemon/188.md) | [270: てだすけ](moves/270.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_009","slot_no":"9","slot_type":"TUTOR"} | tm_tutor_changes.csv:422 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [189: ポコキング](pokemon/189.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:423 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [189: ポコキング](pokemon/189.md) | [270: てだすけ](moves/270.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_009","slot_no":"9","slot_type":"TUTOR"} | tm_tutor_changes.csv:424 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [190: アスイーツ](pokemon/190.md) | [1014: アイススピナー](moves/1014.md) | {"compatible":"true","route":"machine","slot_key":"TM_109","slot_no":"109","slot_type":"TM"} | tm_tutor_changes.csv:425 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [190: アスイーツ](pokemon/190.md) | [800: トリプルアクセル](moves/800.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_052","slot_no":"52","slot_type":"TUTOR"} | tm_tutor_changes.csv:426 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [191: コユキムシ](pokemon/191.md) | [800: トリプルアクセル](moves/800.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_052","slot_no":"52","slot_type":"TUTOR"} | tm_tutor_changes.csv:427 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [192: ユキタテハ](pokemon/192.md) | [530: とんぼがえり](moves/530.md) | {"compatible":"true","route":"machine","slot_key":"TM_064","slot_no":"64","slot_type":"TM"} | tm_tutor_changes.csv:428 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [192: ユキタテハ](pokemon/192.md) | [535: むしくい](moves/535.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_030","slot_no":"30","slot_type":"TUTOR"} | tm_tutor_changes.csv:429 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [192: ユキタテハ](pokemon/192.md) | [800: トリプルアクセル](moves/800.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_052","slot_no":"52","slot_type":"TUTOR"} | tm_tutor_changes.csv:430 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [194: オオペラー](pokemon/194.md) | [528: アクロバット](moves/528.md) | {"compatible":"true","route":"machine","slot_key":"TM_069","slot_no":"69","slot_type":"TM"} | tm_tutor_changes.csv:433 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [194: オオペラー](pokemon/194.md) | [554: おいかぜ](moves/554.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_007","slot_no":"7","slot_type":"TUTOR"} | tm_tutor_changes.csv:434 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [195: オリバー](pokemon/195.md) | [579: サイコショック](moves/579.md) | {"compatible":"true","route":"machine","slot_key":"TM_075","slot_no":"75","slot_type":"TM"} | tm_tutor_changes.csv:435 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [195: オリバー](pokemon/195.md) | [271: トリック](moves/271.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_008","slot_no":"8","slot_type":"TUTOR"} | tm_tutor_changes.csv:436 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [196: ランペルン](pokemon/196.md) | [391: シャドークロー](moves/391.md) | {"compatible":"true","route":"machine","slot_key":"TM_011","slot_no":"11","slot_type":"TM"} | tm_tutor_changes.csv:437 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [196: ランペルン](pokemon/196.md) | [271: トリック](moves/271.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_008","slot_no":"8","slot_type":"TUTOR"} | tm_tutor_changes.csv:438 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [196: ランペルン](pokemon/196.md) | [796: ポルターガイスト](moves/796.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_054","slot_no":"54","slot_type":"TUTOR"} | tm_tutor_changes.csv:439 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [197: キーボン](pokemon/197.md) | [391: シャドークロー](moves/391.md) | {"compatible":"true","route":"machine","slot_key":"TM_011","slot_no":"11","slot_type":"TM"} | tm_tutor_changes.csv:440 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [197: キーボン](pokemon/197.md) | [796: ポルターガイスト](moves/796.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_054","slot_no":"54","slot_type":"TUTOR"} | tm_tutor_changes.csv:441 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [200: レディバル](pokemon/200.md) | [530: とんぼがえり](moves/530.md) | {"compatible":"true","route":"machine","slot_key":"TM_064","slot_no":"64","slot_type":"TM"} | tm_tutor_changes.csv:448 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [200: レディバル](pokemon/200.md) | [798: コーチング](moves/798.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_056","slot_no":"56","slot_type":"TUTOR"} | tm_tutor_changes.csv:449 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [202: ケンタル](pokemon/202.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:452 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [206: アスリスク](pokemon/206.md) | [391: シャドークロー](moves/391.md) | {"compatible":"true","route":"machine","slot_key":"TM_011","slot_no":"11","slot_type":"TM"} | tm_tutor_changes.csv:459 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [206: アスリスク](pokemon/206.md) | [796: ポルターガイスト](moves/796.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_054","slot_no":"54","slot_type":"TUTOR"} | tm_tutor_changes.csv:460 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [207: プラネム](pokemon/207.md) | [579: サイコショック](moves/579.md) | {"compatible":"true","route":"machine","slot_key":"TM_075","slot_no":"75","slot_type":"TM"} | tm_tutor_changes.csv:461 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [208: モドラ](pokemon/208.md) | [771: ワイドブレイカー](moves/771.md) | {"compatible":"true","route":"machine","slot_key":"TM_103","slot_no":"103","slot_type":"TM"} | tm_tutor_changes.csv:462 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [209: コモラゴン](pokemon/209.md) | [771: ワイドブレイカー](moves/771.md) | {"compatible":"true","route":"machine","slot_key":"TM_103","slot_no":"103","slot_type":"TM"} | tm_tutor_changes.csv:463 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [209: コモラゴン](pokemon/209.md) | [399: りゅうせいぐん](moves/399.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_001","slot_no":"1","slot_type":"TUTOR"} | tm_tutor_changes.csv:464 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [214: ヤミクラゲ](pokemon/214.md) | [520: バークアウト](moves/520.md) | {"compatible":"true","route":"machine","slot_key":"TM_066","slot_no":"66","slot_type":"TM"} | tm_tutor_changes.csv:470 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [214: ヤミクラゲ](pokemon/214.md) | [282: はたきおとす](moves/282.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_006","slot_no":"6","slot_type":"TUTOR"} | tm_tutor_changes.csv:471 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [214: ヤミクラゲ](pokemon/214.md) | [799: クイックターン](moves/799.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_060","slot_no":"60","slot_type":"TUTOR"} | tm_tutor_changes.csv:472 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [215: コイナリ](pokemon/215.md) | [53: かえんほうしゃ](moves/53.md) | {"compatible":"true","route":"machine","slot_key":"TM_092","slot_no":"92","slot_type":"TM"} | tm_tutor_changes.csv:473 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [215: コイナリ](pokemon/215.md) | [257: ねっぷう](moves/257.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_016","slot_no":"16","slot_type":"TUTOR"} | tm_tutor_changes.csv:474 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [216: オオイナリ](pokemon/216.md) | [53: かえんほうしゃ](moves/53.md) | {"compatible":"true","route":"machine","slot_key":"TM_092","slot_no":"92","slot_type":"TM"} | tm_tutor_changes.csv:475 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [217: キャンペル](pokemon/217.md) | [391: シャドークロー](moves/391.md) | {"compatible":"true","route":"machine","slot_key":"TM_011","slot_no":"11","slot_type":"TM"} | tm_tutor_changes.csv:476 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [218: ホムロソク](pokemon/218.md) | [391: シャドークロー](moves/391.md) | {"compatible":"true","route":"machine","slot_key":"TM_011","slot_no":"11","slot_type":"TM"} | tm_tutor_changes.csv:477 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [218: ホムロソク](pokemon/218.md) | [257: ねっぷう](moves/257.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_016","slot_no":"16","slot_type":"TUTOR"} | tm_tutor_changes.csv:478 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [219: ガレキダマ](pokemon/219.md) | [550: ステルスロック](moves/550.md) | {"compatible":"true","route":"machine","slot_key":"TM_061","slot_no":"61","slot_type":"TM"} | tm_tutor_changes.csv:479 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [219: ガレキダマ](pokemon/219.md) | [796: ポルターガイスト](moves/796.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_054","slot_no":"54","slot_type":"TUTOR"} | tm_tutor_changes.csv:480 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [220: ジバクン](pokemon/220.md) | [787: メテオビーム](moves/787.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_047","slot_no":"47","slot_type":"TUTOR"} | tm_tutor_changes.csv:481 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [220: ジバクン](pokemon/220.md) | [796: ポルターガイスト](moves/796.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_054","slot_no":"54","slot_type":"TUTOR"} | tm_tutor_changes.csv:482 | True | &#91;"level_up","machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [221: ワラコゾウ](pokemon/221.md) | [802: ねっさのだいち](moves/802.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_051","slot_no":"51","slot_type":"TUTOR"} | tm_tutor_changes.csv:483 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [222: ワラガシラ](pokemon/222.md) | [554: おいかぜ](moves/554.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_007","slot_no":"7","slot_type":"TUTOR"} | tm_tutor_changes.csv:484 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [222: ワラガシラ](pokemon/222.md) | [802: ねっさのだいち](moves/802.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_051","slot_no":"51","slot_type":"TUTOR"} | tm_tutor_changes.csv:485 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [225: ドルマイン](pokemon/225.md) | [397: ラスターカノン](moves/397.md) | {"compatible":"true","route":"machine","slot_key":"TM_077","slot_no":"77","slot_type":"TM"} | tm_tutor_changes.csv:487 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [225: ドルマイン](pokemon/225.md) | [405: アイアンヘッド](moves/405.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_014","slot_no":"14","slot_type":"TUTOR"} | tm_tutor_changes.csv:488 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [233: プカスカ](pokemon/233.md) | [531: ボルトチェンジ](moves/531.md) | {"compatible":"true","route":"machine","slot_key":"TM_063","slot_no":"63","slot_type":"TM"} | tm_tutor_changes.csv:500 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [233: プカスカ](pokemon/233.md) | [554: おいかぜ](moves/554.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_007","slot_no":"7","slot_type":"TUTOR"} | tm_tutor_changes.csv:501 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [233: プカスカ](pokemon/233.md) | [489: エレキネット](moves/489.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_029","slot_no":"29","slot_type":"TUTOR"} | tm_tutor_changes.csv:502 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [234: スモーガス](pokemon/234.md) | [531: ボルトチェンジ](moves/531.md) | {"compatible":"true","route":"machine","slot_key":"TM_063","slot_no":"63","slot_type":"TM"} | tm_tutor_changes.csv:503 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [235: ココロン](pokemon/235.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:504 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [236: カモドック](pokemon/236.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:505 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [237: トノッパー](pokemon/237.md) | [667: アクアブレイク](moves/667.md) | {"compatible":"true","route":"machine","slot_key":"TM_082","slot_no":"82","slot_type":"TM"} | tm_tutor_changes.csv:506 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [237: トノッパー](pokemon/237.md) | [799: クイックターン](moves/799.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_060","slot_no":"60","slot_type":"TUTOR"} | tm_tutor_changes.csv:507 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [238: ガルラーダ](pokemon/238.md) | [379: ドレインパンチ](moves/379.md) | {"compatible":"true","route":"machine","slot_key":"TM_074","slot_no":"74","slot_type":"TM"} | tm_tutor_changes.csv:508 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [238: ガルラーダ](pokemon/238.md) | [667: アクアブレイク](moves/667.md) | {"compatible":"true","route":"machine","slot_key":"TM_082","slot_no":"82","slot_type":"TM"} | tm_tutor_changes.csv:509 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [238: ガルラーダ](pokemon/238.md) | [798: コーチング](moves/798.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_056","slot_no":"56","slot_type":"TUTOR"} | tm_tutor_changes.csv:510 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [238: ガルラーダ](pokemon/238.md) | [799: クイックターン](moves/799.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_060","slot_no":"60","slot_type":"TUTOR"} | tm_tutor_changes.csv:511 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [239: ハサーガ](pokemon/239.md) | [379: ドレインパンチ](moves/379.md) | {"compatible":"true","route":"machine","slot_key":"TM_074","slot_no":"74","slot_type":"TM"} | tm_tutor_changes.csv:512 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [239: ハサーガ](pokemon/239.md) | [397: ラスターカノン](moves/397.md) | {"compatible":"true","route":"machine","slot_key":"TM_077","slot_no":"77","slot_type":"TM"} | tm_tutor_changes.csv:513 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [239: ハサーガ](pokemon/239.md) | [798: コーチング](moves/798.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_056","slot_no":"56","slot_type":"TUTOR"} | tm_tutor_changes.csv:514 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [240: アメクジ](pokemon/240.md) | [799: クイックターン](moves/799.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_060","slot_no":"60","slot_type":"TUTOR"} | tm_tutor_changes.csv:515 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [241: アメリシア](pokemon/241.md) | [522: ベノムショック](moves/522.md) | {"compatible":"true","route":"machine","slot_key":"TM_070","slot_no":"70","slot_type":"TM"} | tm_tutor_changes.csv:516 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [241: アメリシア](pokemon/241.md) | [667: アクアブレイク](moves/667.md) | {"compatible":"true","route":"machine","slot_key":"TM_082","slot_no":"82","slot_type":"TM"} | tm_tutor_changes.csv:517 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [241: アメリシア](pokemon/241.md) | [404: ダストシュート](moves/404.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_020","slot_no":"20","slot_type":"TUTOR"} | tm_tutor_changes.csv:518 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [241: アメリシア](pokemon/241.md) | [799: クイックターン](moves/799.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_060","slot_no":"60","slot_type":"TUTOR"} | tm_tutor_changes.csv:519 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [242: カララン](pokemon/242.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:520 | True | &#91;"egg","machine"&#93; | False |
| vega_to_official_historical_adoption | [242: カララン](pokemon/242.md) | [408: くさむすび](moves/408.md) | {"compatible":"true","route":"machine","slot_key":"TM_071","slot_no":"71","slot_type":"TM"} | tm_tutor_changes.csv:521 | True | &#91;"egg","machine"&#93; | False |
| vega_to_official_historical_adoption | [242: カララン](pokemon/242.md) | [270: てだすけ](moves/270.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_009","slot_no":"9","slot_type":"TUTOR"} | tm_tutor_changes.csv:522 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [243: カンカーン](pokemon/243.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:523 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [243: カンカーン](pokemon/243.md) | [270: てだすけ](moves/270.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_009","slot_no":"9","slot_type":"TUTOR"} | tm_tutor_changes.csv:524 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [243: カンカーン](pokemon/243.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:525 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [244: クラウン](pokemon/244.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:526 | True | &#91;"egg","machine"&#93; | False |
| vega_to_official_historical_adoption | [244: クラウン](pokemon/244.md) | [270: てだすけ](moves/270.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_009","slot_no":"9","slot_type":"TUTOR"} | tm_tutor_changes.csv:527 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [245: テイルーン](pokemon/245.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:528 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [245: テイルーン](pokemon/245.md) | [528: アクロバット](moves/528.md) | {"compatible":"true","route":"machine","slot_key":"TM_069","slot_no":"69","slot_type":"TM"} | tm_tutor_changes.csv:529 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [246: モグルトン](pokemon/246.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:530 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [246: モグルトン](pokemon/246.md) | [270: てだすけ](moves/270.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_009","slot_no":"9","slot_type":"TUTOR"} | tm_tutor_changes.csv:531 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [251: ラクチャン](pokemon/251.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:536 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [277: ドゴン](pokemon/277.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:540 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [277: ドゴン](pokemon/277.md) | [798: コーチング](moves/798.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_056","slot_no":"56","slot_type":"TUTOR"} | tm_tutor_changes.csv:541 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [279: トコヤミ](pokemon/279.md) | [520: バークアウト](moves/520.md) | {"compatible":"true","route":"machine","slot_key":"TM_066","slot_no":"66","slot_type":"TM"} | tm_tutor_changes.csv:543 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [279: トコヤミ](pokemon/279.md) | [528: アクロバット](moves/528.md) | {"compatible":"true","route":"machine","slot_key":"TM_069","slot_no":"69","slot_type":"TM"} | tm_tutor_changes.csv:544 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [279: トコヤミ](pokemon/279.md) | [282: はたきおとす](moves/282.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_006","slot_no":"6","slot_type":"TUTOR"} | tm_tutor_changes.csv:545 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [279: トコヤミ](pokemon/279.md) | [554: おいかぜ](moves/554.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_007","slot_no":"7","slot_type":"TUTOR"} | tm_tutor_changes.csv:546 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [281: クチールス](pokemon/281.md) | [282: はたきおとす](moves/282.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_006","slot_no":"6","slot_type":"TUTOR"} | tm_tutor_changes.csv:548 | True | &#91;"level_up","machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [281: クチールス](pokemon/281.md) | [800: トリプルアクセル](moves/800.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_052","slot_no":"52","slot_type":"TUTOR"} | tm_tutor_changes.csv:549 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [285: ガッツロス](pokemon/285.md) | [798: コーチング](moves/798.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_056","slot_no":"56","slot_type":"TUTOR"} | tm_tutor_changes.csv:555 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [288: アーボスク](pokemon/288.md) | [404: ダストシュート](moves/404.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_020","slot_no":"20","slot_type":"TUTOR"} | tm_tutor_changes.csv:556 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [291: モアドガス](pokemon/291.md) | [53: かえんほうしゃ](moves/53.md) | {"compatible":"true","route":"machine","slot_key":"TM_092","slot_no":"92","slot_type":"TM"} | tm_tutor_changes.csv:560 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [291: モアドガス](pokemon/291.md) | [404: ダストシュート](moves/404.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_020","slot_no":"20","slot_type":"TUTOR"} | tm_tutor_changes.csv:561 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [305: ベタデーム](pokemon/305.md) | [799: クイックターン](moves/799.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_060","slot_no":"60","slot_type":"TUTOR"} | tm_tutor_changes.csv:586 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [306: テッコンボ](pokemon/306.md) | [379: ドレインパンチ](moves/379.md) | {"compatible":"true","route":"machine","slot_key":"TM_074","slot_no":"74","slot_type":"TM"} | tm_tutor_changes.csv:587 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [306: テッコンボ](pokemon/306.md) | [798: コーチング](moves/798.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_056","slot_no":"56","slot_type":"TUTOR"} | tm_tutor_changes.csv:588 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [307: ボンバット](pokemon/307.md) | [554: おいかぜ](moves/554.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_007","slot_no":"7","slot_type":"TUTOR"} | tm_tutor_changes.csv:589 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [307: ボンバット](pokemon/307.md) | [404: ダストシュート](moves/404.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_020","slot_no":"20","slot_type":"TUTOR"} | tm_tutor_changes.csv:590 | True | &#91;"egg","level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [310: ダンカンス](pokemon/310.md) | [408: くさむすび](moves/408.md) | {"compatible":"true","route":"machine","slot_key":"TM_071","slot_no":"71","slot_type":"TM"} | tm_tutor_changes.csv:593 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [310: ダンカンス](pokemon/310.md) | [270: てだすけ](moves/270.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_009","slot_no":"9","slot_type":"TUTOR"} | tm_tutor_changes.csv:594 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [310: ダンカンス](pokemon/310.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:595 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [311: ドサーモン](pokemon/311.md) | [379: ドレインパンチ](moves/379.md) | {"compatible":"true","route":"machine","slot_key":"TM_074","slot_no":"74","slot_type":"TM"} | tm_tutor_changes.csv:596 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [311: ドサーモン](pokemon/311.md) | [667: アクアブレイク](moves/667.md) | {"compatible":"true","route":"machine","slot_key":"TM_082","slot_no":"82","slot_type":"TM"} | tm_tutor_changes.csv:597 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [311: ドサーモン](pokemon/311.md) | [798: コーチング](moves/798.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_056","slot_no":"56","slot_type":"TUTOR"} | tm_tutor_changes.csv:598 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [311: ドサーモン](pokemon/311.md) | [799: クイックターン](moves/799.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_060","slot_no":"60","slot_type":"TUTOR"} | tm_tutor_changes.csv:599 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [312: テッケン](pokemon/312.md) | [379: ドレインパンチ](moves/379.md) | {"compatible":"true","route":"machine","slot_key":"TM_074","slot_no":"74","slot_type":"TM"} | tm_tutor_changes.csv:600 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [320: ヒョウカク](pokemon/320.md) | [531: ボルトチェンジ](moves/531.md) | {"compatible":"true","route":"machine","slot_key":"TM_063","slot_no":"63","slot_type":"TM"} | tm_tutor_changes.csv:617 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [320: ヒョウカク](pokemon/320.md) | [1014: アイススピナー](moves/1014.md) | {"compatible":"true","route":"machine","slot_key":"TM_109","slot_no":"109","slot_type":"TM"} | tm_tutor_changes.csv:618 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [320: ヒョウカク](pokemon/320.md) | [489: エレキネット](moves/489.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_029","slot_no":"29","slot_type":"TUTOR"} | tm_tutor_changes.csv:619 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [323: プレシオン](pokemon/323.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:624 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [323: プレシオン](pokemon/323.md) | [667: アクアブレイク](moves/667.md) | {"compatible":"true","route":"machine","slot_key":"TM_082","slot_no":"82","slot_type":"TM"} | tm_tutor_changes.csv:625 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [323: プレシオン](pokemon/323.md) | [270: てだすけ](moves/270.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_009","slot_no":"9","slot_type":"TUTOR"} | tm_tutor_changes.csv:626 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [326: メルリコ](pokemon/326.md) | [667: アクアブレイク](moves/667.md) | {"compatible":"true","route":"machine","slot_key":"TM_082","slot_no":"82","slot_type":"TM"} | tm_tutor_changes.csv:632 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [327: サムラダケ](pokemon/327.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:633 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [328: ブレイドン](pokemon/328.md) | [798: コーチング](moves/798.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_056","slot_no":"56","slot_type":"TUTOR"} | tm_tutor_changes.csv:634 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [329: ブレイオー](pokemon/329.md) | [379: ドレインパンチ](moves/379.md) | {"compatible":"true","route":"machine","slot_key":"TM_074","slot_no":"74","slot_type":"TM"} | tm_tutor_changes.csv:635 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [329: ブレイオー](pokemon/329.md) | [405: アイアンヘッド](moves/405.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_014","slot_no":"14","slot_type":"TUTOR"} | tm_tutor_changes.csv:636 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [329: ブレイオー](pokemon/329.md) | [798: コーチング](moves/798.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_056","slot_no":"56","slot_type":"TUTOR"} | tm_tutor_changes.csv:637 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [333: アルデッパ](pokemon/333.md) | [495: じならし](moves/495.md) | {"compatible":"true","route":"machine","slot_key":"TM_065","slot_no":"65","slot_type":"TM"} | tm_tutor_changes.csv:643 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [333: アルデッパ](pokemon/333.md) | [53: かえんほうしゃ](moves/53.md) | {"compatible":"true","route":"machine","slot_key":"TM_092","slot_no":"92","slot_type":"TM"} | tm_tutor_changes.csv:644 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [333: アルデッパ](pokemon/333.md) | [257: ねっぷう](moves/257.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_016","slot_no":"16","slot_type":"TUTOR"} | tm_tutor_changes.csv:645 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [333: アルデッパ](pokemon/333.md) | [802: ねっさのだいち](moves/802.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_051","slot_no":"51","slot_type":"TUTOR"} | tm_tutor_changes.csv:646 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [334: ゴキブロス](pokemon/334.md) | [530: とんぼがえり](moves/530.md) | {"compatible":"true","route":"machine","slot_key":"TM_064","slot_no":"64","slot_type":"TM"} | tm_tutor_changes.csv:647 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [334: ゴキブロス](pokemon/334.md) | [535: むしくい](moves/535.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_030","slot_no":"30","slot_type":"TUTOR"} | tm_tutor_changes.csv:648 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [335: ビビッドン](pokemon/335.md) | [531: ボルトチェンジ](moves/531.md) | {"compatible":"true","route":"machine","slot_key":"TM_063","slot_no":"63","slot_type":"TM"} | tm_tutor_changes.csv:649 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [335: ビビッドン](pokemon/335.md) | [667: アクアブレイク](moves/667.md) | {"compatible":"true","route":"machine","slot_key":"TM_082","slot_no":"82","slot_type":"TM"} | tm_tutor_changes.csv:650 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [335: ビビッドン](pokemon/335.md) | [489: エレキネット](moves/489.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_029","slot_no":"29","slot_type":"TUTOR"} | tm_tutor_changes.csv:651 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [335: ビビッドン](pokemon/335.md) | [799: クイックターン](moves/799.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_060","slot_no":"60","slot_type":"TUTOR"} | tm_tutor_changes.csv:652 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [336: ドルン](pokemon/336.md) | [531: ボルトチェンジ](moves/531.md) | {"compatible":"true","route":"machine","slot_key":"TM_063","slot_no":"63","slot_type":"TM"} | tm_tutor_changes.csv:653 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [336: ドルン](pokemon/336.md) | [489: エレキネット](moves/489.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_029","slot_no":"29","slot_type":"TUTOR"} | tm_tutor_changes.csv:654 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [337: バーネッコ](pokemon/337.md) | [53: かえんほうしゃ](moves/53.md) | {"compatible":"true","route":"machine","slot_key":"TM_092","slot_no":"92","slot_type":"TM"} | tm_tutor_changes.csv:655 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [337: バーネッコ](pokemon/337.md) | [257: ねっぷう](moves/257.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_016","slot_no":"16","slot_type":"TUTOR"} | tm_tutor_changes.csv:656 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [338: コケゾー](pokemon/338.md) | [408: くさむすび](moves/408.md) | {"compatible":"true","route":"machine","slot_key":"TM_071","slot_no":"71","slot_type":"TM"} | tm_tutor_changes.csv:657 | True | &#91;"egg","machine"&#93; | False |
| vega_to_official_historical_adoption | [338: コケゾー](pokemon/338.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:658 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [339: オンネット](pokemon/339.md) | [282: はたきおとす](moves/282.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_006","slot_no":"6","slot_type":"TUTOR"} | tm_tutor_changes.csv:659 | True | &#91;"level_up","machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [344: カミギリー](pokemon/344.md) | [530: とんぼがえり](moves/530.md) | {"compatible":"true","route":"machine","slot_key":"TM_064","slot_no":"64","slot_type":"TM"} | tm_tutor_changes.csv:667 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [344: カミギリー](pokemon/344.md) | [397: ラスターカノン](moves/397.md) | {"compatible":"true","route":"machine","slot_key":"TM_077","slot_no":"77","slot_type":"TM"} | tm_tutor_changes.csv:668 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [345: レファン](pokemon/345.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:669 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [345: レファン](pokemon/345.md) | [270: てだすけ](moves/270.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_009","slot_no":"9","slot_type":"TUTOR"} | tm_tutor_changes.csv:670 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [347: ストータス](pokemon/347.md) | [528: アクロバット](moves/528.md) | {"compatible":"true","route":"machine","slot_key":"TM_069","slot_no":"69","slot_type":"TM"} | tm_tutor_changes.csv:672 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [349: ラブリン](pokemon/349.md) | [182: まもる](moves/182.md) | {"compatible":"true","route":"machine","slot_key":"TM_051","slot_no":"51","slot_type":"TM"} | tm_tutor_changes.csv:675 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [350: オールガ](pokemon/350.md) | [531: ボルトチェンジ](moves/531.md) | {"compatible":"true","route":"machine","slot_key":"TM_063","slot_no":"63","slot_type":"TM"} | tm_tutor_changes.csv:676 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [353: ヒカリゴケ](pokemon/353.md) | [531: ボルトチェンジ](moves/531.md) | {"compatible":"true","route":"machine","slot_key":"TM_063","slot_no":"63","slot_type":"TM"} | tm_tutor_changes.csv:682 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [353: ヒカリゴケ](pokemon/353.md) | [489: エレキネット](moves/489.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_029","slot_no":"29","slot_type":"TUTOR"} | tm_tutor_changes.csv:683 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [353: ヒカリゴケ](pokemon/353.md) | [790: グラススライダー](moves/790.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_048","slot_no":"48","slot_type":"TUTOR"} | tm_tutor_changes.csv:684 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [356: セルディー](pokemon/356.md) | [1014: アイススピナー](moves/1014.md) | {"compatible":"true","route":"machine","slot_key":"TM_109","slot_no":"109","slot_type":"TM"} | tm_tutor_changes.csv:688 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [356: セルディー](pokemon/356.md) | [800: トリプルアクセル](moves/800.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_052","slot_no":"52","slot_type":"TUTOR"} | tm_tutor_changes.csv:689 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [357: コゴボー](pokemon/357.md) | [53: かえんほうしゃ](moves/53.md) | {"compatible":"true","route":"machine","slot_key":"TM_092","slot_no":"92","slot_type":"TM"} | tm_tutor_changes.csv:690 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [357: コゴボー](pokemon/357.md) | [257: ねっぷう](moves/257.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_016","slot_no":"16","slot_type":"TUTOR"} | tm_tutor_changes.csv:691 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [358: ガネーシャ](pokemon/358.md) | [802: ねっさのだいち](moves/802.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_051","slot_no":"51","slot_type":"TUTOR"} | tm_tutor_changes.csv:692 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [360: プレゼンタ](pokemon/360.md) | [1014: アイススピナー](moves/1014.md) | {"compatible":"true","route":"machine","slot_key":"TM_109","slot_no":"109","slot_type":"TM"} | tm_tutor_changes.csv:695 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [360: プレゼンタ](pokemon/360.md) | [800: トリプルアクセル](moves/800.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_052","slot_no":"52","slot_type":"TUTOR"} | tm_tutor_changes.csv:696 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [372: サンドリル](pokemon/372.md) | [495: じならし](moves/495.md) | {"compatible":"true","route":"machine","slot_key":"TM_065","slot_no":"65","slot_type":"TM"} | tm_tutor_changes.csv:719 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [372: サンドリル](pokemon/372.md) | [802: ねっさのだいち](moves/802.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_051","slot_no":"51","slot_type":"TUTOR"} | tm_tutor_changes.csv:720 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [373: カモナイツ](pokemon/373.md) | [554: おいかぜ](moves/554.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_007","slot_no":"7","slot_type":"TUTOR"} | tm_tutor_changes.csv:721 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [373: カモナイツ](pokemon/373.md) | [798: コーチング](moves/798.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_056","slot_no":"56","slot_type":"TUTOR"} | tm_tutor_changes.csv:722 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [383: シルドール](pokemon/383.md) | [397: ラスターカノン](moves/397.md) | {"compatible":"true","route":"machine","slot_key":"TM_077","slot_no":"77","slot_type":"TM"} | tm_tutor_changes.csv:738 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [383: シルドール](pokemon/383.md) | [282: はたきおとす](moves/282.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_006","slot_no":"6","slot_type":"TUTOR"} | tm_tutor_changes.csv:739 | True | &#91;"level_up","machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [384: セルシィ](pokemon/384.md) | [800: トリプルアクセル](moves/800.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_052","slot_no":"52","slot_type":"TUTOR"} | tm_tutor_changes.csv:740 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [386: ワークロ](pokemon/386.md) | [528: アクロバット](moves/528.md) | {"compatible":"true","route":"machine","slot_key":"TM_069","slot_no":"69","slot_type":"TM"} | tm_tutor_changes.csv:741 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [386: ワークロ](pokemon/386.md) | [282: はたきおとす](moves/282.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_006","slot_no":"6","slot_type":"TUTOR"} | tm_tutor_changes.csv:742 | True | &#91;"level_up","machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [386: ワークロ](pokemon/386.md) | [554: おいかぜ](moves/554.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_007","slot_no":"7","slot_type":"TUTOR"} | tm_tutor_changes.csv:743 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [387: アリンセス](pokemon/387.md) | [530: とんぼがえり](moves/530.md) | {"compatible":"true","route":"machine","slot_key":"TM_064","slot_no":"64","slot_type":"TM"} | tm_tutor_changes.csv:744 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [387: アリンセス](pokemon/387.md) | [535: むしくい](moves/535.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_030","slot_no":"30","slot_type":"TUTOR"} | tm_tutor_changes.csv:745 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [388: ティオルス](pokemon/388.md) | [399: りゅうせいぐん](moves/399.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_001","slot_no":"1","slot_type":"TUTOR"} | tm_tutor_changes.csv:746 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [390: ティラノス](pokemon/390.md) | [771: ワイドブレイカー](moves/771.md) | {"compatible":"true","route":"machine","slot_key":"TM_103","slot_no":"103","slot_type":"TM"} | tm_tutor_changes.csv:747 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [391: ブレイバー](pokemon/391.md) | [798: コーチング](moves/798.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_056","slot_no":"56","slot_type":"TUTOR"} | tm_tutor_changes.csv:748 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [392: ヤマネツ](pokemon/392.md) | [408: くさむすび](moves/408.md) | {"compatible":"true","route":"machine","slot_key":"TM_071","slot_no":"71","slot_type":"TM"} | tm_tutor_changes.csv:749 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [393: ヒササビ](pokemon/393.md) | [531: ボルトチェンジ](moves/531.md) | {"compatible":"true","route":"machine","slot_key":"TM_063","slot_no":"63","slot_type":"TM"} | tm_tutor_changes.csv:750 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [393: ヒササビ](pokemon/393.md) | [528: アクロバット](moves/528.md) | {"compatible":"true","route":"machine","slot_key":"TM_069","slot_no":"69","slot_type":"TM"} | tm_tutor_changes.csv:751 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [393: ヒササビ](pokemon/393.md) | [554: おいかぜ](moves/554.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_007","slot_no":"7","slot_type":"TUTOR"} | tm_tutor_changes.csv:752 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [394: シャーモン](pokemon/394.md) | [379: ドレインパンチ](moves/379.md) | {"compatible":"true","route":"machine","slot_key":"TM_074","slot_no":"74","slot_type":"TM"} | tm_tutor_changes.csv:753 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [400: ロイツァー](pokemon/400.md) | [667: アクアブレイク](moves/667.md) | {"compatible":"true","route":"machine","slot_key":"TM_082","slot_no":"82","slot_type":"TM"} | tm_tutor_changes.csv:763 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [400: ロイツァー](pokemon/400.md) | [799: クイックターン](moves/799.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_060","slot_no":"60","slot_type":"TUTOR"} | tm_tutor_changes.csv:764 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [401: ガタノア](pokemon/401.md) | [667: アクアブレイク](moves/667.md) | {"compatible":"true","route":"machine","slot_key":"TM_082","slot_no":"82","slot_type":"TM"} | tm_tutor_changes.csv:765 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [401: ガタノア](pokemon/401.md) | [271: トリック](moves/271.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_008","slot_no":"8","slot_type":"TUTOR"} | tm_tutor_changes.csv:766 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [402: テツカブリ](pokemon/402.md) | [397: ラスターカノン](moves/397.md) | {"compatible":"true","route":"machine","slot_key":"TM_077","slot_no":"77","slot_type":"TM"} | tm_tutor_changes.csv:767 | True | &#91;"level_up","machine"&#93; | False |
| vega_to_official_historical_adoption | [402: テツカブリ](pokemon/402.md) | [667: アクアブレイク](moves/667.md) | {"compatible":"true","route":"machine","slot_key":"TM_082","slot_no":"82","slot_type":"TM"} | tm_tutor_changes.csv:768 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [402: テツカブリ](pokemon/402.md) | [405: アイアンヘッド](moves/405.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_014","slot_no":"14","slot_type":"TUTOR"} | tm_tutor_changes.csv:769 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [402: テツカブリ](pokemon/402.md) | [799: クイックターン](moves/799.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_060","slot_no":"60","slot_type":"TUTOR"} | tm_tutor_changes.csv:770 | True | &#91;"machine","tutor"&#93; | False |
| vega_to_official_historical_adoption | [406: オルディナ](pokemon/406.md) | [520: バークアウト](moves/520.md) | {"compatible":"true","route":"machine","slot_key":"TM_066","slot_no":"66","slot_type":"TM"} | tm_tutor_changes.csv:775 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [406: オルディナ](pokemon/406.md) | [282: はたきおとす](moves/282.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_006","slot_no":"6","slot_type":"TUTOR"} | tm_tutor_changes.csv:776 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [409: オルマリア](pokemon/409.md) | [520: バークアウト](moves/520.md) | {"compatible":"true","route":"machine","slot_key":"TM_066","slot_no":"66","slot_type":"TM"} | tm_tutor_changes.csv:782 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [409: オルマリア](pokemon/409.md) | [282: はたきおとす](moves/282.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_006","slot_no":"6","slot_type":"TUTOR"} | tm_tutor_changes.csv:783 | True | &#91;"tutor"&#93; | False |
| vega_to_official_historical_adoption | [410: アスフィア](pokemon/410.md) | [520: バークアウト](moves/520.md) | {"compatible":"true","route":"machine","slot_key":"TM_066","slot_no":"66","slot_type":"TM"} | tm_tutor_changes.csv:784 | True | &#91;"machine"&#93; | False |
| vega_to_official_historical_adoption | [410: アスフィア](pokemon/410.md) | [399: りゅうせいぐん](moves/399.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_001","slot_no":"1","slot_type":"TUTOR"} | tm_tutor_changes.csv:785 | True | &#91;"level_up","tutor"&#93; | False |
| vega_to_official_historical_adoption | [410: アスフィア](pokemon/410.md) | [282: はたきおとす](moves/282.md) | {"compatible":"true","route":"tutor","slot_key":"TUTOR_006","slot_no":"6","slot_type":"TUTOR"} | tm_tutor_changes.csv:786 | True | &#91;"tutor"&#93; | False |

## Species別全経路

| Species | 経路別件数 |
| --- | --- |
| [0: ？？？？？](pokemon/0.md) | {"machine":14,"tutor":19} |
| [1: リープン](pokemon/1.md) | {"egg":25,"level_up":15,"machine":47,"tutor":32} |
| [2: リーティン](pokemon/2.md) | {"egg":1,"level_up":18,"machine":37,"tutor":24} |
| [3: リーテイル](pokemon/3.md) | {"egg":2,"level_up":24,"machine":44,"tutor":31} |
| [4: ファマー](pokemon/4.md) | {"egg":22,"level_up":16,"machine":39,"tutor":33} |
| [5: ファイマー](pokemon/5.md) | {"egg":1,"level_up":17,"machine":16,"tutor":27} |
| [6: ファマイン](pokemon/6.md) | {"egg":2,"level_up":25,"machine":44,"tutor":31} |
| [7: アクタシ](pokemon/7.md) | {"egg":27,"level_up":16,"machine":32,"tutor":32} |
| [8: レクオレ](pokemon/8.md) | {"egg":1,"level_up":18,"machine":28,"tutor":37} |
| [9: タテボーシ](pokemon/9.md) | {"egg":2,"level_up":25,"machine":31,"tutor":31} |
| [10: スバメ](pokemon/10.md) | {"egg":14,"level_up":14,"machine":9,"machine_archive":15,"tutor":4,"tutor_archive":2} |
| [11: オオスバメ](pokemon/11.md) | {"egg":2,"level_up":19,"machine":9,"machine_archive":17,"tutor":4,"tutor_archive":3} |
| [12: リオル](pokemon/12.md) | {"egg":8,"level_up":18,"machine":23,"machine_archive":20,"shared_egg":7} |
| [13: ルカリオ](pokemon/13.md) | {"egg":2,"level_up":28,"machine":31,"machine_archive":30,"shared_egg":7} |
| [14: デルビル](pokemon/14.md) | {"egg":10,"level_up":17,"machine":23,"machine_archive":25,"shared_egg":8} |
| [15: ヘルガー](pokemon/15.md) | {"egg":2,"level_up":19,"machine":24,"machine_archive":28,"shared_egg":8} |
| [16: ディグダ](pokemon/16.md) | {"egg":6,"level_up":14,"machine":21,"machine_archive":19,"shared_egg":5} |
| [17: ダグトリオ](pokemon/17.md) | {"egg":1,"level_up":17,"machine":22,"machine_archive":21,"shared_egg":5} |
| [18: トゲピー](pokemon/18.md) | {"egg":8,"level_up":16,"machine":21,"machine_archive":24,"shared_egg":6} |
| [19: トゲチック](pokemon/19.md) | {"egg":2,"level_up":18,"machine":26,"machine_archive":30,"shared_egg":6,"tutor":1} |
| [20: トゲキッス](pokemon/20.md) | {"egg":2,"level_up":22,"machine":29,"machine_archive":30,"shared_egg":6,"tutor":1} |
| [21: フロン](pokemon/21.md) | {"egg":23,"level_up":15,"machine":25,"tutor":37} |
| [22: フロルル](pokemon/22.md) | {"egg":1,"level_up":17,"machine":38,"tutor":34} |
| [23: フローリア](pokemon/23.md) | {"egg":2,"level_up":22,"machine":25,"tutor":35} |
| [24: ピチュー](pokemon/24.md) | {"build_learnable_preservation":1,"egg":8,"level_up":7,"machine":20,"machine_archive":14,"shared_egg":7} |
| [25: ピカチュウ](pokemon/25.md) | {"build_learnable_preservation":1,"egg":1,"level_up":21,"machine":24,"machine_archive":23,"shared_egg":7} |
| [26: ライチュウ](pokemon/26.md) | {"build_learnable_preservation":1,"egg":1,"level_up":21,"machine":25,"machine_archive":25,"shared_egg":7} |
| [27: ゴリチュウ](pokemon/27.md) | {"egg":2,"level_up":16,"machine":40,"tutor":33} |
| [28: エアームド](pokemon/28.md) | {"egg":10,"level_up":16,"machine":24,"machine_archive":20,"shared_egg":7} |
| [29: ニドラン♀](pokemon/29.md) | {"egg":9,"level_up":13,"machine":16,"machine_archive":15,"shared_egg":7} |
| [30: ニドリーナ](pokemon/30.md) | {"egg":1,"level_up":13,"machine":17,"machine_archive":15,"shared_egg":7} |
| [31: ニドクイン](pokemon/31.md) | {"egg":2,"level_up":15,"machine":37,"machine_archive":34,"shared_egg":7,"tutor":1} |
| [32: ニドラン♂](pokemon/32.md) | {"egg":12,"level_up":13,"machine":18,"machine_archive":14,"shared_egg":10} |
| [33: ニドリーノ](pokemon/33.md) | {"egg":1,"level_up":13,"machine":19,"machine_archive":14,"shared_egg":10} |
| [34: ニドキング](pokemon/34.md) | {"egg":2,"level_up":15,"machine":40,"machine_archive":32,"shared_egg":10,"tutor":1} |
| [35: ブイゼル](pokemon/35.md) | {"egg":9,"level_up":16,"machine":23,"machine_archive":17,"shared_egg":8} |
| [36: フローゼル](pokemon/36.md) | {"build_learnable_preservation":1,"egg":1,"level_up":17,"machine":25,"machine_archive":24,"shared_egg":8} |
| [37: ララベリー](pokemon/37.md) | {"egg":25,"level_up":16,"machine":37,"tutor":39} |
| [38: セラーナ](pokemon/38.md) | {"egg":2,"level_up":23,"machine":36,"tutor":35} |
| [39: クヌギダマ](pokemon/39.md) | {"egg":8,"level_up":16,"machine":24,"machine_archive":20,"shared_egg":7} |
| [40: フォレトス](pokemon/40.md) | {"egg":2,"level_up":23,"machine":32,"machine_archive":27,"shared_egg":7} |
| [41: シェルダー](pokemon/41.md) | {"egg":7,"level_up":15,"machine":18,"machine_archive":12,"shared_egg":4} |
| [42: パルシェン](pokemon/42.md) | {"egg":2,"level_up":19,"machine":21,"machine_archive":18,"shared_egg":4} |
| [43: マホース](pokemon/43.md) | {"egg":27,"level_up":16,"machine":42,"tutor":28} |
| [44: ペガーン](pokemon/44.md) | {"egg":2,"level_up":14,"machine":45,"tutor":36} |
| [45: ユニサス](pokemon/45.md) | {"egg":2,"level_up":14,"machine":46,"tutor":24} |
| [46: バルキー](pokemon/46.md) | {"egg":7,"level_up":4,"machine":15,"machine_archive":8,"shared_egg":7} |
| [47: サワムラー](pokemon/47.md) | {"egg":1,"level_up":18,"machine":27,"machine_archive":19,"shared_egg":7} |
| [48: エビワラー](pokemon/48.md) | {"egg":1,"level_up":20,"machine":31,"machine_archive":21,"shared_egg":7} |
| [49: カポエラー](pokemon/49.md) | {"egg":1,"level_up":19,"machine":21,"machine_archive":20,"shared_egg":7} |
| [50: ライノス](pokemon/50.md) | {"egg":26,"level_up":17,"machine":46,"tutor":35} |
| [51: メタゲラス](pokemon/51.md) | {"egg":2,"level_up":19,"machine":39,"tutor":44} |
| [52: アブソル](pokemon/52.md) | {"egg":9,"level_up":14,"machine":31,"machine_archive":27,"shared_egg":6} |
| [53: ディザソル](pokemon/53.md) | {"egg":1,"level_up":24,"machine":39,"tutor":9} |
| [54: キリンリキ](pokemon/54.md) | {"egg":9,"level_up":17,"machine":31,"machine_archive":29,"shared_egg":8} |
| [55: フォリキー](pokemon/55.md) | {"egg":1,"level_up":20,"machine":39,"tutor":13} |
| [56: バーニン](pokemon/56.md) | {"egg":27,"level_up":18,"machine":35,"tutor":15} |
| [57: ファントマ](pokemon/57.md) | {"egg":2,"level_up":15,"machine":36,"tutor":27} |
| [58: コイル](pokemon/58.md) | {"egg":2,"level_up":16,"machine":21,"machine_archive":14,"shared_egg":2} |
| [59: レアコイル](pokemon/59.md) | {"egg":2,"level_up":18,"machine":21,"machine_archive":15,"shared_egg":2} |
| [60: ジバコイル](pokemon/60.md) | {"egg":2,"level_up":22,"machine":22,"machine_archive":20,"shared_egg":2} |
| [61: ヒトデマン](pokemon/61.md) | {"egg":1,"level_up":18,"machine":21,"machine_archive":12,"tutor":1} |
| [62: スターミー](pokemon/62.md) | {"egg":2,"level_up":18,"machine":24,"machine_archive":20,"tutor":3} |
| [63: ゴース](pokemon/63.md) | {"egg":14,"level_up":16,"machine":32,"machine_archive":16,"shared_egg":8} |
| [64: ゴースト](pokemon/64.md) | {"egg":2,"level_up":17,"machine":35,"machine_archive":20,"shared_egg":8} |
| [65: ゲンガー](pokemon/65.md) | {"egg":2,"level_up":21,"machine":39,"machine_archive":25,"shared_egg":8} |
| [66: タマタマ](pokemon/66.md) | {"egg":10,"level_up":15,"machine":19,"machine_archive":16,"shared_egg":8} |
| [67: ナッシー](pokemon/67.md) | {"build_learnable_preservation":1,"egg":2,"level_up":19,"machine":23,"machine_archive":28,"move_memory_reminder":1,"shared_egg":8} |
| [68: テディ](pokemon/68.md) | {"egg":28,"level_up":18,"machine":33,"tutor":26} |
| [69: ググズリー](pokemon/69.md) | {"egg":2,"level_up":23,"machine":34,"tutor":20} |
| [70: ハンタマ](pokemon/70.md) | {"egg":25,"level_up":20,"machine":31,"tutor":15} |
| [71: サイホーン](pokemon/71.md) | {"egg":9,"level_up":16,"machine":25,"machine_archive":29,"shared_egg":6} |
| [72: サイドン](pokemon/72.md) | {"egg":2,"level_up":17,"machine":35,"machine_archive":38,"shared_egg":6} |
| [73: ドサイドン](pokemon/73.md) | {"egg":2,"level_up":18,"machine":37,"machine_archive":41,"shared_egg":6} |
| [74: トロピウス](pokemon/74.md) | {"egg":9,"level_up":17,"machine":24,"machine_archive":25,"shared_egg":6} |
| [75: ポリゴン](pokemon/75.md) | {"egg":1,"level_up":15,"machine":20,"machine_archive":16} |
| [76: ポリゴン2](pokemon/76.md) | {"egg":1,"level_up":16,"machine":20,"machine_archive":16} |
| [77: ポリゴンZ](pokemon/77.md) | {"egg":1,"level_up":19,"machine":21,"machine_archive":18} |
| [78: タマザラシ](pokemon/78.md) | {"egg":11,"level_up":15,"machine":17,"machine_archive":9,"shared_egg":9,"tutor_archive":1} |
| [79: トドグラー](pokemon/79.md) | {"egg":2,"level_up":17,"machine":17,"machine_archive":10,"shared_egg":9,"tutor_archive":1} |
| [80: トドゼルガ](pokemon/80.md) | {"egg":2,"level_up":18,"machine":22,"machine_archive":17,"shared_egg":9,"tutor_archive":1} |
| [81: ダンゴロウ](pokemon/81.md) | {"egg":22,"level_up":17,"machine":48,"tutor":10} |
| [82: マルマジロ](pokemon/82.md) | {"egg":2,"level_up":23,"machine":29,"tutor":15} |
| [83: アロフィー](pokemon/83.md) | {"egg":24,"level_up":15,"machine":31,"tutor":17} |
| [84: リーフィス](pokemon/84.md) | {"egg":2,"level_up":22,"machine":30,"tutor":18} |
| [85: ユキカブリ](pokemon/85.md) | {"egg":8,"level_up":14,"machine":20,"machine_archive":16,"shared_egg":5} |
| [86: ユキノオー](pokemon/86.md) | {"egg":2,"level_up":16,"machine":27,"machine_archive":26,"shared_egg":5} |
| [87: ユカリア](pokemon/87.md) | {"egg":22,"level_up":16,"machine":27,"tutor":17} |
| [88: ネクロシア](pokemon/88.md) | {"egg":2,"level_up":23,"machine":42,"tutor":13} |
| [89: カプリン](pokemon/89.md) | {"egg":23,"level_up":14,"machine":41,"tutor":15} |
| [90: ゴートン](pokemon/90.md) | {"egg":1,"level_up":16,"machine":40,"tutor":17} |
| [91: バフォット](pokemon/91.md) | {"egg":2,"level_up":21,"machine":26,"tutor":20} |
| [92: ミルタンク](pokemon/92.md) | {"egg":8,"level_up":15,"machine":29,"machine_archive":24,"shared_egg":7,"tutor_archive":1} |
| [93: ツボツボ](pokemon/93.md) | {"egg":12,"level_up":17,"machine":18,"machine_archive":14,"shared_egg":9,"tutor":1,"tutor_archive":2} |
| [94: バードン](pokemon/94.md) | {"egg":22,"level_up":14,"machine":43,"tutor":21} |
| [95: ゴルドー](pokemon/95.md) | {"egg":2,"level_up":20,"machine":22,"tutor":23} |
| [96: フィニクス](pokemon/96.md) | {"egg":2,"level_up":24,"machine":21,"tutor":23} |
| [97: クロッチ](pokemon/97.md) | {"egg":29,"level_up":19,"machine":44,"tutor":15} |
| [98: コクジャク](pokemon/98.md) | {"egg":2,"level_up":23,"machine":58,"tutor":16} |
| [99: シャミネ](pokemon/99.md) | {"egg":27,"level_up":20,"machine":21,"tutor":26} |
| [100: コーシャン](pokemon/100.md) | {"egg":1,"level_up":21,"machine":17,"tutor":37} |
| [101: プラズン](pokemon/101.md) | {"egg":32,"level_up":17,"machine":37,"tutor":19} |
| [102: ボルトック](pokemon/102.md) | {"egg":2,"level_up":14,"machine":41,"tutor":17} |
| [103: カワラベ](pokemon/103.md) | {"egg":23,"level_up":16,"machine":50,"tutor":23} |
| [104: テペトラー](pokemon/104.md) | {"egg":2,"level_up":21,"machine":47,"tutor":25} |
| [105: ロップル](pokemon/105.md) | {"egg":29,"level_up":20,"machine":27,"tutor":25} |
| [106: オタクン](pokemon/106.md) | {"egg":32,"level_up":17,"machine":26,"tutor":18} |
| [107: ネラー](pokemon/107.md) | {"egg":1,"level_up":17,"machine":35,"tutor":29} |
| [108: ニートン](pokemon/108.md) | {"egg":1,"level_up":17,"machine":28,"tutor":27} |
| [109: ホーホー](pokemon/109.md) | {"egg":9,"level_up":17,"machine":22,"machine_archive":20,"shared_egg":5} |
| [110: ヨルノズク](pokemon/110.md) | {"egg":2,"level_up":18,"machine":22,"machine_archive":28,"shared_egg":5} |
| [111: ハクタクン](pokemon/111.md) | {"egg":28,"level_up":20,"machine":42,"tutor":25} |
| [112: エレキッド](pokemon/112.md) | {"egg":9,"level_up":14,"machine":24,"machine_archive":17,"shared_egg":6} |
| [113: エレブー](pokemon/113.md) | {"egg":1,"level_up":16,"machine":26,"machine_archive":20,"shared_egg":6} |
| [114: エレキブル](pokemon/114.md) | {"egg":1,"level_up":17,"machine":32,"machine_archive":23,"shared_egg":6} |
| [115: ブビィ](pokemon/115.md) | {"egg":10,"level_up":14,"machine":20,"machine_archive":15,"shared_egg":7} |
| [116: ブーバー](pokemon/116.md) | {"egg":1,"level_up":16,"machine":24,"machine_archive":22,"shared_egg":7} |
| [117: ブーバーン](pokemon/117.md) | {"egg":1,"level_up":16,"machine":29,"machine_archive":26,"shared_egg":7} |
| [118: ガルーラ](pokemon/118.md) | {"egg":7,"level_up":15,"machine":27,"machine_archive":31,"shared_egg":6,"tutor":1} |
| [119: リリーラ](pokemon/119.md) | {"egg":7,"level_up":16,"machine":17,"machine_archive":11,"shared_egg":5,"tutor":1} |
| [120: ユレイドル](pokemon/120.md) | {"egg":2,"level_up":17,"machine":21,"machine_archive":16,"shared_egg":5,"tutor":1} |
| [121: スミロドン](pokemon/121.md) | {"egg":23,"level_up":16,"machine":53,"tutor":31} |
| [122: マカドゥス](pokemon/122.md) | {"egg":2,"level_up":20,"machine":47,"tutor":28} |
| [123: プテラ](pokemon/123.md) | {"egg":12,"level_up":15,"machine":22,"machine_archive":24,"shared_egg":6,"tutor":2} |
| [124: ヨーギラス](pokemon/124.md) | {"egg":13,"level_up":18,"machine":22,"machine_archive":20,"shared_egg":9} |
| [125: サナギラス](pokemon/125.md) | {"egg":2,"level_up":18,"machine":22,"machine_archive":23,"shared_egg":9} |
| [126: バンギラス](pokemon/126.md) | {"egg":2,"level_up":24,"machine":38,"machine_archive":41,"shared_egg":9} |
| [127: ダンバル](pokemon/127.md) | {"egg":2,"level_up":1,"machine":3,"machine_archive":3} |
| [128: メタング](pokemon/128.md) | {"egg":2,"level_up":16,"machine":28,"machine_archive":25} |
| [129: メタグロス](pokemon/129.md) | {"build_learnable_preservation":2,"egg":2,"level_up":17,"machine":34,"machine_archive":26,"move_memory_reminder":2} |
| [130: フカマル](pokemon/130.md) | {"egg":6,"level_up":13,"machine":22,"machine_archive":21,"shared_egg":4} |
| [131: ガバイト](pokemon/131.md) | {"egg":2,"level_up":12,"machine":23,"machine_archive":24,"shared_egg":4} |
| [132: ガブリアス](pokemon/132.md) | {"egg":2,"level_up":13,"machine":29,"machine_archive":27,"shared_egg":4} |
| [133: タツゴン](pokemon/133.md) | {"egg":20,"level_up":13,"machine":1,"tutor":11} |
| [134: ラグーン](pokemon/134.md) | {"egg":2,"level_up":17,"machine":2,"tutor":26} |
| [135: ドラドーン](pokemon/135.md) | {"egg":2,"level_up":18,"machine":2,"tutor":45} |
| [136: フリーザー](pokemon/136.md) | {"level_up":17,"machine":23,"machine_archive":18} |
| [137: サンダー](pokemon/137.md) | {"level_up":17,"machine":21,"machine_archive":19} |
| [138: ファイヤー](pokemon/138.md) | {"level_up":18,"machine":21,"machine_archive":20} |
| [139: ライコウ](pokemon/139.md) | {"level_up":18,"machine":24,"machine_archive":22} |
| [140: エンテイ](pokemon/140.md) | {"build_learnable_preservation":2,"level_up":17,"machine":21,"machine_archive":22,"move_memory_reminder":2} |
| [141: スイクン](pokemon/141.md) | {"build_learnable_preservation":2,"level_up":18,"machine":22,"machine_archive":19,"move_memory_reminder":2} |
| [142: ライラプス](pokemon/142.md) | {"egg":2,"level_up":18,"machine":40,"tutor":19} |
| [143: ガニメデ](pokemon/143.md) | {"egg":2,"level_up":18,"machine":35,"tutor":23} |
| [144: ネメア](pokemon/144.md) | {"egg":2,"level_up":18,"machine":46,"tutor":15} |
| [145: ディアルガ](pokemon/145.md) | {"level_up":15,"machine":32,"machine_archive":27} |
| [146: パルキア](pokemon/146.md) | {"level_up":13,"machine":35,"machine_archive":29} |
| [147: ダークライ](pokemon/147.md) | {"level_up":12,"machine":33,"machine_archive":20} |
| [148: ルギア](pokemon/148.md) | {"build_learnable_preservation":1,"level_up":15,"machine":33,"machine_archive":31,"move_memory_reminder":1} |
| [149: ホウオウ](pokemon/149.md) | {"level_up":15,"machine":27,"machine_archive":26} |
| [150: ミュウツー](pokemon/150.md) | {"level_up":19,"machine":47,"machine_archive":44} |
| [151: ミュウ](pokemon/151.md) | {"level_up":13,"machine":98,"machine_archive":131} |
| [152: フシギダネ](pokemon/152.md) | {"egg":5,"level_up":16,"machine":18,"machine_archive":16,"shared_egg":4} |
| [153: フシギソウ](pokemon/153.md) | {"egg":2,"level_up":17,"machine":18,"machine_archive":17,"shared_egg":4} |
| [154: フシギバナ](pokemon/154.md) | {"egg":2,"level_up":20,"machine":23,"machine_archive":23,"shared_egg":4} |
| [155: ヒトカゲ](pokemon/155.md) | {"egg":9,"level_up":12,"machine":22,"machine_archive":24,"shared_egg":8} |
| [156: リザード](pokemon/156.md) | {"egg":1,"level_up":11,"machine":22,"machine_archive":23,"shared_egg":8} |
| [157: リザードン](pokemon/157.md) | {"build_learnable_preservation":1,"egg":2,"level_up":15,"machine":27,"machine_archive":34,"shared_egg":8} |
| [158: ゼニガメ](pokemon/158.md) | {"egg":10,"level_up":15,"machine":19,"machine_archive":17,"shared_egg":9} |
| [159: カメール](pokemon/159.md) | {"egg":1,"level_up":15,"machine":19,"machine_archive":17,"shared_egg":9} |
| [160: カメックス](pokemon/160.md) | {"egg":1,"level_up":15,"machine":27,"machine_archive":26,"shared_egg":9} |
| [161: バジール](pokemon/161.md) | {"egg":26,"level_up":16,"machine":41,"tutor":11} |
| [162: バジルス](pokemon/162.md) | {"egg":2,"level_up":18,"machine":36,"tutor":7} |
| [163: バジリール](pokemon/163.md) | {"egg":2,"level_up":23,"machine":34,"tutor":19} |
| [164: コマシシ](pokemon/164.md) | {"egg":22,"level_up":14,"machine":46,"tutor":22} |
| [165: コマレオ](pokemon/165.md) | {"egg":1,"level_up":16,"machine":44,"tutor":21} |
| [166: コマレオン](pokemon/166.md) | {"egg":2,"level_up":22,"machine":38,"tutor":19} |
| [167: トッコウオ](pokemon/167.md) | {"egg":23,"level_up":13,"machine":46,"tutor":22} |
| [168: ボウソウオ](pokemon/168.md) | {"egg":1,"level_up":17,"machine":40,"tutor":20} |
| [169: バクソウオ](pokemon/169.md) | {"egg":2,"level_up":23,"machine":36,"tutor":21} |
| [170: チェキラ](pokemon/170.md) | {"egg":35,"level_up":16,"machine":31,"tutor":31} |
| [171: チェキッド](pokemon/171.md) | {"egg":1,"level_up":17,"machine":39,"tutor":26} |
| [172: チェキラス](pokemon/172.md) | {"egg":1,"level_up":18,"machine":34,"tutor":22} |
| [173: リバード](pokemon/173.md) | {"egg":25,"level_up":18,"machine":39,"tutor":31} |
| [174: ララミンゴ](pokemon/174.md) | {"egg":2,"level_up":19,"machine":24,"tutor":20} |
| [175: パチリス](pokemon/175.md) | {"egg":13,"level_up":17,"machine":24,"machine_archive":24,"shared_egg":11} |
| [176: パチリック](pokemon/176.md) | {"egg":2,"level_up":20,"machine":40,"tutor":27} |
| [177: パンプリー](pokemon/177.md) | {"egg":31,"level_up":15,"machine":48,"tutor":23} |
| [178: パンプッチ](pokemon/178.md) | {"egg":2,"level_up":20,"machine":44,"tutor":32} |
| [179: ルナビット](pokemon/179.md) | {"egg":29,"level_up":15,"machine":33,"tutor":22} |
| [180: ルナバイン](pokemon/180.md) | {"egg":2,"level_up":22,"machine":46,"tutor":25} |
| [181: ウソギー](pokemon/181.md) | {"egg":30,"level_up":16,"machine":16,"tutor":22} |
| [182: ウソドロ](pokemon/182.md) | {"egg":2,"level_up":21,"machine":40,"tutor":24} |
| [183: メタモン](pokemon/183.md) | {"egg":1,"level_up":1} |
| [184: ムチュール](pokemon/184.md) | {"egg":5,"level_up":14,"machine":19,"machine_archive":25,"shared_egg":3} |
| [185: ルージュラ](pokemon/185.md) | {"egg":2,"level_up":17,"machine":24,"machine_archive":32,"shared_egg":3,"tutor":2} |
| [186: レジュリア](pokemon/186.md) | {"egg":1,"level_up":20,"machine":41,"tutor":15} |
| [187: タダヌキ](pokemon/187.md) | {"egg":28,"level_up":14,"machine":45,"tutor":22} |
| [188: オオムジナ](pokemon/188.md) | {"egg":1,"level_up":17,"machine":31,"tutor":25} |
| [189: ポコキング](pokemon/189.md) | {"egg":1,"level_up":19,"machine":31,"tutor":27} |
| [190: アスイーツ](pokemon/190.md) | {"egg":1,"level_up":17,"machine":26,"tutor":14} |
| [191: コユキムシ](pokemon/191.md) | {"egg":31,"level_up":16,"machine":45,"tutor":14} |
| [192: ユキタテハ](pokemon/192.md) | {"egg":2,"level_up":21,"machine":46,"tutor":19} |
| [193: ペラップ](pokemon/193.md) | {"egg":13,"level_up":21,"machine":10,"machine_archive":16,"tutor":5,"tutor_archive":3} |
| [194: オオペラー](pokemon/194.md) | {"egg":1,"level_up":24,"machine":44,"tutor":15} |
| [195: オリバー](pokemon/195.md) | {"egg":29,"level_up":16,"machine":45,"tutor":16} |
| [196: ランペルン](pokemon/196.md) | {"egg":30,"level_up":18,"machine":33,"tutor":19} |
| [197: キーボン](pokemon/197.md) | {"egg":30,"level_up":16,"machine":27,"tutor":13} |
| [198: レディバ](pokemon/198.md) | {"egg":17,"level_up":15,"machine":12,"machine_archive":16,"tutor":4,"tutor_archive":6} |
| [199: レディアン](pokemon/199.md) | {"egg":2,"level_up":17,"machine":13,"machine_archive":18,"tutor":5,"tutor_archive":6} |
| [200: レディバル](pokemon/200.md) | {"egg":2,"level_up":26,"machine":65,"tutor":30} |
| [201: アンノーン](pokemon/201.md) | {"egg":1,"level_up":2,"machine_archive":1} |
| [202: ケンタル](pokemon/202.md) | {"egg":1,"level_up":16,"machine":21,"tutor":17} |
| [203: ケンタロス](pokemon/203.md) | {"egg":2,"level_up":15,"machine":26,"machine_archive":22,"shared_egg":2} |
| [204: ルナトーン](pokemon/204.md) | {"egg":2,"level_up":18,"machine":26,"machine_archive":28,"tutor":1} |
| [205: ソルロック](pokemon/205.md) | {"egg":2,"level_up":17,"machine":30,"machine_archive":28,"tutor":1} |
| [206: アスリスク](pokemon/206.md) | {"egg":1,"level_up":19,"machine":29,"tutor":18} |
| [207: プラネム](pokemon/207.md) | {"egg":1,"level_up":12,"machine":44,"tutor":15} |
| [208: モドラ](pokemon/208.md) | {"egg":29,"level_up":17,"machine":44,"tutor":29} |
| [209: コモラゴン](pokemon/209.md) | {"egg":2,"level_up":21,"machine":50,"tutor":26} |
| [210: テッポウオ](pokemon/210.md) | {"egg":6,"level_up":15,"machine":21,"machine_archive":17,"shared_egg":6} |
| [211: オクタン](pokemon/211.md) | {"egg":1,"level_up":20,"machine":26,"machine_archive":19,"shared_egg":6,"tutor_archive":1} |
| [212: メノクラゲ](pokemon/212.md) | {"egg":10,"level_up":15,"machine":27,"machine_archive":12,"shared_egg":9} |
| [213: ドククラゲ](pokemon/213.md) | {"egg":2,"level_up":16,"machine":27,"machine_archive":17,"shared_egg":9} |
| [214: ヤミクラゲ](pokemon/214.md) | {"egg":2,"level_up":13,"machine":48,"tutor":20} |
| [215: コイナリ](pokemon/215.md) | {"egg":25,"level_up":19,"machine":40,"tutor":22} |
| [216: オオイナリ](pokemon/216.md) | {"egg":1,"level_up":23,"machine":41,"tutor":24} |
| [217: キャンペル](pokemon/217.md) | {"egg":29,"level_up":18,"machine":45,"tutor":28} |
| [218: ホムロソク](pokemon/218.md) | {"egg":2,"level_up":18,"machine":38,"tutor":32} |
| [219: ガレキダマ](pokemon/219.md) | {"egg":24,"level_up":21,"machine":50,"tutor":35} |
| [220: ジバクン](pokemon/220.md) | {"egg":32,"level_up":12,"machine":49,"tutor":31} |
| [221: ワラコゾウ](pokemon/221.md) | {"egg":31,"level_up":17,"machine":50,"tutor":1} |
| [222: ワラガシラ](pokemon/222.md) | {"egg":2,"level_up":16,"machine":57,"tutor":2} |
| [223: ビリリダマ](pokemon/223.md) | {"egg":2,"level_up":18,"machine":17,"machine_archive":13,"shared_egg":2} |
| [224: マルマイン](pokemon/224.md) | {"egg":1,"level_up":19,"machine":17,"machine_archive":18,"shared_egg":2} |
| [225: ドルマイン](pokemon/225.md) | {"egg":1,"level_up":12,"machine":32,"tutor":36} |
| [226: ヤミカラス](pokemon/226.md) | {"egg":13,"level_up":15,"machine":27,"machine_archive":19,"shared_egg":9} |
| [227: ドンカラス](pokemon/227.md) | {"build_learnable_preservation":5,"egg":2,"level_up":15,"machine":29,"machine_archive":21,"shared_egg":9} |
| [228: ゴニョニョ](pokemon/228.md) | {"egg":9,"level_up":14,"machine":14,"machine_archive":18,"shared_egg":8} |
| [229: ドゴーム](pokemon/229.md) | {"egg":1,"level_up":16,"machine":20,"machine_archive":21,"shared_egg":8} |
| [230: バクオング](pokemon/230.md) | {"egg":1,"level_up":22,"machine":22,"machine_archive":31,"shared_egg":8,"tutor":1} |
| [231: クラブ](pokemon/231.md) | {"egg":7,"level_up":15,"machine":20,"machine_archive":16,"shared_egg":5} |
| [232: キングラー](pokemon/232.md) | {"egg":1,"level_up":17,"machine":21,"machine_archive":21,"shared_egg":5} |
| [233: プカスカ](pokemon/233.md) | {"egg":25,"level_up":19,"machine":37,"tutor":9} |
| [234: スモーガス](pokemon/234.md) | {"egg":2,"level_up":22,"machine":33,"tutor":27} |
| [235: ココロン](pokemon/235.md) | {"egg":1,"level_up":19,"machine":28,"tutor":22} |
| [236: カモドック](pokemon/236.md) | {"egg":1,"level_up":19,"machine":45,"tutor":31} |
| [237: トノッパー](pokemon/237.md) | {"egg":1,"level_up":19,"machine":38,"tutor":33} |
| [238: ガルラーダ](pokemon/238.md) | {"egg":2,"level_up":21,"machine":41,"tutor":13} |
| [239: ハサーガ](pokemon/239.md) | {"egg":2,"level_up":21,"machine":39,"tutor":31} |
| [240: アメクジ](pokemon/240.md) | {"egg":28,"level_up":16,"machine":40,"tutor":26} |
| [241: アメリシア](pokemon/241.md) | {"egg":2,"level_up":23,"machine":16,"tutor":26} |
| [242: カララン](pokemon/242.md) | {"egg":26,"level_up":19,"machine":9,"tutor":23} |
| [243: カンカーン](pokemon/243.md) | {"egg":2,"level_up":23,"machine":18,"tutor":6} |
| [244: クラウン](pokemon/244.md) | {"egg":29,"level_up":18,"machine":23,"tutor":21} |
| [245: テイルーン](pokemon/245.md) | {"egg":2,"level_up":24,"machine":22,"tutor":13} |
| [246: モグルトン](pokemon/246.md) | {"egg":29,"level_up":19,"machine":27,"tutor":31} |
| [247: ニューラ](pokemon/247.md) | {"egg":11,"level_up":13,"machine":29,"machine_archive":25,"shared_egg":8} |
| [248: マニューラ](pokemon/248.md) | {"egg":2,"level_up":21,"machine":33,"machine_archive":27,"shared_egg":8} |
| [249: キノココ](pokemon/249.md) | {"egg":5,"level_up":15,"machine":19,"machine_archive":12,"shared_egg":4} |
| [250: キノガッサ](pokemon/250.md) | {"build_learnable_preservation":1,"egg":2,"level_up":19,"machine":29,"machine_archive":25,"move_memory_reminder":1,"shared_egg":4} |
| [251: ラクチャン](pokemon/251.md) | {"egg":1,"level_up":12,"machine":37,"tutor":30} |
| [252: フシギバナ](pokemon/252.md) | {"level_up":22,"machine":29,"tutor":22} |
| [253: リザードン](pokemon/253.md) | {"level_up":21,"machine":34,"tutor":24} |
| [254: カメックス](pokemon/254.md) | {"level_up":20,"machine":28,"tutor":14} |
| [255: ストライク](pokemon/255.md) | {"egg":5,"level_up":14,"machine":22,"machine_archive":18,"shared_egg":5} |
| [256: ピカチュウ](pokemon/256.md) | {"level_up":14,"machine":34,"tutor":7} |
| [257: アスフィア](pokemon/257.md) | {"level_up":18,"machine":34,"tutor":29} |
| [258: アスフィア](pokemon/258.md) | {"level_up":18,"machine":29,"tutor":30} |
| [259: ラクチャン](pokemon/259.md) | {"level_up":10,"machine":37,"tutor":17} |
| [260: ルギア](pokemon/260.md) | {"level_up":16,"machine":45,"tutor":29} |
| [261: ディアルガ](pokemon/261.md) | {"level_up":14,"machine":44,"tutor":33} |
| [262: ネメア](pokemon/262.md) | {"level_up":14,"machine":34,"tutor":40} |
| [263: ？](pokemon/263.md) | {"machine":36,"tutor":32} |
| [264: ？](pokemon/264.md) | {"machine":43,"tutor":26} |
| [265: ？](pokemon/265.md) | {"machine":32,"tutor":29} |
| [266: ？](pokemon/266.md) | {"machine":40,"tutor":27} |
| [267: ？](pokemon/267.md) | {"machine":8,"tutor":19} |
| [268: ？](pokemon/268.md) | {"machine":23,"tutor":26} |
| [269: ？](pokemon/269.md) | {"machine":21,"tutor":32} |
| [270: ？](pokemon/270.md) | {"machine":31,"tutor":38} |
| [271: ？](pokemon/271.md) | {"machine":34,"tutor":19} |
| [272: ？](pokemon/272.md) | {"machine":20,"tutor":38} |
| [273: ？](pokemon/273.md) | {"machine":27,"tutor":31} |
| [274: ？](pokemon/274.md) | {"machine":31,"tutor":25} |
| [275: ？](pokemon/275.md) | {"machine":34,"tutor":19} |
| [276: ？](pokemon/276.md) | {"machine":34,"tutor":24} |
| [277: ドゴン](pokemon/277.md) | {"egg":26,"level_up":22,"machine":34,"tutor":21} |
| [278: ヤミラミ](pokemon/278.md) | {"egg":12,"level_up":19,"machine":38,"machine_archive":34,"shared_egg":6} |
| [279: トコヤミ](pokemon/279.md) | {"egg":2,"level_up":29,"machine":32,"tutor":26} |
| [280: クチート](pokemon/280.md) | {"egg":8,"level_up":18,"machine":33,"machine_archive":24,"shared_egg":5,"tutor":1} |
| [281: クチールス](pokemon/281.md) | {"egg":2,"level_up":28,"machine":37,"tutor":23} |
| [282: ストライク](pokemon/282.md) | {"egg":23,"level_up":18,"machine":34,"tutor":20} |
| [283: ハッサム](pokemon/283.md) | {"build_learnable_preservation":3,"egg":2,"level_up":19,"machine":27,"machine_archive":24,"shared_egg":5} |
| [284: カイロス](pokemon/284.md) | {"egg":8,"level_up":16,"machine":21,"machine_archive":18,"shared_egg":5} |
| [285: ガッツロス](pokemon/285.md) | {"egg":1,"level_up":20,"machine":38,"tutor":28} |
| [286: アーボ](pokemon/286.md) | {"egg":9,"level_up":18,"machine":25,"machine_archive":18,"shared_egg":6} |
| [287: アーボック](pokemon/287.md) | {"egg":1,"level_up":22,"machine":29,"machine_archive":25,"shared_egg":6} |
| [288: アーボスク](pokemon/288.md) | {"egg":2,"level_up":29,"machine":43,"tutor":31} |
| [289: ドガース](pokemon/289.md) | {"egg":11,"level_up":17,"machine":20,"machine_archive":14,"shared_egg":6} |
| [290: マタドガス](pokemon/290.md) | {"egg":1,"level_up":19,"machine":21,"machine_archive":16,"shared_egg":6} |
| [291: モアドガス](pokemon/291.md) | {"egg":2,"level_up":23,"machine":38,"tutor":31} |
| [292: ヨマワル](pokemon/292.md) | {"egg":9,"level_up":16,"machine":22,"machine_archive":18,"shared_egg":3} |
| [293: サマヨール](pokemon/293.md) | {"egg":1,"level_up":23,"machine":26,"machine_archive":23,"shared_egg":3} |
| [294: ヨノワール](pokemon/294.md) | {"egg":1,"level_up":25,"machine":29,"machine_archive":26,"shared_egg":3} |
| [295: ベロリンガ](pokemon/295.md) | {"egg":6,"level_up":15,"machine":28,"machine_archive":25,"shared_egg":4,"tutor":1,"tutor_archive":1} |
| [296: ベロベルト](pokemon/296.md) | {"egg":1,"level_up":17,"machine":29,"machine_archive":27,"shared_egg":4,"tutor":1,"tutor_archive":1} |
| [297: イトマル](pokemon/297.md) | {"egg":6,"level_up":19,"machine":21,"machine_archive":17,"shared_egg":5} |
| [298: アリアドス](pokemon/298.md) | {"egg":2,"level_up":23,"machine":24,"machine_archive":19,"shared_egg":5} |
| [299: バチュル](pokemon/299.md) | {"egg":7,"level_up":17,"machine":20,"machine_archive":12,"shared_egg":5} |
| [300: デンチュラ](pokemon/300.md) | {"egg":2,"level_up":17,"machine":21,"machine_archive":15,"shared_egg":5} |
| [301: ツチニン](pokemon/301.md) | {"egg":5,"level_up":13,"machine":10,"machine_archive":8,"shared_egg":5,"tutor_archive":1} |
| [302: テッカニン](pokemon/302.md) | {"egg":2,"level_up":25,"machine":16,"machine_archive":14,"shared_egg":5,"tutor":1,"tutor_archive":1} |
| [303: ヌケニン](pokemon/303.md) | {"egg":2,"level_up":19,"machine":13,"machine_archive":14,"shared_egg":5,"tutor":1,"tutor_archive":1} |
| [304: マグッピ](pokemon/304.md) | {"egg":31,"level_up":17,"machine":37,"tutor":35} |
| [305: ベタデーム](pokemon/305.md) | {"egg":1,"level_up":18,"machine":39,"tutor":32} |
| [306: テッコンボ](pokemon/306.md) | {"egg":1,"level_up":22,"machine":42,"tutor":30} |
| [307: ボンバット](pokemon/307.md) | {"egg":31,"level_up":22,"machine":29,"tutor":16} |
| [308: パッチール](pokemon/308.md) | {"egg":19,"level_up":18,"machine":12,"machine_archive":18,"tutor":11,"tutor_archive":11} |
| [309: ジーランス](pokemon/309.md) | {"egg":5,"level_up":14,"machine":24,"machine_archive":20,"shared_egg":2,"tutor":2} |
| [310: ダンカンス](pokemon/310.md) | {"egg":2,"level_up":25,"machine":38,"tutor":2} |
| [311: ドサーモン](pokemon/311.md) | {"egg":2,"level_up":22,"machine":35,"tutor":15} |
| [312: テッケン](pokemon/312.md) | {"egg":28,"level_up":18,"machine":37,"tutor":33} |
| [313: カゲボウズ](pokemon/313.md) | {"egg":9,"level_up":18,"machine":27,"machine_archive":19,"shared_egg":5} |
| [314: ジュペッタ](pokemon/314.md) | {"build_learnable_preservation":1,"egg":1,"level_up":19,"machine":33,"machine_archive":22,"shared_egg":5} |
| [315: ラルトス](pokemon/315.md) | {"egg":8,"level_up":17,"machine":30,"machine_archive":24,"shared_egg":8} |
| [316: キルリア](pokemon/316.md) | {"egg":2,"level_up":17,"machine":30,"machine_archive":26,"shared_egg":8} |
| [317: イシズマイ](pokemon/317.md) | {"egg":7,"level_up":16,"machine":16,"machine_archive":10,"shared_egg":6,"tutor_archive":1} |
| [318: サボネア](pokemon/318.md) | {"egg":12,"level_up":19,"machine":28,"machine_archive":21,"shared_egg":8} |
| [319: ノクタス](pokemon/319.md) | {"egg":2,"level_up":20,"machine":34,"machine_archive":25,"shared_egg":8} |
| [320: ヒョウカク](pokemon/320.md) | {"egg":2,"level_up":22,"machine":25,"tutor":15} |
| [321: イノムー](pokemon/321.md) | {"egg":2,"level_up":17,"machine":21,"machine_archive":24,"shared_egg":7} |
| [322: サーナイト](pokemon/322.md) | {"egg":2,"level_up":23,"machine":33,"machine_archive":32,"shared_egg":8} |
| [323: プレシオン](pokemon/323.md) | {"egg":35,"level_up":21,"machine":34,"tutor":16} |
| [324: ラプラス](pokemon/324.md) | {"egg":7,"level_up":16,"machine":26,"machine_archive":26,"shared_egg":7} |
| [325: ドレディア](pokemon/325.md) | {"egg":1,"level_up":21,"machine":16,"machine_archive":16,"shared_egg":4} |
| [326: メルリコ](pokemon/326.md) | {"egg":29,"level_up":18,"machine":29,"tutor":13} |
| [327: サムラダケ](pokemon/327.md) | {"egg":1,"level_up":19,"machine":36,"tutor":15} |
| [328: ブレイドン](pokemon/328.md) | {"egg":1,"level_up":21,"machine":28,"tutor":10} |
| [329: ブレイオー](pokemon/329.md) | {"egg":2,"level_up":23,"machine":39,"tutor":11} |
| [330: スコルピ](pokemon/330.md) | {"egg":8,"level_up":18,"machine":18,"machine_archive":18,"shared_egg":4,"tutor_archive":1} |
| [331: ドラピオン](pokemon/331.md) | {"egg":2,"level_up":23,"machine":25,"machine_archive":28,"shared_egg":4,"tutor":1,"tutor_archive":1} |
| [332: マスキッパ](pokemon/332.md) | {"egg":15,"level_up":15,"machine":10,"machine_archive":17,"tutor":5,"tutor_archive":6} |
| [333: アルデッパ](pokemon/333.md) | {"egg":2,"level_up":22,"machine":39,"tutor":16} |
| [334: ゴキブロス](pokemon/334.md) | {"egg":27,"level_up":20,"machine":39,"tutor":11} |
| [335: ビビッドン](pokemon/335.md) | {"egg":2,"level_up":27,"machine":34,"tutor":11} |
| [336: ドルン](pokemon/336.md) | {"egg":27,"level_up":18,"machine":41,"tutor":15} |
| [337: バーネッコ](pokemon/337.md) | {"egg":1,"level_up":21,"machine":46,"tutor":13} |
| [338: コケゾー](pokemon/338.md) | {"egg":22,"level_up":17,"machine":34,"tutor":14} |
| [339: オンネット](pokemon/339.md) | {"egg":1,"level_up":23,"machine":42,"tutor":1} |
| [340: ウリムー](pokemon/340.md) | {"egg":8,"level_up":13,"machine":20,"machine_archive":22,"shared_egg":7} |
| [341: ノコッチ](pokemon/341.md) | {"egg":8,"level_up":16,"machine":32,"machine_archive":34,"shared_egg":6} |
| [342: ノコウテイ](pokemon/342.md) | {"egg":1,"level_up":26,"machine":32,"tutor":20} |
| [343: カモネギ](pokemon/343.md) | {"egg":18,"level_up":17,"machine":20,"machine_archive":17,"shared_egg":13,"tutor":1} |
| [344: カミギリー](pokemon/344.md) | {"egg":2,"level_up":22,"machine":17,"tutor":16} |
| [345: レファン](pokemon/345.md) | {"egg":32,"level_up":18,"machine":18,"tutor":16} |
| [346: コータス](pokemon/346.md) | {"egg":9,"level_up":19,"machine":24,"machine_archive":21,"shared_egg":4} |
| [347: ストータス](pokemon/347.md) | {"egg":1,"level_up":25,"machine":27,"tutor":29} |
| [348: ラブカス](pokemon/348.md) | {"egg":4,"level_up":17,"machine":15,"machine_archive":11,"shared_egg":4} |
| [349: ラブリン](pokemon/349.md) | {"egg":1,"level_up":18,"machine":29,"tutor":20} |
| [350: オールガ](pokemon/350.md) | {"egg":1,"level_up":21,"machine":29,"tutor":20} |
| [351: マンムー](pokemon/351.md) | {"egg":2,"level_up":18,"machine":25,"machine_archive":27,"shared_egg":7} |
| [352: マッギョ](pokemon/352.md) | {"egg":9,"level_up":16,"machine":21,"machine_archive":16,"shared_egg":7,"tutor":1} |
| [353: ヒカリゴケ](pokemon/353.md) | {"egg":2,"level_up":24,"machine":35,"tutor":22} |
| [354: フリージオ](pokemon/354.md) | {"egg":3,"level_up":20,"machine":20,"machine_archive":12,"shared_egg":3} |
| [355: エルレイド](pokemon/355.md) | {"egg":2,"level_up":35,"machine":47,"machine_archive":42,"shared_egg":8} |
| [356: セルディー](pokemon/356.md) | {"egg":1,"level_up":23,"machine":36,"tutor":22} |
| [357: コゴボー](pokemon/357.md) | {"egg":26,"level_up":17,"machine":32,"tutor":23} |
| [358: ガネーシャ](pokemon/358.md) | {"egg":1,"level_up":22,"machine":35,"tutor":24} |
| [359: ギアル](pokemon/359.md) | {"egg":1,"level_up":16,"machine":11,"machine_archive":9,"tutor":2,"tutor_archive":1} |
| [360: プレゼンタ](pokemon/360.md) | {"egg":1,"level_up":15,"machine":36,"tutor":21} |
| [361: ナットレイ](pokemon/361.md) | {"egg":2,"level_up":16,"machine":23,"machine_archive":18,"shared_egg":5,"tutor":1,"tutor_archive":1} |
| [362: シビシラス](pokemon/362.md) | {"egg":1,"level_up":4,"machine":4,"machine_archive":1} |
| [363: イシツブテ](pokemon/363.md) | {"egg":10,"level_up":15,"machine":19,"machine_archive":19,"shared_egg":7} |
| [364: ピンプク](pokemon/364.md) | {"egg":7,"level_up":7,"machine":16,"machine_archive":11,"shared_egg":4} |
| [365: ラッキー](pokemon/365.md) | {"egg":1,"level_up":21,"machine":35,"machine_archive":26,"shared_egg":4} |
| [366: ハピナス](pokemon/366.md) | {"egg":1,"level_up":21,"machine":35,"machine_archive":31,"shared_egg":4} |
| [367: ゴローン](pokemon/367.md) | {"egg":2,"level_up":15,"machine":22,"machine_archive":21,"shared_egg":7} |
| [368: ゴローニャ](pokemon/368.md) | {"build_learnable_preservation":1,"egg":2,"level_up":16,"machine":22,"machine_archive":24,"shared_egg":7} |
| [369: シビビール](pokemon/369.md) | {"build_learnable_preservation":1,"egg":1,"level_up":16,"machine":20,"machine_archive":14} |
| [370: サンド](pokemon/370.md) | {"egg":7,"level_up":19,"machine":24,"machine_archive":26,"shared_egg":6} |
| [371: サンドパン](pokemon/371.md) | {"egg":1,"level_up":20,"machine":26,"machine_archive":29,"shared_egg":6} |
| [372: サンドリル](pokemon/372.md) | {"egg":1,"level_up":22,"machine":30,"tutor":28} |
| [373: カモナイツ](pokemon/373.md) | {"egg":2,"level_up":24,"machine":31,"tutor":23} |
| [374: ズルッグ](pokemon/374.md) | {"egg":5,"level_up":17,"machine":35,"machine_archive":26,"shared_egg":4} |
| [375: ズルズキン](pokemon/375.md) | {"egg":2,"level_up":17,"machine":36,"machine_archive":33,"shared_egg":4} |
| [376: デリバード](pokemon/376.md) | {"egg":14,"level_up":2,"machine":29,"machine_archive":21,"shared_egg":11} |
| [377: イワパレス](pokemon/377.md) | {"egg":2,"level_up":15,"machine":18,"machine_archive":14,"shared_egg":6,"tutor":1,"tutor_archive":1} |
| [378: テッシード](pokemon/378.md) | {"egg":11,"level_up":14,"machine":17,"machine_archive":12,"shared_egg":5,"tutor":1,"tutor_archive":1} |
| [379: ギギギアル](pokemon/379.md) | {"egg":1,"level_up":24,"machine":12,"machine_archive":12,"tutor":2,"tutor_archive":1} |
| [380: ギギアル](pokemon/380.md) | {"egg":1,"level_up":19,"machine":11,"machine_archive":9,"tutor":2,"tutor_archive":1} |
| [381: チュリネ](pokemon/381.md) | {"egg":8,"level_up":17,"machine":14,"machine_archive":8,"shared_egg":4} |
| [382: キルギシア](pokemon/382.md) | {"egg":2,"level_up":26,"machine":36,"tutor":34} |
| [383: シルドール](pokemon/383.md) | {"egg":2,"level_up":27,"machine":37,"tutor":18} |
| [384: セルシィ](pokemon/384.md) | {"egg":31,"level_up":18,"machine":35,"tutor":19} |
| [385: テルテン](pokemon/385.md) | {"egg":29,"level_up":21,"machine":39,"tutor":9} |
| [386: ワークロ](pokemon/386.md) | {"egg":30,"level_up":22,"machine":46,"tutor":19} |
| [387: アリンセス](pokemon/387.md) | {"egg":29,"level_up":22,"machine":39,"tutor":31} |
| [388: ティオルス](pokemon/388.md) | {"egg":26,"level_up":17,"machine":37,"tutor":36} |
| [389: プテリクス](pokemon/389.md) | {"egg":2,"level_up":23,"machine":39,"tutor":41} |
| [390: ティラノス](pokemon/390.md) | {"egg":37,"level_up":21,"machine":49,"tutor":24} |
| [391: ブレイバー](pokemon/391.md) | {"egg":32,"level_up":17,"machine":45,"tutor":26} |
| [392: ヤマネツ](pokemon/392.md) | {"egg":26,"level_up":19,"machine":34,"tutor":31} |
| [393: ヒササビ](pokemon/393.md) | {"egg":2,"level_up":23,"machine":12,"tutor":47} |
| [394: シャーモン](pokemon/394.md) | {"egg":22,"level_up":18,"machine":16,"tutor":46} |
| [395: コジョフー](pokemon/395.md) | {"egg":3,"level_up":15,"machine":25,"machine_archive":16,"shared_egg":3} |
| [396: コジョンド](pokemon/396.md) | {"egg":1,"level_up":17,"machine":26,"machine_archive":21,"shared_egg":3} |
| [397: メグロコ](pokemon/397.md) | {"egg":8,"level_up":17,"machine":23,"machine_archive":21,"shared_egg":4} |
| [398: ワルビル](pokemon/398.md) | {"egg":2,"level_up":17,"machine":27,"machine_archive":27,"shared_egg":4} |
| [399: ワルビアル](pokemon/399.md) | {"egg":2,"level_up":18,"machine":32,"machine_archive":33,"shared_egg":4} |
| [400: ロイツァー](pokemon/400.md) | {"egg":1,"level_up":19,"machine":32,"tutor":28} |
| [401: ガタノア](pokemon/401.md) | {"egg":2,"level_up":21,"machine":24,"tutor":23} |
| [402: テツカブリ](pokemon/402.md) | {"egg":2,"level_up":19,"machine":37,"tutor":27} |
| [403: ヒードラン](pokemon/403.md) | {"level_up":17,"machine":28,"machine_archive":25} |
| [404: フィオネ](pokemon/404.md) | {"level_up":13,"machine":22,"machine_archive":13} |
| [405: マナフィ](pokemon/405.md) | {"level_up":15,"machine":27,"machine_archive":21} |
| [406: オルディナ](pokemon/406.md) | {"egg":1,"level_up":19,"machine":29,"tutor":32} |
| [407: ラティアス](pokemon/407.md) | {"level_up":17,"machine":37,"machine_archive":32} |
| [408: ラティオス](pokemon/408.md) | {"level_up":16,"machine":38,"machine_archive":28} |
| [409: オルマリア](pokemon/409.md) | {"egg":1,"level_up":19,"machine":26,"tutor":26} |
| [410: アスフィア](pokemon/410.md) | {"egg":2,"level_up":22,"machine":38,"tutor":32} |
| [411: シビルドン](pokemon/411.md) | {"build_learnable_preservation":3,"egg":1,"level_up":13,"machine":35,"machine_archive":27} |
| [412: タマゴ](pokemon/412.md) | {"tutor":15} |
| [413: トランセル](pokemon/413.md) | {"build_learnable_preservation":2,"egg":1,"level_up":2,"machine":2} |
| [414: バタフリー](pokemon/414.md) | {"egg":2,"level_up":19,"machine":19,"machine_archive":14,"tutor":1} |
| [415: ビードル](pokemon/415.md) | {"egg":2,"level_up":3,"tutor":2} |
| [416: コクーン](pokemon/416.md) | {"build_learnable_preservation":1,"egg":2,"level_up":2,"tutor":2,"tutor_archive":1} |
| [417: スピアー](pokemon/417.md) | {"build_learnable_preservation":3,"egg":2,"level_up":15,"machine":14,"machine_archive":19,"tutor":8,"tutor_archive":3} |
| [418: ポッポ](pokemon/418.md) | {"egg":9,"level_up":14,"machine":9,"machine_archive":14,"tutor":4,"tutor_archive":2} |
| [419: ピジョン](pokemon/419.md) | {"build_learnable_preservation":5,"egg":2,"level_up":16,"machine":9,"machine_archive":14,"tutor":4,"tutor_archive":2} |
| [420: ピジョット](pokemon/420.md) | {"build_learnable_preservation":5,"egg":2,"level_up":18,"machine":9,"machine_archive":16,"tutor":4,"tutor_archive":3} |
| [421: コラッタ](pokemon/421.md) | {"egg":11,"level_up":13,"machine":15,"machine_archive":14,"tutor":6,"tutor_archive":4} |
| [422: ラッタ](pokemon/422.md) | {"build_learnable_preservation":8,"egg":1,"level_up":18,"machine":16,"machine_archive":17,"tutor":7,"tutor_archive":5} |
| [423: オニスズメ](pokemon/423.md) | {"egg":11,"level_up":12,"machine":10,"machine_archive":15,"tutor":5,"tutor_archive":2} |
| [424: オニドリル](pokemon/424.md) | {"build_learnable_preservation":8,"egg":2,"level_up":17,"machine":10,"machine_archive":17,"tutor":6,"tutor_archive":3} |
| [425: ピッピ](pokemon/425.md) | {"build_learnable_preservation":4,"egg":1,"level_up":21,"machine":36,"machine_archive":36,"shared_egg":4} |
| [426: ピクシー](pokemon/426.md) | {"build_learnable_preservation":16,"egg":1,"level_up":4,"machine":37,"machine_archive":39,"move_memory_reminder":17,"shared_egg":4} |
| [427: ロコン](pokemon/427.md) | {"egg":8,"level_up":15,"machine":20,"machine_archive":21,"shared_egg":8} |
| [428: キュウコン](pokemon/428.md) | {"build_learnable_preservation":12,"egg":1,"level_up":3,"machine":22,"machine_archive":29,"move_memory_reminder":13,"shared_egg":8} |
| [429: プリン](pokemon/429.md) | {"build_learnable_preservation":6,"egg":2,"level_up":20,"machine":41,"machine_archive":36,"shared_egg":8} |
| [430: プクリン](pokemon/430.md) | {"build_learnable_preservation":6,"egg":2,"level_up":21,"machine":42,"machine_archive":39,"shared_egg":8} |
| [431: ズバット](pokemon/431.md) | {"egg":7,"level_up":13,"machine":19,"machine_archive":15,"shared_egg":7,"tutor":1} |
| [432: ゴルバット](pokemon/432.md) | {"build_learnable_preservation":7,"egg":2,"level_up":14,"machine":19,"machine_archive":18,"shared_egg":7,"tutor":1} |
| [433: ナゾノクサ](pokemon/433.md) | {"egg":9,"level_up":14,"machine":16,"machine_archive":10,"shared_egg":9} |
| [434: クサイハナ](pokemon/434.md) | {"build_learnable_preservation":8,"egg":2,"level_up":14,"machine":16,"machine_archive":12,"shared_egg":9} |
| [435: ラフレシア](pokemon/435.md) | {"build_learnable_preservation":8,"egg":2,"level_up":15,"machine":18,"machine_archive":18,"shared_egg":9} |
| [436: パラス](pokemon/436.md) | {"egg":17,"level_up":12,"machine":14,"machine_archive":15,"tutor":3,"tutor_archive":5} |
| [437: パラセクト](pokemon/437.md) | {"build_learnable_preservation":15,"egg":2,"level_up":16,"machine":14,"machine_archive":17,"tutor":4,"tutor_archive":5} |
| [438: コンパン](pokemon/438.md) | {"egg":8,"level_up":13,"machine":17,"machine_archive":19,"shared_egg":8} |
| [439: モルフォン](pokemon/439.md) | {"build_learnable_preservation":3,"egg":2,"level_up":15,"machine":21,"machine_archive":23,"shared_egg":8} |
| [440: ニャース](pokemon/440.md) | {"egg":6,"level_up":13,"machine":29,"machine_archive":20,"shared_egg":6} |
| [441: ペルシアン](pokemon/441.md) | {"build_learnable_preservation":5,"egg":1,"level_up":15,"machine":29,"machine_archive":24,"shared_egg":6} |
| [442: コダック](pokemon/442.md) | {"egg":7,"level_up":14,"machine":30,"machine_archive":25,"shared_egg":7} |
| [443: ゴルダック](pokemon/443.md) | {"build_learnable_preservation":5,"egg":1,"level_up":16,"machine":32,"machine_archive":29,"shared_egg":7} |
| [444: マンキー](pokemon/444.md) | {"egg":6,"level_up":16,"machine":33,"machine_archive":21,"shared_egg":6} |
| [445: オコリザル](pokemon/445.md) | {"build_learnable_preservation":4,"egg":1,"level_up":17,"machine":34,"machine_archive":26,"shared_egg":6} |
| [446: ガーディ](pokemon/446.md) | {"egg":6,"level_up":16,"machine":16,"machine_archive":23,"shared_egg":6} |
| [447: ウインディ](pokemon/447.md) | {"build_learnable_preservation":5,"egg":1,"level_up":17,"machine":19,"machine_archive":30,"shared_egg":6} |
| [448: ニョロモ](pokemon/448.md) | {"egg":5,"level_up":11,"machine":20,"machine_archive":18,"shared_egg":5} |
| [449: ニョロゾ](pokemon/449.md) | {"build_learnable_preservation":2,"egg":1,"level_up":11,"machine":24,"machine_archive":21,"shared_egg":5} |
| [450: ニョロボン](pokemon/450.md) | {"build_learnable_preservation":6,"egg":2,"level_up":4,"machine":33,"machine_archive":31,"move_memory_reminder":9,"shared_egg":5} |
| [451: ケーシィ](pokemon/451.md) | {"egg":3,"level_up":1,"machine":27,"machine_archive":21,"shared_egg":3} |
| [452: ユンゲラー](pokemon/452.md) | {"build_learnable_preservation":2,"egg":1,"level_up":14,"machine":27,"machine_archive":23,"shared_egg":3,"tutor":1} |
| [453: フーディン](pokemon/453.md) | {"build_learnable_preservation":2,"egg":1,"level_up":13,"machine":28,"machine_archive":28,"shared_egg":3,"tutor":1} |
| [454: ワンリキー](pokemon/454.md) | {"egg":5,"level_up":15,"machine":23,"machine_archive":23,"shared_egg":5,"tutor":1} |
| [455: ゴーリキー](pokemon/455.md) | {"build_learnable_preservation":5,"egg":1,"level_up":15,"machine":24,"machine_archive":23,"shared_egg":5,"tutor":1} |
| [456: カイリキー](pokemon/456.md) | {"build_learnable_preservation":5,"egg":1,"level_up":16,"machine":26,"machine_archive":30,"shared_egg":5,"tutor":1} |
| [457: マダツボミ](pokemon/457.md) | {"egg":7,"level_up":14,"machine":23,"machine_archive":11,"shared_egg":7} |
| [458: ウツドン](pokemon/458.md) | {"build_learnable_preservation":6,"egg":2,"level_up":14,"machine":23,"machine_archive":14,"shared_egg":7} |
| [459: ウツボット](pokemon/459.md) | {"build_learnable_preservation":17,"egg":2,"level_up":6,"machine":23,"machine_archive":17,"move_memory_reminder":5,"shared_egg":7} |
| [460: ポニータ](pokemon/460.md) | {"egg":6,"level_up":13,"machine":11,"machine_archive":19,"shared_egg":6} |
| [461: ギャロップ](pokemon/461.md) | {"build_learnable_preservation":6,"egg":1,"level_up":18,"machine":17,"machine_archive":23,"shared_egg":6,"tutor":1} |
| [462: ヤドン](pokemon/462.md) | {"egg":4,"level_up":17,"machine":28,"machine_archive":24,"shared_egg":4} |
| [463: ヤドラン](pokemon/463.md) | {"build_learnable_preservation":4,"egg":2,"level_up":18,"machine":35,"machine_archive":33,"move_memory_reminder":1,"shared_egg":4} |
| [464: ドードー](pokemon/464.md) | {"egg":4,"level_up":13,"machine":18,"machine_archive":12,"shared_egg":4} |
| [465: ドードリオ](pokemon/465.md) | {"build_learnable_preservation":4,"egg":2,"level_up":14,"machine":23,"machine_archive":16,"shared_egg":4} |
| [466: パウワウ](pokemon/466.md) | {"egg":10,"level_up":17,"machine":20,"machine_archive":18,"shared_egg":10} |
| [467: ジュゴン](pokemon/467.md) | {"build_learnable_preservation":10,"egg":2,"level_up":17,"machine":23,"machine_archive":22,"shared_egg":10} |
| [468: ベトベター](pokemon/468.md) | {"egg":9,"level_up":16,"machine":28,"machine_archive":19,"shared_egg":9} |
| [469: ベトベトン](pokemon/469.md) | {"build_learnable_preservation":6,"egg":1,"level_up":16,"machine":33,"machine_archive":26,"shared_egg":9} |
| [470: イワーク](pokemon/470.md) | {"egg":7,"level_up":18,"machine":20,"machine_archive":20,"shared_egg":7,"tutor":2} |
| [471: スリープ](pokemon/471.md) | {"egg":8,"level_up":14,"machine":32,"machine_archive":27,"shared_egg":8} |
| [472: スリーパー](pokemon/472.md) | {"build_learnable_preservation":5,"egg":1,"level_up":15,"machine":35,"machine_archive":31,"shared_egg":8} |
| [473: カラカラ](pokemon/473.md) | {"egg":8,"level_up":14,"machine":24,"machine_archive":20,"shared_egg":8,"tutor":1} |
| [474: ガラガラ](pokemon/474.md) | {"build_learnable_preservation":8,"egg":1,"level_up":14,"machine":27,"machine_archive":23,"shared_egg":8,"tutor":1} |
| [475: モンジャラ](pokemon/475.md) | {"egg":6,"level_up":16,"machine":15,"machine_archive":13,"shared_egg":6,"tutor":1} |
| [476: タッツー](pokemon/476.md) | {"egg":5,"level_up":13,"machine":17,"machine_archive":11,"shared_egg":5} |
| [477: シードラ](pokemon/477.md) | {"build_learnable_preservation":5,"egg":1,"level_up":13,"machine":18,"machine_archive":14,"shared_egg":5} |
| [478: トサキント](pokemon/478.md) | {"egg":5,"level_up":12,"machine":17,"machine_archive":15,"shared_egg":5,"tutor":2} |
| [479: アズマオウ](pokemon/479.md) | {"build_learnable_preservation":5,"egg":1,"level_up":12,"machine":17,"machine_archive":17,"shared_egg":5,"tutor":2} |
| [480: バリヤード](pokemon/480.md) | {"egg":5,"level_up":21,"machine":32,"machine_archive":32,"shared_egg":5,"tutor":1} |
| [481: コイキング](pokemon/481.md) | {"egg":1,"level_up":3} |
| [482: ギャラドス](pokemon/482.md) | {"egg":2,"level_up":19,"machine":27,"machine_archive":27} |
| [483: イーブイ](pokemon/483.md) | {"egg":8,"level_up":16,"machine":12,"machine_archive":16,"shared_egg":8} |
| [484: シャワーズ](pokemon/484.md) | {"build_learnable_preservation":6,"egg":1,"level_up":24,"machine":21,"machine_archive":23,"shared_egg":8} |
| [485: サンダース](pokemon/485.md) | {"build_learnable_preservation":5,"egg":1,"level_up":24,"machine":18,"machine_archive":27,"shared_egg":8} |
| [486: ブースター](pokemon/486.md) | {"build_learnable_preservation":6,"egg":1,"level_up":23,"machine":17,"machine_archive":27,"shared_egg":8} |
| [487: オムナイト](pokemon/487.md) | {"egg":10,"level_up":14,"machine":19,"machine_archive":16,"shared_egg":10,"tutor":1} |
| [488: オムスター](pokemon/488.md) | {"build_learnable_preservation":10,"egg":2,"level_up":16,"machine":21,"machine_archive":20,"shared_egg":10,"tutor":1} |
| [489: カブト](pokemon/489.md) | {"egg":8,"level_up":14,"machine":20,"machine_archive":16,"shared_egg":8,"tutor":1} |
| [490: カブトプス](pokemon/490.md) | {"build_learnable_preservation":8,"egg":2,"level_up":18,"machine":23,"machine_archive":25,"shared_egg":8,"tutor":2} |
| [491: カビゴン](pokemon/491.md) | {"egg":14,"level_up":27,"machine":33,"machine_archive":30,"shared_egg":5} |
| [492: ミニリュウ](pokemon/492.md) | {"egg":6,"level_up":14,"machine":23,"machine_archive":18,"shared_egg":6} |
| [493: ハクリュー](pokemon/493.md) | {"build_learnable_preservation":5,"egg":1,"level_up":14,"machine":23,"machine_archive":19,"shared_egg":6} |
| [494: カイリュー](pokemon/494.md) | {"build_learnable_preservation":4,"egg":2,"level_up":20,"machine":41,"machine_archive":31,"shared_egg":6} |
| [495: チコリータ](pokemon/495.md) | {"egg":6,"level_up":14,"machine":17,"machine_archive":16,"shared_egg":6} |
| [496: ベイリーフ](pokemon/496.md) | {"build_learnable_preservation":6,"egg":1,"level_up":14,"machine":19,"machine_archive":16,"shared_egg":6} |
| [497: メガニウム](pokemon/497.md) | {"build_learnable_preservation":6,"egg":1,"level_up":16,"machine":22,"machine_archive":25,"shared_egg":6} |
| [498: ヒノアラシ](pokemon/498.md) | {"egg":6,"level_up":16,"machine":14,"machine_archive":19,"shared_egg":6} |
| [499: マグマラシ](pokemon/499.md) | {"build_learnable_preservation":4,"egg":1,"level_up":16,"machine":15,"machine_archive":20,"shared_egg":6} |
| [500: バクフーン](pokemon/500.md) | {"build_learnable_preservation":4,"egg":1,"level_up":17,"machine":26,"machine_archive":30,"shared_egg":6} |
| [501: ワニノコ](pokemon/501.md) | {"egg":5,"level_up":14,"machine":22,"machine_archive":27,"shared_egg":5} |
| [502: アリゲイツ](pokemon/502.md) | {"build_learnable_preservation":5,"egg":1,"level_up":14,"machine":23,"machine_archive":28,"shared_egg":5} |
| [503: オーダイル](pokemon/503.md) | {"build_learnable_preservation":5,"egg":1,"level_up":15,"machine":30,"machine_archive":37,"shared_egg":5} |
| [504: オタチ](pokemon/504.md) | {"egg":6,"level_up":13,"machine":30,"machine_archive":19,"shared_egg":6} |
| [505: オオタチ](pokemon/505.md) | {"build_learnable_preservation":5,"egg":1,"level_up":15,"machine":31,"machine_archive":23,"shared_egg":6} |
| [506: クロバット](pokemon/506.md) | {"build_learnable_preservation":7,"egg":2,"level_up":18,"machine":20,"machine_archive":22,"shared_egg":7,"tutor":1} |
| [507: チョンチー](pokemon/507.md) | {"egg":5,"level_up":13,"machine":23,"machine_archive":17,"shared_egg":5} |
| [508: ランターン](pokemon/508.md) | {"build_learnable_preservation":3,"egg":2,"level_up":17,"machine":23,"machine_archive":19,"shared_egg":5} |
| [509: ピィ](pokemon/509.md) | {"egg":4,"level_up":8,"machine":23,"machine_archive":25,"shared_egg":4} |
| [510: ププリン](pokemon/510.md) | {"egg":8,"level_up":8,"machine":21,"machine_archive":21,"shared_egg":8} |
| [511: ネイティ](pokemon/511.md) | {"egg":6,"level_up":12,"machine":22,"machine_archive":18,"shared_egg":6,"tutor":2} |
| [512: ネイティオ](pokemon/512.md) | {"build_learnable_preservation":5,"egg":2,"level_up":15,"machine":24,"machine_archive":20,"shared_egg":6,"tutor":2} |
| [513: メリープ](pokemon/513.md) | {"egg":6,"level_up":15,"machine":19,"machine_archive":14,"shared_egg":6} |
| [514: モココ](pokemon/514.md) | {"build_learnable_preservation":2,"egg":1,"level_up":15,"machine":23,"machine_archive":19,"shared_egg":6} |
| [515: デンリュウ](pokemon/515.md) | {"build_learnable_preservation":2,"egg":1,"level_up":20,"machine":28,"machine_archive":26,"shared_egg":6} |
| [516: キレイハナ](pokemon/516.md) | {"build_learnable_preservation":8,"egg":1,"level_up":16,"machine":21,"machine_archive":20,"shared_egg":9} |
| [517: マリル](pokemon/517.md) | {"build_learnable_preservation":5,"egg":15,"level_up":17,"machine":26,"machine_archive":24,"shared_egg":9} |
| [518: マリルリ](pokemon/518.md) | {"build_learnable_preservation":10,"egg":2,"level_up":17,"machine":27,"machine_archive":26,"shared_egg":9} |
| [519: ウソッキー](pokemon/519.md) | {"build_learnable_preservation":1,"egg":10,"level_up":18,"machine":29,"machine_archive":25,"shared_egg":6} |
| [520: ニョロトノ](pokemon/520.md) | {"build_learnable_preservation":7,"egg":1,"level_up":5,"machine":25,"machine_archive":24,"move_memory_reminder":10,"shared_egg":5} |
| [521: ハネッコ](pokemon/521.md) | {"egg":8,"level_up":18,"machine":24,"machine_archive":13,"shared_egg":8} |
| [522: ポポッコ](pokemon/522.md) | {"build_learnable_preservation":5,"egg":2,"level_up":18,"machine":24,"machine_archive":14,"shared_egg":8} |
| [523: ワタッコ](pokemon/523.md) | {"build_learnable_preservation":5,"egg":2,"level_up":18,"machine":24,"machine_archive":16,"shared_egg":8} |
| [524: エイパム](pokemon/524.md) | {"egg":9,"level_up":14,"machine":31,"machine_archive":21,"shared_egg":9} |
| [525: ヒマナッツ](pokemon/525.md) | {"egg":6,"level_up":13,"machine":16,"machine_archive":12,"shared_egg":6} |
| [526: キマワリ](pokemon/526.md) | {"build_learnable_preservation":1,"egg":1,"level_up":17,"machine":19,"machine_archive":16,"shared_egg":6} |
| [527: ヤンヤンマ](pokemon/527.md) | {"egg":3,"level_up":15,"machine":16,"machine_archive":17,"shared_egg":3} |
| [528: ウパー](pokemon/528.md) | {"egg":10,"level_up":13,"machine":29,"machine_archive":18,"shared_egg":10} |
| [529: ヌオー](pokemon/529.md) | {"build_learnable_preservation":8,"egg":2,"level_up":13,"machine":35,"machine_archive":25,"shared_egg":10} |
| [530: エーフィ](pokemon/530.md) | {"build_learnable_preservation":6,"egg":1,"level_up":23,"machine":22,"machine_archive":32,"shared_egg":8} |
| [531: ブラッキー](pokemon/531.md) | {"build_learnable_preservation":6,"egg":1,"level_up":24,"machine":23,"machine_archive":25,"shared_egg":8} |
| [532: ヤドキング](pokemon/532.md) | {"build_learnable_preservation":5,"egg":2,"level_up":19,"machine":38,"machine_archive":35,"move_memory_reminder":2,"shared_egg":4} |
| [533: ムウマ](pokemon/533.md) | {"egg":9,"level_up":12,"machine":29,"machine_archive":28,"shared_egg":9} |
| [534: ソーナンス](pokemon/534.md) | {"egg":1,"level_up":12,"machine":2,"machine_archive":2} |
| [535: グライガー](pokemon/535.md) | {"egg":6,"level_up":14,"machine":35,"machine_archive":26,"shared_egg":6} |
| [536: ハガネール](pokemon/536.md) | {"build_learnable_preservation":7,"egg":2,"level_up":24,"machine":23,"machine_archive":26,"shared_egg":7,"tutor":3,"tutor_archive":1} |
| [537: ブルー](pokemon/537.md) | {"egg":5,"level_up":16,"machine":30,"machine_archive":34,"shared_egg":5} |
| [538: グランブル](pokemon/538.md) | {"build_learnable_preservation":5,"egg":1,"level_up":17,"machine":34,"machine_archive":38,"shared_egg":5} |
| [539: ハリーセン](pokemon/539.md) | {"egg":10,"level_up":17,"machine":27,"machine_archive":23,"shared_egg":10} |
| [540: ヘラクロス](pokemon/540.md) | {"egg":6,"level_up":15,"machine":28,"machine_archive":27,"shared_egg":6} |
| [541: ヒメグマ](pokemon/541.md) | {"egg":12,"level_up":15,"machine":25,"machine_archive":21,"shared_egg":12} |
| [542: リングマ](pokemon/542.md) | {"build_learnable_preservation":7,"egg":1,"level_up":17,"machine":28,"machine_archive":25,"shared_egg":12} |
| [543: マグマッグ](pokemon/543.md) | {"egg":8,"level_up":15,"machine":21,"machine_archive":18,"shared_egg":8} |
| [544: マグカルゴ](pokemon/544.md) | {"build_learnable_preservation":8,"egg":2,"level_up":16,"machine":23,"machine_archive":24,"shared_egg":8} |
| [545: サニーゴ](pokemon/545.md) | {"egg":6,"level_up":13,"machine":27,"machine_archive":19,"shared_egg":6,"tutor":1} |
| [546: マンタイン](pokemon/546.md) | {"egg":7,"level_up":17,"machine":25,"machine_archive":19,"shared_egg":7,"tutor":1} |
| [547: キングドラ](pokemon/547.md) | {"build_learnable_preservation":5,"egg":2,"level_up":16,"machine":21,"machine_archive":19,"shared_egg":5} |
| [548: ゴマゾウ](pokemon/548.md) | {"egg":12,"level_up":12,"machine":24,"machine_archive":18,"shared_egg":12} |
| [549: ドンファン](pokemon/549.md) | {"build_learnable_preservation":10,"egg":1,"level_up":16,"machine":30,"machine_archive":25,"shared_egg":12} |
| [550: オドシシ](pokemon/550.md) | {"egg":8,"level_up":13,"machine":26,"machine_archive":28,"shared_egg":8} |
| [551: ドーブル](pokemon/551.md) | {"egg":1,"level_up":1} |
| [552: セレビィ](pokemon/552.md) | {"level_up":12,"machine":25,"machine_archive":30,"tutor":3} |
| [553: キモリ](pokemon/553.md) | {"egg":8,"level_up":15,"machine":21,"machine_archive":20,"shared_egg":8} |
| [554: ジュプトル](pokemon/554.md) | {"build_learnable_preservation":8,"egg":1,"level_up":15,"machine":23,"machine_archive":23,"move_memory_reminder":4,"shared_egg":8} |
| [555: ジュカイン](pokemon/555.md) | {"build_learnable_preservation":9,"egg":1,"level_up":15,"machine":29,"machine_archive":34,"move_memory_reminder":5,"shared_egg":8} |
| [556: アチャモ](pokemon/556.md) | {"egg":6,"level_up":15,"machine":17,"machine_archive":19,"shared_egg":6} |
| [557: ワカシャモ](pokemon/557.md) | {"build_learnable_preservation":6,"egg":2,"level_up":16,"machine":25,"machine_archive":24,"move_memory_reminder":2,"shared_egg":6} |
| [558: バシャーモ](pokemon/558.md) | {"build_learnable_preservation":7,"egg":2,"level_up":16,"machine":33,"machine_archive":33,"move_memory_reminder":4,"shared_egg":6} |
| [559: ミズゴロウ](pokemon/559.md) | {"egg":11,"level_up":15,"machine":16,"machine_archive":21,"shared_egg":11} |
| [560: ヌマクロー](pokemon/560.md) | {"build_learnable_preservation":9,"egg":2,"level_up":15,"machine":22,"machine_archive":24,"move_memory_reminder":1,"shared_egg":11} |
| [561: ラグラージ](pokemon/561.md) | {"build_learnable_preservation":10,"egg":2,"level_up":15,"machine":30,"machine_archive":33,"move_memory_reminder":4,"shared_egg":11} |
| [562: ポチエナ](pokemon/562.md) | {"egg":3,"level_up":15,"machine":18,"machine_archive":19,"shared_egg":3} |
| [563: グラエナ](pokemon/563.md) | {"build_learnable_preservation":3,"egg":1,"level_up":20,"machine":19,"machine_archive":22,"shared_egg":3} |
| [564: ジグザグマ](pokemon/564.md) | {"egg":3,"level_up":14,"machine":19,"machine_archive":19,"shared_egg":3} |
| [565: マッスグマ](pokemon/565.md) | {"build_learnable_preservation":3,"egg":1,"level_up":19,"machine":23,"machine_archive":21,"shared_egg":3} |
| [566: ケムッソ](pokemon/566.md) | {"egg":1,"level_up":4,"tutor":2,"tutor_archive":1} |
| [567: カラサリス](pokemon/567.md) | {"build_learnable_preservation":3,"egg":1,"level_up":2,"tutor":2,"tutor_archive":1} |
| [568: アゲハント](pokemon/568.md) | {"build_learnable_preservation":4,"egg":2,"level_up":14,"machine":12,"machine_archive":17,"tutor":4,"tutor_archive":4} |
| [569: マユルド](pokemon/569.md) | {"build_learnable_preservation":3,"egg":1,"level_up":2,"tutor":2,"tutor_archive":1} |
| [570: ドクケイル](pokemon/570.md) | {"build_learnable_preservation":4,"egg":2,"level_up":14,"machine":14,"machine_archive":16,"tutor":4,"tutor_archive":4} |
| [571: ハスボー](pokemon/571.md) | {"egg":6,"level_up":13,"machine":19,"machine_archive":17,"shared_egg":6} |
| [572: ハスブレロ](pokemon/572.md) | {"build_learnable_preservation":4,"egg":2,"level_up":17,"machine":27,"machine_archive":22,"shared_egg":6} |
| [573: ルンパッパ](pokemon/573.md) | {"build_learnable_preservation":14,"egg":2,"level_up":3,"machine":30,"machine_archive":27,"move_memory_reminder":13,"shared_egg":6} |
| [574: タネボー](pokemon/574.md) | {"egg":6,"level_up":13,"machine":17,"machine_archive":15,"shared_egg":6} |
| [575: コノハナ](pokemon/575.md) | {"build_learnable_preservation":6,"egg":2,"level_up":19,"machine":26,"machine_archive":26,"shared_egg":6} |
| [576: ダーテング](pokemon/576.md) | {"build_learnable_preservation":22,"egg":2,"level_up":5,"machine":34,"machine_archive":39,"move_memory_reminder":17,"shared_egg":6} |
| [577: キャモメ](pokemon/577.md) | {"egg":8,"level_up":11,"machine":24,"machine_archive":13,"shared_egg":8} |
| [578: ペリッパー](pokemon/578.md) | {"build_learnable_preservation":3,"egg":2,"level_up":19,"machine":26,"machine_archive":18,"shared_egg":8} |
| [579: アメタマ](pokemon/579.md) | {"egg":8,"level_up":10,"machine":23,"machine_archive":16,"shared_egg":8} |
| [580: アメモース](pokemon/580.md) | {"build_learnable_preservation":6,"egg":2,"level_up":13,"machine":28,"machine_archive":25,"shared_egg":8} |
| [581: ホエルコ](pokemon/581.md) | {"egg":9,"level_up":16,"machine":17,"machine_archive":17,"shared_egg":9,"tutor_archive":1} |
| [582: ホエルオー](pokemon/582.md) | {"build_learnable_preservation":7,"egg":1,"level_up":18,"machine":19,"machine_archive":19,"shared_egg":9,"tutor_archive":1} |
| [583: エネコ](pokemon/583.md) | {"egg":14,"level_up":19,"machine":12,"machine_archive":21,"tutor":6,"tutor_archive":6} |
| [584: エネコロロ](pokemon/584.md) | {"build_learnable_preservation":21,"egg":1,"level_up":4,"machine":12,"machine_archive":23,"tutor":6,"tutor_archive":8} |
| [585: カクレオン](pokemon/585.md) | {"egg":12,"level_up":19,"machine":18,"machine_archive":19,"tutor":14,"tutor_archive":11} |
| [586: ヤジロン](pokemon/586.md) | {"egg":2,"level_up":17,"machine":21,"machine_archive":24,"tutor":2} |
| [587: ネンドール](pokemon/587.md) | {"egg":2,"level_up":20,"machine":24,"machine_archive":29,"tutor":2} |
| [588: ノズパス](pokemon/588.md) | {"egg":4,"level_up":16,"machine":26,"machine_archive":18,"shared_egg":4} |
| [589: ドジョッチ](pokemon/589.md) | {"egg":4,"level_up":11,"machine":23,"machine_archive":18,"shared_egg":4} |
| [590: ナマズン](pokemon/590.md) | {"build_learnable_preservation":2,"egg":2,"level_up":15,"machine":24,"machine_archive":25,"shared_egg":4} |
| [591: ヘイガニ](pokemon/591.md) | {"egg":6,"level_up":15,"machine":22,"machine_archive":18,"shared_egg":6} |
| [592: シザリガー](pokemon/592.md) | {"build_learnable_preservation":4,"egg":2,"level_up":16,"machine":25,"machine_archive":28,"shared_egg":6} |
| [593: ヒンバス](pokemon/593.md) | {"egg":7,"level_up":3,"machine":17,"machine_archive":8,"shared_egg":7} |
| [594: ミロカロス](pokemon/594.md) | {"build_learnable_preservation":5,"egg":1,"level_up":19,"machine":23,"machine_archive":25,"shared_egg":7} |
| [595: キバニア](pokemon/595.md) | {"egg":5,"level_up":13,"machine":19,"machine_archive":21,"shared_egg":5,"tutor":2} |
| [596: サメハダー](pokemon/596.md) | {"build_learnable_preservation":5,"egg":2,"level_up":16,"machine":22,"machine_archive":26,"shared_egg":5,"tutor":2} |
| [597: ナックラー](pokemon/597.md) | {"egg":7,"level_up":13,"machine":14,"machine_archive":14,"shared_egg":7} |
| [598: ビブラーバ](pokemon/598.md) | {"build_learnable_preservation":10,"egg":2,"level_up":15,"machine":21,"machine_archive":26,"move_memory_reminder":6,"shared_egg":7} |
| [599: フライゴン](pokemon/599.md) | {"build_learnable_preservation":10,"egg":2,"level_up":16,"machine":27,"machine_archive":35,"move_memory_reminder":8,"shared_egg":7} |
| [600: マクノシタ](pokemon/600.md) | {"egg":7,"level_up":17,"machine":29,"machine_archive":21,"shared_egg":7} |
| [601: ハリテヤマ](pokemon/601.md) | {"build_learnable_preservation":6,"egg":1,"level_up":19,"machine":31,"machine_archive":26,"shared_egg":7} |
| [602: ラクライ](pokemon/602.md) | {"egg":4,"level_up":13,"machine":15,"machine_archive":16,"shared_egg":4,"tutor":1} |
| [603: ライボルト](pokemon/603.md) | {"build_learnable_preservation":4,"egg":1,"level_up":15,"machine":15,"machine_archive":22,"shared_egg":4,"tutor":1} |
| [604: ドンメル](pokemon/604.md) | {"egg":15,"level_up":14,"machine":25,"machine_archive":25,"shared_egg":15} |
| [605: バクーダ](pokemon/605.md) | {"build_learnable_preservation":9,"egg":2,"level_up":16,"machine":25,"machine_archive":29,"shared_egg":15} |
| [606: ユキワラシ](pokemon/606.md) | {"egg":5,"level_up":15,"machine":17,"machine_archive":13,"shared_egg":5} |
| [607: オニゴーリ](pokemon/607.md) | {"build_learnable_preservation":5,"egg":1,"level_up":17,"machine":23,"machine_archive":17,"shared_egg":5} |
| [608: ルリリ](pokemon/608.md) | {"egg":9,"level_up":8,"machine":14,"machine_archive":11,"shared_egg":9} |
| [609: バネブー](pokemon/609.md) | {"egg":8,"level_up":13,"machine":31,"machine_archive":19,"shared_egg":8} |
| [610: ブーピッグ](pokemon/610.md) | {"build_learnable_preservation":5,"egg":1,"level_up":15,"machine":43,"machine_archive":32,"shared_egg":8} |
| [611: プラスル](pokemon/611.md) | {"build_learnable_preservation":1,"egg":4,"level_up":19,"machine":20,"machine_archive":19,"move_memory_reminder":1,"shared_egg":4} |
| [612: マイナン](pokemon/612.md) | {"build_learnable_preservation":1,"egg":5,"level_up":19,"machine":20,"machine_archive":17,"move_memory_reminder":1,"shared_egg":5} |
| [613: アサナン](pokemon/613.md) | {"egg":11,"level_up":16,"machine":30,"machine_archive":25,"shared_egg":11} |
| [614: チャーレム](pokemon/614.md) | {"build_learnable_preservation":7,"egg":2,"level_up":19,"machine":32,"machine_archive":29,"shared_egg":11} |
| [615: チルット](pokemon/615.md) | {"egg":7,"level_up":13,"machine":22,"machine_archive":13,"shared_egg":7} |
| [616: チルタリス](pokemon/616.md) | {"build_learnable_preservation":3,"egg":2,"level_up":16,"machine":28,"machine_archive":25,"shared_egg":7} |
| [617: ソーナノ](pokemon/617.md) | {"egg":1,"level_up":8,"machine":2,"machine_archive":2} |
| [618: ロゼリア](pokemon/618.md) | {"egg":5,"level_up":18,"machine":18,"machine_archive":15,"shared_egg":5,"tutor":1} |
| [619: ナマケロ](pokemon/619.md) | {"egg":9,"level_up":11,"machine":31,"machine_archive":18,"shared_egg":9} |
| [620: ヤルキモノ](pokemon/620.md) | {"build_learnable_preservation":10,"egg":1,"level_up":11,"machine":41,"machine_archive":29,"shared_egg":9} |
| [621: ケッキング](pokemon/621.md) | {"build_learnable_preservation":9,"egg":1,"level_up":14,"machine":43,"machine_archive":36,"shared_egg":9} |
| [622: ゴクリン](pokemon/622.md) | {"egg":7,"level_up":16,"machine":26,"machine_archive":14,"shared_egg":7} |
| [623: マルノーム](pokemon/623.md) | {"build_learnable_preservation":5,"egg":1,"level_up":16,"machine":31,"machine_archive":19,"shared_egg":7} |
| [624: パールル](pokemon/624.md) | {"egg":11,"level_up":5,"machine":9,"machine_archive":12,"tutor":1,"tutor_archive":3} |
| [625: ハンテール](pokemon/625.md) | {"build_learnable_preservation":12,"egg":1,"level_up":15,"machine":9,"machine_archive":16,"tutor":4,"tutor_archive":4} |
| [626: サクラビス](pokemon/626.md) | {"build_learnable_preservation":13,"egg":1,"level_up":15,"machine":11,"machine_archive":17,"tutor":2,"tutor_archive":5} |
| [627: ハブネーク](pokemon/627.md) | {"egg":9,"level_up":17,"machine":33,"machine_archive":22,"shared_egg":9} |
| [628: ザングース](pokemon/628.md) | {"egg":16,"level_up":16,"machine":36,"machine_archive":27,"move_memory_reminder":12} |
| [629: ココドラ](pokemon/629.md) | {"egg":6,"level_up":17,"machine":17,"machine_archive":13,"shared_egg":6,"tutor":1,"tutor_archive":1} |
| [630: コドラ](pokemon/630.md) | {"build_learnable_preservation":6,"egg":2,"level_up":17,"machine":19,"machine_archive":15,"shared_egg":6,"tutor":1,"tutor_archive":1} |
| [631: ボスゴドラ](pokemon/631.md) | {"build_learnable_preservation":6,"egg":2,"level_up":17,"machine":35,"machine_archive":35,"shared_egg":6,"tutor":2,"tutor_archive":1} |
| [632: ポワルン](pokemon/632.md) | {"egg":10,"level_up":13,"machine":15,"machine_archive":17,"tutor":4,"tutor_archive":3} |
| [633: バルビート](pokemon/633.md) | {"egg":4,"level_up":14,"machine":31,"machine_archive":22,"shared_egg":4} |
| [634: イルミーゼ](pokemon/634.md) | {"egg":3,"level_up":15,"machine":29,"machine_archive":26,"shared_egg":3} |
| [635: アノプス](pokemon/635.md) | {"egg":6,"level_up":13,"machine":14,"machine_archive":13,"shared_egg":6,"tutor":1} |
| [636: アーマルド](pokemon/636.md) | {"build_learnable_preservation":6,"egg":2,"level_up":13,"machine":22,"machine_archive":18,"shared_egg":6,"tutor":1} |
| [637: タツベイ](pokemon/637.md) | {"egg":4,"level_up":13,"machine":16,"machine_archive":22,"shared_egg":4} |
| [638: コモルー](pokemon/638.md) | {"build_learnable_preservation":4,"egg":1,"level_up":14,"machine":16,"machine_archive":23,"shared_egg":4} |
| [639: ボーマンダ](pokemon/639.md) | {"build_learnable_preservation":4,"egg":2,"level_up":17,"machine":25,"machine_archive":29,"shared_egg":4} |
| [640: レジロック](pokemon/640.md) | {"level_up":15,"machine":27,"machine_archive":21} |
| [641: レジアイス](pokemon/641.md) | {"level_up":15,"machine":26,"machine_archive":14} |
| [642: レジスチル](pokemon/642.md) | {"level_up":17,"machine":28,"machine_archive":19} |
| [643: カイオーガ](pokemon/643.md) | {"level_up":14,"machine":21,"machine_archive":18} |
| [644: グラードン](pokemon/644.md) | {"level_up":14,"machine":31,"machine_archive":32} |
| [645: レックウザ](pokemon/645.md) | {"level_up":15,"machine":35,"machine_archive":34} |
| [646: ジラーチ](pokemon/646.md) | {"level_up":15,"machine":38,"machine_archive":28} |
| [647: デオキシス](pokemon/647.md) | {"build_learnable_preservation":10,"level_up":14,"machine":36,"machine_archive":31} |
| [648: チリーン](pokemon/648.md) | {"build_learnable_preservation":3,"egg":12,"level_up":14,"machine":26,"machine_archive":23,"shared_egg":7} |
| [649: キャタピー](pokemon/649.md) | {"egg":1,"level_up":3,"machine":1} |
| [650: アンノーン](pokemon/650.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [651: アンノーン](pokemon/651.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [652: アンノーン](pokemon/652.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [653: アンノーン](pokemon/653.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [654: アンノーン](pokemon/654.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [655: アンノーン](pokemon/655.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [656: アンノーン](pokemon/656.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [657: アンノーン](pokemon/657.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [658: アンノーン](pokemon/658.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [659: アンノーン](pokemon/659.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [660: アンノーン](pokemon/660.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [661: アンノーン](pokemon/661.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [662: アンノーン](pokemon/662.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [663: アンノーン](pokemon/663.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [664: アンノーン](pokemon/664.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [665: アンノーン](pokemon/665.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [666: アンノーン](pokemon/666.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [667: アンノーン](pokemon/667.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [668: アンノーン](pokemon/668.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [669: アンノーン](pokemon/669.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [670: アンノーン](pokemon/670.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [671: アンノーン](pokemon/671.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [672: アンノーン](pokemon/672.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [673: アンノーン](pokemon/673.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [674: アンノーン](pokemon/674.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [675: アンノーン](pokemon/675.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [676: アンノーン](pokemon/676.md) | {"egg":1,"level_up":1,"machine_archive":1} |
| [677: ナエトル](pokemon/677.md) | {"egg":11,"level_up":12,"machine":19,"machine_archive":21,"shared_egg":11} |
| [678: ハヤシガメ](pokemon/678.md) | {"build_learnable_preservation":10,"egg":1,"level_up":12,"machine":19,"machine_archive":21,"shared_egg":11} |
| [679: ドダイトス](pokemon/679.md) | {"build_learnable_preservation":10,"egg":2,"level_up":15,"machine":26,"machine_archive":32,"shared_egg":11} |
| [680: ヒコザル](pokemon/680.md) | {"egg":10,"level_up":13,"machine":31,"machine_archive":25,"shared_egg":10} |
| [681: モウカザル](pokemon/681.md) | {"build_learnable_preservation":5,"egg":2,"level_up":14,"machine":33,"machine_archive":30,"shared_egg":10} |
| [682: ゴウカザル](pokemon/682.md) | {"build_learnable_preservation":6,"egg":2,"level_up":14,"machine":38,"machine_archive":41,"move_memory_reminder":2,"shared_egg":10} |
| [683: ポッチャマ](pokemon/683.md) | {"egg":7,"level_up":13,"machine":21,"machine_archive":16,"shared_egg":7} |
| [684: ポッタイシ](pokemon/684.md) | {"build_learnable_preservation":6,"egg":1,"level_up":13,"machine":22,"machine_archive":19,"shared_egg":7} |
| [685: エンペルト](pokemon/685.md) | {"build_learnable_preservation":6,"egg":2,"level_up":16,"machine":34,"machine_archive":33,"shared_egg":7} |
| [686: ムックル](pokemon/686.md) | {"egg":6,"level_up":12,"machine":18,"machine_archive":11,"shared_egg":6} |
| [687: ムクバード](pokemon/687.md) | {"build_learnable_preservation":3,"egg":2,"level_up":12,"machine":18,"machine_archive":11,"shared_egg":6} |
| [688: ムクホーク](pokemon/688.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":18,"machine_archive":15,"shared_egg":6} |
| [689: ビッパ](pokemon/689.md) | {"egg":13,"level_up":14,"machine":15,"machine_archive":14,"tutor":7,"tutor_archive":3} |
| [690: ビーダル](pokemon/690.md) | {"build_learnable_preservation":9,"egg":2,"level_up":18,"machine":19,"machine_archive":17,"tutor":8,"tutor_archive":6} |
| [691: コロボーシ](pokemon/691.md) | {"egg":1,"level_up":4,"machine":2,"machine_archive":4} |
| [692: コロトック](pokemon/692.md) | {"egg":1,"level_up":15,"machine":20,"machine_archive":14} |
| [693: コリンク](pokemon/693.md) | {"egg":7,"level_up":14,"machine":21,"machine_archive":17,"shared_egg":7} |
| [694: ルクシオ](pokemon/694.md) | {"build_learnable_preservation":6,"egg":1,"level_up":14,"machine":21,"machine_archive":17,"shared_egg":7} |
| [695: レントラー](pokemon/695.md) | {"build_learnable_preservation":6,"egg":1,"level_up":15,"machine":22,"machine_archive":22,"shared_egg":7} |
| [696: スボミー](pokemon/696.md) | {"egg":6,"level_up":4,"machine":17,"machine_archive":11,"shared_egg":6,"tutor":1} |
| [697: ロズレイド](pokemon/697.md) | {"build_learnable_preservation":5,"egg":2,"level_up":19,"machine":18,"machine_archive":19,"shared_egg":5,"tutor":1} |
| [698: ズガイドス](pokemon/698.md) | {"egg":4,"level_up":12,"machine":25,"machine_archive":22,"shared_egg":4} |
| [699: ラムパルド](pokemon/699.md) | {"build_learnable_preservation":4,"egg":1,"level_up":13,"machine":30,"machine_archive":31,"shared_egg":4} |
| [700: タテトプス](pokemon/700.md) | {"egg":6,"level_up":12,"machine":23,"machine_archive":23,"shared_egg":6} |
| [701: トリデプス](pokemon/701.md) | {"build_learnable_preservation":7,"egg":2,"level_up":13,"machine":26,"machine_archive":29,"move_memory_reminder":1,"shared_egg":6} |
| [702: ミノムッチ](pokemon/702.md) | {"egg":1,"level_up":4,"machine":1,"machine_archive":1,"tutor":2,"tutor_archive":1} |
| [703: ミノマダム](pokemon/703.md) | {"egg":2,"level_up":19,"machine":12,"machine_archive":17,"tutor":6,"tutor_archive":6} |
| [704: ガーメイル](pokemon/704.md) | {"egg":2,"level_up":18,"machine":13,"machine_archive":19,"tutor":5,"tutor_archive":3} |
| [705: ミツハニー](pokemon/705.md) | {"egg":2,"level_up":4,"machine":3,"machine_archive":5} |
| [706: ビークイン](pokemon/706.md) | {"egg":2,"level_up":19,"machine":21,"machine_archive":24} |
| [707: チェリンボ](pokemon/707.md) | {"egg":10,"level_up":11,"machine":13,"machine_archive":12,"shared_egg":10,"tutor":1} |
| [708: チェリム](pokemon/708.md) | {"build_learnable_preservation":9,"egg":1,"level_up":15,"machine":14,"machine_archive":15,"shared_egg":10,"tutor":1} |
| [709: カラナクシ](pokemon/709.md) | {"egg":11,"level_up":11,"machine":21,"machine_archive":15,"shared_egg":11} |
| [710: トリトドン](pokemon/710.md) | {"build_learnable_preservation":10,"egg":2,"level_up":11,"machine":26,"machine_archive":21,"shared_egg":11} |
| [711: エテボース](pokemon/711.md) | {"build_learnable_preservation":9,"egg":1,"level_up":14,"machine":31,"machine_archive":24,"shared_egg":9} |
| [712: フワンテ](pokemon/712.md) | {"egg":6,"level_up":15,"machine":23,"machine_archive":21,"shared_egg":6} |
| [713: フワライド](pokemon/713.md) | {"build_learnable_preservation":5,"egg":2,"level_up":17,"machine":24,"machine_archive":25,"shared_egg":6} |
| [714: ミミロル](pokemon/714.md) | {"egg":9,"level_up":15,"machine":22,"machine_archive":22,"shared_egg":9,"tutor":1} |
| [715: ミミロップ](pokemon/715.md) | {"build_learnable_preservation":9,"egg":1,"level_up":18,"machine":26,"machine_archive":29,"shared_egg":9,"tutor":1} |
| [716: ムウマージ](pokemon/716.md) | {"build_learnable_preservation":9,"egg":1,"level_up":7,"machine":29,"machine_archive":29,"shared_egg":9} |
| [717: ニャルマー](pokemon/717.md) | {"egg":10,"level_up":14,"machine":12,"machine_archive":18,"tutor":6,"tutor_archive":5} |
| [718: ブニャット](pokemon/718.md) | {"build_learnable_preservation":10,"egg":1,"level_up":17,"machine":13,"machine_archive":21,"tutor":7,"tutor_archive":6} |
| [719: リーシャン](pokemon/719.md) | {"egg":7,"level_up":8,"machine":24,"machine_archive":14,"shared_egg":7} |
| [720: スカンプー](pokemon/720.md) | {"egg":6,"level_up":16,"machine":27,"machine_archive":18,"shared_egg":6} |
| [721: スカタンク](pokemon/721.md) | {"build_learnable_preservation":4,"egg":2,"level_up":16,"machine":28,"machine_archive":23,"shared_egg":6} |
| [722: ドーミラー](pokemon/722.md) | {"egg":2,"level_up":13,"machine":28,"machine_archive":23,"shared_egg":2} |
| [723: ドータクン](pokemon/723.md) | {"build_learnable_preservation":1,"egg":2,"level_up":17,"machine":29,"machine_archive":31,"shared_egg":2} |
| [724: ウソハチ](pokemon/724.md) | {"egg":6,"level_up":13,"machine":21,"machine_archive":18,"shared_egg":6} |
| [725: マネネ](pokemon/725.md) | {"egg":5,"level_up":17,"machine":25,"machine_archive":20,"shared_egg":5} |
| [726: ミカルゲ](pokemon/726.md) | {"egg":4,"level_up":14,"machine":23,"machine_archive":21,"shared_egg":4} |
| [727: ゴンベ](pokemon/727.md) | {"egg":5,"level_up":16,"machine":30,"machine_archive":21,"shared_egg":5} |
| [728: ヒポポタス](pokemon/728.md) | {"egg":5,"level_up":15,"machine":17,"machine_archive":19,"shared_egg":5} |
| [729: カバルドン](pokemon/729.md) | {"build_learnable_preservation":4,"egg":1,"level_up":18,"machine":18,"machine_archive":24,"shared_egg":5} |
| [730: グレッグル](pokemon/730.md) | {"egg":9,"level_up":14,"machine":34,"machine_archive":22,"shared_egg":9} |
| [731: ドクロッグ](pokemon/731.md) | {"build_learnable_preservation":8,"egg":2,"level_up":14,"machine":38,"machine_archive":25,"shared_egg":9} |
| [732: ケイコウオ](pokemon/732.md) | {"egg":9,"level_up":13,"machine":19,"machine_archive":13,"shared_egg":9} |
| [733: ネオラント](pokemon/733.md) | {"build_learnable_preservation":5,"egg":1,"level_up":13,"machine":21,"machine_archive":16,"shared_egg":9} |
| [734: タマンタ](pokemon/734.md) | {"egg":7,"level_up":14,"machine":19,"machine_archive":11,"shared_egg":7} |
| [735: モジャンボ](pokemon/735.md) | {"build_learnable_preservation":6,"egg":1,"level_up":17,"machine":22,"machine_archive":18,"shared_egg":6,"tutor":1} |
| [736: メガヤンマ](pokemon/736.md) | {"build_learnable_preservation":3,"egg":2,"level_up":15,"machine":17,"machine_archive":21,"move_memory_reminder":1,"shared_egg":3} |
| [737: リーフィア](pokemon/737.md) | {"build_learnable_preservation":6,"egg":1,"level_up":24,"machine":18,"machine_archive":27,"shared_egg":8} |
| [738: グレイシア](pokemon/738.md) | {"build_learnable_preservation":6,"egg":1,"level_up":23,"machine":17,"machine_archive":26,"shared_egg":8} |
| [739: グライオン](pokemon/739.md) | {"build_learnable_preservation":6,"egg":2,"level_up":16,"machine":35,"machine_archive":28,"shared_egg":6} |
| [740: ダイノーズ](pokemon/740.md) | {"build_learnable_preservation":4,"egg":2,"level_up":20,"machine":27,"machine_archive":23,"shared_egg":4} |
| [741: ユキメノコ](pokemon/741.md) | {"build_learnable_preservation":5,"egg":2,"level_up":21,"machine":27,"machine_archive":27,"shared_egg":5} |
| [742: ロトム](pokemon/742.md) | {"egg":2,"level_up":13,"machine":23,"machine_archive":16} |
| [743: ユクシー](pokemon/743.md) | {"build_learnable_preservation":8,"level_up":14,"machine":37,"machine_archive":24,"move_memory_reminder":9} |
| [744: エムリット](pokemon/744.md) | {"build_learnable_preservation":8,"level_up":14,"machine":35,"machine_archive":25,"move_memory_reminder":9} |
| [745: アグノム](pokemon/745.md) | {"build_learnable_preservation":11,"level_up":14,"machine":35,"machine_archive":25,"move_memory_reminder":12} |
| [746: レジギガス](pokemon/746.md) | {"level_up":15,"machine":26,"machine_archive":18} |
| [747: ギラティナ](pokemon/747.md) | {"level_up":14,"machine":28,"machine_archive":23} |
| [748: クレセリア](pokemon/748.md) | {"level_up":14,"machine":24,"machine_archive":21} |
| [749: シェイミ](pokemon/749.md) | {"build_learnable_preservation":1,"level_up":12,"machine":18,"machine_archive":20} |
| [750: アルセウス](pokemon/750.md) | {"level_up":12,"machine":59,"machine_archive":55} |
| [751: ビクティニ](pokemon/751.md) | {"level_up":18,"machine":28,"machine_archive":32,"tutor":2} |
| [752: ツタージャ](pokemon/752.md) | {"egg":7,"level_up":14,"machine":18,"machine_archive":14,"shared_egg":7} |
| [753: ジャノビー](pokemon/753.md) | {"build_learnable_preservation":6,"egg":1,"level_up":14,"machine":18,"machine_archive":14,"shared_egg":7} |
| [754: ジャローダ](pokemon/754.md) | {"build_learnable_preservation":6,"egg":1,"level_up":14,"machine":21,"machine_archive":21,"shared_egg":7} |
| [755: ポカブ](pokemon/755.md) | {"egg":4,"level_up":15,"machine":17,"machine_archive":22,"shared_egg":4} |
| [756: チャオブー](pokemon/756.md) | {"build_learnable_preservation":4,"egg":2,"level_up":16,"machine":28,"machine_archive":30,"shared_egg":4} |
| [757: エンブオー](pokemon/757.md) | {"build_learnable_preservation":5,"egg":2,"level_up":15,"machine":32,"machine_archive":35,"move_memory_reminder":2,"shared_egg":4} |
| [758: ミジュマル](pokemon/758.md) | {"egg":8,"level_up":15,"machine":24,"machine_archive":13,"shared_egg":8} |
| [759: フタチマル](pokemon/759.md) | {"build_learnable_preservation":6,"egg":1,"level_up":15,"machine":25,"machine_archive":14,"shared_egg":8} |
| [760: ダイケンキ](pokemon/760.md) | {"build_learnable_preservation":6,"egg":1,"level_up":17,"machine":27,"machine_archive":21,"shared_egg":8} |
| [761: ミネズミ](pokemon/761.md) | {"egg":9,"level_up":17,"machine":10,"machine_archive":12,"tutor":9,"tutor_archive":6} |
| [762: ミルホッグ](pokemon/762.md) | {"build_learnable_preservation":8,"egg":1,"level_up":23,"machine":14,"machine_archive":17,"tutor":10,"tutor_archive":12} |
| [763: ヨーテリー](pokemon/763.md) | {"egg":6,"level_up":14,"machine":14,"machine_archive":19,"shared_egg":6} |
| [764: ハーデリア](pokemon/764.md) | {"build_learnable_preservation":5,"egg":1,"level_up":14,"machine":15,"machine_archive":19,"shared_egg":6} |
| [765: ムーランド](pokemon/765.md) | {"build_learnable_preservation":5,"egg":1,"level_up":17,"machine":17,"machine_archive":22,"shared_egg":6} |
| [766: チョロネコ](pokemon/766.md) | {"egg":6,"level_up":12,"machine":23,"machine_archive":14,"shared_egg":6,"tutor":1} |
| [767: レパルダス](pokemon/767.md) | {"build_learnable_preservation":6,"egg":1,"level_up":12,"machine":24,"machine_archive":17,"shared_egg":6,"tutor":2,"tutor_archive":1} |
| [768: ヤナップ](pokemon/768.md) | {"egg":12,"level_up":16,"machine":12,"machine_archive":17,"tutor":10,"tutor_archive":8} |
| [769: ヤナッキー](pokemon/769.md) | {"build_learnable_preservation":16,"egg":1,"level_up":4,"machine":15,"machine_archive":19,"tutor":12,"tutor_archive":8} |
| [770: バオップ](pokemon/770.md) | {"egg":13,"level_up":16,"machine":14,"machine_archive":18,"tutor":10,"tutor_archive":6} |
| [771: バオッキー](pokemon/771.md) | {"build_learnable_preservation":15,"egg":1,"level_up":4,"machine":17,"machine_archive":20,"tutor":12,"tutor_archive":6} |
| [772: ヒヤップ](pokemon/772.md) | {"egg":11,"level_up":16,"machine":15,"machine_archive":17,"tutor":11,"tutor_archive":7} |
| [773: ヒヤッキー](pokemon/773.md) | {"build_learnable_preservation":14,"egg":1,"level_up":4,"machine":18,"machine_archive":19,"tutor":13,"tutor_archive":7} |
| [774: ムンナ](pokemon/774.md) | {"egg":2,"level_up":15,"machine":18,"machine_archive":18,"shared_egg":2,"tutor":1} |
| [775: ムシャーナ](pokemon/775.md) | {"build_learnable_preservation":2,"egg":1,"level_up":16,"machine":18,"machine_archive":21,"shared_egg":2,"tutor":2} |
| [776: マメパト](pokemon/776.md) | {"egg":5,"level_up":13,"machine":12,"machine_archive":10,"shared_egg":5,"tutor":1} |
| [777: ハトーボー](pokemon/777.md) | {"build_learnable_preservation":5,"egg":2,"level_up":13,"machine":12,"machine_archive":10,"shared_egg":5,"tutor":1} |
| [778: ケンホロウ](pokemon/778.md) | {"build_learnable_preservation":5,"egg":2,"level_up":13,"machine":13,"machine_archive":13,"shared_egg":5,"tutor":1} |
| [779: シママ](pokemon/779.md) | {"egg":4,"level_up":12,"machine":19,"machine_archive":16,"shared_egg":4} |
| [780: ゼブライカ](pokemon/780.md) | {"build_learnable_preservation":4,"egg":1,"level_up":12,"machine":21,"machine_archive":21,"shared_egg":4} |
| [781: ダンゴロ](pokemon/781.md) | {"egg":5,"level_up":13,"machine":14,"machine_archive":9,"shared_egg":5,"tutor":1} |
| [782: ガントル](pokemon/782.md) | {"build_learnable_preservation":5,"egg":1,"level_up":15,"machine":15,"machine_archive":10,"shared_egg":5,"tutor":1} |
| [783: ギガイアス](pokemon/783.md) | {"build_learnable_preservation":5,"egg":1,"level_up":14,"machine":17,"machine_archive":16,"shared_egg":5,"tutor":1} |
| [784: コロモリ](pokemon/784.md) | {"egg":5,"level_up":13,"machine":25,"machine_archive":23,"shared_egg":5,"tutor":2} |
| [785: ココロモリ](pokemon/785.md) | {"build_learnable_preservation":4,"egg":2,"level_up":13,"machine":26,"machine_archive":25,"shared_egg":5,"tutor":2} |
| [786: モグリュー](pokemon/786.md) | {"egg":2,"level_up":14,"machine":19,"machine_archive":18,"shared_egg":2} |
| [787: ドリュウズ](pokemon/787.md) | {"build_learnable_preservation":1,"egg":2,"level_up":15,"machine":23,"machine_archive":24,"shared_egg":2} |
| [788: タブンネ](pokemon/788.md) | {"egg":4,"level_up":17,"machine":31,"machine_archive":27,"shared_egg":4} |
| [789: ドッコラー](pokemon/789.md) | {"egg":5,"level_up":14,"machine":24,"machine_archive":14,"shared_egg":5} |
| [790: ドテッコツ](pokemon/790.md) | {"build_learnable_preservation":4,"egg":1,"level_up":14,"machine":24,"machine_archive":15,"shared_egg":5} |
| [791: ローブシン](pokemon/791.md) | {"build_learnable_preservation":4,"egg":1,"level_up":14,"machine":27,"machine_archive":21,"shared_egg":5} |
| [792: オタマロ](pokemon/792.md) | {"egg":4,"level_up":14,"machine":11,"machine_archive":15,"shared_egg":4} |
| [793: ガマガル](pokemon/793.md) | {"build_learnable_preservation":4,"egg":2,"level_up":14,"machine":13,"machine_archive":16,"shared_egg":4} |
| [794: ガマゲロゲ](pokemon/794.md) | {"build_learnable_preservation":4,"egg":2,"level_up":17,"machine":25,"machine_archive":25,"shared_egg":4} |
| [795: ナゲキ](pokemon/795.md) | {"egg":1,"level_up":13,"machine":23,"machine_archive":21,"tutor":1} |
| [796: ダゲキ](pokemon/796.md) | {"egg":1,"level_up":13,"machine":23,"machine_archive":21,"tutor":1} |
| [797: クルミル](pokemon/797.md) | {"egg":5,"level_up":9,"machine":18,"machine_archive":11,"shared_egg":5} |
| [798: クルマユ](pokemon/798.md) | {"build_learnable_preservation":4,"egg":2,"level_up":10,"machine":19,"machine_archive":11,"shared_egg":5} |
| [799: ハハコモリ](pokemon/799.md) | {"build_learnable_preservation":6,"egg":2,"level_up":13,"machine":28,"machine_archive":21,"move_memory_reminder":1,"shared_egg":5} |
| [800: フシデ](pokemon/800.md) | {"egg":2,"level_up":13,"machine":11,"machine_archive":13,"shared_egg":2,"tutor_archive":2} |
| [801: ホイーガ](pokemon/801.md) | {"build_learnable_preservation":2,"egg":2,"level_up":15,"machine":11,"machine_archive":13,"shared_egg":2,"tutor_archive":2} |
| [802: ペンドラー](pokemon/802.md) | {"build_learnable_preservation":2,"egg":2,"level_up":16,"machine":21,"machine_archive":21,"shared_egg":2,"tutor_archive":2} |
| [803: モンメン](pokemon/803.md) | {"egg":5,"level_up":17,"machine":15,"machine_archive":9,"shared_egg":5} |
| [804: エルフーン](pokemon/804.md) | {"build_learnable_preservation":4,"egg":2,"level_up":22,"machine":22,"machine_archive":14,"shared_egg":5} |
| [805: バスラオ](pokemon/805.md) | {"egg":2,"level_up":16,"machine":18,"machine_archive":19,"shared_egg":2} |
| [806: ダルマッカ](pokemon/806.md) | {"egg":6,"level_up":14,"machine":17,"machine_archive":21,"shared_egg":6} |
| [807: ヒヒダルマ](pokemon/807.md) | {"build_learnable_preservation":5,"egg":1,"level_up":16,"machine":26,"machine_archive":31,"shared_egg":6,"tutor":3} |
| [808: マラカッチ](pokemon/808.md) | {"egg":2,"level_up":20,"machine":16,"machine_archive":16,"shared_egg":2,"tutor":1} |
| [809: シンボラー](pokemon/809.md) | {"egg":3,"level_up":15,"machine":23,"machine_archive":22,"shared_egg":3,"tutor":2} |
| [810: デスマス](pokemon/810.md) | {"egg":1,"level_up":16,"machine":14,"machine_archive":16,"shared_egg":1,"tutor":1} |
| [811: デスカーン](pokemon/811.md) | {"build_learnable_preservation":1,"egg":1,"level_up":19,"machine":17,"machine_archive":23,"shared_egg":1,"tutor":1} |
| [812: プロトーガ](pokemon/812.md) | {"egg":6,"level_up":17,"machine":22,"machine_archive":17,"shared_egg":6,"tutor":1} |
| [813: アバゴーラ](pokemon/813.md) | {"build_learnable_preservation":6,"egg":2,"level_up":17,"machine":24,"machine_archive":22,"shared_egg":6,"tutor":1} |
| [814: アーケン](pokemon/814.md) | {"egg":6,"level_up":17,"machine":19,"machine_archive":18,"shared_egg":6,"tutor":3} |
| [815: アーケオス](pokemon/815.md) | {"build_learnable_preservation":6,"egg":2,"level_up":17,"machine":22,"machine_archive":21,"shared_egg":6,"tutor":3} |
| [816: ヤブクロン](pokemon/816.md) | {"egg":5,"level_up":17,"machine":18,"machine_archive":9,"shared_egg":5,"tutor":1} |
| [817: ダストダス](pokemon/817.md) | {"build_learnable_preservation":5,"egg":1,"level_up":19,"machine":23,"machine_archive":16,"shared_egg":5,"tutor":1} |
| [818: ゾロア](pokemon/818.md) | {"egg":6,"level_up":14,"machine":24,"machine_archive":21,"shared_egg":6} |
| [819: ゾロアーク](pokemon/819.md) | {"build_learnable_preservation":6,"egg":1,"level_up":15,"machine":30,"machine_archive":28,"shared_egg":6} |
| [820: チラーミィ](pokemon/820.md) | {"egg":5,"level_up":14,"machine":23,"machine_archive":16,"shared_egg":5} |
| [821: チラチーノ](pokemon/821.md) | {"build_learnable_preservation":10,"egg":1,"level_up":5,"machine":26,"machine_archive":21,"move_memory_reminder":11,"shared_egg":5} |
| [822: ゴチム](pokemon/822.md) | {"egg":5,"level_up":14,"machine":23,"machine_archive":20,"shared_egg":5} |
| [823: ゴチミル](pokemon/823.md) | {"build_learnable_preservation":5,"egg":1,"level_up":13,"machine":23,"machine_archive":21,"shared_egg":5} |
| [824: ゴチルゼル](pokemon/824.md) | {"build_learnable_preservation":5,"egg":1,"level_up":14,"machine":26,"machine_archive":24,"shared_egg":5} |
| [825: ユニラン](pokemon/825.md) | {"egg":3,"level_up":14,"machine":22,"machine_archive":21,"shared_egg":3} |
| [826: ダブラン](pokemon/826.md) | {"build_learnable_preservation":2,"egg":1,"level_up":14,"machine":22,"machine_archive":21,"shared_egg":3} |
| [827: ランクルス](pokemon/827.md) | {"build_learnable_preservation":2,"egg":1,"level_up":15,"machine":29,"machine_archive":27,"shared_egg":3} |
| [828: コアルヒー](pokemon/828.md) | {"egg":6,"level_up":14,"machine":18,"machine_archive":11,"shared_egg":6} |
| [829: スワンナ](pokemon/829.md) | {"build_learnable_preservation":5,"egg":2,"level_up":14,"machine":21,"machine_archive":16,"shared_egg":6} |
| [830: バニプッチ](pokemon/830.md) | {"egg":6,"level_up":14,"machine":12,"machine_archive":12,"shared_egg":6} |
| [831: バニリッチ](pokemon/831.md) | {"build_learnable_preservation":5,"egg":1,"level_up":14,"machine":12,"machine_archive":12,"shared_egg":6} |
| [832: バイバニラ](pokemon/832.md) | {"build_learnable_preservation":4,"egg":1,"level_up":17,"machine":12,"machine_archive":16,"shared_egg":6} |
| [833: シキジカ](pokemon/833.md) | {"egg":7,"level_up":12,"machine":20,"machine_archive":17,"shared_egg":7} |
| [834: メブキジカ](pokemon/834.md) | {"build_learnable_preservation":2,"egg":2,"level_up":14,"machine":24,"machine_archive":22,"shared_egg":7} |
| [835: エモンガ](pokemon/835.md) | {"egg":6,"level_up":13,"machine":20,"machine_archive":14,"shared_egg":6,"tutor":2} |
| [836: カブルモ](pokemon/836.md) | {"egg":5,"level_up":14,"machine":14,"machine_archive":9,"shared_egg":5} |
| [837: シュバルゴ](pokemon/837.md) | {"build_learnable_preservation":5,"egg":2,"level_up":21,"machine":18,"machine_archive":17,"shared_egg":5,"tutor":1} |
| [838: タマゲタケ](pokemon/838.md) | {"egg":4,"level_up":14,"machine":15,"machine_archive":9,"shared_egg":4} |
| [839: モロバレル](pokemon/839.md) | {"build_learnable_preservation":4,"egg":2,"level_up":14,"machine":16,"machine_archive":13,"shared_egg":4} |
| [840: プルリル](pokemon/840.md) | {"egg":6,"level_up":14,"machine":24,"machine_archive":12,"shared_egg":6,"tutor":1} |
| [841: ブルンゲル](pokemon/841.md) | {"build_learnable_preservation":5,"egg":2,"level_up":15,"machine":24,"machine_archive":15,"shared_egg":6,"tutor":1} |
| [842: ママンボウ](pokemon/842.md) | {"egg":6,"level_up":15,"machine":24,"machine_archive":15,"shared_egg":6} |
| [843: リグレー](pokemon/843.md) | {"egg":4,"level_up":13,"machine":18,"machine_archive":21,"shared_egg":4,"tutor":2} |
| [844: オーベム](pokemon/844.md) | {"build_learnable_preservation":4,"egg":1,"level_up":14,"machine":20,"machine_archive":25,"shared_egg":4,"tutor":2} |
| [845: ヒトモシ](pokemon/845.md) | {"egg":4,"level_up":16,"machine":22,"machine_archive":17,"shared_egg":4} |
| [846: ランプラー](pokemon/846.md) | {"build_learnable_preservation":3,"egg":2,"level_up":16,"machine":22,"machine_archive":18,"shared_egg":4} |
| [847: シャンデラ](pokemon/847.md) | {"build_learnable_preservation":3,"egg":2,"level_up":16,"machine":23,"machine_archive":20,"shared_egg":4} |
| [848: キバゴ](pokemon/848.md) | {"egg":6,"level_up":18,"machine":23,"machine_archive":21,"shared_egg":6} |
| [849: オノンド](pokemon/849.md) | {"build_learnable_preservation":5,"egg":1,"level_up":18,"machine":23,"machine_archive":22,"shared_egg":6} |
| [850: オノノクス](pokemon/850.md) | {"build_learnable_preservation":5,"egg":1,"level_up":18,"machine":28,"machine_archive":25,"shared_egg":6} |
| [851: クマシュン](pokemon/851.md) | {"egg":3,"level_up":16,"machine":25,"machine_archive":22,"shared_egg":3} |
| [852: ツンベアー](pokemon/852.md) | {"build_learnable_preservation":2,"egg":1,"level_up":20,"machine":32,"machine_archive":31,"shared_egg":3} |
| [853: チョボマキ](pokemon/853.md) | {"egg":4,"level_up":14,"machine":13,"machine_archive":10,"shared_egg":4,"tutor_archive":1} |
| [854: アギルダー](pokemon/854.md) | {"build_learnable_preservation":4,"egg":1,"level_up":22,"machine":17,"machine_archive":17,"shared_egg":4,"tutor_archive":1} |
| [855: クリムガン](pokemon/855.md) | {"egg":4,"level_up":13,"machine":28,"machine_archive":21,"shared_egg":4,"tutor":4} |
| [856: ゴビット](pokemon/856.md) | {"egg":2,"level_up":16,"machine":33,"machine_archive":22} |
| [857: ゴルーグ](pokemon/857.md) | {"egg":2,"level_up":16,"machine":39,"machine_archive":31,"move_memory_reminder":2} |
| [858: コマタナ](pokemon/858.md) | {"egg":4,"level_up":15,"machine":27,"machine_archive":14,"shared_egg":4} |
| [859: キリキザン](pokemon/859.md) | {"build_learnable_preservation":4,"egg":2,"level_up":16,"machine":29,"machine_archive":17,"shared_egg":4} |
| [860: バッフロン](pokemon/860.md) | {"egg":7,"level_up":13,"machine":21,"machine_archive":23,"shared_egg":7,"tutor":1} |
| [861: ワシボン](pokemon/861.md) | {"egg":2,"level_up":14,"machine":20,"machine_archive":14,"shared_egg":2} |
| [862: ウォーグル](pokemon/862.md) | {"build_learnable_preservation":1,"egg":2,"level_up":15,"machine":21,"machine_archive":18,"shared_egg":2} |
| [863: バルチャイ](pokemon/863.md) | {"egg":3,"level_up":14,"machine":24,"machine_archive":15,"shared_egg":3} |
| [864: バルジーナ](pokemon/864.md) | {"build_learnable_preservation":1,"egg":2,"level_up":17,"machine":26,"machine_archive":19,"shared_egg":3} |
| [865: クイタラン](pokemon/865.md) | {"egg":5,"level_up":16,"machine":21,"machine_archive":17,"shared_egg":5,"tutor":2} |
| [866: アイアント](pokemon/866.md) | {"egg":5,"level_up":16,"machine":17,"machine_archive":15,"shared_egg":5,"tutor":1,"tutor_archive":1} |
| [867: モノズ](pokemon/867.md) | {"egg":4,"level_up":17,"machine":14,"machine_archive":19,"shared_egg":4} |
| [868: ジヘッド](pokemon/868.md) | {"build_learnable_preservation":3,"egg":2,"level_up":18,"machine":16,"machine_archive":20,"shared_egg":4} |
| [869: サザンドラ](pokemon/869.md) | {"build_learnable_preservation":3,"egg":2,"level_up":20,"machine":34,"machine_archive":28,"shared_egg":4} |
| [870: メラルバ](pokemon/870.md) | {"egg":4,"level_up":12,"machine":20,"machine_archive":17,"shared_egg":4} |
| [871: ウルガモス](pokemon/871.md) | {"build_learnable_preservation":4,"egg":2,"level_up":22,"machine":25,"machine_archive":22,"shared_egg":4} |
| [872: コバルオン](pokemon/872.md) | {"level_up":14,"machine":28,"machine_archive":23} |
| [873: テラキオン](pokemon/873.md) | {"level_up":14,"machine":25,"machine_archive":23} |
| [874: ビリジオン](pokemon/874.md) | {"level_up":14,"machine":24,"machine_archive":25,"move_memory_reminder":1} |
| [875: トルネロス](pokemon/875.md) | {"level_up":17,"machine":29,"machine_archive":19} |
| [876: ボルトロス](pokemon/876.md) | {"level_up":17,"machine":32,"machine_archive":22} |
| [877: レシラム](pokemon/877.md) | {"level_up":15,"machine":27,"machine_archive":32} |
| [878: ゼクロム](pokemon/878.md) | {"level_up":15,"machine":32,"machine_archive":32} |
| [879: ランドロス](pokemon/879.md) | {"level_up":17,"machine":26,"machine_archive":22} |
| [880: キュレム](pokemon/880.md) | {"level_up":15,"machine":28,"machine_archive":27} |
| [881: ケルディオ](pokemon/881.md) | {"level_up":15,"machine":27,"machine_archive":21} |
| [882: メロエッタ](pokemon/882.md) | {"level_up":15,"machine":34,"machine_archive":25} |
| [883: ゲノセクト](pokemon/883.md) | {"level_up":15,"machine":24,"machine_archive":17,"tutor":1} |
| [884: ケンホロウ](pokemon/884.md) | {"build_learnable_preservation":5,"level_up":13,"machine":13,"machine_archive":13,"shared_egg":5,"tutor":1} |
| [885: プルリル](pokemon/885.md) | {"egg":6,"level_up":14,"machine":24,"machine_archive":12,"shared_egg":6,"tutor":1} |
| [886: ブルンゲル](pokemon/886.md) | {"build_learnable_preservation":5,"egg":2,"level_up":15,"machine":24,"machine_archive":15,"shared_egg":6,"tutor":1} |
| [887: かげ](pokemon/887.md) | {"level_up":6,"tutor":4} |
| [888: ミノムッチ](pokemon/888.md) | {"egg":1,"level_up":4,"machine":1,"machine_archive":1,"tutor":2,"tutor_archive":1} |
| [889: ミノムッチ](pokemon/889.md) | {"egg":1,"level_up":4,"machine":1,"machine_archive":1,"tutor":2,"tutor_archive":1} |
| [890: ミノマダム](pokemon/890.md) | {"egg":2,"level_up":19,"machine":13,"machine_archive":17,"tutor":7,"tutor_archive":3} |
| [891: ミノマダム](pokemon/891.md) | {"egg":2,"level_up":20,"machine":11,"machine_archive":17,"tutor":8,"tutor_archive":5} |
| [892: カラナクシ](pokemon/892.md) | {"egg":11,"level_up":11,"machine":21,"machine_archive":15,"shared_egg":11} |
| [893: トリトドン](pokemon/893.md) | {"build_learnable_preservation":10,"egg":2,"level_up":11,"machine":26,"machine_archive":21,"shared_egg":11} |
| [894: ロトム](pokemon/894.md) | {"build_learnable_preservation":1,"egg":2,"level_up":13,"machine":23,"machine_archive":16} |
| [895: ロトム](pokemon/895.md) | {"build_learnable_preservation":1,"egg":2,"level_up":13,"machine":23,"machine_archive":16} |
| [896: ロトム](pokemon/896.md) | {"build_learnable_preservation":1,"egg":2,"level_up":13,"machine":23,"machine_archive":16} |
| [897: ロトム](pokemon/897.md) | {"build_learnable_preservation":1,"egg":2,"level_up":13,"machine":23,"machine_archive":16} |
| [898: ロトム](pokemon/898.md) | {"build_learnable_preservation":1,"egg":2,"level_up":13,"machine":23,"machine_archive":16} |
| [899: ギラティナ](pokemon/899.md) | {"level_up":14,"machine":28,"machine_archive":23} |
| [900: シェイミ](pokemon/900.md) | {"build_learnable_preservation":2,"level_up":12,"machine":18,"machine_archive":20} |
| [901: アルセウス](pokemon/901.md) | {"level_up":12,"machine":59,"machine_archive":55} |
| [902: アルセウス](pokemon/902.md) | {"level_up":12,"machine":59,"machine_archive":55} |
| [903: アルセウス](pokemon/903.md) | {"level_up":12,"machine":59,"machine_archive":55} |
| [904: アルセウス](pokemon/904.md) | {"level_up":12,"machine":59,"machine_archive":55} |
| [905: アルセウス](pokemon/905.md) | {"level_up":12,"machine":59,"machine_archive":55} |
| [906: アルセウス](pokemon/906.md) | {"level_up":12,"machine":59,"machine_archive":55} |
| [907: アルセウス](pokemon/907.md) | {"level_up":12,"machine":59,"machine_archive":55} |
| [908: アルセウス](pokemon/908.md) | {"level_up":12,"machine":59,"machine_archive":55} |
| [909: アルセウス](pokemon/909.md) | {"level_up":12,"machine":59,"machine_archive":55} |
| [910: アルセウス](pokemon/910.md) | {"level_up":12,"machine":59,"machine_archive":55} |
| [911: アルセウス](pokemon/911.md) | {"level_up":12,"machine":59,"machine_archive":55} |
| [912: アルセウス](pokemon/912.md) | {"level_up":12,"machine":59,"machine_archive":55} |
| [913: アルセウス](pokemon/913.md) | {"level_up":12,"machine":59,"machine_archive":55} |
| [914: アルセウス](pokemon/914.md) | {"level_up":12,"machine":59,"machine_archive":55} |
| [915: アルセウス](pokemon/915.md) | {"level_up":12,"machine":59,"machine_archive":55} |
| [916: アルセウス](pokemon/916.md) | {"level_up":12,"machine":59,"machine_archive":55} |
| [917: バスラオ](pokemon/917.md) | {"egg":2,"level_up":16,"machine":18,"machine_archive":19,"shared_egg":2} |
| [918: ヒヒダルマ](pokemon/918.md) | {"egg":1,"level_up":22,"machine":48,"tutor":10} |
| [919: シキジカ](pokemon/919.md) | {"egg":7,"level_up":12,"machine":20,"machine_archive":17,"shared_egg":7} |
| [920: シキジカ](pokemon/920.md) | {"egg":7,"level_up":12,"machine":20,"machine_archive":17,"shared_egg":7} |
| [921: シキジカ](pokemon/921.md) | {"egg":7,"level_up":12,"machine":20,"machine_archive":17,"shared_egg":7} |
| [922: メブキジカ](pokemon/922.md) | {"build_learnable_preservation":2,"egg":2,"level_up":14,"machine":24,"machine_archive":22,"shared_egg":7} |
| [923: メブキジカ](pokemon/923.md) | {"build_learnable_preservation":2,"egg":2,"level_up":14,"machine":24,"machine_archive":22,"shared_egg":7} |
| [924: メブキジカ](pokemon/924.md) | {"build_learnable_preservation":2,"egg":2,"level_up":14,"machine":24,"machine_archive":22,"shared_egg":7} |
| [925: ヒポポタス](pokemon/925.md) | {"egg":5,"level_up":15,"machine":17,"machine_archive":19,"shared_egg":5} |
| [926: カバルドン](pokemon/926.md) | {"build_learnable_preservation":4,"level_up":18,"machine":18,"machine_archive":24,"shared_egg":5} |
| [927: メロエッタ](pokemon/927.md) | {"level_up":21,"machine":50,"tutor":9} |
| [928: ゲノセクト](pokemon/928.md) | {"level_up":15,"machine":24,"machine_archive":17,"tutor":1} |
| [929: ゲノセクト](pokemon/929.md) | {"level_up":15,"machine":24,"machine_archive":17,"tutor":1} |
| [930: ゲノセクト](pokemon/930.md) | {"level_up":15,"machine":24,"machine_archive":17,"tutor":1} |
| [931: ゲノセクト](pokemon/931.md) | {"level_up":15,"machine":24,"machine_archive":17,"tutor":1} |
| [932: チェリム](pokemon/932.md) | {"egg":1,"level_up":17,"machine":29,"tutor":10} |
| [933: キュレム](pokemon/933.md) | {"level_up":15,"machine":28,"machine_archive":27} |
| [934: キュレム](pokemon/934.md) | {"level_up":15,"machine":28,"machine_archive":27} |
| [935: トルネロス](pokemon/935.md) | {"level_up":17,"machine":29,"machine_archive":19} |
| [936: ボルトロス](pokemon/936.md) | {"level_up":17,"machine":32,"machine_archive":22} |
| [937: ランドロス](pokemon/937.md) | {"level_up":17,"machine":26,"machine_archive":22} |
| [938: ケルディオ](pokemon/938.md) | {"level_up":15,"machine":27,"machine_archive":21} |
| [939: ハリマロン](pokemon/939.md) | {"egg":7,"level_up":12,"machine":25,"machine_archive":25,"shared_egg":7} |
| [940: ハリボーグ](pokemon/940.md) | {"build_learnable_preservation":3,"egg":1,"level_up":13,"machine":30,"machine_archive":26,"shared_egg":7} |
| [941: ブリガロン](pokemon/941.md) | {"build_learnable_preservation":3,"egg":2,"level_up":18,"machine":35,"machine_archive":39,"shared_egg":7} |
| [942: フォッコ](pokemon/942.md) | {"egg":5,"level_up":14,"machine":22,"machine_archive":20,"shared_egg":5} |
| [943: テールナー](pokemon/943.md) | {"build_learnable_preservation":3,"egg":1,"level_up":15,"machine":24,"machine_archive":22,"shared_egg":5} |
| [944: マフォクシー](pokemon/944.md) | {"build_learnable_preservation":3,"egg":2,"level_up":20,"machine":29,"machine_archive":35,"shared_egg":5} |
| [945: ケロマツ](pokemon/945.md) | {"egg":5,"level_up":14,"machine":24,"machine_archive":15,"shared_egg":5} |
| [946: ゲコガシラ](pokemon/946.md) | {"build_learnable_preservation":3,"egg":1,"level_up":14,"machine":27,"machine_archive":16,"shared_egg":5} |
| [947: ゲッコウガ](pokemon/947.md) | {"build_learnable_preservation":5,"egg":2,"level_up":18,"machine":32,"machine_archive":21,"shared_egg":5} |
| [948: ホルビー](pokemon/948.md) | {"egg":2,"level_up":15,"machine":21,"machine_archive":13,"shared_egg":2} |
| [949: ホルード](pokemon/949.md) | {"build_learnable_preservation":2,"egg":2,"level_up":16,"machine":27,"machine_archive":25,"shared_egg":2,"tutor":1} |
| [950: ヤヤコマ](pokemon/950.md) | {"egg":3,"level_up":12,"machine":20,"machine_archive":11,"shared_egg":3} |
| [951: ヒノヤコマ](pokemon/951.md) | {"build_learnable_preservation":2,"egg":2,"level_up":14,"machine":22,"machine_archive":14,"shared_egg":3} |
| [952: ファイアロー](pokemon/952.md) | {"build_learnable_preservation":2,"egg":2,"level_up":16,"machine":23,"machine_archive":18,"shared_egg":3} |
| [953: コフキムシ](pokemon/953.md) | {"egg":2,"level_up":4,"machine":2,"machine_archive":2,"shared_egg":2} |
| [954: コフーライ](pokemon/954.md) | {"build_learnable_preservation":4,"egg":1,"level_up":2,"machine":4,"machine_archive":2,"shared_egg":2} |
| [955: ビビヨン](pokemon/955.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":2} |
| [956: シシコ](pokemon/956.md) | {"egg":4,"level_up":15,"machine":20,"machine_archive":19,"shared_egg":4} |
| [957: カエンジシ](pokemon/957.md) | {"build_learnable_preservation":1,"egg":2,"level_up":16,"machine":22,"machine_archive":22,"shared_egg":4} |
| [958: フラベベ](pokemon/958.md) | {"egg":3,"level_up":14,"machine":19,"machine_archive":15,"shared_egg":3} |
| [959: フラエッテ](pokemon/959.md) | {"build_learnable_preservation":2,"egg":1,"level_up":14,"machine":19,"machine_archive":18,"shared_egg":3} |
| [960: フラージェス](pokemon/960.md) | {"build_learnable_preservation":6,"egg":1,"level_up":12,"machine":19,"machine_archive":22,"shared_egg":3} |
| [961: メェークル](pokemon/961.md) | {"egg":4,"level_up":15,"machine":21,"machine_archive":17,"shared_egg":4} |
| [962: ゴーゴート](pokemon/962.md) | {"build_learnable_preservation":2,"egg":1,"level_up":18,"machine":23,"machine_archive":21,"shared_egg":4} |
| [963: ヤンチャム](pokemon/963.md) | {"egg":5,"level_up":13,"machine":29,"machine_archive":19,"shared_egg":5,"tutor":2} |
| [964: ゴロンダ](pokemon/964.md) | {"build_learnable_preservation":5,"egg":2,"level_up":17,"machine":36,"machine_archive":31,"shared_egg":5,"tutor":2} |
| [965: トリミアン](pokemon/965.md) | {"egg":5,"level_up":13,"machine":13,"machine_archive":15,"tutor":5,"tutor_archive":4} |
| [966: ニャスパー](pokemon/966.md) | {"egg":2,"level_up":10,"machine":21,"machine_archive":15,"shared_egg":2} |
| [967: ニャオニクス](pokemon/967.md) | {"build_learnable_preservation":2,"egg":1,"level_up":19,"machine":23,"machine_archive":23,"shared_egg":2} |
| [968: ヒトツキ](pokemon/968.md) | {"egg":3,"level_up":14,"machine":15,"machine_archive":12,"shared_egg":3,"tutor":1} |
| [969: ニダンギル](pokemon/969.md) | {"build_learnable_preservation":2,"egg":2,"level_up":14,"machine":15,"machine_archive":12,"shared_egg":3,"tutor":1} |
| [970: ギルガルド](pokemon/970.md) | {"build_learnable_preservation":2,"egg":2,"level_up":17,"machine":18,"machine_archive":14,"shared_egg":3,"tutor":1} |
| [971: シュシュプ](pokemon/971.md) | {"egg":3,"level_up":15,"machine":17,"machine_archive":12,"shared_egg":3,"tutor":1} |
| [972: フレフワン](pokemon/972.md) | {"build_learnable_preservation":3,"egg":1,"level_up":18,"machine":19,"machine_archive":16,"shared_egg":3,"tutor":1} |
| [973: ペロッパフ](pokemon/973.md) | {"egg":4,"level_up":15,"machine":18,"machine_archive":9,"shared_egg":4,"tutor":1} |
| [974: ペロリーム](pokemon/974.md) | {"build_learnable_preservation":3,"egg":1,"level_up":16,"machine":19,"machine_archive":13,"shared_egg":4,"tutor":1} |
| [975: マーイーカ](pokemon/975.md) | {"egg":3,"level_up":15,"machine":25,"machine_archive":17,"shared_egg":3} |
| [976: カラマネロ](pokemon/976.md) | {"build_learnable_preservation":3,"egg":2,"level_up":16,"machine":27,"machine_archive":22,"shared_egg":3} |
| [977: カメテテ](pokemon/977.md) | {"egg":3,"level_up":13,"machine":29,"machine_archive":18,"shared_egg":3} |
| [978: ガメノデス](pokemon/978.md) | {"build_learnable_preservation":3,"egg":2,"level_up":15,"machine":32,"machine_archive":27,"shared_egg":3,"tutor":1} |
| [979: クズモー](pokemon/979.md) | {"egg":4,"level_up":13,"machine":25,"machine_archive":16,"shared_egg":4} |
| [980: ドラミドロ](pokemon/980.md) | {"build_learnable_preservation":3,"egg":2,"level_up":14,"machine":27,"machine_archive":19,"shared_egg":4} |
| [981: ウデッポウ](pokemon/981.md) | {"egg":3,"level_up":13,"machine":26,"machine_archive":10,"shared_egg":3} |
| [982: ブロスター](pokemon/982.md) | {"build_learnable_preservation":3,"egg":1,"level_up":16,"machine":29,"machine_archive":14,"shared_egg":3} |
| [983: エリキテル](pokemon/983.md) | {"egg":3,"level_up":13,"machine":20,"machine_archive":12,"shared_egg":3,"tutor":2} |
| [984: エレザード](pokemon/984.md) | {"build_learnable_preservation":3,"egg":2,"level_up":15,"machine":26,"machine_archive":22,"shared_egg":3,"tutor":2} |
| [985: チゴラス](pokemon/985.md) | {"egg":4,"level_up":14,"machine":21,"machine_archive":23,"shared_egg":4,"tutor":4} |
| [986: ガチゴラス](pokemon/986.md) | {"build_learnable_preservation":4,"egg":2,"level_up":16,"machine":22,"machine_archive":27,"shared_egg":4,"tutor":4} |
| [987: アマルス](pokemon/987.md) | {"egg":6,"level_up":16,"machine":23,"machine_archive":19,"shared_egg":6,"tutor":1} |
| [988: アマルルガ](pokemon/988.md) | {"build_learnable_preservation":5,"egg":2,"level_up":16,"machine":25,"machine_archive":22,"shared_egg":6,"tutor":1} |
| [989: ニンフィア](pokemon/989.md) | {"build_learnable_preservation":6,"egg":1,"level_up":23,"machine":18,"machine_archive":25,"shared_egg":8} |
| [990: ルチャブル](pokemon/990.md) | {"egg":6,"level_up":16,"machine":37,"machine_archive":21,"shared_egg":6} |
| [991: デデンネ](pokemon/991.md) | {"egg":3,"level_up":15,"machine":23,"machine_archive":19,"shared_egg":3} |
| [992: メレシー](pokemon/992.md) | {"egg":2,"level_up":14,"machine":23,"machine_archive":23} |
| [993: ヌメラ](pokemon/993.md) | {"egg":2,"level_up":12,"machine":14,"machine_archive":11,"shared_egg":2} |
| [994: ヌメイル](pokemon/994.md) | {"build_learnable_preservation":2,"egg":1,"level_up":14,"machine":15,"machine_archive":15,"shared_egg":2} |
| [995: ヌメルゴン](pokemon/995.md) | {"build_learnable_preservation":3,"egg":1,"level_up":17,"machine":27,"machine_archive":25,"shared_egg":2} |
| [996: クレッフィ](pokemon/996.md) | {"egg":2,"level_up":14,"machine":22,"machine_archive":13,"shared_egg":2} |
| [997: ボクレー](pokemon/997.md) | {"egg":2,"level_up":15,"machine":27,"machine_archive":18,"shared_egg":2} |
| [998: オーロット](pokemon/998.md) | {"build_learnable_preservation":2,"egg":2,"level_up":16,"machine":33,"machine_archive":27,"shared_egg":2} |
| [999: バケッチャ](pokemon/999.md) | {"egg":3,"level_up":16,"machine":21,"machine_archive":15,"shared_egg":3,"tutor":2,"tutor_archive":1} |
| [1000: パンプジン](pokemon/1000.md) | {"build_learnable_preservation":2,"egg":2,"level_up":19,"machine":22,"machine_archive":21,"shared_egg":3,"tutor":2,"tutor_archive":1} |
| [1001: カチコール](pokemon/1001.md) | {"egg":3,"level_up":16,"machine":16,"machine_archive":12,"shared_egg":3} |
| [1002: クレベース](pokemon/1002.md) | {"build_learnable_preservation":2,"egg":1,"level_up":19,"machine":22,"machine_archive":18,"shared_egg":3} |
| [1003: オンバット](pokemon/1003.md) | {"egg":3,"level_up":15,"machine":21,"machine_archive":18,"shared_egg":3} |
| [1004: オンバーン](pokemon/1004.md) | {"build_learnable_preservation":3,"egg":2,"level_up":18,"machine":24,"machine_archive":28,"shared_egg":3} |
| [1005: ゼルネアス](pokemon/1005.md) | {"level_up":19,"machine":21,"machine_archive":17,"tutor":2} |
| [1006: イベルタル](pokemon/1006.md) | {"level_up":19,"machine":22,"machine_archive":14,"tutor":2} |
| [1007: ジガルデ](pokemon/1007.md) | {"level_up":18,"machine":19,"machine_archive":20,"tutor":3,"tutor_archive":1} |
| [1008: ディアンシー](pokemon/1008.md) | {"level_up":15,"machine":29,"machine_archive":25} |
| [1009: フーパ](pokemon/1009.md) | {"build_learnable_preservation":1,"level_up":17,"machine":32,"machine_archive":24} |
| [1010: フーパ](pokemon/1010.md) | {"build_learnable_preservation":1,"level_up":15,"machine":32,"machine_archive":24} |
| [1011: ボルケニオン](pokemon/1011.md) | {"level_up":18,"machine":28,"machine_archive":30} |
| [1012: カエンジシ](pokemon/1012.md) | {"build_learnable_preservation":1,"egg":2,"level_up":16,"machine":22,"machine_archive":22,"shared_egg":4} |
| [1013: ニャオニクス](pokemon/1013.md) | {"build_learnable_preservation":2,"egg":1,"level_up":19,"machine":23,"machine_archive":23,"shared_egg":2} |
| [1014: ギルガルド](pokemon/1014.md) | {"egg":2,"level_up":16,"machine":31,"tutor":8} |
| [1015: アルセウス](pokemon/1015.md) | {"level_up":12,"machine":59,"machine_archive":55} |
| [1016: ジガルデ](pokemon/1016.md) | {"level_up":16,"tutor":7} |
| [1017: ジガルデ](pokemon/1017.md) | {"level_up":16,"tutor":9} |
| [1018: ジガルデ](pokemon/1018.md) | {"level_up":18,"machine":19,"machine_archive":20,"tutor":3,"tutor_archive":1} |
| [1019: ジガルデ](pokemon/1019.md) | {"level_up":19,"machine":35,"tutor":8} |
| [1020: ゲッコウガ](pokemon/1020.md) | {"egg":2,"level_up":27,"machine":42,"tutor":10} |
| [1021: フラベベ](pokemon/1021.md) | {"egg":3,"level_up":14,"machine":19,"machine_archive":15,"shared_egg":3} |
| [1022: フラベベ](pokemon/1022.md) | {"egg":3,"level_up":14,"machine":19,"machine_archive":15,"shared_egg":3} |
| [1023: フラベベ](pokemon/1023.md) | {"egg":3,"level_up":14,"machine":19,"machine_archive":15,"shared_egg":3} |
| [1024: フラベベ](pokemon/1024.md) | {"egg":3,"level_up":14,"machine":19,"machine_archive":15,"shared_egg":3} |
| [1025: フラエッテ](pokemon/1025.md) | {"build_learnable_preservation":2,"egg":1,"level_up":14,"machine":19,"machine_archive":18,"shared_egg":3} |
| [1026: フラエッテ](pokemon/1026.md) | {"build_learnable_preservation":2,"egg":1,"level_up":14,"machine":19,"machine_archive":18,"shared_egg":3} |
| [1027: フラエッテ](pokemon/1027.md) | {"build_learnable_preservation":2,"egg":1,"level_up":14,"machine":19,"machine_archive":18,"shared_egg":3} |
| [1028: フラエッテ](pokemon/1028.md) | {"build_learnable_preservation":2,"egg":1,"level_up":14,"machine":19,"machine_archive":18,"shared_egg":3} |
| [1029: フラエッテ](pokemon/1029.md) | {"egg":1,"level_up":16,"machine":32,"tutor":10} |
| [1030: フラージェス](pokemon/1030.md) | {"build_learnable_preservation":6,"egg":1,"level_up":12,"machine":19,"machine_archive":22,"shared_egg":3} |
| [1031: フラージェス](pokemon/1031.md) | {"build_learnable_preservation":6,"egg":1,"level_up":12,"machine":19,"machine_archive":22,"shared_egg":3} |
| [1032: フラージェス](pokemon/1032.md) | {"build_learnable_preservation":6,"egg":1,"level_up":12,"machine":19,"machine_archive":22,"shared_egg":3} |
| [1033: フラージェス](pokemon/1033.md) | {"build_learnable_preservation":6,"egg":1,"level_up":12,"machine":19,"machine_archive":22,"shared_egg":3} |
| [1034: バケッチャ](pokemon/1034.md) | {"egg":3,"level_up":16,"machine":21,"machine_archive":15,"shared_egg":3,"tutor":2,"tutor_archive":1} |
| [1035: バケッチャ](pokemon/1035.md) | {"egg":3,"level_up":16,"machine":21,"machine_archive":15,"shared_egg":3,"tutor":2,"tutor_archive":1} |
| [1036: バケッチャ](pokemon/1036.md) | {"egg":3,"level_up":16,"machine":21,"machine_archive":15,"shared_egg":3,"tutor":2,"tutor_archive":1} |
| [1037: パンプジン](pokemon/1037.md) | {"build_learnable_preservation":2,"egg":2,"level_up":19,"machine":22,"machine_archive":21,"shared_egg":3,"tutor":2,"tutor_archive":1} |
| [1038: パンプジン](pokemon/1038.md) | {"build_learnable_preservation":2,"egg":2,"level_up":19,"machine":22,"machine_archive":21,"shared_egg":3,"tutor":2,"tutor_archive":1} |
| [1039: パンプジン](pokemon/1039.md) | {"build_learnable_preservation":2,"egg":2,"level_up":19,"machine":22,"machine_archive":21,"shared_egg":3,"tutor":2,"tutor_archive":1} |
| [1040: トリミアン](pokemon/1040.md) | {"egg":5,"level_up":13,"machine":13,"machine_archive":15,"tutor":5,"tutor_archive":4} |
| [1041: トリミアン](pokemon/1041.md) | {"egg":5,"level_up":13,"machine":13,"machine_archive":15,"tutor":5,"tutor_archive":4} |
| [1042: トリミアン](pokemon/1042.md) | {"egg":5,"level_up":13,"machine":13,"machine_archive":15,"tutor":5,"tutor_archive":4} |
| [1043: トリミアン](pokemon/1043.md) | {"egg":5,"level_up":13,"machine":13,"machine_archive":15,"tutor":5,"tutor_archive":4} |
| [1044: トリミアン](pokemon/1044.md) | {"egg":5,"level_up":13,"machine":13,"machine_archive":15,"tutor":5,"tutor_archive":4} |
| [1045: トリミアン](pokemon/1045.md) | {"egg":5,"level_up":13,"machine":13,"machine_archive":15,"tutor":5,"tutor_archive":4} |
| [1046: トリミアン](pokemon/1046.md) | {"egg":5,"level_up":13,"machine":13,"machine_archive":15,"tutor":5,"tutor_archive":4} |
| [1047: トリミアン](pokemon/1047.md) | {"egg":5,"level_up":13,"machine":13,"machine_archive":15,"tutor":5,"tutor_archive":4} |
| [1048: トリミアン](pokemon/1048.md) | {"egg":5,"level_up":13,"machine":13,"machine_archive":15,"tutor":5,"tutor_archive":4} |
| [1049: ビビヨン](pokemon/1049.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":2} |
| [1050: フシギバナ](pokemon/1050.md) | {"egg":2,"level_up":25,"machine":33,"tutor":18} |
| [1051: リザードン](pokemon/1051.md) | {"egg":2,"level_up":23,"machine":35,"tutor":25} |
| [1052: リザードン](pokemon/1052.md) | {"egg":2,"level_up":23,"machine":35,"tutor":25} |
| [1053: カメックス](pokemon/1053.md) | {"egg":1,"level_up":23,"machine":28,"tutor":16} |
| [1054: スピアー](pokemon/1054.md) | {"egg":2,"level_up":19,"machine":38,"tutor":8} |
| [1055: ピジョット](pokemon/1055.md) | {"egg":2,"level_up":21,"machine":27,"tutor":16} |
| [1056: フーディン](pokemon/1056.md) | {"egg":1,"level_up":17,"machine":43,"tutor":14} |
| [1057: ヤドラン](pokemon/1057.md) | {"egg":2,"level_up":22,"machine":52,"tutor":9} |
| [1058: ゲンガー](pokemon/1058.md) | {"egg":2,"level_up":23,"machine":26,"tutor":28} |
| [1059: ガルーラ](pokemon/1059.md) | {"egg":36,"level_up":18,"machine":34,"tutor":31} |
| [1060: カイロス](pokemon/1060.md) | {"egg":23,"level_up":20,"machine":40,"tutor":23} |
| [1061: ギャラドス](pokemon/1061.md) | {"egg":2,"level_up":18,"machine":45,"tutor":3} |
| [1062: プテラ](pokemon/1062.md) | {"egg":24,"level_up":21,"machine":42,"tutor":29} |
| [1063: ミュウツー](pokemon/1063.md) | {"level_up":19,"machine":23,"tutor":21} |
| [1064: ミュウツー](pokemon/1064.md) | {"level_up":19,"machine":23,"tutor":21} |
| [1065: デンリュウ](pokemon/1065.md) | {"egg":1,"level_up":25,"machine":43,"tutor":6} |
| [1066: ハガネール](pokemon/1066.md) | {"egg":2,"level_up":28,"machine":43,"tutor":13} |
| [1067: ハッサム](pokemon/1067.md) | {"egg":2,"level_up":19,"machine":45,"tutor":25} |
| [1068: ヘラクロス](pokemon/1068.md) | {"egg":12,"level_up":22,"machine":41,"tutor":7} |
| [1069: ヘルガー](pokemon/1069.md) | {"egg":2,"level_up":23,"machine":45,"tutor":39} |
| [1070: バンギラス](pokemon/1070.md) | {"egg":2,"level_up":23,"machine":2,"tutor":28} |
| [1071: ジュカイン](pokemon/1071.md) | {"egg":1,"level_up":23,"machine":47,"tutor":4} |
| [1072: バシャーモ](pokemon/1072.md) | {"egg":2,"level_up":23,"machine":48,"tutor":5} |
| [1073: ラグラージ](pokemon/1073.md) | {"egg":2,"level_up":21,"machine":42,"tutor":10} |
| [1074: サーナイト](pokemon/1074.md) | {"egg":2,"level_up":23,"machine":31,"tutor":15} |
| [1075: ヤミラミ](pokemon/1075.md) | {"egg":33,"level_up":21,"machine":37,"tutor":35} |
| [1076: クチート](pokemon/1076.md) | {"egg":35,"level_up":20,"machine":34,"tutor":25} |
| [1077: ボスゴドラ](pokemon/1077.md) | {"egg":2,"level_up":22,"machine":60,"tutor":7} |
| [1078: チャーレム](pokemon/1078.md) | {"egg":2,"level_up":27,"machine":47,"tutor":11} |
| [1079: ライボルト](pokemon/1079.md) | {"egg":1,"level_up":19,"machine":33,"tutor":9} |
| [1080: サメハダー](pokemon/1080.md) | {"egg":2,"level_up":25,"machine":35,"tutor":12} |
| [1081: バクーダ](pokemon/1081.md) | {"egg":2,"level_up":25,"machine":43,"tutor":11} |
| [1082: チルタリス](pokemon/1082.md) | {"egg":2,"level_up":26,"machine":43,"tutor":8} |
| [1083: ジュペッタ](pokemon/1083.md) | {"egg":1,"level_up":21,"machine":37,"tutor":14} |
| [1084: アブソル](pokemon/1084.md) | {"egg":35,"level_up":18,"machine":41,"tutor":12} |
| [1085: オニゴーリ](pokemon/1085.md) | {"egg":1,"level_up":21,"machine":37,"tutor":3} |
| [1086: ボーマンダ](pokemon/1086.md) | {"egg":2,"level_up":25,"machine":40,"tutor":15} |
| [1087: メタグロス](pokemon/1087.md) | {"egg":2,"level_up":18,"machine":2,"tutor":28} |
| [1088: ラティアス](pokemon/1088.md) | {"level_up":22,"machine":37,"tutor":32} |
| [1089: ラティオス](pokemon/1089.md) | {"level_up":22,"machine":36,"tutor":32} |
| [1090: グラードン](pokemon/1090.md) | {"level_up":14,"machine":18,"machine_archive":26,"tutor":5,"tutor_archive":7} |
| [1091: カイオーガ](pokemon/1091.md) | {"level_up":14,"machine":15,"machine_archive":19,"tutor":6,"tutor_archive":4} |
| [1092: レックウザ](pokemon/1092.md) | {"level_up":16,"machine":59,"tutor":10} |
| [1093: ミミロップ](pokemon/1093.md) | {"egg":1,"level_up":26,"machine":42,"tutor":11} |
| [1094: ガブリアス](pokemon/1094.md) | {"egg":2,"level_up":19,"machine":2,"tutor":35} |
| [1095: ルカリオ](pokemon/1095.md) | {"egg":2,"level_up":24,"machine":34,"tutor":41} |
| [1096: ユキノオー](pokemon/1096.md) | {"egg":2,"level_up":22,"machine":35,"tutor":16} |
| [1097: エルレイド](pokemon/1097.md) | {"egg":2,"level_up":25,"machine":37,"tutor":18} |
| [1098: タブンネ](pokemon/1098.md) | {"egg":11,"level_up":23,"machine":51,"tutor":13} |
| [1099: ディアンシー](pokemon/1099.md) | {"level_up":20,"machine":45,"tutor":11} |
| [1100: ディアルガ](pokemon/1100.md) | {"level_up":13,"machine":32,"machine_archive":27} |
| [1101: パルキア](pokemon/1101.md) | {"level_up":12,"machine":35,"machine_archive":29} |
| [1102: ビビヨン](pokemon/1102.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":2} |
| [1103: ビビヨン](pokemon/1103.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":2} |
| [1104: ビビヨン](pokemon/1104.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":2} |
| [1105: ビビヨン](pokemon/1105.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":2} |
| [1106: ビビヨン](pokemon/1106.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":2} |
| [1107: ビビヨン](pokemon/1107.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":2} |
| [1108: ビビヨン](pokemon/1108.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":2} |
| [1109: ビビヨン](pokemon/1109.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":2} |
| [1110: ビビヨン](pokemon/1110.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":2} |
| [1111: ビビヨン](pokemon/1111.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":2} |
| [1112: ビビヨン](pokemon/1112.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":2} |
| [1113: ビビヨン](pokemon/1113.md) | {"egg":2,"level_up":13,"machine":19,"machine_archive":16} |
| [1114: ビビヨン](pokemon/1114.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":2} |
| [1115: ビビヨン](pokemon/1115.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":2} |
| [1116: ビビヨン](pokemon/1116.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":2} |
| [1117: ビビヨン](pokemon/1117.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":2} |
| [1118: ビビヨン](pokemon/1118.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":2} |
| [1119: ビビヨン](pokemon/1119.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":2} |
| [1120: モクロー](pokemon/1120.md) | {"egg":5,"level_up":14,"machine":25,"machine_archive":14,"shared_egg":5} |
| [1121: フクスロー](pokemon/1121.md) | {"build_learnable_preservation":2,"egg":2,"level_up":14,"machine":26,"machine_archive":15,"shared_egg":5} |
| [1122: ジュナイパー](pokemon/1122.md) | {"build_learnable_preservation":3,"egg":2,"level_up":19,"machine":31,"machine_archive":28,"shared_egg":5} |
| [1123: ニャビー](pokemon/1123.md) | {"egg":3,"level_up":14,"machine":19,"machine_archive":18,"shared_egg":3} |
| [1124: ニャヒート](pokemon/1124.md) | {"build_learnable_preservation":3,"egg":1,"level_up":14,"machine":19,"machine_archive":18,"shared_egg":3} |
| [1125: ガオガエン](pokemon/1125.md) | {"build_learnable_preservation":5,"egg":2,"level_up":15,"machine":36,"machine_archive":30,"move_memory_reminder":3,"shared_egg":3} |
| [1126: アシマリ](pokemon/1126.md) | {"egg":3,"level_up":14,"machine":19,"machine_archive":14,"shared_egg":3} |
| [1127: オシャマリ](pokemon/1127.md) | {"build_learnable_preservation":2,"egg":1,"level_up":14,"machine":19,"machine_archive":15,"shared_egg":3} |
| [1128: アシレーヌ](pokemon/1128.md) | {"build_learnable_preservation":2,"egg":2,"level_up":15,"machine":28,"machine_archive":25,"shared_egg":3} |
| [1129: ツツケラ](pokemon/1129.md) | {"egg":3,"level_up":13,"machine":22,"machine_archive":10,"shared_egg":3} |
| [1130: ケララッパ](pokemon/1130.md) | {"build_learnable_preservation":3,"egg":2,"level_up":13,"machine":22,"machine_archive":12,"move_memory_reminder":1,"shared_egg":3} |
| [1131: ドデカバシ](pokemon/1131.md) | {"build_learnable_preservation":2,"egg":2,"level_up":15,"machine":26,"machine_archive":19,"shared_egg":3} |
| [1132: ヤングース](pokemon/1132.md) | {"egg":5,"level_up":14,"machine":19,"machine_archive":17,"shared_egg":5} |
| [1133: デカグース](pokemon/1133.md) | {"build_learnable_preservation":1,"egg":1,"level_up":14,"machine":26,"machine_archive":24,"shared_egg":5} |
| [1134: アゴジムシ](pokemon/1134.md) | {"egg":2,"level_up":10,"machine":17,"machine_archive":13,"shared_egg":2} |
| [1135: デンヂムシ](pokemon/1135.md) | {"build_learnable_preservation":1,"egg":2,"level_up":13,"machine":18,"machine_archive":16,"shared_egg":2} |
| [1136: クワガノン](pokemon/1136.md) | {"build_learnable_preservation":2,"egg":2,"level_up":13,"machine":24,"machine_archive":23,"move_memory_reminder":6,"shared_egg":2} |
| [1137: マケンカニ](pokemon/1137.md) | {"egg":4,"level_up":13,"machine":27,"machine_archive":16,"shared_egg":4} |
| [1138: ケケンカニ](pokemon/1138.md) | {"build_learnable_preservation":5,"egg":2,"level_up":13,"machine":32,"machine_archive":22,"shared_egg":4} |
| [1139: オドリドリ](pokemon/1139.md) | {"egg":5,"level_up":15,"machine":21,"machine_archive":13,"shared_egg":5} |
| [1140: アブリー](pokemon/1140.md) | {"egg":3,"level_up":11,"machine":21,"machine_archive":18,"shared_egg":3} |
| [1141: アブリボン](pokemon/1141.md) | {"build_learnable_preservation":3,"egg":2,"level_up":12,"machine":23,"machine_archive":26,"shared_egg":3} |
| [1142: イワンコ](pokemon/1142.md) | {"egg":4,"level_up":14,"machine":21,"machine_archive":17,"shared_egg":4} |
| [1143: ルガルガン](pokemon/1143.md) | {"build_learnable_preservation":2,"egg":1,"level_up":18,"machine":24,"machine_archive":23,"shared_egg":4} |
| [1144: ヨワシ](pokemon/1144.md) | {"egg":3,"level_up":14,"machine":18,"machine_archive":11,"shared_egg":3,"tutor":2} |
| [1145: ヒドイデ](pokemon/1145.md) | {"egg":5,"level_up":12,"machine":22,"machine_archive":10,"shared_egg":5} |
| [1146: ドヒドイデ](pokemon/1146.md) | {"build_learnable_preservation":4,"egg":2,"level_up":13,"machine":22,"machine_archive":16,"shared_egg":5} |
| [1147: ドロバンコ](pokemon/1147.md) | {"egg":5,"level_up":13,"machine":17,"machine_archive":16,"shared_egg":5} |
| [1148: バンバドロ](pokemon/1148.md) | {"build_learnable_preservation":1,"egg":1,"level_up":13,"machine":19,"machine_archive":21,"shared_egg":5} |
| [1149: シズクモ](pokemon/1149.md) | {"egg":4,"level_up":14,"machine":19,"machine_archive":11,"shared_egg":4} |
| [1150: オニシズクモ](pokemon/1150.md) | {"build_learnable_preservation":4,"egg":2,"level_up":15,"machine":20,"machine_archive":15,"shared_egg":4} |
| [1151: カリキリ](pokemon/1151.md) | {"egg":3,"level_up":12,"machine":14,"machine_archive":15,"shared_egg":3} |
| [1152: ラランテス](pokemon/1152.md) | {"build_learnable_preservation":3,"egg":1,"level_up":15,"machine":19,"machine_archive":20,"shared_egg":3} |
| [1153: ネマシュ](pokemon/1153.md) | {"egg":4,"level_up":13,"machine":15,"machine_archive":10,"shared_egg":4} |
| [1154: マシェード](pokemon/1154.md) | {"build_learnable_preservation":4,"egg":2,"level_up":13,"machine":17,"machine_archive":13,"shared_egg":4} |
| [1155: ヤトウモリ](pokemon/1155.md) | {"egg":4,"level_up":13,"machine":27,"machine_archive":21,"shared_egg":4} |
| [1156: エンニュート](pokemon/1156.md) | {"build_learnable_preservation":3,"egg":2,"level_up":20,"machine":30,"machine_archive":29,"shared_egg":4} |
| [1157: ヌイコグマ](pokemon/1157.md) | {"egg":4,"level_up":14,"machine":18,"machine_archive":14,"shared_egg":4,"tutor":1} |
| [1158: キテルグマ](pokemon/1158.md) | {"build_learnable_preservation":4,"egg":2,"level_up":16,"machine":21,"machine_archive":24,"shared_egg":4,"tutor":1} |
| [1159: アマカジ](pokemon/1159.md) | {"egg":3,"level_up":9,"machine":17,"machine_archive":13,"shared_egg":3} |
| [1160: アママイコ](pokemon/1160.md) | {"build_learnable_preservation":1,"egg":1,"level_up":11,"machine":18,"machine_archive":16,"shared_egg":3} |
| [1161: アマージョ](pokemon/1161.md) | {"build_learnable_preservation":1,"egg":1,"level_up":15,"machine":22,"machine_archive":20,"shared_egg":3} |
| [1162: キュワワー](pokemon/1162.md) | {"egg":2,"level_up":18,"machine":24,"machine_archive":21,"shared_egg":2} |
| [1163: ヤレユータン](pokemon/1163.md) | {"egg":4,"level_up":14,"machine":28,"machine_archive":26,"shared_egg":4} |
| [1164: ナゲツケサル](pokemon/1164.md) | {"egg":6,"level_up":14,"machine":31,"machine_archive":21,"shared_egg":6} |
| [1165: コソクムシ](pokemon/1165.md) | {"egg":5,"level_up":3,"machine":11,"machine_archive":11,"shared_egg":5,"tutor_archive":1} |
| [1166: グソクムシャ](pokemon/1166.md) | {"build_learnable_preservation":5,"egg":2,"level_up":17,"machine":31,"machine_archive":23,"shared_egg":5,"tutor_archive":1} |
| [1167: スナバァ](pokemon/1167.md) | {"egg":6,"level_up":14,"machine":25,"machine_archive":18,"shared_egg":6} |
| [1168: シロデスナ](pokemon/1168.md) | {"build_learnable_preservation":4,"egg":2,"level_up":14,"machine":25,"machine_archive":21,"shared_egg":6} |
| [1169: ナマコブシ](pokemon/1169.md) | {"egg":4,"level_up":14,"machine":11,"machine_archive":5,"shared_egg":4} |
| [1170: タイプ:ヌル](pokemon/1170.md) | {"level_up":13,"machine":18,"machine_archive":13,"tutor":1} |
| [1171: シルヴァディ](pokemon/1171.md) | {"level_up":23,"machine":27,"machine_archive":23,"tutor":3,"tutor_archive":1} |
| [1172: メテノ](pokemon/1172.md) | {"egg":2,"level_up":15,"machine":21,"machine_archive":18} |
| [1173: ネッコアラ](pokemon/1173.md) | {"egg":5,"level_up":13,"machine":26,"machine_archive":18,"shared_egg":5} |
| [1174: バクガメス](pokemon/1174.md) | {"egg":4,"level_up":15,"machine":23,"machine_archive":25,"shared_egg":4,"tutor":5} |
| [1175: トゲデマル](pokemon/1175.md) | {"egg":6,"level_up":14,"machine":18,"machine_archive":22,"shared_egg":6,"tutor":2,"tutor_archive":1} |
| [1176: ミミッキュ](pokemon/1176.md) | {"egg":2,"level_up":15,"machine":29,"machine_archive":19,"shared_egg":2} |
| [1177: ハギギシリ](pokemon/1177.md) | {"egg":4,"level_up":12,"machine":24,"machine_archive":18,"shared_egg":4} |
| [1178: ジジーロン](pokemon/1178.md) | {"egg":3,"level_up":13,"machine":31,"machine_archive":24,"shared_egg":3,"tutor":3} |
| [1179: ダダリン](pokemon/1179.md) | {"egg":2,"level_up":18,"machine":27,"machine_archive":18,"tutor":2,"tutor_archive":1} |
| [1180: ジャラコ](pokemon/1180.md) | {"egg":3,"level_up":13,"machine":22,"machine_archive":16,"shared_egg":3} |
| [1181: ジャランゴ](pokemon/1181.md) | {"build_learnable_preservation":2,"egg":2,"level_up":14,"machine":25,"machine_archive":24,"shared_egg":3} |
| [1182: ジャラランガ](pokemon/1182.md) | {"build_learnable_preservation":3,"egg":2,"level_up":17,"machine":37,"machine_archive":29,"move_memory_reminder":1,"shared_egg":3} |
| [1183: カプ・コケコ](pokemon/1183.md) | {"level_up":17,"machine":24,"machine_archive":21} |
| [1184: カプ・テテフ](pokemon/1184.md) | {"level_up":17,"machine":20,"machine_archive":21} |
| [1185: カプ・ブルル](pokemon/1185.md) | {"level_up":17,"machine":25,"machine_archive":26} |
| [1186: カプ・レヒレ](pokemon/1186.md) | {"level_up":18,"machine":23,"machine_archive":19} |
| [1187: コスモッグ](pokemon/1187.md) | {"level_up":2} |
| [1188: コスモウム](pokemon/1188.md) | {"build_learnable_preservation":1,"level_up":2} |
| [1189: ソルガレオ](pokemon/1189.md) | {"build_learnable_preservation":1,"level_up":17,"machine":27,"machine_archive":34} |
| [1190: ルナアーラ](pokemon/1190.md) | {"build_learnable_preservation":1,"level_up":16,"machine":30,"machine_archive":21} |
| [1191: ウツロイド](pokemon/1191.md) | {"egg":2,"level_up":17,"machine":23,"machine_archive":15,"tutor":2} |
| [1192: マッシブーン](pokemon/1192.md) | {"egg":2,"level_up":16,"machine":20,"machine_archive":21,"tutor":2} |
| [1193: フェローチェ](pokemon/1193.md) | {"egg":2,"level_up":16,"machine":17,"machine_archive":17,"tutor":2,"tutor_archive":1} |
| [1194: デンジュモク](pokemon/1194.md) | {"egg":1,"level_up":16,"machine":17,"machine_archive":15,"tutor":1} |
| [1195: テッカグヤ](pokemon/1195.md) | {"egg":2,"level_up":16,"machine":23,"machine_archive":14,"tutor":2,"tutor_archive":1} |
| [1196: カミツルギ](pokemon/1196.md) | {"egg":2,"level_up":16,"machine":12,"machine_archive":9,"tutor":1} |
| [1197: アクジキング](pokemon/1197.md) | {"egg":2,"level_up":17,"machine":27,"machine_archive":20,"tutor":3,"tutor_archive":1} |
| [1198: ネクロズマ](pokemon/1198.md) | {"level_up":16,"machine":32,"machine_archive":26} |
| [1199: マギアナ](pokemon/1199.md) | {"level_up":17,"machine":37,"machine_archive":27} |
| [1200: マーシャドー](pokemon/1200.md) | {"level_up":18,"machine":27,"machine_archive":26,"tutor":2,"tutor_archive":1} |
| [1201: コラッタ](pokemon/1201.md) | {"egg":11,"level_up":13,"machine":16,"machine_archive":14,"tutor":7,"tutor_archive":4} |
| [1202: ラッタ](pokemon/1202.md) | {"build_learnable_preservation":9,"egg":1,"level_up":18,"machine":20,"machine_archive":17,"tutor":9,"tutor_archive":5} |
| [1203: ライチュウ](pokemon/1203.md) | {"build_learnable_preservation":6,"egg":1,"level_up":21,"machine":27,"machine_archive":30,"shared_egg":7} |
| [1204: サンド](pokemon/1204.md) | {"egg":8,"level_up":17,"machine":26,"machine_archive":23,"shared_egg":8} |
| [1205: サンドパン](pokemon/1205.md) | {"build_learnable_preservation":16,"egg":1,"level_up":5,"machine":29,"machine_archive":27,"move_memory_reminder":15,"shared_egg":8} |
| [1206: ロコン](pokemon/1206.md) | {"egg":6,"level_up":15,"machine":19,"machine_archive":24,"shared_egg":6} |
| [1207: キュウコン](pokemon/1207.md) | {"build_learnable_preservation":13,"egg":1,"level_up":5,"machine":20,"machine_archive":29,"move_memory_reminder":12,"shared_egg":6} |
| [1208: ディグダ](pokemon/1208.md) | {"egg":7,"level_up":13,"machine":23,"machine_archive":19,"shared_egg":7} |
| [1209: ダグトリオ](pokemon/1209.md) | {"build_learnable_preservation":6,"egg":1,"level_up":16,"machine":25,"machine_archive":25,"shared_egg":7} |
| [1210: ニャース](pokemon/1210.md) | {"egg":6,"level_up":13,"machine":29,"machine_archive":20,"shared_egg":6} |
| [1211: ペルシアン](pokemon/1211.md) | {"build_learnable_preservation":5,"egg":1,"level_up":16,"machine":30,"machine_archive":25,"shared_egg":6} |
| [1212: イシツブテ](pokemon/1212.md) | {"egg":8,"level_up":16,"machine":23,"machine_archive":21,"shared_egg":8} |
| [1213: ゴローン](pokemon/1213.md) | {"build_learnable_preservation":6,"egg":2,"level_up":16,"machine":25,"machine_archive":25,"shared_egg":8} |
| [1214: ゴローニャ](pokemon/1214.md) | {"build_learnable_preservation":8,"egg":2,"level_up":16,"machine":27,"machine_archive":29,"shared_egg":8} |
| [1215: ベトベター](pokemon/1215.md) | {"egg":10,"level_up":16,"machine":31,"machine_archive":24,"shared_egg":10} |
| [1216: ベトベトン](pokemon/1216.md) | {"build_learnable_preservation":8,"egg":1,"level_up":16,"machine":33,"machine_archive":26,"shared_egg":10} |
| [1217: タマタマ](pokemon/1217.md) | {"egg":8,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":8} |
| [1218: ナッシー](pokemon/1218.md) | {"build_learnable_preservation":8,"egg":2,"level_up":18,"machine":30,"machine_archive":30,"move_memory_reminder":1,"shared_egg":8} |
| [1219: カラカラ](pokemon/1219.md) | {"egg":8,"level_up":14,"machine":24,"machine_archive":20,"shared_egg":8,"tutor":1} |
| [1220: ガラガラ](pokemon/1220.md) | {"build_learnable_preservation":8,"egg":1,"level_up":20,"machine":33,"machine_archive":28,"shared_egg":8,"tutor":3} |
| [1221: デオキシス](pokemon/1221.md) | {"build_learnable_preservation":8,"level_up":14,"machine":37,"machine_archive":31} |
| [1222: デオキシス](pokemon/1222.md) | {"build_learnable_preservation":6,"level_up":16,"machine":40,"machine_archive":30} |
| [1223: デオキシス](pokemon/1223.md) | {"build_learnable_preservation":8,"level_up":14,"machine":38,"machine_archive":31} |
| [1224: オドリドリ](pokemon/1224.md) | {"egg":5,"level_up":15,"machine":21,"machine_archive":13,"shared_egg":5} |
| [1225: オドリドリ](pokemon/1225.md) | {"egg":5,"level_up":15,"machine":21,"machine_archive":13,"shared_egg":5} |
| [1226: オドリドリ](pokemon/1226.md) | {"egg":5,"level_up":15,"machine":21,"machine_archive":13,"shared_egg":5} |
| [1227: ルガルガン](pokemon/1227.md) | {"build_learnable_preservation":3,"egg":1,"level_up":18,"machine":31,"machine_archive":26,"shared_egg":4} |
| [1228: ヨワシ](pokemon/1228.md) | {"egg":3,"level_up":14,"machine":18,"machine_archive":11,"shared_egg":3,"tutor":2} |
| [1229: シルヴァディ](pokemon/1229.md) | {"level_up":23,"machine":27,"machine_archive":23,"tutor":3,"tutor_archive":1} |
| [1230: シルヴァディ](pokemon/1230.md) | {"level_up":23,"machine":27,"machine_archive":23,"tutor":3,"tutor_archive":1} |
| [1231: シルヴァディ](pokemon/1231.md) | {"level_up":23,"machine":27,"machine_archive":23,"tutor":3,"tutor_archive":1} |
| [1232: シルヴァディ](pokemon/1232.md) | {"level_up":23,"machine":27,"machine_archive":23,"tutor":3,"tutor_archive":1} |
| [1233: シルヴァディ](pokemon/1233.md) | {"level_up":23,"machine":27,"machine_archive":23,"tutor":3,"tutor_archive":1} |
| [1234: シルヴァディ](pokemon/1234.md) | {"level_up":23,"machine":27,"machine_archive":23,"tutor":3,"tutor_archive":1} |
| [1235: シルヴァディ](pokemon/1235.md) | {"level_up":23,"machine":27,"machine_archive":23,"tutor":3,"tutor_archive":1} |
| [1236: シルヴァディ](pokemon/1236.md) | {"level_up":23,"machine":27,"machine_archive":23,"tutor":3,"tutor_archive":1} |
| [1237: シルヴァディ](pokemon/1237.md) | {"level_up":23,"machine":27,"machine_archive":23,"tutor":3,"tutor_archive":1} |
| [1238: シルヴァディ](pokemon/1238.md) | {"level_up":23,"machine":27,"machine_archive":23,"tutor":3,"tutor_archive":1} |
| [1239: シルヴァディ](pokemon/1239.md) | {"level_up":23,"machine":27,"machine_archive":23,"tutor":3,"tutor_archive":1} |
| [1240: シルヴァディ](pokemon/1240.md) | {"level_up":23,"machine":27,"machine_archive":23,"tutor":3,"tutor_archive":1} |
| [1241: シルヴァディ](pokemon/1241.md) | {"level_up":23,"machine":27,"machine_archive":23,"tutor":3,"tutor_archive":1} |
| [1242: シルヴァディ](pokemon/1242.md) | {"level_up":23,"machine":27,"machine_archive":23,"tutor":3,"tutor_archive":1} |
| [1243: シルヴァディ](pokemon/1243.md) | {"level_up":23,"machine":27,"machine_archive":23,"tutor":3,"tutor_archive":1} |
| [1244: シルヴァディ](pokemon/1244.md) | {"level_up":23,"machine":27,"machine_archive":23,"tutor":3,"tutor_archive":1} |
| [1245: シルヴァディ](pokemon/1245.md) | {"level_up":23,"machine":27,"machine_archive":23,"tutor":3,"tutor_archive":1} |
| [1246: メテノ](pokemon/1246.md) | {"egg":2,"level_up":15,"machine":21,"machine_archive":18} |
| [1247: メテノ](pokemon/1247.md) | {"egg":2,"level_up":15,"machine":21,"machine_archive":18} |
| [1248: メテノ](pokemon/1248.md) | {"egg":2,"level_up":15,"machine":21,"machine_archive":18} |
| [1249: メテノ](pokemon/1249.md) | {"egg":2,"level_up":15,"machine":21,"machine_archive":18} |
| [1250: メテノ](pokemon/1250.md) | {"egg":2,"level_up":15,"machine":21,"machine_archive":18} |
| [1251: メテノ](pokemon/1251.md) | {"egg":2,"level_up":15,"machine":21,"machine_archive":18} |
| [1252: メテノ](pokemon/1252.md) | {"egg":2,"level_up":15,"machine":21,"machine_archive":18} |
| [1253: ミミッキュ](pokemon/1253.md) | {"egg":5,"level_up":15,"machine":29,"machine_archive":19,"shared_egg":2} |
| [1254: マギアナ](pokemon/1254.md) | {"level_up":17,"machine":37,"machine_archive":27} |
| [1255: ベベノム](pokemon/1255.md) | {"egg":1,"level_up":14,"machine":13,"machine_archive":9} |
| [1256: アーゴヨン](pokemon/1256.md) | {"egg":2,"level_up":18,"machine":28,"machine_archive":21,"tutor":3} |
| [1257: ツンデツンデ](pokemon/1257.md) | {"egg":2,"level_up":16,"machine":19,"machine_archive":19,"tutor":2,"tutor_archive":1} |
| [1258: ズガドーン](pokemon/1258.md) | {"egg":2,"level_up":16,"machine":20,"machine_archive":18,"tutor":1} |
| [1259: ゼラオラ](pokemon/1259.md) | {"level_up":18,"machine":26,"machine_archive":28,"tutor":2} |
| [1260: ネクロズマ](pokemon/1260.md) | {"build_learnable_preservation":1,"level_up":16,"machine":32,"machine_archive":26} |
| [1261: ネクロズマ](pokemon/1261.md) | {"build_learnable_preservation":1,"level_up":16,"machine":32,"machine_archive":26} |
| [1262: ネクロズマ](pokemon/1262.md) | {"build_learnable_preservation":2,"level_up":19,"machine":22,"machine_archive":21,"tutor":8,"tutor_archive":8} |
| [1263: ルガルガン](pokemon/1263.md) | {"build_learnable_preservation":2,"egg":1,"level_up":23,"machine":24,"machine_archive":23,"shared_egg":4} |
| [1264: メルタン](pokemon/1264.md) | {"level_up":7,"machine":9,"machine_archive":4,"tutor":1} |
| [1265: メルメタル](pokemon/1265.md) | {"level_up":16,"machine":17,"machine_archive":19,"tutor":1,"tutor_archive":1} |
| [1266: ピカチュウ](pokemon/1266.md) | {"build_learnable_preservation":1,"level_up":20,"machine":24,"machine_archive":23,"shared_egg":7} |
| [1267: ピカチュウ](pokemon/1267.md) | {"build_learnable_preservation":1,"level_up":20,"machine":24,"machine_archive":23,"shared_egg":7} |
| [1268: ピカチュウ](pokemon/1268.md) | {"egg":1,"level_up":15,"machine":42,"tutor":30} |
| [1269: ピカチュウ](pokemon/1269.md) | {"egg":1,"level_up":15,"machine":42,"tutor":30} |
| [1270: ピカチュウ](pokemon/1270.md) | {"egg":1,"level_up":15,"machine":42,"tutor":30} |
| [1271: ピカチュウ](pokemon/1271.md) | {"egg":1,"level_up":15,"machine":42,"tutor":30} |
| [1272: ピカチュウ](pokemon/1272.md) | {"egg":1,"level_up":15,"machine":42,"tutor":30} |
| [1273: ピカチュウ](pokemon/1273.md) | {"egg":1,"level_up":15,"machine":42,"tutor":30} |
| [1274: ピカチュウ](pokemon/1274.md) | {"egg":1,"level_up":20,"machine":24,"machine_archive":23,"shared_egg":7} |
| [1275: ピカチュウ](pokemon/1275.md) | {"egg":1,"level_up":20,"machine":24,"machine_archive":23,"shared_egg":7} |
| [1276: ピカチュウ](pokemon/1276.md) | {"egg":1,"level_up":20,"machine":24,"machine_archive":23,"shared_egg":7} |
| [1277: ピカチュウ](pokemon/1277.md) | {"egg":1,"level_up":20,"machine":24,"machine_archive":23,"shared_egg":7} |
| [1278: ピカチュウ](pokemon/1278.md) | {"egg":1,"level_up":20,"machine":24,"machine_archive":23,"shared_egg":7} |
| [1279: ピカチュウ](pokemon/1279.md) | {"egg":1,"level_up":20,"machine":24,"machine_archive":23,"shared_egg":7} |
| [1280: ピカチュウ](pokemon/1280.md) | {"egg":1,"level_up":20,"machine":24,"machine_archive":23,"shared_egg":7} |
| [1281: ピチュー](pokemon/1281.md) | {"level_up":6,"machine":31,"tutor":5} |
| [1282: ゼルネアス](pokemon/1282.md) | {"level_up":18,"tutor":5} |
| [1283: サルノリ](pokemon/1283.md) | {"egg":6,"level_up":11,"machine":20,"machine_archive":16,"shared_egg":6} |
| [1284: バチンキー](pokemon/1284.md) | {"build_learnable_preservation":6,"egg":1,"level_up":12,"machine":20,"machine_archive":18,"shared_egg":6} |
| [1285: ゴリランダー](pokemon/1285.md) | {"build_learnable_preservation":6,"egg":1,"level_up":16,"machine":29,"machine_archive":26,"shared_egg":6} |
| [1286: ヒバニー](pokemon/1286.md) | {"egg":4,"level_up":11,"machine":19,"machine_archive":16,"shared_egg":4} |
| [1287: ラビフット](pokemon/1287.md) | {"build_learnable_preservation":3,"egg":1,"level_up":11,"machine":21,"machine_archive":18,"shared_egg":4} |
| [1288: エースバーン](pokemon/1288.md) | {"build_learnable_preservation":3,"egg":1,"level_up":14,"machine":27,"machine_archive":27,"shared_egg":4} |
| [1289: メッソン](pokemon/1289.md) | {"egg":7,"level_up":11,"machine":15,"machine_archive":10,"shared_egg":7} |
| [1290: ジメレオン](pokemon/1290.md) | {"build_learnable_preservation":5,"egg":1,"level_up":11,"machine":16,"machine_archive":11,"shared_egg":7} |
| [1291: インテレオン](pokemon/1291.md) | {"build_learnable_preservation":5,"egg":1,"level_up":14,"machine":28,"machine_archive":23,"shared_egg":7} |
| [1292: ホシガリス](pokemon/1292.md) | {"egg":4,"level_up":13,"machine":10,"machine_archive":15,"shared_egg":4} |
| [1293: ヨクバリス](pokemon/1293.md) | {"build_learnable_preservation":4,"egg":1,"level_up":14,"machine":19,"machine_archive":22,"shared_egg":4} |
| [1294: ココガラ](pokemon/1294.md) | {"egg":7,"level_up":11,"machine":13,"machine_archive":12,"shared_egg":7} |
| [1295: アオガラス](pokemon/1295.md) | {"build_learnable_preservation":4,"egg":1,"level_up":11,"machine":14,"machine_archive":13,"shared_egg":7} |
| [1296: アーマーガア](pokemon/1296.md) | {"build_learnable_preservation":4,"egg":2,"level_up":15,"machine":22,"machine_archive":22,"shared_egg":7} |
| [1297: サッチムシ](pokemon/1297.md) | {"egg":4,"level_up":1,"shared_egg":4} |
| [1298: レドームシ](pokemon/1298.md) | {"build_learnable_preservation":4,"egg":2,"level_up":7,"machine":15,"machine_archive":21,"shared_egg":4,"tutor":1} |
| [1299: イオルブ](pokemon/1299.md) | {"build_learnable_preservation":4,"egg":2,"level_up":15,"machine":18,"machine_archive":25,"shared_egg":4,"tutor":1} |
| [1300: クスネ](pokemon/1300.md) | {"egg":4,"level_up":11,"machine":11,"machine_archive":14,"shared_egg":4,"tutor":1} |
| [1301: フォクスライ](pokemon/1301.md) | {"build_learnable_preservation":4,"egg":1,"level_up":14,"machine":18,"machine_archive":20,"shared_egg":4,"tutor":2} |
| [1302: ヒメンカ](pokemon/1302.md) | {"egg":6,"level_up":11,"machine":11,"machine_archive":12,"shared_egg":6,"tutor":1} |
| [1303: ワタシラガ](pokemon/1303.md) | {"build_learnable_preservation":6,"egg":1,"level_up":14,"machine":12,"machine_archive":15,"shared_egg":6,"tutor":1} |
| [1304: ウールー](pokemon/1304.md) | {"egg":3,"level_up":12,"machine":6,"machine_archive":10,"shared_egg":3,"tutor":1} |
| [1305: バイウールー](pokemon/1305.md) | {"build_learnable_preservation":3,"egg":1,"level_up":13,"machine":9,"machine_archive":17,"shared_egg":3,"tutor":1} |
| [1306: カムカメ](pokemon/1306.md) | {"egg":3,"level_up":9,"machine":14,"machine_archive":12,"shared_egg":3} |
| [1307: カジリガメ](pokemon/1307.md) | {"build_learnable_preservation":2,"egg":2,"level_up":14,"machine":27,"machine_archive":25,"shared_egg":3} |
| [1308: ワンパチ](pokemon/1308.md) | {"egg":5,"level_up":11,"machine":11,"machine_archive":14,"shared_egg":5,"tutor":1} |
| [1309: パルスワン](pokemon/1309.md) | {"build_learnable_preservation":5,"egg":1,"level_up":13,"machine":13,"machine_archive":21,"shared_egg":5,"tutor":1} |
| [1310: タンドン](pokemon/1310.md) | {"egg":3,"level_up":10,"machine":16,"machine_archive":15,"shared_egg":3} |
| [1311: トロッゴン](pokemon/1311.md) | {"build_learnable_preservation":2,"egg":2,"level_up":12,"machine":22,"machine_archive":21,"shared_egg":3} |
| [1312: セキタンザン](pokemon/1312.md) | {"build_learnable_preservation":2,"egg":2,"level_up":13,"machine":24,"machine_archive":26,"shared_egg":3} |
| [1313: カジッチュ](pokemon/1313.md) | {"egg":4,"level_up":2,"machine":2,"shared_egg":4} |
| [1314: アップリュー](pokemon/1314.md) | {"build_learnable_preservation":3,"egg":2,"level_up":17,"machine":20,"machine_archive":18,"shared_egg":4} |
| [1315: タルップル](pokemon/1315.md) | {"build_learnable_preservation":3,"egg":2,"level_up":17,"machine":25,"machine_archive":19,"shared_egg":4} |
| [1316: スナヘビ](pokemon/1316.md) | {"egg":5,"level_up":12,"machine":13,"machine_archive":15,"shared_egg":5} |
| [1317: サダイジャ](pokemon/1317.md) | {"build_learnable_preservation":3,"egg":1,"level_up":12,"machine":16,"machine_archive":24,"shared_egg":5} |
| [1318: ウッウ](pokemon/1318.md) | {"build_learnable_preservation":1,"egg":6,"level_up":12,"machine":22,"machine_archive":17,"move_memory_reminder":1,"shared_egg":6} |
| [1319: サシカマス](pokemon/1319.md) | {"egg":4,"level_up":10,"machine":16,"machine_archive":12,"shared_egg":4} |
| [1320: カマスジョー](pokemon/1320.md) | {"build_learnable_preservation":4,"egg":1,"level_up":11,"machine":18,"machine_archive":16,"shared_egg":4} |
| [1321: エレズン](pokemon/1321.md) | {"egg":2,"level_up":6,"machine":7,"machine_archive":4,"shared_egg":2} |
| [1322: ストリンダー](pokemon/1322.md) | {"egg":2,"level_up":23,"machine":29,"machine_archive":27,"shared_egg":2} |
| [1323: ヤクデ](pokemon/1323.md) | {"egg":4,"level_up":13,"machine":9,"machine_archive":11,"shared_egg":4,"tutor":1,"tutor_archive":1} |
| [1324: マルヤクデ](pokemon/1324.md) | {"build_learnable_preservation":4,"egg":2,"level_up":14,"machine":11,"machine_archive":21,"shared_egg":4,"tutor":1,"tutor_archive":1} |
| [1325: タタッコ](pokemon/1325.md) | {"egg":6,"level_up":11,"machine":14,"machine_archive":15,"shared_egg":6,"tutor":1} |
| [1326: オトスパス](pokemon/1326.md) | {"build_learnable_preservation":6,"egg":1,"level_up":15,"machine":17,"machine_archive":22,"shared_egg":6,"tutor":1,"tutor_archive":1} |
| [1327: ヤバチャ](pokemon/1327.md) | {"egg":1,"level_up":11,"machine":17,"machine_archive":15} |
| [1328: ポットデス](pokemon/1328.md) | {"egg":1,"level_up":15,"machine":19,"machine_archive":18} |
| [1329: ミブリム](pokemon/1329.md) | {"egg":4,"level_up":11,"machine":18,"machine_archive":18,"shared_egg":4} |
| [1330: テブリム](pokemon/1330.md) | {"build_learnable_preservation":4,"egg":1,"level_up":12,"machine":18,"machine_archive":18,"shared_egg":4} |
| [1331: ブリムオン](pokemon/1331.md) | {"build_learnable_preservation":4,"egg":2,"level_up":14,"machine":21,"machine_archive":25,"shared_egg":4} |
| [1332: ベロバー](pokemon/1332.md) | {"egg":1,"level_up":13,"machine":20,"machine_archive":13,"shared_egg":1} |
| [1333: ギモー](pokemon/1333.md) | {"build_learnable_preservation":1,"egg":2,"level_up":14,"machine":21,"machine_archive":14,"shared_egg":1} |
| [1334: オーロンゲ](pokemon/1334.md) | {"build_learnable_preservation":1,"egg":2,"level_up":17,"machine":30,"machine_archive":19,"shared_egg":1} |
| [1335: タチフサグマ](pokemon/1335.md) | {"build_learnable_preservation":3,"egg":2,"level_up":22,"machine":31,"machine_archive":33,"shared_egg":3,"tutor":1} |
| [1336: ニャイキング](pokemon/1336.md) | {"build_learnable_preservation":3,"egg":1,"level_up":16,"machine":33,"machine_archive":27,"shared_egg":6} |
| [1337: サニゴーン](pokemon/1337.md) | {"build_learnable_preservation":5,"egg":1,"level_up":14,"machine":29,"machine_archive":25,"shared_egg":6,"tutor":3} |
| [1338: ネギガナイト](pokemon/1338.md) | {"build_learnable_preservation":11,"egg":1,"level_up":19,"machine":13,"machine_archive":16,"shared_egg":11,"tutor":3} |
| [1339: バリコオル](pokemon/1339.md) | {"build_learnable_preservation":4,"egg":2,"level_up":29,"machine":32,"machine_archive":36,"shared_egg":4,"tutor":2} |
| [1340: デスバーン](pokemon/1340.md) | {"build_learnable_preservation":1,"egg":2,"level_up":19,"machine":26,"machine_archive":28,"shared_egg":1,"tutor":1} |
| [1341: マホミル](pokemon/1341.md) | {"egg":2,"level_up":12,"machine":8,"machine_archive":5,"shared_egg":2} |
| [1342: マホイップ](pokemon/1342.md) | {"build_learnable_preservation":2,"egg":1,"level_up":13,"machine":16,"machine_archive":20,"shared_egg":2} |
| [1343: タイレーツ](pokemon/1343.md) | {"egg":1,"level_up":14,"machine":24,"machine_archive":16} |
| [1344: バチンウニ](pokemon/1344.md) | {"egg":2,"level_up":14,"machine":19,"machine_archive":19,"shared_egg":2} |
| [1345: ユキハミ](pokemon/1345.md) | {"egg":3,"level_up":2,"machine":8,"machine_archive":6,"shared_egg":3} |
| [1346: モスノウ](pokemon/1346.md) | {"build_learnable_preservation":2,"egg":2,"level_up":18,"machine":22,"machine_archive":19,"shared_egg":3} |
| [1347: イシヘンジン](pokemon/1347.md) | {"egg":2,"level_up":13,"machine":17,"machine_archive":22,"shared_egg":2} |
| [1348: コオリッポ](pokemon/1348.md) | {"egg":6,"level_up":12,"machine":22,"machine_archive":16,"shared_egg":6} |
| [1349: イエッサン](pokemon/1349.md) | {"egg":3,"level_up":13,"machine":16,"machine_archive":21,"shared_egg":3} |
| [1350: モルペコ](pokemon/1350.md) | {"egg":8,"level_up":14,"machine":23,"machine_archive":27,"shared_egg":8} |
| [1351: ゾウドウ](pokemon/1351.md) | {"egg":8,"level_up":13,"machine":19,"machine_archive":16,"shared_egg":8} |
| [1352: ダイオウドウ](pokemon/1352.md) | {"build_learnable_preservation":6,"egg":1,"level_up":14,"machine":22,"machine_archive":23,"shared_egg":8} |
| [1353: パッチラゴン](pokemon/1353.md) | {"egg":2,"level_up":13,"machine":20,"machine_archive":23,"tutor":3} |
| [1354: パッチルドン](pokemon/1354.md) | {"egg":2,"level_up":13,"machine":18,"machine_archive":23,"tutor":2} |
| [1355: ウオノラゴン](pokemon/1355.md) | {"egg":2,"level_up":13,"machine":20,"machine_archive":19,"tutor":2} |
| [1356: ウオチルドン](pokemon/1356.md) | {"egg":2,"level_up":13,"machine":18,"machine_archive":17,"tutor":1} |
| [1357: ジュラルドン](pokemon/1357.md) | {"egg":3,"level_up":13,"machine":24,"machine_archive":21,"shared_egg":3} |
| [1358: ドラメシヤ](pokemon/1358.md) | {"egg":6,"level_up":4,"machine":10,"machine_archive":5,"shared_egg":6} |
| [1359: ドロンチ](pokemon/1359.md) | {"build_learnable_preservation":3,"egg":2,"level_up":17,"machine":25,"machine_archive":17,"shared_egg":6} |
| [1360: ドラパルト](pokemon/1360.md) | {"build_learnable_preservation":3,"egg":2,"level_up":18,"machine":26,"machine_archive":22,"shared_egg":6} |
| [1361: ザシアン](pokemon/1361.md) | {"level_up":14,"machine":21,"machine_archive":22} |
| [1362: ザマゼンタ](pokemon/1362.md) | {"level_up":13,"machine":24,"machine_archive":24} |
| [1363: ムゲンダイナ](pokemon/1363.md) | {"level_up":15,"machine":21,"machine_archive":19} |
| [1364: ダクマ](pokemon/1364.md) | {"level_up":15,"machine":17,"machine_archive":14} |
| [1365: ウーラオス](pokemon/1365.md) | {"level_up":17,"machine":32,"machine_archive":21} |
| [1366: ザルード](pokemon/1366.md) | {"level_up":17,"machine":29,"machine_archive":29} |
| [1367: レジエレキ](pokemon/1367.md) | {"level_up":15,"machine":15,"machine_archive":14} |
| [1368: レジドラゴ](pokemon/1368.md) | {"level_up":14,"machine":12,"machine_archive":17} |
| [1369: ブリザポス](pokemon/1369.md) | {"level_up":14,"machine":19,"machine_archive":19} |
| [1370: レイスポス](pokemon/1370.md) | {"level_up":14,"machine":18,"machine_archive":20} |
| [1371: バドレックス](pokemon/1371.md) | {"level_up":16,"machine":21,"machine_archive":29} |
| [1372: ウッウ](pokemon/1372.md) | {"egg":5,"level_up":17,"machine":29,"tutor":6} |
| [1373: ウッウ](pokemon/1373.md) | {"egg":5,"level_up":17,"machine":29,"tutor":6} |
| [1374: ストリンダー](pokemon/1374.md) | {"egg":2,"level_up":23,"machine":29,"machine_archive":27,"shared_egg":2} |
| [1375: ヤバチャ](pokemon/1375.md) | {"egg":1,"level_up":11,"machine":17,"machine_archive":15} |
| [1376: ポットデス](pokemon/1376.md) | {"egg":1,"level_up":15,"machine":19,"machine_archive":18} |
| [1377: マホイップ](pokemon/1377.md) | {"build_learnable_preservation":2,"egg":1,"level_up":13,"machine":16,"machine_archive":20,"shared_egg":2} |
| [1378: マホイップ](pokemon/1378.md) | {"build_learnable_preservation":2,"egg":1,"level_up":13,"machine":16,"machine_archive":20,"shared_egg":2} |
| [1379: マホイップ](pokemon/1379.md) | {"build_learnable_preservation":2,"egg":1,"level_up":13,"machine":16,"machine_archive":20,"shared_egg":2} |
| [1380: マホイップ](pokemon/1380.md) | {"build_learnable_preservation":2,"egg":1,"level_up":13,"machine":16,"machine_archive":20,"shared_egg":2} |
| [1381: マホイップ](pokemon/1381.md) | {"build_learnable_preservation":2,"egg":1,"level_up":13,"machine":16,"machine_archive":20,"shared_egg":2} |
| [1382: マホイップ](pokemon/1382.md) | {"build_learnable_preservation":2,"egg":1,"level_up":13,"machine":16,"machine_archive":20,"shared_egg":2} |
| [1383: コオリッポ](pokemon/1383.md) | {"egg":7,"level_up":13,"machine":28,"tutor":12} |
| [1384: イエッサン](pokemon/1384.md) | {"egg":3,"level_up":12,"machine":18,"machine_archive":20,"shared_egg":3} |
| [1385: モルペコ](pokemon/1385.md) | {"egg":9,"level_up":17,"machine":33,"tutor":5} |
| [1386: ザシアン](pokemon/1386.md) | {"build_learnable_preservation":1,"level_up":14,"machine":21,"machine_archive":22} |
| [1387: ザマゼンタ](pokemon/1387.md) | {"build_learnable_preservation":1,"level_up":13,"machine":24,"machine_archive":24} |
| [1388: ムゲンダイナ](pokemon/1388.md) | {"level_up":18,"tutor":6} |
| [1389: ウーラオス](pokemon/1389.md) | {"build_learnable_preservation":1,"level_up":17,"machine":33,"machine_archive":18} |
| [1390: ザルード](pokemon/1390.md) | {"level_up":17,"machine":29,"machine_archive":29} |
| [1391: バドレックス](pokemon/1391.md) | {"level_up":31,"machine":32,"machine_archive":42} |
| [1392: バドレックス](pokemon/1392.md) | {"build_learnable_preservation":1,"level_up":31,"machine":29,"machine_archive":39} |
| [1393: ニャース](pokemon/1393.md) | {"egg":6,"level_up":13,"machine":31,"machine_archive":23,"shared_egg":6} |
| [1394: ポニータ](pokemon/1394.md) | {"egg":6,"level_up":13,"machine":9,"machine_archive":18,"shared_egg":6,"tutor":1} |
| [1395: ギャロップ](pokemon/1395.md) | {"build_learnable_preservation":6,"egg":1,"level_up":17,"machine":15,"machine_archive":27,"shared_egg":6,"tutor":1} |
| [1396: ヤドン](pokemon/1396.md) | {"egg":4,"level_up":17,"machine":28,"machine_archive":24,"shared_egg":4} |
| [1397: ヤドラン](pokemon/1397.md) | {"build_learnable_preservation":4,"egg":2,"level_up":19,"machine":41,"machine_archive":38,"shared_egg":4} |
| [1398: カモネギ](pokemon/1398.md) | {"egg":11,"level_up":15,"machine":12,"machine_archive":16,"shared_egg":11,"tutor":1} |
| [1399: ドガース](pokemon/1399.md) | {"egg":6,"level_up":15,"machine":20,"machine_archive":14,"shared_egg":6} |
| [1400: マタドガス](pokemon/1400.md) | {"build_learnable_preservation":3,"egg":1,"level_up":22,"machine":23,"machine_archive":20,"shared_egg":6} |
| [1401: バリヤード](pokemon/1401.md) | {"egg":4,"level_up":25,"machine":32,"machine_archive":35,"shared_egg":4,"tutor":2} |
| [1402: フリーザー](pokemon/1402.md) | {"level_up":15,"machine":21,"machine_archive":20} |
| [1403: サンダー](pokemon/1403.md) | {"level_up":16,"machine":24,"machine_archive":16} |
| [1404: ファイヤー](pokemon/1404.md) | {"level_up":16,"machine":22,"machine_archive":17} |
| [1405: ヤドキング](pokemon/1405.md) | {"build_learnable_preservation":5,"egg":2,"level_up":21,"machine":43,"machine_archive":38,"move_memory_reminder":3,"shared_egg":4} |
| [1406: サニーゴ](pokemon/1406.md) | {"egg":6,"level_up":13,"machine":29,"machine_archive":20,"shared_egg":6,"tutor":1} |
| [1407: ジグザグマ](pokemon/1407.md) | {"egg":3,"level_up":14,"machine":21,"machine_archive":22,"shared_egg":3,"tutor":1} |
| [1408: マッスグマ](pokemon/1408.md) | {"build_learnable_preservation":3,"egg":1,"level_up":19,"machine":25,"machine_archive":24,"shared_egg":3,"tutor":1} |
| [1409: マネネ](pokemon/1409.md) | {"egg":5,"level_up":17,"machine":25,"machine_archive":20,"shared_egg":5} |
| [1410: ダルマッカ](pokemon/1410.md) | {"egg":8,"level_up":14,"machine":19,"machine_archive":24,"shared_egg":8} |
| [1411: ヒヒダルマ](pokemon/1411.md) | {"build_learnable_preservation":8,"egg":1,"level_up":16,"machine":28,"machine_archive":29,"shared_egg":8,"tutor":2} |
| [1412: ヒヒダルマ](pokemon/1412.md) | {"level_up":16,"machine":51,"tutor":10} |
| [1413: デスマス](pokemon/1413.md) | {"egg":1,"level_up":16,"machine":17,"machine_archive":19,"shared_egg":1,"tutor":1} |
| [1414: マッギョ](pokemon/1414.md) | {"egg":8,"level_up":15,"machine":21,"machine_archive":16,"shared_egg":8,"tutor":3} |
| [1415: ガーディ](pokemon/1415.md) | {"egg":6,"level_up":15,"machine":18,"machine_archive":25,"shared_egg":6} |
| [1416: ウインディ](pokemon/1416.md) | {"build_learnable_preservation":5,"egg":1,"level_up":19,"machine":23,"machine_archive":31,"shared_egg":6} |
| [1417: ビリリダマ](pokemon/1417.md) | {"egg":3,"level_up":17,"machine":20,"machine_archive":16,"shared_egg":3} |
| [1418: マルマイン](pokemon/1418.md) | {"build_learnable_preservation":3,"egg":1,"level_up":18,"machine":20,"machine_archive":21,"shared_egg":3} |
| [1419: バクフーン](pokemon/1419.md) | {"build_learnable_preservation":4,"egg":1,"level_up":18,"machine":26,"machine_archive":31,"shared_egg":6} |
| [1420: ハリーセン](pokemon/1420.md) | {"egg":10,"level_up":17,"machine":25,"machine_archive":23,"shared_egg":10} |
| [1421: ニューラ](pokemon/1421.md) | {"egg":7,"level_up":13,"machine":26,"machine_archive":24,"shared_egg":7} |
| [1422: ダイケンキ](pokemon/1422.md) | {"build_learnable_preservation":6,"egg":1,"level_up":18,"machine":30,"machine_archive":22,"shared_egg":8} |
| [1423: ドレディア](pokemon/1423.md) | {"build_learnable_preservation":4,"egg":1,"level_up":23,"machine":22,"machine_archive":25,"shared_egg":4} |
| [1424: バスラオ](pokemon/1424.md) | {"egg":2,"level_up":16,"machine":17,"machine_archive":17,"shared_egg":2} |
| [1425: ゾロア](pokemon/1425.md) | {"egg":4,"level_up":13,"machine":22,"machine_archive":24,"shared_egg":4} |
| [1426: ゾロアーク](pokemon/1426.md) | {"build_learnable_preservation":4,"egg":1,"level_up":16,"machine":32,"machine_archive":30,"shared_egg":4} |
| [1427: ウォーグル](pokemon/1427.md) | {"build_learnable_preservation":1,"egg":2,"level_up":17,"machine":27,"machine_archive":29,"shared_egg":2} |
| [1428: ヌメイル](pokemon/1428.md) | {"build_learnable_preservation":2,"egg":1,"level_up":14,"machine":19,"machine_archive":18,"shared_egg":2} |
| [1429: ヌメルゴン](pokemon/1429.md) | {"build_learnable_preservation":3,"egg":1,"level_up":19,"machine":29,"machine_archive":28,"shared_egg":2} |
| [1430: クレベース](pokemon/1430.md) | {"build_learnable_preservation":2,"egg":1,"level_up":20,"machine":22,"machine_archive":21,"shared_egg":3} |
| [1431: ジュナイパー](pokemon/1431.md) | {"build_learnable_preservation":3,"egg":2,"level_up":16,"machine":33,"machine_archive":27,"shared_egg":5} |
| [1432: アヤシシ](pokemon/1432.md) | {"build_learnable_preservation":5,"egg":2,"level_up":15,"machine":26,"machine_archive":31,"shared_egg":8} |
| [1433: バサギリ](pokemon/1433.md) | {"build_learnable_preservation":5,"egg":2,"level_up":14,"machine":26,"machine_archive":22,"shared_egg":5} |
| [1434: ガチグマ](pokemon/1434.md) | {"build_learnable_preservation":6,"egg":2,"level_up":18,"machine":30,"machine_archive":31,"shared_egg":12} |
| [1435: イダイトウ](pokemon/1435.md) | {"egg":2,"level_up":18,"machine":19,"machine_archive":25,"shared_egg":2} |
| [1436: イダイトウ](pokemon/1436.md) | {"egg":2,"level_up":18,"machine":19,"machine_archive":25,"shared_egg":2} |
| [1437: オオニューラ](pokemon/1437.md) | {"build_learnable_preservation":7,"egg":2,"level_up":15,"machine":30,"machine_archive":27,"shared_egg":7} |
| [1438: ハリーマン](pokemon/1438.md) | {"build_learnable_preservation":7,"egg":2,"level_up":17,"machine":27,"machine_archive":24,"shared_egg":10} |
| [1439: ラブトロス](pokemon/1439.md) | {"level_up":17,"machine":18,"machine_archive":22} |
| [1440: ラブトロス](pokemon/1440.md) | {"level_up":17,"machine":18,"machine_archive":22} |
| [1441: フシギバナ](pokemon/1441.md) | {"egg":2,"level_up":25,"machine":33,"tutor":18} |
| [1442: リザードン](pokemon/1442.md) | {"egg":2,"level_up":23,"machine":35,"tutor":25} |
| [1443: カメックス](pokemon/1443.md) | {"egg":1,"level_up":23,"machine":28,"tutor":16} |
| [1444: バタフリー](pokemon/1444.md) | {"egg":2,"level_up":21,"machine":39,"tutor":2} |
| [1445: ピカチュウ](pokemon/1445.md) | {"egg":1,"level_up":15,"machine":40,"tutor":30} |
| [1446: ニャース](pokemon/1446.md) | {"egg":1,"level_up":17,"machine":38,"tutor":8} |
| [1447: カイリキー](pokemon/1447.md) | {"egg":1,"level_up":23,"machine":42,"tutor":14} |
| [1448: ゲンガー](pokemon/1448.md) | {"egg":2,"level_up":23,"machine":26,"tutor":28} |
| [1449: キングラー](pokemon/1449.md) | {"egg":1,"level_up":21,"machine":36,"tutor":29} |
| [1450: ラプラス](pokemon/1450.md) | {"egg":2,"level_up":19,"machine":33,"tutor":15} |
| [1451: イーブイ](pokemon/1451.md) | {"egg":16,"level_up":19,"machine":24,"tutor":19} |
| [1452: カビゴン](pokemon/1452.md) | {"egg":14,"level_up":19,"machine":44,"tutor":5} |
| [1453: ダストダス](pokemon/1453.md) | {"egg":1,"level_up":20,"machine":37,"tutor":14} |
| [1454: メルメタル](pokemon/1454.md) | {"level_up":18,"machine":34,"tutor":1} |
| [1455: ゴリランダー](pokemon/1455.md) | {"egg":1,"level_up":19,"machine":42,"tutor":10} |
| [1456: エースバーン](pokemon/1456.md) | {"egg":1,"level_up":17,"machine":37,"tutor":4} |
| [1457: インテレオン](pokemon/1457.md) | {"egg":1,"level_up":15,"machine":36,"tutor":12} |
| [1458: アーマーガア](pokemon/1458.md) | {"egg":2,"level_up":17,"machine":37,"tutor":13} |
| [1459: イオルブ](pokemon/1459.md) | {"egg":2,"level_up":19,"machine":40,"tutor":14} |
| [1460: カジリガメ](pokemon/1460.md) | {"egg":2,"level_up":19,"machine":40,"tutor":9} |
| [1461: セキタンザン](pokemon/1461.md) | {"egg":2,"level_up":17,"machine":41,"tutor":10} |
| [1462: アップリュー](pokemon/1462.md) | {"egg":2,"level_up":20,"machine":32,"tutor":6} |
| [1463: タルップル](pokemon/1463.md) | {"egg":2,"level_up":20,"machine":36,"tutor":10} |
| [1464: サダイジャ](pokemon/1464.md) | {"egg":1,"level_up":14,"machine":29,"tutor":8} |
| [1465: ストリンダー](pokemon/1465.md) | {"egg":2,"level_up":29,"machine":40,"tutor":11} |
| [1466: ストリンダー](pokemon/1466.md) | {"level_up":26,"machine":40,"tutor":8} |
| [1467: マルヤクデ](pokemon/1467.md) | {"egg":2,"level_up":18,"machine":34,"tutor":11} |
| [1468: ブリムオン](pokemon/1468.md) | {"egg":2,"level_up":18,"machine":41,"tutor":4} |
| [1469: オーロンゲ](pokemon/1469.md) | {"egg":2,"level_up":22,"machine":41,"tutor":12} |
| [1470: マホイップ](pokemon/1470.md) | {"egg":1,"level_up":16,"machine":32,"tutor":9} |
| [1471: ダイオウドウ](pokemon/1471.md) | {"egg":1,"level_up":15,"machine":36,"tutor":10} |
| [1472: ジュラルドン](pokemon/1472.md) | {"egg":5,"level_up":14,"machine":41,"tutor":16} |
| [1473: ウーラオス](pokemon/1473.md) | {"level_up":19,"machine":40,"tutor":15} |
| [1474: ウーラオス](pokemon/1474.md) | {"level_up":18,"machine":36,"tutor":12} |
| [1475: ニャオハ](pokemon/1475.md) | {"egg":4,"level_up":13,"machine":17,"machine_archive":17,"shared_egg":4} |
| [1476: ニャローテ](pokemon/1476.md) | {"build_learnable_preservation":3,"egg":1,"level_up":14,"machine":19,"machine_archive":20,"shared_egg":4} |
| [1477: マスカーニャ](pokemon/1477.md) | {"build_learnable_preservation":4,"egg":2,"level_up":18,"machine":30,"machine_archive":31,"move_memory_reminder":2,"shared_egg":4} |
| [1478: ホゲータ](pokemon/1478.md) | {"egg":4,"level_up":12,"machine":16,"machine_archive":20,"shared_egg":4} |
| [1479: アチゲータ](pokemon/1479.md) | {"build_learnable_preservation":2,"egg":1,"level_up":14,"machine":16,"machine_archive":20,"shared_egg":4} |
| [1480: ラウドボーン](pokemon/1480.md) | {"build_learnable_preservation":4,"egg":2,"level_up":18,"machine":20,"machine_archive":32,"move_memory_reminder":2,"shared_egg":4} |
| [1481: クワッス](pokemon/1481.md) | {"egg":4,"level_up":12,"machine":16,"machine_archive":12,"shared_egg":4} |
| [1482: ウェルカモ](pokemon/1482.md) | {"build_learnable_preservation":4,"egg":1,"level_up":15,"machine":19,"machine_archive":14,"shared_egg":4} |
| [1483: ウェーニバル](pokemon/1483.md) | {"build_learnable_preservation":4,"egg":2,"level_up":19,"machine":27,"machine_archive":25,"move_memory_reminder":1,"shared_egg":4} |
| [1484: グルトン](pokemon/1484.md) | {"egg":5,"level_up":13,"machine":16,"machine_archive":15,"shared_egg":5} |
| [1485: パフュートン](pokemon/1485.md) | {"build_learnable_preservation":4,"egg":1,"level_up":15,"machine":19,"machine_archive":20,"shared_egg":5} |
| [1486: パフュートン](pokemon/1486.md) | {"build_learnable_preservation":4,"egg":1,"level_up":15,"machine":19,"machine_archive":20,"shared_egg":5} |
| [1487: タマンチュラ](pokemon/1487.md) | {"egg":4,"level_up":14,"machine":20,"machine_archive":11,"shared_egg":4} |
| [1488: ワナイダー](pokemon/1488.md) | {"build_learnable_preservation":3,"egg":1,"level_up":15,"machine":24,"machine_archive":20,"shared_egg":4} |
| [1489: マメバッタ](pokemon/1489.md) | {"egg":2,"level_up":13,"machine":12,"machine_archive":9,"shared_egg":2} |
| [1490: エクスレッグ](pokemon/1490.md) | {"build_learnable_preservation":1,"egg":2,"level_up":19,"machine":20,"machine_archive":18,"shared_egg":2} |
| [1491: パモ](pokemon/1491.md) | {"egg":4,"level_up":15,"machine":18,"machine_archive":17,"shared_egg":4} |
| [1492: パモット](pokemon/1492.md) | {"build_learnable_preservation":4,"egg":2,"level_up":16,"machine":21,"machine_archive":21,"shared_egg":4} |
| [1493: パーモット](pokemon/1493.md) | {"build_learnable_preservation":4,"egg":2,"level_up":19,"machine":30,"machine_archive":28,"shared_egg":4} |
| [1494: ワッカネズミ](pokemon/1494.md) | {"egg":6,"level_up":14,"machine":20,"machine_archive":17,"shared_egg":6} |
| [1495: イッカネズミ](pokemon/1495.md) | {"build_learnable_preservation":5,"egg":1,"level_up":16,"machine":22,"machine_archive":19,"shared_egg":6} |
| [1496: イッカネズミ](pokemon/1496.md) | {"build_learnable_preservation":5,"level_up":16,"machine":22,"machine_archive":19,"shared_egg":6} |
| [1497: パピモッチ](pokemon/1497.md) | {"egg":5,"level_up":15,"machine":16,"machine_archive":18,"shared_egg":5} |
| [1498: バウッツェル](pokemon/1498.md) | {"build_learnable_preservation":5,"egg":1,"level_up":15,"machine":17,"machine_archive":22,"shared_egg":5} |
| [1499: ミニーブ](pokemon/1499.md) | {"egg":4,"level_up":13,"machine":13,"machine_archive":11,"shared_egg":4} |
| [1500: オリーニョ](pokemon/1500.md) | {"build_learnable_preservation":2,"egg":2,"level_up":13,"machine":13,"machine_archive":11,"shared_egg":4} |
| [1501: オリーヴァ](pokemon/1501.md) | {"build_learnable_preservation":2,"egg":2,"level_up":17,"machine":17,"machine_archive":20,"shared_egg":4} |
| [1502: イキリンコ](pokemon/1502.md) | {"egg":4,"level_up":16,"machine":19,"machine_archive":16,"shared_egg":4} |
| [1503: イキリンコ](pokemon/1503.md) | {"egg":4,"level_up":16,"machine":19,"machine_archive":16,"shared_egg":4} |
| [1504: イキリンコ](pokemon/1504.md) | {"egg":4,"level_up":16,"machine":19,"machine_archive":16,"shared_egg":4} |
| [1505: イキリンコ](pokemon/1505.md) | {"egg":4,"level_up":16,"machine":19,"machine_archive":16,"shared_egg":4} |
| [1506: コジオ](pokemon/1506.md) | {"egg":4,"level_up":14,"machine":19,"machine_archive":12,"shared_egg":4} |
| [1507: ジオヅム](pokemon/1507.md) | {"build_learnable_preservation":2,"egg":1,"level_up":15,"machine":20,"machine_archive":15,"shared_egg":4} |
| [1508: キョジオーン](pokemon/1508.md) | {"build_learnable_preservation":2,"egg":1,"level_up":19,"machine":24,"machine_archive":22,"shared_egg":4} |
| [1509: カルボウ](pokemon/1509.md) | {"egg":3,"level_up":10,"machine":13,"machine_archive":8,"shared_egg":3} |
| [1510: グレンアルマ](pokemon/1510.md) | {"build_learnable_preservation":2,"egg":2,"level_up":17,"machine":27,"machine_archive":21,"shared_egg":3} |
| [1511: ソウブレイズ](pokemon/1511.md) | {"build_learnable_preservation":4,"egg":2,"level_up":15,"machine":27,"machine_archive":19,"move_memory_reminder":4,"shared_egg":3} |
| [1512: ズピカ](pokemon/1512.md) | {"egg":3,"level_up":13,"machine":16,"machine_archive":14,"shared_egg":3} |
| [1513: ハラバリー](pokemon/1513.md) | {"build_learnable_preservation":2,"egg":1,"level_up":14,"machine":16,"machine_archive":18,"shared_egg":3} |
| [1514: カイデン](pokemon/1514.md) | {"egg":6,"level_up":12,"machine":18,"machine_archive":17,"shared_egg":6} |
| [1515: タイカイデン](pokemon/1515.md) | {"build_learnable_preservation":3,"egg":2,"level_up":14,"machine":18,"machine_archive":21,"shared_egg":6} |
| [1516: オラチフ](pokemon/1516.md) | {"egg":4,"level_up":15,"machine":16,"machine_archive":16,"shared_egg":4} |
| [1517: マフィティフ](pokemon/1517.md) | {"build_learnable_preservation":2,"egg":1,"level_up":17,"machine":16,"machine_archive":24,"shared_egg":4} |
| [1518: シルシュルー](pokemon/1518.md) | {"egg":6,"level_up":15,"machine":26,"machine_archive":15,"shared_egg":6} |
| [1519: タギングル](pokemon/1519.md) | {"build_learnable_preservation":5,"egg":2,"level_up":15,"machine":28,"machine_archive":20,"shared_egg":6} |
| [1520: アノクサ](pokemon/1520.md) | {"egg":5,"level_up":15,"machine":17,"machine_archive":13,"shared_egg":5} |
| [1521: アノホラグサ](pokemon/1521.md) | {"build_learnable_preservation":5,"egg":2,"level_up":15,"machine":17,"machine_archive":16,"shared_egg":5} |
| [1522: ノノクラゲ](pokemon/1522.md) | {"egg":8,"level_up":17,"machine":25,"machine_archive":16,"shared_egg":8} |
| [1523: リククラゲ](pokemon/1523.md) | {"build_learnable_preservation":6,"egg":2,"level_up":18,"machine":25,"machine_archive":19,"shared_egg":8} |
| [1524: ガケガニ](pokemon/1524.md) | {"egg":4,"level_up":15,"machine":23,"machine_archive":23,"shared_egg":4} |
| [1525: カプサイジ](pokemon/1525.md) | {"egg":5,"level_up":12,"machine":16,"machine_archive":12,"shared_egg":5} |
| [1526: スコヴィラン](pokemon/1526.md) | {"build_learnable_preservation":4,"egg":2,"level_up":17,"machine":19,"machine_archive":20,"shared_egg":5} |
| [1527: シガロコ](pokemon/1527.md) | {"egg":4,"level_up":10,"machine":12,"machine_archive":14,"shared_egg":4} |
| [1528: ベラカス](pokemon/1528.md) | {"build_learnable_preservation":4,"egg":2,"level_up":17,"machine":25,"machine_archive":32,"move_memory_reminder":2,"shared_egg":4} |
| [1529: ヒラヒナ](pokemon/1529.md) | {"egg":2,"level_up":10,"machine":22,"machine_archive":14,"shared_egg":2} |
| [1530: クエスパトラ](pokemon/1530.md) | {"build_learnable_preservation":2,"egg":1,"level_up":16,"machine":28,"machine_archive":25,"shared_egg":2} |
| [1531: カヌチャン](pokemon/1531.md) | {"egg":3,"level_up":16,"machine":21,"machine_archive":12,"shared_egg":3} |
| [1532: ナカヌチャン](pokemon/1532.md) | {"build_learnable_preservation":3,"egg":2,"level_up":16,"machine":22,"machine_archive":12,"shared_egg":3} |
| [1533: デカヌチャン](pokemon/1533.md) | {"build_learnable_preservation":3,"egg":2,"level_up":17,"machine":23,"machine_archive":15,"shared_egg":3} |
| [1534: ウミディグダ](pokemon/1534.md) | {"egg":2,"level_up":12,"machine":17,"machine_archive":13,"shared_egg":2} |
| [1535: ウミトリオ](pokemon/1535.md) | {"build_learnable_preservation":2,"egg":1,"level_up":13,"machine":17,"machine_archive":16,"shared_egg":2} |
| [1536: オトシドリ](pokemon/1536.md) | {"egg":5,"level_up":16,"machine":27,"machine_archive":19,"shared_egg":5} |
| [1537: ナミイルカ](pokemon/1537.md) | {"egg":5,"level_up":13,"machine":17,"machine_archive":14,"shared_egg":5} |
| [1538: イルカマン](pokemon/1538.md) | {"build_learnable_preservation":4,"egg":1,"level_up":17,"machine":27,"machine_archive":24,"shared_egg":5} |
| [1539: イルカマン](pokemon/1539.md) | {"egg":1,"level_up":20,"machine":34,"tutor":10} |
| [1540: ブロロン](pokemon/1540.md) | {"egg":5,"level_up":15,"machine":21,"machine_archive":14,"shared_egg":5} |
| [1541: ブロロローム](pokemon/1541.md) | {"build_learnable_preservation":3,"egg":2,"level_up":17,"machine":21,"machine_archive":23,"shared_egg":5} |
| [1542: モトトカゲ](pokemon/1542.md) | {"egg":4,"level_up":14,"machine":20,"machine_archive":25,"shared_egg":4} |
| [1543: ミミズズ](pokemon/1543.md) | {"egg":3,"level_up":14,"machine":18,"machine_archive":19,"shared_egg":3} |
| [1544: キラーメ](pokemon/1544.md) | {"egg":3,"level_up":14,"machine":22,"machine_archive":11,"shared_egg":3} |
| [1545: キラフロル](pokemon/1545.md) | {"build_learnable_preservation":2,"egg":2,"level_up":17,"machine":24,"machine_archive":15,"shared_egg":3} |
| [1546: ボチ](pokemon/1546.md) | {"egg":6,"level_up":15,"machine":19,"machine_archive":20,"shared_egg":6} |
| [1547: ハカドッグ](pokemon/1547.md) | {"build_learnable_preservation":5,"egg":1,"level_up":16,"machine":21,"machine_archive":22,"shared_egg":6} |
| [1548: カラミンゴ](pokemon/1548.md) | {"egg":3,"level_up":15,"machine":23,"machine_archive":17,"shared_egg":3} |
| [1549: アルクジラ](pokemon/1549.md) | {"egg":5,"level_up":15,"machine":21,"machine_archive":15,"shared_egg":5} |
| [1550: ハルクジラ](pokemon/1550.md) | {"build_learnable_preservation":5,"egg":1,"level_up":15,"machine":22,"machine_archive":17,"shared_egg":5} |
| [1551: ミガルーサ](pokemon/1551.md) | {"egg":2,"level_up":13,"machine":18,"machine_archive":18,"shared_egg":2} |
| [1552: ヘイラッシャ](pokemon/1552.md) | {"egg":4,"level_up":17,"machine":16,"machine_archive":16,"shared_egg":4} |
| [1553: シャリタツ](pokemon/1553.md) | {"egg":3,"level_up":12,"machine":15,"machine_archive":13,"shared_egg":3} |
| [1554: シャリタツ](pokemon/1554.md) | {"egg":3,"level_up":12,"machine":15,"machine_archive":13,"shared_egg":3} |
| [1555: シャリタツ](pokemon/1555.md) | {"egg":3,"level_up":12,"machine":15,"machine_archive":13,"shared_egg":3} |
| [1556: コノヨザル](pokemon/1556.md) | {"build_learnable_preservation":3,"egg":2,"level_up":19,"machine":35,"machine_archive":29,"shared_egg":6} |
| [1557: ドオー](pokemon/1557.md) | {"build_learnable_preservation":10,"egg":2,"level_up":13,"machine":30,"machine_archive":23,"shared_egg":12} |
| [1558: リキキリン](pokemon/1558.md) | {"build_learnable_preservation":5,"egg":2,"level_up":16,"machine":32,"machine_archive":32,"shared_egg":8} |
| [1559: ノココッチ](pokemon/1559.md) | {"build_learnable_preservation":5,"egg":1,"level_up":17,"machine":35,"machine_archive":39,"shared_egg":6} |
| [1560: ノココッチ](pokemon/1560.md) | {"build_learnable_preservation":5,"egg":1,"level_up":17,"machine":35,"machine_archive":39,"shared_egg":6} |
| [1561: ドドゲザン](pokemon/1561.md) | {"build_learnable_preservation":4,"egg":2,"level_up":17,"machine":29,"machine_archive":18,"shared_egg":4} |
| [1562: イダイナキバ](pokemon/1562.md) | {"egg":2,"level_up":17,"machine":26,"machine_archive":25} |
| [1563: サケブシッポ](pokemon/1563.md) | {"egg":2,"level_up":16,"machine":35,"machine_archive":36,"move_memory_reminder":1} |
| [1564: アラブルタケ](pokemon/1564.md) | {"egg":2,"level_up":15,"machine":19,"machine_archive":19,"move_memory_reminder":1} |
| [1565: ハバタクカミ](pokemon/1565.md) | {"egg":2,"level_up":16,"machine":21,"machine_archive":21,"move_memory_reminder":1} |
| [1566: チヲハウハネ](pokemon/1566.md) | {"egg":2,"level_up":17,"machine":24,"machine_archive":23,"move_memory_reminder":1} |
| [1567: スナノケガワ](pokemon/1567.md) | {"egg":2,"level_up":17,"machine":23,"machine_archive":22,"move_memory_reminder":1} |
| [1568: テツノワダチ](pokemon/1568.md) | {"egg":2,"level_up":16,"machine":20,"machine_archive":26} |
| [1569: テツノツツミ](pokemon/1569.md) | {"egg":2,"level_up":14,"machine":21,"machine_archive":15,"move_memory_reminder":1} |
| [1570: テツノカイナ](pokemon/1570.md) | {"egg":2,"level_up":17,"machine":24,"machine_archive":21,"move_memory_reminder":1} |
| [1571: テツノコウベ](pokemon/1571.md) | {"egg":2,"level_up":17,"machine":25,"machine_archive":26} |
| [1572: テツノドクガ](pokemon/1572.md) | {"egg":2,"level_up":17,"machine":25,"machine_archive":20,"move_memory_reminder":1} |
| [1573: テツノイバラ](pokemon/1573.md) | {"egg":2,"level_up":17,"machine":35,"machine_archive":37,"move_memory_reminder":1} |
| [1574: セビエ](pokemon/1574.md) | {"egg":4,"level_up":13,"machine":13,"machine_archive":13,"shared_egg":4} |
| [1575: セゴール](pokemon/1575.md) | {"build_learnable_preservation":3,"egg":2,"level_up":12,"machine":15,"machine_archive":15,"shared_egg":4} |
| [1576: セグレイブ](pokemon/1576.md) | {"build_learnable_preservation":3,"egg":2,"level_up":17,"machine":22,"machine_archive":23,"shared_egg":4} |
| [1577: コレクレー](pokemon/1577.md) | {"egg":1,"level_up":2,"machine":11,"machine_archive":5} |
| [1578: コレクレー](pokemon/1578.md) | {"egg":1,"level_up":2,"machine":11,"machine_archive":5} |
| [1579: サーフゴー](pokemon/1579.md) | {"egg":2,"level_up":12,"machine":24,"machine_archive":16} |
| [1580: チオンジェン](pokemon/1580.md) | {"level_up":19,"machine":21,"machine_archive":19} |
| [1581: パオジアン](pokemon/1581.md) | {"level_up":19,"machine":20,"machine_archive":13} |
| [1582: ディンルー](pokemon/1582.md) | {"level_up":18,"machine":20,"machine_archive":18} |
| [1583: イーユイ](pokemon/1583.md) | {"level_up":18,"machine":19,"machine_archive":16} |
| [1584: トドロクツキ](pokemon/1584.md) | {"build_learnable_preservation":1,"egg":2,"level_up":17,"machine":29,"machine_archive":29,"move_memory_reminder":4} |
| [1585: テツノブジン](pokemon/1585.md) | {"egg":2,"level_up":18,"machine":37,"machine_archive":29,"move_memory_reminder":1} |
| [1586: コライドン](pokemon/1586.md) | {"level_up":16,"machine":30,"machine_archive":37} |
| [1587: ミライドン](pokemon/1587.md) | {"level_up":16,"machine":22,"machine_archive":27} |
| [1588: ウネルミナモ](pokemon/1588.md) | {"build_learnable_preservation":1,"egg":2,"level_up":15,"machine":19,"machine_archive":25,"move_memory_reminder":2} |
| [1589: テツノイサハ](pokemon/1589.md) | {"build_learnable_preservation":1,"egg":2,"level_up":16,"machine":20,"machine_archive":25,"move_memory_reminder":2} |
| [1590: ケンタロス](pokemon/1590.md) | {"egg":2,"level_up":14,"machine":22,"machine_archive":19,"shared_egg":2} |
| [1591: ケンタロス](pokemon/1591.md) | {"egg":2,"level_up":14,"machine":23,"machine_archive":24,"shared_egg":2} |
| [1592: ケンタロス](pokemon/1592.md) | {"egg":2,"level_up":14,"machine":22,"machine_archive":22,"shared_egg":2} |
| [1593: ウパー](pokemon/1593.md) | {"egg":12,"level_up":12,"machine":29,"machine_archive":17,"shared_egg":12} |
| [1594: ガチグマ](pokemon/1594.md) | {"build_learnable_preservation":1,"egg":2,"level_up":16,"machine":28,"machine_archive":27,"move_memory_reminder":1} |
| [1595: カミッチュ](pokemon/1595.md) | {"build_learnable_preservation":4,"egg":2,"level_up":15,"machine":14,"machine_archive":17,"move_memory_reminder":1,"shared_egg":4} |
| [1596: チャデス](pokemon/1596.md) | {"egg":2,"level_up":13,"machine":15,"machine_archive":15} |
| [1597: チャデス](pokemon/1597.md) | {"egg":2,"level_up":13,"machine":15,"machine_archive":15} |
| [1598: ヤバソチャ](pokemon/1598.md) | {"egg":2,"level_up":14,"machine":15,"machine_archive":16} |
| [1599: ヤバソチャ](pokemon/1599.md) | {"egg":2,"level_up":14,"machine":15,"machine_archive":16} |
| [1600: イイネイヌ](pokemon/1600.md) | {"level_up":12,"machine":28,"machine_archive":30} |
| [1601: マシマシラ](pokemon/1601.md) | {"level_up":13,"machine":26,"machine_archive":24} |
| [1602: キチキギス](pokemon/1602.md) | {"level_up":14,"machine":27,"machine_archive":23} |
| [1603: オーガポン](pokemon/1603.md) | {"build_learnable_preservation":4,"level_up":15,"machine":27,"machine_archive":18,"move_memory_reminder":4} |
| [1604: オーガポン](pokemon/1604.md) | {"build_learnable_preservation":4,"level_up":15,"machine":27,"machine_archive":18,"move_memory_reminder":4} |
| [1605: オーガポン](pokemon/1605.md) | {"build_learnable_preservation":4,"level_up":15,"machine":27,"machine_archive":18,"move_memory_reminder":4} |
| [1606: オーガポン](pokemon/1606.md) | {"build_learnable_preservation":4,"level_up":15,"machine":27,"machine_archive":18,"move_memory_reminder":4} |
| [1607: オーガポン](pokemon/1607.md) | {"level_up":21,"machine":35,"tutor":6} |
| [1608: オーガポン](pokemon/1608.md) | {"level_up":19,"machine":34,"tutor":6} |
| [1609: オーガポン](pokemon/1609.md) | {"level_up":19,"machine":34,"tutor":7} |
| [1610: オーガポン](pokemon/1610.md) | {"level_up":19,"machine":34,"tutor":6} |
| [1611: ブリジュラス](pokemon/1611.md) | {"build_learnable_preservation":3,"egg":2,"level_up":14,"machine":26,"machine_archive":24,"shared_egg":3} |
| [1612: カミツオロチ](pokemon/1612.md) | {"build_learnable_preservation":6,"egg":2,"level_up":16,"machine":18,"machine_archive":25,"move_memory_reminder":3,"shared_egg":4} |
| [1613: ウガツホムラ](pokemon/1613.md) | {"build_learnable_preservation":3,"egg":2,"level_up":17,"machine":21,"machine_archive":26,"move_memory_reminder":3} |
| [1614: タケルライコ](pokemon/1614.md) | {"build_learnable_preservation":1,"egg":2,"level_up":17,"machine":19,"machine_archive":26,"move_memory_reminder":1} |
| [1615: テツノイワオ](pokemon/1615.md) | {"egg":2,"level_up":17,"machine":20,"machine_archive":18} |
| [1616: テツノカシラ](pokemon/1616.md) | {"egg":2,"level_up":17,"machine":18,"machine_archive":23} |
| [1617: テラパゴス](pokemon/1617.md) | {"level_up":12,"machine":24,"machine_archive":28} |
| [1618: テラパゴス](pokemon/1618.md) | {"level_up":13,"tutor":12} |
| [1619: テラパゴス](pokemon/1619.md) | {"level_up":13,"tutor":12} |
| [1620: モモワロウ](pokemon/1620.md) | {"build_learnable_preservation":3,"level_up":13,"machine":13,"machine_archive":10,"move_memory_reminder":3} |
| [1621: アブソル（Mega Absol Z）](pokemon/1621.md) | {"level_up":13,"machine":31} |
| [1622: ガメノデス（Mega Barbaracle）](pokemon/1622.md) | {"level_up":15,"machine":32,"tutor":1} |
| [1623: セグレイブ（Mega Baxcalibur）](pokemon/1623.md) | {"level_up":17,"machine":22} |
| [1624: シャンデラ（Mega Chandelure）](pokemon/1624.md) | {"level_up":16,"machine":23} |
| [1625: ブリガロン（Mega Chesnaught）](pokemon/1625.md) | {"level_up":18,"machine":35} |
| [1626: チリーン（Mega Chimecho）](pokemon/1626.md) | {"level_up":14,"machine":26} |
| [1627: ピクシー（Mega Clefable）](pokemon/1627.md) | {"level_up":4,"machine":37} |
| [1628: ケケンカニ（Mega Crabominable）](pokemon/1628.md) | {"level_up":13,"machine":32} |
| [1629: ダークライ（Mega Darkrai）](pokemon/1629.md) | {"level_up":11,"machine":33} |
| [1630: マフォクシー（Mega Delphox）](pokemon/1630.md) | {"level_up":20,"machine":29} |
| [1631: ドラミドロ（Mega Dragalge）](pokemon/1631.md) | {"level_up":14,"machine":27} |
| [1632: カイリュー（Mega Dragonite）](pokemon/1632.md) | {"level_up":20,"machine":41} |
| [1633: ジジーロン（Mega Drampa）](pokemon/1633.md) | {"level_up":13,"machine":31,"tutor":3} |
| [1634: シビルドン（Mega Eelektross）](pokemon/1634.md) | {"level_up":10,"machine":35} |
| [1635: エンブオー（Mega Emboar）](pokemon/1635.md) | {"level_up":15,"machine":32} |
| [1636: ドリュウズ（Mega Excadrill）](pokemon/1636.md) | {"level_up":15,"machine":23} |
| [1637: タイレーツ（Mega Falinks）](pokemon/1637.md) | {"level_up":14,"machine":24} |
| [1638: オーダイル（Mega Feraligatr）](pokemon/1638.md) | {"level_up":15,"machine":30} |
| [1639: フラエッテ（Mega Floette (Eternal Flower)）](pokemon/1639.md) | {"level_up":16,"machine":32,"tutor":10} |
| [1640: ユキメノコ（Mega Froslass）](pokemon/1640.md) | {"level_up":21,"machine":27} |
| [1641: ガブリアス（Mega Garchomp Z）](pokemon/1641.md) | {"level_up":13,"machine":29} |
| [1642: キラフロル（Mega Glimmora）](pokemon/1642.md) | {"level_up":17,"machine":24} |
| [1643: グソクムシャ（Mega Golisopod）](pokemon/1643.md) | {"level_up":17,"machine":31} |
| [1644: ゴルーグ（Mega Golurk）](pokemon/1644.md) | {"level_up":16,"machine":39} |
| [1645: ゲッコウガ（Mega Greninja）](pokemon/1645.md) | {"level_up":18,"machine":32} |
| [1646: ルチャブル（Mega Hawlucha）](pokemon/1646.md) | {"level_up":16,"machine":37} |
| [1647: ヒードラン（Mega Heatran）](pokemon/1647.md) | {"level_up":14,"machine":28} |
| [1648: ルカリオ（Mega Lucario Z）](pokemon/1648.md) | {"level_up":26,"machine":31} |
| [1649: マギアナ（Mega Magearna）](pokemon/1649.md) | {"level_up":17,"machine":37} |
| [1650: マギアナ（Mega Magearna (Original Color source)）](pokemon/1650.md) | {"level_up":17,"machine":37} |
| [1651: カラマネロ（Mega Malamar）](pokemon/1651.md) | {"level_up":16,"machine":27} |
| [1652: メガニウム（Mega Meganium）](pokemon/1652.md) | {"level_up":16,"machine":22} |
| [1653: ニャオニクス（Mega Meowstic (Female source)）](pokemon/1653.md) | {"level_up":19,"machine":23} |
| [1654: ニャオニクス（Mega Meowstic (Male source)）](pokemon/1654.md) | {"level_up":19,"machine":23} |
| [1655: カエンジシ（Mega Pyroar）](pokemon/1655.md) | {"level_up":16,"machine":22} |
| [1656: ライチュウ（Mega Raichu X）](pokemon/1656.md) | {"level_up":21,"machine":25} |
| [1657: ライチュウ（Mega Raichu Y）](pokemon/1657.md) | {"level_up":21,"machine":25} |
| [1658: ペンドラー（Mega Scolipede）](pokemon/1658.md) | {"level_up":16,"machine":21} |
| [1659: スコヴィラン（Mega Scovillain）](pokemon/1659.md) | {"level_up":17,"machine":19} |
| [1660: ズルズキン（Mega Scrafty）](pokemon/1660.md) | {"level_up":15,"machine":36} |
| [1661: エアームド（Mega Skarmory）](pokemon/1661.md) | {"level_up":15,"machine":24} |
| [1662: ムクホーク（Mega Staraptor）](pokemon/1662.md) | {"level_up":13,"machine":18} |
| [1663: スターミー（Mega Starmie）](pokemon/1663.md) | {"level_up":16,"machine":24,"tutor":3} |
| [1664: シャリタツ（Mega Tatsugiri (Curly Form)）](pokemon/1664.md) | {"level_up":12,"machine":15} |
| [1665: シャリタツ（Mega Tatsugiri (Droopy Form)）](pokemon/1665.md) | {"level_up":12,"machine":15} |
| [1666: シャリタツ（Mega Tatsugiri (Stretchy Form)）](pokemon/1666.md) | {"level_up":12,"machine":15} |
| [1667: ウツボット（Mega Victreebel）](pokemon/1667.md) | {"level_up":6,"machine":23} |
| [1668: ゼラオラ（Mega Zeraora）](pokemon/1668.md) | {"level_up":18,"machine":26,"tutor":2} |
| [1669: ジガルデ（Mega Zygarde）](pokemon/1669.md) | {"level_up":19,"machine":35,"tutor":8} |
| [1670: イワンコ（マイペース）](pokemon/1670.md) | {"conditional_egg":4,"level_up":14,"machine":21,"machine_archive":17,"shared_egg":4} |
