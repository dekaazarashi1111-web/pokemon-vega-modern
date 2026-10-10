# Forest壁紙：全asset・実table・LZ tokenの照合

**全asset・有限条件付きreader・対象4byteの正式型受領を完了。保存容量と保存controller統合は未完です。**

入力HEAD `30a1edc5dc3cbbf0852a9ec955a1d77d32dc3e88`、Actions `38066038086`、新34境界試験とtask graph PASS。先行bindingのActionsはcompleted/successを照合済み。

公開PNGは64×56で56tile相当ですが、固定ビルドルールは`-num_tiles 53`です。最後の空3tileを除いた1696byteから生成し、消費973byte、整列込み976byteを確定しました。Pillow全pixel照合と固定公開C compressorでも同一結果です。

現候補0641af70…を新scopeのためだけに再構成し、全32MiB SHAと115ownerを照合しました。0x08397188の全976byte、sWallpapers先頭の12byte tuple、保存hit0x08397492の4byteが一致しました。対象はLZ参照2byte・literal1byte・flags1byteで、整列paddingではありません。ROM/PNG/生byte列は公開せずhashとtoken型だけを記録します。

[機械可読checkpoint](../content/modernization/pr16_forest_wallpaper_asset_checkpoint.json)に全source/依存/親のidentity、symbol行、tokenごとの範囲と展開位置を保存しました。

## 全asset受入時の停止点（履歴）

Forest全asset976byte・実table先頭tuple・LZ消費973byte/展開1696byteは保存checkpointから継承し再測定しない。次はLoadWallpaperGfxの実literal/table選択→DecompressAndLoadBgGfxUsingHeap→LZ77境界を有限命令・caller状態・heap成功/失敗で結ぶ。成立するまで正式784/90・安全容量0を保持。全クリ/旧Bubble/Blastoiseの再走は禁止。

このtoken parserはBIOSやゲームentryの実行ではありません。sourceでcallがあることとtable一致だけからreader成立へ昇格しません。controller6528byte配置、同期heap寿命、保存writer/loaderと局所Save/fresh Continueは別gateです。所有者調整承認0、正式ROM/Save101・baseline不変、merge/releaseなし。

## 実readerの測定結果

入力HEAD `948e3773b4909eb7a5baaf77388686a61549e255`、Actions `38081577392`。新33境界試験とtask graph PASS。前回asset run38066038086の全job/必須step成功を受領。

固定公開headerをARM向けにコンパイルしたlayoutと、実JP symbol/候補全SHAを束縛。オフセット0/1×確保成功/NULLの4条件を実Thumb 130/131/130/131命令で追跡。LoadWallpaperGfxの実table全3fieldと5引数、MallocAndDecompressのheader→1696byte確保要求、実malloc stack/保存レジスタ帰還を照合。成功側はSWI11仕様モデルが973byteを消費して1696byteを展開し、継承済み独立hashと一致。対象08397492全4byteを消費。NULL側はheaderのみでasset展開/heap書込なし、実loader帰還を確認。

これは明示した正常同期ABIと非alias caller/heap状態に対する有限条件付き証明であり、実allocator/BIOS本体/描画/DMA/Freeのnative受入ではない。成功はCreateTask直前で止め、heap生存を記録する。

[新reader checkpoint](../content/modernization/pr16_forest_wallpaper_reader_checkpoint.json)。正式型受領は未完のため784分類/90未知/安全容量0を維持。旧asset/PNG/受入済みreaderの再走0、新scope候補再構成1、native0。

## reader測定時の停止点（履歴）

Forest新readerの成功run完了・原本hash・4profileの実call/stack/全4byte消費を読取専用で受領し、条件付き最小型1件だけを正式差分へ追加する。測定済みreader/ROM再構成/33試験と旧assetは再走しない。784/90・安全容量0は正式receiptまで維持。task/DMA/Freeと保存controllerは別gate。

## Forest条件付き最小型の正式受領

測定Actions `38081577392` / job `114299405185` の全9step成功、artifact `11680930584` の全ZIP/3member hash、公開commit `bc10f50ea7e3ce338f63d6ab5823644cd4fbe931` のcheckpoint完全byteを照合。オフセット0/1×確保成功/NULL、実call/table/stack帰還、973byte消費/1696byte展開と対象4byteを原本から受領しました。測定原本のpending表記は履歴として改作していません。

[正式receipt](../content/modernization/pr16_forest_wallpaper_receipt.json) / [singleton差分](../content/modernization/pr16_forest_wallpaper_receipt_evidence/reference-chain.json) / [未知89行](../content/modernization/pr16_forest_wallpaper_receipt_evidence/unknown-frontier.json)。正式784/90から785/89へ対象1件だけを追加し、他873行と全旧受入namespaceを保持。安全容量0、ROM/Save101/Wiki R0/baseline不変です。

