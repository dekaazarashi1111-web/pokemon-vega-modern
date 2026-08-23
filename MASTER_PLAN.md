# マスタープラン

## 完成像

```text
FireRed JPN Rev0 clean
  └─ Vega 2018-02-23
      └─ Vega互換DPE-JP
          └─ Vega互換CFRU-JP
              └─ Modern breeding / training / speed QoL
                  └─ Early-access / post-HoF Kanto maps
                      └─ Tohoku/Kanto symbolic ecology manifests
                          └─ final 32 MiB ROM
                              └─ 配布用差分パッチ
```

## フェーズ

| ID | タスク | 主レーン | 依存 | ゴール |
|---|---|---|---|---|
| T00 | Bootstrap | Platform | — | 入力検証・source pin・参照ROM |
| T01 | Upstream reproducibility | Engine | T00 | DPE/CFRUビルド環境を再現 |
| T02 | Exact address audit | QA | T00 | ROM/RAM/save/ID競合を機械化 |
| T03 | Rebuildable Vega harness | Engine | T01,T02 | clean→Vega→moduleの再現ビルド |
| T04 | Move ID port | Engine | T03 | Vega技ID固定でCFRU技系統合 |
| T05 | Type/Ability/Item IDs | Engine | T03,T02 | 拡張ID空間と生成header |
| T06 | CFRU battle core | Engine | T04,T05 | 戦闘コアをVega上で起動 |
| T07 | DPE Species port | Engine | T04,T05,T03 | Vega species固定＋追加species |
| T08 | Save/RAM compatibility | QA/Engine | T02,T03 | save/RAM衝突解消 |
| T09 | Graphics/Dex/Evolution | Engine | T07,T08 | 表示・図鑑・進化・習得技 |
| T10 | Engine/QOL vertical slice | Engine/QA | T04–T09 | 新要素、現代育成、高速操作、PC QOL、トーホク非破壊overlayを通しで動作 |
| T11 | Kanto importer | Map | T00,T02 | FR本土inventory、1マップround-trip、新Map ID |
| T12 | Dual-region content schema | Content | T00 | 二地方の野生/トレーナー/アイテム/イベント仕様 |
| T13 | Early Kanto vertical slice | Map/Content | T10,T11,T12 | 本編中盤の港→クチバ→安全帰還 |
| T14 | Full Kanto import | Map | T11,T13 | 選定マップと接続を一括追加 |
| T15 | Dual-phase Kanto progression | Content/Engine | T13,T14 | 早期解禁・認定章・殿堂入り後進行 |
| T16 | Populate dual-region content | Content | T12,T14,T15 | トーホク49＋カントー47論理地点を生成 |
| T17 | QOL-B + Regression/playtest | QA/Engine | T10,T13,T16 | 高度PC/自動戦闘を統合しVega本編＋二地方回帰確認 |
| T18 | Release pipeline | Platform | T17 | 再現ビルド・差分パッチ・記録 |
| T19 | Production QOL completion | Engine/UI/Save/QA | T18 | 35機能を実UI・field・PC・預かり屋・battle・saveへ接続 |
| T20 | Event design implementation | Maps/Content/Engine/Save/QA | T19 | 実装可能設計76件をStage 36にrebaseし、実map event・会話・進行・serviceへ接続 |
| T21 | Mirage production runtime | Maps/Content/Engine/Save/QA | T20 | 設計済みMirage 4周を既存map・持込party・仮想item・独立記録へproduction接続 |
| T22 | Move Distribution V4 | Engine/Content/QA | T21 | 返却済み全習得表・form・野生初期技をStage 39へproduction統合 |
| T23 | Research Economy V1 | Content/Engine/Save/Maps/QA | T22 | 独立研究通貨・6活動・7 rank・23 shopをStage 40へproduction統合 |
| T24 | Reward Encounters V2 | Content/Engine/Save/Maps/QA | T23 | 4 tier・typed credit・pending再戦・24 encounterをStage 41へproduction統合 |
| T25 | Factory High Modes V2 | Content/Engine/Save/UI/QA | T24 | 既存Trialを保って24 Factory modeをStage 42へproduction統合 |
| T26 | Codex Battle Bridge | Platform/Tooling/Engine/QA | T25 | iPad RetroArch NCIとversioned mailboxをStage 43で実証 |
| T27 | Codex Battle Runtime | Engine/UI/Content/Tooling/QA | T26 | 構築catalog、双方6体提示・3体選出、公平な非公開commit、自由gimmick、Codex行動をStage 44へproduction統合 |
| T28 | Codex Rewards and iPad Gate | Engine/Save/Tooling/Release/QA | T27 | 任意item/Pokémon報酬とiPad対戦E2EをStage 45で完成 |
| T29 | Windows Battle Catalog | Engine/Save/Tooling/QA | T28 | NPC前IDLEでcanonical templateを通常収納へ一括生成するStage 46を完成 |
| T30 | Windows Box 14 Vault | Engine/Save/Tooling/QA | T29 | Box 14とWindows owner-only個体庫の双方向exact移動をStage 47で完成 |

