# PR16 図鑑codecの実配置とABI境界

この工程は正式ROM/Save101を変更しない。Stage39で退役したT09 level-up pointer ownerへ、codec/compact mapping/save bridgeと固定24個のABI入口を私有候補として配置する。ゲームの保存schedulerとconsumerへのhookは次工程であり、この配置だけでは図鑑不具合を修復しない。

## 所有境界

- `pr16_learnset_natural_checkpoint.json#wild_repair.allocation` の最終107-owner reportを既存 `tools/rom_allocator.py` で厳密再構成する。
- `species_surface_level_up_pointers` の全6484bytesだけを、`pr16_dex_capacity_lease.json` の退役証拠と全ROM SHAに束縛して移管する。他106owner、region、使用量、空き量、sequenceは不変。
- payloadが使わなかったsuffixも新ownerの予約領域として保持し、元byteを維持する。未使用に見えるFFや隣ownerを借りない。
- 全ROM差分をlease内に限定し、元owner byteを戻した全ROMが入力と一致することを確認する。旧level-up DATAとsentinelのbyteは不変。

## 実アドレスと固定export ABI

codec全APIを0x09FC0998で新しくARMv4T linkする。先頭384bytesは24個×16bytesの固定entry。Thumb tail veneerはr3を一時stackへ退避し、targetをr12へ移し、r3とSPを戻してからBXする。r0〜r3、第5引数以降、LRを壊さない。旧footprintのVMA=0x08000000を実配置の証拠として使わない。

link後の全24entry、命令構造、Thumb target literal、implementation範囲、mutable/undefined symbol不在を確認する。関数アドレスの手入力やROM byteの公開はしない。新しい入口を使う後段sourceは公開metadataのentry名・アドレスに固定し、保存scheduler全体をcloneしない。

## 限定native試験

固定版mGBAの新規1process/1coreで、私有候補内の24entryを実CPU命令として直接呼ぶ。game boot/戦闘/保存なし。各veneerの4register引数・最大6stack引数・SP/LRを観測し、各APIのreturnとEWRAM全262144bytesを同sourceのhost referenceと照合する。callee-saved registerも確認する。

これはisolated ABI試験であり、通常game callsite到達、Save/Continue、CRC fallback、全save mode、consumer統一、ストーリー受入ではない。5UI RAM寿命など既受入nativeを再実行しない。

## 次の接続

Stage61 code ownerは0x09448960..0x0944BA78の12568bytesで、次ownerまでpad8bytesのみ。全44required exportと後段hotfixを保持してexisting-owner内置換を設計する。validate_slot、inject_tail、expected_prepared_byte、tail_matches、load、clone、record-onlyを同世代MDXに接続し、sector31 shadowよりmain-bank MDXを優先して復旧Save前にloadする。その後SIDを失う前の全consumer、Bag count、reward clear、Factory/Codex rollbackを接続する。

基準候補切替、trainer131勝利、シオウPokecenter通常回復はこれらの候補限定受入後に進める。雑魚戦ごとのcheckpointは作らない。
