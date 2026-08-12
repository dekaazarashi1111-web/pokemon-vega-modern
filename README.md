# Pokémon Vega Modern — トーホク＋カントー二地方版

FireRed日本版Rev.0からVega 2018-02-23を再生成し、DPE-JP/CFRU-JPを公開ソースからVega互換で移植したうえで、元FireRedのカントーをVega本編の中盤から任意で訪問できる高難度の第二地方として復活させる長期開発ワークスペースです。トーホクとカントーを自由に往復でき、両地方へ追加生態を配置します。最終成果は32 MiB ROMの再現ビルドと、ROM本体を含まない差分パッチです。

早期渡航は「シオウの3個目バッジ取得後、アーシア島D・Hビル初回攻略完了」を概念条件とし、実ROMの数値flagはT02監査で確定します。カントーのLv.68〜100帯は自動スケーリングせず維持し、後半認定章・リーグ・最終共鳴だけをVega殿堂入り後に解禁します。

Factory UPSをVegaへ重ねる方式は採用しません。Factory ROMは挙動・配置の参照オラクルとしてだけ使います。

## セッション開始

毎回、次だけを順に読みます。

1. `AGENTS.md`
2. `design/current_state.md`
3. `design/agent_context_map.md`
4. `design/tasks_next.md`
5. 選択した `tasks/T*.md`

```bash
git status --short --branch
python3 scripts/taskctl.py next
```

詳細資料を全件読み直さず、`design/agent_context_map.md` から目的別に絞ります。

## 重要な正本

- 状態: `design/tasks_next.md`
- 依存関係: `tasks/task_graph.json`
- タスク完了条件: `tasks/T*.md`
- 現在地: `design/current_state.md`
- 採択済み判断: `design/decisions.md`
- 全体ロードマップ: `MASTER_PLAN.md`
- 入力・上流pin: `state/source-lock.json`
- 受領物一覧: `design/import_inventory.md`
- 受領資料レビュー: `design/import_review.md`
- 育成・操作QOL: `docs/QOL_POLICY.md`
- 二地方設計のactive review資料: `design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/`

## 私有入力

ROM、IPS、UPS、元ZIPは `userfile/imports/` に読み取り専用で置き、Gitへ入れません。`inputs/private/` と `inputs/reference/` はツール向けのGit管理外参照です。入力原本へ直接パッチを当てず、生成先へコピーして処理します。

## 必要時に選ぶコマンド

```bash
make status       # 状態とRESUME/PRIMARY/並列準備候補
make plan         # PRIMARY、並列準備候補、全実行wave
make harness      # clean+Vega IPSから32 MiB T03 no-op harnessを再構築
make harness-check # 生成済みT03成果を現在の入力/configへ照合
make moves        # T03からVega固定512技＋CFRU追加551技のT04 stageを再構築
make moves-check  # エミュレータを再実行せずT04成果と現在入力を照合
make validate     # DAG、manifest、状態、受領資料の静的検査
make guard        # 私有バイナリ混入防止
make test         # unit test
```

WSLでは全体標準verifyを実行しません。選択タスクのacceptanceに必要なコマンドだけを使い、同じ検査を重ねません。

初期入力・上流取得・参照ROM生成は `make quickstart` で行います。副作用と生成先は `CODEX_START_HERE.md` を先に確認してください。

T03以降のROM stageは入力原本を上書きしません。`make harness` は固定clean ROMへVega IPSをmemory上で適用し、32 MiBへ `0xFF` 拡張して、named allocatorが許可した拡張領域へno-op moduleを配置します。

`make moves` はVega Move ID 0〜511を固定し、V3技調整を優先適用してCFRU-JPの未収録551技を512〜1062へappendします。生成したgame-encoding表、70個のVega固有effect adapter、178 pointer repointをstage 04へ配置し、固定wild battleで実際に技を1回実行します。

## 効率方針

同一hash・同一source commit・同一tool versionの検証済み成果を再利用し、独立作業は所有ファイルを分けて並列化します。正本IN_PROGRESSは1件に保ちますが、`PRIMARY` は推奨順であり、依存READYの `PARALLEL_PREP` を待ち時間やfan-outに応じて先に選べます。大規模統合を一度に行わず、no-op ROM、Move/battle/Species、育成・操作QOL、クチバ往復の順に動く成果を出してから広げます。現在対象とDAG由来の準備waveは `make plan`、マイルストーン要約は `MASTER_PLAN.md`、厳密な完了条件は各 `tasks/T*.md` を正とします。

既定QOLは、全文字の即時表示、Vega比でダッシュ25%以上・自転車50%以上の移動時間短縮、現代式孵化、経験アメ、育成値表示・変更、全体学習装置、PC一括操作です。固定仕様は `docs/QOL_POLICY.md` を参照します。

UIと追加イベントは機能優先の最小構成です。既存画面・標準menu・既存NPC/端末を再利用し、新規full-screen UI、装飾演出、長いcutsceneや多段questは原則追加しません。

## 補助ツール

ChatGPT Webを補助的な相談、要約、レビュー、画像生成に使う場合だけ `tools/chatgpt_browser/README.md` を参照します。私有ROMや非公開データは送信しません。
