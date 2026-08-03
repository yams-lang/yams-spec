# YAMS conformance suite

Test documents that define, by example, what a YAMS implementation must accept
and reject. Any implementation in any language runs these — the suite is the
executable half of the specification.

Without it, "is this valid YAMS?" resolves to "whatever the reference
implementation happens to accept." That is a description of a program, not a
specification.

## Layout

```
conformance/
  manifest.json     machine-readable case list — the thing to iterate over
  valid/            documents every implementation must accept
  invalid/          documents every implementation must reject
```

## `manifest.json`

Each case carries:

| Field | Meaning |
|---|---|
| `file` | path relative to `manifest.json` |
| `expect` | `accept` or `reject` |
| `rule` | for rejections, the rule violated — implementations should report *this* rule |
| `stage` | `safe-yams` (subset violation, caught before parsing) or `structural` (well-formed YAML, invalid YAMS) |
| `exercises` | what the case is for, in prose |
| `spec` | the section of the specification it derives from |

Reporting the right `rule` matters as much as the accept/reject outcome. An
implementation that rejects `invalid/tabs.yams` because its YAML library choked
has not demonstrated it implements Safe YAMS.

The two stages are deliberately distinct: `safe-yams` cases are rejected on the
*text*, before a parser runs, while `structural` cases parse cleanly as YAML and
fail only against the format's own rules.

## Running it

There is no runner here on purpose — a harness in one language would privilege
that language. Each implementation iterates `manifest.json` in whatever its
native test framework is.

The Swift reference implementation is
[`yams-swift`](https://github.com/yams-lang/yams-swift); see its test target for
one worked example.

## Adding a case

1. Add the document to `valid/` or `invalid/`.
2. Add an entry to `manifest.json`. A rejection needs `rule` and `stage`.
3. Make sure the case fails for exactly one reason — a document that violates
   two rules at once cannot tell you which one an implementation caught.
4. If it exercises behavior the specification does not state, fix the
   specification first. The suite illustrates the spec; it does not extend it.

## Scope

These cases cover the **format**: document structure, the Safe YAMS subset, and
structural validity. They do not cover node semantics, which belong to a
catalog and are a host's concern — a conforming implementation knows nothing
about what any node type means.
