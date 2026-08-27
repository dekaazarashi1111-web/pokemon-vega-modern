# Stage57 横断デバッグ・修復報告

- Status: PASS
- ROM SHA-256: `546136a6baa26efd7a70c2b6826bf902c4841a4a1113cb53bfdc44c77971663d`
- 変更byte数: 3392

## 修復

- NPC会話pointer: 9件
- story/固定遭遇control-flow: 3件
- menu VRAM base callsite: 10件
- research binding: 846件
- Field PC binding: 69件
- 通常story trainerの再戦Lv80～100誤流入: 26戦修復、残存0戦
- 共有trainer 348は通常戦をID 1384へ分離し、Kanto高難度戦を保持
- 種族変更時のdefault nicknameと野生初期技をSpeciesへ同期

## 高速full scan

- physical maps: 678
- contactable roots: 5432
- reachable scripts: 8925
- diagnostics: 0
- wild headers / slots: 265 / 6175
- QOL research / Collection wild forms: 846 / 78
- Species range mismatch: 0

## mGBA exact-ROM

- Status: PASS
- domains: collection, menu, route505, species, static, story, world
- 動的process: 10（各domain独立2 process）
- warnings / errors: 0
- menu: 23 cases、Collection 14 hosts
- Route505: 66 natural encounters、identity 3 species
- Species: canonical 1621、created 1619、named 1620
- world: 22 input fixtures

## 505番道路

- 現行physical binding由来のRESEARCH候補: 431, 511, 521, 535, 540, 784, 809, 953, 990, 1003, 1316, 1524
- 旧T503 Speciesの自然流入: 0件
- Species 92 / 717 / 804は、party・戦闘Species・canonical名・front画像一致

## 再現性・境界

- declared span外変更: 0
- ROM / RAM / save / map / hook overlap: 0 / 0 / 0 / 0 / 0
- Stage56差分BPS往復: True
- clean直接BPS往復: True
