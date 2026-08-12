# Upstream source pin

初期監査で使用する推奨pin:

| Source | Commit |
|---|---|
| CFRU-JP | `e24a16fe39e27ae162faf5b78596d1f3df18489d` |
| DPE-JP | `10ff98c85ebf37ab5cb39a41b6e9b50f06efb19e` |
| pret/pokefirered | `c75f352304d529f6ba92d4f74b9cf8b5c3810788` |

これらは2026-08-12時点の初期pinです。最新版へ追従する場合は、作業途中で無条件にpullせず、専用ブランチで更新差分を監査してから`source-lock.json`を変更します。

2026-08-12にGitHubの既定ブランチHEADを直接照会し、3件ともこの表のcommitと一致することを確認しました。以後「最新」ではなくcommit SHAで参照します。

受領した統合設計CSVはDPE-JP `520937c0959e2a1be57771d1dfee9f6fee806c7e` を来歴として持ちます。実装pin `10ff98c85ebf37ab5cb39a41b6e9b50f06efb19e` はその1コミット後で、差分は `src/Back_Pic_Coords_Table.c` の1行です。CSV来歴は書換えず、最新版との差分監査をT02/T07で行います。

## 役割

- CFRU-JP: 戦闘エンジン、技、特性、道具、新進化方式など
- DPE-JP: Species拡張、画像、図鑑、進化、習得技等
- pret/pokefirered: 原作Map/Eventを構造化して読む参照。BPRJの最終offsetの根拠ではない
- Factory UPS: 完成見本・config差分・挙動比較用。Vegaへ直接適用しない
