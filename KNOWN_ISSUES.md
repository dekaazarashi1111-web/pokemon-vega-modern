# Known issues

## Release scope exclusions

### KI-001 — Link multi is not supported

- Severity: S4 / scope exclusion
- Reproduction: Battle Factoryで通信相手を必要とする形式を探す。
- Result: 選択肢へ表示されない。NPC partner multiは利用可能。
- Workaround: single、double、NPC partner multi、randomを使用する。

### KI-002 — Kantoの一部動的warpは安全なクチバ帰還へ置換

- Severity: S4 / intentional compatibility behavior
- Reproduction: Union Room、Trade Center、元FireRedの状態依存elevatorへ入る。
- Result: 未解決runtime destinationではなくクチバの安全地点へ戻る。
- Workaround: 通常の建物・道路warpを使う。進行・帰還は阻害しない。

### KI-003 — emulator savestateはversion間非互換

- Severity: S4 / expected platform behavior
- Reproduction: 旧ROMで作ったsavestateをv1.4.0で直接読み込む。
- Result: ROM内部addressや一時stateが一致せず、安全なmigration対象にならない。
- Workaround: 旧ROM上でゲーム内saveを行い、v1.4.0を再起動してbattery saveから読む。

### KI-004 — V4の性格・特性・EV・gimmick triggerは設計台帳のみ

- Severity: S4 / intentional ABI scope
- Reproduction: V4設計CSVの性格・特性・EV欄と通常trainer戦の生成個体を比較する。
- Result: Species、level、持ち物、4技、IV下限、trainer item、AI段階は反映されるが、通常の
  16-byte TrainerMon ABIに欄のない性格・特性・EV・個別gimmick triggerは直接固定されない。
- Workaround: 現行CFRUの個体生成規則と1戦1gimmick policyを使用する。値は正規化台帳に保持済み。

### KI-005 — Factoryの実受付はTrialのみ

- Severity: S4 / release scope exclusion
- Reproduction: クチバのFactory受付でStandard、Full、Master、施設外報酬遭遇を探す。
- Result: v1.4.0の実ROM受付は候補6体から3体を選ぶTrial 3連戦だけを提供する。post-v1.4.0
  stage 27〜29ではBP shopとTrial初回・連勝・反復報酬を接続済みだが、後続3 modeと
  encounter creditを消費する施設外報酬遭遇はNPCから開始できない。
- Workaround: Trialとpost-release BP shopを利用する。未接続mode／報酬遭遇を実装済みと扱わず、
  後続stageで個別に結合する。

## v1.4.0で解決済み

- コレクション対象1,206種と必須10フォームのうち、通常プレイで到達できる入手経路が
  明示されていなかった不足分。201件の取得イベント、24ホスト、交換進化30経路へ結合した。
- 取得transactionを通常セーブ関数だけで終えると、プロジェクト固有の2 KiB台帳がsector 31へ
  確定されない問題。取得runtimeもFactoryと同じ直接sector書込みを使う。
- PC満杯時のrollbackがCFRUの一時展開BoxPokemonだけを消し、実圧縮boxを戻さない問題。
  `ZeroBoxMonAt`で実slotを戻し、全収納満杯時は書込み前に拒否する。
- タマゴ受取時にSpeciesを登録すると未孵化でも図鑑へ載る問題。受取時はclaimだけを確定し、
  元の孵化script完了後に専用hookで登録・保存する。
- sector 31だけを保存すると取得個体や図鑑が通常saveへ残らない問題。標準saveと台帳保存を
  transaction phaseごとに組み合わせ、通常load後の台帳復元まで実ROMで確認する。

## v1.3.9で解決済み

- canonicalでは6文字あるSpecies名がstock UI互換表とnickname表示処理で5文字へ切られ、
  エースバーンやムゲンダイナの末尾が戦闘HUD・メッセージ等で欠ける問題。

## v1.3.8で解決済み

- 追加Speciesを含むtrainer戦が戦闘開始時に黒画面のまま停止する初期技表ABI不一致。
- 最初の草むら（map 3/19）が別の論理地点へ誤結合され、追加種が出現しない問題。
- 戦闘中Lの旧HELP競合が技Type・特性通知・行動順を破損した問題。
- トーホク外来生態293行のうち、夜・大量発生・朝昼・釣り・DexNav相当140行が
  実ROM未接続だった問題。RTC自動と「せいたいレーダー」の手動切替を併設した。

Release-blocking known issue: **none**.
