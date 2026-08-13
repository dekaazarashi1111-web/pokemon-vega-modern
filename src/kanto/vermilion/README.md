# クチバ早期縦切り runtime

T02で確認した `0x0824 && 0x114B` を一回性の `kanto_travel_unlocked` へ写し、T08のversioned save ledgerだけへ二地方状態を保存する。全国図鑑やVega殿堂入りは早期渡航の必須条件にしない。

到着処理は警告確認後、クチバterminalをKantoのheal/return/whiteout anchorとして先に永続化する。船上戦の拒否・勝利・敗北・辞退は渡航latchを変更しない。クチバジムは認定章2個を要求し、Vega badge/HM/story flagへ書かない。

Factory Trialと建物外遭遇NPCはT08のparty snapshotおよびpersist-before-battle transactionを直接利用する。専用map/UIは持たない。
