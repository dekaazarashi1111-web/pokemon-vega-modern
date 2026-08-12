# Manifests

These CSV files are the only source of truth for stable IDs and Kanto content. Generated code must reference them; generated outputs must not be hand-edited.

Run:

```bash
python3 scripts/validate_manifests.py
```

Empty files with headers are valid during bootstrap. Tasks populate them incrementally.
