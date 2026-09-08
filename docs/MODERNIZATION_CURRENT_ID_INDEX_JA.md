# P01 現行ID・対象集合の生成入口

固定 `docs/wiki/stage61/` と `scripts/build_stage61_wiki.py` は過去Stage61の再現用として保持する。現行ID・原作習得対象の判断には、次の専用consumerを使う。進化条件の採用はP02、技表の全反映はP03であり、本工程はどちらも開始しない。

```bash
python3 scripts/build_modernization_catalog.py build
python3 scripts/build_modernization_targets.py build
python3 scripts/build_modernization_catalog.py check
python3 scripts/build_modernization_targets.py check
```

出力は `generated/modernization/current_targets.json`、`current_targets.csv`、`current_species_index.md`。原本ZIP・固定Wiki・ROM・saveへは書き込まない。consumerは既存catalogの現在sourceとのbyte一致を必須にし、stale出力を拒否する。

`content/modernization/identity_contract.json` のdigest定義はUTF-8 JSON、ensure_ascii=False、sort_keys=True、separators=(',', ':')、末尾改行なし。Speciesはkey順の `[key,id,national_no,form_key]`、Moveはkey順の `[key,id]`、集合はkeyの昇順配列である。原本の対象区分集合は訂正前を記録している。キャタピー／タマゴの2keyだけを明示訂正し、他の集合と除外7フォームを不変のdigestへ照合する。

キャタピー649を通常基本種・原作習得対象、内部タマゴ412を除外とし、訂正後1300keyの完全一致を検証する。これは1300種への技表適用を意味しない。Move806対は現行key/IDに照合し、未実装のALLY SWITCH候補1063は実装済み集合へ入れない。Form388対はmanifestの全フォーム集合と照合する。

復元資料のAbility参照は数値と名前の照合結果を記録するが、未承認の特性変更を採用しない。現行ROM内の値・capacity・実機動作の証拠は別gateで必要であり、このsource-only検証で代用しない。
