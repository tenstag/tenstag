<!-- Generated from tensdataspecs d71a1f0a5f5f by the maintainers' stores.py. Do not edit by hand. -->

# Jan's data folder (llama.cpp models)

Rules JAN-nnn. Formats: gguf. Certainty: verified-source.

```text
Where the Jan desktop application (janhq) keeps the GGUF models it runs with its llama.cpp engine. Added 2026-11-23.
Read in Jan v0.8.8 (src-tauri/src/core/app/commands.rs, paths.rs, constants.rs, models.rs;
src-tauri/src/core/downloads/helpers.rs; extensions/llamacpp-extension/src/index.ts;
src-tauri/plugins/tauri-plugin-llamacpp/guest-js/types.ts). Read, not run. Jan's MLX models (folder mlx/) are not
GGUF and are not described. Layouts of Jan releases before the llamacpp/ folder are described only as far as v0.8.8
still reads them.
```

## Sources

- `jan`: [Jan source at release v0.8.8](https://github.com/janhq/jan/tree/a7752d5be16fc5d92df7809def274ffd2b27db07) (v0.8.8 = a7752d5be16f (2026-10-27; release published 2026-10-28), read 2026-11-23), reference-implementation

## Rules

### JAN-001

Level IMPL, source `jan`, verified-source.

```text
The configuration file (commands.rs resolve_config_file_path, paths.rs): <data root>/Jan/settings.json, where <data
root> is JAN_DATA_ROOT when it is an absolute path, else the system data folder of the Rust crate dirs:
$XDG_DATA_HOME or ~/.local/share on Linux, ~/Library/Application Support on macOS, the Roaming AppData folder on
Windows (from the known-folder API, not %APPDATA%). Its JSON field data_folder holds Jan's data folder; moving the
folder in Jan's settings changes this field. A settings.json under the bundle identifier (<data root>/jan.ai.app/),
or on Linux under ~/.config/Jan/, is an older place, which Jan moves to the canonical one when that is missing.
```

### JAN-002

Level IMPL, source `jan`, verified-source.

```text
The data folder (commands.rs resolve_jan_data_folder): JAN_DATA_FOLDER when set and not empty; else data_folder from
JAN-001's file; else <data root>/Jan/data (APP_NAME replaces 'Jan' when set). The folder named in data_folder may be
anywhere.
```

### JAN-003

Level IMPL, source `jan`, verified-source.

```text
The models (llamacpp-extension index.ts). Each model has the id <model id> ([A-Za-z0-9/_.-], may contain '/', no
empty, '.' or '..' part) and the file <data folder>/llamacpp/models/<model id>/model.yml, a YAML mapping with
model_path, optional mmproj_path, name (the name shown), size_bytes, and optional sha256, mmproj_sha256,
mmproj_size_bytes and embedding (true for an embedding model), among others. model_path and mmproj_path are relative
to the data folder for files Jan downloaded or migrated, and absolute for a local file imported in place (Jan does
not copy it). A download from a URL is saved as llamacpp/models/<model id>/model.gguf, with mmproj.gguf for a
projector and mtp.gguf for a speculative-decoding draft model: the original file name is not kept. model.yml is
written after the downloads finish.
```

### JAN-004

Level IMPL, source `jan`, verified-source.

```text
Downloads in progress (downloads/helpers.rs): <file>.tmp holds the data and <file>.url the source URL, both kept
while a download is paused; the file takes its own name when complete.
```

### JAN-005

Level IMPL, source `jan`, verified-source.

```text
Older models (index.ts, the migration of legacy configurations): Jan before the llamacpp/ folder kept a YAML file
per model under <data folder>/models/ (in folders cortex.so/, huggingface.co/ or imported/), whose files list named
the GGUF file relative to the data folder. v0.8.8 writes a model.yml for each such model, pointing at the old file
where it is, so the old GGUF file stays in use and is not moved.
```

### JAN-006

Level MUST, source `jan`, verified-source.

```text
A reader writes nothing in the data folder. Besides models, the data folder holds settings.json and
provider_secrets.enc (keys for remote providers) and the user's threads (constants.rs); a reader of models has no
reason to open them.
```

### JAN-007

Level SHOULD, source `jan`, verified-source, suggestion SUG-046 (suggestions.md).

```text
Suggestion SUG-046. A reader lists a Jan model for each model.yml under <data folder>/llamacpp/models/ (at any
depth, since ids may contain '/'), with id the folder's path below models/ and name from the name field. Its GGUF
file is model_path (relative paths against the data folder) and its projector mmproj_path; mtp.gguf is a side file.
A folder without model.yml is not a finished model, and *.tmp and *.url files are skipped. A file named model.gguf
carries no name or quant tag of its own: take them from model.yml or the GGUF metadata.
```

## Open questions

### JAN-Q1

Status: open. Impact: old installations.

```text
Releases before the llamacpp/ layout, and their default data folder (~/jan is believed), were not read; only what
v0.8.8 migrates is described. Not run.
```
