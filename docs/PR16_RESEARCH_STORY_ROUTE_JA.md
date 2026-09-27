# PR16 道路通常進行・キズぐすり取得と保存継続

## 受入範囲

前回の正式 `route.srm`（artifact10933499471 / SHA-256 `503e26cfdc8605ff79984afdcab3ffd9ce448f4557a8d1cdf64526ad15cdd65a`）から先だけを通常入力で進めた。道路map3/19のトレーナー戦は2回とも敗北。自宅への通常復帰と母親の回復を経て草側へ迂回し、落ちているキズぐすり1個を取得した。勝利・研究活動施設到達・全体ストーリー完成は受け入れていない。

道路map3/19 (26,17)、手持ち1体、RP0で通常Saveを1回だけ実行し、counter2→3。保存前のバッグと独立coreのContinue後のバッグはいずれも「キズぐすり ×1」で、実画面のSHA-256が完全一致した。道具はまだ使っていない。

## 実装と証拠

新しい `scripts/pr16_research_story_route.py` と専用試験は、親Save/runner/candidate/runtimeの由来、2回の敗北と通常復帰、迂回地点、実バッグ、保存と独立Continueを照合する。既受入のrunner/解析器/ROMは変更しない。

進行301入力/31904frames・49画面、独立Continue24入力/1942frames・4画面。実画面53枚のうち観測16は母親の治療中の完全暗転で、内容受入対象は52枚。この1枚だけをexact frame10080/hash/map4/0 (8,5)/lock1/敗北後という条件で遷移証拠として保持する。他の暗転を許す一般的な緩和ではない。

保存前後で全party600bytes、Flash128KiB、研究ledger、位置、向き、RP0、counter3を保持する。移動全体にわたるparty/ledger不変は要求せず、途中の通常状態変化を改変しない。戦闘の一時flags/outcomeはcold起動で0へ戻る。

開発原本は `content/modernization/pr16_research_story_route_development/verification.json`。新74試験は実原本の陽性を前提として改変拒否を確認した。最初の終端欠落試験が期待するValueErrorではなくKeyErrorになった1件は履歴を保持し、新wrapperで終端を先に検査して修正。影響する解析経路を含む新74件は修正後全PASS。旧受入試験は再実行していない。

開発native2process/2core、host/ARM compile0、ROM変更0、旧native再実行0。初回SONAMEリンク不足はmGBA起動前のloader failureとして別記録し、固定runtimeの既存復元規約どおりsymlinkを用意した。7host-write禁止barrierは同じrunnerの受入済み実装を再利用し、禁止操作を再起動しない。

## 後継保存と次工程

後継 `potion.srm` は131088bytes / SHA-256 `8e924f8f058007f204db4319304f064f5b3232256b2e41a3706f88d4e2105110`。通常Save由来の全Flash/RTCであり、savestateや進行注入ではない。候補 `e1efb1009c6e6b0ec4967bf7b20562d2330bbd933f64f7f7863cdad56eb1f842`、runner `67096f8c8a487c03957da071d0190f74542480fb051cf8e8934e1b05adee9a61`、runtime10898620034/data10898510128を維持する。

次は正式Actions終端と後継artifactを確認し、保存コピーへ `continue-story <全Save SHA>` を渡してこの地点より先だけ進める。トレーナーは未撃破。現時点でキズぐすり1個を持つ。旧NewGame/スターター/前回114入力/今回301入力を再生しない。

固定再開MD/JSONを最新停止点の正とする。ROM/save/runner/画面はartifactにのみ保持する。一般CIのaction_requiredや歴史的全体private guardをこの限定検証の成功へ混同しない。merge、release、active baseline切替を行わない。

## Actions独立測定（終端は外部照合待ち）

道路でのトレーナー敗北2回・母親の通常回復・草側迂回・キズぐすり1個の通常取得・Save counter2→3・独立Continueの所持保持を限定受入。次はpotion.srmのmap3/19 (26,17)から通常ストーリーへ。トレーナー勝利0、研究活動施設への自然到達は未完。旧starter/完走301入力/旧RP/UI/BP/P08を再実行しない。

正式source `228d31f3e3ab74dbfc089b63a75478c0d5fde1eb`、run `36330546824`。開発と独立測定の全stdout/53画面/Saveが一致。正式native2、開発native2は別会計。新74検査成功原本はsource一致で再利用し再起動0。
