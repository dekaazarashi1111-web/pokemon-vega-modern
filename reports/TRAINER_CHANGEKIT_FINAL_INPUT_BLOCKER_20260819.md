# Trainer ChangeKit 最終統合入力ブロッカー（2026-08-19）

## 結論

`USER-20260819-TRAINER-CHANGEKIT-FINAL-INTEGRATION` は実装開始前ゲートで **BLOCKED** とする。
採用したStage 34完全版は正常だが、提供されたAUTHORING_KIT／ChangeKitは、全1,302行を
1,302個の物理戦闘consumerへ一対一で接続できない。

`FINAL_CODEX_INTEGRATION_JA.txt` は、6個のChangeKitを最初に検証し、1件でもFAILなら実装を
開始せず、物理audit未完了値を推測で接続しないことを要求する。公式原本に対するTask 05
validatorがFAILし、exact-ROM監査でも設計入力の欠落が確定したため、ROM patch、clean build、
mGBA、最終commit、完全版ZIPは生成していない。

## 採用入力

- Stage 34: `Pokemon-Vega_FULL-WORKSPACE_STAGE34_TRAINER-V5-TOHOKU-BATCH03_RECOVERED_20260819.zip`
  - ZIP SHA-256: `b2997d185394c135198b756d2bdc59e1ab77fda80f60cf34163ee0ddfdb889da`
  - HEAD: `0619d43694819a6ef80cb1386e4e3ee641c6aad0`
  - tree: `55ff7913782894f2dca21f54089c4deee320e41a`
  - Stage 34 ROM SHA-256: `84395df49b5cee3fa83b501714828fa03db29bc24b1ed0f1a9cb292e1437946f`
  - `VERIFY_SNAPSHOT.py`: PASS（manifest 28,469件、Git clean、focused check）
- 非RECOVERED版はZIPのEOCD欠落で不採用。
- AUTHORING_KITとTask 01〜06は外側ZIP CRC、内部manifest／SHA256SUMS、共通BASELINEを確認済み。

## 公式validator

元ZIPをfresh一時領域へ展開し、`python3 -B`で検証した。

| 対象 | 結果 |
|---|---|
| AUTHORING_KIT | PASS |
| Task 01 | PASS |
| Task 02 | PASS |
| Task 03 | PASS |
| Task 04 | PASS |
| Task 05 | **FAIL**: `party/partition format mismatch: ENC_TOHOKU_REF_1012` |
| Task 06 | PASS |

`ENC_TOHOKU_REF_1012`を単純にDOUBLEへ変更してはいけない。記録address
`0x0885B0C0`の実byteは`0x62`（`cleartrainerflag 708`）であり、実DOUBLE戦
`0x08890AFB`（kind 8）は既に`ENC_TOHOKU_REF_1013`が所有する。

## Tohoku物理crosswalkの欠落

ChangeKitのTohoku 1,101行は、ROM-rooted graphの全trainer関連参照をそのまま戦闘として採番している。
Stage 34 ROMの指定addressを全件再読取りした結果は次のとおり。

| command | 行数 |
|---|---:|
| `0x5C trainerbattle` | 1,050 |
| `0x60 checktrainerflag` | 7 |
| `0x61 settrainerflag` | 40 |
| `0x62 cleartrainerflag` | 4 |

`battle_type=UNKNOWN` 54件のうち、実戦闘は次のkind 9 SINGLE 3件だけである。

- `ENC_TOHOKU_REF_0440`: `0x0817C9C7`
- `ENC_TOHOKU_REF_0441`: `0x0817CABA`
- `ENC_TOHOKU_REF_0442`: `0x0817CA3F`

残る51件はflag consumerであり、同じphysical Trainer IDの実`trainerbattle`候補はすべて
別encounterが既に所有する。例:

- `ENC_TOHOKU_REF_0075`: 記録`0x0819444D`は`settrainerflag 132`。
  唯一の実戦闘`0x08186058`は`ENC_TOHOKU_REF_0074`が所有する。
