# Kanto map importer

`kanto_importer.py` は固定済みpokefireredの意味構造と、ユーザー所有のclean日本版BPRJ ROMに存在するraw layout byteを照合し、新規 `KANTO_*` IDへ変換する。

```bash
python3 scripts/build_kanto_import.py build
python3 scripts/build_kanto_import.py check
```

`check` は書き込みを行わず、manifest、inventory、V2 crosswalk、canonical round-tripが再生成結果とbyte一致することを検証する。ナナシマは明示的にscope外である。
