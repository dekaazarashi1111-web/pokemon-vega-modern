# Trainer V5 Stage 31 runtime

安定した公開入口`BuildTrainerPartySetup`の返却直後に、選定trainerだけへV5 sidecarを適用します。最適化でABIが変化するprivate `CreateNPCTrainerParty`はhookしません。既存0x20 trainer recordと16-byte party memberはspecies/item/moves/levelを保持し、sidecarはexact IV、ability slot、nature mint、6EVをlive `Pokemon`へ設定して再計算します。

高IDの戦闘recordは保存flagのindexとして使わず、trainer専用のscript command / `HasTrainerBeenFought` / `SetTrainerFlag` / `ClearTrainerFlag`だけで物理trainerの既存flagへ変換します。グローバル`FlagSet/Clear/Get`は変更しません。再戦は`GetRematchTrainerId`で物理source IDからV5 instance IDへ解決します。

初回DOUBLEのrooted scriptは物理trainer ID 702を保持します。`BattleSetup_ConfigureTrainerBattle`がその正確なkind-4引数を消費した直後だけV5 instance ID 1342へ再束縛するため、NPC視界判定と敗北flagは既存save ABIのままです。
