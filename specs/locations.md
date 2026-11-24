# Built-in locations

Status: stable since 2026-11-23 (tenstag-rust 0.7.0). A change that changes behaviour is a new rule, never a silent
change (README.md, Status).

Where the programs that download models keep them, found as those programs find them. How each program's folder is
found is written down in [stores/](stores/README.md), one document per store (`stores/<store>.md`); this
document says which of their rules tenstag follows, in which order, and what tenstag decides where they leave it
open.

Test vectors: [`test-vectors/configuration.json`](test-vectors/configuration.json) (the `defaults` cases).

## Rules

### LOC-001 (MUST): the built-in locations, in order

When `defaults` is not `false` (configuration.md CFG-002):

| # | location | kind | found by (stores/) |
|---|---|---|---|
| 1 | the Hugging Face cache | `directory` | stores/hf-hub-cache.md HFC-001, as HFC-003 (SUG-037) suggests: `HF_HUB_CACHE`, else `HUGGINGFACE_HUB_CACHE`, else `$HF_HOME/hub`, where `HF_HOME` defaults to `$XDG_CACHE_HOME/huggingface`, else `<home>/.cache/huggingface`. `~` and `$VAR` in them are expanded as Python's `os.path.expanduser(os.path.expandvars(...))` does (a variable not set is left as written). |
| 2 | llama.cpp's cache | `directory` | stores/llama-cpp-cache.md LCC-001: `LLAMA_CACHE` as it is; else `llama.cpp` in `%LOCALAPPDATA%` (Windows), `<home>/Library/Caches` (macOS), `$XDG_CACHE_HOME` or `<home>/.cache` (elsewhere). |
| 3 | LM Studio's models | `lmstudio` | stores/lm-studio.md LMS-001, LMS-002: the home in `<home>/.lmstudio-home-pointer` (links resolved, trimmed), else `<home>/.cache/lm-studio` when it exists, else `<home>/.lmstudio`; then `downloadsFolder` of its `settings.json`, else its `models`. |
| 4 | GPT4All's models | `gpt4all` | stores/gpt4all.md G4A-001, G4A-002 (LOC-002). |
| 5 | the ModelScope cache | `modelscope` | stores/modelscope-cache.md MSC-001: `MODELSCOPE_CACHE`, else `MS_CACHE_HOME`, else `<home>/.cache/modelscope`, on every system, `~` expanded. |
| 6 | Jan's data folder | `jan` | stores/jan.md JAN-001, JAN-002: `JAN_DATA_FOLDER` (`~` expanded); else `data_folder` of `<data root>/Jan/settings.json`, else `<data root>/Jan/data`, where `<data root>` is `JAN_DATA_ROOT` when absolute, else `%APPDATA%` (Windows), `<home>/Library/Application Support` (macOS), `$XDG_DATA_HOME` or `<home>/.local/share`. |
| 7 | Docker Model Runner's store | `docker` | stores/docker-model-runner.md DMR-001: `MODELS_PATH`, else `<home>/.docker/models`, `~` expanded. |
| 8 | RamaLama's store | `ramalama` | stores/ramalama.md RML-001 (LOC-003). |
| 9 | Ollama's models | `ollama` | stores/ollama.md OLM-001: `OLLAMA_MODELS`, surrounding spaces and quotes removed, `~` expanded; else `<home>/.ollama/models`, and on Linux also `/usr/share/ollama/.ollama/models` (LOC-004). |

A location whose folder does not exist is listed (for a person to see where tenstag looked) and has no models.

### LOC-002 (MUST): GPT4All's folder

`modelPath` in the `[General]` section of `nomic.ai/GPT4All.ini` in `$XDG_CONFIG_HOME` or `<home>/.config` (Linux),
`<home>/.config` (macOS) or `%APPDATA%` (Windows) (G4A-001). A value in double quotes is taken without them. A value
holding `\` is in Qt's escaped form, which tenstag does not decode: the default folder is used instead, and a
warning given. Else `nomic.ai/GPT4All` in `$XDG_DATA_HOME` or `<home>/.local/share` (Linux),
`<home>/Library/Application Support` (macOS) or `%LOCALAPPDATA%` (Windows) (G4A-002). The folder of GPT4All's own
executable, which GPT4All also searches, is not known to a reader and is not read.

### LOC-003 (MUST): RamaLama's store

`RAMALAMA_STORE`; else `store` in the `[ramalama]` table of the RamaLama configuration files, a later file winning:
`RAMALAMA_CONFIG` alone when that file exists; else `ramalama/ramalama.conf` then `ramalama/ramalama.conf.d/*.conf`
(sorted by name) in each of `/etc`, `$XDG_DATA_HOME` or `<home>/.local/share`, and `$XDG_CONFIG_HOME` or
`<home>/.config` (on Windows `%LOCALAPPDATA%` and `%APPDATA%`); else `/var/lib/ramalama` when `USER` is `root`; else
`ramalama` in `$XDG_DATA_HOME` or `<home>/.local/share`, on every system (RML-001). The configuration folders under
Python's install prefix are not read: a reader cannot know which Python RamaLama runs under.

### LOC-004 (MUST): Ollama's Linux service

On Linux, when `OLLAMA_MODELS` is not set, the store of Ollama's system service, `/usr/share/ollama/.ollama/models`,
is read as well as the user's, after it (OLM-001 documents both).

### LOC-005 (SHOULD): saying where it looked

An implementation can describe its locations for a person: each location's path, what it is (`the Hugging Face cache
(HF_HOME)`), which layer gave it (default, configuration, environment, program), and whether the folder exists; and
the configuration file read, the tag folder and the cache folder.
