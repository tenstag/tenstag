# Listing models

Status: stable since 2026-11-23 (tenstag-rust 0.7.0). A change that changes behaviour is a new rule, never a silent
change (README.md, Status).

What models each location holds, and the *entry* each becomes: its id, the path a reader opens, its format, and the
files that make it up. Where a store's layout is written down in [stores/](stores/README.md), this document says
which of its rules are followed and decides the names; the store document decides the layout.

An implementation never opens a model to list it. It reads names, sizes, links, and the stores' own bookkeeping
(manifests, refs, settings, a safetensors index's list of shards); the one exception is the first four bytes of an
Ollama blob (LST-008).

Test vectors: [`test-vectors/listing.json`](test-vectors/listing.json), which also holds the names of names.md.

## Entries

### LST-001 (MUST): what an entry has

| field | what |
|---|---|
| id | its name, unique among the entries (LST-015) |
| path | what a reader opens: a model file (a split set's first part), or a model folder |
| format | `gguf`, `hf-directory`, `safetensors`, `checkpoint`, `diffusers`, `adapter`, or `other` (LST-018) |
| quant | the quant tag its name or store gives (`Q4_K_M`), upper case, or empty |
| bytes | the size of its weights (LST-018) |
| location | the location it was found in |
| hub | for the Hugging Face cache layout: repository, commit, the refs pointing at the commit (`main` first, then by name), and the file in the repository (empty for a folder) |
| parts | the parts in order of a split GGUF model whose files carry no part names (Ollama's, Docker's and RamaLama's blobs); empty otherwise |
| note | what an `other` entry is |

Names are compared and sorted by their bytes (UTF-8), and every folder is read in that order, so every
implementation lists the same entries in the same order.

## Folders of your own and caches (`directory`)

### LST-002 (MUST): the walk

A `directory` location is read folder by folder from its root (configuration.md CFG-004 for depth):
1. A folder named `models--<…>` holding a `snapshots` folder is a Hugging Face cache repository (LST-005), and is
   not walked further.
2. A model folder (LST-003) is one entry, and nothing in it is listed or walked.
3. Otherwise its contents are read, when the folder is less than `depth` parts below the root:
   - names starting with `.` are skipped;
   - a sub-folder is walked, unless it is software: named `node_modules`, `__pycache__` or `site-packages`, or
     holding `pyvenv.cfg` (a Python environment);
   - a `.gguf` file is an entry by LST-006, its id its path below the root without `.gguf`, unless a llama.cpp
     manifest names it (LST-014);
   - any other file is an entry when LST-004 takes it, its id its path below the root.

Links are followed. Each real folder (links resolved) is read once, so a link cannot make a walk loop.

### LST-003 (MUST): model folders

A folder's kind is given by the first of these that it holds directly:
1. `model_index.json`: a diffusers pipeline (`diffusers`). Its bytes are those of the `*.safetensors` and `*.bin`
   files directly in it and directly in each of its sub-folders not starting with `.`.
2. `config.json`, with weights: a model folder (`hf-directory`). The weights are those an index names, every one
   present (the first of `model.safetensors.index.json` and `pytorch_model.bin.index.json`, by its `weight_map`'s
   values; an index that cannot be read means no weights); with no index, the `*.safetensors` and
   `pytorch_model*.bin` files directly in it (stores/hf-hub-cache.md HFC-011). Its bytes are those files'.
3. `adapter_config.json`, and no `config.json`: an adapter (`adapter`). Its bytes are the `adapter_model*` files'.

A pipeline or an adapter with no bytes is not an entry. The rule is tenstag's own: one folder has
one kind, so one set of files and one identity, wherever it is found.

### LST-004 (MUST): single files

A file is a single-file model when its name ends (in any letter case) in:
- `.safetensors` or `.sft`: `safetensors`;
- `.ckpt`: `checkpoint` (a Python pickle: listed, never opened).

In a walked `directory`, it is listed when its bytes are at least the location's `min_size` (1 MiB, 1,048,576 bytes,
by default; 0 lists every size). `.pt`, `.pth`, `.pt2` and `.bin` files are not listed there: they are as often
training state or caches as models. A safetensors set split as `<base>-NNNNN-of-MMMMM.safetensors` (five digits
each, `NNNNN` from 1 to `MMMMM`) is one entry, by its first part; its bytes are all its parts' (0 when one is
missing, so a set with a part missing is under any `min_size` but 0).

### LST-005 (MUST): Hugging Face cache repositories

A folder `models--<org>--<name>` is the repository `<org>/<name>` (`--` read as `/`), laid out as
stores/hf-hub-cache.md HFC-004 to HFC-006 say. Its refs are the files under `refs/` (a ref may hold `/`), each holding a
commit; they are ordered `main` first, then by name. Every snapshot is listed (not only the one a name without a
revision reaches): first the commits the refs point at, in the refs' order, then every other folder in `snapshots/`,
by name; each once.

A snapshot is reached as `at`: empty when `main` points at it, `@<ref>` for the first ref that does, else
`@<commit>`. Its files are every file below it, links followed, sorted, without names ending in `.incomplete`,
`.downloadInProgress`, `.etag` or `.lock` (HFC-006). Its entries:
- when the snapshot is a model folder (LST-003): the folder, id `<org>/<name><at>`;
- unless it is a pipeline, each GGUF model file in it (LST-006), id `<org>/<name>:<QUANT><at>`; with no quant tag, or
  when an earlier entry of the repository has that id already, `<org>/<name>/<file><at>` (`<file>` its path in the
  snapshot);
- when it is no model folder, each single file (LST-004 endings, any size: it was fetched by name, HFC-019), id
  `<org>/<name>/<file><at>`.

An entry's `hub` is the repository, the commit, the refs pointing at the commit, and the file (empty for the
folder). GGUF entries come before the folder's, each in file order.

