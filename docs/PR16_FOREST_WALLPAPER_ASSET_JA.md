# Forest壁紙：全asset・実table・LZ tokenの照合

**全assetの限定検証は完了。実entryからheap/BIOSへ至る条件付きreaderと正式型受入は未完です。**

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

## 次の未完作業

Forest新readerの成功run完了・原本hash・4profileの実call/stack/全4byte消費を読取専用で受領し、条件付き最小型1件だけを正式差分へ追加する。測定済みreader/ROM再構成/33試験と旧assetは再走しない。784/90・安全容量0は正式receiptまで維持。task/DMA/Freeと保存controllerは別gate。
