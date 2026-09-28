# PR16 母親回復と渡航の共存

母親previous_script0x0817BCBBを固定Vega原本で確認。未解禁時と渡航辞退時を元会話/回復へ15bytesで委譲し、canonical全179bytes一致と52専用検査を確認。次はtraining.srmから新候補で実会話・回復・Save・独立Continueだけを測定する。研究施設自然到達/実渡航nativeは未受入。旧194/367/301/114入力と旧RP/UI/BP/P08は再生しない。

原本取得run36363658910、artifact10946690893。元script/会話1024bytes・回復subscript12bytes・movement8bytesは現候補と原本で一致。NPC位置・解禁flag・承諾時渡航・帰還・保存codeは不変。goto委譲のみで回復を注入しない。旧locked text領域と全symbol配置は保持。

候補SHA 06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5。52試験、全ROM rollback、変更外不変、16通りのflag/yes-no、canonical一致を確認。driverは候補SHAを固定したCから通常compileし、実行ファイルは書換えない。初期探索の実行ファイル文字列更新方式は正式採用しない。

このsource checkpointはnative受入ではない。一般CIの既存失敗/action_requiredとは区別する。merge/release/active baseline変更は禁止。

## 新規回復oracle準備

母親回復の新oracle73検査と81/cold34入力の開発原本を固定。source52検査は再利用。次は通常compile済みbuild artifact10946449847を照合し、pr16-home-recovery-native.ymlで新区間2processのみ正式測定。旧194/367/301/114入力を再生しない。

初回73試験のうち、不完全schemaの例外2件と実入力未結合1件を修正後73全成功。初期探索の実行ファイル文字列更新方式は正式採用せず、source通常compile版で独立測定する。冷起動開発はその通常compile版を使用。native正式受入は未完。

## 完走済みnativeの保存処理失敗から回収

元run36366437821はfailureのまま保持。回復/Continueの実processはともにrc0、stderr空で、26画面・2入力原本・3Save・候補・通常compile runnerはartifact10946773841に残存。第2回copy2がread-only候補に再書込して失敗した。ゲームを再生せず全原本を照合し、同一immutable保存の再実行は書込しない方式へ修正。新規7検査のみ実行し、旧52/73検査は再利用。以下のsource/runは回収・公表のsource/runで、実測source ee915a7fe4f9ad987a04063c094f30f5509ce760 / run36366437821はJSONに別記する。

## 母親の自然回復・Save・独立Continue

母親との元会話でHP13/23→23/23・麻痺解消・ひっかくPP31→35、通常Save5→6と独立Continueのparty/Flash/4画面保持を限定受入。次はartifactのrecovery.srmを作業コピーとして通常ストーリーへ。map4/0 (8,5)、Lv7/EXP245、RP0、キズぐすり0。母親81入力と旧194/367/301/114入力・starter/RP/UI/BP/P08は再生しない。渡航16条件はstatic検証で、解禁後実渡航native・研究施設自然到達・全ストーリー・releaseは未完。

正式source `f895a324d160055e70bd0788208907e2b4044a8f` / run `36366801337`。81入力/19画面でSave5→6、別core34入力/7画面。全Save131088bytes SHA 0de597b9e95fd33d62de19610a166ed6dd650a5ba6a4309770083cefe9560773。600partybytes中ひっかくPP/麻痺/HPの3bytesだけが変化、残り597bytes不変。RAM ledger分32→33とチェックサムは全byte SHAから確認し、残高や他ownerの改変と区別した。終端artifact/全必須stepの外部確認は次段階。

## 外部終端確認済み

run 36366801337、job 108754722968、全11必須step成功。completion 8be37140565ed514ce39bfcefe7707d5a66bdc76。artifact 10947623338 の全ZIP/26実画面/3Save/runner/候補/commit textを検証。追加native/compile/unit0。これより上の終端待ちは記録時点の履歴。現在の再開点はrecovery.srmで、回復区間を再生しない。
