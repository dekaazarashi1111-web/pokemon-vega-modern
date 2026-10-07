# JP text境界の独立address候補

## 直前の完了

JP symbol gateはsource `f9780b534f2562518c64d6a14d9950ef4e8402c5`、run `37674533900`、job `112974501079`、初回全8step成功。34試験と全文checkoutの再開bindingを照合した。固定再開workflow `37674533860` も成功。正式分類は779/95を保持する。

一般CIの2runは既知の `overlays/qol_production/qol_production.c` source-binding不一致で失敗し、解決済みにしない。Stage79の成功は全7domainの旧cache利用で、新native実行ではない。

## 新source

`ComplexRobot/frlg-sym@c04a31542086b20d8c6ee641eaa70b8db6713fd3` のJP出力・audit・metadata・conflictsと生成source、および固定pret sourceを全文size/SHA/Gitblobへ結んだ。target clean ROMのSHAは正本BPRJ rev0と一致する。全11sourceと30symbolの固定情報は `content/modernization/pr16_dex_hof_jp_crosswalk_candidates.json` を参照する。

この出力も長さは英語referenceを保持する。address候補だけに使用する。auditは採用proposalの具体的caller・literal siteを出さないため、Cで対応するcallerを発見したことと、生成時の採用票の起点を同一視しない。

## 次に絞る2組

- `083DDEE1`: 左 `gText_CantUseUntilNewBadge=083DDEC6`、右 `gText_NoMoreThanThreeMayEnter=083DDEE4`。固定Cの `CursorCB_FieldMove` / `CursorCB_Enter` と `sCursorOptions` の実選択cellを現候補で結ぶ。
- `083DE02B`: 左 `gText_SwitchedPkmnItem=083DE016`、右 `gText_PkmnHoldingItemCantHoldMail=083DE02E`。実item交換taskまたはmailboxのparty登録からcallerへ結ぶ。左の `StringExpandPlaceholders` による原text全文読取をprinter読取から分離する。

API候補は `DisplayPartyMenuMessage→PartyMenuPrintText→AddTextPrinterParameterized2(window6)`。Parameterized4ではない。現CFRU/Vega hook・wrapperを固定cleanJP住所だけで同一と扱わない。

隣接差30/24byteはEOS込み長ではない。実literal/table cellとAPI引数、制御文字列全体のEOS読取を現0641で閉じてから、対象hitを覆う最小型だけを分類する。必要future-live資源と正常ABI復帰の有限条件を使い、自然全play・全callee・普遍IRQ/heap寿命へ拡張しない。

## 第3組を保持

`083DE6AB`の右symbolに、順序整列由来の採用 `083DE6B0` と `CancelParticipationPrompt` 由来の強い候補 `083DE6AE` が競合する。6B0を採用しない。6AEも今回の現ROM未測定値なので自動採用しない。

## 検証と残件

`scripts/pr16_dex_hof_jp_crosswalk_candidates.py --sources .local/jp-crosswalk-sources --download` は固定公開sourceだけを取得・照合する。`python3 -B -m unittest discover -s tests -p test_pr16_dex_hof_jp_crosswalk_candidates.py -v` の新23試験で、英語長・rank・競合・未測定EOS・分類数の誤昇格を拒否する。

source候補2組、EOS/実cell受入0、ROM窓読取0、ROM再構成/native0。旧779受入を再走しない。全親delta、133曲/50asset、115owner/52保存owner、正式ROM/Save101を保持し、egg15118保護・安全0のまま次の限定実測へ進む。
