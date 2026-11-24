# Configuration

Status: stable since 2026-11-23 (tenstag-rust 0.7.0). A change that changes behaviour is a new rule or a new key,
never a silent change (README.md, Status). CFG-009 to CFG-014 (who added a location, and programs changing the file)
were added on 2026-11-24 (tenstag-rust 0.10.0, tenstag-python 0.2.0).

Where an implementation looks for models: the configuration file, the environment variables, the locations a
program gives, and the built-in defaults (locations.md). Every implementation reads the same file and variables the
same way, so a person configures tenstag once for every program on the machine. A program may also change the file
for the person (CFG-010 to CFG-013): add a folder, remove one, turn the defaults off; the rest of the file stays as
the person wrote it.

Test vectors: [`test-vectors/configuration.json`](test-vectors/configuration.json) (reading),
[`test-vectors/config-writing.json`](test-vectors/config-writing.json) (changing the file).

## Rules

### CFG-001 (MUST): the configuration file

The first of these that applies:
1. `TENSTAG_CONFIG` (a file that must exist: one that cannot be read is an error);
2. `tenstag/config.toml` in `XDG_CONFIG_HOME` when that is set, else in `<home>/.config` (on every system, Windows
   and macOS included), when that file exists. Only one of the two folders is looked in.

None is no error: every key then has its default. `<home>` is `HOME`, or `USERPROFILE` on Windows. An environment
variable set to the empty string counts as not set, here and everywhere in this specification.

### CFG-002 (MUST): its form

TOML 1.0, UTF-8. All keys are optional:

```toml
defaults = true                    # also read the built-in locations (locations.md)

[[location]]                       # a location, read in the order written
path = "/data/models"              # required; `~/` at the start is the home folder
kind = "directory"                 # how it is laid out: CFG-003
depth = 6                          # for a walked kind only: CFG-004
min_size = 1048576                 # for `directory` (listing.md LST-004); no effect on other kinds
added_by = "goldnode/tensrun"      # who added it: CFG-009
added = 2026-11-24T18:48:18Z       # when: CFG-009

[names]
small = "Qwen/Qwen3-0.6B-GGUF:Q8_0"   # a nickname: names.md NAM-002
```

