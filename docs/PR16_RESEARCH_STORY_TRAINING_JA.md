# PR16 Lv7自然習得・後継保存と自宅回復境界

## 新規区間と発見

受入済みgrowth.srm（artifact10944976226）から新規194入力/19042framesを前進実行した。野生ヒメグマLv4に勝利し、41経験値でLv6→7、すいとるを自然習得。トレーナー戦はこの区間0。新しい候補ROMへの変更や経験値/状態注入はない。

自宅map4/0のNPC local1 (8,4)に(8,5)から会話すると「まだ ふねは うごいていません」。HP13/23・麻痺は変わらない。実ROMのobject scriptは0x09220CD0で、T17 portalのearly-gate→0x09220CF8 locked→msgbox/release/endに繋がる。`tools/regression/rom_runtime.py` はmap4/0 local1を「Hakuji research object」として上書きするが、通常開始の実画面では自宅の母親である。完全なpointer鎖・原本SHAは開発 `diagnostic.json` に固定した。

過去の「母親の通常回復」という解釈は、敗北後の自動帰宅回復と区別しなければならない。過去のSave/HP21保持や敗北復帰の原本自体は変更しない。今回、母親との会話による通常回復は **未受入**。原作/stage16の旧scriptと渡航ownerを未照合のまま、恒常的に回復を注入したりportalを別NPCへ移設したりしない。

## 新しい保存点

通常Save counter4→5。後継training.srmは131088 bytes、SHA-256 `e3ff50a1d88d24db28b4996440cf11c0114fa75f228c238f9e2e87fb122ac48a`。map3/0 (4,27)、party1、RP0、Lv7、EXP245、HP13/23・麻痺、キズぐすり0。

別process/coreでのContinueは34入力/2572frames。全party600bytes/Flash128KiB/ledger/位置/counter5を保持。party一覧・情報・能力/経験値・技PPの4画面が訪問後と全byte一致。ひっかく31/35、しっぽをふる30/30、すいとる25/25、4枠目空。一時戦闘flags/outcomeだけ0へ戻る。通常Saveはこのcold processでは行わず、Flash+RTC全131088bytesは不変。

## 実装・検証

`pr16_research_story_training.py` は旧oracleを編集せず、新しいinput/observe/Save対応、自然野生勝利、習得の実画面原本、非回復の全party一致、独立Continueを結合する。bool整数別名、fixture/host write、余剰Save、unknown command、偽の回復・trainer勝利・研究到達、画面/位置/原本交換を拒否する。新86検査は初回全成功。実画面は49+7枚、全56枚。OCR不使用。

開発native2と正式Actions native2は別会計。旧受入367/301/114入力・starter/RP/UI/BP/P08、guard subprocess、compileは再実行しない。固定候補e1efb100…/runner67096f8c…/runtime10898620034/data10898510128を継承。バイナリ・ROM/save/runner/PPMはartifactだけに保持し、GitにはUTF8 code/test/原本JSONとログだけを入れる。

## 次の未完作業

この新区間のActions runがあれば再生せず、全必須stepとartifact/通常Save/画面原本を終端回収する。正式受入後はT17より前の原作Vegaまたはstage16の同一object/previous_scriptを照合し、序盤の正規回復と既存渡航の共存を最小差分で修正・検証する。その変更影響に必要な回復/渡航だけを試験し、training.srmから通常ストーリーへ戻る。原本不一致なら推測でpatchせず診断境界を保持する。

研究活動施設map96/0→98/3への自然到達、全ストーリー、releaseは未完。PR16 draft/open・未merge、active baseline変更なし。一般CIのaction_required/既知のlegacy不一致と専用新区間の成功は別記録。全体private guard成功を主張しない。
