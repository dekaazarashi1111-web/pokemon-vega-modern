"""Narrow checks for two reproduced PR16 evidence defects, not release gates.

V4 legacy rows use the canonical manifest classification.  The old key-prefix
count is retained only to explain the 472 -> 499 discrepancy, not to adopt or
remove any distribution. PPM checks reject the reproduced dummy-renderer output;
they do not replace visual review or prove native acquisition/save coverage.
"""
from __future__ import annotations
from collections import Counter
import hashlib
from pathlib import Path

OLD_COUNTS = {'level_up': 297, 'egg': 175}
ALIASES = {
    'MOVE_KEY_SOUL_BITE': (470, {'level_up': 11, 'egg': 10}),
    'MOVE_KEY_DARK_SNIPE': (509, {'level_up': 2, 'egg': 4}),
}
# Exact V4 CSV source positions and stable species identities, not proposed rows.
ALIAS_POSITIONS = {
    'level_up_final.csv': {
        1131: ('GENGAR', 470), 4029: ('HONCHKROW', 470),
        4439: ('SNEASEL', 509), 4748: ('SABLEYE', 509),
        4920: ('EKANS', 470), 4943: ('ARBOK', 470),
        5048: ('DUSKULL', 470), 5071: ('DUSCLOPS', 470),
        5093: ('DUSKNOIR', 470), 5172: ('ARIADOS', 470),
        5473: ('SHUPPET', 470), 5493: ('BANETTE', 470),
        7403: ('EELEKTROSS', 470),
    },
    'egg_moves_final.csv': {
        152: ('HOUNDOUR', 470), 572: ('ABSOL', 509),
        666: ('GASTLY', 470), 1450: ('AERODACTYL', 470),
        1475: ('LARVITAR', 470), 2452: ('WHISMUR', 470),
        2790: ('MAWILE', 470), 2912: ('KOFFING', 509),
        2947: ('DUSKULL', 509), 3432: ('SKORUPI', 470),
        3466: ('CARNIVINE', 470), 3610: ('DUNSPARCE', 470),
        3646: ('FARFETCHD', 509), 4339: ('SANDILE', 470),
    },
}
SUMMARY_CASES = ('summary-220-0', 'summary-220-1', 'summary-373-0')


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def reconcile_legacy_count(records: list[dict]) -> dict:
    """Explain every row outside the old prefix tally; never suppress a row."""
    old = []
    aliases = []
    seen = set()
    for row in records:
        route = row['route']
        need(route in OLD_COUNTS and row['source_class'] == 'CURRENT_PRESERVED',
             'legacy reconciliation is not authority for a new route')
        member = 'level_up_final.csv' if route == 'level_up' else 'egg_moves_final.csv'
        need(row['source_member'] == member, 'legacy route/source mismatch')
        key = (member, row['source_csv_line'])
        need(key not in seen, 'duplicate legacy CSV row')
        seen.add(key)
        if row['move_key'].startswith('MOVE_KEY_VEGA_'):
            old.append(row)
            continue
        spec = ALIASES.get(row['move_key'])
        need(spec is not None and row['move_id'] == spec[0], 'unreviewed non-prefix Vega alias')
        source = ALIAS_POSITIONS[member].get(row['source_csv_line'])
        need(source == (row['species_key'].removeprefix('SPECIES_KEY_'), row['move_id']),
             'alias source species/move/line differs')
        aliases.append(row)
    need(dict(Counter(r['route'] for r in old)) == OLD_COUNTS,
         'the historical 472-row projection changed')
    for key, (_, expected) in ALIASES.items():
        need(dict(Counter(r['route'] for r in aliases if r['move_key'] == key)) == expected,
             'alias route counts differ: ' + key)
    counts = dict(Counter(r['route'] for r in records))
    need(counts == {'level_up': 310, 'egg': 189}, 'canonical legacy row counts differ')
    return {
        'status': 'EXACT_SOURCE_ALIAS_RECONCILIATION',
        'canonical_classification': 'VEGA_EXCLUSIVE_V3',
        'historical_prefix_projection': {'rows': len(old), 'route_counts': OLD_COUNTS},
        'previously_unaccounted_named_aliases': {
            'rows': len(aliases),
            'route_counts': dict(Counter(r['route'] for r in aliases)),
            'source_rows': aliases,
        },
        'canonical_legacy_preservation': {'rows': len(records), 'route_counts': counts},
        'new_adoptions': 0,
        'old_472_rows_removed': 0,
        'rom_or_native_acceptance_implied': False,
    }


def inspect_ppm(raw: bytes) -> dict:
    header = b'P6\n240 160\n255\n'
    need(type(raw) is bytes and raw.startswith(header), 'native screenshot header differs')
    pixels = raw[len(header):]
    need(len(pixels) == 240 * 160 * 3, 'native screenshot is truncated or oversized')
    colors = len(set(zip(pixels[0::3], pixels[1::3], pixels[2::3])))
    need(colors > 1, 'single-color screenshot: renderer output was not observed')
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'distinct_colors': colors}


def validate_summary_screenshots(directory: Path) -> dict:
    observations = {}
    skills = set()
    for case in SUMMARY_CASES:
        for suffix in ('summary-entry', 'skills'):
            name = case + '-' + suffix + '.ppm'
            path = directory / name
            need(path.is_file() and not path.is_symlink(), 'missing/unsafe native screenshot: ' + name)
            observations[name] = inspect_ppm(path.read_bytes())
        a = observations[case + '-summary-entry.ppm']['sha256']
        b = observations[case + '-skills.ppm']['sha256']
        need(a != b, 'native Summary page transition was not rendered')
        skills.add(b)
    need(len(skills) == len(SUMMARY_CASES), 'different adopted Summary screens reuse one image')
    return observations
