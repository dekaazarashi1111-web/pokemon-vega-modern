# 694親保持と残script・表・音声の有限根

## 目的と境界

現候補 `0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583` の旧egg見かけ参照874件に対し、694分類・180未知の親を保持したまま、残る参照の実根・型・consumerを追加検証する。正式ROM、Save101、115 actual owner、52 save subowner、残804byteは変更しない。旧全ROM参照scan、既受入native、heap測定は再実行しない。

この文書は実装の契約であり、実測の成功宣言ではない。正本の件数とsource/runは `content/modernization/pr16_dex_hof_script_references_checkpoint.json` とその閉じた証拠を用いる。

## 親の完全性

- 元619分類の4.1MB監査、25追加delta、17追加chain、33追加chainを上書き・再公開しない。
- `pr16_dex_hof_script_chain.parent` が元・全親を全file size/SHAで検査する。直近71138byteは直近checkpointの独立 `delta_identity` を `remaining_chain.read_measured` へ渡す。
- 計算時のみ874行をmaterializeする。旧acceptedと今回残unknownは全field不変。旧25/17/33 changes、22/16/33 witnessesを全保持する。
- 新証拠は別namespaceの `script_reference_chain`。型が衝突する窓、未包含hit、参照先を省いたwitness、未使用witness、自己署名だけのenvelopeを拒否する。

## 追加根

1. battle scriptはmove-animationの文法を使わない。実主dispatch・FF副dispatch・move-effect tableの有限根と実handlerのfield/後継を検査する。隣接命令のpointer上位半分と拡張opcodeを跨ぐ4byteのみを型付けし、完全pointer operandを非pointerへ分類しない。複雑なattackcanceler/accuracycheck/callasmの未証明経路は未知のまま残す。
2. 旧DPE level-upは固定公開Cの17 initializerと1440-entry歴史pointer根を直接照合する。packed u16 move/u8 level、終端、双方の実root、隣接境界を全byteで検査する。現1671species根とは別の歴史型であり、現runtime到達・不存在・退役を主張しない。
3. 命令窓は実reset、special dispatch、main callback、task登録・同じtask.func遷移からのみ到達を結ぶ。register保存、引数、table stride、条件分岐とinterworkまで連続した意味検査を行う。symbol名だけ、関数範囲だけ、owner名だけでは分類しない。
4. object/field-effect画像は実table・map/object selector・公開animation serializer・frame pointer/sizeを束縛し、有限raw4bpp frameだけを分類する。描画の実観測を主張しない。
5. 曲306は固定physical map96/5から3 connectionと通常warpを経た97/88のmusic fieldを、実JP consumerへ結ぶ。JP全map/曲tableのextentを推測しない。133曲を一つのモデルで処理し、既132曲と49sample identity、新旧command/structure/payload、全追加非音声root窓の競合を拒否する。曲85/43/44は未証明なら未知維持。

## 現候補と反証

旧formal候補の診断は現0641の受入の代用にしない。Actionsは現候補を一度再構成して全SHA、全115 actual owner、元874hitの全byte、追加有限窓を再束縛する。新scopeの反証を同じcandidateで行う。親測定の原本を書換えず、無影響nativeは0のまま保持する。

改変ROMと改変reviewを同時に再hashした対照も拒否する。callback引数やtaskId、loadからcall/storeまでのregister保持、script任意書込みのdestination/幅、consumerが実際に全命令長を消費することを確認する。

## 公開と記録

同一branch・同一source・初回run・正確なpendingの範囲だけで既存tokenを使う。新credential、永続アクセス拡張、merge、release、force pushはしない。

producer、guard、upload、consumerのdirectory/nameを機械照合する。公開対象はsource、最小address-size-SHA、text、全snapshot receiptのみ。成功の固定集合だけを専用directoryへ渡し、空・部分成功・hidden・symlink・未知file/拡張子・binary・LF欠損・全量上限超過を拒否する。ROM断片、rawhex、ROM、入力save、runtime、runner、credentialは追加公開しない。失敗の詳細はprivate出力だけに残す。

固定引継ぎMD/JSON、checkpoint、両append-onlyログを記録し、全blob全文と改行を読戻してから非force更新する。成功後は専用closeoutで終端・全artifact・全snapshotを確認し、測定triggerをmanual-onlyへ退役する。

## 次の境界

T09上位wordは旧20stride/species278/word4仮説と現16strideの物理row348を混同しない。現PLC2 wrapperのconsumerを旧T09の根へ転用しない。当時の実root/functionと全候補identityを閉じない限り未知を維持する。

全unknown0だけでもdonorは不可。間接参照・旧egg退役完全性を証明し、必要容量の明示移管後に実Ccontroller配置、全S61E/MDX writer-loader-Link exact-source/no-main/INITIAL、全mode/早期31/species9bit、同期heap lifetimeへ進む。heap13352byteを保存退避53300byteの入口を跨いで保持しない。正式切替後にtrainer131後半からシオウ通常回復・保存・独立coldContinue。雑魚毎checkpointは行わない。
