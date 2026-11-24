# Names

Status: stable since 2026-11-23 (tenstag-rust 0.7.0). A change that changes behaviour is a new rule, never a silent
change (README.md, Status).

How a name a person types becomes a model, so that `qwen3 0.6 q8` or `Qwen/Qwen3-0.6B-GGUF:Q8_0` means the same model
in every program using tenstag. The grammar is tenstag's own; a Hugging Face repository name is chosen from as
llama.cpp and huggingface_hub choose (stores/hf-hub-cache.md).

Test vectors: [`test-vectors/listing.json`](test-vectors/listing.json) (each case's `resolve`) and
[`test-vectors/names.json`](test-vectors/names.json) (repository names).

## Rules

### NAM-001 (MUST): the order

A name is tried as each of these in turn, and the first that applies decides:
1. **A path that exists:** its entry (listing.md LST-016), or an error when it is not a model.
2. **A nickname** from the configuration's `[names]`: its target, resolved again from step 1. A nickname that leads
   through more than four nicknames is an error.
3. **The id of an entry not from the Hugging Face cache**, ignoring ASCII case.
4. **A Hugging Face repository name** (NAM-003): the model the cache holds (NAM-004), or an error saying the cache
   does not hold it. Nothing is downloaded.
5. **The id of any entry**, ignoring ASCII case.
6. **A search** (NAM-005): its one match; an error when nothing matches; and when several do, an error listing their
   ids, for a person to choose from. A search never guesses.

Step 3 comes before step 4 so that another store's model whose id looks like a repository (`dirs/tiny`) is that
model. When a program has chosen which models it works with (NAM-006), steps 3 to 6 see only those.

### NAM-002 (MUST): nicknames

`[names]` maps a nickname to any name: a path, a repository name, an id, another nickname, or search words.

### NAM-003 (MUST): Hugging Face repository names

`[hf.co/ | huggingface.co/]<org>/<name>[:<quant>][@<revision>]`:
1. `hf.co/` or `huggingface.co/` at the start is removed (as Ollama writes a Hub repository; neither huggingface_hub
   nor llama.cpp accepts it, HFC-014).
2. At the last `@`: the revision after it must be non-empty, without `..` and without whitespace, else the name is
   not a repository name.
3. At the first `:`: the quant after it must be non-empty letters, digits, `_`, `.` and `-`, else the name is not a
   repository name.
4. The repository is 1 to 256 bytes with exactly one `/`, of ASCII letters, digits and `_`, with `/`, `.` and `-`
   only between two of those (llama.cpp's check, the stricter of HFC-014's two).

### NAM-004 (MUST): the cached choice

Among the entries of the Hugging Face cache layout whose repository equals the name's, ignoring ASCII case
(HFC-013, HFC-015):
- the commit is the revision when it is 40 hex digits (lower-cased); else the commit of the entry whose refs hold the
  revision; with no revision, the commit `main` points at, else the commit of the entry whose first ref is first by
  name;
- among that commit's entries, the file is chosen from their files, in listing order, as llama.cpp chooses
  (HFC-010): the first GGUF model file that is its model's first part and carries the quant as a whole token
  (`(^|[-./])<quant>[.-]`, ignoring case); with no quant, `Q4_K_M`, then `Q8_0`, then the first such file;
- with no quant and no GGUF file, the snapshot's folder entry (a model folder, a pipeline or an adapter).

No entry otherwise.

### NAM-005 (MUST): search

The query is split at whitespace, each word lower-cased. An entry matches when every word is a substring of its
*text*, lower-cased: its id, a space, the last part of its path, and for each of its tags of every owner (tags.md),
in order of owner then key, a space, the key, a space and the value (empty for a word). An empty query matches every entry.

Only the tags of entries whose identity is already in the fingerprint cache are read, so a search never reads a
model (fingerprint-cache.md).

### NAM-006 (MUST): a program's choice of models

A program may give a rule, a function of an entry, that keeps the models it works with: listings, searches, tag
queries and NAM-001 steps 3 to 6 then see only those. tenstag decides nothing about what a model is for (listing.md
LST-018); the rule is the program's.
