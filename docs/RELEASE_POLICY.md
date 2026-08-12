# 配布・リリース方針

- ROM本体をreleaseしない。
- 自分のクリーンFireRed Rev0へ適用する差分パッチだけを作る。
- upstreamのcredit/license/利用条件を保持する。
- 元のVega patch、Factory patch、clean ROMをrelease archiveへ同梱しない。
- final patchの入力hash、出力hash、必要な適用順を明記する。
- 開発版とstable版を分ける。
- セーブ互換性を明記する。

最終archive例:

```text
vega-modern-kanto-v0.1.0/
├─ vega-modern-kanto.bps
├─ README_JA.md
├─ CHANGELOG.md
├─ CREDITS.md
├─ CHECKSUMS.txt
└─ KNOWN_ISSUES.md
```
