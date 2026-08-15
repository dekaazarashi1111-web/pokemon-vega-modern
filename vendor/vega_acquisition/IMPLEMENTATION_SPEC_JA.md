# 実装仕様

## 1. レイヤ構成

1. **content layer**: Species route、event、dialogue、FSM、unlock、hostをCSVで保持。
2. **generated layer**: `build_acquisition_content.py` がC table、host wrapper、薄いfield script、patch manifestを決定的に生成。
3. **common runtime**: `overlays/acquisition_runtime/**`。capture/gift/egg/fossil/evolution/trade/serviceを同じtransaction APIで扱う。
4. **engine adapter**: repository固有のparty/PC、battle、save、item、unlock、UI、evolution ABIを結ぶ。添付資料だけでABIを推測しない。
5. **serializer**: named allocator結果とexact stage metadataを必須にし、既存object script pointerだけを置換。
6. **acceptance**: static graph、host C test、exact ROM byte inspection、mGBA全case結果をrelease gateにする。

## 2. transaction状態機械

`IDLE → PREFLIGHT → PREPARED(persist) → OPERATION_STAGED/CAPTURE_ACTIVE → COMMITTING → IDLE`。

- unlock、claim上限、入力item、party/PC/egg queueを変更前に検査。
- irreversible操作前にpending transactionを保存。
- captureはcaught callbackだけがclaimをcommit。defeat/escape/abortはclaimを変えない。
- gift/egg/fossilはdelivery tokenと`OPERATION_STAGED` journalを先に永続化し、その後claimをcommit。fossil itemは最後にconsumeし、persist失敗時はtokenでrestore。
- reset recoveryはjournal phaseを判定。OPERATION_STAGEDは同じdurable generationにdeliveryがある証明としてcommitし、PREPARED/CAPTURE_ACTIVEはrollbackして再試行。
- eggは受取時にevent claimをcommitするがSpecies登録は孵化時。
- full/cancel/invalid selectionは非消費。

全eventは9状態分岐を `content/acquisition_event_states.csv`、実台詞を `content/acquisition_event_dialogue.csv` に持ちます。

## 3. 保存

collection ledgerは1206完成種 + enabling form 10 = 1216 bits (152 bytes)。event claimは共有key単位で176 bits。Cosmogだけ二回受取counterを持ちます。pending、CRC、version、optional evolution countersを含む標準C ABI上240-byteの相対layoutは `manifests/save_layout.csv` と `generated/acquisition_save_layout.h` にあります。save blockの実address/sectorは既存allocatorが所有します。

migrationはcaught/registered状態からcollection bitをseedし、one-shot eventはpolicy flagに従ってclaimをseedします。legacy Vega flagはexact binding後にだけseedへ追加します。

## 4. host script

薄いscriptは `lock; faceplayer; callnative wrapper; waitstate; release; end`。hostごとの分岐をfield scriptへ複製せず、wrapper indexからdata tableを開きます。release manifestは `READY_TO_SERIALIZE_OBJECT_REUSE_ONLY`。新規object、推測座標、未解決Tohoku hostは書き込みません。

## 5. fail-closed条件

- engine ABI probe不成立。
- exact input SHA不一致。
- named allocation不在／重複／fill byte不在。
- allocation領域が宣言fillでない。
- current script pointer、object数、local ID、座標が証拠と違う。
- internal ID 252, 253, 254, 256〜276, 282がwild/event payloadへ出る（公式ストライク255は許可）。
- unlock cycle、route欠落、unknown symbol、dialogue/FSM不足。

これらは全てbuildまたはvalidatorを失敗させます。

## 6. engine adapterの未確定項目

`manifests/engine_adapter_requirements.csv` がhook単位の契約です。添付資料にはallocator本体、save free block、battle callback ABI、message charmap/window幅がないため、fail-closed adapterを同梱し、release link時に置換します。
