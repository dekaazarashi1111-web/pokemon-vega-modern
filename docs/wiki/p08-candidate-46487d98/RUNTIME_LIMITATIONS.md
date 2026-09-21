# 証拠区分・runtime限界

候補 SHA-256 `46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38` / 33554432 bytes / CRC32 `CC068B4A`。

[Wiki入口](README.md)

| 証拠ラベル | 意味 |
| --- | --- |
| EXACT_CANDIDATE_ROM | 選択候補から読取またはbyte照合。動作の全経路受入ではない。 |
| GENERATED_CANONICAL | tracked正本・固定上流に由来。実配布や実callerの全面受入ではない。 |
| INHERITED_ACCEPTED | 旧候補の限定native原本をP08移送根拠に従って継承。再実行なし。 |
| NATIVE_ACCEPTED | 同一候補・同一scopeの実行原本がある場合のみ。今回のWiki生成では新規付与しない。 |
| IMPLEMENTED_NOT_NATIVE_ACCEPTED | 候補table/実装はあるが対象全体の独立native受入はない。 |
| SUPPLY_NOT_FOUND_IN_CURRENT_SOURCES | 隠れslotや仕様値の存在とは別に、初回供給根拠を現在の入力から特定できない。 |
| DEFERRED_AUDIT | 今回の読取スコープでは未監査。 |

## 明示的な未監査範囲

野生初期技と固定配布の全実moveset、隠れ特性の種族別初回供給caller・patch、専用Z全組合せのnative E2E、全メガの交代・ひんし・終了・Save/Continue個別受入、全特性のAIとCircus抑制組合せは今回追加実行していません。各ページのDEFERRED_AUDIT/IMPLEMENTED_NOT_NATIVE_ACCEPTEDを参照してください。

専用handlerの完全新規追加か既存流用かはeffect IDだけで断定しません。effect_noveltyはStage61の技行に同じeffect IDが存在したかであり、handler新設の証拠ではありません。役割候補は自動検索補助で、強さの採否判断ではありません。

## 受入済み原本の再利用

