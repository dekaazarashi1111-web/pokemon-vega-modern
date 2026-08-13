# Kanto release checkpoint matrix

- Version: 1
- Task: T17
- Entry: group 96 / map 5 / (20,20)
- Return: 常時利用可能。National Dex不要。

| Checkpoint | 自動証跡 | 手動確認 |
|---|---|---|
| 未解禁 | save matrixで到達不可 | 研究所の船を調べる |
| 早期到着 | mGBA exact-ROM map load/render/move | クチバで歩行・帰還NPC |
| 全physical map | 253/253往路・253/253復路 | 主要道路・洞窟・建物のwarp |
| 認定章1〜4 | 順序flag script検査 | ニビ→ハナダ→クチバ→タマムシ |
| 殿堂入り後・認定章5〜8 | HOF gate＋順序flag検査 | セキチク→ヤマブキ→グレン→トキワ |
| Kanto League | 四天王5人の連鎖script・ID 759〜763 | カンナ→シバ→キクコ→ワタル→チャンピオン |
| 地方往復 | pre/post-HOF各200回 | save/load、heal、whiteout、PC満杯 |
| 野生 | 実ROM wild header 133件 | Lv68〜100、NORMAL/RESEARCH/Safari |
| 施設 | 20 mode・140 restore case | Trial/Standard/Full/Master、BP、交換、辞退 |

## 認定順

`KANTO_CERT_1`〜`KANTO_CERT_8`、`KANTO_LEAGUE_1`〜`KANTO_LEAGUE_CLEAR` を順に更新する。後半4gymとLeagueはVega Hall of Fameも要求する。最後の目標は `KANTO_LEAGUE_CLEAR`。
