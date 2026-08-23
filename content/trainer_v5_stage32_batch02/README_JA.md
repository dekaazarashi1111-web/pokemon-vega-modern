# Trainer V5 / Stage 32 Tohoku Batch02 source bundle

このdirectoryは、Stage 31の先行25 encounterへ、同梱Trainer Redesign V5から物理的に連続する14 encounterを追加した累積正本入力です。

- `trainer_encounters_v5.csv` / `trainer_parties_v5.csv` / `trainer_party_members_v5.csv`: 累積39戦・39一意party・113 memberのV5原文行。
- `trainer_stage32_bindings.csv`: Stage 32実ROMで監査したmap/object/script、trainerbattle kind、物理保存flag owner、個別採用理由。
- map 3/21、3/22、22/1を追加し、同一物理命令を指す論理別名419/424は除外しています。
- registry CSV: 選定partyが参照するkeyだけをV5原文から抽出したものです。
- `trainer_v5_stage32.schema.json`: SINGLE / DOUBLE / MULTIの別契約と、16-byte party ABI + 16-byte sidecar V1のlive field契約です。
- `source_manifest.json`: 同梱参照ZIPと抽出物のSHA-256です。

Builderはこのbundleだけを読み、原V5 ZIPや外部networkには依存しません。
