#!/usr/bin/env python3
"""Issue19の隔離生成/読み取り専用check。ROMは生成しない。"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.pr16_learnset_baseline import prepare, check


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'check'))
    parser.add_argument('--zip', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare' and args.zip is None:
        parser.error('prepareにはhash固定された--zipが必要')
    try:
        result = (prepare(ROOT, args.zip, args.output) if args.command == 'prepare'
                  else check(ROOT, args.output))
    except (OSError, ValueError, KeyError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
