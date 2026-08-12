# import_inventory.md

2026-08-12にユーザー提供ファイルを `userfile/imports/` へ原名のままコピーし、原本とのSHA-256一致を確認した。私有ROM、パッチ、元ZIPはGit管理外かつ読み取り専用である。

## 配置とハッシュ

| 種別 | ワークスペース内の物理ファイル | Size | SHA-256 | 補足 |
|---|---|---:|---|---|
| プレイブックZIP | `userfile/imports/archives/vega_modern_codex_playbook.zip` | 133,940 | `2b99ed24b67d80277d7cbfea3b9d30dfbb6fcfecace9f56caf1357fa86840304` | 132ファイル、破損なし |
| 統合設計ZIP | `userfile/imports/archives/VEGA_CFRU_DPE_統合設計パッケージ.zip` | 223,960 | `78d196e1e24b7f95b595c74f1646c5cc1e345422862ce4c298118447d1b9164d` | 36ファイル、破損なし |
| 競合監査ZIP | `userfile/imports/archives/vega_cfru_integration_audit.zip` | 55,244 | `5b009797b037c597aac8371140d21d3731bc5329d8addd2356b9756a5e679459` | 監査正本、破損なし |
| FireRed日本版Rev.0 | `userfile/imports/roms/Pocket Monsters - FireRed (Japan).gba` | 16,777,216 | `1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486` | CRC32 `3B2056E9`、BPRJ01 Rev.00 |
| Vega参照ROM | `userfile/imports/roms/Pocket Monsters Vega.gba` | 16,777,216 | `f600fb3faa565bd335ea75114f9233f9a4fe97c12cfed145e0a7b48784d0c9d5` | CRC32 `42A73E62` |
| Factory参照ROM | `userfile/imports/roms/factory test pokemon.gba` | 33,554,432 | `570ac486f0e66563ee23278ff7ee34dd8dfeed11cbf37ab924d13eb2c62c0da5` | CRC32 `216AB7FD` |
| Factory UPS | `userfile/imports/patches/factory_test_20260524.ups` | 16,012,506 | `46ef4b008b7c68a94f919d037a0bba31853b32af3f50895e722e39deea336358` | clean→32 MiB |
| Vega IPS | `userfile/imports/patches/18年2月23日完成版ベガ.ips` | 3,720,110 | `94955c5830888c69a7dee3696abda3b88f69184af67f28a9fb77a8e8abd77f5b` | 2018-02-23完成版 |

ツール向けの安定名は `inputs/private/` と `inputs/reference/` にGit管理外の相対symlinkとして用意する。物理ファイルを複製せず、`userfile/imports/` を一度だけ検証する。

## 入力検証

- clean ROMは16,777,216 bytes、CRC32 `3B2056E9`、MD5 `47596db5a16556c60027e7bf372ec917`、SHA-1 `04139887b6cd8f53269aca098295b006ddba6cfe` で入力契約に一致した。
- clean ROMへVega IPSを単独適用した生成物は、提供Vega参照ROMとbyte単位で一致した。
- clean ROMへFactory UPSを単独適用した生成物は、提供Factory参照ROMとbyte単位で一致した。
- 両パッチを重ねた統合ROMは生成していない。
- 775重複byteの厳密比較は、同じ最終値191 byte、異なる最終値584 byteだった。

## 展開先

| 内容 | 状態 | 配置 |
|---|---|---|
| プレイブック実行基盤 | 現行運用へ統合 | ルート、`tasks/`、`scripts/`、`manifests/` ほか |
| 競合監査 | 受領ZIP単体版を正本として統合 | `audit_seed/` |
| 統合設計パッケージ | 不変のreview資料 | `design/imported/VEGA_CFRU_DPE_統合設計/` |
| 元の展開結果 | Git管理外バックアップ | `userfile/imports/extracted/` |

## 最新上流pin

2026-08-12にGitHubの既定ブランチHEADを照会した。

| Source | Branch | Commit |
|---|---|---|
| `kapibarasan000/CFRU-JP` | `main` | `e24a16fe39e27ae162faf5b78596d1f3df18489d` |
| `kapibarasan000/DPE-JP` | `main` | `10ff98c85ebf37ab5cb39a41b6e9b50f06efb19e` |
| `pret/pokefirered` | `master` | `c75f352304d529f6ba92d4f74b9cf8b5c3810788` |

以後は `state/source-lock.json` の固定値を使い、最新版の再確認や更新は専用タスクで行う。