## 最短実行戦略

実際の二地方往復であるT13へ最短で到達する主経路は次です。T02→T11とT00→T12はEngine主経路と並行準備します。

```text
T01 + T02
  -> T03
  -> T04 / T05 / T08
  -> T06 / T07
  -> T09
  -> T10
  -> T13

並行枝:
T02 -> T11 ----┐
T00 -> T12 ----┴-> T13
```

`make plan` はDAGから現在の `RESUME` / 推奨 `PRIMARY` / その他の依存READY候補 `PARALLEL_PREP` と準備waveを自動導出します。正本IN_PROGRESSは1件だけとし、同じwaveの他タスクは所有ファイルを分けたsubtaskまたは別worktreeで先行します。準備waveは依存深度を表す論理並列単位であり、正本完了のbarrierや強制統合順ではありません。

正本の既定優先順は `design/tasks_next.md` の `T01 → T02 → T03 → … → T30` です。これは強制順ではないが、返却4設計はshared table/save/hookを安全に継承するため `T22 → T23 → T24 → T25`、Codex対戦・Windowsカタログ・Box 14固有個体庫はtransport/battle/save/toolingを分離するため `T26 → T27 → T28 → T29 → T30` の依存順を固定する。W1開始時はT01を推奨PRIMARY、T02とT12をREADY候補とし、進行後の現在値は `make plan` と `design/current_state.md` を正とする。

## 高速並列準備waveと統合時の成果基準

| Wave | 論理並列準備 | 各タスクをPRIMARY統合する際の成果基準 |
|---|---|---|
| W0 | T00 | 入力hash、参照ROM、上流commit、初期監査が固定済み（完了） |
| W1 | T01 / T02 / T12 | 上流2構成の再現build、全固定write・RAM/save/ID・早期解禁flagの証拠化、symbolic schemaとV2正規化検査 |
| W2 | T03 / T11 | clean→Vega→32 MiB no-op ROMが再現・boot/saveし、Kanto 1 mapが新IDでround-tripする |
| W3 | T04 / T05 / T08 | Vega ID固定、生成ID空間、RAM/save衝突解消、地方別stateが成立し、旧saveは移行成功または安全な明示拒否になる |
| W4 | T06 / T07 | CFRU基本戦闘が完走し、Vega Species IDを維持した追加Speciesをpartyへ生成できる |
| W5 | T09 | 追加Speciesの画像、鳴き声、図鑑、進化、習得技、saveが一通り動く |
| W6 | T10 | 追加技・特性・道具・Species・進化とQOL-Aを1セーブで完走し、Vega回帰とoverlay fallbackがPASSする |
| W7 | T13 | 殿堂入り前の港→クチバ→save/全滅→無料帰還が安全に動く（Gate D） |
| W8 | T14 | 採用Kanto全physical mapの接続、到達性、ID衝突検査がPASSする |
| W9 | T15 | 早期層とpost-HoF層の進行DAGが完成し、循環・帰還不能・Vega flag汚染が0になる |
| W10 | T16 | 49+47論理地点、541系統、125共有捕獲stateを生成配置し、全参照が解決する |
| W11 | T17 | QOL-B統合、新規saveと旧save方針、Kanto訪問あり/なしのVega完走、往復・長時間回帰がPASSする |
| W12 | T18 | clean checkoutからbyte再現buildでき、配布patch再適用hashとprivate guardがPASSする |
| W13 | T19 | 35/35 release QOLがproduction bindingを持ち、実入力・save/reload・clean Stage 36をPASSする |
| W14 | T20 | 76 event・63 placement・326会話をStage 36へ再解決し、実入力・保存・回帰・clean Stage 37をPASSする |
| W15 | T21 | Mirage 7戦×4周を既存mapへ接続し、持込party・gimmick・仮想item・記録・全cleanup・clean Stage 38をPASSする |
| W16 | T22 | 全習得表・TM/tutor追加・form・新規野生初期技を実consumerへ接続し、clean Stage 39をPASSする |
| W17 | T23 | 研究通貨・6活動・7 rank・23 shop・save migrationを通常入口へ接続し、clean Stage 40をPASSする |
| W18 | T24 | 4 tier・24 pool・typed credit/BP・pending同一個体再戦・10 sourceを接続し、clean Stage 41をPASSする |
| W19 | T25 | 24 mode・248 rental・55 profile・16 rewardを既存Trial不変で接続し、clean Stage 42をPASSする |
| W20 | T26 | iPad RetroArch NCIの実memory read/write、versioned mailbox、CLI doctor/PING、clean Stage 43をPASSする |
| W21 | T27 | catalog、双方6→3選出、2 regulation、`UPSTREAM_OPEN` gimmick、pending action非公開、Codex move/switch/forfeit、全cleanup、clean Stage 44をPASSする |
| W22 | T28 | 任意item/Pokémon報酬、exactly-once save、Codex skill、iPad E2E、clean Stage 45をPASSする |
| W23 | T29 | NPC前Windows catalog、1件単位batch停止・再開、通常収納、Stage45/報酬/PC回帰、Stage 46をPASSする |
| W24 | T30 | Box 14全枠の固有個体export/import、Windows原子的在庫、移動確定後だけの削除、Stage 47をPASSする |

