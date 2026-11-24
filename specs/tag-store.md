# The tag store

Status: stable since 2026-11-23 (tenstag-rust 0.6.0; format 2, with owners, since tenstag-rust 0.9.0). A change that
changes bytes is a new version (README.md, Status).

Where and how tags (tags.md) are kept, so that every program, in every language, reads and writes the same tags.
One file per identity (fingerprint.md) that has tags.

Test vectors: [`test-vectors/tag-store.json`](test-vectors/tag-store.json).

```text
  <cache folder>/tags/tfp1/<64 hex>.json          one identity's tags
  <cache folder>/tags/tfp1/<64 hex>.lock          its lock, held while writing; never deleted by a writer
  <cache folder>/tags/tfp1/<64 hex>.json.tmp-*    a file being written
```

## Rules

### TGS-001 (MUST): the tag folder

Tags are kept in `tags/` in the cache folder of fingerprint-cache.md TFC-001 (a folder the program gives, else
`TENSTAG_CACHE_DIR`, else the system's cache folder): tags are a cache (tags.md TAG-008), kept beside the
fingerprints they are keyed by, where a person expects to be able to clear them.

(Until 2026-11-23, tenstag-rust 0.6.0 to 0.7.1, tags were kept in a data folder, `TENSTAG_DATA_DIR` or
`~/.local/share/tenstag`. That folder is no longer read; what was there can be worked out again.)


### TGS-002 (MUST): file names

An identity `tfp1:<hex>` has its tags in `tags/tfp1/<hex>.json` under the cache folder. A later fingerprint version
uses its own folder (`tags/tfp2/`). Every other name in the folder is ignored.

### TGS-003 (MUST): the file

A JSON object, UTF-8, with:

| key | value |
|---|---|
| `format` | `"tenstag-tags/2"` |
| `identity` | the identity, `"tfp1:<hex>"`, the same as the file's name |
| `tags` | an object: each owner's name (TAG-009) to `{"version": <TAG-010>, "tags": {<key>: <value as a string, or null for a word>}}` |
| `bytes` | the model's size in bytes (a set's members' together): a hint for people and for clean-up |
| `sha256` | optional: the lowercase hexadecimal SHA-256 of a one-file model's bytes, when it is known (TGS-008) |
| `sha256_from` | with `sha256`: `"store"` or `"read"`, as fingerprint-cache.md TFC-002 says |
| `seen` | the paths the model was last seen at, newest first, at most 16: each `{"path": <absolute path>, "time": <RFC 3339 UTC, seconds>}` |

Writers write owners and keys in ascending byte order, change only their own owner's object, and keep any top-level
key they do not know, and other owners' objects as they are. `seen` is a
hint for programs and for clean-up; it never decides identity.

Example:

```json
{
  "format": "tenstag-tags/2",
  "identity": "tfp1:5c0c4b0b...",
  "tags": {
    "chatrun": {"version": 2, "tags": {"arch": "qwen3", "chat": null, "context": "32768"}},
    "imagenode": {"version": 1, "tags": {"encoder": "qwen2.5-vl-7b"}}
  },
  "bytes": 639446688,
  "seen": [{"path": "/models/Qwen3-0.6B-Q8_0.gguf", "time": "2026-11-23T14:02:11Z"}]
}
```

### TGS-004 (MUST): reading

A file is read without a lock (writers replace it by a rename, TGS-005). A reader treats as no tags: a missing file;
a file of format `tenstag-tags/1` (tenstag-rust 0.6.0 to 0.8.0, whose tags had no owners); and, with a warning, a file
that is not valid JSON, has another `format`, an `identity` that does not match its name, a `tags` that is not an
object, an owner's object without a whole-number `version` or with a `tags` that is not an object, an owner name that
breaks TAG-009, a key or value that breaks TAG-002 or TAG-003, or an owner or a key that appears twice. A file over
1 MiB need not be read.

### TGS-005 (MUST): writing

To change an identity's tags:
1. Create `<hex>.lock` if it is missing, and take an exclusive lock on it: `flock(LOCK_EX)` on Unix; `LockFileEx`
   with `LOCKFILE_EXCLUSIVE_LOCK` over byte 0 on Windows. Wait for it. A file system that cannot lock is an error:
   nothing is written.
2. Read `<hex>.json`.
   - Missing, or of format `tenstag-tags/1`: start from no tags (the older file is replaced: tags are a cache).
   - Of a format other than those two: never changed. Stop with an error.
   - Unreadable as `tenstag-tags/2` (TGS-004): rename it to `<hex>.json.corrupt-<unique>`, keep it for a person to
     look at, and start from no tags.
3. Change only the writer's own owner's tags (TAG-004, TAG-009): when they were written at another version (TAG-010),
   start them from none. Write them with the writer's version; an owner left with no tags is removed. Update `bytes`,
   `sha256` and `seen` when the writer knows better.
4. When no owner has tags left, delete `<hex>.json`. Otherwise write `<hex>.json.tmp-<unique>` in the same folder, flush it
   to disk, and rename it over `<hex>.json` (on Windows, retry for a short while if a reader holds the file open).
5. Release the lock. The lock file stays: deleting it would let two writers lock two different files.

`<unique>` is any text that two writers cannot both choose, such as the process id and the time in nanoseconds.

### TGS-006 (MAY): cleaning

Tags are a cache, so anything in the tag folder may be deleted at any time: by a person clearing the cache, or by
an implementation, under the file's lock, deleting `.json.tmp-*` files older than an hour, `seen` paths that no
longer exist while the folder that held them does, or whole tag files (of identities not seen for a while, say).
A reader takes a missing folder or file as no tags, and a writer creates them again (TGS-005). A lock file deleted
while a writer holds it can let a second writer lock a new file at the same time; one of the two changes is then
lost, which a cache allows.

### TGS-007 (MUST): the model's paths are not its key

Two copies of a model at different paths have one identity and share one tags file. A program that wants different
tags for two copies cannot have them: the copies are the same model.

### TGS-008 (SHOULD): SHA-256

A full SHA-256 of a one-file model is recorded in `sha256`, with `sha256_from`, when a writer knows it: from the
store's name for the file (fingerprint-cache.md TFC-006, `"store"`), or computed from the bytes when a program asked
(`"read"`). A `"read"` value is never replaced by a `"store"` one. It is never required, and never part of the
identity.
