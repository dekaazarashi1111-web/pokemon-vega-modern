# 通常生態・化石・ベビィ・進化・Vega固有種

## 通常生態

strict direct 581種の現行証拠は、ROM wild table 567種と接続済みecology runtime 14種です。設計routeではTohokuを先、同地方なら低levelを先に選び、御三家・specialの一部には明示的な再取得／救済eventを追加します。論理候補を一つの通常wild slotへ詰める方式は使わず、既存95 ecology entryとレーダーmode 0〜4を前提に分散します。内部ストライク282はdirect sourceから除外し、公式255へ差し替えます。

## 化石16

公式13 + Vega 3をCinnabar Lab existing objectへ集約し、素材key単位で復元します。素材なし、cancel、storage full、save失敗では素材とclaimを消費しません。Vegaの牙/翼/闇の化石は既存意味を保持し、exact Tohoku入口が未確認でも同じ共有ledgerでKanto復元可能です。全件は `content/fossil_restoration_catalog_16.csv`。

## ベビィ50 family row

同ROM daycare/egg queueを使い、incense-era babyも外部itemへ依存しない統合条件にします。親やitemはeggのdurable生成前に消費しません。全50行は `content/baby_family_catalog_50.csv`。

## 通信進化30 edge

Saffron Pokémon Center 2Fのexisting scientistへ通信進化シミュレータを置きます。標準party selectionで対象とheld itemを再検証し、成功時だけ進化／item消費。通信相手を要求しません。全30行は `content/trade_alternative_catalog_30.csv`。

## 現代追加進化13

| 全国No. | 対象 | 進化元 | 正規条件 | ROM内fallback |
| --- | --- | --- | --- | --- |
| 862 | タチフサグマ | SPECIES_KEY_LINOONE_G | Lv.35以上＋夜 | せいたいレーダーの夜固定 |
| 863 | ニャイキング | SPECIES_KEY_MEOWTH_G | Lv.28以上 | 不要 |
| 864 | サニゴーン | SPECIES_KEY_CORSOLA_G | Lv.38以上 | 不要 |
| 865 | ネギガナイト | SPECIES_KEY_FARFETCHD_G | 1戦中に急所3回 | れんげきのあかしを使用 |
| 866 | バリコオル | SPECIES_KEY_MR_MIME_G | Lv.42以上 | 不要 |
| 867 | デスバーン | SPECIES_KEY_YAMASK_G | 累積49以上の被ダメージ後、指定場所でレベルアップ | われたせきばんを使用 |
| 900 | バサギリ | SPECIES_KEY_SCYTHER | くろのきせき使用 | 化石調査所で反復供給 |
| 902 | イダイトウ | SPECIES_KEY_BASCULIN_H | 反動ダメージ累計294以上 | 累計カウンタ表示＋研究員確認 |
| 903 | オオニューラ | SPECIES_KEY_SNEASEL_H | 昼にするどいツメ使用 | せいたいレーダーの朝昼固定 |
| 904 | ハリーマン | SPECIES_KEY_QWILFISH_H | どくばりセンボンを20回使用後レベルアップ | 技回数カウンタ表示＋技思い出し |
| 980 | ドオー | SPECIES_KEY_WOOPER_P | Lv.20以上 | 不要 |
| 981 | リキキリン | SPECIES_KEY_GIRAFARIG | ツインビーム習得後レベルアップ | 条件技教えNPC |
| 982 | ノココッチ | SPECIES_KEY_DUNSPARCE | ハイパードリル習得後レベルアップ | 条件技教えNPC |

条件実装の正規性を保ちつつ、RTC・場所predicate・累積counterが現engineに無い場合だけtoken/service fallbackを使います。全553 edgeの供給監査は `content/evolution_requirements_553.csv` と `content/evolution_supply_routes.csv`。

## Vega固有14 route

| Vega ID | 名称 | 既存意味 | 一次扱い | Kanto fallback |
| --- | --- | --- | --- | --- |
| 121 | スミロドン | FOSSIL_RESTORE | Tohoku行は監査完了までemit禁止。Kanto fallbackはexact hostのみemit可。 | EVENT_FOSSIL_RESTORE_VEGA_0121 |
| 122 | マカドゥス | EVOLUTION | Tohoku行は監査完了までemit禁止。Kanto fallbackはexact hostのみemit可。 | EVENT_VEGA_ARCHIVE_0122 |
| 142 | ライラプス | FIXED_CAPTURE | Tohoku行は監査完了までemit禁止。Kanto fallbackはexact hostのみemit可。 | EVENT_VEGA_ARCHIVE_0142 |
| 143 | ガニメデ | FIXED_CAPTURE | Tohoku行は監査完了までemit禁止。Kanto fallbackはexact hostのみemit可。 | EVENT_VEGA_ARCHIVE_0143 |
| 144 | ネメア | FIXED_CAPTURE | Tohoku行は監査完了までemit禁止。Kanto fallbackはexact hostのみemit可。 | EVENT_VEGA_ARCHIVE_0144 |
| 388 | ティオルス | FOSSIL_RESTORE | Tohoku行は監査完了までemit禁止。Kanto fallbackはexact hostのみemit可。 | EVENT_FOSSIL_RESTORE_VEGA_0388 |
| 389 | プテリクス | EVOLUTION | Tohoku行は監査完了までemit禁止。Kanto fallbackはexact hostのみemit可。 | EVENT_VEGA_ARCHIVE_0389 |
| 390 | ティラノス | FOSSIL_RESTORE | Tohoku行は監査完了までemit禁止。Kanto fallbackはexact hostのみemit可。 | EVENT_FOSSIL_RESTORE_VEGA_0390 |
| 400 | ロイツァー | FIXED_CAPTURE | Tohoku行は監査完了までemit禁止。Kanto fallbackはexact hostのみemit可。 | EVENT_VEGA_ARCHIVE_0400 |
| 401 | ガタノア | FIXED_CAPTURE | Tohoku行は監査完了までemit禁止。Kanto fallbackはexact hostのみemit可。 | EVENT_VEGA_ARCHIVE_0401 |
| 402 | テツカブリ | GIFT | Tohoku行は監査完了までemit禁止。Kanto fallbackはexact hostのみemit可。 | EVENT_VEGA_ARCHIVE_0402 |
| 406 | オルディナ | GIFT | Tohoku行は監査完了までemit禁止。Kanto fallbackはexact hostのみemit可。 | EVENT_VEGA_ARCHIVE_0406 |
| 409 | オルマリア | EVOLUTION | Tohoku行は監査完了までemit禁止。Kanto fallbackはexact hostのみemit可。 | EVENT_VEGA_ARCHIVE_0409 |
| 410 | アスフィア | FIXED_CAPTURE | Tohoku行は監査完了までemit禁止。Kanto fallbackはexact hostのみemit可。 | EVENT_VEGA_ARCHIVE_0410 |

既存Tohoku eventをprimary semanticとして壊さず、座標とscript entryを推測しません。exact auditで昇格するまで、Kanto archive/fossil fallbackだけがserializer対象です。ネメア後のライラプス／ガニメデ、化石3系統、ロイツァー等の既存順序はshared ledgerで重複を防ぎます。
