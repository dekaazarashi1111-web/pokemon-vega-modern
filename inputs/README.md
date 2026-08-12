# Input placement

Place private files under `inputs/private/`:

```text
FireRed_JPN_Rev0_clean.gba
Vega_2018-02-23.ips
factory_test_20260524.ups
```

Actual filenames may differ. `bootstrap_project.py` can detect the clean ROM by hash and patches by signature/name.

Place the prior audit ZIP under `inputs/reference/` if available:

```text
vega_cfru_integration_audit.zip
```

Never commit these inputs.