### LST-006 (MUST): GGUF files

From a GGUF file's name (stores/hf-hub-cache.md HFC-010):
- a *split* file ends in `-NNNNN-of-MMMMM.gguf` (five digits each, `of` in any case); its *prefix* is the name
  without that, and part `i` is `<prefix>-<i, five digits>-of-<MMMMM>.gguf`;
- the *quant tag* is the last run of letters, digits and `_` after a `-` or `.` at the end of the prefix (without
  `.gguf`), in upper case; none when there is no such run.

A GGUF file is an entry when it is a model (its name holds neither `imatrix` nor `mmproj`, `mtp-`, `dflash-`,
`eagle3-`, `dspark-`, the side files of HFC-010), it is its model's first part, and every part is present with more
than 0 bytes in all; its bytes are its parts'.

### LST-014 (MUST): llama.cpp's old flat files

In a walked `directory` folder, a file `manifest=<owner>=<repo>=<tag>.json` whose JSON `ggufFile.rfilename` is `<p>`
names the file `<owner>_<repo>_<p with every / and \ made _>` in the same folder, when it exists: that GGUF file's id
is `<owner>/<repo>:<tag>` (stores/llama-cpp-cache.md LCC-003 to LCC-005, SUG-040). A flat file no manifest
names keeps its own name as its id.

## Other programs' stores

### LST-007 (MUST): LM Studio (`lmstudio`)

GGUF files exactly three levels below the folder, `<publisher>/<model>/<file>.gguf`, that are entries by LST-006 and
whose name does not start with `mmproj` (any case), id `<publisher>/<model>/<file>` without `.gguf`
(stores/lm-studio.md LMS-003, LMS-004, SUG-042). Nothing else.

### LST-008 (MUST): Ollama (`ollama`)

As stores/ollama.md OLM-002 to OLM-008 (SUG-041) say:
- Names are the files four levels below `manifests-v2/` (read first) and `manifests/`: `<host>/<namespace>/<model>/<tag>`,
  `%3A` in a host read as `:`, and `ollama.com` read as `registry.ollama.ai`. A name already listed (ignoring case)
  is not listed again.
- The id leaves out the defaults: `ollama:<model>:<tag>` for `registry.ollama.ai` and `library`;
  `ollama:<namespace>/<model>:<tag>` for another namespace there; `ollama:<host>/<namespace>/<model>:<tag>`
  otherwise.
- A blob is `blobs/sha256-<64 lowercase hex>` for the digest `sha256:<hex>`, when present.
- A manifest of media type `application/vnd.ollama.manifest.list.v2+json` is replaced by its entry of `format`
  `gguf` whose blob is present, else its first entry whose blob is present: the manifest in that blob, with the list
  entry's `format` as its `format` when it has none of its own.
- The format is the config blob's `model_format`, else the manifest's `format`, else empty; the quant is the config
  blob's `file_type`, or empty.
- Format `gguf` or empty: the `application/vnd.ollama.image.model` layers, in order, are the model; every one must
  be present and start with the four bytes `GGUF`, else there is no entry. Path the first; parts all when more
  than one; bytes theirs.
- Any other format: one `other` entry, path the `blobs` folder, bytes those of the
  `application/vnd.ollama.image.tensor` layers whose blobs are present (missing ones count nothing), note `an Ollama <format> model, not a GGUF file`.

### LST-009 (MUST): GPT4All (`gpt4all`)

Every file ending `.gguf` whose name does not start with `incomplete`, at any level within the depth, is one entry:
id its path below the folder without `.gguf`, quant from its name (LST-006), bytes its size. `.rmodel` files hold an
API key and are never opened (stores/gpt4all.md G4A-003 to G4A-006, SUG-044). Each real folder is read once.

### LST-010 (MUST): ModelScope (`modelscope`)

As stores/modelscope-cache.md MSC-002 to MSC-007 (SUG-045) say, folders starting with `.` skipped:
- `models/<owner>--<name>/snapshots/<revision>/`, each revision; `at` is empty for `master`, else `@<revision>`;
- then `models/<owner>/<name>/` and `hub/models/<owner>/<name>/` (an `<owner>` not holding `--`), `___` in a name
  read as `.`, `at` empty.

