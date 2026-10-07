# YAMS — Yet Another Modular Syntax

A YAML-based interchange format for modular dataflow graphs — nodes connected by wires, each wire carrying a time-varying value. Domain-general: audio synths, control modulation, effect chains, lighting rigs, video mixers, signal-processing pipelines — any system where named modules exchange values over explicit connections.

This document is self-contained: it depends on no host application and no domain. Hosts (DAWs, editors, runtimes, installations) reference this spec and ship a **catalog** that defines their domain-specific node types and any presentation metadata.

**A note on the examples.** Every example below is written against `example/1`, a small fictional catalog that exists only in this document — see [Appendix A](#appendix-a--the-example1-catalog). Its types (`emit`, `scale`, `clamp`, `merge`, `split`, `collect`) are deliberately abstract dataflow verbs, so that no example can be mistaken for a real catalog's vocabulary or copied into a working patch. Where a rule concerns structure rather than semantics, the type names carry no weight at all.

## Goals

- **Human-readable, human-writable.** Patches are documentation. Diffs are reviewable. No GUI required.
- **Agent-authorable.** LLMs produce valid YAMS as readily as they produce YAML. No DSL grammar to learn.
- **Tool-portable.** A visual editor, a runtime, a documentation viewer, and a CLI all read the same file.
- **Domain-general core, domain-specific catalogs.** The format defines structure; catalogs define semantics and any UI-facing metadata.

## Non-Goals

- YAMS does not specify execution — update rate, timing, scheduling, concurrency, lifecycle. Those belong to runtimes.
- YAMS does not enumerate node types or their semantics. Those belong to catalogs.
- YAMS does not define user-facing presentation — knobs, cues, pads, macros, bindings to external input. Those belong to catalog extensions or hosts.
- YAMS does not standardize visual layout (positions, colors, notes-on-nodes). Those belong to optional editor sidecars.

## File Format

- **Encoding:** UTF-8.
- **Syntax:** YAML 1.2, restricted to the **Safe YAMS** subset (see below).
- **Extension:** `.yams`.
- **MIME type:** `application/yaml` (no registered YAMS-specific type).

## Top-Level Structure

```yaml
schema: yams/1
catalog: <catalog-id>
name: <optional human name>

nodes:
  <node-id>:
    type: <type-id-from-catalog>
    params: <map>

connections:
  - { from: <node-id>.<port>, to: <node-id>.<port>, atten: <number> }
```

| Key           | Required | Type   | Meaning                                                  |
|---------------|----------|--------|----------------------------------------------------------|
| `schema`      | yes      | string | YAMS format version, of the form `yams/<major>`.         |
| `catalog`     | cond.    | string | Catalog identifier. Required if any node uses a non-trivial type. |
| `name`        | no       | string | Human-readable name for the patch.                       |
| `nodes`       | yes      | map    | Node ID → node definition.                               |
| `connections` | yes      | list   | List of connection objects.                              |
| `include`     | no       | list   | Names of external definition files to load before this file. See **Include**. |
| `alias`       | no       | map    | Named parameter aliases for compound definition documents. See **Compound Definitions — alias**. |

Catalogs MAY introduce additional top-level keys. See **Extension Keys** under Catalogs.

## Nodes

Each node has:

- A unique ID (the YAML key under `nodes`).
- A `type` string referencing the catalog's vocabulary.
- An optional `params` map.

```yaml
nodes:
  src1: { type: emit, params: { value: 0.8 } }
  lim:  { type: clamp, params: { min: -0.5, max: 0.5 } }
```

**Scalar shorthand.** When a node has no `params`, `enabled`, or `bypass` keys, the value MAY be written as a bare type string instead of a mapping:

```yaml
nodes:
  fbk: feedback
  src: emit
```

This is exactly equivalent to `{ type: feedback }` / `{ type: emit }`. Serializers SHOULD emit the map form for round-trip stability; this shorthand is a read convenience.

### Node IDs

- IDs are stable, human-readable identifiers. They MUST match `[a-z][a-z0-9_]*` and be unique within the file.
- Tools that auto-generate IDs SHOULD use type-prefixed names (`emit1`, `emit2`, `clamp1`).
- IDs are the addressing primitive for connections and for external references (scripts, automation, action invocations).

### Node flags

Two optional boolean keys control how a node is processed at runtime:

| Key       | Default  | Meaning |
|-----------|----------|---------|
| `enabled` | `true`   | When `false`, the node produces all-zero output. Signal does not flow. Equivalent to patching silence into its outputs. |
| `bypass`  | `false`  | When `true`, the first input is copied to the first output unmodified. The node's own processing is skipped. |

```yaml
nodes:
  lim: { type: clamp, params: { max: 0.8 },    enabled: false }
  pre: { type: scale, params: { factor: 0.5 }, bypass: true }
```

`enabled` and `bypass` are node-level keys, not entries inside `params`.

### Ports

A port is a named input or output on a node. The catalog defines which ports a type exposes.

Port addresses have the form `<node-id>.<port-name>`.

Ports are not typed in YAMS. Any output port can connect to any input port. Type interpretation lives in the destination type, not in the format. (See "Value Model" below.)

### Parameters

Node parameters take two shapes:

**Primitive** — when only the value matters:
```yaml
factor: 0.5
```

**Object** — when range, unit, or other metadata matters:
```yaml
factor: { value: 0.5, min: 0, max: 4, unit: ratio }
```

Object form is recognized by the presence of a `value` key. Reserved object keys: `value`, `min`, `max`, `unit`. Catalogs MAY define additional keys; readers MUST ignore unknown keys.

A parameter MAY also be addressed as a port — connections can target `<node-id>.<param-name>` to drive the parameter dynamically. This is what makes "one node's output continuously varying another node's parameter" expressible.

## Connections

Connections are an ordered list. Two syntactic forms are accepted:

**Long form** — explicit mapping with all optional fields available:
```yaml
connections:
  - { from: src.out, to: lim.in, atten: 0.7 }
  - { from: mod.out, to: lim.max, atten: 0.6 }
```

**Compact form** — single-wire shorthand, or fan-out to multiple destinations:
```yaml
connections:
  - src.out: lim.in
  - mod.out:
    - lim.max
    - trim.factor
```

Compact form does not support `atten`, `enabled`, or other optional fields. Use long form when those are needed.

| Field      | Required | Type    | Default | Meaning                                                              |
|------------|----------|---------|---------|----------------------------------------------------------------------|
| `from`     | yes      | string  | —       | Source port address (`node-id.port-name`).                           |
| `to`       | yes      | string  | —       | Destination port address (`node-id.port-name`).                      |
| `atten`    | no       | number  | `1.0`   | Scalar multiplier applied to the signal. Range `-1..1`. Negative inverts. |
| `enabled`  | no       | bool    | `true`  | When `false`, signal does not flow. Soft-mute without deletion.      |

A connection is a near-pure wire: it scales the source by `atten` (optionally), sums into the destination, and that's it. Any other signal transformation is a node.

**Deprecated connection fields (parsers MUST still accept on read, runtimes MUST ignore, writers SHOULD omit on new files; implementations SHOULD warn that the field has no effect, naming the replacement node):**

| Field      | Replaced by                                        |
|------------|----------------------------------------------------|
| `offset`   | a node that adds a constant                        |
| `polarity` | a rectifying node (half- or full-wave)             |
| `curve`    | a node applying the transfer curve (power, exp, log) |

Catalogs name these nodes; the format does not. The point of the deprecation is that a wire scales and sums — every other transformation is a node.

Readers MUST ignore unknown fields (forward-compatibility).

### List-form endpoints

`from` and `to` each accept a list of port addresses in long form. Expansion rules:

- One side list, other side scalar → fan-out / fan-in (N connections).
- Both sides lists of equal length → zip-pair: element *i* of `from` wires to element *i* of `to`.
- Both sides lists of unequal length → error naming both counts.

Shape decides, not count: a one-entry list is a list. `{ from: [ a.out ], to: [ x.in, y.in ] }` is two lists of unequal length, an error; the fan-out is spelled `{ from: a.out, to: [ x.in, y.in ] }`.

Optional fields (`atten`, `enabled`, …) replicate to every expanded connection. The compact form's value may also be a list (fan-out only).

```yaml
connections:
  - { from: [ src_a.out, src_b.out ], to: sink.in }        # fan-in
  - { from: gate.out, to: [ src_a.reset, src_b.reset ] }   # fan-out
  - { from: [ a.out, b.out ], to: [ fa.in, fb.in ] }       # zip-pair
```

### Wildcard endpoints

A list element MAY be a **pattern**: a port address whose node-id segment contains `*` (matching any run of characters). The pattern expands, in node declaration order, to one entry per node that (a) matches the id pattern and (b) actually exposes the named port in the required direction (output for `from`, input for `to`). Nodes that match the id but don't expose the port are skipped silently — that is the point of a pattern; it must skip the unrelated nodes in scope.

```yaml
connections:
  - { from: [ src_*.out ], to: sink.in }            # fan-in of every src_* output
  - { from: gate.out, to: [ src_*.reset ] }         # fan-out to every src_* reset
  - { from: [ src_*.out ], to: [ lim_*.in ] }       # patterns zip pairwise
```

Rules:

- **Patterns are only legal in list position.** A scalar `from`/`to` (or compact-form endpoint) containing `*` is a parse error. Scalar position always means exactly one literal wire; anything that can fan is visibly a list. Against a scalar on the other side, expansion is a purely element-level rewrite inside the list — literals expand to themselves, patterns to their matches, results concatenate — so patterns and explicit entries mix freely: `{ from: [ src_*.out, gate.out ], to: sink.in }`.
- **Node-id segment only.** The port segment is literal; `*` there is an error.
- **Zero matches is an error.** A pattern that matches no exposing node fails loudly (naming any id-only matches), so a typo cannot become a silently dead wire.
- **Zip with patterns:** list elements pair positionally first; a pattern element's expansion then zips against its partner's. Expansion-count mismatch is an error naming both patterns and both match lists. Because pairing comes first, a pattern stands in for exactly one entry of the other list: `{ from: [ src_*.out ], to: [ a.in, b.in ] }` is unequal lists (1 and 2), an error — never every match into every destination.
- **Scope.** Patterns match the top-level node ids of their own document (main or definition). A compound-typed node matches when its surface — member-path reach-in plus any aliases (the two coexist) — exposes the port.
- **Quoting.** A pattern beginning with `*` (`"*.reset"`) MUST be quoted — unquoted `*` is a YAML alias, forbidden by the restricted subset. Patterns beginning with a literal (`src_*.reset`) need no quotes; prefer them.

### Uniqueness

A `(from, to)` pair MUST be unique within a file. Multiple connections between the same two endpoints are invalid; combine their attenuations into a single connection.

### Modulating connection parameters

YAMS connection fields (`atten`, `offset`, etc.) are not modulation targets. To modulate a connection's effective attenuation, insert a node into the path whose own parameter is modulatable. Catalogs typically provide a scaling node for this purpose — in this document's examples, `scale`, whose `factor` is itself addressable as a port.

This keeps connections as pure wires: a single signal scaled and offset, nothing else. The graph itself carries all dynamic behavior.

### Multicursal routing

Fan-out and fan-in are emergent from the connection list:

- **Fan-out:** multiple connections share a `from`. The source signal is replicated.
- **Fan-in:** multiple connections share a `to`. Signals sum at the destination, each with its own attenuation.

No mixer node is required for summing. A mixer node MAY be provided by a catalog when explicit per-input control or named inputs are desired.

## Value Model

YAMS imposes one data model on every connection:

- **Range.** Values are normalized to `-1..1` by convention. Producers should emit values in this range; consumers should accept it. Out-of-range values are not forbidden; how they are handled (clipped, wrapped, passed through) is a runtime or catalog concern.
- **Untyped.** YAMS does not distinguish categories of values — continuous vs discrete, time-varying vs static, dense vs sparse. Any output port may feed any input port. Meaning emerges at the destination.
- **Schedule-agnostic.** YAMS does not specify update rate, block size, or timing model. Runtimes decide when and how fast values flow. Catalogs MAY document scheduling hints per type.

A parameter destination maps the incoming value through its `min`/`max` into the destination's own range. A non-parameter destination receives the raw normalized value.

## Catalogs

A **catalog** is a published list of node types with documented ports, parameters, and behavior.

Files declare their catalog with:

```yaml
catalog: <name>/<major-version>
```

Examples: `example/1`, `eurorack.docs/1`, `lighting.dmx/2`.

Catalogs are external to YAMS. Their identifier strings have no inherent structure beyond `<name>/<major-version>`; resolution (where to find the catalog document) is a host concern.

A YAMS implementation that does not recognize a catalog can still:
- Parse the file.
- Render the graph topologically (nodes, edges, attens).
- Preserve unknown params and unknown connection fields on round-trip.

It cannot execute the patch. That requires the catalog.

### Structural types

Some node types are not signal-processing operations — they exist purely for graph topology. These are reserved by the YAMS spec, carry no namespace prefix, and are valid without a catalog declaration.

| Type | Ports | Purpose |
|---|---|---|
| `passthrough` | `in` ↓, `out` ↑ | Identity (`out = in`). Named fan-in junction or labeled wire tap. |
| `constant` | `out` ↑; param `value` | Emits a fixed value every sample. Injects a scalar into the graph. |
| `feedback` | `in` ↓, `out` ↑ | Cycle-breaker. Re-injects the previous block's signal, breaking the dependency so the compiler can schedule the cycle. Introduces one block (~10 ms at 512 frames / 48 kHz) of latency. |

The distinction matters: these nodes are infrastructure. They are to signal graphs what variables and wires are to circuits — not operations, just structure. Catalog-owned operation nodes transform signals; structural nodes only route or hold them. This is why they have no namespace prefix and belong to the spec rather than any catalog.

**Feedback cycles** — without `feedback`, any cycle in the connection graph is a compile error. Place exactly one `feedback` node in each cycle to break it:

```yaml
nodes:
  stage1: { type: clamp,    params: { min: -1, max: 1 } }
  fbk1:   { type: feedback }
  amt1:   { type: scale,    params: { factor: 0.45 } }
connections:
  - stage1.out: fbk1.in
  - fbk1.out:   amt1.in
  - amt1.out:   stage1.in
```

The compiler schedules `feedback` nodes last. At render time, `feedback.out` carries last block's signal (silence on block 0), and `feedback.in` latches this block for next render.

### Extension Keys

Catalogs and hosts often associate domain-specific metadata with a patch — user-facing knob bindings for a synth, cue triggers for a lighting rig, pad layouts for a video mixer, arbitrary presentation hints. YAMS accommodates this with **extension keys**: top-level keys not defined by this core spec.

- A catalog MAY define additional top-level keys and their schemas.
- Readers MUST preserve unknown top-level keys on round-trip.
- Validators SHOULD NOT reject a file solely because of an unrecognized top-level key. They MAY warn.
- Extension keys are catalog-scoped by convention. Collision across catalogs is a catalog-authorship concern; YAMS core does not mandate a naming scheme.

A YAMS-core-only reader remains useful across domains: it parses the graph, preserves extensions opaquely, and lets catalog-aware tools interpret the rest.

## Multi-Document Files

A YAMS file MAY contain multiple YAML documents separated by `---`. This is the primary mechanism for defining reusable sub-patch types inline.

### Structure

```
<file header>
---
<definition document>
---
<definition document>
---
<main document>
```

**File header** — the first segment (before the first `---`). Contains `schema`, optional `catalog`, and optional `include`. These apply to all subsequent documents unless overridden. No `nodes` or `connections` allowed here.

**Definition documents** — any segment except the last that contains `nodes`. MUST have a `name:` key. The name becomes a usable type ID within this file.

**Main document** — the last segment. The runnable patch. May optionally have a `name:`.

### Reuse and instantiation

A type defined in a definition document behaves like a catalog type: each `nodes:` entry that references it creates an independent instance with its own internal state (phase accumulators, envelope levels, etc.).

```yaml
schema: yams/1
catalog: example/1
---
name: ramp
nodes:
  src: { type: emit,  params: { value: 0.5 } }
  amt: { type: scale, params: { factor: 1.0 } }
connections:
  - { from: src.out, to: amt.in }
---
name: my-patch
nodes:
  ramp1: { type: ramp, params: { value: 0.1 } }
  ramp2: { type: ramp, params: { value: 0.3 } }
```

### Port exposure

Ports are derived from graph topology — no explicit declaration required.

**Signal outputs** — output ports with no outgoing connections. If exactly one: exposed as `out`. If multiple: exposed as `nodeID.portName`.

**Signal inputs** — unconnected signal input ports. If exactly one: exposed as `in`. If multiple: exposed as `nodeID.portName`.

```yaml
---
name: single-out
nodes:
  fan: { type: split }
  amt: { type: scale, params: { factor: 0.5 } }
connections:
  - fan.left:  amt.in
  - fan.right: amt.in     # both of fan's outputs are consumed
---
name: multi-out
nodes:
  fan: { type: split }    # neither output is consumed
connections: []
```

In `single-out`, `amt.out` is the only unconnected output, so the compound exposes it as plain `out`. In `multi-out`, both `fan.left` and `fan.right` are free, so neither can claim the bare name and each is exposed qualified: `fan.left`, `fan.right`.

**Parameters** — every param and port of every internal node is reachable by its **member path**, unconditionally. The qualified form `nodeID.paramName` always works, at any nesting depth: a compound built from compounds is addressed by chaining (`stage.amt.factor` reaches two levels in, `voice.stage.amt.factor` three). If a param name is unique across all internal nodes the short form (e.g. `value`) also works; if the same name appears on multiple nodes the short form is ambiguous and callers MUST use the qualified form (a validator MUST emit a helpful error: `ambiguous param 'factor' — did you mean amt.factor or trim.factor?`).

This is the one model: **member-path reach-in is the default and is always available.** An `alias` section does not switch it off — aliases are optional sugar that *add* named shortcuts on top of the always-present surface (see **Compound Definitions — alias** below).

**Member-path resolution.** The compiler resolves a member path to its leaf node+port by walking the definition tree — conceptually one nesting level per expansion pass — until the path lands on a catalog-kernel port/param. Depth is unbounded; the only structural limit is that a definition MUST NOT (transitively) instantiate itself (a recursive definition can't expand to a finite graph and MUST be a compile error). This resolution is uniform across every context that addresses a port: connections, controls, timeline (`transport:`) events, taps, and wildcard patterns.

### Compound Definitions — alias

The `alias` section in a definition document declares the **public parameter API** for that compound type. It is a mapping from an external name (what callers write) to an internal `nodeID.paramName` target:

```yaml
---
name: bounded-ramp
nodes:
  src: { type: emit,  params: { value: 0.5 } }
  lim: { type: clamp, params: { min: -1, max: 1 } }
connections:
  - src.out: lim.in
alias:
  level: src.value
  lo:    lim.min
  hi:    lim.max
---
name: my-patch
nodes:
  ramp: { type: bounded-ramp, params: { level: 0.3, lo: -0.6, hi: 0.6 } }
  out:  { type: collect }
connections:
  - ramp.out: out.in
```

An alias target may be a single string or a list — useful when one external name should drive multiple internal params simultaneously:

```yaml
alias:
  level: src.value        # single target — scalar
  ceiling:                # multi-target — list
    - lim1.max
    - lim2.max
```

Setting `ceiling` on an instance writes the same value to both `lim1.max` and `lim2.max`.

A list element MAY be a wildcard pattern (`*` in the node-id segment, port segment literal), expanding to one target per internal node that matches the id and exposes the named param/port — same rules as **Wildcard endpoints** under Connections (list position only, zero matches is an error, non-exposing nodes skip silently, quote a leading `*`):

```yaml
alias:
  reset: [ src_*.reset ]     # one external reset fans to every src_* node
```

`alias` is **optional sugar layered on the always-present member-path surface — it is not a replacement for it.** When `alias` is present:
- The listed names become *additional* accepted params/ports on instances of this type — **in addition to** member-path reach-in (`lfo.osc.freq`) and the topology-derived short names, which remain available. Declaring an alias does NOT hide the internals or make the table the sole surface.
- Each target must be an exact `nodeID.<name>` string pointing to a real param, port, or list-typed param inside the definition. A validator MUST reject alias entries that don't resolve.
- **Alias targets may reach through nested compounds.** When the target's `nodeID` names a sub-node whose type is itself a compound, the remaining segment is resolved against that compound's surface (its own aliases and its reach-in surface) — at any depth, the same member-path resolution described above. A compound aliasing `level: inner.level`, where `inner` is itself a compound, resolves through `inner`'s own surface to the leaf param. Chains are flattened at expansion time; live-control writes terminate at the deepest catalog-kernel param.
- **List-typed params** are valid alias targets even though they are not scalar. Catalogs declare which of a type's params accept lists. A scalar value passed where the target expects a list (e.g. `taps: 3` instead of `taps: [3]`) is a compile-time type-mismatch error, not a silent no-op.

Use `alias` to publish a **clean, stable public name** (rename) or to drive several internal targets at once (fan-out). Prefer it for a definition's intended public API. Note that, because member-path reach-in is always available, an alias is a convenience and a recommendation, not an encapsulation boundary — callers *can* still reach internals directly, so renaming an internal node can still break a caller who reached past the alias.

### Single-document files

Files without any `---` separator parse identically to before. `schema:` is required on the document itself.

## Include

The `include:` key takes one or more names, without extension: a bare file name, or a relative path to one (see §Resolution). Each name resolves to an external `.yams` file (or directory of files) whose definition documents are prepended to this file's own definitions before expansion.

```yaml
include: [ stdlib, my-lib ]   # multi-include sequence form
include: stdlib                # single-include shorthand
include: ../shared/drums       # a relative path: drums in a sibling directory
```

Single-include shorthand and the 1-element sequence `[ stdlib ]` are equivalent — pick whichever reads better.

In a multi-document file, `include:` belongs in the file header alongside `schema:` and `catalog:`. In a single-document file, it is a plain top-level key. It is not valid inside a definition document or the main document of a multi-document file.

### Resolution

A name is either a bare name (`foo`) or a relative path (`lib/foo`, `../shared/foo`): directory components separated by `/`, where `..` names the parent directory. A path resolves exactly as a bare name does, joined onto each search path in turn — so `../shared/foo`, searched from the including file's directory, is `foo` in that directory's sibling `shared/`. The last component is the name that the rules below match; its directory components only say where to look.

A name MUST NOT be an absolute path (one beginning with `/`): a document that names a location on one machine cannot load on another. Separators are always `/`, whatever the host platform.

A name `foo` (bare, or the last component of a path) resolves to one of, in order:

1. A file `foo.yams` (canonical extension).
2. A file with another loader-recognized extension. A host that gives its patches its own extension resolves that too.
3. A package — a directory bundle with a loader-recognized package extension. A package include behaves exactly like a directory include over the bundle's top level; the directory rules below skip the bundle's non-library files (manifests, layouts, assets).
4. A directory `foo/` containing one or more `.yams` files.

Resolution order across search paths is implementation-defined and MUST be documented by the loader. The following conventions apply:

- The directory containing the including file is always searched first.
- Additional paths (bundled libraries, environment variables, flags) are searched in order afterward.
- First match wins.
- Within a single search path, files take precedence over a directory of the same name. This protects against a stale-named directory accidentally shadowing a current file. A package ranks with documents for the same reason — plain files beat a same-named package, and a package beats a same-named bare directory.

A loader that cannot resolve a name MUST emit an error.

### What is imported

Only the **definition documents** (named `---`-separated segments) of an included file are imported. The included file's header and main document are ignored. An included file's `schema` MUST match the including file's `schema`; a mismatch is an error.

When a name resolves to a directory, every `.yams` file inside is loaded as if each were a separate include with the same name. Directory rules:

- **Files only.** Each `.yams` file in the directory contributes its definitions. Loaders MAY also accept other recognized extensions.
- **Flat.** Subdirectories are not recursed. A directory-include loads only the files at its top level.
- **Lexicographic order.** Files load in lexicographic order by filename. Order does not carry semantic meaning (each definition stands alone), but a stable order makes collision messages reproducible.
- **Skip non-library files.** Files whose extension is not a recognized library extension (README.md, LICENSE, .DS_Store, etc.) are silently skipped so a library directory can carry top-level documentation.
- **Schema match.** Every loaded file's `schema` must match the including file's, just as for single-file includes.
- **Collisions.** Two files inside the same directory defining the same name is a name collision (see §Name collisions); the error message names both files.

### Load order

Definitions are collected depth-first: each name in `include:` is fully resolved — including its own transitive includes — before moving to the next name in the list. Within the resolved set, dependencies precede dependents. The including file's own definitions come last.

```
A includes [B, C]; B includes [D]
Definition order: D, B, C, then A's own definitions
```

### Name collisions

**Diamond import** — the same file reached via two paths in the include tree is loaded exactly once, at its earliest position. No error.

**Include-vs-include collision** — two different files both define the same name. Error: `definition 'foo' defined in both 'lib-a' and 'lib-b'`. The file does not load.

**File-vs-include shadowing** — the including file defines a name that an included file also defines. The including file's definition wins silently. This is intentional local override; no warning is required, though loaders MAY emit one.

### Circular includes

A loader MUST detect and reject circular chains (`A → B → A`). Detection uses the set of files currently being loaded: if a file about to be loaded is already in that set, a circular include error is emitted.

## Safe YAMS

To avoid YAML parser ambiguities and ensure cross-implementation consistency, YAMS files MUST conform to this restricted subset:

- No anchors (`&`) or aliases (`*`).
- No tags (`!!str`, `!!int`, etc.).
- No directives (`%YAML`, `%TAG`).
- No end-of-document markers (`...`). Document separators (`---`) are allowed for multi-document files.
- Booleans MUST be lowercase `true` or `false`. The strings `yes`, `no`, `on`, `off`, `Y`, `N`, etc. are NOT recognized as booleans.
- Strings that could be misinterpreted as booleans, nulls, or numbers MUST be quoted.
- Numbers are decimal only. No octal (`0o17`), hex (`0x1F`), or sexagesimal (`1:30:00`).
- Indentation is two spaces. Tabs are forbidden in indentation.
- Keys are strings. No complex/mapping keys.
- No block scalars (`|`, `>`) or block collections. Only inline/flow syntax is permitted.
- Strings containing `:` must be quoted to avoid interpretation as key-value separators.

### Formatting Rules

To ensure consistent parsing and support reliable agent generation:

- **Colon-space rule:** A mapping key followed by `:` MUST have whitespace before the value. Write `key: value`, never `key:value`. This is required before all value types, especially flow collections: `key: { ... }`, not `key:{ ... }`.
- **List item spacing:** List items MUST have space after the `-` prefix. Write `- item`, never `-item`.
- **Flow collection spacing:** Flow mappings and sequences MUST have spaces after `{` and `[`, before `}` and `]`, and after `,` separators. Write `{ key: value }` and `[ a, b, c ]`, not `{key:value}` or `[a,b,c]`.
- **Quoted strings:** Strings that could be ambiguous (contain `:`, look like numbers, look like booleans, or start with special characters) MUST be quoted with double quotes. When in doubt, quote.
- **No inline comments.** Comments are allowed at the end of a line but not within flow collections or on the same line as connection definitions.

Validators SHOULD reject files that violate Safe YAMS even if the underlying YAML parser accepts them.

## Validation

A YAMS validator checks, in order:

1. The file is valid YAML and conforms to Safe YAMS.
2. `schema`, `nodes`, and `connections` are present and well-formed.
3. Every node ID matches the ID syntax and is unique.
4. Every node `type` exists in the declared catalog (skip if no catalog).
5. Every connection's `from` and `to` reference an existing node and a port that the node's type exposes (skip port check if no catalog).
6. No `(from, to)` pair appears twice.
7. All optional connection fields are within their documented ranges.
8. In multi-document files: every `alias` target resolves to a real `nodeID.paramName` inside its definition. Instances of alias-bearing types may only set params listed in `alias`.

When `include:` is present, these additional checks apply:

9. Each name in `include:` resolves to a loadable `.yams` file or directory of `.yams` files under the configured search path.
10. No circular include chains exist in the transitive include tree.
11. No two different included files define the same name (include-vs-include collision). For directory includes, two files inside the same directory defining the same name is the same kind of collision.
12. Each included file declares the same `schema` as the including file.

A validator MAY perform additional catalog-defined checks (e.g., type compatibility, recommended ranges) but these are non-normative.

## Versioning

- **`schema`** versions the YAMS format itself. Backwards-incompatible changes increment the major version: `yams/1` → `yams/2`. No minor versions.
- **`catalog`** versions are owned by each catalog and version on their own cadence.

A reader implementing `yams/1` MUST reject files declaring `yams/2`. A reader implementing `yams/2` MAY accept `yams/1` files.

## Examples

### Minimal

```yaml
schema: yams/1
nodes:
  src: { type: passthrough }
  dst: { type: passthrough }
connections:
  - { from: src.out, to: dst.in }
```

### Patch using a catalog

```yaml
schema: yams/1
catalog: example/1
name: two-sources

nodes:
  a:    { type: emit,  params: { value: 0.8 } }
  b:    { type: emit,  params: { value: 0.4 } }
  mix:  { type: merge }
  trim: { type: scale, params: { factor: 0.5 } }
  lim:  { type: clamp, params: { min: -1, max: 1 } }
  out:  { type: collect }

connections:
  - { from: a.out,    to: mix.a }
  - { from: b.out,    to: mix.b,  atten: 0.5 }
  - { from: mix.out,  to: trim.in }
  - { from: trim.out, to: lim.in }
  - { from: lim.out,  to: out.in }
```

Node types come from the declared catalog — here the fictional `example/1` of [Appendix A](#appendix-a--the-example1-catalog). A catalog may also define extension keys (e.g. `controls` for user-facing knob bindings) that appear alongside `nodes` and `connections`; see the catalog's own spec.

### Modulating a modulation amount

One signal's influence on another is itself made dynamic, by inserting a scaling node into the path and driving *its* factor from a third source. This is the pattern that makes a parameter-as-port worth having.

```yaml
schema: yams/1
catalog: example/1

nodes:
  source: { type: emit,  params: { value: 0.9 } }
  shaper: { type: emit,  params: { value: 0.1 } }
  depth:  { type: scale, params: { factor: 0.5 } }
  target: { type: scale, params: { factor: 1.0 } }
  out:    { type: collect }

connections:
  - { from: source.out, to: depth.in }
  - { from: shaper.out, to: depth.factor, atten: 0.5 }
  - { from: depth.out,  to: target.factor, atten: 0.02 }
  - { from: target.out, to: out.in }
```

`depth` is the attenuverter. Its own `factor` is driven by `shaper`, so how much of `source` reaches `target.factor` varies over time. Note that `factor` appears twice in different roles — as a param in `params:` and as a connection destination — which is the same addressing either way.

## Round-Tripping

A conformant reader/writer pair MUST preserve:

- All declared keys, including unknown fields (forward-compatibility).
- Connection order.
- Node order (insertion order in the YAML map).
- Object-form vs primitive-form parameters (do not normalize one to the other).

Comments and formatting are NOT required to round-trip. Tools that wish to preserve them SHOULD use a comment-preserving YAML library; the spec does not require it.

## Relationship to Other Formats

YAMS sits near several existing formats. Comparisons are drawn from domains where node-graph serialization has history; analogous relationships hold elsewhere.

- **Patchbook** (SpektroAudio): documentation-first text format for modular synth patches. YAMS overlaps in intent but targets execution + documentation, drops typed connection operators in favor of universal wires, and adds connection-level parameters.
- **JSON Patch / JSON Pointer:** YAMS is a serialization format, not an edit protocol. JSON Pointer-style addressing of YAMS fields is straightforward but not standardized here.
- **Pure Data / Max patches:** structured patch formats specific to a runtime. YAMS is runtime-neutral.
- **Node-based shader graphs, VJ routing, DMX cue engines, Web Audio API graphs:** each domain builds live graphs at runtime but rarely serializes them to a stable, human-editable text format. YAMS is the serializable counterpart anywhere a graph wants to be written down, diffed, or authored by an agent.

## Appendix A — the `example/1` catalog

Every example in this document is written against `example/1`. **It is fictional.** It exists to give the examples something concrete to name without tying the specification to any real domain, and it is deliberately abstract: no host ships it, and no patch written against it will run anywhere.

It is defined here for the same reason IETF documents use `example.com` — a reader needs to see a complete file, and a reader must never mistake the illustration for the thing.

| Type | Inputs | Outputs | Params | Behavior |
|---|---|---|---|---|
| `emit` | — | `out` | `value` | Emits `value`. A graph's origin. |
| `scale` | `in`, `factor` | `out` | `factor` | `out = in × factor`. `factor` is addressable both as a param and as an input port — the case that makes parameter-as-port concrete. |
| `clamp` | `in` | `out` | `min`, `max` | Constrains `in` to the range. A type with more than one param. |
| `merge` | `a`, `b` | `out` | — | Combines two inputs. Exists so fan-in and `atten` have somewhere to land. |
| `split` | `in` | `left`, `right` | — | Two outputs, so the multiple-output branch of **Port exposure** has a case. |
| `collect` | `in` | — | — | A terminus. A graph's sink. |

The structural types `passthrough`, `constant` and `feedback` are **not** part of this catalog — they are defined by this specification and are available without any catalog declaration. See [Structural types](#structural-types).

A real catalog documents far more per type: value ranges, units, scheduling hints, error conditions. `example/1` documents the minimum needed to read the examples.

## Open Questions

These are deferred to future versions or to catalog conventions:

- **Visual sidecars.** Layout (positions, colors, notes) lives in an optional sidecar file (`<name>.yams.layout`?), schema TBD.
- **Variable port counts.** Some types (mixer with N inputs) want runtime-determined port arity. Convention TBD; current guidance is to enumerate ports explicitly (`in0`, `in1`, ...).
- **Polyphony.** Multiple simultaneous voices sharing the same patch structure. Convention TBD.
