# 研究所・御三家イベント完全仕様

## host

- map: `KANTO_INDOOR_PALLET_TOWN_PROFESSOR_OAKS_LAB` (group 98 / map 3)。
- primary host: local 1、scientist、(3,11,elevation 3)、現script `...OBJECT_01_STUB`。
- regional nursery: local 3、scientist、(11,10,elevation 3)、現script `...OBJECT_03_STUB`。
- object数10のまま。新規objectなし。

## 操作

NPCへ話す → 説明 → 世代list → 種list → Yes/No → storage preflight → 研究タマゴ生成 → party、PC、shared egg queueの順でdurable delivery → claim保存。cancel、reset、全storage満杯ではclaimを消費しません。同一Speciesは一回だけです。

未接続11系統は `PRIMARY_REQUIRED`。既存wild/evolutionで到達する13種は `BACKUP_REGISTERED_ONLY` とし、図鑑登録済みの取り直し救済に限定して既存導線の価値を壊しません。

## 未接続11系統

| 世代 | 全国No. | Species key | 名称 | 方針 |
| --- | --- | --- | --- | --- |
| 6 | 653 | SPECIES_KEY_FENNEKIN | フォッコ | PRIMARY_REQUIRED |
| 6 | 656 | SPECIES_KEY_FROAKIE | ケロマツ | PRIMARY_REQUIRED |
| 7 | 722 | SPECIES_KEY_ROWLET | モクロー | PRIMARY_REQUIRED |
| 7 | 725 | SPECIES_KEY_LITTEN | ニャビー | PRIMARY_REQUIRED |
| 7 | 728 | SPECIES_KEY_POPPLIO | アシマリ | PRIMARY_REQUIRED |
| 8 | 810 | SPECIES_KEY_GROOKEY | サルノリ | PRIMARY_REQUIRED |
| 8 | 813 | SPECIES_KEY_SCORBUNNY | ヒバニー | PRIMARY_REQUIRED |
| 8 | 816 | SPECIES_KEY_SOBBLE | メッソン | PRIMARY_REQUIRED |
| 9 | 906 | SPECIES_KEY_SPRIGATITO | ニャオハ | PRIMARY_REQUIRED |
| 9 | 909 | SPECIES_KEY_FUECOCO | ホゲータ | PRIMARY_REQUIRED |
| 9 | 912 | SPECIES_KEY_QUAXLY | クワッス | PRIMARY_REQUIRED |

## 台詞と状態

全24種を同じ9-state runtimeへ載せ、個別の対象名をdataから差し込みます。実日本語は `content/acquisition_event_dialogue.csv`、state遷移は `content/acquisition_event_states.csv`。全storage満杯時は「タマゴを あずける ばしょが ない。あきを つくって また おいで。」相当で終了し、受取済み扱いにしません。

## 受入条件

- 11種全てをnew game→殿堂入り→Kanto accessから一回受取可能。
- cancel/reset/fullで再試行可能。
- egg受取だけではSpecies登録せず、孵化で登録。
- 13 backupは未登録時に配布しない。
- save migration後の重複配布なし。
