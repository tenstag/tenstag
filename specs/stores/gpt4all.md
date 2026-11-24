<!-- Generated from tensdataspecs d71a1f0a5f5f by the maintainers' stores.py. Do not edit by hand. -->

# GPT4All's model folder

Rules G4A-nnn. Formats: gguf. Certainty: verified-source.

```text
Where the GPT4All desktop application (Nomic) keeps its model files. Added 2026-11-23. Read in GPT4All v3.10.0
(gpt4all-chat/src/main.cpp, mysettings.cpp, modellist.cpp, download.cpp); main was 4 commits ahead on 2026-11-23,
none touching these files. Paths that depend on Qt come from Qt 6's documentation of QStandardPaths and QSettings.
Read, not run: GPT4All is not installed here.
```

## Sources

- `gpt4all`: [GPT4All source at release v3.10.0](https://github.com/nomic-ai/gpt4all/tree/228d5379cfb54e966449e153082c74c66b27c6c9/gpt4all-chat/src) (v3.10.0 = 228d5379cfb5 (2025-02-24), read 2026-11-23; main b666d16db5ae (2025-05-27) checked for changes), reference-implementation
- `qt`: [Qt 6 documentation, QStandardPaths and QSettings](https://doc.qt.io/qt-6/qstandardpaths.html) (Qt 6.12 documentation as fetched 2026-11-23 (qstandardpaths.html, qsettings.html)), normative

## Rules

### G4A-001

Level IMPL, source `gpt4all`, verified-source.

```text
The settings file. GPT4All sets the organisation nomic.ai, the application GPT4All and the INI format (main.cpp), so
by QSettings' documented rule its settings are $HOME/.config/nomic.ai/GPT4All.ini on Linux and macOS (the Linux path
follows $XDG_CONFIG_HOME when set) and %APPDATA%\nomic.ai\GPT4All.ini on Windows. The key modelPath (in the
[General] section, where QSettings writes keys with no group) holds the model folder as a canonical absolute path
ending in '/'. An older key modelPaths is renamed to modelPath when GPT4All next starts (mysettings.cpp). Values are
written in QSettings' INI escaping; a path with characters it escapes is not decoded by a plain INI reader.
```

### G4A-002

Level IMPL, source `qt`, documented.

```text
The model folder: modelPath when set, else QStandardPaths AppLocalDataLocation (mysettings.cpp
defaultLocalModelsPath). Qt documents that location as ~/.local/share/<APPNAME> on Linux, ~/Library/Application
Support/<APPNAME> on macOS and C:/Users/<USER>/AppData/Local/<APPNAME> on Windows, where <APPNAME> is 'usually the
organization name, the application name, or both'; for GPT4All that gives .../nomic.ai/GPT4All (the folder named in
the issue; Qt's choice of both names is inferred from its documentation, not read in Qt's source). On Linux the base
follows $XDG_DATA_HOME. GPT4All also scans the folder holding its executable (modellist.cpp
updateModelsFromDirectory).
```

### G4A-003

Level IMPL, source `gpt4all`, verified-source.

```text
What GPT4All lists as a model (modellist.cpp processModelDirectory): every regular file in the folder or any
subfolder whose name ends in .gguf (or .rmodel, below), except names starting with 'incomplete'. Each .gguf file is
a model on its own: GPT4All has no split GGUF sets and no projectors. Models are identified by file name; names and
quantization labels shown for models it offers for download come from its catalogue models3.json (fields name,
filename, quant, md5sum or sha256sum), fetched from gpt4all.io and cached in QStandardPaths CacheLocation
(~/.cache/nomic.ai/GPT4All on Linux, by the same reading of Qt's documentation as G4A-002). A file not in the
catalogue is named by its file name.
```

### G4A-004

Level IMPL, source `gpt4all`, verified-source.

```text
Downloads (download.cpp, modellist.cpp incompleteDownloadPath): a download is written to <model folder>/incomplete-
<file name>, resumed with an HTTP Range request, checked against the catalogue's md5sum or sha256sum when complete,
and renamed to <model folder>/<file name>. So an incomplete- file is never a finished model.
```

### G4A-005

Level MUST, source `gpt4all`, verified-source.

```text
A reader never opens .rmodel files. They describe remote models, and those named *-capi.rmodel are JSON holding an
apiKey for an OpenAI-compatible service (modellist.cpp). They are not weights.
```

### G4A-006

Level SHOULD, source `gpt4all`, verified-source, suggestion SUG-044 (suggestions.md).

```text
Suggestion SUG-044. A reader lists each *.gguf file under the model folder (G4A-002, from G4A-001 when set), at any
depth, whose name does not start with 'incomplete', as one model named by its file name; it may show the catalogue's
name and quant for a file name the cached models3.json lists. It writes nothing in the folder or the settings file.
```

## Open questions

### G4A-Q1

Status: open. Impact: G4A-002 default paths.

```text
Qt's exact <APPNAME> for an application with an organisation name (nomic.ai/GPT4All) is taken from Qt's
documentation, which says only 'usually the organization name, the application name, or both'; Qt's source was not
read and no installation was examined.
```

### G4A-Q2

Status: open. Impact: all rules.

```text
No release since v3.10.0 (2025-02-24); the project may be inactive. A new release would need a re-read.
```
