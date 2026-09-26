# PR16 購入後Continueの再受付停止・診断記録

Task: `USER-20260926-RESEARCH-PURCHASE`

## 原本を上書きしない

初回Actions run `36248750283` / source `b15e08f07e58fe0e924efc1136ea5f3beea99cec` は失敗のまま保持する。原本は `content/modernization/pr16_research_purchase_evidence/36248750283/`。購入確認の拒否、購入成功、取引直後の独立Continueまで観測され、再開後にショップを開けず停止した。これを途中成功だけで最終受入にはしない。

候補は一貫して SHA256 `5d1fc9c47225ae8c0a369514b899a062af3699fa3c9a2f617e94ffd5f7dcc1ab`。ROM変更・ARM compile/linkなし。

## 切り分けと原因

停止fixtureを一度ローカルで再現し、購入処理自体が作成したprivate saveを退避した。その後の対照は退避した購入後saveから開始し、購入prefixを再実行していない。位置、向き、player object、実map events、キー入力をread-onlyで観測した。観測中の7API write barrierは解除していない。

再開直後の実測:

```
counter=4 map=98/3 saved_xy=2,2
object_id=0 active=1 live_xy=9,9 facing=2
running=0 transition=0 quest=0 playback=0
live_events=155270224
```

live座標はstockの7タイルborderを含む。RAM ownerは既存 `tools/mgba_world_runtime_input_e2e.c`、`tools/mgba_stage58_convenience_smoke.c` と照合した。保存位置と実event rootは一致しており、player生成待ちや入力pulseの長さだけでは解決しない。

通常入力の対照:

```
# 保存再開時は既に上向き。無条件UPは「向き合わせ」ではなく歩行になる。
UP 2 frames -> saved_xy=2,1 live_xy=9,8 facing=2

# 同じ購入後saveから、不要なUPなしで通常Aを押した別対照。
A 2 frames -> field_lock=1
A 2 frames + settle -> result=9 shop_active=1
次のA -> result=10 shop_active=0
counter=4 / 座標2,2を維持
```

したがって新driverは上向きでない場合だけUPを送り、各受付前後にSaveBlockと実player objectの両方が(2,2)/(9,9)であることをassertする。Aは2frame pulseに揃える。既受入の取消driverは変更しない。既存Ring/shopの「必要な時だけ向きを変える」方式と一致させる。実ROMのショップ・保存delegateの不具合とは判定していない。

## ローカル診断の計数と限定

記録が得られた診断processは6件（初回の停止再現1、購入後cacheからのhand-off対照1、pulse対照1、画面/入力読取1、通常Save前後の読取1、不要な方向入力を省く対照1）。host compileは5回、最後の2対照は同一console executableを使った。これらは受入テストではなく原因切分けである。42oracle・旧取消・旧host49・phase0/V1/retry試験はローカル診断中に再実行していない。

別途、streaming実行要求はtoolで拒否されたため実行証拠として扱わない。非root Pythonからの一試行はsave attachmentで失敗し、ゲーム進行の証拠には含めない。headless画面出力は黒一色だったため日本語画面の目視受入を主張しない。private ROM/save/画像はtrackedへ追加しない。

この原因切分けを再実行する必要はない。最終受入は修正source `8bfa34e0b40db10f488e5d7dbe4da8f6c8b528e0` のdriverを用いたActionsのclosed oracle、全Bag/party/ledger、Save counter、独立Continueの結果を参照する。成功42oracleは依存hashを照合した原本再利用であり、再実行ではない。
