# P03 技枠満杯・観測書込みガード・保存再読込

## 検証範囲

既採用のキャタピー（species 649）Lv8→9／むしくい（move 535）だけを対象にする。
通常Start/Bag/Party入力から、4枠それぞれの入替、最初の習得拒否、技選択画面からの取消、
Lv7→8の非習得を試験する。空き枠の習得・非習得も含め、修正候補の9ケースすべてで
通常Start保存→旧core破棄→独立coreの通常Continueを通す。
全技枠・全PP・PP Up未使用・種族・レベル・消費アイテム・保存カウンタを照合する。
初期PPは7/8/9/10と区別し、未選択枠の誤更新を検出する。

習得開始のParty画面から進化取消・field復帰まで、mCoreのbusWrite 8/16/32、
rawWrite 8/16/32、writeRegisterの7 APIを拒否する。
この区間ではキー・frame進行・受動readだけを使用する。各APIに実際の書込みを試みる
別processの負例も7件実行する。fixture構築、区間外の検査getterはhost駆動であり、
「全行程でhost操作ゼロ」「自然入手個体」とは主張しない。

## 既存Stage81候補を再利用

`tools/modernization_p03_native_pp_repair.py` の5か所・20 bytesの既存レシピをそのまま使用する。
この補助試験は独自のROM修正、候補選択、技データ変更を追加しない。
親ROMは `6ff621edb1c1f99c6b1feb665ddce576eff939519776a2135002ab4fa90603a3`、
候補は `521624a5e6065bd969b7c3143044f1d96491b8af05a0231827ba2e709d04d579`。
両方とも32 MiBで固定する。レシピ原本の全文と依存ファイルをsource bindingに含める。

親ROMでは空き枠・満杯slot0の新規習得PP45と、採用済み技表のPP20の不一致を
`EXPECTED_PP_DEFECT` として別集計する。親の不具合再現は受入PASSではない。
候補側の習得PPは20以外を認めない。未選択枠のPPも7/8/9/10で個別照合する。
このUI試験だけでは、レシピ内のtrainer生成など残り3つの消費側をE2E確認したとは主張しない。

既存の `p03-fullslots-e2e` とその8ケース・証跡は変更しない。
本試験は7 APIの実書込み拒否、満杯状態のレベル未到達、全枠の保存前後照合を
独立に検証する補助試験である。結果を既存runの上書きや受入範囲の拡大に使わない。

## mGBA RTC footerのfixture初期化

libmGBA 0.10.2のRTCWriteは、128 KiB saveに16-byte RTC footerを初めて付加する際に
flash領域をunmap/remapするが、currentBankを更新しない。その後のflash readで
旧mappingを参照して異常終了する場合があり、長い技選択経路で再現した。
ゲームの保存処理やエミュレータを改変せず、起動前の試験専用コピーにだけ、
同ライブラリのデフォルトfooter `00000000000000400000000000000000` を追加する。

128 KiBのゲームsave本体はseedと全byte一致する。元seedへの書込み、既存fileへの
二重付加、symlink経由の上書きは禁止する。初期化後SHAもC/Pythonの両側で検証する。
保存後は元coreを破棄し、同じ実ファイルから再起動する。状態スナップショットの
復元やRAMの持越しで再読込を代用しない。

参照: mGBA `0.10.2` の `src/gba/savedata.c`（GBASavedataRTCWrite、
GBASavedataReadFlash、_flashSwitchBank）および `include/mgba/internal/gba/savedata.h`。

## 実行と証跡

```sh
python3 -m unittest tests.test_modernization_p03_fullslots_guarded_e2e tests.test_modernization_p03_learning_e2e -v
python3 scripts/run_modernization_p03_fullslots_guarded_e2e.py
```

GitHub Actions `p03-fullslots-guarded-e2e` は既存の固定Ubuntu/mGBA toolchainを使用する。
新規11 process＝親の不具合再現2＋候補の受入9。再読込を含め新規coreは22。
7件の書込み拒否負例は別集計する。cache再利用は0。
source/ROM/seed/baselineのidentity、実行stdout/stderr・終了コード、fixtureと
保存後fileのhash、native UI taskの時系列を残す。
異常終了・timeout・source不一致・JSON重複key・bool/intの取り違え・欠落した
native UIの証拠・保存前後の不一致をPASSで覆わない。失敗時に過去result.jsonは消す。

## 採用範囲と未完了

候補は一時作業領域で生成し、Stage80原本・Stage62実プレイ基準・既存の
P03/P05/Stage79/P08証跡を更新しない。候補の正式採用には他domainの累積受入と
P08への新たなROM identityの統合が必要である。
P03の全習得UI、繁殖・タマゴ生成、自然入手、PP Upありの全経路、未試験のPP消費側、
P05全経路、P06/P07採用仕様、配布受入を完了扱いしない。
`candidate_promoted=false`、`full_p03_acceptance=false`、`release_ready=false`を維持する。
