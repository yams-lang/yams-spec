# Specification versions

Each `schema:` major version gets its own directory, published side by side.
A released version's directory is **never edited** except for errata — a
citation, a DOI, or an implementer's bookmark must keep resolving to the text
it resolved to originally.

| Directory | `schema` | Status |
|---|---|---|
| [`1.0/`](1.0/) | `yams/1` | Current. Released — tag `1.0.0`. |

## Three version numbers, three jobs

They are easy to conflate and mean different things:

| Number | Where it appears | Changes when |
|---|---|---|
| `yams/1` | in every patch file's `schema:` key | a backwards-incompatible format change lands |
| `1.0`, `1.1` | this directory, and the repo's git tags | the specification document changes at all, including clarifications |
| `yams-swift` semver | that package's releases | the implementation changes, on its own cadence |

The first is deliberately coarse. A patch file declares only the major
version, because that is the only thing a reader needs in order to decide
whether it can load the file at all. A `yams/1` document written against
spec 1.0 stays valid under spec 1.3 — later revisions clarify and add, they do
not invalidate.

The second is the document's own history. A wording fix that changes no
behavior still gets a version, because someone cited the old wording.

The third is nobody else's business. An implementation can release a hundred
times against one frozen specification.

## Adding a version

A **new minor** (`1.0` → `1.1`) is a copy of the directory with the revisions
applied, and a row added above. Both remain readable at their own paths.

A **new major** (`yams/2`) means a document a `yams/1` reader must refuse. It
gets `2.0/`, and the `Versioning` section of the specification states the
compatibility rule: a reader implementing `yams/1` MUST reject `yams/2`; a
reader implementing `yams/2` MAY accept `yams/1`.

Errata to a released version are applied in place and noted in an `Errata`
section at the foot of that version's document, dated. Anything larger than an
erratum is a new version.
