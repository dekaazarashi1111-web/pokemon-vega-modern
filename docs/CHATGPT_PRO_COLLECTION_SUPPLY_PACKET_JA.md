# ChatGPT Pro 全収集・供給設計パケット

## 目的

world runtimeのバグ修正と並行して、ChatGPT Proに次の未確定設計を完成させるための
入力ZIPを生成する。Proの返却物は、バグ修正後にCodexが短い実装batchへ分割できる
symbolic key単位のCSVと設計書に固定する。

- 全フォームの入手・除外方針
- G-Max可能個体の取得方針
- 全道具の供給・除外方針
- 既存Raidのrotation pool割当、物理Raid入口、報酬
- 既存NPC／service／point交換所を再利用するための要件

現行ROM、save、patch、私有入力はZIPへ含めない。Stage53の物理map／NPC IDは誤同定を
含む再調査中なので、Proには確定させない。

## 入力監査の結論

| 対象 | 行数 | 現状 |
|---|---:|---|
| canonical Species | 1,621 | symbolic key一覧を同梱 |
| 通常図鑑完成対象 | 1,206 | Stage26で設計・実装済み。再設計せず回帰対象にする |
| 進化入口フォーム | 10 | Stage26の研究タマゴ経路を保持する |
| 全フォーム | 388 | 全行を返却CSVで一度ずつ分類する |
| optional form | 272 | 完成数から外しただけで取得経路は未設計 |
| リージョン範囲 | 63 | Alola 20、Galar 22、Hisui 17、Paldea 4。内部補助・戦闘形態を個別判定する |
| G-Max form | 34 | 巨大化Speciesを直接配らず、base個体のG-Max bitを使う |
| Item | 999 | 明示供給109、Vega既存供給宣言のみ362、明示供給なし528 |
| 用途不明表示Item | 68 | `ITEM_KEY_NONE`を含む。使用可能品と決めつけず内部／予約監査を行う |
| Raid manifest | 256 | 125共有捕獲key、撤回済み低レベル物理入口6。全行をpoolへ再割当する |
| 会話だけに見えるNPC | 118 | Vega由来84、source復元24、無効復元10。使用前の個別再監査が必要 |

上のItem件数は「現在の監査資料で物理供給をどこまで証明できるか」を表し、
528個が即座に入手不可という意味ではない。Proには全999行を、入手可能、有限、story key、
service専用、内部未使用、危険な無効化対象へ分類させる。

## パケットが固定する方針

- 正当な保存可能フォームには、野生、孵化、進化、研究タマゴ、form service、Raidの
  いずれかを与える。DPE内部補助、Mega、戦闘中変身、Tera、G-Max表示形態は直接配布しない。
- G-Maxは`ITEM_KEY_DYNAMAX_CANDY`の反復供給と、対応Raid捕獲時のbit付与を併用する。
  G-Max可能な34 base種はRaid poolにも含める。
- 道具は一律店売りにしない。通常店、BP、研究ポイント、Factory、Raid、field item、
  NPC gift、wild held itemを用途と進行に応じて分担する。
- 必須進化品・フォーム変更用消耗品を、一度限りのfield itemや低確率盗難だけに依存させない。
- Raidは専用map／ロビー／full-screen UIを増やさず、12〜24のSIMPLE_EVENT入口と
  rotation poolへ集約する。既存256行のspecies、capture policy、unlock、共有捕獲stateを保持する。
- PC容量はBox 14外部vaultを使う。フォーム別図鑑完成ledgerやROM内PC拡張は追加しない。
- NPC 118件は候補一覧としてだけ渡す。Proは地域・役割・menu・必要容量を設計し、
  Codexがworld修正後に原作Vegaの意味と実A入力を確認して物理IDへ束縛する。

## Windows側の成果物

- ZIP: Windowsの「ダウンロード」内 `Pokemon-Vega_CHATGPT-PRO_COLLECTION-SUPPLY-V1_INPUT_20260825.zip`
- SHA-256: `b93d0b8cdf758694084e98d7101074ea5c1886b9985fca1bd526c55404a28c27`
- サイズ: 97,131 bytes
- 期待する返却ZIP: `Pokemon-Vega_COLLECTION-SUPPLY-V1_IMPLEMENTATION-READY.zip`

ZIP内の`00_START_HERE_JA.md`から読み、`01_CHATGPT_PRO_PROMPT_JA.txt`をChatGPT Proへ
貼り付ける。OpenAIの公式ファイル対応表は一般的な文書・表形式を案内しているが、ZIPの
自動展開を明記していない。ZIPを直接読めない場合はWindowsで展開し、中のMarkdown、TXT、
CSV、JSON、Pythonファイルをアップロードする。パケットは28ファイルなので、ProのProjectへ
置く場合は公式案内の40ファイル上限内に収まる。

- OpenAI公式: <https://help.openai.com/en/articles/8983675>
- OpenAI Projects公式: <https://help.openai.com/en/articles/10169521>

## 返却物の機械検証

Proは`submission_template/`を`submission/`へ複製して完成させ、次をPASSさせる。

```bash
python tools/validate_submission.py submission --packet-root .
```

validatorは少なくとも次を拒否する。

- 388フォーム、34 G-Max、999 Item、既存Raid 256行の欠落・重複
- baselineのSpecies、form category、Item role、供給証跡の書き換え
- G-Max formの直接配布、ダイマックスアメの非再生可能化
- G-Max可能base種がRaid poolに存在しない設計
- 既存Raidのspecies、capture policy、unlock変更
- hostのないpool／reward、min/max逆転
- world修正前のmap group／map／local／object ID確定
- `TODO`、`TBD`、`未定`、open questionの残存

## 再生成

ワークスペース直下で次を実行する。

```bash
python3 scripts/build_chatgpt_pro_collection_supply_packet.py
```

生成器は入力件数、manifest、全ファイルSHA-256、禁止binary／private path、ZIP CRC、path traversal、
展開後validator self-test、byte決定性、Windowsコピーhashをfail-closedで検査する。正本件数が
変化した場合は、固定値を機械的に書き換えず、取得・道具・Raid・worldの変更理由を再監査する。

## 実装開始条件

Pro返却物だけでは現行ROMの全入手可能性を証明しない。別セッションのworld runtime修正後に、
Codexがexact map／NPC／script root、flag／var／save owner、free object slotを再監査し、batchごとに
build、mGBA、通常save／Continue、実機入力を通してから実装済みと判定する。
