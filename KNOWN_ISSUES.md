# Known Issues

リリース候補と起動可能な統合ROMはまだありません。

- 269 ranges / 775 byteの直接競合のうち584 byteは異なる最終値になる。固定アドレス、RAM、SaveBlock、script special、全IDの完全監査は未完了。
- プレイブックの実装領域とmanifestは大半が雛形で、CFRU/DPEのVega向けbuild harnessは未実装。
- 受領した統合設計CSVには、フォームを識別できない進化条件、意味重複、全国番号表記、救済道具参照の既知課題がある。`design/import_review.md` を参照。
- 公式1025種、フォーム、25箱PC、DexNav、SaveBlockを32 MiB ROM/GBA saveへ収める容量計画は未検証。
- Z、ダイマックス、テラのv1.0必須範囲と旧Vegaセーブ移行方針は未決定。
- 上流toolchain再現、emulator automation、全ストーリー回帰は未着手。
