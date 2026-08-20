# Move Distribution V4 production入力

T22は、Git管理外の読取専用原本
`userfile/imports/Pokemon-Vega_MOVE-DISTRIBUTION-V4_IMPLEMENTATION-READY.zip`
を固定入力として使用する。このdirectoryには原本CSVを複製しない。

- ZIP SHA-256: `4022cd6e1358f58dffc5ebc38b756166f0a1072f948af6934298f65bd82678b2`
- submission fingerprint: `d0e014e49beb339668ce3531b8fe6871c793a063f2bff1c8d2b97898f81d02a9`
- level-up: 28,274行
- egg move: 8,219行
- TM/tutor追加: 2,799件
- form policy: 509件
- wild initial/source coverage: 1,206件

builderは毎回安全な一時directoryへ11 entryを展開し、packet self-testと共通validatorを
再実行する。その後、`manifests/species_ids.csv` と `manifests/move_ids.csv` でnumeric IDへ
解決し、Stage 38から再監査した物理表を基準にStage 39を生成する。

Stage 38の`CanMonLearnTutorMove`には旧20-byte strideの加算命令が残っているため、
builderは`0x091100F6`をexpected-byteで監査し、その1命令だけをNOP化する。これにより
consumer固有の特殊判定を維持したまま、設計固定の16-byte Tutor正本を直接参照する。

原本ZIP、ROM、saveは変更・追跡しない。
