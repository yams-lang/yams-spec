# Contributing to YAMS

This repository holds the YAMS format specification and its conformance suite.
Contributions are welcome — the notes below exist to make review quick rather
than to gatekeep.

## Sign your commits (DCO)

Every commit must carry a `Signed-off-by` line certifying you have the right to
submit the work under this repository's licenses. That's the
[Developer Certificate of Origin](https://developercertificate.org) — a
one-line assertion, not a copyright assignment, and no paperwork.

```bash
git commit -s -m "your message"
```

`-s` appends the line using your configured `user.name` and `user.email`. If you
forget on the last commit, `git commit --amend -s` fixes it.

## Licensing

| What you're changing | License it falls under |
|---|---|
| The specification, this file, any prose | CC BY 4.0 |
| Example snippets inside the specification | CC0 1.0 — they are meant to be copied into implementations |

By contributing you agree your work is offered under whichever applies.

## What kind of change is this?

**A wording fix or clarification** that changes no behavior — open a PR against
the current version directory. Say plainly that behavior is unchanged.

**A behavior change** — open an issue first. A specification with implementations
in the wild cannot take changes casually, and it is much cheaper to talk before
you write. Expect to be asked what breaks and what an existing implementation
should do with an older document.

**A conformance case** — see [`conformance/README.md`](../conformance/README.md).
Add the document and its `manifest.json` entry together, make sure it fails for
exactly one reason, and if it exercises behavior the specification does not
state, fix the specification first. The suite illustrates the spec; it never
extends it.

**An implementation change** — this repository holds no implementation. The
Swift reference implementation lives in
[yams-swift](https://github.com/yams-lang/yams-swift); other languages have
their own repositories. Changes go there. If an implementation disagrees with
the specification, that is a bug in one of them — say which you think it is.

## Things worth knowing

- **Released version directories are frozen.** `spec/1.0/` is not edited once
  tagged, except for errata. See [`spec/README.md`](../spec/README.md).
- **The examples use a fictional catalog**, `example/1`, defined in the
  specification's Appendix A. Please keep new examples inside that vocabulary —
  the point is that the format demonstrates itself without borrowing any real
  domain's node names.
- **The specification does not define node semantics.** If a proposal needs to
  say what a node *does*, it belongs in a catalog, not here.

## Reporting a problem

An issue that says which version you read, what you expected, and what you got
is enough. For an ambiguity, quoting the sentence and the two readings you can
see is the most useful thing you can do — that's usually the whole bug.
