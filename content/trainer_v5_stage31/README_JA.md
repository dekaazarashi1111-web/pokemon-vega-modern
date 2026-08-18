# Trainer V5 / Stage 31 integration source bundle

このdirectoryは、同梱Trainer Redesign V5からTask上限の25 encounterだけを無改変で抽出し、Stage 31実ROM監査で確定した物理bindingを追加した正本入力です。

- `trainer_encounters_v5.csv` / `trainer_parties_v5.csv` / `trainer_party_members_v5.csv`: V5原文行。
- `trainer_stage31_bindings.csv`: Stage 31のmap/object/script/trainerbattle kind、保存flag owner、採用理由。
- registry CSV: 選定partyで参照するkeyの原文行。
- `trainer_v5_stage31.schema.json`: SINGLE / DOUBLE / MULTIを分離し、V5で従来catalog-onlyだったability/nature/6EVを16-byte sidecar V1の必須live fieldとする契約。
- `source_manifest.json`: 同梱参照ZIPと抽出物のSHA-256。

Builderはこのbundleだけを読み、原V5 ZIPや外部networkには依存しません。
