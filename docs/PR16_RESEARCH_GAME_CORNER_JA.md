# PR16 GAME_CORNER 実配当の限定受入

入口は `CHATGPT_RESUME.md` と固定再開MD/JSON。専用正本は
`content/modernization/pr16_research_game_corner_checkpoint.json`。

## 今回閉じた範囲

候補 `26dac23cfdbc02c3c25e357b79dcdf3d247c10d893f54a4f6d6b1227bf5624da`
の実スロットを物理キーで開始し、4枚配当の無RP、赤777の300枚配当
（923→1223コイン）、0→3RP、取引の2保存、別coreの通常Continueを確認した。
100枚以上を受け取った途中でもRPは0のまま。配当終了後だけ3RPとなる。
保存counterは2→3→4。取引tokenは `0x012c039a`、next transactionは2。

開始map98/56・座標1,7・coin case・元手1000はfixtureである。
観測barrier後は物理入力と読取のみ。RP、配当、RNG、結果、PCを書き換えない。
入口はbg13 `(0,7)`、script `0x094324dd`。両配当hook
`0x0814061a/0x0814065a` のveneerを候補byteとcanonical modelから照合。
製品overlay/ROMの変更は0。既設hookが動作したため検証専用Cと独立oracleを追加した。

配当後の未保存の賭けで終了時コインは1188だが、cold Continueは取引保存時の
1223コイン/3RP/counter4へ復帰する。これは保存不具合ではない。
Flash131072byteとRTC付きファイル131088byteを別identityで照合した。
全ledger2048/checksum・研究owner64・他owner・全Bag・手持ち600byte/6体を照合。
Continue後600idleでFlash・残高・台帳は不変。手動Saveは0。

## 原本と失敗履歴

`pr16_research_game_corner_evidence/` の3分割textは、原本3440行から未確認画像の
hash行1145だけを除いた全2295行である。入力・状態・終端の値と順序は不変。
展開は `pr16_research_game_corner.unpack_text` がsize/hash/単一stream/UTF-8を制限する。
完全stdoutのhashも保存した。画像は開始、UI、4枚配当、300枚配当、終了、Continueの
6画面のみ目視受入。1145画面全確認や研究ガイドのnative文言は主張しない。

稼得runnerの原本終端は `STOPPED` のまま保全し、別oracleが限定PASSを判定する。
native5process/5coresのうち、入口pointer検査の誤り2件、Continueのhash境界誤り1件は
失敗として保持。実稼得1件と独立Continue1件が検証対象。host compile6、ARM0。
書込barrier7経路は各拒否。初回117検査中1失敗を修正後117PASS。
3分割loader変更後は影響2検査だけPASS。受入済みnative/旧unit再実行0。

新規suiteは `tests.test_pr16_research_game_corner.GameCornerTests`。
記録だけの検査は `tests.test_pr16_research_game_corner_record.RecordTests`。
旧受入やこの成功nativeを無変更で再起動しない。原本save/ROMはGitへ入れない。
Actions native成功ではなく、ハッシュ固定Actions資材を復元したローカル実測である。

## 次の未完作業

通常進行の研究受付/ショップへの到達・自然RPでの支出接続、未確認native文言を進める。
Startまとめ払いと日内上限18のnative境界は別scopeで未受入。
全活動・全map・自然到達・release完了へ拡大解釈しない。
写真/虫取り/採掘/釣り/生態/BP/P08の原本は不変。merge/release/baseline変更なし。
