# The fingerprint `tfp1`

Status: stable since 2026-11-23 (tenstag-rust 0.6.0). A change that changes bytes is a new version (README.md, Status).

A model's *identity* is a fingerprint of its contents. A model that is moved, renamed, or copied to another store keeps
its identity, so it keeps its tags. A fingerprint reads at most about 33 MiB of a file, whatever its size: a full
hash of a 40 GB model takes minutes on a hard disk, and a library of them takes hours.

A fingerprint is not a cryptographic commitment to every byte. It reads the whole of a small file, and of a large
one the parts that differ between models (the header, with names, quantisation and tokenizer) and an even sample of
the rest. It catches any change of size, any change in the first 16 MiB or the last 1 MiB, and a change of the
weights in place with a probability that grows with the share of the file changed (see "What it misses"). A program
that needs every byte checked uses a full SHA-256 (tag-store.md TGS-008).

The reference implementation is [`tools/reference.py`](../tools/reference.py); its test vectors are in
[`test-vectors/fingerprint.json`](test-vectors/fingerprint.json).

## Rules

### TFP-001 (MUST): the form of an identity

An identity is the text `tfp1:` followed by 64 lowercase hexadecimal digits, the SHA-256 digest computed below.
The digits alone (without `tfp1:`) name files (tag-store.md).

### TFP-002 (MUST): the constants

| name | value |
|---|---|
| `HEAD` | 16 MiB = 16,777,216 bytes |
| `TAIL` | 1 MiB = 1,048,576 bytes |
| `BLOCK` | 4 KiB = 4,096 bytes |
| `SAMPLES` | 4,096 |
| `WHOLE` | `HEAD` + `TAIL` + `SAMPLES` × `BLOCK` = 33 MiB = 34,603,008 bytes |

### TFP-003 (MUST): a file of at most `WHOLE` bytes

The digest is SHA-256 of, in order:
1. the four ASCII bytes `tfp1`;
2. the file's size in bytes, as an unsigned 64-bit integer, little-endian;
3. every byte of the file.

### TFP-004 (MUST): a larger file

With `size` the file's size:
- `M` = (`size` - `HEAD` - `TAIL`) / `BLOCK`, rounded down: the number of whole blocks between the head and the
  tail. `M` is at least `SAMPLES` whenever `size` is more than `WHOLE`.
- The blocks are numbered 0 to `M` - 1; block `b` is the `BLOCK` bytes at offset `HEAD` + `b` × `BLOCK`.
- They are split into `SAMPLES` runs: run `i` (0 ≤ `i` < `SAMPLES`) is blocks `lo` to `hi` - 1, where
  `lo` = `i` × `M` / `SAMPLES` and `hi` = (`i` + 1) × `M` / `SAMPLES`, both rounded down. Every run has at least
  one block. (Compute `i` × `M` without overflow: it can exceed 64 bits only for files over 2^52 blocks, but an
  implementation must not wrap.)
- From each run, in order of `i`, one block is chosen: `lo` + (`r` mod (`hi` - `lo`)), where `r` is the next output
  of the generator of TFP-005.

The digest is SHA-256 of, in order:
1. the four ASCII bytes `tfp1`;
2. `size` as an unsigned 64-bit integer, little-endian;
3. the first `HEAD` bytes;
4. the `SAMPLES` chosen blocks, in order of `i` (which is the order they appear in the file);
5. the last `TAIL` bytes (offset `size` - `TAIL` to the end).

Everything is hashed in file order, so a file can be read front to back in one pass. The tail may overlap the last
chosen block by less than a block; the overlapping bytes are hashed twice.

### TFP-005 (MUST): the generator

SplitMix64, with its state set to `size` (an unsigned 64-bit integer). Each output, with all arithmetic modulo
2^64:

```text
state = state + 0x9E3779B97F4A7C15
z = state
z = (z XOR (z >> 30)) * 0xBF58476D1CE4E5B9
z = (z XOR (z >> 27)) * 0x94D049BB133111EB
output z XOR (z >> 31)
```

The positions depend only on the size, so the same bytes give the same identity on every machine and in every
language. They are fixed, not secret: tfp1 does not resist someone who builds two files to collide.

### TFP-006 (MUST): reading

- Links are followed; the fingerprint is of the file they lead to.
- When the file's size changes while it is read, or a read returns fewer bytes than the size promised, there is no
  fingerprint: the implementation reports an error and records nothing.
- Implementations may read in any order and in parallel, as long as the bytes are hashed in the order of TFP-003 or
  TFP-004.

### TFP-007 (MUST): a model of several files

A model may be several files: a split GGUF or safetensors set, a model directory (weights, configuration and
tokenizer), a diffusers pipeline, an adapter. Which files make up a model is set by the document of the store it is
in ([stores/](stores/README.md)) and, for a plain folder, by the implementation's rules for that folder; the *members*
are those files, without any whose own name (the last part of its path):
- ends in `.md`, in any letter case;
- starts with `LICENSE` or `LICENCE`, in any letter case;
- starts with `.`.

These change without changing the model (a model card, a licence, `.gitattributes`).

The identity is then:
- with no members, none (the model has no identity and cannot be tagged);
- with one member, that member's fingerprint;
- with more, `tfp1:` and the hexadecimal SHA-256 of, in order:
  1. the eight ASCII bytes `tfp1-set`;
  2. the number of members, an unsigned 64-bit integer, little-endian;
  3. the members' digests (32 bytes each, not hexadecimal), sorted in ascending byte order. A digest that occurs
     twice (two members with the same contents) is included twice.

Paths and file names are not part of a set's identity, so the same model in two stores, whose files are named
differently (the Hugging Face cache, Docker Model Runner's blobs), has the same identity.

## What it misses

The region between `HEAD` and `TAIL` is sampled in `SAMPLES` runs of `s` = `M` / 4096 blocks each (about 10 blocks,
40 KiB, for a 200 MB file; about 2,400 blocks, 10 MiB, for a 40 GB one). For an edit in place that keeps the size:

| edit | chance it is missed |
|---|---|
| any change of size, or in the first 16 MiB or the last 1 MiB | 0 |
| one stretch of at least 2 × `s` blocks | 0: it covers a whole run |
| one stretch of `L` blocks, `L` < `s` | at most 1 - `L` / `s` |
| scattered over 1% of the region | about (1 - 0.01)^4096, less than 10^-17 |
| scattered over 0.1% | about 1.7% |
| scattered over 0.01% | about 66% |

Models are not edited in place in practice: a converted, requantised or fine-tuned model is written as a new file,
and differs everywhere. An edit to a header (names, quantisation, chat template) falls in the first 16 MiB.

## Changes

A later sampling is a new name (`tfp2`), never a change to `tfp1`; records name the version they use.
