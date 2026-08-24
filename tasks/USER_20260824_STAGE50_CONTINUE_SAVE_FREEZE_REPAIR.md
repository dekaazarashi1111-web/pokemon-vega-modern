# USER-20260824-STAGE50-CONTINUE-SAVE-FREEZE-REPAIR — Stage 50のContinue復帰を修正する

- Lane: `save/map/field/qa/release`
- Depends on: `USER-20260824-STAGE49-INTERACTION-OWNERSHIP-REPAIR`、`T26`〜`T30`
- Queue ID: `USER-20260824-STAGE50-CONTINUE-SAVE-FREEZE-REPAIR`
- Baseline: Stage 50 / ROM SHA-256 `af9bd50194e16fc409a31b6c179ec8c53a15d6961220daf29a0bd38a2b7dc92d`

## 再現対象

1. Stage47由来のCodex受付前セーブをStage50で「つづきから」読み込むと、NPCまたは地形の一部が破損表示になる。
2. 読込後は1歩だけ移動できるが、その直後からfield入力を受け付けなくなる。
3. 既存セーブはCodex受付前へ試験用に進行させた生成物であり、通常のmap復帰情報と一致していない可能性がある。

## 受入条件

- [x] iPadで報告されたStage50セーブをbyte同一で退避し、fresh libmGBA coreの自然Continueから再現する。
- [x] Continue直後のmap、座標、map view、object state、callback、script contextを記録し、ROM側とセーブ側を切り分ける。
- [x] Codex受付map `96/5`、座標`20/20`で、描画が正常かつ2歩以上の実入力後もoverworld callbackと入力復帰を維持する。
- [x] Codex受付NPCの配置／script ownerをexact回帰し、左右または下方向へ移動する自然入力で無限script・連続遭遇・入力lockを0にする。
- [x] Stage50のinteraction owner、trainer視線、511番水道、知恵の洞窟、Dark Pulse、Focus Sashを回帰させない。
- [x] 必要ならStage51 ROMをclean基準から再生成し、旧Stage50を上書きしない。
- [x] 通常手順で作ったCodex受付前セーブを新規発行し、両save slot、自然Continue、map view、複数歩行を検証する。
- [x] iPadへ新しいROM／セーブをversioned filenameで配置し、旧Stage49／Stage50と既存savestateを変更しない。
- [x] `design/run_log.md`、`design/version_log.md`、`design/current_state.md`、task状態、commitを完了する。
