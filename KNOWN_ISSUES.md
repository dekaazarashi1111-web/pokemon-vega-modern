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
- Reproduction: 旧ROMで作ったsavestateをv1.1.0で直接読み込む。
- Result: ROM内部addressや一時stateが一致せず、安全なmigration対象にならない。
- Workaround: 旧ROM上でゲーム内saveを行い、v1.1.0を再起動してbattery saveから読む。

### KI-004 — V4の性格・特性・EV・gimmick triggerは設計台帳のみ

- Severity: S4 / intentional ABI scope
- Reproduction: V4設計CSVの性格・特性・EV欄と通常trainer戦の生成個体を比較する。
- Result: Species、level、持ち物、4技、IV下限、trainer item、AI段階は反映されるが、通常の
  16-byte TrainerMon ABIに欄のない性格・特性・EV・個別gimmick triggerは直接固定されない。
- Workaround: 現行CFRUの個体生成規則と1戦1gimmick policyを使用する。値は正規化台帳に保持済み。

Release-blocking known issue: **none**.
