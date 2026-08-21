# Reward Encounters V2 provenance

- Task: T24
- private原本: `userfile/imports/Pokemon-Vega_REWARD-ENCOUNTERS-V2_IMPLEMENTATION-READY.zip`
- ZIP SHA-256: `b293c9f9c65eaf7acf4a6c5707163460b095d761283dc821d920801b38262195`
- validation fingerprint: `823664fd0f53a88014f361ba592838084ad660101a724e416f3ddffb507a42df`
- baseline: T23 Stage40 `b46e28935675198db09f5947e6701918deafb49db27c03343f4b5b2ddaceb488`

`canonical_model.json` は上記read-only ZIPを共通validatorで検証した後、4 service、
24 pool entry、10 credit source、56 dialogue、5 implementation batchをstable keyで
正規化した生成正本である。private ZIPは展開先を含めて入力専用とし、ROM・BPS・mGBA
証跡はGit管理外の再生成領域へ出力する。

Stage41は既存のT08 `encounter_credits`、`VegaPendingEncounter`、Factory BP/claimを
再利用し、新しい捕獲ownerを設けない。Factory 3/7/14/21 sourceはStage28の既存
transactionをbyte identity付きで継承し、T24はwild-end chainとBP voucher、共有
Scientistだけを追加所有する。