新39受領試験と13統合境界検査、決定的差分、保存後read-only復元、task graphを検証。新native/ROM再構成/旧reader/旧試験再走は0。BIOS本体・allocator・task/DMA/Free・自然PC描画・全story・releaseの受入ではありません。

受領処理自身のActions完了は[外部読戻しreceipt](../content/modernization/pr16_forest_wallpaper_receipt_evidence/actions-completion.json)で別記録します。生成中のrunを成功と先取りしません。

## Forest受領時の停止点（履歴）

正式785分類/89未知・安全容量0の保存親から、保存controller6528byteに必要な候補窓のowner/間接参照を有限範囲で絞る。未知frontier先頭0x0805D12Fを採用する場合もsource/asset identityから開始し、未知削減だけを容量確保としない。Forest測定・受領39試験・旧asset/旧readerを再走しない。必要範囲の退役/移管、heap寿命、保存接続と局所受入は未完。

## 保存controllerの有限候補窓

入力HEAD `1aa6966db7f6ca647e5c665d6794179aba7a2822`。保存785/89親から全2148整列窓を比較し、[0x09FED0C4,0x09FEEA44)の6528byteを調査候補に固定しました。窓内の未知target点は最小10行です。これは安全容量や退役証明ではありません。

[窓計画](../content/modernization/pr16_donor_window_evidence/windows.json) / [検証checkpoint](../content/modernization/pr16_donor_window_checkpoint.json)。新49試験、150組の総当たり対照、実2148窓の独立総当たり、決定的read-only check、task graphを検証。窓外targetからの跨りread、旧inventoryで除外された旧owner内origin、計算参照は未証明として保持。正式785/89/安全容量0、旧受入/R0/ROM/Save101は不変です。

## 窓選定時の停止点（履歴）

候補窓[0x09FED0C4,0x09FEEA44)の6528byteについて、保存未知target 10行（先頭0x080A006F）のsource/asset identityと実consumerを限定して結ぶ。窓外targetからの跨りread・旧owner内originの除外・間接参照を残し、owner退役/部分移管を証明する。全874scan/Forest/Bubble/49窓試験の無変更再走は禁止。安全容量0を維持し、controller/heap/保存接続は別gate。

## 選定10originの固定公開symbol近傍

入力HEAD `3cdd1b0fef4d83eadc1a9b6197bfdbac24196e65`。保存済み10行と固定公開JP symbol全hashを照合しました。先頭0x080A006Fの直前labelは `HideMoneyBox` です。これは現ROMの関数/asset ownerや命令境界の証明ではありません。

[対応表](../content/modernization/pr16_donor_origins_evidence/symbol-frontier.json) / [checkpoint](../content/modernization/pr16_donor_origins_checkpoint.json)。新20試験、同入力決定性、読取専用byte/mtime、task graphを検証。正式785/89・安全容量0、旧窓計画/reader/R0/ROM/Save101不変。新native/ROM再構成/旧試験再走0。

## 以前の停止点（履歴）

選定窓10originの公開JP symbol近傍を保存済み。先頭0x080A006Fについてsymbol-frontierの出典/行を読み、固定公開関数sourceと現候補0641af70の有限命令範囲を束縛し、実consumer/命令境界を確認する。近傍labelだけでownerやFALSE_POSITIVEに昇格しない。窓外跨りread/旧owner内origin/間接参照は残す。正式785/89・安全容量0。全874scan/Forest/Bubble/窓49試験/symbol20試験の無変更再走禁止。

## 先頭originの現候補有限範囲

新候補復元1回で全SHA/115ownerと保存10originを照合。4個の有限範囲、前entryの条件付きCFG、first originと交差する命令形を記録しました。前entryの公開money呼出順一致=True、境界数=1。形を実consumer証明には昇格していません。初回run38090391926はGNU未定義命令コメントの表現差で未受入停止。adapterと5試験を追加し、失敗1回を含む本taskの復元は計2回です。

[有限事実](../content/modernization/pr16_first_origin_evidence/bounded-code-facts.json) / [checkpoint](../content/modernization/pr16_first_origin_checkpoint.json) / [symbol成功Actions受領](../content/modernization/pr16_donor_origins_evidence/actions-completion.json)。新40試験・読取専用byte/mtime・task graph・全旧原本保全。native0、旧受入再走0、正式785/89、安全容量0。

## 次の未完作業

保存したfirst-origin有限命令/owner事実から0x080A006Fの実型とconsumerを確定する。前後labelや逆アセンブル形だけの分類は禁止。実必要reader/配置元へ閉じる。正式785/89、安全容量0。既受入symbol20試験/今回40試験/有限ROM測定をsource不変なら再走しない。全874scanと旧Forest/Bubbleは再走せず、窓外跨りread/旧owner内origin/間接参照を残す。
