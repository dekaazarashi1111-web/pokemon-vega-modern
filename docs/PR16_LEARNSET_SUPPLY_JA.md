# Issue19: Tutor/追加archive consumer

Task `USER-20260922-LEARNSET-SUPPLY`。WIP: Actionsの新規host照合前。既存のPLC2四条件入口受入は不変。

保存済みpayload（run35659593954）とFloette差分（run35663067820）だけから不足技archiveをPLA1へ同値圧縮する。1671 owner×2consumer、1232共有行、3順序template、深さ8以下のXOR差分で21,383 bytes。最大machine131行とtutor14行、Floette1029の不足machine12行を保持。元の技順序をID順に並べ替えず、188非学習ownerはlookup対象にしない。旧ROM/祖先/通常Floette表へのfallbackなし。

新規C decoderは範囲・型・循環/深さ・padding・capacityを確認してから出力し、不正入力では出力を書かない。技マシンは既存raw40行単位（mode3..6）、probeはmode2、tutor archiveはmode7。既習得4技を除く前にページ境界を切る。殿堂入りflag0x082Cがないと追加archiveを列挙しない。新規game adapterはmode0/1を受入済みconsumerへ委譲する契約で、fixture検証に限定する。

Tutor通常slot0..63は明示ownerの16byte互換bitを読む。特殊Tutor ID、実ROMの呼出しABI、ページ数/選択/UI callbackの実接続は別工程であり、64以上を通常表へ押し込まない。新規adapterをhostで呼んだだけでは実供給・ゲームプレイ・Save/Continueを受入にしない。

## 未完境界

実ROMのTutor入口と特殊条件、archiveのpage count/選択callbackを実測して束縛する。保存PLC2候補 `284b88223be484a1f0a674d242bc7f4447258bf79cdd5a04b54dadb928d85c85` と新PLA1を再利用し、新しいARM moduleだけを配置する。旧96試験・4入口direct probe・元payload生成は再実行しない。新候補Wikiは旧Wikiと別pathへ作成し、変更影響のBag/戦闘/習得選択/Save/Continueへ進む。

現段階はROM変更0、ARM compile0、native0、実供給未受入。正式BP/P08、旧Wiki、保存4技、P03進化LR、baselineを変更しない。Issue19全体、merge、releaseは未完。
