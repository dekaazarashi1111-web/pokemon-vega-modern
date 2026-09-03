# Stage61 実行時の既知制約

[Wiki入口へ](README.md)

## ROM候補の状態

- SHA-256: `44e951e20e7985b6f4480a04ff997cc77e6305dd0945eb90cfed7e3c6d85ae4e`
- `candidate_status=CANDIDATE`
- strict全件監査: `DEFERRED_AUDIT`
- 通常野生、ecology、種族値、技性能、習得表、進化表は現ROMから直接抽出しています。
- 取得イベント、Raid、フォーム供給、item供給は統合済みのStage26/56/58正本を継承していますが、現SHAで全経路を手動走破したという意味ではありません。

## TM/HMと教え技（接続修正済み）

`gTMHMMoves` は128件（TM01–120＋HM01–08）へ再配置し、TM51–58と旧HM slotの衝突を解消しました。HM互換は実行時index 121–128へ移し、V4のTM51–58互換は設計入力から再構築しています。

`gTutorMoves` はV4の64件を全件接続し、通常教え技consumerの上限をslot 01–64へ修正しました。16件目以降が終端や隣接dataをMove IDとして誤読する状態はありません。

このWikiの各ポケモンページは、現ROMの実行時tableと互換bitsetからTM/HM 128件・教え技64件を直接抽出して掲載します。
ここで示すのは互換判定の接続状態であり、NPC配置・価格・解禁経路の一覧ではありません。
