<!-- Generated from tensdataspecs d71a1f0a5f5f by the maintainers' stores.py. Do not edit by hand. -->

# Hugging Face Hub cache and downloads

Rules HFC-nnn. Formats: gguf, safetensors, tokenizer-hf. Certainty: verified-source.

```text
Where huggingface_hub, transformers and llama.cpp keep files downloaded from the Hugging Face Hub, how that cache is
laid out on disk, how a file and its identity are found on the Hub, and how llama.cpp chooses a GGUF file by quant
tag. This is not a file format: what is inside the files is not described here. Added 2026-11-22. The cache belongs
to huggingface_hub (its layout and environment variables); llama.cpp writes the same layout with a few differences,
listed as IMPL rules. Read in huggingface_hub 0.36.2 (constants.py, file_download.py, utils/_auth.py; 2.4.0 was
compared on every point below and agrees) and in llama.cpp 7bcbc04fbf47 (common/hf-cache.cpp, common/download.cpp,
conversion/base.py, gguf-py/gguf/vocab.py). Read, not run.
```

## Sources

- `hf-hub`: [huggingface_hub constants.py, file_download.py, utils/_auth.py (the cache's owner)](https://pypi.org/project/huggingface-hub/0.36.2/) (0.36.2 (PyPI wheel in the check environment), read 2026-11-22; 2.4.0 compared the same day), reference-implementation
- `llama-cpp`: [llama.cpp common/hf-cache.cpp, common/download.cpp, conversion/base.py, gguf-py/gguf/vocab.py](https://github.com/ggml-org/llama.cpp/tree/7bcbc04fbf4724eb864d05b706638eb5256cc434/common) (llama.cpp @ 7bcbc04fbf47, read 2026-11-22), reference-implementation
- `diffusers`: [diffusers pipelines/pipeline_utils.py (DiffusionPipeline.download), pipelines/pipeline_loading_utils.py, utils/constants.py](https://github.com/huggingface/diffusers/tree/423ab90580b2847998591669b8326f47b6d14d8b/src/diffusers) (v0.43.0 = 423ab90580b2 (2026-11-12), read 2026-11-23), reference-implementation

## Rules

### HFC-001

Level IMPL, source `hf-hub`, verified-source.

```text
The cache directory, as huggingface_hub computes it (constants.py). HF_HOME is the HF_HOME variable, else
$XDG_CACHE_HOME/huggingface, else ~/.cache/huggingface; ~ and $VAR in it are expanded. The hub cache is
HF_HUB_CACHE, else HUGGINGFACE_HUB_CACHE, else $HF_HOME/hub (also expanded). transformers uses the same constants.
```

### HFC-002

Level IMPL, source `llama-cpp`, verified-source.

```text
llama.cpp's cache directory (hf-cache.cpp get_cache_directory) is the first of these that is set and not empty:
LLAMA_CACHE, HF_HUB_CACHE, HUGGINGFACE_HUB_CACHE, $HF_HOME/hub, $XDG_CACHE_HOME/huggingface/hub,
$HOME/.cache/huggingface/hub, then the passwd entry's home + /.cache/huggingface/hub. It differs from HFC-001 in
LLAMA_CACHE, which only llama.cpp reads, so with LLAMA_CACHE set llama.cpp writes where huggingface_hub does not
look; without it the two agree.
```

### HFC-003

Level SHOULD, source `hf-hub`, verified-source, suggestion SUG-037 (suggestions.md).

```text
Suggestion SUG-037. A program that shares the cache with huggingface_hub, transformers and llama.cpp finds it by
HFC-001 (the cache's owner) and writes only there. It may also read the directory LLAMA_CACHE names, as a place
llama.cpp alone may have written, but does not write there.
```

### HFC-004

Level MUST, source `hf-hub`, verified-source.

```text
The layout (huggingface_hub file_download.py; llama.cpp hf-cache.cpp writes the same names). A repository's folder
in the hub cache is '<type>s--' followed by the repository id with each '/' replaced by '--': models--<org>--<name>
for a model. Inside it: refs/<revision> is a file holding the commit hash (40 hex, no newline), written when the
revision asked for is not itself a full commit (a branch, a tag, or a short commit, which huggingface_hub records as
refs/<short commit>); blobs/<blob> holds each file's content once; snapshots/<commit>/<path> is the file as it is in
that commit, normally a relative symbolic link to ../../blobs/<blob> (one more ../ for each directory level in
<path>). The blob name is the file's identity on the Hub (HFC-008): the sha256 of the content for an LFS file, the
git blob id for a file kept in git. Locks are .locks/<repository folder>/<blob>.lock at the top of the hub cache.
```

### HFC-005

Level MUST, source `hf-hub`, verified-source.

```text
Reading a snapshot. A snapshot entry may be a relative symbolic link, an absolute one (huggingface_hub falls back to
an absolute path when no relative one exists, for example across volumes), or a regular file: where symbolic links
cannot be made both programs put the content itself there (huggingface_hub moves a new blob there, or copies an
existing one; llama.cpp moves its file there, "degraded mode"). A reader takes the content the entry resolves to in
every case and does not require a blob to exist.
```

### HFC-006

Level IMPL, source `llama-cpp`, verified-source.

```text
Downloads in progress and side files. huggingface_hub writes blobs/<blob>.incomplete and renames it to blobs/<blob>
when the size matches (it resumes a partial file with a Range request unless forced). llama.cpp writes
<target>.downloadInProgress, keeps the server's ETag in <target>.etag beside the file it downloads, and renames to
<target> when done; its target is blobs/<oid> when the tree listing gave an oid, else the snapshot path itself. Both
take the lock of HFC-004: huggingface_hub around the download and the link, llama.cpp around making the snapshot
entry (its source says the lock file is shared with huggingface_hub). Each ignores the other's partial files. A
reader ignores names ending in .incomplete, .downloadInProgress, .etag and .lock.
```

### HFC-007

Level SHOULD, source `hf-hub`, verified-source, suggestion SUG-038 (suggestions.md).

```text
Suggestion SUG-038. A program that writes into the cache writes what huggingface_hub writes, so that every reader of
HFC-004 and HFC-005 can use the result: the blob as blobs/<blob> with the partial file blobs/<blob>.incomplete
renamed when complete, the lock of HFC-004 held while it writes the blob and the snapshot entry, the snapshot entry
as a relative symbolic link (a regular file where links cannot be made), and refs/<revision> when it resolved a
branch or tag.
```

### HFC-008

Level IMPL, source `hf-hub`, verified-source.

```text
Finding a file and its identity on the Hub. Endpoint: HF_ENDPOINT, else https://huggingface.co, trailing '/'
removed. huggingface_hub (get_hf_file_metadata) sends HEAD <endpoint>/<repo>/resolve/<revision>/<path> with
Accept-Encoding: identity, follows a redirect only when its Location is relative (follow_relative_redirects; a file
kept in git answers 307 to /api/resolve-cache/..., an LFS file answers with an absolute Location on another host,
which is not followed), and reads from the last answer: the commit from X-Repo-Commit; the blob name from
X-Linked-Etag, else ETag, with a leading W/ and the surrounding quotes removed (_normalize_etag, which strips the
characters 'W' and '/' from the left, then '"' from both ends); the size from X-Linked-Size, else Content-Length.
The Content-Length of a 307 answer is the size of its own body, not the file's (observed 2026-11-22: 270 bytes for a
726-byte config.json, whose 307 also carried X-Linked-Size 726 and whose followed 200 answer had Content-Length
726). llama.cpp instead lists the repository: GET <endpoint>/api/models/<repo>/refs (the branches' name and
targetCommit), then GET <endpoint>/api/models/<repo>/tree/<commit>?recursive=true, taking for each entry of type
'file' its path and its lfs.oid when present, else its oid (each 40 or 64 hex, others skipped), and downloads
<endpoint>/<repo>/resolve/<commit>/<path>. Offline: HF_HUB_OFFLINE, else TRANSFORMERS_OFFLINE, whose value is true
when it is 1, ON, YES or TRUE in any case (constants.py _is_true). Token (utils/_auth.py): HF_TOKEN, else
HUGGING_FACE_HUB_TOKEN, else the file at HF_TOKEN_PATH (default $HF_HOME/token); in Google Colab its secret store is
asked first. The token goes as Authorization: Bearer on the requests to the endpoint (HEAD, the API listings, and a
relative redirect on the same host); huggingface_hub removes it before downloading from a Location whose host
differs from the request's (file_download.py, the bytes of an LFS file).
```

### HFC-009

Level MAY, source `hf-hub`, verified-empirical.

```text
Checking a file. Neither program checks content against its identity at the pins: huggingface_hub compares the
downloaded size with the expected size (EnvironmentError otherwise); llama.cpp checks a sha256 only for Docker / OCI
digests, not for Hub files. A reader may check an LFS file, whose blob name is the sha256 of its content. For a file
kept in git the blob name is the git blob id: the sha1 of 'blob ' + the size in decimal + a zero byte + the content.
Observed 2026-11-22 on Qwen/Qwen3-0.6B config.json at c1899de289a0: X-Linked-Etag and the followed answer's ETag
were f5c3703b78ae2a478ae15b247e9f855e0ce2107b, the git blob id of the 726 bytes, which equal the copy in the model
store. The same holds for the git and LFS files of five more repositories.
```

### HFC-010

Level IMPL, source `llama-cpp`, verified-source.

```text
Choosing a GGUF file by quant tag, as llama.cpp's -hf <org>/<repo>[:tag] does (download.cpp find_best_model) over
the files of the tree listing in the order the Hub returns them. A model file is one whose path ends in .gguf and
whose file name contains neither 'imatrix' nor a sidecar keyword ('mmproj', 'mtp-', 'dflash-', 'eagle3-',
'dspark-'). The tags tried are the given one, or with none Q4_K_M then Q8_0; for each tag in turn the first model
file whose path matches (^|[-./])<tag>[.-], ignoring case, is chosen, except that of a split set
(<prefix>-NNNNN-of-MMMMM.gguf, five digits each, ignoring case) only the part 00001 can be chosen. When no tag was
given and none matched, the first model file (again only a first part of a split set) is chosen; when a tag was
given and none matched, nothing is. The other parts of a split set are then fetched by their numbered names. The tag
of a file name (get_gguf_split_info, used to group and list files): remove '.gguf', then a split suffix
-NNNNN-of-MMMMM (five digits each, ignoring case), then take the last match of [-.]([A-Z0-9_]+)$ ignoring case and
upper-case it; no match, no tag. Giving that tag back as :<tag> picks the same file again when it is the first file
in the listing that HFC-010's pattern matches.
```

### HFC-011

Level IMPL, source `llama-cpp`, verified-source.

```text
The files of a model directory that llama.cpp's converter reads, from the transcriptions of tensdataspecs' gguf
format notes (not public yet) (GGUF-037 to GGUF-039, GGUF-058 algorithms.write_vocab) and gguf-py metadata.py
(corrected 2026-11-22: an earlier version said generation_config.json was not read). Always: config.json; the
weights, <prefix>*.safetensors with <prefix>.safetensors.index.json when present (else pytorch_model*.bin and its
index); README.md, the model card (Metadata.load_model_card, for general.* metadata); generation_config.json
(Metadata.load_hf_parameters, for the general.sampling.* keys of GGUF-038). Tokenizer, as a repository has them:
tokenizer.json, tokenizer_config.json, special_tokens_map.json, added_tokens.json, vocab.json, merges.txt,
tokenizer.model, spiece.model (T5), sentencepiece.bpe.model, tokenizer.jsonl (PLaMo), rwkv_vocab_v20230424.txt
(RWKV), and for a Mistral-format directory params.json, tekken.json or tokenizer.model.v<N>. Chat templates:
chat_template.jinja, else chat_template.json, and the files of additional_chat_templates/. Some classes read more,
named in their rows (gguf_class_parameters): the sentence-transformers modules.json and <pooling path>/config.json
(TextModel._try_set_pooling_type), and side files listed in gguf_generated_tensors (for example 1_Dense/). The
tiktoken writers that run a repository's own code are not transcribed (GGUF-058), so their files are not listed.
Files outside these (training logs, evaluation results) are not read.
```

### HFC-012

Level IMPL, source `hf-hub`, verified-empirical.

```text
The tree listing comes in pages (added 2026-11-22). GET <endpoint>/api/models/<repo>/tree/<revision>?recursive=true
answers a JSON array; when more entries remain it carries Link: <next url>; rel="next", the next URL holding a
cursor parameter. huggingface_hub follows every rel="next" (utils/_pagination.py paginate, used by list_repo_tree).
llama.cpp reads the first answer only (hf-cache.cpp get_repo_files), so for a repository with more files than one
page holds it does not see the rest, and HFC-010 chooses among the first page only. The default page size is not
documented; observed 2026-11-22: 271 entries of bigscience/bloom came in one page, and with limit=50 the listing
paged by 50 with no entry repeated. A reader that needs every file follows rel="next".
```

### HFC-013

Level IMPL, source `hf-hub`, verified-empirical.

```text
Revisions (added 2026-11-22). huggingface_hub puts the revision as given (default 'main') into the resolve URL and
the Hub resolves it: a branch, a tag, a full commit or a short commit (observed 2026-11-22: 'main', the 40-hex
commit and its first 7 characters all answered X-Repo-Commit c1899de289a04d12100db370d81485cdf75e47ca for
Qwen/Qwen3-0.6B). Offline, huggingface_hub takes a revision matching ^[0-9a-f]{40}$ as a commit and looks anything
else up in refs/<revision>. llama.cpp's -hf names no revision: its refs request takes the branch 'main', else the
first branch listed, and writes refs/<branch>; tags are not used.
```

### HFC-014

Level IMPL, source `hf-hub`, verified-source.

```text
Repository ids (added 2026-11-22). huggingface_hub (utils/_validators.py validate_repo_id): 'name' or
'namespace/name', at most one '/', characters [A-Za-z0-9_.-], the name 1 to 96 characters starting and ending at a
word boundary, no '--' or '..', not ending in '.git'. llama.cpp (hf-cache.cpp is_valid_repo_id): 1 to 256
characters, exactly one '/', base characters [A-Za-z0-9_], and '/', '.' and '-' only between base characters.
Neither accepts a leading hf.co/ or huggingface.co/; that is another program's way of naming a repository.
```

### HFC-015

Level IMPL, source `llama-cpp`, verified-source.

```text
Which snapshot a reader of the cache takes for a repository named without a revision (added 2026-11-22).
huggingface_hub (try_to_load_from_cache, hf_hub_download offline) takes the revision 'main' and so the snapshot of
refs/main, and finds nothing without it. llama.cpp (hf-cache.cpp get_cached_ref) takes refs/main, else the commit of
the first other regular file directly in refs/ that it meets (directory order, so not defined), and needs that
commit's snapshot to exist; neither looks at modification times. llama.cpp lists the Hub first and uses the cached
snapshot only when it is offline or the listing is empty (download.cpp common_download_get_hf_plan).
```

### HFC-016

Level SHOULD, source `llama-cpp`, verified-source, suggestion SUG-039 (suggestions.md).

```text
Suggestion SUG-039. A program that accepts <org>/<repo>[:tag] chooses the GGUF file as llama.cpp does, so that both
pick the same file: by HFC-010 over the Hub's listing when online, and over the snapshot of HFC-015 only when
offline or when the listing fails; with no tag it does not prefer a file only because it is already cached.
```

### HFC-017

Level IMPL, source `diffusers`, verified-source.

```text
Diffusers pipelines (added 2026-11-23). A pipeline repository has model_index.json at its root: a JSON object whose
_class_name names the pipeline and whose other keys with a list value (["library", "Class"]) name its components,
each a subfolder of that name. DiffusionPipeline.download fetches the repository with snapshot_download into the
cache of HFC-004 (same layout), so a pipeline is a snapshot folder holding model_index.json, and that folder is what
a pipeline is loaded from. It fetches: model_index.json, config.json and scheduler_config.json at the root when
present; for each component folder holding weights, its config.json and the weights of one kind and one variant
(below), with their *.index.json; component folders without weights (scheduler/, tokenizer/, feature_extractor/)
whole; a component's <name>.py when the component is custom code; and the root files chat_template.jinja,
generation_config.json, preprocessor_config.json, processor_config.json, tokenizer.json and tokenizer_config.json.
Files listed in model_index.json's _ignore_files are not fetched.
```

### HFC-018

Level IMPL, source `diffusers`, verified-source.

```text
Weights of a pipeline download (pipeline_loading_utils.py _get_ignore_patterns, variant_compatible_siblings). Weight
files are named diffusion_pytorch_model, model or pytorch_model, with .safetensors, .bin, or for ONNX pipelines
model.onnx and weights.pb, optionally sharded as <prefix>-NNNNN-of-MMMMM. Safetensors are taken when every component
has them (then .bin and .msgpack are not fetched); otherwise .bin; .onnx and .pb only for ONNX pipelines. A variant
(for example fp16) is the files <prefix>.<variant>.<ext> or <prefix>.<variant>-NNNNN-of-MMMMM.<ext> (older
repositories <prefix>-NNNNN-of-MMMMM.<variant>.<ext>); with variant given, each component takes its variant files
when it has them and its plain files otherwise; with none, the plain files. So a cached pipeline may hold one
variant while the repository holds several.
```

### HFC-019

Level IMPL, source `hf-hub`, verified-source.

```text
Single files (added 2026-11-23). Any file of a repository can be fetched alone (huggingface_hub hf_hub_download, and
diffusers' from_single_file for checkpoints such as sd_xl_base_1.0.safetensors at a repository's root); it lands in
the same snapshot folder of HFC-004, which then holds only the files fetched so far. So a snapshot folder may hold a
pipeline, a model directory, single files, or a mix, and a snapshot without model_index.json or config.json at its
root is not a model directory, whatever files it has. How a program names one file of a repository is that program's
choice; no document read here defines a grammar for it (llama.cpp's <repo>:<tag> of HFC-010 names a quant tag, not a
path).
```

### HFC-020

Level IMPL, source `hf-hub`, verified-source.

```text
Blob names as digests (added 2026-11-23). A blob name of 64 hex digits is the SHA-256 of the file's bytes as the Hub
states it (an LFS file's ETag, HFC-009). huggingface_hub does not hash the bytes when it downloads into the cache,
only checks their size (file_download.py http_get), so the name is the Hub's claim, not a checked fact; a corrupted
file keeps its name. A blob name of 40 hex digits is a file kept in git: the git blob id, SHA-1 of 'blob <size>' + a
zero byte + the bytes (HFC-009), not a SHA-256 of anything. A reader takes a blob name as the file's SHA-256 only
when it is 64 hex digits.
```

## Open questions

### HFC-Q1

Status: partially-resolved. Impact: HFC-004 to HFC-007 rest on source and that report.

```text
Partly resolved 2026-11-22. Checked here against the Hub: the git blob id (HFC-009), the 307 answer of a git file
(HFC-008), paging (HFC-012) and short commits (HFC-013). Reported by another program's maintainers (their runs, not
repeated here): files that program wrote to HFC-004 and HFC-007 are found by huggingface_hub 0.36.2 with
local_files_only and scan_cache_dir, files huggingface_hub downloaded are found by it, and llama.cpp's llama-bench
-hf --offline loaded a file from the same cache. Open: neither huggingface_hub nor llama.cpp was run here.
```
