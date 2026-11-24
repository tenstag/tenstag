<!-- Generated from tensdataspecs d71a1f0a5f5f by the maintainers' stores.py. Do not edit by hand. -->

# RamaLama's model store

Rules RML-nnn. Formats: gguf, safetensors. Certainty: verified-source.

```text
Where RamaLama (containers/ramalama) keeps models it pulls from Hugging Face, ModelScope, Ollama and URLs. Added
2026-11-23. Read in RamaLama v0.26.0 (ramalama/config.py, common.py, path_utils.py, model_store/global_store.py,
store.py, reffile.py, constants.py, transports/base.py, transports/url.py, transports/huggingface.py). Read, not
run. Models pulled from OCI registries are kept as images in Podman's or Docker's own storage, not in this store,
and are not described.
```

## Sources

- `ramalama`: [RamaLama source at release v0.26.0](https://github.com/containers/ramalama/tree/066e9cc7bbd6229abbe9e3b02b6b7f05151719df) (v0.26.0 = 066e9cc7bbd6 (2026-11-04), read 2026-11-23), reference-implementation

## Rules

### RML-001

Level IMPL, source `ramalama`, verified-source.

```text
The store folder (config.py): the store option, set by --store, by RAMALAMA_STORE (environment variables
RAMALAMA_<KEY> set option <key>), or by store = "..." in the [ramalama] table of a ramalama.conf file; else
/var/lib/ramalama when running as root, else $XDG_DATA_HOME/ramalama or ~/.local/share/ramalama. The default does
not depend on the system: on macOS and Windows it is also ~/.local/share/ramalama. ramalama.conf is read from
RAMALAMA_CONFIG when that file exists, else from each of <python prefix>/share/ramalama, <python
prefix>/local/share/ramalama, then on Unix /etc/ramalama, $XDG_DATA_HOME/ramalama and $XDG_CONFIG_HOME/ramalama (on
Windows %LOCALAPPDATA%\ramalama and %APPDATA%\ramalama), each followed by its ramalama.conf.d/*.conf, read in that
order into one table.
```

### RML-002

Level IMPL, source `ramalama`, verified-source.

```text
The layout (model_store): models are under <store folder>/store/<transport>/<organisation>/<name>/, where
<transport> is huggingface, modelscope, ollama, or the scheme of a URL (file, http, https); the name is split at its
last '/' into organisation and name, the organisation being the name itself when there is none. Each model folder
has blobs/, refs/ and snapshots/: blobs/<hash> are the files, named by their hash with ':' written '-' (for example
sha256-<hex>); snapshots/<snapshot hash>/<file name> link to the blobs (a hard link, else a symbolic link, else a
copy; path_utils.create_file_link); refs/<tag>.json names a tag's snapshot. The tag is the part after the last ':'
of the name, default latest.
```

### RML-003

Level IMPL, source `ramalama`, verified-source.

```text
A ref file (reffile.py RefJSONFile) is JSON with version (v1.0.1 at this release), hash (the snapshot) and files,
each {hash, name, type}, type one of gguf, safetensor, mmproj, chat_template, other. A model's GGUF files are the
entries of type gguf (several for a split model), its projector the mmproj entry. An older ref file, refs/<tag>
without .json (a text file: the snapshot hash, then one file per line), is converted to the JSON form when RamaLama
next reads it.
```

### RML-004

Level IMPL, source `ramalama`, verified-source.

```text
Downloads in progress: blobs/<hash>.partial; a file named in a ref file is not complete while its snapshot entry is
missing (global_store.py list_models marks such files partial). The folder <store folder>/repos/ is a working folder
for the Hugging Face and ModelScope command-line tools, not part of the store.
```

### RML-005

Level SHOULD, source `ramalama`, verified-source, suggestion SUG-048 (suggestions.md).

```text
Suggestion SUG-048. A reader lists a RamaLama model for each refs/<tag>.json under <store folder>/store/ (a folder
that has refs/, blobs/ and snapshots/), named as RamaLama lists it, <transport>://<organisation>/<name>:<tag>
(file:/// for the file transport), and takes as the model the snapshot files whose ref entries have type gguf, with
the mmproj entry as its projector. A model whose files are not all in its snapshot is partial and not listed as
usable. A reader reads refs/<tag> files without .json in place and writes nothing in the store.
```

### RML-006

Level IMPL, source `ramalama`, verified-source.

```text
Blob names are not reliable digests (added 2026-11-23). Every blob is named sha256-<64 hex>, but the hex is not
always the SHA-256 of the blob's bytes (transports/url.py, hf_style_repo_base.py, transports/ollama.py,
transports/modelscope.py, common.py generate_sha256). It is a content hash for a Hugging Face file stored in LFS
(its oid), the first GGUF file and the projector of a Hugging Face GGUF repository (the manifest's blobId), Ollama
layers (their digests) and ModelScope files (the listed sha256), checked after download where should_verify_checksum
is set. It is the SHA-256 of a name, not of the bytes, for the second and later parts of a split GGUF set, models
from URLs and local files, config.json, generation_config.json, tokenizer_config.json, a safetensors index file and
Hugging Face files kept in git; those are not checked. Nothing in the store tells the two kinds apart. A reader does
not take a RamaLama blob name as the file's SHA-256.
```

## Open questions

### RML-Q1

Status: open. Impact: old stores.

```text
Layouts of RamaLama releases before the blobs/refs/snapshots store (a per-transport folder tree is believed) were
not read. Not run.
```
