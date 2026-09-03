# Stage61 マップ・ストーリー進行ガイド

[Wiki入口へ](README.md)

現在地を『バッジ何個・直前に倒した相手・今いる町』で照合し、同じ項目の到達済みマップまでを捕獲・育成候補として扱ってください。トーホクの順路は既存Vegaを骨格にし、レベル帯、QOL、カントー分岐、フィールド能力はStage61の現行正本を反映しています。

## 早見表

| 区間 | 目安レベル | 主な順路 | 次に開く場所 |
|---|---:|---|---|
| [ゲーム開始〜1個目のジム](#story-s00) | Lv.2〜15 | ハクジタウン → 501ばんどうろ → 502ばんどうろ → アヤメシティ → アヤメシティジム | 503ばんどうろ、ちえのどうくつ方面 |
| [1個目のジム後〜2個目のジム](#story-s01) | Lv.13〜25 | 503ばんどうろ → ちえのどうくつ → 504ばんどうろ → 505ばんどうろ → ミルシティ → こころのやかた → ミルシティジム | 博物館へ重要書類を返すと505ばんどうろの封鎖が解除され、506ばんどうろへ進める |
| [2個目のジム後〜3個目のジム](#story-s02) | Lv.23〜31 | 505ばんどうろ → 506ばんどうろ → 519ばんどうろ・育て屋 → シオウシティ → リムけんきゅうじょ → シオウシティジム | 507ばんすいどうから海路へ。ジム3とD・Hビル初回攻略後は高レベルのカントー早期渡航も開く |
| [3個目のジム後〜D・Hビル攻略](#story-s03) | Lv.31〜38 | 507ばんすいどう → 508ばんすいどう → かいていトンネル → 509ばんすいどう → アーシアとう → D・Hビル | D・Hビル攻略で520ばんどうろの封鎖が解除される。カントー早期渡航はLv.68以上の任意高難度ルート |
| [D・Hビル攻略後〜4個目のジム](#story-s04) | Lv.35〜41 | 520ばんどうろ → 521ばんどうろ → ヒスイシティ → レンジャーベース周辺 → サファリ関連イベント → ヒスイシティジム | 518ばんどうろとハクジのもり北西、さらに522ばんどうろからオウニ方面 |
| [4個目のジム後〜5個目のジム](#story-s05) | Lv.41〜50 | 518ばんどうろ → ハクジのもり北西 → 522ばんどうろ → オウニシティ → ダークタワー → オウニシティジム | 514ばんどうろをいあいぎりで進み、カラスバ方面へ |
| [5個目のジム後〜6個目のジム](#story-s06) | Lv.48〜56 | 514ばんどうろ → カラスバシティ → ときのようかん → 517ばんどうろ → ユキユキやま → カラスバシティジム | オウニでいんせきを受け取り、515ばんどうろからラピスラ方面へ |
| [6個目のジム後〜7個目のジム](#story-s07) | Lv.54〜60 | オウニシティ → 515ばんどうろ → ラピスラシティ → ラピスラシティジム | D・Hだんアジトの終盤イベント |
| [7個目のジム後〜8個目のジム](#story-s08) | Lv.59〜67 | D・Hだんアジト → アーシアとう → 510ばんすいどう → 513ばんすいどう → 島部・任意探索 → ニューアイランド → ニューアイランドジム | ポケモンじょう、523ばんすいどう、チャンピオンロード、トーホクリーグ |
| [8個目のジム後〜初回殿堂入り](#story-s09) | Lv.67〜82 | ポケモンじょう → オウニシティ → 523ばんすいどう → チャンピオンロード → シャクドウとう → トーホクポケモンリーグ | 研究プロフィール、TM再利用、隠れ特性DexNav、強化リーグ、カントー認定章5以降などの殿堂入り後要素 |
| [任意のカントー早期渡航〜認定章4個](#story-s10) | Lv.68〜89 | カントー渡航ターミナル → 序盤認定エリア → 認定章1〜4の各エリア → 安全帰還ターミナル | 殿堂入りと認定章4個の両方で対戦用供給・高難度Raid、強化リーグIIが段階解禁 |
| [殿堂入り後〜最終章](#story-s11) | Lv.84〜100 | トーホク再訪・強化リーグ → カントー認定章5〜8 → カントーリーグ → スフィアいせき → 最終リーグ・D・H無限炉心 | Factory Master、UB・パラドックス研究、最終伝説イベント、全国収集完成 |

## 進行区間の詳細

> バッジ数だけで曖昧な場合は、直前のボス名と現在地も照合します。例:『2個目のジムに勝った』ならS02を現在区間とし、S00〜S01とS02の到達途中マップを候補にできます。

<a id="story-s00"></a>
### S00 ゲーム開始〜1個目のジム

- 進行key: `VEGA_PRE_ENTRY`
- 目安レベル: **Lv.2〜15**
- マップ順: **ハクジタウン → 501ばんどうろ → 502ばんどうろ → アヤメシティ → アヤメシティジム**
- 主目的:
  - ハクジ研究所で御三家とライバル初戦
  - 502ばんどうろでHM05フラッシュを受け取る
  - アヤメのゲートにいる3人を倒してジムへ
  - アマナを倒してエルナトバッジを得る
- 次の行先・解禁: 503ばんどうろ、ちえのどうくつ方面
- 主要戦: [RIVAL01_PLAYER_FAMER](MAJOR_BATTLES.md#battle-rival01_player_famer)、[RIVAL01_PLAYER_ACTASHI](MAJOR_BATTLES.md#battle-rival01_player_actashi)、[RIVAL01_PLAYER_LEEPUN](MAJOR_BATTLES.md#battle-rival01_player_leepun)、[GYM01_AMANA](MAJOR_BATTLES.md#battle-gym01_amana)
- Stage61 QOL解禁: 文章の即時表示、高速移動、個体値・努力値ジャッジ、PC検索・複数選択
- 注意: ライバルの御三家は主人公が選んだ御三家に応じて3分岐する。

<a id="story-s01"></a>
### S01 1個目のジム後〜2個目のジム

- 進行key: `VEGA_BADGE_1`
- 目安レベル: **Lv.13〜25**
- マップ順: **503ばんどうろ → ちえのどうくつ → 504ばんどうろ → 505ばんどうろ → ミルシティ → こころのやかた → ミルシティジム**
- 主目的:
  - ちえのどうくつを抜けてミルシティへ
  - こころのやかた周辺のイベントを進める
  - ナギナタを倒してアルネブバッジを得る
- 次の行先・解禁: 博物館へ重要書類を返すと505ばんどうろの封鎖が解除され、506ばんどうろへ進める
- 主要戦: [GYM02_NAGINATA](MAJOR_BATTLES.md#battle-gym02_naginata)
- Stage61 QOL解禁: 学習装置、かわらずのいし供給、タマゴのPC転送、無料の技思い出し
- 注意: Stage61ではバッジ1個で学習装置、かわらずのいし供給、タマゴPC転送、無料技思い出しが解禁される。

<a id="story-s02"></a>
### S02 2個目のジム後〜3個目のジム

- 進行key: `VEGA_BADGE_2`
- 目安レベル: **Lv.23〜31**
- マップ順: **505ばんどうろ → 506ばんどうろ → 519ばんどうろ・育て屋 → シオウシティ → リムけんきゅうじょ → シオウシティジム**
- 主目的:
  - 重要書類を返して506ばんどうろを開通させる
  - 519ばんどうろで育て屋を利用可能にする
  - シオウ到着後、リムけんきゅうじょでナバリを倒す
  - 研究所攻略後にHM03なみのりを受け取る
  - キリを倒してファクトバッジを得る
- 次の行先・解禁: 507ばんすいどうから海路へ。ジム3とD・Hビル初回攻略後は高レベルのカントー早期渡航も開く
- 主要戦: [RIVAL02_PLAYER_FAMER](MAJOR_BATTLES.md#battle-rival02_player_famer)、[RIVAL02_PLAYER_ACTASHI](MAJOR_BATTLES.md#battle-rival02_player_actashi)、[RIVAL02_PLAYER_LEEPUN](MAJOR_BATTLES.md#battle-rival02_player_leepun)、[NABARI01](MAJOR_BATTLES.md#battle-nabari01)、[GYM03_KIRI](MAJOR_BATTLES.md#battle-gym03_kiri)
- Stage61 QOL解禁: PC内技編集
- 注意: 捕獲要員や次の手持ち相談では、この時点で506・519・シオウ・研究所までを候補範囲に含める。

<a id="story-s03"></a>
### S03 3個目のジム後〜D・Hビル攻略

- 進行key: `VEGA_SHIOU_BADGE_3`
- 目安レベル: **Lv.31〜38**
- マップ順: **507ばんすいどう → 508ばんすいどう → かいていトンネル → 509ばんすいどう → アーシアとう → D・Hビル**
- 主目的:
  - なみのりで507〜509ばんすいどうを進む
  - かいていトンネルでライバル＆モスギスとのタッグ戦を行い、バトルサーチャーを得る
  - アーシアとうのD・Hビルを攻略してナバリを倒す
  - D・Hビル4FでHM06いわくだきを受け取る
- 次の行先・解禁: D・Hビル攻略で520ばんどうろの封鎖が解除される。カントー早期渡航はLv.68以上の任意高難度ルート
- 主要戦: [MOS_RIVAL_TAG_PLAYER_FAMER](MAJOR_BATTLES.md#battle-mos_rival_tag_player_famer)、[MOS_RIVAL_TAG_PLAYER_ACTASHI](MAJOR_BATTLES.md#battle-mos_rival_tag_player_actashi)、[MOS_RIVAL_TAG_PLAYER_LEEPUN](MAJOR_BATTLES.md#battle-mos_rival_tag_player_leepun)、[NABARI02](MAJOR_BATTLES.md#battle-nabari02)、[DH_RAID01_REVAVROOM](MAJOR_BATTLES.md#battle-dh_raid01_revavroom)
- Stage61 QOL解禁: このkeyでの追加解禁なし
- 注意: カントーは本編の適正レベルを大きく上回るため、進行必須ではない。

<a id="story-s04"></a>
### S04 D・Hビル攻略後〜4個目のジム

- 進行key: `VEGA_DH_CLEAR`
- 目安レベル: **Lv.35〜41**
- マップ順: **520ばんどうろ → 521ばんどうろ → ヒスイシティ → レンジャーベース周辺 → サファリ関連イベント → ヒスイシティジム**
- 主目的:
  - 解除された520ばんどうろからヒスイへ
  - レンジャー4連戦とジャッキー戦を突破する
  - サファリ関連の届け物を済ませる
  - ハンザを倒してセルファバッジを得る
- 次の行先・解禁: 518ばんどうろとハクジのもり北西、さらに522ばんどうろからオウニ方面
- 主要戦: [JACKIE01](MAJOR_BATTLES.md#battle-jackie01)、[GYM04_HANZA](MAJOR_BATTLES.md#battle-gym04_hanza)
- Stage61 QOL解禁: 経験アメXS/S供給、経験アメM初回分、特性カプセル・初期ミント供給、努力値全リセット、フィールドPC、PC持ち物一括操作、自動戦闘
- 注意: Stage61のD・Hビル攻略後にはフィールドPC、自動戦闘、経験アメXS/S、特性カプセル・ミント系など多くのQOLが解禁される。

<a id="story-s05"></a>
### S05 4個目のジム後〜5個目のジム

- 進行key: `VEGA_BADGE_4`
- 目安レベル: **Lv.41〜50**
- マップ順: **518ばんどうろ → ハクジのもり北西 → 522ばんどうろ → オウニシティ → ダークタワー → オウニシティジム**
- 主目的:
  - いわくだきで518ばんどうろ方面へ進む
  - ハクジのもり北西でHM04かいりきを受け取る
  - かいりきで522ばんどうろを抜けてオウニへ
  - オウニの橋でライバル戦
  - ダークタワー6FでHM01いあいぎりを受け取る
  - モク＆レンとのダブル戦に勝ち、ゲンマバッジを得る
- 次の行先・解禁: 514ばんどうろをいあいぎりで進み、カラスバ方面へ
- 主要戦: [RIVAL03_PLAYER_FAMER](MAJOR_BATTLES.md#battle-rival03_player_famer)、[RIVAL03_PLAYER_ACTASHI](MAJOR_BATTLES.md#battle-rival03_player_actashi)、[RIVAL03_PLAYER_LEEPUN](MAJOR_BATTLES.md#battle-rival03_player_leepun)、[GYM05_MOKU_REN](MAJOR_BATTLES.md#battle-gym05_moku_ren)
- Stage61 QOL解禁: このkeyでの追加解禁なし
- 注意: ジム5はダブルバトル。単体火力だけでなく、全体技・まもる・素早さ操作も準備候補になる。

<a id="story-s06"></a>
### S06 5個目のジム後〜6個目のジム

- 進行key: `VEGA_BADGE_5`
- 目安レベル: **Lv.48〜56**
- マップ順: **514ばんどうろ → カラスバシティ → ときのようかん → 517ばんどうろ → ユキユキやま → カラスバシティジム**
- 主目的:
  - 514ばんどうろの助手からHM02そらをとぶを受け取る
  - カラスバでライバル戦
  - ときのようかん最奥で過去のダイゴ＆ミクリとのイベント戦
  - 517ばんどうろ・ユキユキやまで救出イベントを進める
  - サザンカを倒してハダルバッジを得る
- 次の行先・解禁: オウニでいんせきを受け取り、515ばんどうろからラピスラ方面へ
- 主要戦: [RIVAL04_PLAYER_FAMER](MAJOR_BATTLES.md#battle-rival04_player_famer)、[RIVAL04_PLAYER_ACTASHI](MAJOR_BATTLES.md#battle-rival04_player_actashi)、[RIVAL04_PLAYER_LEEPUN](MAJOR_BATTLES.md#battle-rival04_player_leepun)、[PAST_DAIGO_MIKURI](MAJOR_BATTLES.md#battle-past_daigo_mikuri)、[GYM06_SAZANKA](MAJOR_BATTLES.md#battle-gym06_sazanka)
- Stage61 QOL解禁: パワー系道具
- 注意: Stage61ではバッジ5個で育成用パワー系道具の供給が解禁される。
- 注意: ときのようかんは既存Vega順路ではジム6前。PAST_DAIGO_MIKURIのV4戦闘表には『6個目後』という履歴ラベルも残るため、戦闘表側ではdirect binding未確定として区別する。

<a id="story-s07"></a>
### S07 6個目のジム後〜7個目のジム

- 進行key: `VEGA_BADGE_6`
- 目安レベル: **Lv.54〜60**
- マップ順: **オウニシティ → 515ばんどうろ → ラピスラシティ → ラピスラシティジム**
- 主目的:
  - オウニでいんせきを受け取って515ばんどうろを開く
  - ラピスラへ進む
  - コナギを倒してプリオルバッジを得る
- 次の行先・解禁: D・Hだんアジトの終盤イベント
- 主要戦: [GYM07_KONAGI](MAJOR_BATTLES.md#battle-gym07_konagi)
- Stage61 QOL解禁: 経験アメM反復供給
- 注意: Stage61ではバッジ6個で経験アメMの反復供給が解禁される。

<a id="story-s08"></a>
### S08 7個目のジム後〜8個目のジム

- 進行key: `VEGA_BADGE_7`
- 目安レベル: **Lv.59〜67**
- マップ順: **D・Hだんアジト → アーシアとう → 510ばんすいどう → 513ばんすいどう → 島部・任意探索 → ニューアイランド → ニューアイランドジム**
- 主目的:
  - D・HだんアジトB1Fでナバリ、ジョージ、ターナーを倒す
  - 攻略後にHM07たきのぼりを受け取る
  - アーシアから510・513ばんすいどうを進む
  - 島部の固定伝説は必要条件を満たしたものだけ任意で回収する
  - ニューアイランドでミュウツーを倒してミラクバッジを得る
- 次の行先・解禁: ポケモンじょう、523ばんすいどう、チャンピオンロード、トーホクリーグ
- 主要戦: [NABARI03](MAJOR_BATTLES.md#battle-nabari03)、[GEORGE01](MAJOR_BATTLES.md#battle-george01)、[TURNER01](MAJOR_BATTLES.md#battle-turner01)、[GYM08_MEWTWO](MAJOR_BATTLES.md#battle-gym08_mewtwo)
- Stage61 QOL解禁: 経験アメL・ぎんのおうかん
- 注意: バッジ7個で経験アメLとぎんのおうかん系供給が解禁される。

<a id="story-s09"></a>
### S09 8個目のジム後〜初回殿堂入り

- 進行key: `VEGA_BADGE_8`
- 目安レベル: **Lv.67〜82**
- マップ順: **ポケモンじょう → オウニシティ → 523ばんすいどう → チャンピオンロード → シャクドウとう → トーホクポケモンリーグ**
- 主目的:
  - ポケモンじょうでターナーを倒す
  - オウニ経由で523ばんすいどうへ
  - チャンピオンロードで最後のライバル戦
  - 523ばんすいどうでモスギスを倒す
  - 四天王ホオノキ・ミヤマ・ヤチヨ・カンゾウを順に倒す
  - チャンピオンのギンノを倒して初回殿堂入り
- 次の行先・解禁: 研究プロフィール、TM再利用、隠れ特性DexNav、強化リーグ、カントー認定章5以降などの殿堂入り後要素
- 主要戦: [TURNER02](MAJOR_BATTLES.md#battle-turner02)、[RIVAL05_PLAYER_FAMER](MAJOR_BATTLES.md#battle-rival05_player_famer)、[RIVAL05_PLAYER_ACTASHI](MAJOR_BATTLES.md#battle-rival05_player_actashi)、[RIVAL05_PLAYER_LEEPUN](MAJOR_BATTLES.md#battle-rival05_player_leepun)、[MOSUGISU_PRELEAGUE](MAJOR_BATTLES.md#battle-mosugisu_preleague)、[LEAGUE01_HOONOKI](MAJOR_BATTLES.md#battle-league01_hoonoki)、[LEAGUE02_MIYAMA](MAJOR_BATTLES.md#battle-league02_miyama)、[LEAGUE03_YACHIYO](MAJOR_BATTLES.md#battle-league03_yachiyo)、[LEAGUE04_KANZO](MAJOR_BATTLES.md#battle-league04_kanzo)、[CHAMPION_GINNO](MAJOR_BATTLES.md#battle-champion_ginno)
- Stage61 QOL解禁: 特性パッチ・全ミント、努力値リセット品、標準育成ショップ
- 注意: Stage61ではバッジ8個で特性パッチ・全ミント・努力値リセット品・標準育成ショップが解禁される。

<a id="story-s10"></a>
### S10 任意のカントー早期渡航〜認定章4個

- 進行key: `KANTO_EARLY_ACCESS`
- 目安レベル: **Lv.68〜89**
- マップ順: **カントー渡航ターミナル → 序盤認定エリア → 認定章1〜4の各エリア → 安全帰還ターミナル**
- 主目的:
  - ジム3とD・Hビル初回攻略後から任意で渡航
  - Lv.68以上の固定高難度帯として認定章を順に集める
  - 危険ならターミナルからトーホクへ戻り本編を続ける
- 次の行先・解禁: 殿堂入りと認定章4個の両方で対戦用供給・高難度Raid、強化リーグIIが段階解禁
- Stage61 QOL解禁: このkeyでの追加解禁なし
- 注意: カントーはプレイヤーレベル連動ではなく固定高レベル。本編の近道ではない。

<a id="story-s11"></a>
### S11 殿堂入り後〜最終章

- 進行key: `VEGA_HALL_OF_FAME`
- 目安レベル: **Lv.84〜100**
- マップ順: **トーホク再訪・強化リーグ → カントー認定章5〜8 → カントーリーグ → スフィアいせき → 最終リーグ・D・H無限炉心**
- 主目的:
  - 強化リーグIを攻略
  - カントー認定章8個とカントーリーグを攻略
  - 各世代の伝説アーク・スフィアいせきを進める
  - リーグII・スフィア完了・カントーリーグ完了後に最終リーグへ
  - 最終章のターナー戦へ
- 次の行先・解禁: Factory Master、UB・パラドックス研究、最終伝説イベント、全国収集完成
- Stage61 QOL解禁: 経験アメXL初回分
- 注意: 固定捕獲イベントはLEGENDARY_ENCOUNTERS.mdで解禁条件・場所・レベル・遭遇時技を検索できる。

## フィールド能力とHM受領時期

Stage61では対応するVega既存HM（Item 339〜346）をバッグに持っていれば使えます。バッジ、手持ち数、その技を覚えたポケモン、適性は要求しません。受領前の順路をHM使用で飛ばせるという意味ではありません。

| HM | 能力 | 受領場所 | 時期 | 根拠状態 |
|---|---|---|---|---|
| HM05 | フラッシュ | 502ばんどうろ北西の男性 | ジム1前 | 受領地点はVega攻略情報、バッグ所持による使用条件はStage61現行仕様 |
| HM03 | なみのり | リムけんきゅうじょ攻略後、システムかいはつしつのカラマツ | ジム3前後 | 受領地点はVega攻略情報、バッグ所持による使用条件はStage61現行仕様 |
| HM06 | いわくだき | D・Hビル4Fのカウンターにいる研究員 | ジム3後、D・Hビル攻略中 | 受領地点はVega攻略情報、バッグ所持による使用条件はStage61現行仕様 |
| HM04 | かいりき | ハクジのもり北西の山男 | ジム4後 | 受領地点はVega攻略情報、バッグ所持による使用条件はStage61現行仕様 |
| HM01 | いあいぎり | ダークタワー6Fで隠れている男性 | ジム5前 | 受領地点はVega攻略情報、バッグ所持による使用条件はStage61現行仕様 |
| HM02 | そらをとぶ | 514ばんどうろの助手 | ジム5後 | 受領地点はVega攻略情報、バッグ所持による使用条件はStage61現行仕様 |
| HM07 | たきのぼり | D・Hだんアジト攻略後、B1Fで取り残された団員 | ジム7後 | 受領地点はVega攻略情報、バッグ所持による使用条件はStage61現行仕様 |
| HM08 | ダイビング | Stage61の現行入力では精密受領地点未確定 | 終盤以降の探索用 | バッグ所持による使用条件と技の対応だけ現行仕様で確定。地点は推測しない |

## Stage61のカントー・終盤解禁グラフ

カントーはジム3＋D・Hビル初回攻略後から任意で入れますが、固定高レベルです。`predecessor_keys`を満たす順に進み、危険なら安全帰還ターミナルからトーホク本編へ戻れます。

| 順 | 解禁key | 地方 | 前提 | 推奨Lv | 必須 | 使用可能ギミック |
|---:|---|---|---|---:|---|---|
| 0 | `VEGA_PRE_ENTRY` | TOHOKU | `NONE` | 1-12 | 必須 | NONE |
| 10 | `VEGA_BADGE_1` | TOHOKU | `VEGA_PRE_ENTRY` | 12-25 | 必須 | NONE |
| 20 | `VEGA_DAYCARE_FIRST` | TOHOKU | `VEGA_BADGE_1` | 18-32 | 任意 | NONE |
| 30 | `VEGA_BADGE_2` | TOHOKU | `VEGA_BADGE_1` | 24-38 | 必須 | NONE |
| 40 | `VEGA_SHIOU_BADGE_3` | TOHOKU | `VEGA_BADGE_2` | 32-48 | 必須 | NONE |
| 50 | `VEGA_DH_CLEAR` | TOHOKU | `VEGA_SHIOU_BADGE_3` | 42-58 | 必須 | NONE |
| 55 | `KANTO_EARLY_ACCESS` | KANTO | `VEGA_DH_CLEAR` | 68-78 | 任意 | NONE |
| 56 | `KANTO_DAYCARE_QUEST` | KANTO | `KANTO_EARLY_ACCESS` | 68-80 | 任意 | NONE |
| 56 | `KANTO_CERT_1` | KANTO | `KANTO_EARLY_ACCESS` | 78-80 | 任意 | NONE |
| 57 | `KANTO_CERT_2` | KANTO | `KANTO_CERT_1` | 81-83 | 任意 | NONE |
| 58 | `KANTO_CERT_3` | KANTO | `KANTO_CERT_2` | 84-86 | 任意 | NONE |
| 59 | `KANTO_CERT_4` | KANTO | `KANTO_CERT_3` | 87-89 | 任意 | NONE |
| 60 | `VEGA_BADGE_5` | TOHOKU | `VEGA_DH_CLEAR` | 48-64 | 必須 | NONE |
| 61 | `FACTORY_STANDARD` | TOHOKU | `VEGA_BADGE_5` | 50-68 | 任意 | NONE |
| 70 | `VEGA_BADGE_6` | TOHOKU | `VEGA_BADGE_5` | 54-70 | 必須 | NONE |
| 80 | `VEGA_BADGE_7` | TOHOKU | `VEGA_BADGE_6` | 58-74 | 必須 | NONE |
| 90 | `VEGA_BADGE_8` | TOHOKU | `VEGA_BADGE_7` | 62-78 | 必須 | NONE |
| 100 | `VEGA_HALL_OF_FAME` | TOHOKU | `VEGA_BADGE_8` | 70-85 | 必須 | MEGA |
| 101 | `LEAGUE_I_AVAILABLE` | TOHOKU | `VEGA_HALL_OF_FAME` | 84-90 | 任意 | NONE |
| 102 | `LEAGUE_I_CLEARED` | TOHOKU | `LEAGUE_I_AVAILABLE` | 84-90 | 任意 | NONE |
| 103 | `RESEARCH_PROFILE_UNLOCKED` | TOHOKU | `VEGA_HALL_OF_FAME` | 70-100 | 任意 | NONE |
| 104 | `TM_LICENSE_UNLOCKED` | TOHOKU | `VEGA_HALL_OF_FAME` | 70-100 | 任意 | NONE |
| 105 | `HIDDEN_ABILITY_DEXNAV_UNLOCKED` | TOHOKU | `VEGA_HALL_OF_FAME` | 70-100 | 任意 | NONE |
| 106 | `FACTORY_FULL` | TOHOKU | `VEGA_HALL_OF_FAME` | 72-100 | 任意 | MEGA |
| 110 | `KANTO_CERT_5` | KANTO | `KANTO_CERT_4|VEGA_HALL_OF_FAME` | 90-92 | 任意 | MEGA\|Z |
| 120 | `KANTO_CERT_6` | KANTO | `KANTO_CERT_5` | 93-95 | 任意 | MEGA\|Z |
| 130 | `KANTO_CERT_7` | KANTO | `KANTO_CERT_6` | 96-98 | 任意 | MEGA\|Z |
| 140 | `KANTO_CERT_8` | KANTO | `KANTO_CERT_7` | 98-100 | 任意 | MEGA\|Z |
| 141 | `LEAGUE_II_AVAILABLE` | TOHOKU | `KANTO_CERT_4|VEGA_HALL_OF_FAME|LEAGUE_I_CLEARED` | 92-96 | 任意 | MEGA\|Z |
| 142 | `LEAGUE_II_CLEARED` | TOHOKU | `LEAGUE_II_AVAILABLE` | 92-96 | 任意 | MEGA\|Z |
| 143 | `COMPETITIVE_SUPPLY_UNLOCKED` | KANTO | `KANTO_CERT_4|VEGA_HALL_OF_FAME` | 90-100 | 任意 | MEGA\|Z |
| 144 | `RAID_HIGH_UNLOCKED` | KANTO | `KANTO_CERT_4|VEGA_HALL_OF_FAME` | 85-100 | 任意 | RAID_DYNAMAX |
| 150 | `KANTO_LEAGUE` | KANTO | `KANTO_CERT_8|VEGA_HALL_OF_FAME` | 94-100 | 任意 | MEGA\|Z |
| 160 | `KANTO_LEAGUE_CLEAR` | KANTO | `KANTO_LEAGUE` | 100-100 | 任意 | MEGA\|Z\|TERA\|DYNAMAX |
| 161 | `FACTORY_MASTER` | KANTO | `KANTO_LEAGUE_CLEAR` | 94-100 | 任意 | MEGA\|Z\|TERA\|DYNAMAX |
| 162 | `UB_PARADOX_UNLOCKED` | KANTO | `KANTO_LEAGUE_CLEAR` | 94-100 | 任意 | MEGA\|Z\|TERA\|DYNAMAX |
| 163 | `SPHERE_COMPLETE` | KANTO | `KANTO_LEAGUE_CLEAR` | 100-100 | 任意 | MEGA\|Z\|TERA\|DYNAMAX |
| 170 | `FINAL_LEAGUE_AVAILABLE` | KANTO | `KANTO_LEAGUE_CLEAR|SPHERE_COMPLETE|LEAGUE_II_CLEARED` | 100-100 | 任意 | MEGA\|Z\|TERA\|DYNAMAX |
| 171 | `FINAL_LEAGUE_CLEARED` | KANTO | `FINAL_LEAGUE_AVAILABLE` | 100-100 | 任意 | MEGA\|Z\|TERA\|DYNAMAX |

## カントー論理マップ対応表

固定捕獲・野生遭遇で使うK01〜K47を、現行ROMの代表物理マップ名と解禁keyへ対応づけます。同じ論理コードに複数階・複数区画が属する場合、表は代表マップを示します。

| 論理コード | 代表マップ | 物理map key | 解禁 | 種別 | Field PC |
|---|---|---|---|---|---|
| <a id="kanto-map-k01"></a>`K01` | 1ばん どうろ | `KANTO_OUTDOOR_ROUTE1` | `KANTO_EARLY_ACCESS` | ROUTE | 可 |
| <a id="kanto-map-k02"></a>`K02` | 2ばん どうろ | `KANTO_OUTDOOR_ROUTE2` | `KANTO_EARLY_ACCESS` | ROUTE | 可 |
| <a id="kanto-map-k03"></a>`K03` | 3ばん どうろ | `KANTO_OUTDOOR_ROUTE3` | `KANTO_EARLY_ACCESS` | ROUTE | 可 |
| <a id="kanto-map-k04"></a>`K04` | 4ばん どうろ | `KANTO_OUTDOOR_ROUTE4` | `KANTO_EARLY_ACCESS` | ROUTE | 可 |
| <a id="kanto-map-k05"></a>`K05` | 5ばん どうろ | `KANTO_OUTDOOR_ROUTE5` | `KANTO_EARLY_ACCESS` | ROUTE | 可 |
| <a id="kanto-map-k06"></a>`K06` | 6ばん どうろ | `KANTO_OUTDOOR_ROUTE6` | `KANTO_EARLY_ACCESS` | ROUTE | 可 |
| <a id="kanto-map-k07"></a>`K07` | 7ばん どうろ | `KANTO_OUTDOOR_ROUTE7` | `KANTO_CERT_1` | ROUTE | 可 |
| <a id="kanto-map-k08"></a>`K08` | 8ばん どうろ | `KANTO_OUTDOOR_ROUTE8` | `KANTO_CERT_1` | ROUTE | 可 |
| <a id="kanto-map-k09"></a>`K09` | 9ばん どうろ | `KANTO_OUTDOOR_ROUTE9` | `KANTO_EARLY_ACCESS` | ROUTE | 可 |
| <a id="kanto-map-k10"></a>`K10` | 10ばん どうろ | `KANTO_OUTDOOR_ROUTE10` | `KANTO_CERT_1` | ROUTE | 可 |
| <a id="kanto-map-k11"></a>`K11` | 11ばん どうろ | `KANTO_OUTDOOR_ROUTE11` | `KANTO_EARLY_ACCESS` | ROUTE | 可 |
| <a id="kanto-map-k12"></a>`K12` | 12ばん どうろ | `KANTO_OUTDOOR_ROUTE12` | `KANTO_CERT_2` | ROUTE | 可 |
| <a id="kanto-map-k13"></a>`K13` | 13ばん どうろ | `KANTO_OUTDOOR_ROUTE13` | `KANTO_CERT_2` | ROUTE | 可 |
| <a id="kanto-map-k14"></a>`K14` | 14ばん どうろ | `KANTO_OUTDOOR_ROUTE14` | `KANTO_CERT_3` | ROUTE | 可 |
| <a id="kanto-map-k15"></a>`K15` | 15ばん どうろ | `KANTO_OUTDOOR_ROUTE15` | `KANTO_CERT_3` | ROUTE | 可 |
| <a id="kanto-map-k16"></a>`K16` | 16ばん どうろ | `KANTO_OUTDOOR_ROUTE16` | `KANTO_CERT_2` | ROUTE | 可 |
| <a id="kanto-map-k17"></a>`K17` | 17ばん どうろ | `KANTO_OUTDOOR_ROUTE17` | `KANTO_CERT_2` | ROUTE | 可 |
| <a id="kanto-map-k18"></a>`K18` | 18ばん どうろ | `KANTO_OUTDOOR_ROUTE18` | `KANTO_CERT_3` | ROUTE | 可 |
| <a id="kanto-map-k19"></a>`K19` | 19ばん すいどう | `KANTO_OUTDOOR_ROUTE19` | `KANTO_CERT_4` | ROUTE | 可 |
| <a id="kanto-map-k20"></a>`K20` | 20ばん すいどう | `KANTO_OUTDOOR_ROUTE20` | `KANTO_CERT_4` | ROUTE | 可 |
| <a id="kanto-map-k21"></a>`K21` | 21ばん すいどう | `KANTO_OUTDOOR_ROUTE21_NORTH` | `KANTO_CERT_4` | ROUTE | 可 |
| <a id="kanto-map-k22"></a>`K22` | 22ばん どうろ | `KANTO_OUTDOOR_ROUTE22` | `KANTO_CERT_5` | ROUTE | 可 |
| <a id="kanto-map-k23"></a>`K23` | 23ばん どうろ | `KANTO_OUTDOOR_ROUTE23` | `KANTO_CERT_5` | ROUTE | 可 |
| <a id="kanto-map-k24"></a>`K24` | 24ばん どうろ | `KANTO_OUTDOOR_ROUTE24` | `KANTO_EARLY_ACCESS` | ROUTE | 可 |
| <a id="kanto-map-k25"></a>`K25` | 25ばん どうろ | `KANTO_OUTDOOR_ROUTE25` | `KANTO_EARLY_ACCESS` | ROUTE | 可 |
| <a id="kanto-map-k26"></a>`K26` | トキワのもり | `KANTO_DUNGEON_VIRIDIAN_FOREST` | `KANTO_EARLY_ACCESS` | DUNGEON | 不可 |
| <a id="kanto-map-k27"></a>`K27` | オツキミやま | `KANTO_DUNGEON_MT_MOON_1_F` | `KANTO_EARLY_ACCESS` | DUNGEON | 不可 |
| <a id="kanto-map-k28"></a>`K28` | ディグダのあな | `KANTO_DUNGEON_DIGLETTS_CAVE_NORTH_ENTRANCE` | `KANTO_EARLY_ACCESS` | DUNGEON | 不可 |
| <a id="kanto-map-k29"></a>`K29` | サント・アンヌごう | `KANTO_DUNGEON_SSANNE_EXTERIOR` | `KANTO_CERT_1` | ROUTE | 可 |
| <a id="kanto-map-k30"></a>`K30` | イワヤマトンネル | `KANTO_DUNGEON_ROCK_TUNNEL_1_F` | `KANTO_CERT_1` | DUNGEON | 不可 |
| <a id="kanto-map-k31"></a>`K31` | ポケモンタワー | `KANTO_DUNGEON_POKEMON_TOWER_1_F` | `KANTO_CERT_2` | DUNGEON | 不可 |
| <a id="kanto-map-k32"></a>`K32` | ロケットだんアジト | `KANTO_DUNGEON_ROCKET_HIDEOUT_B1_F` | `KANTO_CERT_2` | DUNGEON | 不可 |
| <a id="kanto-map-k33"></a>`K33` | タマムシシティ | `KANTO_OUTDOOR_CELADON_CITY` | `KANTO_CERT_2` | ROUTE | 可 |
| <a id="kanto-map-k34"></a>`K34` | セキチクシティ | `KANTO_OUTDOOR_FUCHSIA_CITY` | `KANTO_CERT_3` | ROUTE | 可 |
| <a id="kanto-map-k35"></a>`K35` | サファリゾーン | `KANTO_DUNGEON_SAFARI_ZONE_EAST` | `KANTO_CERT_3` | ROUTE | 可 |
| <a id="kanto-map-k36"></a>`K36` | サファリゾーン | `KANTO_DUNGEON_SAFARI_ZONE_NORTH` | `KANTO_CERT_3` | ROUTE | 可 |
| <a id="kanto-map-k37"></a>`K37` | サファリゾーン | `KANTO_DUNGEON_SAFARI_ZONE_WEST` | `KANTO_CERT_3` | ROUTE | 可 |
| <a id="kanto-map-k38"></a>`K38` | ふたごじま | `KANTO_DUNGEON_SEAFOAM_ISLANDS_1_F` | `KANTO_CERT_4` | ROUTE | 可 |
| <a id="kanto-map-k39"></a>`K39` | ポケモンやしき | `KANTO_DUNGEON_POKEMON_MANSION_1_F` | `KANTO_CERT_5` | DUNGEON | 不可 |
| <a id="kanto-map-k40"></a>`K40` | むじんはつでんしょ | `KANTO_DUNGEON_POWER_PLANT` | `KANTO_CERT_2` | DUNGEON | 不可 |
| <a id="kanto-map-k41"></a>`K41` | シルフカンパニー | `KANTO_DUNGEON_SILPH_CO_1_F` | `KANTO_CERT_5` | DUNGEON | 不可 |
| <a id="kanto-map-k42"></a>`K42` | チャンピオンロード | `KANTO_DUNGEON_VICTORY_ROAD_1_F` | `KANTO_LEAGUE` | LEAGUE | 不可 |
| <a id="kanto-map-k43"></a>`K43` | ハナダのどうくつ | `KANTO_DUNGEON_CERULEAN_CAVE_1_F` | `KANTO_CERT_6` | DUNGEON | 不可 |
| <a id="kanto-map-k44"></a>`K44` | ニビシティ | `KANTO_OUTDOOR_PEWTER_CITY` | `KANTO_EARLY_ACCESS` | EVENT | 不可 |
| <a id="kanto-map-k45"></a>`K45` | グレンじま | `KANTO_OUTDOOR_CINNABAR_ISLAND` | `KANTO_EARLY_ACCESS` | TOWN | 可 |
| <a id="kanto-map-k46"></a>`K46` | クチバシティ | `KANTO_OUTDOOR_VERMILION_CITY` | `KANTO_EARLY_ACCESS` | TOWN | 可 |
| <a id="kanto-map-k47"></a>`K47` | マサラタウン | `KANTO_OUTDOOR_PALLET_TOWN` | `KANTO_EARLY_ACCESS` | TOWN | 可 |

## 出典境界

- トーホクの道順・HM01〜07受領地点: [既存Vega攻略チャート](https://w.atwiki.jp/np369/pages/58.html) / [既存Vegaアイテム表](https://w.atwiki.jp/altair0/pages/664.html)
- ボスの現行レベル・手持ち・技: Stage61 trainer final正本（[主要戦一覧](MAJOR_BATTLES.md)）
- カントー・QOL・フィールド能力: Stage61統合済み正本
- HM08の精密受領地点など、現行入力で確定できないものは推測していません。
