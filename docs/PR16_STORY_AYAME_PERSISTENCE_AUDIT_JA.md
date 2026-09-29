# アヤメSave18 保存領域の独立監査

`PASS_AYAME_SAVE18_PERSISTENCE_AUDIT`。正式測定run36522150353/job109257152262の全7stepと、その記録run36523214697のpush/upload/post終端を照合した。原本artifact11012768108の外側SHA-256 `4e7a2e5d25dbf01284fdd992327971b7a0d84df2e86022ea6cefc685b2dd064b` と全170memberを検証。新しいnative実行・ROM生成・既存55試験の再実行は0。

実ROMの0x080DB224→0x083C4B28が示す14section配置からchecksum長を取得し、inputのcounter16/17とoutputの18/17の4bank・56件を検査した。同じ前世代bankをinput/outputで照合した件数を含み、56種類の独立Saveとは数えない。対象は宣言されたpayloadのみ。S61E拡張record、padding、RTCはstock checksumの対象と主張しない。S61Eの既受入CRC32判定を改変しない。

既受入map22/1 rootのtrainer ID1/1200/1203を、現ROMの372行remap表へ結合。external0x501/0x9B0/0x9B3→physical0x501/0x63D/0x63Fの3bitだけが0→1になった。section2相対bit1/317/319をtrainer IDと誤認しない。新規のnative call-path試験ではなく、完了原本の静的表・保存対応照合である。

legacy var全256件の差分は0x4021:93→5、0x4022:1→2、0x404D:0→8、0x4071:1→3。前3件のruntime owner同定は主張しない。連戦完了var0x4071は既受入map rootの完了値3と一致。NationalDex magic/flag0x840/var0x404Eと後続story var0x4072はいずれも0。注入による解禁・自然育成・進化・ジムリーダー勝利・全storyを受入しない。

唯一の次のstory-fast開始点は既存artifact11012768108の `story-fast.srm`、SHA-256 `dc1f690f0616affc61b6d45632924e4c81995c91c7c1939994f37bbe8527432d`、131088bytes、counter18、map5/4・7,4北、party4/RP0。同じartifactのcold.srmは全byte一致。前Save17 bank57344bytesも保持する。

新42試験は開発とActionsで同じ42件を確認したもので、84別件とは数えない。checksum/endian/overflow/対象外padding、sector重複/署名/部分世代、remap重複/誤physical、進行未完/全国図鑑注入、欠けたjob一覧/upload/post終端を拒否する。影響なしに再実行しない。

並行セッションの別Save948d9e58…（通常報酬取得済み）は `content/modernization/pr16_story_ayame_gate_development/parallel_development.json` に未採用開発履歴として分離した。非force拒否で同時更新を検知した後、正式nativeの重複起動0。正式Save dc1f690f…へ置換しない。並行開発native2は監査native0とは別計数。既存55試験・record工程・ROM/原本・全国図鑑owner・active baselineを維持した。

監査run自身 `36524125377` の最終push/uploadは自己予測しない。終了後のAPI照合とartifact内record-head.txt/record.zipを参照する。一般CIは全greenと主張しない。