最初のEngine動作成果はT03の「32 MiB no-op Vega ROM」です。T11の「独立したKanto 1-map importer検証」はT02後に先行でき、依存READYになった時点で正本へ選択・統合できます。最初の製品経路としての二地方往復はT13、配布可能候補はT18、QOL production completionはT19、イベント設計統合はT20、Mirage production接続はT21。返却済み4設計はT22〜T25でStage 38から順次rebaseしてStage 42を完成点とし、Codex対戦・Windowsカタログ・Box 14固有個体庫はT26〜T30でStage 47まで段階統合する。

受領したV2二地方生態版は完成像・進行・生態・イベントのactive review資料です。V1は来歴保存専用です。V2の47カントー地点はraw map総数ではないため、T11ではclean BPRJとpokefireredから約256候補mapの再現可能なinventoryを作り、論理地点とのcrosswalkを確定します。採用済みデータだけをT12/T16のschemaへ昇格します。

追加UIと新規event演出はcritical pathにしません。QOLは既存画面のcompact切替/標準menu、追加eventは `SIMPLE_EVENT` の短い会話・flag・rewardを既定とし、機能・二地方統合・回帰へ工数を集中します。

## ボトルネック優先順位

1. T01/T02: 現在不足するtoolchainを固定するT01と、T03/T05/T08/T11を解放する最大fan-outのT02を共同最優先にする。T02はUNKNOWN、実write span、早期解禁flagを曖昧なまま後続へ渡さない。
2. T03/T06: no-op harnessとCFRU hook移植。カテゴリ別test ROMで壊れた最初の境界を特定する。
3. T08/T10: save互換・地方別anchorに加え、育成stateと設定を先に固定し、現代孵化・高速操作・PC QOLを最小fixtureで通してからcontentを広げる。
4. T11/T14: 約256候補physical map、日本版差異、signed Map IDをimporter/validatorで吸収する。
5. T13: Engine/Maps/Content最初の統合点。ここまでのinterfaceをfreezeしてから全mapへ広げる。
6. T16/T17: データ量と手動確認が支配的になるため、schema validatorとsave fixtureをW1から前倒しする。

## 重要ゲート

### Gate A — 再現可能な参照ビルド

- clean ROM hash一致
- Vega reference生成
- Factory reference生成
- pinned source記録

### Gate B — No-op module boot

Vegaへ拡張領域を追加してもタイトル、ニューゲーム、セーブが壊れない。

### Gate C — Battle vertical slice

Vega既存技と追加技、新特性、新Species、追加道具が1つずつ動作する。加えて `docs/QOL_POLICY.md` のQOL-A、即時文章、ダッシュ・自転車高速化が1つの継続saveで動作する。QOL-BはT13を待たせずT17の全回帰前に統合する。

### Gate D — Kanto vertical slice

Vegaのシオウ3個目バッジ取得後・アーシア島D・Hビル攻略後の安全な実flagでカントーを恒久解禁する。殿堂入り前saveからクチバへ移動し、推奨Lv.65警告、NPC、PC/回復、セーブ、全滅復帰、強制戦闘なしの常時帰還が動作する。ジムは必要認定章のtest fixtureで別検証する。

### Gate E — Release candidate

再現ビルド、静的検査、主要手動チェック、配布用差分パッチ生成が完了する。
