# Research Economy V1 来歴

T23は、読取専用の返却原本
`Pokemon-Vega_RESEARCH-ECONOMY-V1_IMPLEMENTATION-READY.zip`を設計入力とし、
T22の正規出力Stage 39へ研究経済をproduction統合する。

## 固定入力

- Stage 39 ROM SHA-256:
  `c6d9d118e329512235e27efd876108d630b827bd8f2a8eb5b2bce63748e3f6dd`
- 返却ZIP SHA-256:
  `0cd2a68535f5543da919a6502a21321adb826dbff37d356b0cacfc697c7367de`
- canonical fingerprint:
  `2ea4497307af6aece808fd9a98158561c7c87e83cd4748b2e6d3ab8c4aa27a8b`
- canonical件数: currency 1、activity 6、rank 7、shop 23、host 9、
  dialogue 35、batch 7。

原本ZIPは展開後の実装正本として直接編集しない。builderが全entryのidentity、
共通validator、stable key、相互参照を検証し、採用した内容だけを
`canonical_model.json`と生成headerへ決定的に正規化する。

## Stage 39再監査

返却資料のStage 37 snapshotに記載された物理addressは採用根拠にしない。
Stage 39 ROM、allocation、save/RAM台帳、現行map event rootを再監査し、次を固定した。

- v1予約末尾193 bytesの先頭64 bytesだけをversion 2の研究経済ownerへ割り当て、
  残り129 bytesをゼロ予約として維持する。
- 既存Factory、Raid、T08 Research encounter、T20、T21 Mirage、取得台帳、
  Reward pendingとはROM/RAM/save ownerを共有しない。
- 保存loadは現行QOL→Mirage連鎖を保持し、v1検証後にowner初期化・version更新・
  外側checksum再計算を行う。
- 釣り・生態・Game Cornerは現在のproduction wrapperへ連鎖し、購入コインと
  quit時返却をGame Corner研究報酬から除外する。
- 9 hostはStage 39のevent header、object上限、座標、occupied一覧を再確認して
  expected-byte付きで再配置する。

## 生成方針

Stage 40はStage 39から毎回再生成する。Stage 39差分BPSとclean ROM直接BPSを
別経路で適用し、ROMのbyte一致、declared span外変更0、allocation重複0、
libmGBA quick/full独立processを完了条件とする。ユーザー提供ROM、原本ZIP、
私有saveは成果物へ同梱せず、Gitへ追跡しない。
