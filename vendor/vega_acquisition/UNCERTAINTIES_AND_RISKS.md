# 未確定事項・判断が必要な仕様・危険な仮定

## 推奨defaultとして確定したもの

1. 完成対象は1206。恒常フォームは原則optional、別全国種への進化入口10だけ必須・完成数0。
2. 未接続御三家11はprimary研究タマゴ。既存13は登録済みbackupのみ。
3. Cosmogは一save二回まで。分岐を一ROMで両方完成可能。
4. Kubfuは一全国種必須、Urshifu styleはフォーム実績扱い。
5. Vega既存eventは意味をprimaryとして保持し、物理証拠がない間はKanto救済をreleaseする。
6. RTCなしでもレーダー固定modeまたは限定fallback tokenで詰ませない。

## ユーザー判断で変更可能な点

- フォームを別実績として何種類まで数えるか。本packageの1206完成判定とは別ledgerにすることを推奨。
- 既存到達13御三家のbackupを登録済み限定にするか、全員へ一回配るか。前者を推奨。
- Cosmog二回配布を許すか、片方をbranch-change itemへするか。個体収集を尊重して二回を推奨。
- Kanto rescueの難易度。現在はpostgame Lv.68〜100の任意導線を想定し、個別levelは125 catalogに記録。
- legacy Tohoku eventが完全に健全だった場合もKanto救済を残すか。共有ledger付きの任意救済を推奨。

## 最も危険な仮定

1. **engine ABI**: party/PC/egg、battle callback、item rollback、evolution、message/listの正確なsymbol/呼出規約は添付資料だけでは証明できない。
2. **save余白**: 相対layoutは確定したが、実save block/sector ownerはallocator結果が必要。
3. **legacy event**: 場所名・攻略情報だけでは現ROMのentry、Species ID、flagを証明できない。
4. **451 evolution edge**: edge存在と条件供給の完全実行は別。特定技、場所、手持ち、時間、累積counterを全件試験する必要がある。
5. **text/charmap**: 日本語台詞は短くしたが、実font幅、制御code、window行数はexact UI testが必要。
6. **allocator contract**: source bundleにallocator本体がないため、buildは結果JSONを要求するだけで自ら空き領域を推測しない。
7. **existing script symbol**: Kanto JSONのstub symbolとexact stage pointerが一致しない場合、serializerは停止する。自動で上書きしない。

## 未完了とみなす条件

ROMを添付していないため、patched ROM、exact-ROM test PASS、Tohoku primary昇格、repository固有adapter完成を主張しません。`OUTPUT_STATUS.json`の `DESIGN_COMPLETE_PHYSICAL_AUDIT_REQUIRED` 行が残る限りrelease完了ではありません。
