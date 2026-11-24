<!-- Generated from tensdataspecs d71a1f0a5f5f by the maintainers' stores.py. Do not edit by hand. -->

# llama.cpp's own cache directory (and its layout before the Hugging Face cache)

Rules LCC-nnn. Formats: gguf. Certainty: verified-source.

```text
The directory llama.cpp keeps for its own downloads, separate from the Hugging Face hub cache (hf-hub-cache.md), and
the layout its -hf downloads had there until 2026-03-24, when llama.cpp moved them to the Hugging Face cache. A
store of that age may still hold files in the old layout. At the pin the directory still receives --model-url and
Docker downloads. Added 2026-11-22. Read in llama.cpp 7bcbc04fbf47 (common/common.cpp, common/arg.cpp,
common/download.cpp), at 8c7957ca33a4 and its parent (the commit that added the Hugging Face cache, 2026-03-24) and
at 45b455e66fc0 (2026-05-18, which removed the migration). History before 2026-03-10 was not read. Read, not run.
```

## Sources

- `llama-cpp`: [llama.cpp common/common.cpp (fs_get_cache_directory, fs_get_cache_file), common/arg.cpp, common/download.cpp](https://github.com/ggml-org/llama.cpp/tree/7bcbc04fbf4724eb864d05b706638eb5256cc434/common) (llama.cpp @ 7bcbc04fbf47, read 2026-11-22), reference-implementation
- `llama-cpp-old`: [llama.cpp common/download.cpp and common/arg.cpp before the Hugging Face cache; common/hf-cache.cpp migrate_old_cache_to_hf_cache](https://github.com/ggml-org/llama.cpp/commit/8c7957ca33a40cd928146fd3f33a98180e486004) (8c7957ca33a4 (2026-03-24, 'common : add standard Hugging Face cache support (#20775)') and its parent; 45b455e66fc0 (2026-05-18, 'common : remove hf cache migration (#23266)'); read 2026-11-22), reference-implementation

## Rules

### LCC-001

Level IMPL, source `llama-cpp`, verified-source.

```text
The directory (common.cpp fs_get_cache_directory, the same before and at the pin): LLAMA_CACHE when set and not
empty, used as it is; otherwise %LOCALAPPDATA% on Windows (an error when unset), ~/Library/Caches on macOS, else
$XDG_CACHE_HOME or ~/.cache; then the subdirectory llama.cpp. With LLAMA_CACHE set, this directory and llama.cpp's
Hugging Face cache (hf-hub-cache.md HFC-002) are the same path, so its flat files and the hub layout's models--*
folders sit side by side.
```

### LCC-002

Level IMPL, source `llama-cpp`, verified-source.

```text
What the pin still writes there (fs_get_cache_file): a --model-url download, named by the last '/'-separated
component of the URL with any '?query' and '#fragment' removed (arg.cpp get_default_local_path); and a Docker / OCI
model, named <repository with each '/' made '_'>_<tag>.gguf (download.cpp). A partial download is
<file>.downloadInProgress and the server's ETag is kept in <file>.etag, as in the Hugging Face cache
(hf-hub-cache.md HFC-006). Files in this directory carry no repository name of their own.
```

### LCC-003

Level IMPL, source `llama-cpp-old`, verified-source.

```text
The -hf layout before 8c7957ca33a4 (read at its parent; earlier versions not read). Each file of an -hf download was
stored flat as <owner>_<repo>_<path>, every '/' and '\' made '_' (arg.cpp clean_file_name; hf-cache.cpp
make_old_cache_filename at 8c7957ca33a4 rebuilds the same name), with <file>.etag beside it and
<file>.downloadInProgress while downloading. For each repository and tag llama.cpp kept the Hub's manifest answer as
manifest=<owner>=<repo>=<tag>.json ('/' made '='): the JSON of GET <endpoint>v2/<owner>/<repo>/manifests/<tag> with
Accept: application/json and the User-Agent llama-cpp (which the Hub needs to answer ggufFile). The tag was the one
given after ':', else 'latest'. The manifest's ggufFile and mmprojFile objects hold rfilename (the path in the
repository) and lfs.sha256.
```

### LCC-004

Level IMPL, source `llama-cpp-old`, verified-source.

```text
What happened to those files. From 8c7957ca33a4 (2026-03-24), when online, llama.cpp read each manifest=*.json,
matched its ggufFile and mmprojFile against the repository's current file list, moved each flat file that was still
current (same path, and lfs.sha256 equal to the listing's oid) into the Hugging Face cache, deleted the stale ones
and their .etag files, and skipped all of this offline. 45b455e66fc0 (2026-05-18) removed the migration. So a
directory not used online by llama.cpp between those dates keeps the old layout, and llama.cpp at the pin neither
reads nor migrates it. The migration deleted each manifest after handling it; a manifest was kept only when the
repository's file list could not be fetched or the manifest did not parse. So a manifest found today belongs to a
directory that was never migrated (or whose migration failed for that repository).
```

### LCC-005

Level SHOULD, source `llama-cpp-old`, verified-source, suggestion SUG-040 (suggestions.md).

```text
Suggestion SUG-040. A reader that names old -hf files as repository and tag takes the names from the manifests only:
for manifest=<owner>=<repo>=<tag>.json, the file <owner>_<repo>_<ggufFile.rfilename with '/' made '_'> is
<owner>/<repo>:<tag> (and the mmprojFile one its projector), when that file exists. It does not split a flat file
name without a manifest, because owner, repository and path may all contain '_'; such a file, like the files of
LCC-002, is listed by its file name alone. A reader may compare a named file's sha256 with lfs.sha256.
```

## Open questions

### LCC-Q1

Status: open. Impact: very old stores.

```text
Versions of the -hf layout before 2026-03-10 were not read (the history fetched here starts there); manifests or
file names of older llama.cpp releases may differ.
```
