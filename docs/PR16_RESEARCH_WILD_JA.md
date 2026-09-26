# PR16 研究wild実稼得

研究wild専用Cを実装し、釣り/生態の通常Bag→逃走→捕獲→取引保存Continueを新規実測。失敗原本から未完境界だけ修正する。旧受入済み写真/虫取り/採掘/BP/P08/special-wildケースは再実行しない。ゲームコーナー/通常進行の受付ショップ接続/未確認文言は未完。

状態: `content/modernization/pr16_research_wild_checkpoint.json`
原本: `content/modernization/pr16_research_wild_evidence/36273917599/measurement.json`

開始map/lead/道具/進行はfixture。RNG・敵・結果・RPは注入しない。barrier後は通常入力のみ。取引2saveだけのfresh Continueを対象とし、手動Saveで保存欠陥を隠さない。

この記録時点では自己Actions未終端・独立oracle未完であり、新しいnative受入は0。`counts`と`failures`を正本とする。成功したscopeも受入確定前に無意味に再実行しない。
