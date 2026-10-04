# 図鑑runtimeの容量解決: compact lookup

正式Save101と固定候補ROMは不変。既存のnamespace/version1、1206 owner、522-byte保存ABIを変更しない。

## 実装

SID1671、公式番号1025、代表SIDを別APIのままrun/literal lookupへ変換する。2つのu16からなる4-byte descriptorでbinary searchし、傾き1・定数・literal区間を区別する。生成時のDPで論理データ量を最小化し、全区間の順序・境界・subtraction・literal範囲を検証する。

- SID: 106 descriptor＋180 literal = 784 bytes
- 公式owner: 114 descriptor＋149 literal = 754 bytes
- ownerから代表SID: 28 descriptor = 112 bytes
- 公式mask: 151 bytes
- 計1,801 bytes。旧3表＋maskの7,597 bytesから5,796 bytes削減。linker alignmentはこの論理量に含まない

代表SIDは全公式1025件で既存manifestのbase representativeと一致する最小SIDであり、生成の必須条件として照合する。SID1670と1142はowner925、公式744の代表は1142のまま。

元adapterは独立した比較正本としてbyte不変に保つ。新adapterは元sourceのSHA-256を確認し、lookupに関する6箇所だけを生成置換する。エラー優先順、出力alias拒否、CRC、reward caught clear、Factory/Codex rollbackの制御はそのまま。

## 検証範囲

ローカル新51 host tests PASS。既存37件のbehaviorを新compact Cへ適用し、元の生成checkをcompact生成checkへ置換。、新しく4 API×uint16全65536入力＝262,144件を実Cで完全比較した。公式mask全151 bytesとpaddingも一致。生成checkは読取専用。

専用Actionsで4 translation unit（codec、compact adapter、lookup、save bridge）をARMv4Tへcompile/linkし、全API保持時のfootprintとtoolchain identityだけを出力する。これは配置前の容量測定であり、ROM接続・native保存受入ではない。ARM binary、ELF、object、ROM、Save、runnerは公開しない。

## ARM実測と退役owner lease

source 8822a20ba6233bce79d23c54c499461ec0e8fd44、run37219630045/job111487163702の全10step成功。4 translation unit/1 linkで全public APIを保持し、alignment込み4,638 bytesを実測。ARM GCC13.2.1、binutils2.42。これは配置前のfootprintであり、後付けstub/veneer/consumer/save schedulerのcodeはまだ含まない。

退役候補は旧T09 species_surface_level_up_pointers、ROM offset0x01FC0998..0x01FC22ECの6,484 bytes。Stage39が旧2rootを移行し、Stage70/75の後継で現5root/8間接storage参照に追跡できる。旧baseと2mirrorのexact literalは0。正規窓の全byte走査で35候補を列挙し、8命令跨ぎ・21文字列・5音声・1圧縮画像と型を確定。見た目だけで除外していない。直接文字列rootがない1件も採用pinのconst u8[]とcharmap再符号化で全byte一致した。

`pr16_dex_capacity_lease.json` が全preimageとsource20本を固定し、`pr16_dex_lease.py` が型・根・全候補・旧row終端・旧DATAの不変と配置前後の書込範囲を検証する。新4,638 bytesはこのleaseへ収まり残り1,846 bytes。旧level-up DATA 81,885 bytesとlive空row/6参照は対象外で完全保持する。未割当3,151 bytesの窓はこの計算に足していない。

この根拠は既知source/ABIでのtable退役に限定される。任意のプログラムがアドレスを合成しないという一般到達不能性や、非正規mirror内部値の全型解析は主張しない。ROM/source/rootが変われば再検証する。

独立レビューで公開guard失敗後もalways条件のuploadが動けることを修正し、guard成功時だけ公開する。測定workflowは受入済み試験を自動で繰返さない手動入口へ変更した。今回公開されたartifactは検査済みtext2本だけであり、binary混入は0。

## 次の実装

allocatorの正式なowner移管と、実配置addressでの再link/stub/veneer容量、全diff監査、影響learnset回帰を経て候補ROMを作る。Stage61の現12,568-byte codeを丸ごと空きへcloneできるという証明ではない。Stage61の既存owner内置換・export/callsite到達性を別途固定する。

全save mode/CRC bank fallback/partial write/復旧Save前load、全SID喪失前consumer・Bag count・reward clear・Factory/Codex rollbackへの接続、通常Save/独立cold Continueは未完。正式Save101と正式ROM基準は不変。これらを受入してからtrainer131以降とシオウPokecenter通常回復へ戻り、雑魚戦ごとのSaveは作らない。
