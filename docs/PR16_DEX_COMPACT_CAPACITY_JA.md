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

ローカル新51 host tests PASS。既存38件のbehaviorを新compact Cへ適用し、新しく4 API×uint16全65536入力＝262,144件を実Cで完全比較した。公式mask全151 bytesとpaddingも一致。生成checkは読取専用。

専用Actionsで4 translation unit（codec、compact adapter、lookup、save bridge）をARMv4Tへcompile/linkし、全API保持時のfootprintとtoolchain identityだけを出力する。これは配置前の容量測定であり、ROM接続・native保存受入ではない。ARM binary、ELF、object、ROM、Save、runnerは公開しない。

## 次の条件

未割当3151 bytesは連続1704/1240と微小断片に分かれるため、compactだけで容量解決と断定しない。旧T09 level-up pointer owner（6484 bytes）の全preimage、現在のtyped roots、外部参照、旧dataの保持を監査中。署名と到達性の証明が完了するまでleaseもROM patchも採用しない。Stage61 scheduler全mode・consumer全接続と通常Save/独立cold Continueが未完。