```json
{
  "active_baseline_changed": false,
  "new_native_runs": 0,
  "original_native": {
    "accepted_original_core_instances": 48,
    "accepted_original_processes": 42,
    "candidate_rom_sha256": "e9dcb375168c92cb4390aaf390b8278dbf08867dd7dc3b834561799ae021710d",
    "closed_scope": [
      "six_native_mega_ability_assignments",
      "six_native_revert_save_cold_continue_lifecycles",
      "36_nonactivation_controls"
    ],
    "limits": [
      "base Eelektross already has Levitate",
      "native Mega also changes stats; Fire Mane contrast is not ability-only"
    ],
    "native_mega_turn_revert_cold_save_cases": [
      "dragonize",
      "eelevate_ground",
      "fire_mane",
      "mega_sol",
      "piercing_drill",
      "spicy_spray"
    ]
  },
  "release_approved": false,
  "rom_changes": 0,
  "transfer": {
    "candidate": {
      "sha256": "46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38",
      "size": 33554432
    },
    "candidate_crc32": "CC068B4A",
    "completed_actions": [
      {
        "conclusion": "success",
        "head_sha": "5a1b35ad66c0a9a157274835987d9d7d20ba1f12",
        "id": 35506654695,
        "jobs": [
          {
            "conclusion": "success",
            "id": 106067500110,
            "name": "receipt",
            "status": "completed",
            "steps": [
              {
                "completed_at": "2026-09-20T11:01:07Z",
                "conclusion": "success",
                "name": "Set up job",
                "number": 1,
                "started_at": "2026-09-20T11:01:06Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:01:12Z",
                "conclusion": "success",
                "name": "Run actions/checkout@v4",
                "number": 2,
                "started_at": "2026-09-20T11:01:07Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:01:48Z",
                "conclusion": "success",
                "name": "未登録のresume実装bindingを固定入力から修復しsource checkpointを非force保存",
                "number": 3,
                "started_at": "2026-09-20T11:01:12Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:02:36Z",
                "conclusion": "success",
                "name": "完了原本と目視29画面を照合し正式受入・引継ぎ・両ログを非force保存",
                "number": 4,
                "started_at": "2026-09-20T11:01:48Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:02:36Z",
                "conclusion": "success",
                "name": "P08限定読取用tracked textを保存（ROMとsaveは除外）",
                "number": 5,
                "started_at": "2026-09-20T11:02:36Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:02:38Z",
                "conclusion": "success",
                "name": "Run actions/upload-artifact@v4",
                "number": 6,
                "started_at": "2026-09-20T11:02:36Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:02:38Z",
                "conclusion": "success",
                "name": "Post Run actions/checkout@v4",
                "number": 12,
                "started_at": "2026-09-20T11:02:38Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:02:38Z",
                "conclusion": "success",
                "name": "Complete job",
                "number": 13,
                "started_at": "2026-09-20T11:02:38Z",
                "status": "completed"
              }
            ]
          }
        ],
        "status": "completed"
      },
      {
        "conclusion": "success",
        "head_sha": "29202a863b14da9956c1e3b0b306b56ba3f77dc4",
        "id": 35507102023,
        "jobs": [
          {
            "conclusion": "success",
            "id": 106068665551,
            "name": "impact",
            "status": "completed",
            "steps": [
              {
                "completed_at": "2026-09-20T11:10:43Z",
                "conclusion": "success",
                "name": "Set up job",
                "number": 1,
                "started_at": "2026-09-20T11:10:43Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:10:48Z",
                "conclusion": "success",
                "name": "Run actions/checkout@v4",
                "number": 2,
                "started_at": "2026-09-20T11:10:43Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:11:38Z",
                "conclusion": "success",
                "name": "21層の全ROM検証・owner影響・引継ぎと両ログを非force保存",
                "number": 3,
                "started_at": "2026-09-20T11:10:48Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:11:38Z",
                "conclusion": "success",
                "name": "ROMを除外し検査証拠だけ保存",
                "number": 4,
                "started_at": "2026-09-20T11:11:38Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:11:38Z",
                "conclusion": "success",
                "name": "Run actions/upload-artifact@v4",
                "number": 5,
                "started_at": "2026-09-20T11:11:38Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:11:39Z",
                "conclusion": "success",
                "name": "Post Run actions/checkout@v4",
                "number": 10,
                "started_at": "2026-09-20T11:11:38Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:11:39Z",
                "conclusion": "success",
                "name": "Complete job",
                "number": 11,
                "started_at": "2026-09-20T11:11:39Z",
                "status": "completed"
              }
            ]
          }
        ],
        "status": "completed"
      },
      {
        "conclusion": "failure",
        "head_sha": "870e65e58fa34289daa6216ae41ed201e54b5e29",
        "id": 35507654812,
        "jobs": [
          {
            "conclusion": "failure",
            "id": 106070069903,
            "name": "representative",
            "status": "completed",
            "steps": [
              {
                "completed_at": "2026-09-20T11:22:35Z",
                "conclusion": "success",
                "name": "Set up job",
                "number": 1,
                "started_at": "2026-09-20T11:22:35Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:22:41Z",
                "conclusion": "success",
                "name": "Run actions/checkout@v4",
                "number": 2,
                "started_at": "2026-09-20T11:22:36Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:23:26Z",
                "conclusion": "success",
                "name": "P08完了Actions・原本と22context契約を確認し開始を非force保存",
                "number": 3,
                "started_at": "2026-09-20T11:22:41Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:23:46Z",
                "conclusion": "success",
                "name": "host mGBA依存のみ導入（ARM buildなし）",
                "number": 4,
                "started_at": "2026-09-20T11:23:26Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:24:10Z",
                "conclusion": "success",
                "name": "同じ46487d98候補のRing active代表1件だけ実行",
                "number": 5,
                "started_at": "2026-09-20T11:23:46Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:24:46Z",
                "conclusion": "failure",
                "name": "未観測と成功を分離し原本・引継ぎ・両ログを非force保存",
                "number": 6,
                "started_at": "2026-09-20T11:24:10Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:24:46Z",
                "conclusion": "success",
                "name": "ROM・saveを除外し画面と原本を保存",
                "number": 7,
                "started_at": "2026-09-20T11:24:46Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:24:47Z",
                "conclusion": "success",
                "name": "Run actions/upload-artifact@v4",
                "number": 8,
                "started_at": "2026-09-20T11:24:46Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:24:47Z",
                "conclusion": "success",
                "name": "失敗を成功に読み替えない",
                "number": 9,
                "started_at": "2026-09-20T11:24:47Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:24:48Z",
                "conclusion": "success",
                "name": "Post Run actions/checkout@v4",
                "number": 18,
                "started_at": "2026-09-20T11:24:47Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T11:24:48Z",
                "conclusion": "success",
                "name": "Complete job",
                "number": 19,
                "started_at": "2026-09-20T11:24:48Z",
                "status": "completed"
              }
            ]
          }
        ],
        "status": "completed"
      },
      {
        "conclusion": "success",
        "head_sha": "3a08d5dbed832a869161a7e5c842d96eebd58659",
        "id": 35510095146,
        "jobs": [
          {
            "conclusion": "success",
            "id": 106076375842,
            "name": "recovery",
            "status": "completed",
            "steps": [
              {
                "completed_at": "2026-09-20T12:15:27Z",
                "conclusion": "success",
                "name": "Set up job",
                "number": 1,
                "started_at": "2026-09-20T12:15:26Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:15:33Z",
                "conclusion": "success",
                "name": "Run actions/checkout@v4",
                "number": 2,
                "started_at": "2026-09-20T12:15:27Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:16:19Z",
                "conclusion": "success",
                "name": "完了原本だけ回収・14画面とbyteを照合・受入記録を非force保存",
                "number": 3,
                "started_at": "2026-09-20T12:15:33Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:16:21Z",
                "conclusion": "success",
                "name": "Run actions/upload-artifact@v4",
                "number": 4,
                "started_at": "2026-09-20T12:16:19Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:16:21Z",
                "conclusion": "success",
                "name": "Post Run actions/checkout@v4",
                "number": 8,
                "started_at": "2026-09-20T12:16:21Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:16:21Z",
                "conclusion": "success",
                "name": "Complete job",
                "number": 9,
                "started_at": "2026-09-20T12:16:21Z",
                "status": "completed"
              }
            ]
          }
        ],
        "status": "completed"
      },
      {
        "conclusion": "success",
        "head_sha": "2b3fba89ee99e4d1360687f22d4cfb562fd0ec77",
        "id": 35511250297,
        "jobs": [
          {
            "conclusion": "success",
            "id": 106079428228,
            "name": "representative",
            "status": "completed",
            "steps": [
              {
                "completed_at": "2026-09-20T12:39:39Z",
                "conclusion": "success",
                "name": "Set up job",
                "number": 1,
                "started_at": "2026-09-20T12:39:38Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:39:44Z",
                "conclusion": "success",
                "name": "Run actions/checkout@v4",
                "number": 2,
                "started_at": "2026-09-20T12:39:39Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:40:25Z",
                "conclusion": "success",
                "name": "固定原本と新契約を照合し開始checkpointを非force保存",
                "number": 3,
                "started_at": "2026-09-20T12:39:44Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:40:43Z",
                "conclusion": "success",
                "name": "Host mGBA dependency only",
                "number": 4,
                "started_at": "2026-09-20T12:40:25Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:41:07Z",
                "conclusion": "success",
                "name": "共有帰還と保存再開の影響代表1件だけ実行",
                "number": 5,
                "started_at": "2026-09-20T12:40:43Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:41:41Z",
                "conclusion": "success",
                "name": "実行原本と停止点を非force保存",
                "number": 6,
                "started_at": "2026-09-20T12:41:07Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:41:41Z",
                "conclusion": "success",
                "name": "Pack text and bounded screens only",
                "number": 7,
                "started_at": "2026-09-20T12:41:41Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:41:42Z",
                "conclusion": "success",
                "name": "Run actions/upload-artifact@v4",
                "number": 8,
                "started_at": "2026-09-20T12:41:41Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:41:42Z",
                "conclusion": "success",
                "name": "Native result",
                "number": 9,
                "started_at": "2026-09-20T12:41:42Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:41:43Z",
                "conclusion": "success",
                "name": "Post Run actions/checkout@v4",
                "number": 18,
                "started_at": "2026-09-20T12:41:42Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:41:43Z",
                "conclusion": "success",
                "name": "Complete job",
                "number": 19,
                "started_at": "2026-09-20T12:41:43Z",
                "status": "completed"
              }
            ]
          }
        ],
        "status": "completed"
      },
      {
        "conclusion": "success",
        "head_sha": "33bb7bce407e839fbf1931ee8968ca55fce82077",
        "id": 35511721939,
        "jobs": [
          {
            "conclusion": "success",
            "id": 106080666506,
            "name": "representative",
            "status": "completed",
            "steps": [
              {
                "completed_at": "2026-09-20T12:49:31Z",
                "conclusion": "success",
                "name": "Set up job",
                "number": 1,
                "started_at": "2026-09-20T12:49:30Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:49:36Z",
                "conclusion": "success",
                "name": "Run actions/checkout@v4",
                "number": 2,
                "started_at": "2026-09-20T12:49:31Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:51:01Z",
                "conclusion": "success",
                "name": "固定原本と新契約を照合し開始checkpointを非force保存",
                "number": 3,
                "started_at": "2026-09-20T12:49:36Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:51:16Z",
                "conclusion": "success",
                "name": "Host mGBA dependency only",
                "number": 4,
                "started_at": "2026-09-20T12:51:01Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:51:32Z",
                "conclusion": "success",
                "name": "わざメモリー満杯置換と保存再開の影響代表1件だけ実行",
                "number": 5,
                "started_at": "2026-09-20T12:51:16Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:52:10Z",
                "conclusion": "success",
                "name": "実行原本と停止点を非force保存",
                "number": 6,
                "started_at": "2026-09-20T12:51:32Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:52:11Z",
                "conclusion": "success",
                "name": "Pack text and bounded screens only",
                "number": 7,
                "started_at": "2026-09-20T12:52:10Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:52:11Z",
                "conclusion": "success",
                "name": "Run actions/upload-artifact@v4",
                "number": 8,
                "started_at": "2026-09-20T12:52:11Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:52:11Z",
                "conclusion": "success",
                "name": "Native result",
                "number": 9,
                "started_at": "2026-09-20T12:52:11Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:52:12Z",
                "conclusion": "success",
                "name": "Post Run actions/checkout@v4",
                "number": 18,
                "started_at": "2026-09-20T12:52:11Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T12:52:12Z",
                "conclusion": "success",
                "name": "Complete job",
                "number": 19,
                "started_at": "2026-09-20T12:52:12Z",
                "status": "completed"
              }
            ]
          }
        ],
        "status": "completed"
      },
      {
        "conclusion": "failure",
        "head_sha": "304eb25919601ccd7534dfd6e1da1dd5be091019",
        "id": 35512429611,
        "jobs": [
          {
            "conclusion": "failure",
            "id": 106082548688,
            "name": "representative",
            "status": "completed",
            "steps": [
              {
                "completed_at": "2026-09-20T13:04:25Z",
                "conclusion": "success",
                "name": "Set up job",
                "number": 1,
                "started_at": "2026-09-20T13:04:25Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:04:30Z",
                "conclusion": "success",
                "name": "Run actions/checkout@v4",
                "number": 2,
                "started_at": "2026-09-20T13:04:25Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:05:56Z",
                "conclusion": "success",
                "name": "固定原本と新契約を照合し開始checkpointを非force保存",
                "number": 3,
                "started_at": "2026-09-20T13:04:30Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:05:56Z",
                "conclusion": "success",
                "name": "真正退出Save30限定、cache missで再作成しない",
                "number": 4,
                "started_at": "2026-09-20T13:05:56Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:06:11Z",
                "conclusion": "success",
                "name": "Host mGBA dependency only",
                "number": 5,
                "started_at": "2026-09-20T13:05:56Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:06:25Z",
                "conclusion": "failure",
                "name": "真正退出Save30から通常戦闘の自然calleeだけ検証",
                "number": 6,
                "started_at": "2026-09-20T13:06:11Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:07:05Z",
                "conclusion": "success",
                "name": "実行原本と停止点を非force保存",
                "number": 7,
                "started_at": "2026-09-20T13:06:25Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:07:05Z",
                "conclusion": "success",
                "name": "Pack text and bounded screens only",
                "number": 8,
                "started_at": "2026-09-20T13:07:05Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:07:06Z",
                "conclusion": "success",
                "name": "Run actions/upload-artifact@v4",
                "number": 9,
                "started_at": "2026-09-20T13:07:05Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:07:06Z",
                "conclusion": "failure",
                "name": "Native result",
                "number": 10,
                "started_at": "2026-09-20T13:07:06Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:07:06Z",
                "conclusion": "success",
                "name": "Post Run actions/checkout@v4",
                "number": 20,
                "started_at": "2026-09-20T13:07:06Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:07:06Z",
                "conclusion": "success",
                "name": "Complete job",
                "number": 21,
                "started_at": "2026-09-20T13:07:06Z",
                "status": "completed"
              }
            ]
          }
        ],
        "status": "completed"
      },
      {
        "conclusion": "success",
        "head_sha": "63ec984e57524d747ef2a2b9816a7c979f2e1b37",
        "id": 35512907219,
        "jobs": [
          {
            "conclusion": "success",
            "id": 106083860159,
            "name": "representative",
            "status": "completed",
            "steps": [
              {
                "completed_at": "2026-09-20T13:14:22Z",
                "conclusion": "success",
                "name": "Set up job",
                "number": 1,
                "started_at": "2026-09-20T13:14:21Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:14:27Z",
                "conclusion": "success",
                "name": "Run actions/checkout@v4",
                "number": 2,
                "started_at": "2026-09-20T13:14:22Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:15:14Z",
                "conclusion": "success",
                "name": "固定原本と新契約を照合し開始checkpointを非force保存",
                "number": 3,
                "started_at": "2026-09-20T13:14:27Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:15:15Z",
                "conclusion": "success",
                "name": "真正退出Save30限定、cache missで再作成しない",
                "number": 4,
                "started_at": "2026-09-20T13:15:14Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:15:45Z",
                "conclusion": "success",
                "name": "Host mGBA dependency only",
                "number": 5,
                "started_at": "2026-09-20T13:15:15Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:16:02Z",
                "conclusion": "success",
                "name": "真正退出Save30から通常戦闘の自然calleeだけ検証",
                "number": 6,
                "started_at": "2026-09-20T13:15:45Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:16:43Z",
                "conclusion": "success",
                "name": "実行原本と停止点を非force保存",
                "number": 7,
                "started_at": "2026-09-20T13:16:02Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:16:43Z",
                "conclusion": "success",
                "name": "Pack text and bounded screens only",
                "number": 8,
                "started_at": "2026-09-20T13:16:43Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:16:44Z",
                "conclusion": "success",
                "name": "Run actions/upload-artifact@v4",
                "number": 9,
                "started_at": "2026-09-20T13:16:43Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:16:44Z",
                "conclusion": "success",
                "name": "Native result",
                "number": 10,
                "started_at": "2026-09-20T13:16:44Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:16:45Z",
                "conclusion": "success",
                "name": "Post Run actions/checkout@v4",
                "number": 20,
                "started_at": "2026-09-20T13:16:44Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T13:16:45Z",
                "conclusion": "success",
                "name": "Complete job",
                "number": 21,
                "started_at": "2026-09-20T13:16:45Z",
                "status": "completed"
              }
            ]
          }
        ],
        "status": "completed"
      },
      {
        "conclusion": "success",
        "head_sha": "e800b909c1182f07bb4f4b0075f4ba1d7c8637c8",
        "id": 35523960389,
        "jobs": [
          {
            "conclusion": "success",
            "id": 106112751051,
            "name": "accept",
            "status": "completed",
            "steps": [
              {
                "completed_at": "2026-09-20T16:50:19Z",
                "conclusion": "success",
                "name": "Set up job",
                "number": 1,
                "started_at": "2026-09-20T16:50:19Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T16:50:24Z",
                "conclusion": "success",
                "name": "Run actions/checkout@v4",
                "number": 2,
                "started_at": "2026-09-20T16:50:19Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T16:50:24Z",
                "conclusion": "success",
                "name": "原本受入の拒否系契約のみ",
                "number": 3,
                "started_at": "2026-09-20T16:50:24Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T16:51:08Z",
                "conclusion": "success",
                "name": "完了Actions・固定原本・5画面を照合し非force受入checkpoint",
                "number": 4,
                "started_at": "2026-09-20T16:50:24Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T16:51:09Z",
                "conclusion": "success",
                "name": "原本と次の候補移送に必要な限定textを保存",
                "number": 5,
                "started_at": "2026-09-20T16:51:08Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T16:51:11Z",
                "conclusion": "success",
                "name": "Run actions/upload-artifact@v4",
                "number": 6,
                "started_at": "2026-09-20T16:51:09Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T16:51:12Z",
                "conclusion": "success",
                "name": "Post Run actions/checkout@v4",
                "number": 12,
                "started_at": "2026-09-20T16:51:11Z",
                "status": "completed"
              },
              {
                "completed_at": "2026-09-20T16:51:12Z",
                "conclusion": "success",
                "name": "Complete job",
                "number": 13,
                "started_at": "2026-09-20T16:51:12Z",
                "status": "completed"
              }
            ]
          }
        ],
        "status": "completed"
      }
    ],
    "domain_transfers": {
      "BP": {
        "accepted": true,
        "affected_owners": [
          "BATTLE_LOSS_RETURN",
          "DROUGHT_BATTLE_CALLBACK",
          "FACTORY_GETTER_CALL",
          "LOAD_DISPATCH",
          "RING_ORDINARY_BEGIN",
          "SAVE_DISPATCH",
          "codex_battle_runtime_stage44_payload",
          "pr16_circus_cold_load_bridge",
          "pr16_circus_drought_empty_loader",
          "pr16_circus_getter_preserve_r3",
          "pr16_circus_party_retention_runtime",
          "pr16_circus_reception_runtime",
          "pr16_circus_rental_drought",
          "pr16_circus_streak_get_veneer",
          "pr16_circus_streak_runtime",
          "pr16_factory_party_retention_trampoline",
          "pr16_ring_npc_runtime",
          "pr16_ring_ordinary_policy_runtime",
          "regression_runtime_payload"
        ],
        "candidate": {
          "sha256": "46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38",
          "size": 33554432
        },
        "changed_bytes": 11778,
        "decision": "ACCEPTED_CHANGED_OWNER_TRANSFER",
        "hooks": {
          "BATTLE_LOSS_RETURN": [
            "P08_BP_RETURN_PARTY"
          ],
          "DROUGHT_BATTLE_CALLBACK": [
            "P08_RING_ORDINARY",
            "P08_CIRCUS_POST_EXIT_ORDINARY"
          ],
          "FACTORY_GETTER_CALL": [
            "P08_BP_RETURN_PARTY"
          ],
          "LOAD_DISPATCH": [
            "P08_SHARED_SAVE_LOAD",
            "P08_RING_ORDINARY"
          ],
          "RING_ORDINARY_BEGIN": [
            "P08_RING_ORDINARY"
          ],
          "SAVE_DISPATCH": [
            "P08_SHARED_SAVE_LOAD",
            "P08_RING_ORDINARY"
          ]
        },
        "old_cases_replayed": 0,
        "original_candidate_relabelled": false,
        "original_identity": {
          "sha256": "4deb7c27771c63740ab94b9cf8c7b3c386f7193b989f35ede9d131c4f4bf15bf",
          "size": 9442
        },
        "original_source_manifest_missing": true,
        "parent": {
          "sha256": "ceddbe91ecba0d81f6148b82d24771cced2d269f9474400bfed7a0938156934b",
          "size": 33554432
        },
        "representative_ids": [
          "P08_BP_RETURN_PARTY",
          "P08_CIRCUS_POST_EXIT_ORDINARY",
          "P08_RING_ORDINARY",
          "P08_SHARED_SAVE_LOAD"
        ],
        "source_path": "content/modernization/pr16_bp_chooser_checkpoint.json",
        "source_review_scope": "固定原本hashを維持。存在するsource manifestは一致を確認。未記録manifestを捏造しない。"
      },
      "CIRCUS": {
        "accepted": true,
        "affected_owners": [],
        "candidate": {
          "sha256": "46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38",
          "size": 33554432
        },
        "changed_bytes": 0,
        "decision": "SAME_CANDIDATE_INHERIT",
        "hooks": {},
        "old_cases_replayed": 0,
        "original_candidate_relabelled": false,
        "original_identity": {
          "sha256": "265f903d57d1205ef87877b4f29a73bc16ef6ed208ffade8cd62b1c39f5ca2ab",
          "size": 5476
        },
        "original_source_manifest_missing": false,
        "parent": {
          "sha256": "46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38",
          "size": 33554432
        },
        "representative_ids": [],
        "source_path": "content/modernization/pr16_circus_acceptance.json",
        "source_review_scope": "固定原本hashを維持。存在するsource manifestは一致を確認。未記録manifestを捏造しない。"
      },
      "FIXED_FORM": {
        "accepted": true,
        "affected_owners": [
          "BATTLE_LOSS_RETURN",
          "DROUGHT_BATTLE_CALLBACK",
          "FACTORY_GETTER_CALL",
          "LOAD_DISPATCH",
          "PARTY_RESTORE_CALL",
          "RING_ORDINARY_BEGIN",
          "SAVE_DISPATCH",
          "codex_battle_runtime_stage44_payload",
          "facility_runtime_payload",
          "factory_high_modes_v2_stage42_payload",
          "pr16_circus_cold_load_bridge",
          "pr16_circus_drought_empty_loader",
          "pr16_circus_getter_preserve_r3",
          "pr16_circus_party_retention_runtime",
          "pr16_circus_reception_runtime",
          "pr16_circus_rental_drought",
          "pr16_circus_streak_get_veneer",
          "pr16_circus_streak_runtime",
          "pr16_factory_loss_return",
          "pr16_factory_party_retention_runtime",
          "pr16_factory_party_retention_trampoline",
          "pr16_ring_npc_runtime",
          "pr16_ring_ordinary_policy_runtime",
          "regression_runtime_payload"
        ],
        "candidate": {
          "sha256": "46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38",
          "size": 33554432
        },
        "changed_bytes": 12163,
        "decision": "ACCEPTED_CHANGED_OWNER_TRANSFER",
        "hooks": {
          "BATTLE_LOSS_RETURN": [
            "P08_BP_RETURN_PARTY"
          ],
          "DROUGHT_BATTLE_CALLBACK": [
            "P08_RING_ORDINARY",
            "P08_CIRCUS_POST_EXIT_ORDINARY"
          ],
          "FACTORY_GETTER_CALL": [
            "P08_BP_RETURN_PARTY"
          ],
          "LOAD_DISPATCH": [
            "P08_SHARED_SAVE_LOAD",
            "P08_RING_ORDINARY"
          ],
          "PARTY_RESTORE_CALL": [
            "P08_BP_RETURN_PARTY"
          ],
          "RING_ORDINARY_BEGIN": [
            "P08_RING_ORDINARY"
          ],
          "SAVE_DISPATCH": [
            "P08_SHARED_SAVE_LOAD",
            "P08_RING_ORDINARY"
          ]
        },
        "old_cases_replayed": 0,
        "original_candidate_relabelled": false,
        "original_identity": {
          "sha256": "1de5c58c70d63441804a99e3622fef7773c09618cd9b16b6d42071c5d3893b3e",
          "size": 16630
        },
        "original_source_manifest_missing": true,
        "parent": {
          "sha256": "e630f7f199194fb4b531ff3a561da866902aea200770a832aec5c276e1636267",
          "size": 33554432
        },
        "representative_ids": [
          "P08_BP_RETURN_PARTY",
          "P08_CIRCUS_POST_EXIT_ORDINARY",
          "P08_RING_ORDINARY",
          "P08_SHARED_SAVE_LOAD"
        ],
        "source_path": "content/modernization/pr16_fixed_form_acceptance.json",
        "source_review_scope": "固定原本hashを維持。存在するsource manifestは一致を確認。未記録manifestを捏造しない。"
      },
      "GENERIC_FORM": {
        "accepted": true,
        "affected_owners": [
          "BATTLE_LOSS_RETURN",
          "DROUGHT_BATTLE_CALLBACK",
          "FACTORY_GETTER_CALL",
          "LOAD_DISPATCH",
          "PARTY_RESTORE_CALL",
          "RING_ORDINARY_BEGIN",
          "SAVE_DISPATCH",
          "codex_battle_runtime_stage44_payload",
          "facility_runtime_payload",
          "factory_high_modes_v2_stage42_payload",
          "modernization_mega_shop_stage68_payload",
          "pr16-shop-display-safe-content",
          "pr16_circus_cold_load_bridge",
          "pr16_circus_drought_empty_loader",
          "pr16_circus_getter_preserve_r3",
          "pr16_circus_party_retention_runtime",
          "pr16_circus_reception_runtime",
          "pr16_circus_rental_drought",
          "pr16_circus_streak_get_veneer",
          "pr16_circus_streak_runtime",
          "pr16_factory_loss_return",
          "pr16_factory_party_retention_runtime",
          "pr16_factory_party_retention_trampoline",
          "pr16_ring_npc_runtime",
          "pr16_ring_ordinary_policy_runtime",
          "regression_runtime_payload"
        ],
        "candidate": {
          "sha256": "46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38",
          "size": 33554432
        },
        "changed_bytes": 16556,
        "decision": "ACCEPTED_CHANGED_OWNER_TRANSFER",
        "hooks": {
          "BATTLE_LOSS_RETURN": [
            "P08_BP_RETURN_PARTY"
          ],
          "DROUGHT_BATTLE_CALLBACK": [
            "P08_RING_ORDINARY",
            "P08_CIRCUS_POST_EXIT_ORDINARY"
          ],
          "FACTORY_GETTER_CALL": [
            "P08_BP_RETURN_PARTY"
          ],
          "LOAD_DISPATCH": [
            "P08_SHARED_SAVE_LOAD",
            "P08_RING_ORDINARY"
          ],
          "PARTY_RESTORE_CALL": [
            "P08_BP_RETURN_PARTY"
          ],
          "RING_ORDINARY_BEGIN": [
            "P08_RING_ORDINARY"
          ],
          "SAVE_DISPATCH": [
            "P08_SHARED_SAVE_LOAD",
            "P08_RING_ORDINARY"
          ]
        },
        "old_cases_replayed": 0,
        "original_candidate_relabelled": false,
        "original_identity": {
          "sha256": "414cd525f060e1c074d2522e0344dab8a82a3d16f723b9e68237e4949ea3d2b8",
          "size": 2842
        },
        "original_source_manifest_missing": true,
        "parent": {
          "sha256": "635fd890a8d1071560d3cb56c9c663425f7c988119ce098dedad6bf6554f973e",
          "size": 33554432
        },
        "representative_ids": [
          "P08_BP_RETURN_PARTY",
          "P08_CIRCUS_POST_EXIT_ORDINARY",
          "P08_RING_ORDINARY",
          "P08_SHARED_SAVE_LOAD"
        ],
        "source_path": "content/modernization/pr16_generic_form_acceptance.json",
        "source_review_scope": "固定原本hashを維持。存在するsource manifestは一致を確認。未記録manifestを捏造しない。"
      },
      "P03_P06_P07": {
        "accepted": true,
        "affected_owners": [
          "BATTLE_LOSS_RETURN",
          "DROUGHT_BATTLE_CALLBACK",
          "FACTORY_GETTER_CALL",
          "LOAD_DISPATCH",
          "PARTY_RESTORE_CALL",
          "RING_ORDINARY_BEGIN",
          "SAVE_DISPATCH",
          "codex_battle_runtime_stage44_payload",
          "facility_runtime_payload",
          "factory_high_modes_v2_stage42_payload",
          "modernization_mega_shop_stage68_payload",
          "pr16-shop-display-safe-content",
          "pr16_circus_cold_load_bridge",
          "pr16_circus_drought_empty_loader",
          "pr16_circus_getter_preserve_r3",
          "pr16_circus_party_retention_runtime",
          "pr16_circus_reception_runtime",
          "pr16_circus_rental_drought",
          "pr16_circus_streak_get_veneer",
          "pr16_circus_streak_runtime",
          "pr16_factory_loss_return",
          "pr16_factory_party_retention_runtime",
          "pr16_factory_party_retention_trampoline",
          "pr16_ring_npc_runtime",
          "pr16_ring_ordinary_policy_runtime",
          "regression_runtime_payload"
        ],
        "candidate": {
          "sha256": "46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38",
          "size": 33554432
        },
        "changed_bytes": 16556,
        "decision": "ACCEPTED_CHANGED_OWNER_TRANSFER",
        "hooks": {
          "BATTLE_LOSS_RETURN": [
            "P08_BP_RETURN_PARTY"
          ],
          "DROUGHT_BATTLE_CALLBACK": [
            "P08_RING_ORDINARY",
            "P08_CIRCUS_POST_EXIT_ORDINARY"
          ],
          "FACTORY_GETTER_CALL": [
            "P08_BP_RETURN_PARTY"
          ],
          "LOAD_DISPATCH": [
            "P08_SHARED_SAVE_LOAD",
            "P08_RING_ORDINARY"
          ],
          "PARTY_RESTORE_CALL": [
            "P08_BP_RETURN_PARTY"
          ],
          "RING_ORDINARY_BEGIN": [
            "P08_RING_ORDINARY"
          ],
          "SAVE_DISPATCH": [
            "P08_SHARED_SAVE_LOAD",
            "P08_RING_ORDINARY"
          ]
        },
        "old_cases_replayed": 0,
        "original_candidate_relabelled": false,
        "original_identity": {
          "sha256": "f0c438447c8dbcc68fd3ea12ecd3eeaee24c5890caf0ef7d3b14ff2aabd3fc51",
          "size": 4480
        },
        "original_source_manifest_missing": true,
        "parent": {
          "sha256": "635fd890a8d1071560d3cb56c9c663425f7c988119ce098dedad6bf6554f973e",
          "size": 33554432
        },
        "representative_ids": [
          "P08_BP_RETURN_PARTY",
          "P08_CIRCUS_POST_EXIT_ORDINARY",
          "P08_RING_ORDINARY",
          "P08_SHARED_SAVE_LOAD"
        ],
        "source_path": "content/modernization/pr16_completion_acceptance.json",
        "source_review_scope": "固定原本hashを維持。存在するsource manifestは一致を確認。未記録manifestを捏造しない。"
      },
      "RING": {
        "accepted": true,
        "affected_owners": [
          "BATTLE_LOSS_RETURN",
          "DROUGHT_BATTLE_CALLBACK",
          "FACTORY_GETTER_CALL",
          "LOAD_DISPATCH",
          "SAVE_DISPATCH",
          "codex_battle_runtime_stage44_payload",
          "pr16_circus_cold_load_bridge",
          "pr16_circus_drought_empty_loader",
          "pr16_circus_getter_preserve_r3",
          "pr16_circus_party_retention_runtime",
          "pr16_circus_reception_runtime",
          "pr16_circus_rental_drought",
          "pr16_circus_streak_get_veneer",
          "pr16_circus_streak_runtime",
          "pr16_factory_party_retention_trampoline"
        ],
        "candidate": {
          "sha256": "46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38",
          "size": 33554432
        },
        "changed_bytes": 11071,
        "decision": "ACCEPTED_CHANGED_OWNER_TRANSFER",
        "hooks": {
          "BATTLE_LOSS_RETURN": [
            "P08_BP_RETURN_PARTY"
          ],
          "DROUGHT_BATTLE_CALLBACK": [
            "P08_RING_ORDINARY",
            "P08_CIRCUS_POST_EXIT_ORDINARY"
          ],
          "FACTORY_GETTER_CALL": [
            "P08_BP_RETURN_PARTY"
          ],
          "LOAD_DISPATCH": [
            "P08_SHARED_SAVE_LOAD",
            "P08_RING_ORDINARY"
          ],
          "SAVE_DISPATCH": [
            "P08_SHARED_SAVE_LOAD",
            "P08_RING_ORDINARY"
          ]
        },
        "old_cases_replayed": 0,
        "original_candidate_relabelled": false,
        "original_identity": {
          "sha256": "85c56f6eb79b8f589ef6ab7a49db18929f9beb97dc7aac0dadc273623b07acfd",
          "size": 162934
        },
        "original_source_manifest_missing": false,
        "parent": {
          "sha256": "4ea33fb8224b0b84493ccca6e90161da245705eb1eb0a3874691ab39cc3806cc",
          "size": 33554432
        },
        "representative_ids": [
          "P08_BP_RETURN_PARTY",
          "P08_CIRCUS_POST_EXIT_ORDINARY",
          "P08_RING_ORDINARY",
          "P08_SHARED_SAVE_LOAD"
        ],
        "source_path": "content/modernization/pr16_ring_policy_acceptance.json",
        "source_review_scope": "固定原本hashを維持。存在するsource manifestは一致を確認。未記録manifestを捏造しない。"
      }
    },
    "final_native_acceptance_complete": true
  }
}
```

