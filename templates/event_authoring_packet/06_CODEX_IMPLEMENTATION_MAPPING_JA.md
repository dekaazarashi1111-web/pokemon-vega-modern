# Codex実装への写像

この設計bundleは、後続Codexが物語を再解釈せず、次の順で機械変換できるように作ります。

## 1. ID allocation

- `event_plan.json`のsymbolic keyを正本とする。
- `STATE_KEY_EVENT_*`を中央flag/var allocatorへ渡す。
- numeric ID、ROM address、pointerは設計bundleに保存せず、build時に生成する。
- 同じsymbolic keyは全batchで同じ実体として扱う。

## 2. Physical placement

- `REPOINT_SOURCE_BG`: catalogのbg root indexから既存recordを特定し、script pointerだけを差し替える。
- `RESTORE_SOURCE_OBJECT`: catalogのsource object recordを複製し、local ID、flag、script pointerだけを再割当する。
- `REPOINT_SOURCE_COORD`: catalogのcoord rootを使い、collision/warp到達性をexact auditしてから差し替える。
- `ALLOCATE_SAFE_TILE`: Codexがblock collision、warp、trainer sight、live objectを照合して座標を決める。
- `NO_PHYSICAL_HOST`: unlock hookまたは既存ownerのwrapperへ接続し、objectを増やさない。

同じ`placement_key`を複数eventで共有する場合は、1本のdispatcher scriptからconditionで分岐します。別placementが同じhostを奪う設計はvalidatorが拒否します。

## 3. Script compile

各eventの`steps`を先頭からsymbolic label付きfield scriptへ変換します。

| op | 実装先 |
|---|---|
| `SHOW_DIALOGUE` | encoded message + messagebox |
| `CHECK_CONDITION` | condition tableを短絡評価するwrapper |
| `YES_NO` | yes/no prompt + 2 branch |
| `SET_STATE` | generated flag/var write |
| `GIVE_REWARD` | capacity precheck後に既存item API、成功後commit |
| `START_TRAINER_BATTLE` | existing encounter consumer |
| `CALL_ACQUISITION_HOST` | existing acquisition transaction wrapper |
| `OPEN_SERVICE` | existing service entry |
| `HEAL_PARTY` | stock heal transaction |
| `WARP_SAFE` | progression catalogのsafe route |
| `END` | release/end |

`condition_key`は共通condition tableへ一度だけcompileします。event固有の判定を文章から推測して追加しません。

## 4. Text compile

- `dialogue.csv`を`game_charmap.json`でencodeする。
- rowごとにmessage symbolを生成し、`next_step_key`をscript graphと照合する。
- 表示名と台詞の幅を再検査する。
- 原文はUTF-8正本として残し、ROM側にはencoded bytesだけを置く。

## 5. Batch implementation

- `batches[].depends_on`のtopological順で実装する。
- 1 batchを1 generator input、1 focused test群、1 commit、1 rollback boundaryとして扱う。
- 最初の`BATCH_KEY_PILOT_VERMILION`でserializer、save/reload、map host、会話ABIを縦に通してから後続batchへ広げる。
- batch完了ごとにclean ROMから再構築し、対象map、state、失敗経路を検証する。

## 6. 自動生成できる受入試験

`acceptance_tests`は次のfixtureへ直接変換します。

- `setup_terms`: unlock/state/inventory/partyの前提
- `action`: triggerまたはstep呼出
- `expected`: state差分、表示、battle/service、retry可否
- `category`: focused test suiteの分類

最低4分類に加え、choice、reward、battle、acquisition、state writeを含むeventにはvalidatorが対応する失敗分類を要求します。これにより実装後に新しく仕様を聞き直す必要を減らします。

## 7. Codexが再判断してよい範囲

次は実装上の可逆な詳細であり、設計変更ではありません。

- generated numeric IDとROM allocation address
- `ALLOCATE_SAFE_TILE`のexact coordinate/local ID
- text/data/code blobの並びとalignment
- 同義なscript opcode列の選択
- focused test fixtureの内部構造

物語、発生条件、state遷移、報酬、失敗時挙動、会話、batch依存は再判断せず、返却bundleを正本にします。
