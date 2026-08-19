# ChatGPT返却物の契約

## 返却ZIP

ZIP名:

```text
Pokemon-Vega_EVENT-DESIGN_IMPLEMENTATION-READY.zip
```

ZIP直下には次の6ファイルだけを置きます。余分な親directoryは作りません。

```text
EVENT_BIBLE_JA.md
event_plan.json
dialogue.csv
coverage.csv
OPEN_QUESTIONS.md
VALIDATION_REPORT.json
```

## ファイルの役割

### EVENT_BIBLE_JA.md

人が読む物語正本です。少なくとも次を含めます。

- 一文のconcept
- main arcの開始・前半完結・後半再開・最終完結
- 主要actor一覧と口調
- 8認定章・League・Final Leagueとの関係
- sidequest一覧
- 町・道路・ダンジョンのcontent方針
- QOL解禁を世界観へなじませる方針
- implementation batch順

ここにだけ存在するeventやstateを作らず、すべて`event_plan.json`と一致させます。

### event_plan.json

実装正本です。`schemas/event_plan.schema.json`に完全一致させます。

- `design_status` は `IMPLEMENTATION_READY`
- `open_questions` は空配列
- `arcs`, `states`, `actors`, `placements`, `conditions`, `rewards`, `events`, `batches` の全cross-referenceを解決
- eventのstep graphは到達不能stepや終了しないcycleを作らない
- acceptance testは最低でもunlock前、正常完了、再訪、save/reload、主要failureを扱う

### dialogue.csv

headerは固定です。

```text
dialogue_key,event_key,speaker_actor_key,usage,text,next_step_key,notes
```

text内の改行はliteral `\n`です。物理的な改行をCSV cellへ入れません。

### coverage.csv

headerは固定です。

```text
coverage_key,subject_kind,subject_key,coverage_status,event_keys,rationale
```

次を漏れなく1行ずつ記録します。

- `LOGICAL_LOCATION`: K01〜K47
- `QOL_FEATURE`: catalogsの全feature key
- `PROGRESSION_GATE`: catalogsで`event_coverage_required=true`の全unlock key

`event_keys`は`|`区切りです。追加eventが不要なら`EXISTING_CONTENT`、`AUTO_UNLOCK`、`NO_EVENT_JUSTIFIED`のいずれかを使い、理由を具体的に書きます。

### OPEN_QUESTIONS.md

完成時は次の内容だけにします。

```text
# Open questions

なし。実装に必要な判断はevent_plan.jsonのassumptionsへ記録済み。
```

### VALIDATION_REPORT.json

同梱validatorが生成します。手編集しません。

## 作成と検証

`submission_template/`を複製して`submission/`を作り、内容を置き換えます。

```bash
python tools/validate_submission.py submission --report submission/VALIDATION_REPORT.json
```

終了code 0、`status=PASS`、error 0、open_questions 0を確認してから、`submission/`直下の6ファイルだけをZIPへ格納します。
