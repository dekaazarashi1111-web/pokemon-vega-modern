#!/usr/bin/env python3
"""Build/check/dry-run/emit the T12 symbolic content catalog."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from tools.content import ContentError,build_outputs,emit_content


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=("build","check","dry-run","emit"))
    parser.add_argument("--resolution",type=Path)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    try:
        outputs=build_outputs(ROOT)
        if args.mode=="build":
            for relative,raw in outputs.items():
                path=ROOT/relative; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(raw)
            print(f"T12 build: PASS ({len(outputs)} artifacts)")
        elif args.mode=="check":
            drift=[relative for relative,raw in outputs.items() if not (ROOT/relative).is_file() or (ROOT/relative).read_bytes()!=raw]
            if drift: raise ContentError("artifact drift: "+", ".join(drift))
            print("T12 check: PASS (side effects NONE)")
        elif args.mode=="dry-run":
            print(outputs["generated/content/dry_run.json"].decode(),end="")
        else:
            resolution=json.loads(args.resolution.read_text(encoding="utf-8")) if args.resolution else None
            raw=emit_content(ROOT,resolution)
            if not args.output: raise ContentError("emit requires --output")
            args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_bytes(raw)
            print(f"T12 emit: PASS ({args.output})")
    except (ContentError,OSError,ValueError,KeyError,json.JSONDecodeError) as exc:
        print(f"T12 {args.mode}: FAIL: {exc}",file=sys.stderr); return 1
    return 0


if __name__=="__main__": raise SystemExit(main())
