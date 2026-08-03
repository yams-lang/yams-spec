# YAMS — Yet Another Modular Syntax

A YAML-based interchange format for **modular dataflow graphs**: named nodes
connected by wires, each wire carrying a time-varying value. The format is
domain-general — audio synthesis, control modulation, effect chains, lighting
rigs, video mixers, signal-processing pipelines — anywhere named modules
exchange values over explicit connections.

YAMS defines *structure*. It does not define node types, their semantics, or
execution. Those come from a **catalog**: a host supplies one, and the patch
names it. That separation is the whole design.

## Manifest

| Path | What |
|---|---|
| [`spec/1.0/yams-spec.md`](spec/1.0/yams-spec.md) | The format specification — the normative document |
| [`spec/`](spec/) | One directory per version; released versions are frozen |
| [`conformance/`](conformance/) | Test documents every implementation must accept or reject, with a machine-readable manifest |

## Implementations

[**yams-swift**](https://github.com/yams-lang/yams-swift) — the Swift reference
implementation. It is a *reference*, not a privileged one: the specification is
the authority, and an implementation in any language that passes the
conformance suite is equally valid.

If you write one, the suite is how you know it is right. Open an issue and it
can be listed here.

## Catalogs

A catalog defines the node types a patch may use, their ports and parameters,
and any host-facing presentation metadata. A patch declares which one it needs:

```yaml
schema: yams/1
catalog: some.catalog/1
```

The reference implementation validates *structure* — that a file is
well-formed YAMS. It does not know what any node type means; catalog-aware
checking belongs to the host.

New implementations should run [`conformance/`](conformance/) rather than
trusting agreement with `yams-swift`: the suite is what makes the
specification testable in any language, and it is the authority on what "valid
YAMS" means.

## Licensing

The specification and all other prose here are [CC BY 4.0](LICENSE).
Copyright © 2026 Klaxson Sound LLC.

Attribution: *"YAMS — Yet Another Modular Syntax", Klaxson Sound LLC, licensed
under CC BY 4.0.*

Code samples embedded in the specification are intended to be copied into
implementations. To avoid the attribution requirement riding on a few lines of
YAML, **the example snippets in the specification are dedicated to the public
domain (CC0 1.0)**; the surrounding prose remains CC BY 4.0.

YAMS is not claimed as a trademark: implement it, and name your implementation
after it. See [`TRADEMARKS.md`](TRADEMARKS.md).

## Versions

`schema: yams/1` in a patch file names the *format* major version — the only
thing a reader needs to decide whether it can load the file at all. The
specification document has its own finer-grained version (`spec/1.0/`), and
`yams-swift` has its own semver again. See [`spec/README.md`](spec/README.md)
for how the three relate.

## Contributing

See [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md). Contributions are
accepted under the licenses above, certified by a
[Developer Certificate of Origin](https://developercertificate.org)
sign-off (`git commit -s`).
