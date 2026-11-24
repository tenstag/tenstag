<!-- Generated from tensdataspecs d71a1f0a5f5f by the maintainers' stores.py. Do not edit by hand. -->

# Suggestions

Where no upstream document says how another program should read a store, these are the rules tenstag follows,
and why. Each applies to the store rules it names.

### SUG-037: Hugging Face cache: a sharing program finds the cache as huggingface_hub does

Applies to: hf-hub-cache.md HFC-003.

Decision:

```text
A program that shares the Hugging Face hub cache resolves its directory by huggingface_hub's order (HF_HUB_CACHE,
HUGGINGFACE_HUB_CACHE, $HF_HOME/hub with HF_HOME defaulting to $XDG_CACHE_HOME/huggingface or ~/.cache/huggingface)
and writes only there; it may read the directory LLAMA_CACHE names as an extra place llama.cpp alone may have
written, but does not write to it.
```

Why:

```text
The two readers differ: llama.cpp 7bcbc04fbf47 (hf-cache.cpp get_cache_directory) looks at LLAMA_CACHE first, which
huggingface_hub (constants.py, 0.36.2 and 2.4.0) does not read. No document says which order a third program should
follow.
```

### SUG-038: Hugging Face cache: a writer writes what huggingface_hub writes

Applies to: hf-hub-cache.md HFC-007.

Decision:

```text
A program that writes into the Hugging Face hub cache writes blobs/<blob> through blobs/<blob>.incomplete, holds
.locks/<repository folder>/<blob>.lock while writing the blob and the snapshot entry, makes the snapshot entry a
relative symbolic link (a regular file where links cannot be made), and writes refs/<revision> for a resolved branch
or tag.
```

Why:

```text
The cache has no specification document; it is defined by what huggingface_hub writes (file_download.py, 0.36.2 and
2.4.0), and llama.cpp 7bcbc04fbf47 writes the same final layout but its own partial files (.downloadInProgress,
.etag). No document says which a third writer must follow.
```

### SUG-039: Hugging Face cache: choose a GGUF file by tag as llama.cpp does, online first

Applies to: hf-hub-cache.md HFC-016.

Decision:

```text
A program that accepts <org>/<repo>[:tag] chooses the GGUF file by llama.cpp's rule (HFC-010) over the Hub's listing
when it is online, and over the cached snapshot (HFC-015) only when offline or when the listing fails; with no tag
it does not prefer a file only because it is already cached.
```

Why:

```text
No document defines the meaning of org/repo:tag outside llama.cpp, whose download.cpp at 7bcbc04fbf47
(common_download_get_hf_plan) lists the Hub first. huggingface_hub has no tag selection.
```

### SUG-040: llama.cpp's old cache: name flat -hf files from their manifests only

Applies to: llama-cpp-cache.md LCC-005.

Decision:

```text
A reader of llama.cpp's own cache directory names an old -hf file as <owner>/<repo>:<tag> only through a
manifest=<owner>=<repo>=<tag>.json whose ggufFile (or mmprojFile) rfilename gives that file's flat name, and
otherwise lists the file by its name without inventing a repository.
```

Why:

```text
llama.cpp at 7bcbc04fbf47 no longer reads the old layout, and no document says how another program should name its
files. The flat name <owner>_<repo>_<path> cannot be split reliably.
```

### SUG-041: Ollama's store: which layers a reader offers as a GGUF model

Applies to: ollama.md OLM-008.

Decision:

```text
A reader resolves a manifest list to its gguf entry, offers a manifest's model layers as one GGUF model (in manifest
order as a split set) only when the config's model_format is gguf or empty, offers the projector layer as its
projector, checks the GGUF magic of each blob, and lists safetensors models as not GGUF.
```

Why:

```text
Ollama documents no interface for other programs reading its store; its layout is internal. The rule follows what
Ollama v0.40.17 itself does when it loads a model (server/images.go).
```

### SUG-042: LM Studio's folder: what a reader lists

Applies to: lm-studio.md LMS-004.

Decision:

```text
A reader lists GGUF files exactly three levels below the models folder as model <publisher>/<model>, does not assume
that pair is a Hugging Face repository id, treats projector GGUF files as side files, and lists nothing else as
GGUF. A reader that reads no model data recognises projectors by the name mmproj*.gguf only, and leaves the
general.type check to programs that read model data (added 2026-11-22).
```

Why:

```text
LM Studio is not open source; its documentation gives the three-level layout as what it expects, not how it reads,
and says nothing of side files.
```

### SUG-044: GPT4All's folder: what a reader lists

Applies to: gpt4all.md G4A-006.

Decision:

```text
A reader lists each *.gguf file under GPT4All's model folder, at any depth, not starting with 'incomplete', as one
model named by its file name, optionally with the name and quant of the cached models3.json catalogue, and writes
nothing there.
```

Why:

```text
GPT4All documents no interface for other programs reading its folder; the rule follows how GPT4All itself scans it
at v3.10.0 (modellist.cpp processModelDirectory).
```

### SUG-045: ModelScope cache: what a reader lists

Applies to: modelscope-cache.md MSC-007.

Decision:

```text
A reader lists ModelScope repositories from the snapshot layout (one entry per revision folder, or the one
modelscope-hub would pick) and from the older per-repository folders, reading '___' back as '.', each real folder
once; skips partial, temporary, lock and pickle files; and reads GGUF files and model directories inside as for the
Hugging Face cache, with llama.cpp's quant-tag rule.
```

Why:

```text
ModelScope documents no interface for other programs reading its cache, and gives models no quant tags.
```

### SUG-046: Jan: what a reader lists

Applies to: jan.md JAN-007.

Decision:

```text
A reader lists a Jan model per model.yml under <data folder>/llamacpp/models/ at any depth, takes the GGUF file from
model_path (relative to the data folder unless absolute) and the projector from mmproj_path, treats a folder without
model.yml as unfinished, skips .tmp and .url files, and names models from model.yml or GGUF metadata, not from the
generic file name model.gguf.
```

Why:

```text
Jan documents no interface for other programs reading its data folder.
```

### SUG-047: Docker Model Runner: what a reader lists

Applies to: docker-model-runner.md DMR-006.

Decision:

```text
A reader takes a store only when layout.json says 1.0.0, lists one model per models.json entry named by its tags,
uses that model's GGUF layers in manifest order as the model and the mmproj layer as its projector, skips
.incomplete and .tmp-* files and bundles/, and writes nothing.
```

Why:

```text
Docker Model Runner documents no interface for other programs reading its store.
```

### SUG-048: RamaLama: what a reader lists

Applies to: ramalama.md RML-005.

Decision:

```text
A reader lists a RamaLama model per refs/<tag>.json under <store>/store/, named
<transport>://<organisation>/<name>:<tag> as RamaLama lists it, takes the snapshot files of type gguf as the model
and the mmproj file as its projector, treats a model with missing snapshot files as partial, reads old text ref
files in place, and writes nothing.
```

Why:

```text
RamaLama documents no interface for other programs reading its store.
```
