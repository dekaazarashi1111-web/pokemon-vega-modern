# Issue19 明示bindingと配置前payload

正本: `content/modernization/pr16_learnset_payload_checkpoint.json`。最新実行原本とartifactを参照し、原本生成・既受入nativeをやり直さない。

## 完了範囲
191枠は188のidentity/戦闘時持越し保全、Caterpie649の4経路、Own Tempo1670の60経路、Floette Eternal1029の採用待ち1枠へ分類。元128288経路は不変で、明示64経路を別層に保持。54新試験・独立2プロセス・ローカル/Actions全hash一致、旧Wikiから別計算した全byte監査を完了。

後継表の `candidate_slots_zero_based` は旧Wiki `slot=slot+1` 由来の1始まり番号だった。33321経路をbinary bit用の0始まりへ明示補正した。凍結済み後継表を直接変更せず、旧欄をruntimeへ直結することは禁止する。上限はmachine128/tutor64。

## 成果物と境界
level/egg/進化時/reminder/shared egg/互換bit/不足技archiveの配置前binaryとconsumer index、全経路SHA台帳をartifactに保存。shared egg・進化前持越し・フォーム条件・特殊孵化を通常level/eggへ統合しない。188枠は空表ではなくIDENTITY_ONLY_NO_REPLACEMENT、1029はBLOCKED_SOURCE_ADOPTION。保存済み4技は変更しない。選択済みUltra Necrozmaの既存P02解除先2通りも変更しない。

## 次の未完
1029はStage69で入手可能だがP01の習得元はapply=false。旧候補の技表や通常Floetteへのfallbackを避け、固定reference legendsza:0670.05の明示採用裁定を行う。その後、非学習/戦闘姿owner、条件付きconsumer、配置とpointer/容量、実供給を接続し、後継ROM・別Wiki・影響nativeを検証する。今回のartifactはインストール不可の配置前成果物であり、ROM受入/Issue19全体完了/merge/releaseではない。
