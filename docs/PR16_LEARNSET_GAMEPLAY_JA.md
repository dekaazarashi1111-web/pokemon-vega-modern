# Issue19: 通常Bag・Save・fresh Continue

候補 `6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2` / CRC32 `00F31AF7`。run35830398856、source `a906a09cc8537c04f9e6d1dd760634301bef9b3c`。

状態 `FAIL`、新規native 1 process、成功0/23ケース。初期場所・party・進行・道具はfixtureであり、通常ストーリーからの取得の証拠ではない。通常操作中は7host書込APIを禁止する3区間で観測。

正式checkpoint `content/modernization/pr16_learnset_gameplay_checkpoint.json`。原本出力はActions artifact、tracked textは伏字viewと原本hashで結合。保存100byte・全4技/PP・counter2→3・fresh coreを検査。戦闘/条件付きタマゴ等の変更影響、Issue19全体、releaseは未完。

Wiki・旧4hook・ARM/PLA1/PLC2再実行0、ROM変更0、正式BP/P08/baseline不変。

## 次の未完

Issue19: 通常Bag/殿堂入りgate/raw40ページ/取消/Floette12技/通常Save・fresh Continueの保存証拠を先に照合し、未受入ケースだけ続ける。全成功後は習得技の通常戦闘、条件付きタマゴ等の変更影響を検証。Wiki/4hook直接診断/ARM/PLA1/PLC2の単純再実行禁止。
