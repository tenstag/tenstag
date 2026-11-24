# The fingerprint cache

Status: stable since 2026-11-23 (tenstag-rust 0.6.0). A change that changes bytes is a new version (README.md, Status).

A fingerprint reads up to 33 MiB of a file (fingerprint.md). The cache keeps the fingerprints already computed, so
that a file that has not changed is not read again, and a file moved or renamed on the same file system is not
either. It is a cache: losing it costs time. The tags are kept in the same folder (tag-store.md TGS-001), and are a
cache too. Implementations in different languages share it, so that
one does not read what another has read.

```text
  <cache folder>/fingerprints.json      the cache
  <cache folder>/fingerprints.lock      its lock, held while writing; never deleted
```

## Rules

### TFC-001 (MUST): the cache folder

The first of these that applies:
1. a folder the program gives;
2. `TENSTAG_CACHE_DIR`, when it is set to an absolute path;
3. on Windows, `%LOCALAPPDATA%\tenstag` (else `<home>\AppData\Local\tenstag`);
4. on macOS, `~/Library/Caches/tenstag`;
5. elsewhere, `$XDG_CACHE_HOME/tenstag` when `XDG_CACHE_HOME` is an absolute path, else `~/.cache/tenstag`.

### TFC-002 (MUST): the file

`fingerprints.json` is a JSON object, UTF-8:

| key | value |
|---|---|
| `format` | `"tenstag-fingerprints/1"` |
| `files` | an array of rows, one per file fingerprinted |

A row:

| key | value |
|---|---|
| `path` | the file's absolute path, links resolved |
| `bytes` | its size |
| `modified` | its modification time in nanoseconds since 1970-01-01 UTC, as a decimal string (negative before) |
| `file_id` | optional: the file's identity on its file system, as a string: `<st_dev>:<st_ino>` in decimal on Unix; `<volume serial>:<file index>` in decimal on Windows |
| `identity` | its fingerprint, `tfp1:<hex>` |
| `sha256` | optional: the lowercase hexadecimal SHA-256 of its bytes |
| `sha256_from` | with `sha256`: `"store"` when the file's name in its store gives it (TFC-006), `"read"` when it was computed from the bytes |
| `previous` | optional: the identity this path had before its contents changed |

Writers keep any key they do not know, in the file and in each row. A file may have at most one row per `path`.

### TFC-003 (MUST): using a row

A file's fingerprint is taken from a row only when:
- the row's `path`, `bytes` and `modified` are the file's now; or
- the row has a `file_id`, and its `file_id`, `bytes` and `modified` are the file's now (the file was moved or
  renamed on the same file system). The row's `path` is then changed to the new path.

Otherwise the file is read (fingerprint.md). On Windows, `modified` is the last-write time converted to nanoseconds
since 1970, whose unit is 100 ns.

### TFC-004 (MUST): writing

1. Take an exclusive lock on `fingerprints.lock` (as tag-store.md TGS-005 step 1).
2. Read `fingerprints.json`. When it is missing, unreadable, or of another format, start from an empty cache (a
   file of another format is replaced: it is a cache).
3. Add or replace rows. When a path's row is replaced by one with another identity, the new row's `previous` is the
   old row's `identity`.
4. Write `fingerprints.json.tmp-<unique>`, flush it, and rename it over `fingerprints.json`.
5. Release the lock.

An implementation may gather many rows before writing, as a scan of a large library does. A write that fails is
not an error for the program: the fingerprint is still returned, and computed again next time.

### TFC-006 (SHOULD): SHA-256 from store names

Some stores name a file by its SHA-256. An implementation records it in the file's row (`sha256_from` `"store"`)
without reading the file, from the file's real path (links resolved), when the path is one of these, and only
then:

| store | the real path | store rule (stores/) |
|---|---|---|
| the Hugging Face cache | `.../models--<...>/blobs/<64 hex>`: a folder named `blobs` in a folder whose name starts with `models--` | HFC-020: the Hub's statement, which the cache does not check |
| Ollama | `.../blobs/sha256-<64 hex>`, where the folder holding `blobs` also holds `manifests` | OLM-009 |
| Docker Model Runner | `.../blobs/sha256/<64 hex>` | DMR-007 |

Hex digits are lowercase. Never from:
- a Hugging Face blob of 40 hex digits (a git blob id, SHA-1);
- Docker Model Runner's `blobs/sha512/`;
- RamaLama's `blobs/sha256-<hex>`, whose folder holds `refs` and `snapshots`, not `manifests`: the name is
  sometimes the hash of a name (RML-006);
- a file of any other name or place.

A SHA-256 computed from the bytes (`"read"`) is never replaced by one from a name.

Test vectors: [`test-vectors/store-digests.json`](test-vectors/store-digests.json).

### TFC-005 (MAY): cleaning

Rows whose path is gone, while the folder that held it remains, may be dropped. Rows of a path that cannot be
reached (a drive that is not mounted) are kept.
