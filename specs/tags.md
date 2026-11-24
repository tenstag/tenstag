# Tags

Status: stable since 2026-11-23 (tenstag-rust 0.6.0). A change that changes bytes is a new version (README.md, Status).

A tag is something a program worked out about a model and keeps so as not to work it out again: `arch=qwen3`,
`mem-4k=5.1GiB`, `needs-encoders=t5xxl,clip-l`. Every tag has an *owner*, the program that wrote it (TAG-009): through
an implementation, a program writes only its own tags, and may read every owner's. Owners keep well-behaved programs
apart; they are not a protection (TAG-012). Tags belong to a model's identity (fingerprint.md),
not to its path. How they are kept is tag-store.md.

Tags are a cache (TAG-008): they are kept with the fingerprints, and may be deleted at any time.

Test vectors: [`test-vectors/tags.json`](test-vectors/tags.json).

## Rules

### TAG-001 (MUST): the form of a tag

A tag is UTF-8 text. It is either a *word* (`chat`), or a *key* and a *value* separated by the first `=`
(`arch=qwen3`; in `a=b=c` the key is `a` and the value `b=c`). A word is a key with no value.

### TAG-002 (MUST): keys

A key is 1 to 256 bytes of UTF-8 and holds none of:
- `=`;
- the control characters U+0000 to U+001F, U+007F, and U+0080 to U+009F;
- the space U+0020 or any other Unicode `White_Space` character: U+00A0, U+1680, U+2000 to U+200A, U+2028,
  U+2029, U+202F, U+205F, U+3000 (U+0009 to U+000D and U+0085 are controls already).

Keys are compared byte for byte: `Arch` and `arch` are two keys. Each owner (TAG-009) has its own keys, so keys need
no prefix: chatrun's `arch` and imagenode's `arch` are different tags.

### TAG-003 (MUST): values

A value is 1 to 4,096 bytes of UTF-8 and holds none of the control characters of TAG-002. It may hold spaces and
`=`. It is kept exactly as written: nothing is trimmed, changed in case, or reordered. `lang=` (an empty value) is
not a tag.

### TAG-004 (MUST): one value per key

An owner's tags of a model are a map from key to an optional value: each key appears at most once. Setting a tag
whose key the owner has already set replaces it, whatever either was: `lang=de` replaces `lang=en,fr`; `lang`
replaces `lang=de`; `lang=x` replaces the word `lang`. Several values for one key are written in one value
(`lang=en,fr`).

Removing a tag removes its key, whatever its value.

### TAG-005 (MUST): matching

Matching is always within one owner's tags:
- *Has the key* `k`: the owner's tags hold `k`, with or without a value.
- *Has the tag* `k=v`: the owner's tags hold `k` with exactly the value `v`.
- *Has the item* `x` *of key* `k`: `x` is in the value set (TAG-006) of `k`'s value.

All comparisons are byte for byte. An implementation's free-text search may ignore letter case, but these three
never do.

### TAG-006 (MUST): the value set

The *value set* of a value is how a program reads several items written in one value, without parsing it itself:
the value split at every `,`, each part with spaces (U+0020 only) removed from its start and end, and empty parts
dropped. `en, fr,,en` gives the set {`en`, `fr`}. A word has the empty set.

The value set is a reading only: the value is always kept as written (TAG-003), and a program that needs a comma
inside an item reads the value itself.

### TAG-008 (MUST): tags are a cache

A tag is a value a program can work out again: from the model's contents, its file formats, its store, or what the
program knows of them. Any tag may be gone the next time it is read, because a person cleared the cache, or an
implementation cleaned it (tag-store.md TGS-006). So a program:
- treats a missing tag as not yet worked out, and works it out and tags the model then, or when it indexes its own
  folders;
- never keeps in tags the only record of something it cannot work out again, such as a person's favourites or
  ratings: those belong in the program's own settings. A program may copy them into tags, for other programs to
  read, as long as it keeps the original and writes the tag again after a clean-up.

Where a program's way of working something out changes, it raises its owner version (TAG-010), and its older tags
count as missing.

### TAG-007 (SHOULD): how many

An owner has at most 1,024 tags of a model. An implementation refuses a tag that would make more, and one that breaks TAG-002 or
TAG-003, with an error that says why.

### TAG-009 (MUST): owners

Every tag is written by an *owner*: a name for the program, 1 to 128 bytes of lowercase ASCII letters, digits, `-`,
`_`, `.` and `/`, starting with a letter or a digit; a `/` only between two other characters, never two together. A
program gives its owner name when it opens the library, and then:
- it writes, changes and removes only its own tags;
- it reads its own tags, and any other owner's by that owner's name;
- a program that gives no owner reads every owner's tags and writes none.

Searches (names.md NAM-005) read every owner's tags.

### TAG-011 (SHOULD): unique owner names

Two programs with the same owner name would overwrite each other's tags, so a program's owner name is one no other
program will choose. It is one of:
- a **reverse domain name** its maker controls, then the program: `com.example.chatrun` for chatrun made by the
  owner of `example.com`. This is the convention of Java packages, Android, Flatpak and Apple application ids, and it
  sorts one maker's programs together;
- its **GitHub repository**, `<user or organisation>/<repository>`, in lower case: `example/chatrun`. GitHub's names
  are unique and case-insensitive, so the lower-case form is the same name.

A plain name (`chatrun`) is for trying things out, not for a program others will run.

### TAG-012 (MUST): owners are not a protection

An owner name is what a program says it is: nothing checks it, and nothing stops a program from giving another's
name. The tag files are plain files, which any program running as the person can read, change or delete without an
implementation. So:
- owners keep programs that follow this specification from changing each other's tags by mistake; they do not stop a
  program that does not follow it, and they do not prove which program wrote a tag;
- a program treats every tag it reads, its own included, as input it did not check: it parses values defensively,
  and works a tag out again when its value makes no sense to it, as it would for a missing one (TAG-008);
- implementations document owners in these terms, never as a guarantee that a program's tags cannot be changed by
  another.

### TAG-010 (MUST): owner versions

With its owner name a program gives a *version*, a whole number from 0 to 4,294,967,295 (0 by default). Each
owner's tags of a model are kept with the version that wrote them (tag-store.md TGS-003). A program reading its own
tags sees none when they were written at another version, and its first write at its version replaces them all: so
when a program changes how it works something out, it raises its version, and every model's tags are worked out
again once, without the program keeping a version tag of its own. Another owner's tags are read whatever their
version, which is given with them.

A program may also remove all its own tags of a model at once (and never any other owner's).
