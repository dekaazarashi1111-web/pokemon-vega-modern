# プロジェクト概要とイベント設計範囲

## 現在の製品状態

基準はStage 35です。Trainer ChangeKitは1,302戦、6,490 member、1,228 SINGLE、74 DOUBLE、再戦227件を実ROMへ統合済みです。カントーには253 operational map、201 Kanto trainer、201 acquisition eventを担う24 host、Factory Trial/BP shopが存在します。

今回のイベント設計は、これらを作り直す仕事ではありません。現在不足している「第二地方としての物語の流れ」「町や施設での人の存在感」「認定章間の目的」「短いサブイベント」「QOL機能を自然に見せる導線」を追加します。

## 世界観の固定点

- Vega本編のトーホク地方が母体であり、元FireRedの物語を再演しない。
- カントーは、中盤から任意で訪問できるLv.68〜100固定の高難度第二地方。
- 初回到着地はクチバ。高レベル警告、回復、無料帰還を常に保証する。
- カントーの8認定章はVega badgeと別state。認定戦には既存の8 gym bossを使う。
- 認定章1〜4はVega殿堂入り前にも進行可能。認定章5〜8とカントーLeagueはVega殿堂入り後。
- Kanto League、Sphere完結、League II完了後にFinal Leagueへ至る。
- カントーからVegaのbadge、HM、story flagを書き換えない。
- ナナシマは対象外。

## 推奨する物語の軸

創作上の名称や登場人物は設計してよいものの、次の構造を維持してください。

1. クチバで「高難度地域の生態・戦術認定制度」に参加する。
2. 各地の調査・住民・施設を知りながら8認定章を進める。
3. 前半4章は、Vega本編を中断しなくても楽しめる任意の遠征として完結感を持たせる。
4. Vega殿堂入り後に、カントー各地の未解決課題と後半認定を再開する。
5. カントーLeague後に二地方の生態・戦術を結ぶ最終共鳴とFinal Leagueへつなぐ。

元FireRedのロケット団、原作ライバル、おとどけもの、原作badge/HM進行を復元してはいけません。既存の建物や地形は、研究施設、地域サービス、住民活動、認定制度へ意味を置き換えられます。

## コンテンツ密度の目標

固定件数を満たすための水増しは不要ですが、完成版は次を満たしてください。

- 1本の明確なmain arc。
- 8認定章とKanto Leagueに到達理由・前後会話がある。
- 8〜12本程度の短いsidequest chain。1 chainは概ね2〜4 event。
- 各主要都市に複数の役割が異なる会話またはservice event。
- 各論理地点K01〜K47に、新規event、既存content、ambient dialogue、または追加不要の明示判断がある。
- QOL featureは、既存UI自動解禁か、短いNPC/端末eventのどちらかへ必ず割り当てる。
- 最初のimplementation batchはクチバ周辺の5〜10 eventとし、単独で実装・検証できる。

## 文体と演出

- 会話は短く、GBAのテンポを守る。
- 人物ごとに口調を分けるが、説明を一人へ集中させない。
- 1回の会話で一つの目的または感情を伝える。
- 長い強制演出より、再訪時の台詞変化、任意会話、短い依頼で世界を見せる。
- 主人公の性格や発言を固定しない。
- 原作台詞のコピーは使わず、新規に書く。

## 既存contentとの関係

- `catalogs/existing_kanto_trainers.csv` の encounterは、`START_TRAINER_BATTLE`から参照できる。partyやtrainer dialogueを再定義しない。
- `catalogs/acquisition_hosts.csv` のhostは、`CALL_ACQUISITION_HOST`から参照できる。取得transactionを再実装しない。
- `catalogs/existing_events.csv` は既存ownerを維持し、必要なら前後を短いwrapper eventで補う。
- `catalogs/qol_features.csv` のQOL実装本体はCodexが担当する。ChatGPTは解禁理由、NPC/端末、短い説明、再訪時台詞を設計する。
