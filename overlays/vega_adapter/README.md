# Vega adapter no-op module

T03のrebuild harnessで使う、未接続の最小Thumb moduleです。既存Vega領域へのhook/repointは0件で、entryは副作用なしの`bx lr`だけです。

親build driverから次の契約で呼び出します。

```bash
make -C overlays/vega_adapter \
  OUT_DIR=/absolute/path/to/artifact \
  ROM_ORIGIN=0x09200000
```

`ROM_ORIGIN`はallocatorのnamed section `vega_adapter_module`の開始値です。固定CFRU payloadの実末尾は`0x09185F88`ですが、allocatorの`integration_modules`領域に合わせて`0x09200000`以上、DPE領域`0x09600000`未満、4-byte alignmentを必須とします。旧候補`0x09F00000`はDPE blobと重なるため拒否します。

出力は`vega_adapter.bin`、`vega_adapter.elf`、`vega_adapter.map`、`metadata.json`です。metadataはmarker、Thumb entry、section span、hook 0件、source/tool/artifact SHA-256と、`RomAllocator.allocate_request`へそのまま渡せるfile-offset基準の`allocator_request`を持ちます。時刻やbuild directoryは含みません。`metadata.json`が最後に公開されるため、その存在は他3成果物の検証完了を意味します。
