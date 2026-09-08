# P01 独立検証の照合記録

2026-09-08。対象はUSER-MODERNIZATION-P01のみ。これは既にmergeされたPR #15の実装・累積候補を変更せず、並行して実施したPR #14側の独立検証を引き継ぐ補足記録である。P02/P03/P04はこの作業で開始しない。タスク状態の正本、現行プレイ基準、他工程の準備状態を変更しない。

## 並行作業の合流方針

PR #14のsource-only checkpoint `b55af346c8eb0a9c402accb7e3790cba23c8039b`から、現行対象consumer、収集C表generator、旧ROMの再現、clean起点の候補生成、実ARM/mGBA検証を実装した。最終source HEADは `51edbebc2aa6260e0c09a0a53c2eed63b0e85fac`。そのCIはrun34174954995で成功した。

作業中の2026-09-08T00:56:10Zに、別経路のPR #15がmerge commit `69ab9fa03f300387b46833ff01ac0a13a3a23f66`としてmainへ入った。PR #14は同じconfig/identity/CI等の二重実装として競合した。最新mainの`config/modernization_candidate.json`を再取得し、こちらで生成・検証した候補とsize/SHA-256/CRC32が同一であることを確認した。PR #14の実装をmainへ上書きmergeせず、履歴を保持し、この補足記録だけを最新mainへ取り込む。

PR #15のmergeはこのセッションが実行した操作ではない。独立検証の実行・修復と、既存mainの確認を混同しない。

## 両実装で一致した候補ROM

- mainの正本: `build/stages/63_modernization_p01_identity_repair.gba`
- 独立生成側: `build/modernization/P01_identity_collection_repair.gba`
- size: 33554432 bytes
- SHA-256: `6642602d33e1e074c20afebfc649846f0aaf106c2455f2ca212a4f427ec74fbd`
- CRC32: `FB09EF2D`
- 親: 明示採用Stage62、SHA-256 `d97a0d4a6cd6f8f77a1503a5ac6d473b0e94c4892e3d5a94098497ce35cb6e6f`。

両方のROM identityが一致したので、差分BPSファイルがbyte同一であるとも、両source構成が同一であるとも主張しない。BPSにはmetadata等の差があり、独立側のBPSは別hashである。ROM本体・patch・save・元ZIPはこの補足PRへ入れない。

## 根本修正と実consumerの独立検証

旧表ではSpecies412にbit386/通常収集属性、Species649に除外属性が割り当てられていた。現行manifestは内部タマゴ412・キャタピー649であり、keyを照合しない数値joinが原因だった。

独立generatorはspecies_keyから現行IDを再解決し、collection_key→bit/属性の対応を保持した。訂正は2行の非ID属性10byteのみ。既存ID、1216bit、152-byte bitmap、240-byte内側save block、ROM/RAM/save配置は不変。宣言範囲はoffset19763728と19765624の各8byte、宣言外0、新規allocation0。

実host Cのsave consumerへ旧表／訂正表をそれぞれリンクし、旧表のキャタピー登録欠落と内部タマゴ誤登録を再現した。さらに実ROMの`VegaAcqSaveMigrate`、`VegaAcqSaveFinalize`、`VegaAcqSaveValidate`をmGBAで呼び、旧ROMと候補それぞれ独立2process×3caseを実行した。候補ではキャタピー649が既存bit386へ登録され、内部タマゴ412は登録されず、有効な既存save block全240byteは変更されなかった。

これは変更に直結する実ARM direct-call回帰であり、通常プレイ全経路E2Eやユーザー実機saveの確認ではない。既存bit386の過去の由来は推測して消去・再構成しない。

## Actionsで確認した証跡

