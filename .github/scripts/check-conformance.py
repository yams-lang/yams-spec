#!/usr/bin/env python3
"""Check the conformance suite is internally consistent.

Deliberately dependency-free and language-neutral: this repository's suite must
be checkable without a Swift toolchain, because implementations may be written
in any language. `yams-swift` runs equivalent guards in its own test target;
this is the copy that gates every pull request.

Checks:
  1. Every case in manifest.json exists on disk.
  2. Every .yams file on disk is listed in manifest.json.
  3. Rejection cases declare both `rule` and `stage`.
  4. `expect` and `stage` use known values.
  5. Every case file is non-empty and, for valid/ cases, declares a schema.

Exits non-zero with one line per problem.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2] / "conformance"
VALID_EXPECT = {"accept", "reject"}
VALID_STAGE = {"safe-yams", "structural"}


def main() -> int:
    problems: list[str] = []

    manifest_path = ROOT / "manifest.json"
    if not manifest_path.exists():
        print(f"missing {manifest_path}", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text())
    cases = manifest.get("cases", [])
    if not cases:
        problems.append("manifest.json lists no cases")

    listed = set()
    for case in cases:
        rel = case.get("file")
        if not rel:
            problems.append(f"case with no 'file' key: {case}")
            continue
        listed.add(rel)

        path = ROOT / rel
        if not path.exists():
            problems.append(f"{rel}: listed in manifest, not on disk")
            continue
        if not path.read_text().strip():
            problems.append(f"{rel}: file is empty")

        expect = case.get("expect")
        if expect not in VALID_EXPECT:
            problems.append(f"{rel}: expect={expect!r}, want one of {sorted(VALID_EXPECT)}")

        if expect == "reject":
            if not case.get("rule"):
                problems.append(f"{rel}: a rejection must name the rule it violates")
            stage = case.get("stage")
            if stage not in VALID_STAGE:
                problems.append(f"{rel}: stage={stage!r}, want one of {sorted(VALID_STAGE)}")

        if expect == "accept" and "schema:" not in path.read_text():
            problems.append(f"{rel}: an accepted document should declare schema:")

    for directory in ("valid", "invalid"):
        d = ROOT / directory
        if not d.is_dir():
            problems.append(f"missing directory: {directory}/")
            continue
        for path in sorted(d.glob("*.yams")):
            rel = f"{directory}/{path.name}"
            if rel not in listed:
                problems.append(f"{rel}: on disk, missing from manifest.json")

    if problems:
        print(f"conformance suite: {len(problems)} problem(s)", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1

    print(f"conformance suite OK — {len(cases)} cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