- `ENC_TOHOKU_REF_1012`: 記録`0x0885B0C0`は1013戦後の`cleartrainerflag 708`。
  実戦闘`0x08890AFB`は`ENC_TOHOKU_REF_1013`が所有する。

したがって、address補正だけで51個の固有partyを接続できる空きconsumerはない。既存flag命令を
戦闘へ置換するとstory／defeat／rematch状態を変更するため、自動補正の範囲外である。

さらに1,050参照は1,030個の実command addressしか持たず、17個の共有commandに20行の余剰がある。
Stage 34のexact rebind key（command address、kind、source ID）だけでは、同じcommandへ異なるpartyを
要求する行を両立できない。caller/root-aware dispatchまたは設計側のdedupeが必要である。

提供データの名目上限はTohoku 1,050実参照＋Kanto 201計画行＝1,251であり、1,302には51不足する。
独立command address基準ではTohoku 1,030＋Kanto 201＝最大1,231である。

## Kanto物理所有権の競合

Task 06は201戦中13戦が現ROM確認済み、188戦が新規生成候補である。188戦の198 object componentは
clean ROMのsource objectへ全件一致し、69 mapのobject budgetとallocator容量も足りる。しかし次の3件は、
Stage 34 baselineの取得イベントが同一source object／同一座標を既に所有する。

| encounter | Task 06配置 | Stage 34 owner |
|---|---|---|
| `ENC_KANTO_ROUTE_013` / 4108 | Mansion B1F G97/M62 object 2 `(34,13,3)` | `HOST_HOENN_SPACE` |
| `ENC_KANTO_ROUTE_075` / 4170 | Victory Road 3F G97/M41 object 0 `(40,7,3)` | `HOST_GALAR_CROWN` |
| `ENC_KANTO_ROUTE_161` / 4256 | Route 25 G96/M37 object 0 `(11,4,3)` | `HOST_JOHTO_TIME` |

baseline優先契約により取得hostをtrainer scriptで上書きできず、同一座標への二重objectも不可である。
Task 06には代替object／座標、unlock順、collision・sightline・迂回路証明がない。

Task 06の会話814行（35固有本文）も、現行1-byte charmapでは814/814 encode FAILとなる。
不足は漢字等142 glyphで、原文を保持するにはfont／decoder／field・battle printerの拡張が必要である。
現行ABIを維持する場合は35文のかな正規化表と再wrap済み本文を設計入力として確定する必要がある。

## 再開に必要な補正版

次を満たすAUTHORING_KIT／ChangeKit再発行が必要である。

1. Tohoku 51 flag参照をencounterから除外して総数を改訂するか、51個の新規物理戦について
   root、到達条件、初戦／再戦、SINGLE／DOUBLE、defeat flag、会話・報酬ownerを指定する。
2. 共有command 17個／余剰20行をdedupeするか、caller/root別にpartyを選ぶ正式仕様を与える。
3. `ENC_TOHOKU_REF_1012`を1013のpost-battle aliasとして除外／再分類し、Task 05 partition、party、
   expected tests、manifest、checksumsを同時に再生成する。
4. Kanto競合3件の代替object／座標とcollision・sightline・unlock証跡を指定する。
5. Kanto会話35文について、現行charmap用の承認済みかな本文、または漢字renderer/font素材を提供する。
6. 修正版に対しAUTHORING validatorとTask 01〜06 validatorをすべてPASSさせる。

## 復元状態

- 現在の`/home/dekaa/projects/Pokemon-Vega`は検証済みStage 34 workspaceへのsymlink。
- 旧clean workspace（HEAD `408e215b30d60984819cd8bef8f4d5125f763cd8`）は
  `/home/dekaa/projects/Pokemon-Vega-stage26-backup-20260819-408e215`へ退避済み。
- 元ZIP、ROM、ChangeKit原本は変更していない。
