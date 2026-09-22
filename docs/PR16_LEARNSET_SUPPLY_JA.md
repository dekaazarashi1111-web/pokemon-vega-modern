# Issue19: Tutor/追加archive consumer（host受入済み）

保存済み不足技archiveを全3342 owner/consumer行・1232共有行・3順序template・最大差分深さ8のPLA1へ同値圧縮（21383 bytes）。新規30試験/145878 C照合/独立2生成を受入。殿堂入りgate・raw40行ページ・既習得除外・188owner拒否と読取専用game adapterはhost fixture限定。実ROM ABI/接続・新Wiki・通常操作E2Eは未完。

成功run `35726123952` / HEAD `09847331130d1b6764733f09bb8d09bb2bbe6c16`。PLA1 SHA-256 `499714cc04fd43ecb59ac45d8d23dad6badbc0137189c4fbcb8facbe13c46d13`。正本 `content/modernization/pr16_learnset_supply_checkpoint.json`。

machine26308技/tutor1909技、最大machine131/tutor14行。元の順序とownerを保持し、3つのtemplateと有界XOR差分で圧縮。独立validatorは全record境界/参照/未参照/重複を検査し、C decoderは呼出し行の範囲・型・深さ・padding・出力容量を検査する。Cが全image構造walkを行ったとは主張しない。

新規C照合内訳はdecode3342、page35592、Tutor bit106944、計145878。旧受入のhost/native再実行0、今回ARM compile0/ROM変更0/native0。Floette1029の不足machine12技はデータとhost列挙までで実供給未受入。

## 次の未完

Issue19: 保存PLC2候補284b8822と受入済みPLA1の21383 bytesを再利用し、実ROMのTutor通常/特殊ABIおよびarchiveページ数・選択callbackを明示ownerへ束縛する。新しいARM moduleだけを配置・検証し、別候補Wikiと変更影響のBag/戦闘/習得選択/Save/Continueへ進む。30試験/145878照合/独立2PLA1生成と旧96試験・4入口nativeの単純再実行は禁止。

特殊Tutor IDを通常slot0..63へ平坦化しない。殿堂入り0x082C・Bag技メモリー経路・mode0/1・raw40行ページ境界を保持。188非学習owner/保存4技・PP/P03進化LR/通常level-up/正式BP/P08/旧Wiki/基準ROMは不変。Floette12技のデータ保持を実供給受入へ昇格しない。host fixtureを実ROM/実操作へ読み替えずmerge/releaseしない。

配置計画はintegration_modulesのoffset23045368、既存declared範囲内21383 bytes。ROM preimage/新ARM容量/実hookは未検証。予約領域は変更しない。

## 初回設計（履歴）

# Issue19: Tutor/追加archive consumer

Task `USER-20260922-LEARNSET-SUPPLY`。WIP: Actionsの新規host照合前。既存のPLC2四条件入口受入は不変。

保存済みpayload（run35659593954）とFloette差分（run35663067820）だけから不足技archiveをPLA1へ同値圧縮する。1671 owner×2consumer、1232共有行、3順序template、深さ8以下のXOR差分で21,383 bytes。最大machine131行とtutor14行、Floette1029の不足machine12行を保持。元の技順序をID順に並べ替えず、188非学習ownerはlookup対象にしない。旧ROM/祖先/通常Floette表へのfallbackなし。

新規C decoderは範囲・型・循環/深さ・padding・capacityを確認してから出力し、不正入力では出力を書かない。技マシンは既存raw40行単位（mode3..6）、probeはmode2、tutor archiveはmode7。既習得4技を除く前にページ境界を切る。殿堂入りflag0x082Cがないと追加archiveを列挙しない。新規game adapterはmode0/1を受入済みconsumerへ委譲する契約で、fixture検証に限定する。

Tutor通常slot0..63は明示ownerの16byte互換bitを読む。特殊Tutor ID、実ROMの呼出しABI、ページ数/選択/UI callbackの実接続は別工程であり、64以上を通常表へ押し込まない。新規adapterをhostで呼んだだけでは実供給・ゲームプレイ・Save/Continueを受入にしない。

## 未完境界

実ROMのTutor入口と特殊条件、archiveのpage count/選択callbackを実測して束縛する。保存PLC2候補 `284b88223be484a1f0a674d242bc7f4447258bf79cdd5a04b54dadb928d85c85` と新PLA1を再利用し、新しいARM moduleだけを配置する。旧96試験・4入口direct probe・元payload生成は再実行しない。新候補Wikiは旧Wikiと別pathへ作成し、変更影響のBag/戦闘/習得選択/Save/Continueへ進む。

現段階はROM変更0、ARM compile0、native0、実供給未受入。正式BP/P08、旧Wiki、保存4技、P03進化LR、baselineを変更しない。Issue19全体、merge、releaseは未完。