| 検証 | exact HEAD | 実行 | 結果 |
|---|---|---|---|
| 独立候補のclean起点2回再生成、順逆/clean BPS往復、親/候補の実ARM各2process | efc2662dc6d1cc59732da13411b5569ea8525577 | https://github.com/dekaazarashi1111-web/pokemon-vega-modern/actions/runs/34174073406 | success |
| 明示Stage62 checkと独立2process mGBA | a89cd50f4a065a399553619456a4a17dc66de3a3 | https://github.com/dekaazarashi1111-web/pokemon-vega-modern/actions/runs/34172673504 | success |
| 現行対象集合・実C consumer・決定的生成の54テスト | a3c8423f443eac29de1afec7840d94260da1c34c | https://github.com/dekaazarashi1111-web/pokemon-vega-modern/actions/runs/34173113076 | success |
| 実ROMの参照と容量のread-only測定 | 0b9fd7a70d50670a6baa289e2c2e78aa225c6182 | https://github.com/dekaazarashi1111-web/pokemon-vega-modern/actions/runs/34173283267 | success |
| 生成モデル全key/ID、タマゴ技stream、関連12テスト | ad1f9b0d114da9ad31bb8a2922baf3ffa1cef8a3 | https://github.com/dekaazarashi1111-web/pokemon-vega-modern/actions/runs/34174354489 | success |
| 独立branch最終source-validation | 51edbebc2aa6260e0c09a0a53c2eed63b0e85fac | https://github.com/dekaazarashi1111-web/pokemon-vega-modern/actions/runs/34174954995 | success |
| merge済みmainのsource-validation | 69ab9fa03f300387b46833ff01ac0a13a3a23f66 | https://github.com/dekaazarashi1111-web/pokemon-vega-modern/actions/runs/34174952611 | success |

これらのテストは重複があるため件数を単純合計しない。補足PRのworkflowは上記runのHEAD・name・successと正本候補identityを再照合するだけであり、過去ROM検証を新しい実行と装わない。main側builder変更の妥当性はmainのCIとPR #15側gateの責任範囲であり、独立sourceの成功を別sourceへ無条件流用しない。

## 対象・容量の追加注意点

全Species1621、Move1063、Ability312、Item999、Type25のkey/ID対、Species全国番号・form_key・対象集合、取得要求553組、Form388組を検査した。原作習得の対象はキャタピーだけを追加した1300key。技表の全反映ではなく、他の除外を一括解除しない。未実装ALLY SWITCH候補1063は既存Move0..1062の集合に入れない。

実ROMの進化は16枠/種、856使用、最大9、未使用25080、終端後の有効行0。空きは各種族の枠であり、追加Species数ではない。レベル技raw28874行、最大34行/種。表示時に0技を除く28859件との差を不具合として数えない。タマゴ技は1388種族marker・8831技・20440bytes、全marker/技参照と終端を照合した。

**教え技の未使用側64bitには合計20151bitが立っていた。** active64枠/21883互換に対してbitmap自体は128bit/種だが、上位bitをそのまま「空き64枠」として有効化すると誤採用になる。将来の追加時は明示的なcompatibility再生成と対象集合の検査が必要である。TM120＋HM8は128枠/60214互換で、現行bit枠の空きは0。

中央allocatorの未割当量はintegration_modules1760826bytes（最大連続1760688）、future_tail155090bytes（最大連続155076）。合計1915916bytesでmain側監査の総量と一致した。未割当spanは全FFだったが、将来の自動割当承認ではない。未追跡RAM/saveを空き扱いせず、既存reserved ownerとBox80/Party100 ABIを維持する。

## 検証環境の失敗と保全

初回の実コメント起動run34172072248は、資材取得後に`reports/generated/stage61_wiki.json`の現在版と旧環境ZIP版の衝突で失敗した。権限不足やActions未対応ではなかった。

独立側では現在reportのGit blobを固定し、一時退避→既存hash検証restore(force=False)→現在版復帰・旧版別保存で修復した。既存の外側/member hash・symlink・他file衝突・secret保護は緩めていない。両report hashとGit管理source不変を確認した。これをmainの別実装へ上書き移植しない。

repositoryと既存Releaseはpublicであり、名称のPrivateを非公開根拠にしない。この独立作業では既存資材をephemeral runnerへ読むだけで、新しいROM/save/元ZIP/credentialの公開・uploadはしていない。他経路の保管操作を、この作業で非公開性を確認した操作として扱わない。

## 引継ぎ

正本候補・生成入口はmainの`config/modernization_candidate.json`、`config/modernization_inputs.json`、`design/modernization_handoff.md`を引き続き使う。独立branchの候補configや古いBLOCKED状態で正本を上書きしない。通常プレイ基準Stage62は不変。

P02/P03の実行、能力・進化・全習得の採用、実機配布、次候補への切替はこの補足作業の対象ではない。PR #14のsourceと検証履歴は保持し、mainへの二重mergeは行わない。
