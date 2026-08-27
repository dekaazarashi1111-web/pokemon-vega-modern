# USER-20260827-STAGE56-TEST-READY-SAVE — Stage56標準テスト用セーブを生成・配置する

- Status: `IN_PROGRESS`
- Lane: `qa/save/codex-battle/ipad`
- Depends on: `USER-20260827-COLLECTION-SUPPLY-V1-IMPLEMENTATION`、`T27`〜`T30`
- Queue ID: `USER-20260827-STAGE56-TEST-READY-SAVE`
- Baseline: Stage 56 / ROM SHA-256 `9309c073798dc363174458ebcb75bf3f1e86d475dcd129b74875d5a6bb875778`

## 目的

軽い実機確認をすぐ始められる標準テスト用`.srm`を、Stage56 ROM自身の通常save APIから決定的に生成する。Codex対戦受付前、博士のポケモン／図鑑／ランニングシューズ取得済み、全個体服従、Lv.100ミュウツー先頭を固定profileとし、今後のiPad配置でも同じprofileを既定にする。

## 固定profile

- field: group 96 / map 5 / `(20,20)`、Codex対戦受付前の通常field。
- 進行: `FLAG_SYS_POKEMON_GET`、`FLAG_SYS_POKEDEX_GET`、`FLAG_SYS_B_DASH`を設定する。
- 服従: badge flag `0x0820..0x0827`を全設定し、交換個体を含むLv.100までを服従対象にする。
- party: 6体。slot 1はミュウツーLv.100、ミュウツナイトY、サイコキネシス／れいとうビーム／10まんボルト／はどうだん。slot 2に博士の御三家アクタシを保持する。
- save: blank flashから自然new gameを初期化し、ROMの`FlagSet`、`CreateMon`、`SetMonData`、`CalculatePP`、`TrySavingData`を使う。生成済み`.srm`のchecksumやparty byteをhost側で手編集しない。
- iPad: ROM basenameと一致する`56_collection_supply_v1.srm`としてlive mGBA save directoryへ原子的に配置する。実機プレイ／人手承認は完了条件に含めない。

## 必須成果物

- standard QA save profileのmachine-readable config。
- Stage56以降へ再利用できるsave generator／exact-ROM mGBA verifier。
- `.local/`の131,072-byte Stage56 save、slot別fresh-load証跡、自然Continue証跡。
- iPad上のStage56 ROM／同名save配置とread-back証跡（端末固有pathはtracked成果へ残さない）。

## 受入条件

- [ ] Stage56 ROM identityが固定値と一致し、ROM・既存save・原本を変更しない。
- [ ] blank saveから通常ROM APIで2世代saveを作り、full saveとslot 0／1単独をfresh coreで読める。
- [ ] 自然Continue後にgroup 96 / map 5 / `(20,20)`の通常fieldへ復帰し、Codex受付が利用可能である。
- [ ] ポケモン取得、図鑑取得、ランニングシューズ取得の3 flagがsave/reload後も設定済みである。
- [ ] badge flag 8件がsave/reload後も設定済みで、CFRUのbadge-count服従契約上Lv.100まで服従する。
- [ ] party 6体、先頭ミュウツーLv.100、held item 761、move `94/58/85/366`と各正規PP、slot 2アクタシをfresh-loadで確認する。
- [ ] profile、generator、runbookを正本化し、今後のStage配置で同じ標準profileを再利用できる。
- [ ] RetroArch停止、live config／mGBA save directory再解決、一時名転送、size／SHA-256 read-back、既存成果保全を満たす。
- [ ] 実機プレイ／人手承認を要求せず、focused test、task graph、private guard、diff checkをPASSする。
