# tenstag

tenstag finds the language and image models already on your disk, and lets programs tag them. Tags stay with a
model's contents rather than its path, so moving or renaming a model doesn't lose them. It never downloads
anything.

If you're new here, start with [INTRODUCTION.md](INTRODUCTION.md). It explains why a program might want tenstag,
shows what using it looks like, and how one config file can serve lots of programs.

This repository is the specification. There are two implementations, and they both follow it, so a tag file one
writes, the other can read, and the same model gets the same identity whichever language you use:

| implementation | repository |
|---|---|
| Rust | [tenstag/tenstag-rust](https://github.com/tenstag/tenstag-rust) |
| Python | [tenstag/tenstag-python](https://github.com/tenstag/tenstag-python) |

## What is specified here

| document | rules |
|---|---|
| [specs/fingerprint.md](specs/fingerprint.md) | TFP: the identity `tfp1` |
| [specs/tags.md](specs/tags.md) | TAG: what a tag is, one value per key, matching |
| [specs/tag-store.md](specs/tag-store.md) | TGS: where tags are kept, and how they are read and written |
| [specs/fingerprint-cache.md](specs/fingerprint-cache.md) | TFC: fingerprints already computed, and SHA-256s stores name files by |
| [specs/configuration.md](specs/configuration.md) | CFG: the configuration file, environment variables, the order of locations, programs changing the file |
| [specs/locations.md](specs/locations.md) | LOC: the built-in locations, where other programs keep their models |
| [specs/listing.md](specs/listing.md) | LST: what each location holds, and each model's id, path, format and files |
| [specs/names.md](specs/names.md) | NAM: from a name a person types to a model |
| [specs/stores/](specs/stores/README.md) | HFC, LCC, OLM, LMS, G4A, MSC, JAN, DMR, RML, SUG: where other programs keep their models, one document per store |

The test vectors in `specs/test-vectors/` are generated. `tools/reference.py` is a small reference version of the
fingerprint and tag rules in Python, and writes their vectors; `tools/cases.py` holds the hand-written cases for the
configuration, listing and names documents, with the results each should give. `python3 tools/reference.py check`
and `python3 tools/cases.py check` make sure the vectors still match.

In short:

- **The fingerprint `tfp1`:** a model's identity from its size and a fixed sample of its bytes, so a model of any
  size is identified by reading about 33 MiB of it.
- **Tags:** words and `key=value` pairs, one value per key, and how they are compared and searched.
- **The tag folder:** the files that keep each identity's tags.
- **The fingerprint cache:** how an implementation avoids reading a file again when its path or file identity, its
  size and its modification time are unchanged.
- **Test vectors:** files and their expected fingerprints, and tag files to read and write, which every
  implementation runs in its tests.

How other programs lay out their model stores (the Hugging Face cache, Ollama, LM Studio and so on) is in
[specs/stores/](specs/stores/README.md): one document per store, each checked against that program's own source or
documentation. The model file formats themselves aren't described here.

The documents under `specs/` read more formally than the rest, with numbered MUST rules. That's on purpose: two
implementations have to agree on every byte.

## Status

The formats have been stable since 2026-11-23 (tenstag-rust 0.6.0). Anything that would change the bytes an
implementation reads or writes gets a new format version (`tfp2`, `tenstag-tags/2`), and the old one stays readable.

This is a spare-time project, so things move at the pace I have time for.

## Licence

Copyright 2026 Nick Reynolds (goldnode).

Licensed under either of

- the Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE)), or
- the MIT licence ([LICENSE-MIT](LICENSE-MIT)),

at your option.

Unless you say otherwise, any contribution you submit for inclusion is dual-licensed as above, with no extra terms
or conditions.
