# 現状監査

## 数値の読み方

**設計カバー率**と**現行ROMで証明済みの到達率**を混同しません。

| 区分 | 一次対象数 | 意味 |
| --- | ---: | --- |
| strict direct source verified | 581 | ROM wild table 567種 + 接続済みecology runtime 14種に実Species sourceあり |
| exact evolution edge only | 451 | table edgeは確認済みだが、trigger・item・時間・技・場所・手持ち条件を全件実行確認していない |
| event/gift/route integration required | 174 | 本パッケージで具体routeを設計したが、添付ROMなしのため未統合 |
| 合計 | 1206 | 完成対象1206 |

strict directだけの下限は **581/1206 = 48.2%**。edgeを暫定加算すると **1032/1206 = 85.6%** ですが、これは完全到達率ではありません。設計graphは一次対象1206 + enabling form 10 = **1216/1216**をnew-game rootから解決します。

## 再分類の重要点

- 元資料の1231行は、Vega内部slotやフォームを完成数へ混在させていました。最終一次対象は1206です。
- 暫定candidate 198件は、内部除外と独立Vega判定を適用すると一次対象174件になります。進化入口フォーム10件を加え、実装監査対象は184 routeです。
- existing fixed event／giftは、資料上の記述だけでは `EXISTING_ROM_VERIFIED` に昇格していません。script entry、Species ID、completion state、reset挙動をexact-ROMで確認するまでは救済routeと分離します。
- direct source 582件のうち1件は内部ストライク282なので、正しいstrict directは581です。内訳はROM wild table 567種、接続済みecology runtime 14種です。
- evolution closure 1033件のうち同じ内部slotを除き、一次対象でedge到達扱いできる総数は1032です。

## 物理配置

release host 24件は、添付Kanto JSONから既存objectのlocal ID、座標、graphics、movement、script stub、object数を読んでいます。全てbefore=afterでobject delta 0です。`HOST_WEATHER_RESONANCE`は候補監査だけで割当eventがないため `RESERVED_UNUSED_HOST`。Tohoku既存eventは座標を創作せず `PHYSICAL_COORD_AUDIT_REQUIRED`です。

| host | map | group/map | local | 座標 | イベント数 |
| --- | --- | --- | --- | --- | --- |
| HOST_STARTER_LAB | KANTO_INDOOR_PALLET_TOWN_PROFESSOR_OAKS_LAB | 98/3 | 1 | (3,11,3) | 24 |
| HOST_REGIONAL_NURSERY | KANTO_INDOOR_PALLET_TOWN_PROFESSOR_OAKS_LAB | 98/3 | 3 | (11,10,3) | 21 |
| HOST_FOSSIL_LAB | KANTO_INDOOR_CINNABAR_ISLAND_POKEMON_LAB_EXPERIMENT_ROOM | 98/76 | 1 | (11,8,3) | 18 |
| HOST_TRADE_EMULATOR | KANTO_INDOOR_SAFFRON_CITY_POKEMON_CENTER_2_F | 98/89 | 1 | (6,2,3) | 1 |
| HOST_MOVE_TUTOR | KANTO_INDOOR_SAFFRON_CITY_MR_PSYCHICS_HOUSE | 98/90 | 1 | (7,4,3) | 2 |
| HOST_LEGACY_ARCHIVE | KANTO_INDOOR_INDIGO_PLATEAU_POKEMON_CENTER_1_F | 98/80 | 3 | (7,14,3) | 24 |
| HOST_ANCIENT_GIANTS | KANTO_DUNGEON_MT_MOON_B2_F | 97/3 | 1 | (13,7,3) | 16 |
| HOST_LAKE_RIFT | KANTO_DUNGEON_CERULEAN_CAVE_2_F | 97/73 | 1 | (9,18,3) | 8 |
| HOST_SWORDS | KANTO_INDOOR_SAFFRON_CITY_DOJO | 98/84 | 5 | (6,5,3) | 12 |
| HOST_KALOS_BALANCE | KANTO_DUNGEON_VIRIDIAN_FOREST | 97/0 | 1 | (29,58,3) | 6 |
| HOST_KITAKAMI_MASK | KANTO_DUNGEON_VIRIDIAN_FOREST | 97/0 | 2 | (45,58,3) | 5 |
| HOST_ALOLA_LIGHT | KANTO_DUNGEON_SEAFOAM_ISLANDS_B4_F | 97/87 | 1 | (8,18,1) | 14 |
| HOST_ULTRA_BREACH | KANTO_DUNGEON_SILPH_CO_7_F | 97/53 | 1 | (2,6,3) | 11 |
| HOST_GALAR_CROWN | KANTO_DUNGEON_VICTORY_ROAD_3_F | 97/41 | 1 | (40,7,3) | 9 |
| HOST_RUINOUS_SEALS | KANTO_DUNGEON_POKEMON_TOWER_5_F | 97/92 | 5 | (12,8,3) | 5 |
| HOST_FUTURE_CORE | KANTO_DUNGEON_POWER_PLANT | 97/95 | 1 | (7,27,3) | 12 |
| HOST_AREA_ZERO | KANTO_DUNGEON_CERULEAN_CAVE_B1_F | 97/74 | 1 | (31,9,4) | 2 |
| HOST_FINAL_CREATION | KANTO_OUTDOOR_INDIGO_PLATEAU_EXTERIOR | 96/9 | 2 | (11,6,0) | 1 |
| HOST_HOENN_SPACE | KANTO_DUNGEON_POKEMON_MANSION_B1_F | 97/62 | 3 | (34,13,3) | 5 |
| HOST_JOHTO_TIME | KANTO_OUTDOOR_ROUTE25 | 96/37 | 1 | (11,4,3) | 1 |
| HOST_MISC_NATURE | KANTO_OUTDOOR_CELADON_CITY | 96/6 | 2 | (38,14,3) | 1 |
| HOST_ICONIC_ZAPDOS | KANTO_DUNGEON_POWER_PLANT | 97/95 | 6 | (5,11,3) | 1 |
| HOST_ICONIC_ARTICUNO | KANTO_DUNGEON_SEAFOAM_ISLANDS_B4_F | 97/87 | 3 | (9,2,4) | 1 |
| HOST_ICONIC_MEWTWO | KANTO_DUNGEON_CERULEAN_CAVE_B1_F | 97/74 | 3 | (7,12,3) | 1 |

## 監査データ

- 1216行の証拠強度: `content/current_acquisition_audit_1216.csv`
- 184行のevent/route候補: `content/event_route_candidates_184.csv`
- new-game graph cases: `tests/route_reachability_cases.csv`
- exact-ROM全失敗系: `tests/exact_rom_acceptance_cases.csv`
