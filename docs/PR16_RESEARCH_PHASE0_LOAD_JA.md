# PR16 通常load内phase0保存不可とcold回復

通常load内phase0の保存不可2経路（V1移行/未確定稼得回復）を受入。原本全2048byte・全Flashを保持して拒否、通常cold Continueで1回保存し2回の後続Continueで完全一致。

次は通常new-game/取引UIの未受入境界を限定実装/検証する。phase0 load 2件/43unit、通常V1 3件/旧40unit、7retry、BP/P08/特殊野生は変更影響なく再実行しない。

## 境界と受入

通常起動の先行rootとContinue loadを分離。Research→Mirage→QOLの既存本番delegateを通し、phase0入口の可用性word `0x03005044` だけを1→0にする。停止fixture区間で4byteを書き、7 API barrierを即時再装着する。全EWRAM、当該word以外のIWRAM、16レジスタ/CPSR、128KiB Flashを前後比較。ledger/owner/PC/戻り値の注入なし。guard中のhost書込0であり、fixture書込0とは主張しない。

V1移行とV2 prepared fishing稼得5点の2経路。実native return255、load result0、last_result13、counter2、blocked1を確認。全2048byteと128KiB Flashは原本どおり。保存可用性をhostで戻さずfresh通常起動で復帰し、counter2→3、保存1回、期待ledger全byte一致。稼得はbalance/lifetime/daily各5、pending全解除、二重加算0。他sector31 owner/Bag/party保持。実fieldと後続fresh Continue2回で全ledger・counter・owner・Bag・party一致。

## 計測と保存

候補 `5d1fc9c47225ae8c0a369514b899a062af3699fa3c9a2f617e94ffd5f7dcc1ab` を保存済みrecipeから復元。ROM変更/ARM compile/link0、旧受入再実行0。新native2process/8fresh cores、7guard拒否probe、host compile計3（初回単体C1・符号型不一致で失敗した初回runner1・修正runner1）。初回Actionsの43unit PASSはsource同一性を照合して再利用し再実行0。開発時ローカルpreflightも同じ43件PASS（受入前の開発検査）。製品ソース本体修正は不要だった。新runnerのCPSR snapshot型だけをmGBAのsigned packed型へ一致させた。証拠manifestとsource/protected hashはcheckpoint参照。

## 限界

この受入は可用性fixtureであり物理Flash故障ではない。同一coreの拒否後メニューretry、通常new-game/取引UI全体、全catalog、Issue19、releaseは未受入。候補/原本/active baseline/旧Wikiは不変、merge/releaseなし。一般CIのaction_requiredを全CI成功に読み替えない。

## Actions

source `187bb4a87fc4ad63f06022355c2d3be9ac47c2b5` / run `36244964437` / 終端確認 `True`。 finalize run `36245144543`。
