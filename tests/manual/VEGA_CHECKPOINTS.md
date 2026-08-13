# Vega release checkpoint matrix

- Version: 1
- Task: T17
- 自動列はrelease buildで毎回実行する。手動列は実機/エミュレータでの表示・操作感確認用であり、save-stateを互換判定に使わない。

| Checkpoint | 自動証跡 | 手動確認 |
|---|---|---|
| 新規開始 | mGBA自然入力traceでtitle→field | 名前入力、最初の移動、menu表示 |
| 序盤 | T06/T10 battle・save fixture | 最初のbadgeまでの会話・戦闘・保存 |
| 中盤解禁直前 | early flags=falseで渡航拒否 | 研究員NPCの拒否文 |
| シオウ3個目badge＋D・H攻略後 | early flags=trueで渡航可 | 警告・Yes/No・往復 |
| 殿堂入り直前/直後 | HOF OR early flags matrix | 本編最終戦、credits、再読込 |
| カントー訪問を無視 | Vega flag/HM不変model | Vega本編を通常順で完走 |
| カントー訪問後 | 400往復・save操作model | 帰還後にVega本編を完走 |
| 育成/QOL | QOL-A/B fixture | PC、孵化、アメ、全体学習、既定即時文章 |

## 合格条件

全行で進行不能、Vega story/HM flagの早期解禁、個体・道具の複製/消失、save破損がないこと。異常時はROMとゲーム内saveを保持せず、再現手順だけを `KNOWN_ISSUES.md` へ記録する。