Each real folder is read once. A folder's entries are read as a Hugging Face snapshot's (LST-005, the GGUF and folder
entries; no single files), with ids `modelscope:<owner>/<name>:<QUANT><at>`, `modelscope:<owner>/<name>/<file><at>`
and `modelscope:<owner>/<name><at>`. The earliest layout, `<root>/<owner>/<name>`, is not read: any folder two levels
down would match it.

### LST-011 (MUST): Jan (`jan`)

Below `llamacpp/models/`, a folder holding `model.yml`, within the depth, is one model and is not walked further;
folders starting with `.` are skipped, and each real folder is read once. Its `model_path` (a top-level scalar
`model_path: <value>`, plain or quoted, read as LST-019 says) is the GGUF file, relative to the data folder or
absolute; when it is no file there is no entry. Id `jan:<folder path below llamacpp/models>`, quant from that path
read as a GGUF name, bytes the file's (stores/jan.md JAN-003 to JAN-007, SUG-046).

### LST-012 (MUST): Docker Model Runner (`docker`)

Only a store whose `layout.json` says `"version": "1.0.0"`. For each model in `models.json`'s `models`, its `id`
`<algorithm>:<hex>` names `manifests/<algorithm>/<hex>`; its layers' digests name `blobs/<algorithm>/<hex>`. A model
with any layer missing is not listed. The GGUF layers (media types `application/vnd.docker.ai.gguf.v3` and
`application/vnd.cncf.model.weight.v1.gguf`), in order, are the model. One entry per tag, `docker:<tag>`: path the
first GGUF layer (parts all when more than one), bytes theirs, quant empty; with no GGUF layer, an `other` entry with
path the `blobs` folder (stores/docker-model-runner.md DMR-002 to DMR-006, SUG-047).

### LST-013 (MUST): RamaLama (`ramalama`)

Under `store/<transport>/`, a model folder is one holding `refs`, `blobs` and `snapshots`, at `<name>` or
`<organisation>/<name>` (folders starting with `.` skipped). Each file in `refs/` is a tag, its name without
`.json`; when a tag has both a `.json` file and a text file, the `.json` file is read. A JSON ref gives the snapshot
(`hash`) and its files (`files`: `name`, and `type` `gguf` for the model's); a text ref gives the snapshot on its
first line and a file per line after, the model's being those ending `.gguf` not starting `mmproj`. A file missing
from `snapshots/<snapshot>/` means no entry. Id `<transport>://<name or organisation/name>:<tag>`; path the first
model file, parts all when more than one, quant from its name; with no model file, an `other` entry with path the
snapshot folder (stores/ramalama.md RML-002 to RML-005, SUG-048).

## Across locations

### LST-015 (MUST): one entry per file, one id per entry

Locations are read in order (configuration.md CFG-006). An entry whose path (links resolved) an earlier location
already gave is left out, except `other` entries; within one location every entry is kept (a store may give one file
several names). An entry whose id an earlier entry has, ignoring ASCII case, gets the id `<location path>:<id>`.

### LST-016 (MUST): a path given directly

A path a program gives (names.md NAM-001 step 1) is taken whatever its size or location:
- a folder: by LST-003, else as an `hf-directory` with the bytes of its weights;
- a `.gguf` file: `gguf`, id the path without `.gguf`, quant from its name, bytes its parts' (0 when a part is
  missing);
- a file LST-004 takes, or ending `.pt`, `.pth`, `.pt2` or `.bin`: `checkpoint` for those, id the path;
- anything else: not a model.

### LST-017 (MUST): the files of an entry

An entry's files are, from names and listings only:

| format | files |
|---|---|
| `gguf` | its parts, in order (`parts`, else the split names of LST-006), or the file |
| `hf-directory`, `adapter` | the regular files directly in the folder, sorted |
| `diffusers` | the regular files directly in the folder, then those directly in each sub-folder not starting with `.`, each folder's sorted, the folders sorted |
| `safetensors` | its split set's parts, in order, or the file |
| `checkpoint` | the file |
| `other` | none |

These are the files fingerprint.md TFP-007 takes the members from.

### LST-018 (MUST): formats

| format | what `path` is |
|---|---|
| `gguf` | a GGUF file, or a split set's first part |
| `hf-directory` | a Hugging Face model folder: `config.json` and its weights |
| `safetensors` | a single safetensors file, or a split set's first part |
| `checkpoint` | a single PyTorch checkpoint, a Python pickle |
| `diffusers` | a diffusers pipeline folder |
| `adapter` | an adapter folder as PEFT writes it |
| `other` | a model a store holds in another form (`note` says what) |

A format says how a model is stored, not what it is for: a GGUF file may be a language model, an image model's
quantised parts, or a text encoder. Implementations do not guess.

### LST-019 (MUST): Jan's scalars

Jan writes `model.yml` as a flat mapping of scalars. A key is read from a line that starts with `<key>:` (at the
start of the line). Its value, trimmed: in `'…'`, the text inside with `''` read as `'`; in `"…"`, the text inside
with `\\` and `\"` read as `\` and `"` (any other escape: no value); otherwise the text up to ` #`, trimmed, when it is
not empty and does not start with `|`, `>`, `[`, `{`, `&`, `*` or `!` (no value then).
