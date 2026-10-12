# 測定済み型分類の公開表現回復

測定sourceは920cbc492bb8c65ee0364f9420d3a152f1f72e5f、記録commitは
908289942a276fa4f552d96aae4d985f7c6a5156。run37300879978/job111733040155は
現0641・全115owner・168tests・新59分類・記録commit/push・全byte読戻しまで成功した。
全874行を保持して619分類/255未知、内訳はlevel39・palette6・song14である。
正式ROM/Save101は不変、read用候補再構成1回、旧全ROMscan/native0、donor0。

最後のpublication guardは失敗しuploadはskippedで、run全体はfailureのまま保持する。
原因は全型領域を重複列挙したegg-typed-audit.jsonが18,862,653byteになり、
閉じたexportの16,000,000byte上限を超えたこと。guardを緩和して再実行しない。

## 原本と後継

元CPは `content/modernization/pr16_dex_hof_typed_checkpoint.json`、元evidenceは
`pr16_dex_hof_typed_evidence/`。元audit SHA-256は
`679b632bb92d98e67b532a74bf3b9a2c0f288c3bd892ec584c7763a99cba7354`。
元commitに保存済みの全textを正本として再利用し、元ファイルは書換えない。

後継は `pr16_dex_hof_typed_recovery_checkpoint.json` と
`pr16_dex_hof_typed_recovery_evidence/`。新numeric/palette hitに参照されないregion列挙だけを
取り除く。全874hit、各hitの全evidence、全song証拠、全pool partition、source binding、
候補identity、分類計数をそのまま保持し、元全auditへのsize/SHAリンクを記録する。

これは表現の整理で、元分類、168tests、ROM再構成、ARM/nativeを繰り返さない。
新しく実行するのは圧縮関数の境界/負例試験と、元Git・Actions・text整合性の検査だけ。
新dirは8,000,000byte未満/ファイルの閉じた集合で検証し、非空・UTF-8・LF・非symlinkを要求する。
producer/guard/upload/consumerのpath/nameは専用契約を機械照合する。

## 未完

未知255件、tutor上位wordの直接consumer、間接参照・旧egg完全退役、DPCM全実read footprint、
実容量lease、32sector Ccontroller/全保存entry/同期heap lifetimeは未完。
Song250/251のMIDI不一致を保持する。全体図鑑修復と最終シオウの通常回復・保存・cold Continueへ
進めるまで、未証明donorを借りず、通常雑魚戦ごとのcheckpointは作らない。
