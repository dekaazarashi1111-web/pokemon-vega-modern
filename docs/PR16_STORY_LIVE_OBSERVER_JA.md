# PR16 宣言済milestone向けlive observer

所有者の方針どおり、通常戦ごとのSaveは作らない。次の到達点は506→519→シオウPokecenterでの通常回復、Save、fresh Continue。

旧runnerはparty/ledgerのhashだけを返すため、未観測戦のHP/PPや進行差分を推測して続行できなかった。新しい独立runnerへ読取専用observerを追加し、同じframeのobserve/live/screenを組にする。旧runner、旧受入、ROMは変更しない。

- 全party600bytes、enemy party、動的SaveBlock1/2、legacy flags/vars、拡張flags/vars/ball/coins、ledger、objectと戦闘controllerを読取る
- legacy/expandedの進行差分、資源、UI callbackを明示検査。未知差分、未知controller、異常HP/PP、保存変化は診断停止
- 7 APIのhost書込barrierを既存generatorから継承。ゲーム側の正常処理以外のCPU/party/story書込は使わない
- 新runnerの入口は現Save101からのContinueのみ。旧NewGame/fixture経路は実行しない
- 初回nativeはSave101の同一frame raw値をphysical Saveと照合する限定probe。歩行/戦闘/Saveは行わない

49件の新規host試験は実資源解釈、2戦連結の純粋差分処理、未知/改変拒否を検査した。host成功はnative連戦受入ではない。初回probeが通っても、戦闘後adapter、全tile経路、trainer/野生owner、counter会話を解決して実測するまでシオウ到達を主張しない。

この段階のnative_postbattle_adapter_accepted、native_battle_continuation_accepted、milestone_reached、full_story_accepted、release_readyはすべてfalse。通常NationalDex、自然EXP/進化/LuckyEgg/12境界/Lv100は未完。
