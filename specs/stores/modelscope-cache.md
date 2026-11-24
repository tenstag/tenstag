<!-- Generated from tensdataspecs d71a1f0a5f5f by the maintainers' stores.py. Do not edit by hand. -->

# The ModelScope hub cache

Rules MSC-nnn. Formats: gguf, safetensors. Certainty: verified-source.

```text
Where the ModelScope Python libraries keep downloaded repositories. Added 2026-11-23. ModelScope 1.38 and later
download through the separate package modelscope-hub, which writes a snapshot layout and still reads the older
layout of ModelScope 1.37 and before; both are described. Read in modelscope-hub 0.7.1 (_download.py,
_cache_manager.py, config.py, constants.py), ModelScope v1.40.3 (modelscope/utils/file_utils.py,
modelscope/hub/utils/utils.py) and ModelScope v1.37.1 (modelscope/hub/file_download.py,
modelscope/hub/utils/caching.py, modelscope/utils/file_utils.py). Read, not run. Unlike the Hugging Face cache
(hf-hub-cache.md) there are no blobs or refs: files are stored as plain files under a folder named by the revision
as it was asked for.
```

## Sources

- `ms-hub`: [modelscope-hub 0.7.1 source distribution (PyPI)](https://pypi.org/project/modelscope-hub/0.7.1/) (modelscope_hub-0.7.1.tar.gz, uploaded 2026-11-10, sha256 9210e99f775424dbc253b61d6acc1351a7de03e6b9cca9b75fa2f73b03fae8c2, read 2026-11-23), reference-implementation
- `modelscope`: [ModelScope at v1.40.3 (requires modelscope-hub >= 0.7.0)](https://github.com/modelscope/modelscope/tree/53525f503f795e6d7d941b42c075b48824b497d9) (v1.40.3 = 53525f503f79 (2026-11-09), read 2026-11-23), reference-implementation
- `modelscope-old`: [ModelScope at v1.37.1, the last release before the modelscope-hub layout](https://github.com/modelscope/modelscope/tree/121f4150fa9615882414bf424199e15be09c8ae5) (v1.37.1 = 121f4150fa96, read 2026-11-23), reference-implementation

## Rules

### MSC-001

Level IMPL, source `ms-hub`, verified-source.

```text
The cache root of modelscope-hub (config.py HubConfig.cache_dir, get_cache_root): MODELSCOPE_CACHE when set and not
empty, else MS_CACHE_HOME, else ~/.cache/modelscope, '~' expanded; the same on Linux, macOS and Windows (the home
directory's .cache folder). A program may pass another cache_dir. Note that the default root is ~/.cache/modelscope,
while ModelScope 1.37 and earlier used ~/.cache/modelscope/hub when MODELSCOPE_CACHE was not set (MSC-004).
```

### MSC-002

Level IMPL, source `ms-hub`, verified-source.

```text
The current layout (modelscope-hub _download.py): a model repository <owner>/<name> is the folder
<root>/models/<owner>--<name>/ and each file is <root>/models/<owner>--<name>/snapshots/<revision>/<path in the
repository>, a plain file. <revision> is the revision as asked for (a branch, a tag or a commit), default 'master';
it is not resolved to a commit, so 'master' and a commit of it are separate folders. A download in progress is
<target>.incomplete beside its target. Locks are <root>/.lock/file_<sha256>.lock and repo_<sha256>.lock.
```

### MSC-003

Level IMPL, source `ms-hub`, verified-source.

```text
Which snapshot modelscope-hub reads when no revision is named (_cache_manager.py resolve_cached_snapshot,
_download.py _resolve_cached_file_at): snapshots/master, else snapshots/main, else the only folder in snapshots/;
with several and neither name, the choice is ambiguous and it raises an error. For one file it tries master, then
main, then every snapshot that has the file.
```

### MSC-004

Level IMPL, source `modelscope-old`, verified-source.

```text
The older layout (ModelScope 1.37 and before; file_download.py, utils/caching.py at v1.37.1): one folder per
repository with no revisions, <old root>/models/<owner>/<name with every '.' written '___'>/, the files directly in
it (a later download of another revision overwrote them). <old root> is MODELSCOPE_CACHE when set, else
~/.cache/modelscope/hub. Downloads in progress were under <old root>/models/._____temp/<owner>/<name>/. The folder
also holds .msc and .mv, ModelScope's own records of the cached files and the model's version. modelscope-hub 0.7.1
still reads this layout first when it is not empty, at <root>/models/<owner>/<name___> or
<root>/hub/models/<owner>/<name___> (_find_legacy_repo_dir), and ModelScope 1.40.3 also looks for
<root>/<owner>/<name> and <root>/hub/<owner>/<name> from earlier still (hub/utils/utils.py
find_reusable_legacy_repo_dir).
```

### MSC-005

Level IMPL, source `ms-hub`, verified-source.

```text
Compatibility links (modelscope-hub _cache_manager.py _link_legacy_model_path): after a download, modelscope-hub
makes <old root>/models/<owner>/<name> (the name not rewritten) a relative symbolic link to the snapshot it
returned, when that lies inside the cache root, for programs written for the older layout. So one snapshot may be
reached by two paths.
```

### MSC-006

Level MUST, source `modelscope-old`, verified-source.

```text
A reader never opens .msc or .mv files: they are Python pickles (utils/caching.py), and loading a pickle can run
arbitrary code. A reader writes nothing in the cache.
```

### MSC-007

Level SHOULD, source `ms-hub`, verified-source, suggestion SUG-045 (suggestions.md).

```text
Suggestion SUG-045. A reader lists a repository <owner>/<name> from
<root>/models/<owner>--<name>/snapshots/<revision>/ (each revision folder as <owner>/<name>@<revision>, or only the
one MSC-003 picks), and from the older folders of MSC-004, where <owner>/<name___> gives back the name with '___'
read as '.'. It resolves links and lists each real folder once (MSC-005). It skips *.incomplete files, ._____temp,
.lock, .msc and .mv. Inside a folder it reads GGUF files and model directories as for the Hugging Face cache: a
split GGUF set by its -NNNNN-of-MMMMM names and quant tags by llama.cpp's rule (hf-hub-cache.md HFC-010); ModelScope
itself gives no quant tags.
```

## Open questions

### MSC-Q1

Status: open. Impact: all rules.

```text
modelscope-hub publishes no repository URL in its package metadata, so it is pinned by its PyPI source
distribution's sha256 rather than a commit. Not run: no ModelScope cache was written or read here.
```
