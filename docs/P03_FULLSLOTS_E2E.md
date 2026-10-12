# P03 Stage81: native PP・技枠満杯時の通常習得と保存再読込

## 修正対象

固定Stage80候補 `6ff621edb1c1f99c6b1feb665ddce576eff939519776a2135002ab4fa90603a3` のnative技習得には、現行技テーブルではなく旧PP配列 `0x08E0CBB4` を読む経路が残っていた。むしくい（project move 535）の現行PPは20だが、空き枠・入替の両経路で45が設定される。旧代表試験はPPが正数であることしか要求しておらず、既存原本の `learned_slot_pp=45` を遡って正常PPの証跡とは扱わない。

`tools/modernization_p03_native_pp_repair.py` は5個のPP参照consumerを、命令列・旧literal・親ROM全体SHAで分類してから `0x090421F8` に移す。対象は空き枠習得、指定枠入替、2つのtrainer custom-move初期化、native party move PP初期化。全literalの一括置換ではない。変更は5ワード・20 bytesのみ。技バランスや習得仕様は変更しない。

新候補Stage81は `521624a5e6065bd969b7c3143044f1d96491b8af05a0231827ba2e709d04d579`。Stage80製品原本、Stage79設定、Stage62プレイ基準、既存P08証跡を上書きしない。

## 通常入力の検証範囲

キャタピー（species 649）Lv8→9の採用済み経路で、技枠0〜3それぞれへの入替、習得拒否、技選択画面からBで取消、空き枠への習得を検証する。Lv7→8で早期習得しない対照も含め計8ケース。各ケースは新規mGBAプロセスで開始し、通常Bag/Party入力、進化取消、全技枠・全PP・アメ1個の消費、Startメニュー保存、元coreの破棄、新規coreの通常Continue後の保持を照合する。

fixture生成前後のnative getter/setterは初期状態の構築・観測に使うが、技習得シーン中はキー・フレーム・callback/task/cursor読取のみ。対象習得関数や保存callbackの直接呼び出しではない。自然な入手、全習得画面、繁殖・タマゴ、archive economyを通した受入に拡大しない。5参照のうち、通常習得UIで直接カバーするのは空き枠と入替の2経路である。

修正前Stage80の同じ試験では空き枠と入替枠0がPP45/20で終了コード1になることを要求する。クラッシュ、タイムアウト、別原因の失敗、PASS JSON出力は対照試験の成功には数えない。新規実行の内訳は候補8件・修正前の期待失敗2件、キャッシュ0件。

## 実行と証跡

```sh
python3 -m unittest discover -s tests -p test_modernization_p03_fullslots_e2e.py -v
bash infra/setup_github_actions.sh --install
python3 scripts/run_modernization_p03_fullslots_e2e.py
```

147件の回帰テストは、JSON field/type/重複key、入力順序、PP45の拒否、整数以外のexit code、異常終了、途中ログ、前回PASSの無効化、ROM preimage・命令guard、局所置換を検証する。合成JSONを実ROM成功件数に数えない。

private saveにはmGBA 0.10.2のRTC trailer 16 bytesをmap前に予約する。これは既存Floette harnessと同じ方式であり、seed原本を改変しない。保存時のファイル拡張によるflash bank pointer無効化を避ける。

`.github/workflows/p03-fullslots-e2e.yml` は固定GitHub toolchainで実行し、成否を問わず原本stdout/stderr/process結果とtested-headをartifactに保存する。ローカルGCC14.2.0での成功をGitHub固定GCC13.3.0の成功とは扱わない。Stage81の累積7領域受入、P08への現行候補昇格、P03全体・リリース判定は別契約であり、この代表試験だけで完了扱いにしない。