## 読取rootと資産

```json
{
  "ability_descriptions": "0x094A8DFC",
  "ability_names": "0x094A78DC",
  "egg_moves": "0x095D9EFC",
  "evolution": "0x095A0CC8",
  "item_data": "0x094537E0",
  "move_battle": "0x090421F4",
  "move_descriptions": "0x09049638",
  "move_effects": "0x0903FA48",
  "move_names": "0x090453C8",
  "species_back": "0x0954ECC4",
  "species_back_coords": "0x0955C42C",
  "species_base_stats": "0x09576C74",
  "species_front": "0x0954B88C",
  "species_front_coords": "0x0955AA10",
  "species_icon": "0x0955896C",
  "species_icon_palette": "0x0955A388",
  "species_level_up_pointers": "0x095D5FF0",
  "species_national_dex": "0x09575258",
  "species_palette": "0x095520FC",
  "species_shiny_palette": "0x09555534",
  "species_species_names": "0x09583D54",
  "species_tmhm": "0x0958D378",
  "species_tutor": "0x09593BE8",
  "tm_hm_move_catalog": "0x0944BB80",
  "tutor_move_catalog": "0x0944BC80"
}
```

source bindingとtable hashは [data/index.json](data/index.json) / [data/provenance.json](data/provenance.json) に保存します。

[今回追加の固定consumer監査・正確な残件](CONSUMER_AUDIT.md)

[汎用Zの実行時split・候補table監査](RUNTIME_Z_AUDIT.md)

[技effectのsource由来・残件](EFFECT_ORIGIN_AUDIT.md)
