# Box 14⇔Windows固有個体庫

Stage 47以降では、ゲーム内のBox 14をWindowsとの移動専用boxとして扱える。既存PCの箱数は変えず、
Box 14に置いた個体だけを`vega-codex-battle`経由でまとめて預け入れ・引き出しする。

## 使い方

ROMとCLIを生成・導入する。

```bash
make windows-box14-vault
bash scripts/install_vega_codex_battle_cli.sh
```

任意mapの通常fieldで、PC・menu・会話・戦闘を閉じて状態を確認する。NPC前へ移動する必要はない。

```bash
vega-codex-battle vault status --json
```

Box 14の全個体をWindowsへ移す。

```bash
vega-codex-battle vault deposit --json
```

現在ROMと互換なWindows個体をすべてBox 14へ戻す。

```bash
vega-codex-battle vault withdraw --json
```

一部だけ戻す場合は、`vault status`が返すrecord IDを指定する。

```bash
vega-codex-battle vault withdraw <record-id> [<record-id> ...] --json
```

途中で通信が切れた場合は同じ`vault deposit`または`vault withdraw`を再実行する。owner-onlyの
`pending.json`から完了slotを照合して続行するため、手動でpendingやblobを編集しない。

## exact移動の範囲

1体につきPC保存中のCFRU展開済みBoxPokemon 80 byte原本をそのままWindowsのowner-only blobへ保存する。
個体は再生成しないため、personality、OT、ニックネーム、言語、マーキング、種族・form、持ち物、経験値、
なつき度、技・PP、努力値・個体値、コンディション、Pokerus、出会い・ボール、特性・性格・色違い・
ribbon・タマゴ・Tera等、同じ80 byteに含まれるbitは変わらない。持ち物も個体と一緒に移動し、bagへは
戻さない。mail本文はBoxPokemon外部データなので、mail持ち個体を含む預け入れは拒否する。

預け入れはWindows blobとbatch状態を先にfsyncし、その後1slotずつROMの通常saveで削除する。
引き出しはWindows batch状態を先にfsyncし、ROMの通常save成功後にWindows recordを削除する。
hostはversioned request spanと128-byte transfer block以外のsave、party、boxを直接書き換えない。

## 今後のROM

Windows recordごとにBoxPokemon幅とSpecies／Move／Item／Ability namespaceをまとめたABI SHA-256を
保存する。後続ROMでも同じ`box14_vault` protocolとABI fingerprintを公開すればそのまま引き出せる。
ABIが変わったROMでは古い個体を保持したまま引き出しだけを拒否し、誤ったID空間へraw dataを入れない。
固定ROM filenameには依存せず、導入済みprotocolのROM SHA-256／CRC32で実行対象を確認する。
