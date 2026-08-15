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
- Reproduction: 旧ROMで作ったsavestateをv1.3.6で直接読み込む。
- Result: ROM内部addressや一時stateが一致せず、安全なmigration対象にならない。
- Workaround: 旧ROM上でゲーム内saveを行い、v1.3.6を再起動してbattery saveから読む。

### KI-004 — V4の性格・特性・EV・gimmick triggerは設計台帳のみ

- Severity: S4 / intentional ABI scope
- Reproduction: V4設計CSVの性格・特性・EV欄と通常trainer戦の生成個体を比較する。
- Result: Species、level、持ち物、4技、IV下限、trainer item、AI段階は反映されるが、通常の
  16-byte TrainerMon ABIに欄のない性格・特性・EV・個別gimmick triggerは直接固定されない。
- Workaround: 現行CFRUの個体生成規則と1戦1gimmick policyを使用する。値は正規化台帳に保持済み。

### KI-005 — Factoryの実受付はTrialのみ

- Severity: S4 / release scope exclusion
- Reproduction: クチバのFactory受付でStandard、Full、Master、BP shop、施設外報酬遭遇を探す。
- Result: v1.3.6の実ROM受付は候補6体から3体を選ぶTrial 3連戦だけを提供する。後続modeと
  shop/報酬遭遇はmanifest・進行定義・回帰fixtureのみで、NPCからは開始できない。
- Workaround: Trialを利用する。未接続modeを実装済みと扱わず、後続releaseで個別に結合する。

### KI-006 — トーホク外来生態の専用遭遇方式は未接続

- Severity: S4 / release scope exclusion
- Reproduction: 夜間、大量発生、ずつき、釣り、DexNav専用と指定された新種を該当mapで探す。
- Result: v1.3.6で実ROM接続済みなのは設計293行中153行（草むら77、洞窟・屋内31、
  水上23、いわくだき22）のmap別追加抽選。140行の専用方式とevent別解禁条件は
  runtime未接続。通常追加抽選は対象mapで常時有効としている。
- Workaround: 通常の草むら・洞窟・水上・いわくだきの追加種を利用する。専用方式を
  実装済みと扱わない。

## v1.3.6で解決済み

- 追加Speciesを含むtrainer戦が戦闘開始時に黒画面のまま停止する初期技表ABI不一致。
- 最初の草むら（map 3/19）が別の論理地点へ誤結合され、追加種が出現しない問題。
- 戦闘中Lの旧HELP競合が技Type・特性通知・行動順を破損した問題。

Release-blocking known issue: **none**.
