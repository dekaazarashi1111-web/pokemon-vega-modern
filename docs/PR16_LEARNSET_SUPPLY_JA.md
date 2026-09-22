# Issue19: ELF配置修復と新供給4hookの実ROM ABI受入

ELF実loadとROM配置の4byteずれを保存ELFから修復し後継6e88a021を独立2配置一致で確定。新供給4hookを28代表owner×独立2process、合計21392callで検証。特殊Tutor/HoF/raw40ページ/既習得除外/タマゴ/選択境界/保存4技PPを確認。直接ROM診断のみで通常操作・新Wiki・物理供給は未完。

候補 `6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2` / 33554432 bytes / CRC32 `00F31AF7`。run35748601580、入力HEAD `740ecf0a94de514fa735e4697f5d6129d45520e4`。

正本 `content/modernization/pr16_learnset_supply_alignment_checkpoint.json` / `content/modernization/pr16_learnset_supply_native_checkpoint.json`。旧ec5992aaの独立2link結果は履歴として保持するが、実load不整合のため実行可能な現役候補とは扱わない。旧builderは固定証拠復元専用。先頭FF4bytesを補い、元ELF命令/全hook/PLA1/PLC2は不変。ARM再compile/link0。

## 次工程

Issue19: 修復後候補6e88a021のcontent/modernization/pr16_learnset_supply_alignment_checkpoint.jsonから保存ELF配置を復元し、別候補Wikiと変更影響の通常操作（Bag入口・殿堂入りgate・40行ページ選択/取消・習得選択・戦闘・Save/Continue）へ進む。旧ec5992aaは配置ずれがあるため現役候補へ戻さない。新4hook直接診断/16配置試験/旧24試験/ARM/PLA1/PLC2を変更影響なしに再実行しない。

## 前段階（履歴・現役候補ではない）

# Issue19: Tutor/追加archive consumer（実ROM配置受入済み）

run35732715452の新供給ARM2784 bytes・PLA1 21383 bytes・4hookを候補ec5992aaへ配置し独立2生成一致を確認。特殊Tutor152..160 bodyとPLC2保存segmentは不変。14試験は初回失敗runの成功部分を継承。新native/通常操作/新Wikiは未完。

候補SHA-256 `ec5992aa139fb87ddc27857a687dd7146c13a2dffbc88227aa44c1a26bea569f` / 33554432 bytes / CRC32 `9A91E7FB`。正本 `content/modernization/pr16_learnset_supply_link_checkpoint.json`。

固定PLC2親から保存byteを適用した候補であり、clean-ROM最終2生成や通常操作の受入ではない。新ARM8compile/2linkは完了runの値。今回の記録では再実行0。初回記録run35734221410は失敗時artifactのskipを誤拒否してpush前に停止し、failureのまま保持。保存4技/PP、通常level/P03進化LR、正式BP/P08、旧Wiki、baselineを変更しない。

## 次工程

Issue19: 保存候補ec5992aaと供給ARM/PLA1/link.jsonをhash検証で復元し、新しい4hookの実ROM ABI・Tutor特殊条件・raw40行ページ選択を検証する。既受入ARM/PLA1生成/14試験/旧4入口probeを再実行しない。次に別候補Wikiと変更影響のBag/戦闘/習得選択/Save/Continueへ進む。

## 前段階の記録（履歴）

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
