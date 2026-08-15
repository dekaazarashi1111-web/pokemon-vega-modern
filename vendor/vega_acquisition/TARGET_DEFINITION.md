# 収集対象定義

## 完了条件

1種を「入手可能」と数えるのは、自然なnew gameからrouteのunlockへ到達でき、必要なitem・技・時間・手持ち・進化元を同じROM内で用意でき、捕獲／受取／進化が図鑑または収集台帳へ永続化され、撃破・逃走・cancel・手持ち満杯・box満杯・reset・save失敗から回復できる場合だけです。進化tableにedgeがあるだけでは完了にしません。

## 一次対象 1206

- `REQUIRED_BASE`: 全国図鑑1〜1025のbase 1025種。フォーム差分は同じ全国番号へ統合。
- `REQUIRED_VEGA_ORIGINAL`: manifestのVEGA_ORIGINAL 206行から内部別枠25行を除いた181種。
- 同名でもVega本編の独立種として残す: canonical ID 144 ネメア、251 ラクチャン、410 アスフィア。

## 一次対象から除外する25行

- 別ROM／互換用の同名slot 5: 252 フシギバナ、253 リザードン、254 カメックス、256 ピカチュウ、282 ストライク。
- 戦闘専用コピー 6: 257〜262。
- `？`予約slot 14: 263〜276。

canonical ID 282の内部ストライクは現行direct sourceへ漏れているため、release validatorはwild/event payloadへの内部IDを拒否します。収集対象のストライクは公式canonical ID 255です。

## 完成数0だが必須の進化入口フォーム 10

`MEOWTH_G`, `FARFETCHD_G`, `MR_MIME_G`, `CORSOLA_G`, `LINOONE_G`, `YAMASK_G`, `QWILFISH_H`, `SNEASEL_H`, `BASCULIN_H`, `WOOPER_P`。これらは別全国番号の進化先を成立させるため、一度限り研究タマゴで供給します。台帳には持つが1206の完成数には加えません。

## その他のフォーム

恒常外見差分やリージョンフォームは `OPTIONAL_FORM` とし、全国番号のbase個体を完成条件にします。メガ、キョダイ、テラスタル、戦闘中変身、一時状態、タマゴ、NONE、未配信永遠の花フラエッテは完成条件から除外します。フォーム収集を別実績にする余地は残しますが、本設計の100%判定とは分離します。

## 機械可読な根拠

- 全1621行: `content/collectible_species_registry.csv`
- Vega 206行の最終判断: `content/vega_original_target_decisions_206.csv`
- 内部blocklist: `content/internal_species_blocklist_25.csv`
- collection ledger: `manifests/collection_ledger_bits.csv`
