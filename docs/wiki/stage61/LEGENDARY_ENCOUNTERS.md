# Stage61 伝説・幻・UB・パラドックス固定捕獲

[Wiki入口へ](README.md) / [進行ガイドへ](STORY_PROGRESSION.md)

固定捕獲イベント全117件。場所、解禁、遭遇レベル、捕獲戦開始時の技をまとめています。レベルが明示されたイベントの技は、現行ROMのレベル技表と、実装が呼ぶ標準`CreateMon`処理から算出した直近4技です。イベント側が個別技を上書きする実装ではありません。

`LEGACY_VALUE_PRESERVED_LOCATION_OR_LEVEL_AUDIT_REQUIRED`は既存Vegaイベントの値を保持する枠で、レベルまたは精密な入口を現行入力だけでは確定できないため、技を推測していません。`INHERITED_KANTO_RESCUE_READY_LEGACY_ENTRY_UNVERIFIED`はカントー側の救済経路は用意済みでも、従来トーホク側の正確なscript入口が未監査であることを示します。撃破・逃走時は捕獲済み記録を確定せず、イベント定義のretry policyに従って再試行できます。

## Vega既存伝説・遺産救済

| ポケモン | 場所 | 解禁・追加条件 | Lv | 遭遇時の技 | 状態 |
|---|---|---|---:|---|---|
| <a id="capture-event_special_national_0144"></a>[フリーザー](pokemon/0136.md) | ふたごじま (`K38` / `KANTO_DUNGEON_SEAFOAM_ISLANDS_B4_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / 既存条件 | 70 | リフレクター / れいとうビーム / はねやすめ / フェザーダンス | `INHERITED_KANTO_RESCUE_READY_LEGACY_ENTRY_UNVERIFIED`<br>`SCRIPT_PRESENT_ENTRY_UNVERIFIED_WITH_READY_KANTO_RESCUE` |
| <a id="capture-event_special_national_0145"></a>[サンダー](pokemon/0137.md) | むじんはつでんしょ (`K40` / `KANTO_DUNGEON_POWER_PLANT`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / 既存条件 | 70 | こうそくいどう / ほうでん / はねやすめ / ひかりのかべ | `INHERITED_KANTO_RESCUE_READY_LEGACY_ENTRY_UNVERIFIED`<br>`SCRIPT_PRESENT_ENTRY_UNVERIFIED_WITH_READY_KANTO_RESCUE` |
| <a id="capture-event_special_national_0146"></a>[ファイヤー](pokemon/0138.md) | セキエイこうげん (`K42` / `KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / 既存条件 | 70 | しんぴのまもり / エアスラッシュ / はねやすめ / ねっぷう | `INHERITED_KANTO_RESCUE_READY_LEGACY_ENTRY_UNVERIFIED`<br>`SCRIPT_PRESENT_ENTRY_UNVERIFIED_WITH_READY_KANTO_RESCUE` |
| <a id="capture-event_special_national_0150"></a>[ミュウツー](pokemon/0150.md) | ハナダのどうくつ (`K43` / `KANTO_DUNGEON_CERULEAN_CAVE_B1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / 既存条件 | 70 | ドわすれ / ビルドアップ / めいそう / サイコキネシス | `INHERITED_KANTO_RESCUE_READY_LEGACY_ENTRY_UNVERIFIED`<br>`SCRIPT_PRESENT_ENTRY_UNVERIFIED_WITH_READY_KANTO_RESCUE` |
| <a id="capture-event_special_national_0151"></a>[ミュウ](pokemon/0151.md) | セキエイこうげん (`K42` / `KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / 既存条件 | 70 | げんしのちから / めいそう / ドわすれ / サイコバーン | `INHERITED_KANTO_RESCUE_READY_LEGACY_ENTRY_UNVERIFIED`<br>`SCRIPT_PRESENT_ENTRY_UNVERIFIED_WITH_READY_KANTO_RESCUE` |
| <a id="capture-event_special_national_0243"></a>[ライコウ](pokemon/0139.md) | セキエイこうげん (`K42` / `KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / 既存条件 | 70 | かみくだく / かみなりのキバ / ほうでん / じんつうりき | `INHERITED_KANTO_RESCUE_READY_LEGACY_ENTRY_UNVERIFIED`<br>`SCRIPT_PRESENT_ENTRY_UNVERIFIED_WITH_READY_KANTO_RESCUE` |
| <a id="capture-event_special_national_0244"></a>[エンテイ](pokemon/0140.md) | セキエイこうげん (`K42` / `KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / 既存条件 | 70 | いばる / ほのおのキバ / ふんえん / じんつうりき | `INHERITED_KANTO_RESCUE_READY_LEGACY_ENTRY_UNVERIFIED`<br>`SCRIPT_PRESENT_ENTRY_UNVERIFIED_WITH_READY_KANTO_RESCUE` |
| <a id="capture-event_special_national_0245"></a>[スイクン](pokemon/0141.md) | セキエイこうげん (`K42` / `KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / 既存条件 | 70 | ミラーコート / こおりのキバ / アイスバーン / じんつうりき | `INHERITED_KANTO_RESCUE_READY_LEGACY_ENTRY_UNVERIFIED`<br>`SCRIPT_PRESENT_ENTRY_UNVERIFIED_WITH_READY_KANTO_RESCUE` |
| <a id="capture-event_special_national_0249"></a>[ルギア](pokemon/0148.md) | セキエイこうげん (`K42` / `KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / 既存条件 | 70 | エアロブラスト / だいこうずい / げんしのちから / しんぴのまもり | `INHERITED_KANTO_RESCUE_READY_LEGACY_ENTRY_UNVERIFIED`<br>`SCRIPT_PRESENT_ENTRY_UNVERIFIED_WITH_READY_KANTO_RESCUE` |
| <a id="capture-event_special_national_0250"></a>[ホウオウ](pokemon/0149.md) | セキエイこうげん (`K42` / `KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / 既存条件 | 70 | せいなるほのお / オーバーヒート / げんしのちから / しんぴのまもり | `INHERITED_KANTO_RESCUE_READY_LEGACY_ENTRY_UNVERIFIED`<br>`SCRIPT_PRESENT_ENTRY_UNVERIFIED_WITH_READY_KANTO_RESCUE` |
| <a id="capture-event_special_national_0380"></a>[ラティアス](pokemon/0407.md) | セキエイこうげん (`K42` / `KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / 既存条件 | 70 | あまえる / ドラゴンクロー / サイコバーン / りゅうのはどう | `INHERITED_KANTO_RESCUE_READY_LEGACY_ENTRY_UNVERIFIED`<br>`SCRIPT_PRESENT_ENTRY_UNVERIFIED_WITH_READY_KANTO_RESCUE` |
| <a id="capture-event_special_national_0381"></a>[ラティオス](pokemon/0408.md) | セキエイこうげん (`K42` / `KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / 既存条件 | 70 | りゅうのまい / ドラゴンクロー / サイコバーン / りゅうのはどう | `INHERITED_KANTO_RESCUE_READY_LEGACY_ENTRY_UNVERIFIED`<br>`SCRIPT_PRESENT_ENTRY_UNVERIFIED_WITH_READY_KANTO_RESCUE` |
| <a id="capture-event_special_national_0483"></a>[ディアルガ](pokemon/0145.md) | セキエイこうげん (`K42` / `KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / 既存条件 | 70 | メタルブラスト / てっぺき / りゅうのまい / りゅうせいぐん | `INHERITED_KANTO_RESCUE_READY_LEGACY_ENTRY_UNVERIFIED`<br>`SCRIPT_PRESENT_ENTRY_UNVERIFIED_WITH_READY_KANTO_RESCUE` |
| <a id="capture-event_special_national_0484"></a>[パルキア](pokemon/0146.md) | セキエイこうげん (`K42` / `KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / 既存条件 | 70 | あくうせつだん / だいこうずい / りゅうのまい / りゅうせいぐん | `INHERITED_KANTO_RESCUE_READY_LEGACY_ENTRY_UNVERIFIED`<br>`SCRIPT_PRESENT_ENTRY_UNVERIFIED_WITH_READY_KANTO_RESCUE` |
| <a id="capture-event_special_national_0485"></a>[ヒードラン](pokemon/0403.md) | セキエイこうげん (`K42` / `KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / 既存条件 | 70 | スターダスト / てっぺき / だいちのちから / ねっぷう | `INHERITED_KANTO_RESCUE_READY_LEGACY_ENTRY_UNVERIFIED`<br>`SCRIPT_PRESENT_ENTRY_UNVERIFIED_WITH_READY_KANTO_RESCUE` |
| <a id="capture-event_special_national_0490"></a>[マナフィ](pokemon/0405.md) | セキエイこうげん (`K42` / `KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / 既存条件 | 70 | ハイドロポンプ / ハートスタンプ / じこさいせい / こおりのキッス | `INHERITED_KANTO_RESCUE_READY_LEGACY_ENTRY_UNVERIFIED`<br>`SCRIPT_PRESENT_ENTRY_UNVERIFIED_WITH_READY_KANTO_RESCUE` |
| <a id="capture-event_special_national_0491"></a>[ダークライ](pokemon/0147.md) | セキエイこうげん (`K42` / `KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / 既存条件 | 70 | かげぶんしん / あやしいかぜ / くろいきり / ダークホール | `INHERITED_KANTO_RESCUE_READY_LEGACY_ENTRY_UNVERIFIED`<br>`SCRIPT_PRESENT_ENTRY_UNVERIFIED_WITH_READY_KANTO_RESCUE` |

## 時渡りと三獣

| ポケモン | 場所 | 解禁・追加条件 | Lv | 遭遇時の技 | 状態 |
|---|---|---|---:|---|---|
| <a id="capture-event_special_national_0251"></a>[セレビィ](pokemon/0552.md) | 25ばん どうろ (`K25` / `KANTO_OUTDOOR_ROUTE25`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋ときのかけら3個 | 80 | めいそう / かいふくふうじ / みらいよち / いやしのねがい | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |

## 古代巨人の封印

| ポケモン | 場所 | 解禁・追加条件 | Lv | 遭遇時の技 | 状態 |
|---|---|---|---:|---|---|
| <a id="capture-event_special_national_0377"></a>[レジロック](pokemon/0640.md) | オツキミやま (`K27` / `KANTO_DUNGEON_MT_MOON_B2_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋点字石板3枚 | 75 | ロックオン / でんじほう / ばかぢから / はかいこうせん | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0378"></a>[レジアイス](pokemon/0641.md) | オツキミやま (`K27` / `KANTO_DUNGEON_MT_MOON_B2_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋点字石板3枚 | 75 | ロックオン / でんじほう / ばかぢから / はかいこうせん | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0379"></a>[レジスチル](pokemon/0642.md) | オツキミやま (`K27` / `KANTO_DUNGEON_MT_MOON_B2_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋点字石板3枚 | 75 | ロックオン / でんじほう / ばかぢから / はかいこうせん | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0486"></a>[レジギガス](pokemon/0746.md) | オツキミやま (`K27` / `KANTO_DUNGEON_MT_MOON_B2_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 6体のレジ系登録 | 75 | ワイドガード / しねんのずつき / しっぺがえし / にぎりつぶす | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0894"></a>[レジエレキ](pokemon/1367.md) | オツキミやま (`K27` / `KANTO_DUNGEON_MT_MOON_B2_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / レジ系3体登録 | 75 | あばれる / ロックオン / でんじほう / はかいこうせん | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0895"></a>[レジドラゴ](pokemon/1368.md) | オツキミやま (`K27` / `KANTO_DUNGEON_MT_MOON_B2_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / レジ系3体登録 | 75 | あばれる / とぎすます / ドラゴンエナジー / はかいこうせん | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |

## 海・陸・空と星

| ポケモン | 場所 | 解禁・追加条件 | Lv | 遭遇時の技 | 状態 |
|---|---|---|---:|---|---|
| <a id="capture-event_special_national_0382"></a>[カイオーガ](pokemon/0643.md) | ポケモンやしき (`K39` / `KANTO_DUNGEON_POKEMON_MANSION_B1_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋各島の環境調査 | 75 | めいそう / だくりゅう / ぜったいれいど / ハイドロポンプ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0383"></a>[グラードン](pokemon/0644.md) | ポケモンやしき (`K39` / `KANTO_DUNGEON_POKEMON_MANSION_B1_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋各島の環境調査 | 75 | ビルドアップ / ソーラービーム / じわれ / だいもんじ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0384"></a>[レックウザ](pokemon/0645.md) | ポケモンやしき (`K39` / `KANTO_DUNGEON_POKEMON_MANSION_B1_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋各島の環境調査 | 75 | りゅうのはどう / りゅうのまい / そらをとぶ / ハイパーボイス | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0385"></a>[ジラーチ](pokemon/0646.md) | ポケモンやしき (`K39` / `KANTO_DUNGEON_POKEMON_MANSION_B1_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋ほしのかけら7個 | 80 | みらいよち / コスモパワー / とっておき / はめつのねがい | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0386"></a>[デオキシス](pokemon/0647.md) | ポケモンやしき (`K39` / `KANTO_DUNGEON_POKEMON_MANSION_B1_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋いんせき入手 | 80 | コスモパワー / じこさいせい / サイコブースト / はかいこうせん | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |

## 湖と時空の裂け目

| ポケモン | 場所 | 解禁・追加条件 | Lv | 遭遇時の技 | 状態 |
|---|---|---|---:|---|---|
| <a id="capture-event_special_national_0480"></a>[ユクシー](pokemon/0743.md) | ハナダのどうくつ (`K43` / `KANTO_DUNGEON_CERULEAN_CAVE_2_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋三湖の調査 | 75 | ドわすれ / じんつうりき / じたばた / しぜんのめぐみ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0481"></a>[エムリット](pokemon/0744.md) | ハナダのどうくつ (`K43` / `KANTO_DUNGEON_CERULEAN_CAVE_2_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋三湖の調査 | 75 | じんつうりき / めいそう / まねっこ / しぜんのめぐみ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0482"></a>[アグノム](pokemon/0745.md) | ハナダのどうくつ (`K43` / `KANTO_DUNGEON_CERULEAN_CAVE_2_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋三湖の調査 | 75 | じんつうりき / めいそう / とっておき / しぜんのめぐみ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0487"></a>[ギラティナ](pokemon/0747.md) | ハナダのどうくつ (`K43` / `KANTO_DUNGEON_CERULEAN_CAVE_2_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋時空イベント完了 | 75 | シャドークロー / シャドーダイブ / たたりめ / りゅうのまい | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0488"></a>[クレセリア](pokemon/0748.md) | ハナダのどうくつ (`K43` / `KANTO_DUNGEON_CERULEAN_CAVE_2_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋時空イベント完了 | 75 | きりさく / つきのひかり / サイコカッター / サイコシフト | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0492"></a>[シェイミ](pokemon/0749.md) | ハナダのどうくつ (`K43` / `KANTO_DUNGEON_CERULEAN_CAVE_2_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 全国研究ランク3 | 80 | しぜんのめぐみ / なやみのタネ / アロマセラピー / エナジーボール | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0493"></a>[アルセウス](pokemon/0750.md) | ハナダのどうくつ (`K43` / `KANTO_DUNGEON_CERULEAN_CAVE_2_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 各世代伝説アーク10件完了 | 100 | じこさいせい / はかいこうせん / ほろびのうた / さばきのつぶて | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0494"></a>[ビクティニ](pokemon/0751.md) | ハナダのどうくつ (`K43` / `KANTO_DUNGEON_CERULEAN_CAVE_2_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋連勝10 | 80 | めいそう / れんごく / すてみタックル / フレアドライブ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |

## 聖剣・四風・白黒炉心

| ポケモン | 場所 | 解禁・追加条件 | Lv | 遭遇時の技 | 状態 |
|---|---|---|---:|---|---|
| <a id="capture-event_special_national_0638"></a>[コバルオン](pokemon/0872.md) | ヤマブキシティ (`K41` / `KANTO_INDOOR_SAFFRON_CITY_DOJO`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋格闘調査 | 75 | てっぺき / ビルドアップ / メタルバースト / インファイト | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0639"></a>[テラキオン](pokemon/0873.md) | ヤマブキシティ (`K41` / `KANTO_INDOOR_SAFFRON_CITY_DOJO`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋格闘調査 | 75 | ふるいたてる / ビルドアップ / ストーンエッジ / インファイト | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0640"></a>[ビリジオン](pokemon/0874.md) | ヤマブキシティ (`K41` / `KANTO_INDOOR_SAFFRON_CITY_DOJO`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋格闘調査 | 75 | ファストガード / ふるいたてる / リーフブレード / インファイト | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0641"></a>[トルネロス](pokemon/0875.md) | ヤマブキシティ (`K41` / `KANTO_INDOOR_SAFFRON_CITY_DOJO`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋天候観測器 | 75 | あまごい / ぼうふう / あくのはどう / アームハンマー | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0642"></a>[ボルトロス](pokemon/0876.md) | ヤマブキシティ (`K41` / `KANTO_INDOOR_SAFFRON_CITY_DOJO`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋天候観測器 | 75 | わるだくみ / かみなり / あくのはどう / アームハンマー | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0643"></a>[レシラム](pokemon/0877.md) | ヤマブキシティ (`K41` / `KANTO_INDOOR_SAFFRON_CITY_DOJO`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / スフィアいせき後 | 75 | りゅうのまい / りゅうのはどう / おたけび / かみくだく | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0644"></a>[ゼクロム](pokemon/0878.md) | ヤマブキシティ (`K41` / `KANTO_INDOOR_SAFFRON_CITY_DOJO`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / スフィアいせき後 | 75 | りゅうのまい / ドラゴンクロー / おたけび / かみくだく | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0645"></a>[ランドロス](pokemon/0879.md) | ヤマブキシティ (`K41` / `KANTO_INDOOR_SAFFRON_CITY_DOJO`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋天候観測器 | 75 | すなあらし / じわれ / ストーンエッジ / アームハンマー | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0646"></a>[キュレム](pokemon/0880.md) | ヤマブキシティ (`K41` / `KANTO_INDOOR_SAFFRON_CITY_DOJO`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / スフィアいせき後 | 75 | りゅうのまい / りゅうのはどう / おたけび / がむしゃら | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0647"></a>[ケルディオ](pokemon/0881.md) | ヤマブキシティ (`K41` / `KANTO_INDOOR_SAFFRON_CITY_DOJO`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 聖剣3体登録 | 80 | ファストガード / ふるいたてる / ハイドロポンプ / インファイト | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0648"></a>[メロエッタ](pokemon/0882.md) | ヤマブキシティ (`K41` / `KANTO_INDOOR_SAFFRON_CITY_DOJO`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋音符アイテム4個 | 80 | サイコキネシス / ハイパーボイス / なりきり / インファイト | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0649"></a>[ゲノセクト](pokemon/0883.md) | ヤマブキシティ (`K41` / `KANTO_INDOOR_SAFFRON_CITY_DOJO`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋研究ランク4 | 80 | シンプルビーム / でんじほう / はかいこうせん / じばく | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |

## 生命・破壊・秩序

| ポケモン | 場所 | 解禁・追加条件 | Lv | 遭遇時の技 | 状態 |
|---|---|---|---:|---|---|
| <a id="capture-event_special_national_0716"></a>[ゼルネアス](pokemon/1005.md) | トキワのもり (`K26` / `KANTO_DUNGEON_VIRIDIAN_FOREST`) | 研究ランク4 (`UNLOCK_RESEARCH_RANK_4`) / 全国研究ランク4 | 75 | ウッドホーン / じこあんじ / ミストフィールド / しぜんのちから | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0717"></a>[イベルタル](pokemon/1006.md) | トキワのもり (`K26` / `KANTO_DUNGEON_VIRIDIAN_FOREST`) | 研究ランク4 (`UNLOCK_RESEARCH_RANK_4`) / 全国研究ランク4 | 75 | ゴーストダイブ / サイコキネシス / ドラゴンダイブ / きあいだま | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0718"></a>[ジガルデ](pokemon/1007.md) | トキワのもり (`K26` / `KANTO_DUNGEON_VIRIDIAN_FOREST`) | 研究ランク4 (`UNLOCK_RESEARCH_RANK_4`) / 全国研究ランク4 | 75 | じしん / ほごしょく / りゅうのはどう / とぐろをまく | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0719"></a>[ディアンシー](pokemon/1008.md) | トキワのもり (`K26` / `KANTO_DUNGEON_VIRIDIAN_FOREST`) | 研究ランク4 (`UNLOCK_RESEARCH_RANK_4`) / 殿堂入り＋鉱石納品 | 80 | ムーンフォース / ダイヤストーム / ひかりのかべ / しんぴのまもり | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0720"></a>[フーパ](pokemon/1009.md) | トキワのもり (`K26` / `KANTO_DUNGEON_VIRIDIAN_FOREST`) | 研究ランク4 (`UNLOCK_RESEARCH_RANK_4`) / 殿堂入り＋各地の封印輪3個 | 80 | めいそう / シャドーボール / わるだくみ / サイコキネシス | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0721"></a>[ボルケニオン](pokemon/1011.md) | トキワのもり (`K26` / `KANTO_DUNGEON_VIRIDIAN_FOREST`) | 研究ランク4 (`UNLOCK_RESEARCH_RANK_4`) / 殿堂入り＋ボルケニオン用圧力弁 | 80 | ハイドロポンプ / フレアドライブ / オーバーヒート / だいばくはつ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |

## 四島と星雲の子

| ポケモン | 場所 | 解禁・追加条件 | Lv | 遭遇時の技 | 状態 |
|---|---|---|---:|---|---|
| <a id="capture-event_special_national_0785"></a>[カプ・コケコ](pokemon/1183.md) | ふたごじま (`K38` / `KANTO_DUNGEON_SEAFOAM_ISLANDS_B4_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋各島試練 | 75 | しぜんのいかり / ほうでん / こうそくいどう / エレキボール | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0786"></a>[カプ・テテフ](pokemon/1184.md) | ふたごじま (`K38` / `KANTO_DUNGEON_SEAFOAM_ISLANDS_B4_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋各島試練 | 75 | じんつうりき / めいそう / おだてる / ムーンフォース | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0787"></a>[カプ・ブルル](pokemon/1185.md) | ふたごじま (`K38` / `KANTO_DUNGEON_SEAFOAM_ISLANDS_B4_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋各島試練 | 75 | しぜんのいかり / しねんのずつき / メガホーン / ロケットずつき | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0788"></a>[カプ・レヒレ](pokemon/1186.md) | ふたごじま (`K38` / `KANTO_DUNGEON_SEAFOAM_ISLANDS_B4_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋各島試練 | 75 | しぜんのいかり / だくりゅう / アクアリング / ハイドロポンプ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0800"></a>[ネクロズマ](pokemon/1198.md) | ふたごじま (`K38` / `KANTO_DUNGEON_SEAFOAM_ISLANDS_B4_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋星の祈り完了 | 75 | ステルスロック / てっぺき / しぼりとる / プリズムレーザー | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0802"></a>[マーシャドー](pokemon/1200.md) | ふたごじま (`K38` / `KANTO_DUNGEON_SEAFOAM_ISLANDS_B4_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋夜間 | 80 | インファイト / ビルドアップ / ふいうち / がむしゃら | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0807"></a>[ゼラオラ](pokemon/1259.md) | ふたごじま (`K38` / `KANTO_DUNGEON_SEAFOAM_ISLANDS_B4_F`) | 殿堂入り (`UNLOCK_HALL_OF_FAME`) / 殿堂入り＋停電復旧 | 80 | ファストガード / プラズマフィスト / インファイト / ほうでん | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |

## ウルトラホール

| ポケモン | 場所 | 解禁・追加条件 | Lv | 遭遇時の技 | 状態 |
|---|---|---|---:|---|---|
| <a id="capture-event_special_national_0793"></a>[ウツロイド](pokemon/1191.md) | シルフカンパニー (`K41` / `KANTO_DUNGEON_SILPH_CO_7_F`) | ウルトラボール系供給解禁 (`UNLOCK_BEAST_BALL`) / 殿堂入り＋ビーストボール解禁 | 90 | ベノムトラップ / ステルスロック / ワンダールーム / もろはのずつき | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0794"></a>[マッシブーン](pokemon/1192.md) | シルフカンパニー (`K41` / `KANTO_DUNGEON_SILPH_CO_7_F`) | ウルトラボール系供給解禁 (`UNLOCK_BEAST_BALL`) / 殿堂入り＋ビーストボール解禁 | 90 | とびかかる / ばくれつパンチ / ばかぢから / きあいパンチ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0795"></a>[フェローチェ](pokemon/1193.md) | シルフカンパニー (`K41` / `KANTO_DUNGEON_SILPH_CO_7_F`) | ウルトラボール系供給解禁 (`UNLOCK_BEAST_BALL`) / 殿堂入り＋ビーストボール解禁 | 90 | むしのさざめき / さきどり / とびひざげり / スピードスワップ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0796"></a>[デンジュモク](pokemon/1194.md) | シルフカンパニー (`K41` / `KANTO_DUNGEON_SILPH_CO_7_F`) | ウルトラボール系供給解禁 (`UNLOCK_BEAST_BALL`) / 殿堂入り＋ビーストボール解禁 | 90 | エレキフィールド / パワーウィップ / プラズマシャワー / でんじほう | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0797"></a>[テッカグヤ](pokemon/1195.md) | シルフカンパニー (`K41` / `KANTO_DUNGEON_SILPH_CO_7_F`) | ウルトラボール系供給解禁 (`UNLOCK_BEAST_BALL`) / 殿堂入り＋ビーストボール解禁 | 90 | ロケットずつき / てっぺき / ヘビーボンバー / すてみタックル | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0798"></a>[カミツルギ](pokemon/1196.md) | シルフカンパニー (`K41` / `KANTO_DUNGEON_SILPH_CO_7_F`) | ウルトラボール系供給解禁 (`UNLOCK_BEAST_BALL`) / 殿堂入り＋ビーストボール解禁 | 90 | みきり / エアスラッシュ / サイコカッター / ハサミギロチン | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0799"></a>[アクジキング](pokemon/1197.md) | シルフカンパニー (`K41` / `KANTO_DUNGEON_SILPH_CO_7_F`) | ウルトラボール系供給解禁 (`UNLOCK_BEAST_BALL`) / 殿堂入り＋ビーストボール解禁 | 90 | いえき / ヘビーボンバー / しぼりとる / ドラゴンダイブ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0805"></a>[ツンデツンデ](pokemon/1257.md) | シルフカンパニー (`K41` / `KANTO_DUNGEON_SILPH_CO_7_F`) | ウルトラボール系供給解禁 (`UNLOCK_BEAST_BALL`) / 殿堂入り＋ビーストボール解禁 | 90 | アイアンヘッド / ロックブラスト / ワイドガード / すてみタックル | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0806"></a>[ズガドーン](pokemon/1258.md) | シルフカンパニー (`K41` / `KANTO_DUNGEON_SILPH_CO_7_F`) | ウルトラボール系供給解禁 (`UNLOCK_BEAST_BALL`) / 殿堂入り＋ビーストボール解禁 | 90 | だいもんじ / シャドーボール / トリック / ビックリヘッド | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |

## ガラルの王冠

| ポケモン | 場所 | 解禁・追加条件 | Lv | 遭遇時の技 | 状態 |
|---|---|---|---:|---|---|
| <a id="capture-event_special_national_0888"></a>[ザシアン](pokemon/1361.md) | チャンピオンロード (`K42` / `KANTO_DUNGEON_VICTORY_ROAD_3_F`) | スフィア遺跡クリア (`UNLOCK_SPHERE_RUINS_CLEAR`) / スフィアいせき後 | 75 | アイアンヘッド / とぎすます / かみくだく / ムーンフォース | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0889"></a>[ザマゼンタ](pokemon/1362.md) | チャンピオンロード (`K42` / `KANTO_DUNGEON_VICTORY_ROAD_3_F`) | スフィア遺跡クリア (`UNLOCK_SPHERE_RUINS_CLEAR`) / スフィアいせき後 | 75 | とぎすます / ビルドアップ / かみくだく / ムーンフォース | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0890"></a>[ムゲンダイナ](pokemon/1363.md) | チャンピオンロード (`K42` / `KANTO_DUNGEON_VICTORY_ROAD_3_F`) | スフィア遺跡クリア (`UNLOCK_SPHERE_RUINS_CLEAR`) / 殿堂入り＋ダイマックスバンド | 75 | かえんほうしゃ / ダイマックスほう / コスモパワー / じこさいせい | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0893"></a>[ザルード](pokemon/1366.md) | チャンピオンロード (`K42` / `KANTO_DUNGEON_VICTORY_ROAD_3_F`) | スフィア遺跡クリア (`UNLOCK_SPHERE_RUINS_CLEAR`) / 全国研究ランク4 | 80 | エナジーボール / こうごうせい / アームハンマー / あばれる | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0896"></a>[ブリザポス](pokemon/1369.md) | チャンピオンロード (`K42` / `KANTO_DUNGEON_VICTORY_ROAD_3_F`) | スフィア遺跡クリア (`UNLOCK_SPHERE_RUINS_CLEAR`) / 殿堂入り＋豊穣イベント | 75 | あばれる / ちょうはつ / すてみタックル / つるぎのまい | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0897"></a>[レイスポス](pokemon/1370.md) | チャンピオンロード (`K42` / `KANTO_DUNGEON_VICTORY_ROAD_3_F`) | スフィア遺跡クリア (`UNLOCK_SPHERE_RUINS_CLEAR`) / 殿堂入り＋豊穣イベント | 75 | あばれる / かなしばり / すてみタックル / わるだくみ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0898"></a>[バドレックス](pokemon/1371.md) | チャンピオンロード (`K42` / `KANTO_DUNGEON_VICTORY_ROAD_3_F`) | スフィア遺跡クリア (`UNLOCK_SPHERE_RUINS_CLEAR`) / 殿堂入り＋豊穣イベント | 75 | めいそう / サイコキネシス / やどりぎのタネ / いやしのはどう | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |

## ヒスイの記憶

| ポケモン | 場所 | 解禁・追加条件 | Lv | 遭遇時の技 | 状態 |
|---|---|---|---:|---|---|
| <a id="capture-event_special_national_0905"></a>[ラブトロス](pokemon/1439.md) | ポケモンタワー (`K31` / `KANTO_DUNGEON_POKEMON_TOWER_5_F`) | 研究ランク4 (`UNLOCK_RESEARCH_RANK_4`) / 殿堂入り＋天候観測器 | 75 | いやしのねがい / ムーンフォース / げきりん / はるのあらし | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |

## 古代の時代裂け目

| ポケモン | 場所 | 解禁・追加条件 | Lv | 遭遇時の技 | 状態 |
|---|---|---|---:|---|---|
| <a id="capture-event_special_national_0984"></a>[イダイナキバ](pokemon/1562.md) | オツキミやま (`K27` / `KANTO_DUNGEON_MT_MOON_B2_F`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後 | 90 | インファイト / がむしゃら / メガホーン / もろはのずつき | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0985"></a>[サケブシッポ](pokemon/1563.md) | オツキミやま (`K27` / `KANTO_DUNGEON_MT_MOON_B2_F`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後 | 90 | かみくだく / ねがいごと / ジャイロボール / ほろびのうた | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0986"></a>[アラブルタケ](pokemon/1564.md) | オツキミやま (`K27` / `KANTO_DUNGEON_MT_MOON_B2_F`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後 | 90 | ふいうち / キノコのほうし / ねをはる / いかりのこな | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0987"></a>[ハバタクカミ](pokemon/1565.md) | オツキミやま (`K27` / `KANTO_DUNGEON_MT_MOON_B2_F`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後 | 90 | サイコショック / ゴーストダイブ / いたみわけ / ムーンフォース | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0988"></a>[チヲハウハネ](pokemon/1566.md) | オツキミやま (`K27` / `KANTO_DUNGEON_MT_MOON_B2_F`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後 | 90 | ダブルウイング / であいがしら / ふきとばし / きゅうけつ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0989"></a>[スナノケガワ](pokemon/1567.md) | オツキミやま (`K27` / `KANTO_DUNGEON_MT_MOON_B2_F`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後 | 90 | だいちのちから / ミラーコート / じゅうりょく / でんじほう | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_1005"></a>[トドロクツキ](pokemon/1584.md) | オツキミやま (`K27` / `KANTO_DUNGEON_MT_MOON_B2_F`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後 | 90 | ドラゴンダイブ / そらをとぶ / じごくづき / はねやすめ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_1009"></a>[ウネルミナモ](pokemon/1588.md) | オツキミやま (`K27` / `KANTO_DUNGEON_MT_MOON_B2_F`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後 | 90 | りゅうのはどう / げきりん / かえんほうしゃ / ハイドロポンプ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_1020"></a>[ウガツホムラ](pokemon/1613.md) | オツキミやま (`K27` / `KANTO_DUNGEON_MT_MOON_B2_F`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後 | 90 | だいもんじ / ふんえん / げきりん / フレアドライブ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_1021"></a>[タケルライコ](pokemon/1614.md) | オツキミやま (`K27` / `KANTO_DUNGEON_MT_MOON_B2_F`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後 | 90 | ライジングボルト / りゅうのはどう / でんじほう / ボディプレス | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |

## 未来の時代裂け目

| ポケモン | 場所 | 解禁・追加条件 | Lv | 遭遇時の技 | 状態 |
|---|---|---|---:|---|---|
| <a id="capture-event_special_national_0990"></a>[テツノワダチ](pokemon/1568.md) | むじんはつでんしょ (`K40` / `KANTO_DUNGEON_POWER_PLANT`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後 | 90 | ワイルドボルト / がむしゃら / メガホーン / ギガインパクト | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0991"></a>[テツノツツミ](pokemon/1569.md) | むじんはつでんしょ (`K40` / `KANTO_DUNGEON_POWER_PLANT`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後 | 90 | こうそくいどう / ゆきげしき / ハイドロポンプ / オーロラベール | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0992"></a>[テツノカイナ](pokemon/1570.md) | むじんはつでんしょ (`K40` / `KANTO_DUNGEON_POWER_PLANT`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後 | 90 | インファイト / みきり / ヘビーボンバー / はらだいこ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0993"></a>[テツノコウベ](pokemon/1571.md) | むじんはつでんしょ (`K40` / `KANTO_DUNGEON_POWER_PLANT`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後 | 90 | はたきおとす / あくのはどう / げきりん / りゅうのはどう | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0994"></a>[テツノドクガ](pokemon/1572.md) | むじんはつでんしょ (`K40` / `KANTO_DUNGEON_POWER_PLANT`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後 | 90 | きんぞくおん / あさのひざし / ぼうふう / むしのさざめき | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_0995"></a>[テツノイバラ](pokemon/1573.md) | むじんはつでんしょ (`K40` / `KANTO_DUNGEON_POWER_PLANT`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後 | 90 | ミサイルばり / じしん / ステルスロック / ストーンエッジ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_1006"></a>[テツノブジン](pokemon/1585.md) | むじんはつでんしょ (`K40` / `KANTO_DUNGEON_POWER_PLANT`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後 | 90 | はたきおとす / みちづれ / ワイドガード / ファストガード | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_1010"></a>[テツノイサハ](pokemon/1589.md) | むじんはつでんしょ (`K40` / `KANTO_DUNGEON_POWER_PLANT`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後 | 90 | インファイト / ふういん / メガホーン / きしかいせい | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_1022"></a>[テツノイワオ](pokemon/1615.md) | むじんはつでんしょ (`K40` / `KANTO_DUNGEON_POWER_PLANT`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後 | 90 | つるぎのまい / メガホーン / ファストガード / ストーンエッジ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_1023"></a>[テツノカシラ](pokemon/1616.md) | むじんはつでんしょ (`K40` / `KANTO_DUNGEON_POWER_PLANT`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後 | 90 | みらいよち / ボルトチェンジ / ファストガード / メタルバースト | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |

## 災厄の封印

| ポケモン | 場所 | 解禁・追加条件 | Lv | 遭遇時の技 | 状態 |
|---|---|---|---:|---|---|
| <a id="capture-event_special_national_1001"></a>[チオンジェン](pokemon/1580.md) | ポケモンタワー (`K31` / `KANTO_DUNGEON_POKEMON_TOWER_5_F`) | スフィア遺跡クリア (`UNLOCK_SPHERE_RUINS_CLEAR`) / スフィアいせき後 | 90 | パワーウィップ / グラスフィールド / はたきおとす / リーフストーム | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_1002"></a>[パオジアン](pokemon/1581.md) | ポケモンタワー (`K31` / `KANTO_DUNGEON_POKEMON_TOWER_5_F`) | スフィア遺跡クリア (`UNLOCK_SPHERE_RUINS_CLEAR`) / スフィアいせき後 | 90 | せいなるつるぎ / じこさいせい / じごくづき / ぜったいれいど | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_1003"></a>[ディンルー](pokemon/1582.md) | ポケモンタワー (`K31` / `KANTO_DUNGEON_POKEMON_TOWER_5_F`) | スフィア遺跡クリア (`UNLOCK_SPHERE_RUINS_CLEAR`) / スフィアいせき後 | 90 | いわなだれ / おきみやげ / じしん / じわれ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_1004"></a>[イーユイ](pokemon/1583.md) | ポケモンタワー (`K31` / `KANTO_DUNGEON_POKEMON_TOWER_5_F`) | スフィア遺跡クリア (`UNLOCK_SPHERE_RUINS_CLEAR`) / スフィアいせき後 | 90 | いばる / れんごく / おきみやげ / オーバーヒート | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |

## エリアゼロ炉心

| ポケモン | 場所 | 解禁・追加条件 | Lv | 遭遇時の技 | 状態 |
|---|---|---|---:|---|---|
| <a id="capture-event_special_national_1007"></a>[コライドン](pokemon/1586.md) | ハナダのどうくつ (`K43` / `KANTO_DUNGEON_CERULEAN_CAVE_B1_F`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後＋パラドックス調査 | 100 | げきりん / インファイト / フレアドライブ / ギガインパクト | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_1008"></a>[ミライドン](pokemon/1587.md) | ハナダのどうくつ (`K43` / `KANTO_DUNGEON_CERULEAN_CAVE_B1_F`) | パラドックス研究解禁 (`UNLOCK_PARADOX_RESEARCH`) / スフィアいせき後＋パラドックス調査 | 100 | げきりん / かみなり / オーバーヒート / はかいこうせん | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |

## 仮面祭とくさりもち

| ポケモン | 場所 | 解禁・追加条件 | Lv | 遭遇時の技 | 状態 |
|---|---|---|---:|---|---|
| <a id="capture-event_special_national_1014"></a>[イイネイヌ](pokemon/1600.md) | トキワのもり (`K26` / `KANTO_DUNGEON_VIRIDIAN_FOREST`) | 研究ランク5 (`UNLOCK_RESEARCH_RANK_5`) / 殿堂入り＋研究ランク5 | 75 | ぶんまわす / かみくだく / ばかぢから / ギガインパクト | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_1015"></a>[マシマシラ](pokemon/1601.md) | トキワのもり (`K26` / `KANTO_DUNGEON_VIRIDIAN_FOREST`) | 研究ランク5 (`UNLOCK_RESEARCH_RANK_5`) / 殿堂入り＋研究ランク5 | 75 | めいそう / わるだくみ / みらいよち / すてゼリフ | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_1016"></a>[キチキギス](pokemon/1602.md) | トキワのもり (`K26` / `KANTO_DUNGEON_VIRIDIAN_FOREST`) | 研究ランク5 (`UNLOCK_RESEARCH_RANK_5`) / 殿堂入り＋研究ランク5 | 75 | ふくろだたき / おだてる / はねやすめ / ムーンフォース | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_1017"></a>[オーガポン](pokemon/1603.md) | トキワのもり (`K26` / `KANTO_DUNGEON_VIRIDIAN_FOREST`) | 研究ランク5 (`UNLOCK_RESEARCH_RANK_5`) / 殿堂入り＋研究ランク5 | 75 | ニードルガード / パワーウィップ / ばかぢから / ウッドハンマー | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |
| <a id="capture-event_special_national_1025"></a>[モモワロウ](pokemon/1620.md) | トキワのもり (`K26` / `KANTO_DUNGEON_VIRIDIAN_FOREST`) | 研究ランク5 (`UNLOCK_RESEARCH_RANK_5`) / 殿堂入り＋研究ランク5 | 80 | じゃどくのくさり / どくどく / わるだくみ / じこさいせい | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |

## 結晶と創世

| ポケモン | 場所 | 解禁・追加条件 | Lv | 遭遇時の技 | 状態 |
|---|---|---|---:|---|---|
| <a id="capture-event_special_national_1024"></a>[テラパゴス](pokemon/1617.md) | セキエイこうげん (`K42` / `KANTO_OUTDOOR_INDIGO_PLATEAU_EXTERIOR`) | テラオーブ解禁 (`UNLOCK_TERA_ORB`) / テラオーブ解禁＋研究ランク5 | 100 | テラクラスター / すてみタックル / ロックカット / ジャイロボール | `INHERITED_INTEGRATED`<br>`READY_TO_INTEGRATE` |

## Vega固有伝説アーカイブ

| ポケモン | 場所 | 解禁・追加条件 | Lv | 遭遇時の技 | 状態 |
|---|---|---|---:|---|---|
| <a id="capture-event_vega_archive_0142"></a>[ライラプス](pokemon/0142.md) | セキエイこうげん (`K42` / `KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / legacy entry unavailable OR caught dex not set | — | 既存値保持（未確定） | `LEGACY_VALUE_PRESERVED_LOCATION_OR_LEVEL_AUDIT_REQUIRED`<br>`READY_TO_INTEGRATE_KANTO_FALLBACK` |
| <a id="capture-event_vega_archive_0143"></a>[ガニメデ](pokemon/0143.md) | セキエイこうげん (`K42` / `KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / legacy entry unavailable OR caught dex not set | — | 既存値保持（未確定） | `LEGACY_VALUE_PRESERVED_LOCATION_OR_LEVEL_AUDIT_REQUIRED`<br>`READY_TO_INTEGRATE_KANTO_FALLBACK` |
| <a id="capture-event_vega_archive_0144"></a>[ネメア](pokemon/0144.md) | セキエイこうげん (`K42` / `KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / legacy entry unavailable OR caught dex not set | — | 既存値保持（未確定） | `LEGACY_VALUE_PRESERVED_LOCATION_OR_LEVEL_AUDIT_REQUIRED`<br>`READY_TO_INTEGRATE_KANTO_FALLBACK` |
| <a id="capture-event_vega_archive_0400"></a>[ロイツァー](pokemon/0400.md) | セキエイこうげん (`K42` / `KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / legacy entry unavailable OR caught dex not set | — | 既存値保持（未確定） | `LEGACY_VALUE_PRESERVED_LOCATION_OR_LEVEL_AUDIT_REQUIRED`<br>`READY_TO_INTEGRATE_KANTO_FALLBACK` |
| <a id="capture-event_vega_archive_0401"></a>[ガタノア](pokemon/0401.md) | セキエイこうげん (`K42` / `KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / legacy entry unavailable OR caught dex not set | — | 既存値保持（未確定） | `LEGACY_VALUE_PRESERVED_LOCATION_OR_LEVEL_AUDIT_REQUIRED`<br>`READY_TO_INTEGRATE_KANTO_FALLBACK` |
| <a id="capture-event_vega_archive_0410"></a>[アスフィア](pokemon/0410.md) | セキエイこうげん (`K42` / `KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F`) | 特別アーカイブ解禁 (`UNLOCK_SPECIAL_ARCHIVE`) / legacy entry unavailable OR caught dex not set | — | 既存値保持（未確定） | `LEGACY_VALUE_PRESERVED_LOCATION_OR_LEVEL_AUDIT_REQUIRED`<br>`READY_TO_INTEGRATE_KANTO_FALLBACK` |

## 再試行と捕獲前の注意

- 捕獲戦はボックスを含む保存先の空きがないと開始しません。
- 捕獲成功時だけ共有capture ledgerへ確定し、敗北・逃走・中断では再試行可能な設計です。
- 固定個体の現在技だけでなく、捕獲率・覚える状態異常技・みねうち互換を調べる場合は各ポケモンページと技索引を併用してください。
