<!-- Generated from tensdataspecs d71a1f0a5f5f by the maintainers' stores.py. Do not edit by hand. -->

# LM Studio's models folder

Rules LMS-nnn. Formats: gguf. Certainty: documented.

```text
Where LM Studio keeps model files. Added 2026-11-22. LM Studio itself is not open source; what is here comes from
its documentation and from its open-source command-line tool (lms) and the library that tool uses to find LM
Studio's home folder (lmstudio-js, package lms-common-server). Read, not run: LM Studio is not installed here. What
the application itself does is not read; rules taken from the tool say so.
```

## Sources

- `lms-docs`: [LM Studio documentation, "Import Models" (app/advanced/import-model)](https://lmstudio.ai/docs/app/advanced/import-model) (page as fetched 2026-11-22 (undated)), informative
- `lms-cli`: [lms command-line tool, src/lmstudioPaths.ts and src/subcommands/importCmd.ts](https://github.com/lmstudio-ai/lms/tree/138dcffbc40e5fe3d9c0d38cf75dcdc1d883d849) (lms @ 138dcffbc40e (2026-11-09), read 2026-11-22), reference-implementation
- `lmstudio-js`: [lmstudio-js packages/lms-common-server/src/findLMStudioHome.ts](https://github.com/lmstudio-ai/lmstudio-js/tree/2f8b0782e90bfa3b6760a2f1777a2a30ec7d560d/packages/lms-common-server/src) (lmstudio-js @ 2f8b0782e90b (2026-11-19), read 2026-11-22), reference-implementation

## Rules

### LMS-001

Level IMPL, source `lmstudio-js`, verified-source.

```text
LM Studio's home folder, as the lms tool finds it (findLMStudioHome): the path written in the file
.lmstudio-home-pointer in the user's home directory (the home directory with symbolic links resolved), trimmed; else
~/.cache/lm-studio when it exists; else ~/.lmstudio. When the pointer file is missing, the tool writes it with the
folder it chose. The same on every system. So a store that began under ~/.cache/lm-studio (older installs) keeps it,
and the pointer file, not a fixed path, says which.
```

### LMS-002

Level IMPL, source `lms-cli`, verified-source.

```text
The models folder, as lms import finds it (importCmd.ts resolveModelsFolderPath): the string downloadsFolder in
<home>/settings.json, where <home> is LMS-001's folder; else, when that file is missing, does not parse or has no
string downloadsFolder, <home>/models. A folder moved in the application's settings is therefore expected in
downloadsFolder; that the application writes it there is inferred from the tool, not read.
```

### LMS-003

Level IMPL, source `lms-docs`, documented.

```text
The layout: <models folder>/<publisher>/<model>/<file>.gguf, which the documentation says preserves the Hugging Face
repository's names (publisher and repository). lms import puts a file at <models folder>/<user>/<repo>/<file name>,
the user and repository found by searching the Hub for the file name, or asked for (--user-repo).
```

### LMS-004

Level SHOULD, source `lms-docs`, documented, suggestion SUG-042 (suggestions.md).

```text
Suggestion SUG-042. A reader lists <publisher>/<model>/<file>.gguf exactly three levels below the models folder, as
model <publisher>/<model> and file <file>.gguf; it does not take <publisher>/<model> to be a Hugging Face repository
id without checking, since a file imported by hand may sit under any names. It treats a .gguf file whose
general.type is not 'model' (a projector, mmproj-*.gguf) as a side file of the model folder, not a model. The rule
may be split: a reader that reads no model data applies it by file name alone (a name starting with mmproj, in any
case), and a program that reads the file's metadata also applies the general.type test. Other files in a model
folder (for example models in other formats) are not described by any document read here and are not listed as GGUF.
```

## Open questions

### LMS-Q1

Status: open. Impact: LMS-002 to LMS-004.

```text
The application's own code is not open: whether it writes downloadsFolder to settings.json when the folder is moved,
what side files it keeps in a model folder, and how it stores non-GGUF (MLX) models are not documented in what was
read.
```
