# 伝説・幻・UB・パラドックス 125種

## 方針

125種を単一洞窟へ連続配置せず、18のspecialテーマarcへ分散します。下表には、これとは別に御三家・化石・進化・通信代替・RTC救済のservice arc 7件も併記します。各個体は `SHARED_CAPTURE_KEY_NATIONAL_XXXX` を全国共通keyとして持ち、既存Vega eventがexact-ROMで確認できた場合もKanto救済と重複しません。捕獲はcaught時だけcommitし、撃破・逃走・resetで再出現します。

既存Vega由来として資料に挙がる18種は、フリーザー、サンダー、ファイヤー、ミュウツー、ミュウ、ライコウ、エンテイ、スイクン、ルギア、ホウオウ、ラティアス、ラティオス、ディアルガ、パルキア、ヒードラン、フィオネ、マナフィ、ダークライです。ただしentry/Species ID/flagをexact-ROMで確認するまではlegacy意味の保持とKanto救済を分離します。

## arc一覧

| arc | title | host | unlock | 対象数 |
| --- | --- | --- | --- | --- |
| ARC_LEGACY_GUARDIANS | ベガ遺産の守護者 | HOST_LEGACY_ARCHIVE | UNLOCK_SPECIAL_ARCHIVE | 18 |
| ARC_JOHTO_TIME | 時渡りと三獣 | HOST_JOHTO_TIME | UNLOCK_HALL_OF_FAME | 1 |
| ARC_ANCIENT_GIANTS | 古代巨人の封印 | HOST_ANCIENT_GIANTS | UNLOCK_HALL_OF_FAME | 6 |
| ARC_HOENN_RESONANCE | 海・陸・空と星 | HOST_HOENN_SPACE | UNLOCK_HALL_OF_FAME | 5 |
| ARC_SINNOH_RIFT | 湖と時空の裂け目 | HOST_LAKE_RIFT | UNLOCK_HALL_OF_FAME | 8 |
| ARC_UNOVA_OATH | 聖剣・四風・白黒炉心 | HOST_SWORDS | UNLOCK_HALL_OF_FAME | 12 |
| ARC_KALOS_BALANCE | 生命・破壊・秩序 | HOST_KALOS_BALANCE | UNLOCK_RESEARCH_RANK_4 | 6 |
| ARC_ALOLA_LIGHT | 四島と星雲の子 | HOST_ALOLA_LIGHT | UNLOCK_HALL_OF_FAME | 14 |
| ARC_ULTRA_BREACH | ウルトラホール調査 | HOST_ULTRA_BREACH | UNLOCK_BEAST_BALL | 11 |
| ARC_MELTAN_FORGE | 金属生命の炉 | HOST_FUTURE_CORE | UNLOCK_HALL_OF_FAME | 2 |
| ARC_GALAR_CROWN | 双王・双拳・雪原 | HOST_GALAR_CROWN | UNLOCK_SPHERE_RUINS_CLEAR | 9 |
| ARC_HISUI_MEMORY | ヒスイの記憶 | HOST_RUINOUS_SEALS | UNLOCK_RESEARCH_RANK_4 | 1 |
| ARC_RUINOUS_SEALS | 災いの四封 | HOST_RUINOUS_SEALS | UNLOCK_SPHERE_RUINS_CLEAR | 4 |
| ARC_PARADOX_PAST | 過去の時代裂け目 | HOST_ANCIENT_GIANTS | UNLOCK_PARADOX_RESEARCH | 10 |
| ARC_PARADOX_FUTURE | 未来の時代裂け目 | HOST_FUTURE_CORE | UNLOCK_PARADOX_RESEARCH | 10 |
| ARC_KITAKAMI_MASK | 仮面祭とくさりもち | HOST_KITAKAMI_MASK | UNLOCK_RESEARCH_RANK_5 | 5 |
| ARC_AREA_ZERO_CORE | 過去と未来の走者 | HOST_AREA_ZERO | UNLOCK_PARADOX_RESEARCH | 2 |
| ARC_FINAL_CREATION | 結晶と創世 | HOST_FINAL_CREATION | UNLOCK_TERA_ORB | 1 |
| ARC_STARTER_RESEARCH | オーキド研究タマゴ | HOST_STARTER_LAB | UNLOCK_KANTO_EARLY_ACCESS | 0 |
| ARC_REGIONAL_NURSERY | リージョン育成研究 | HOST_REGIONAL_NURSERY | UNLOCK_REGIONAL_NURSERY | 0 |
| ARC_FOSSIL_RESEARCH | 復元研究台帳 | HOST_FOSSIL_LAB | UNLOCK_FOSSIL_SERVICE | 0 |
| ARC_VEGA_LEGACY_ARCHIVE | ベガ固有記録の復旧 | HOST_LEGACY_ARCHIVE | UNLOCK_SPECIAL_ARCHIVE | 0 |
| ARC_EVOLUTION_SUPPORT | 現代進化条件サポート | HOST_REGIONAL_NURSERY | UNLOCK_REGIONAL_NURSERY | 0 |
| ARC_TRADE_EMULATOR | 通信進化シミュレータ | HOST_TRADE_EMULATOR | UNLOCK_LINK_CORD_SERVICE | 0 |
| ARC_RTC_FALLBACK | せいたいレーダー時刻固定 | HOST_MISC_NATURE | UNLOCK_HALL_OF_FAME | 0 |

## 個別ルール

- タイプ：ヌルはgift、シルヴァディは進化。
- コスモッグは一save二回まで。ソルガレオ／ルナアーラ両分岐を外部交換なしで完成。
- フィオネはマナフィ繁殖を正規routeとし、egg生成不能時の研究救済を持つ。
- ベベノムはgift、アーゴヨンはりゅうのはどう条件。
- メルタン素材は反復入手、メルメタルは同ROM進化。
- ダクマは全国種として一体必須。ウーラオスの型はフォーム実績であり完成数には加算しない。
- paradox past/futureは別host/arcへ分離し、Area Zero coreだけ最後にまとめる。

全125行の入口、level、host、unlock、shared key、救済、現行証拠強度は `content/special_event_catalog_125.csv`。event flowと実台詞はevent/dialogue/state CSVにあります。
