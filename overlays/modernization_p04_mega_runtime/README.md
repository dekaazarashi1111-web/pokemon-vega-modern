# P04 Mega runtime oracle

固定CFRU-JP `mega.c` の進化表探索をhost testで照合するためのoracleです。
Stage71 ROMへ新規codeを注入するものではありません。実ROM変更は、Stage70が
移設した進化表に通常Mega順方向49 entryとrevert逆方向49 entryを追加するだけです。

判定は現行projectの `VegaBattlePolicyCanMega`、固定CFRU-JPのmode別
keystone判定、進化表のexact stone照合の順です。通常戦だけMega Ring 580を
所持している必要があり、Frontier/Linkの既存例外はproject policy通過後にだけ
有効です。上流Mega Brawlは`megaData.done`を立てませんが、現行projectの
side-used gateが先に働くため、実機上の複数回挙動は最終mGBA確認待ちです。

交代ではMega姿を維持します。ひんし時は既存
`Faint_FormsRevert -> TryFormRevert`によりbaseへ戻り、`megaData.done`は維持される
ためrevive後の再Megaはできません。通常の戦闘終了は既存
`EndOfBattleThings -> MegaRevert`、特殊戦闘の中断・saveは既存の戦闘前party
snapshot ownerが正常化します。