A key not listed here, or a value of the wrong type, is an error, never ignored: the person's file says something
the implementation would not do. The error names the file and the key. (`download` and `offline` until tensfiler
0.5.0, and a location's `class` until tenstag 0.6.1, are such keys; an implementation may say so in its message.)

### CFG-003 (MUST): kinds

| `kind` | what the location is | read as |
|---|---|---|
| `directory` (the default) | a folder of your own, or a cache in the Hugging Face or llama.cpp layout | listing.md LST-002 |
| `lmstudio` | an LM Studio models folder | LST-007 |
| `ollama` | an Ollama models folder | LST-008 |
| `gpt4all` | a GPT4All model folder | LST-009 |
| `modelscope` | a ModelScope cache root | LST-010 |
| `jan` | a Jan data folder | LST-011 |
| `docker` | a Docker Model Runner store | LST-012 |
| `ramalama` | a RamaLama store folder | LST-013 |

Any other `kind` is an error that lists these.

### CFG-004 (MUST): depth

`directory`, `gpt4all` and `jan` are *walked*: a model is found when its path below the location has at most
`depth` parts (`m.gguf` is 1; `org/m.gguf` and the model folder `org/m/` are 2). The default is 6 for `directory`
and 8 for `gpt4all` and `jan`. The other kinds are read by their stores' fixed layouts, and `depth` on one of them
is an error.

### CFG-005 (MUST): environment variables

| variable | what it does |
|---|---|
| `TENSTAG_CONFIG` | the configuration file (CFG-001) |
| `TENSTAG_PATH` | more folders of your own (`kind = "directory"`), separated as the system separates `PATH` (`:`, or `;` on Windows); empty parts are skipped |
| `TENSTAG_CACHE_DIR` | the cache folder, which holds the fingerprints and the tags (fingerprint-cache.md TFC-001, tag-store.md TGS-001), when absolute |

The stores' own variables (`HF_HUB_CACHE`, `OLLAMA_MODELS` and the others) are read as locations.md says.

### CFG-006 (MUST): the order of locations

Locations are read in this order, and models are listed in it:
1. the configuration file's `[[location]]`s, as written;
2. `TENSTAG_PATH`'s folders, in order;
3. when `defaults` is not `false`, the built-in locations (locations.md LOC-001), in that document's order;
4. the locations a program gives (CFG-007), in the order given.

A folder that appears twice (compared with links resolved) is read once, at its first place.

### CFG-007 (MUST): a program's own locations

An implementation lets a program:
- add locations of its own, of any kind, with a depth and `min_size`, which are read after all others (CFG-006 step
  4) and need not be named in any configuration;
- start with *no* configuration: no file is read (so a broken one is no error), no `TENSTAG_PATH`, no defaults; only
  the locations the program gives. `TENSTAG_CACHE_DIR` still applies, so the program's tags are
  the ones every other program sees.

It also lets a program set the cache folder itself (TFC-001 step 1), which holds the tags too.

### CFG-008 (MUST): paths in the file

A `path` that starts with `~/`, or is `~`, has the home folder put in its place. Nothing else is expanded
(`$VAR` stays as written). A relative path is taken as written, relative to the program's working folder.

### CFG-009 (MUST): who added a location, and when

Two keys of a `[[location]]` record where it came from. Neither changes what is read.

- `added_by`: the program that added it, as an owner name (tags.md TAG-009, TAG-011): a string that is not one is an
  error. Absent: a person wrote the line, or a program that did not say.
- `added`: when, as a TOML local date (`2026-11-24`) or offset date-time (`2026-11-24T18:48:18Z`). Any other value (a
  string, a local date-time, a time) is an error. An implementation gives it to the program as text: a date as
  `YYYY-MM-DD`; a date-time converted to UTC, without fractions of a second, as `YYYY-MM-DDTHH:MM:SSZ`.

Implementations older than this rule (tenstag-rust before 0.10.0, tenstag-python before 0.2.0) take these keys as
unknown, an error (CFG-002): a file a program has changed needs every program on the machine to be current.

### CFG-010 (MUST): changing the file

An implementation lets a program add a location to the file (CFG-011), remove one (CFG-012) and set `defaults`
(CFG-013). Each change:
1. **The file:** the one CFG-001 names. When there is none, `tenstag/config.toml` in `XDG_CONFIG_HOME` when that is
   set, else in `<home>/.config`, created with its folders. `TENSTAG_CONFIG` naming a file that does not exist is an
   error, as when reading.
2. **Lock:** create `<file>.lock` beside it if it is missing, and take an exclusive lock on it, as tag-store.md
   TGS-005 step 1 says; wait for it. Hold it until step 6. The lock file stays.
3. **Read** the file (a missing one is empty). Text that is not UTF-8, is not TOML, or breaks CFG-002 to CFG-004 or
   CFG-009 is an error, and the file is not changed: a program never rewrites a file it cannot understand.
4. **Change only the lines** CFG-011 to CFG-013 say. Every other line stays exactly as written: comments, order,
   spacing, `[names]`. New lines end in `\n`.
5. **Check:** read the new text as TOML. Unless it is exactly the old file's TOML with the one change made, stop with
   an error and change nothing. (A file can say the same thing in forms the line rules below do not follow, such as
   an array of inline tables; this check refuses those rather than damage them.)
6. **Write** `<file>.tmp-<unique>` in the same folder, flush it to disk, and rename it over the file (TGS-005 step 4's
   way). Release the lock.

When there is nothing to change (CFG-011, CFG-012, CFG-013 say when), nothing is written, and no file or folder is
created, except the lock file in a folder that exists.

### CFG-011 (MUST): adding a location

A program gives the location (path, kind, and for a walked kind a depth; for `directory` a `min_size`), and may give
its owner name for `added_by`. The path must be absolute, or `~` or start with `~/`: anything else is an error (a
relative path would mean another folder to each program).

**Already listed:** when a `[[location]]` in the file has the same folder (compared as CFG-006 compares, after
CFG-008), nothing is written, and the implementation tells the program so (not an error), giving that location.
Only the file's locations count: a folder that TENSTAG_PATH or the defaults also give is added.

**Otherwise** these lines are put at the end of the file. First, when the file is not empty, a `\n` when it does not
end in one, then an empty line. Then:

```toml
[[location]]
path = "<the path as given>"
kind = "<kind>"                   # only when not "directory"
depth = <depth>                   # only for a walked kind, and only when not the kind's default (CFG-004)
min_size = <bytes>                # only for "directory", and only when not 1048576
added_by = "<owner>"              # only when the program gave one
added = <the time now, in UTC, as YYYY-MM-DDTHH:MM:SSZ>
```

A string is written as a TOML basic string: `\` as `\\`, `"` as `\"`, and each character from U+0000 to U+001F and
U+007F as `\u` and four upper-case hex digits; every other character as itself. The implementation gives the program
the location added, as it would read it.

### CFG-012 (MUST): removing a location

A program gives a path, compared as CFG-011 compares. When no `[[location]]` in the file has that folder, nothing is
written and the implementation tells the program so (not an error): a folder from TENSTAG_PATH or the defaults is
not in the file, and the program can tell which layer gave a location (locations.md LOC-005).

Otherwise every `[[location]]` with that folder is removed, and the implementation gives the program the first, as it
read it (with `added_by` and `added`, so the program can ask the person before removing one another program added:
whether to ask is the program's choice). A location's lines are:
- its header line (a line that, after any spaces and tabs, starts with `[[location]]`), with the comment lines (`#`
  after any spaces and tabs) directly above it, up to the first line above that is not a comment;
- and the lines after the header up to the next line that, after any spaces and tabs, starts with `[`, or the end of
  the file, less the empty lines (nothing but spaces and tabs) and comment lines at their end, which stay: they
  belong to what follows.

Each location's lines are removed in turn, from the last in the file to the first. After each, when the line before
them and the line now after them are both empty, the second is removed. Finally, when the file ends in empty lines,
they are removed, so that it ends with its last other line and `\n` (or is empty).

### CFG-013 (MUST): turning the defaults on or off

The `defaults` line is a line before the first line that, after any spaces and tabs, starts with `[`, which, after any
spaces and tabs, starts with `defaults`, then any spaces and tabs, then `=`.
- When there is one, its value (`true` or `false`) is replaced by the new one; the rest of the line stays (a comment,
  say). When it already has the new value, nothing is written.
- When there is none, setting `true` writes nothing (it is the default), and setting `false` puts `defaults = false`
  as the file's first line.

### CFG-014 (MUST): the defaults, even when off

An implementation lets a program list the built-in locations (locations.md LOC-001, in that order) whatever
`defaults` says, so that a program can show what turning them on would add.
