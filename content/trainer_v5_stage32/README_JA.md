# Trainer V5 / Stage 33 Tohoku Batch03 source bundle

このdirectoryは、Stage 33 Batch02の39 encounterへ、Gym1直後から同一路線へ連続する15 encounterを追加した累積正本入力です。

- `trainer_encounters_v5.csv` / `trainer_parties_v5.csv` / `trainer_party_members_v5.csv`: 累積54戦・54一意party・171 memberのV5原文行。
- `trainer_stage32_bindings.csv`: Stage 33実ROMで監査したmap/object/script、trainerbattle kind、物理保存flag owner、個別採用理由。歴史的file名は維持しています。
- Gym1直後のmap 22/1 map-script実命令1件と、map 3/21の残る14命令を追加し、同一物理命令を指す論理別名0/419/424は除外しています。
- rematchはcommand-data address + physical source IDを持つRematchMap V2で位置別に解決し、stock selectorの0結果と物理save flag ownerを維持します。
- registry CSV: 選定partyが参照するkeyだけをV5原文から抽出したものです。
- `trainer_v5_stage32.schema.json`: SINGLE / DOUBLE / MULTIの別契約と、16-byte party ABI + 16-byte sidecar V1のlive field契約です。
- `source_manifest.json`: 同梱参照ZIPと抽出物のSHA-256です。

Builderはこのbundleだけを読み、原V5 ZIPや外部networkには依存しません。
