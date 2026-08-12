# 公開ソース参照メモ

監査で参照した公開リポジトリの主要ファイルとblob SHAです。
Codex作業開始時は、cloneした版のSHAが一致するか確認してください。

## DPE-JP

|path|blob SHA|用途|
|---|---|---|
|`README.md`|`04e1a4c1e1a9a84107a707cab191ae450ba48338`|第9世代までのSpecies追加、CFRU-JP併用前提、BPRJ0へのビルド手順|
|`repointall`|`f11ede98fdf00d6ed43d8bafe04010fa543e0`|Species名、種族値、タマゴ技、進化、図鑑、sprite/icon等の全pointer再配置|
|`hooks`|`1b60100037242bc69db3a51ba8bbf7a6a3ac3997`|sprite、図鑑、進化、cry、icon等のhook site|
|`bytereplacement`|`1e2723a6bfe3d5ff9adb378f65b23602164dac4d`|図鑑RAM、名前長、sprite limit、cry等の固定byte変更|
|`scripts/insert.py`|`b26d6358d35272f2348e3a677ebede2540285153`|code insertion、hook/repoint/repointall処理|

## CFRU-JP

|path|blob SHA|用途|
|---|---|---|
|`README.md`|`a3832dc1faf9628cade0dedf09f8e528920267a0`|拡張戦闘エンジン、機能一覧、`src/config.h`設定|
|`repointall`|`0395889b6f0cd20f3de7749c5c0ef5a7a9e799d9`|技、技名、技効果script、特性名、item等の全pointer再配置|
|`repoints`|`e56ff804cca49e38aa7d18466dceb54e776cc662`|技説明、animation、battle commands、save section等の直接repoint|
|`hooks`|`51a0f10dd4cccad235b476edd534a0e3e7e612ad`|戦闘、AI、Mega、Dynamax、overworld、party等のhook site|
|`bytereplacement`|`5f74e264eefe6da7bc05d159adece5fd0eaf9b2f`|save拡張、move name長、ability拡張等の固定byte変更|
|`routinepointers`|`c0722629632ccc337a1710dfa11036fba64181a8`|script commands、specials、field effects等のpointer置換|
|`special_inserts.asm`|`f07e7e18bb747707d73cec62894c28647a737904`|vanilla領域へ直接挿入するassembly/data|
|`scripts/make.py`|`3c2818ebe17f0abb98cb46863fabe18601d947b0`|空き領域探索とbuild/insert開始|
|`scripts/insert.py`|`73222c0c56e3ad462b9ad1b5084764c9ac0ef565`|code insertion、byte replacement、hook/repoint処理|

## 注意

`repointall`は記載siteの4 bytesだけを書き換える処理ではありません。
そのsiteから旧pointerを読み、ROM内の一致pointerを走査して一括置換します。
したがってVegaが旧pointer参照を追加・変更している場合、siteの直接重複だけで互換性を判断できません。
