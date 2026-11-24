# An introduction to tenstag

tenstag is a small library for programs that use AI models: language models, image and video models, and the
adapters and encoders that go with them. It finds the models already on your computer, wherever the tools that
downloaded them put them, and turns the names people type into those models. It also gives every program a place to
remember what it worked out about each model. That memory is tied to the model's contents, so a program reads each
model once, and finds the answer again straight away, even after the model has been moved.

The first half is for developers: two example programs, and what tenstag does for them. The second half is for
anyone running several programs that use models, who'd like one place to tell all of them where the models are.

- [Two programs that use it](#two-programs-that-use-it)
- [What it does for your program](#what-it-does-for-your-program)
- [What tags are for, and what they are not for](#what-tags-are-for-and-what-they-are-not-for)
- [What it is not](#what-it-is-not)
- [A first look at the calls](#a-first-look-at-the-calls)
- [The ideas, one at a time](#the-ideas-one-at-a-time)
- [Questions developers ask](#questions-developers-ask)
- [One configuration for many programs](#one-configuration-for-many-programs)
- [Where to go next](#where-to-go-next)

## Two programs that use it

The programs below are made up, but each is like ones people use every day. Each keeps its own folders and its own
way of working, and adds tags to what it already has.

### A chat runner, like llama.cpp

`chatrun` runs language models from GGUF files. It has a folder of its own, `~/chatrun/models`, and it also wants
the models the person already downloaded with other tools.

To show the person what they can run, it needs to know each model's architecture, its parameter count, its context
length and its chat template, all of which are in the GGUF header, and how much memory it needs, which chatrun works
out from the header's tensor table. Opening and parsing fifty models at every start is slow, the more so on a hard
disk or a network share.

So at start-up it walks its models and tags any it has not seen:

```rust
let mut locations = tenstag::Locations::load()?;                    // the person's places, and the defaults
locations.add(tenstag::Location::folder(chatrun::models_folder()).depth(3)); // and chatrun's own folder
let mut library = tenstag::Library::new(locations);
library.set_owner("com.example.chatrun", 2)?;                         // chatrun owns its tags; version 2
library.only(|e| e.format == tenstag::Format::Gguf);                  // chatrun runs GGUF files only

for entry in library.entries().to_vec() {
    if library.tags(&entry)?.has("arch") {
        continue;                                                     // worked out already
    }
    let header = chatrun::read_gguf_header(&entry.path)?;              // chatrun's own code: the slow part
    library.tag(&entry, &format!("arch={}", header.architecture))?;
    library.tag(&entry, &format!("params={}", header.parameters))?;   // 7.6B
    library.tag(&entry, &format!("context={}", header.context))?;     // 32768
    library.tag(&entry, &format!("template={}", header.template))?;   // chatml
    library.tag(&entry, &format!("mem-4k={}", header.memory(4096)))?; // 5.1GiB: weights and a 4k cache
}
```

The first start reads each model once. Every later start finds every tag, reads nothing, and is instant. When the
person moves a model to another disk, renames it, or downloads the same file through LM Studio, the tags are still
there, because they belong to the model's contents, not its path.

Now its model list can say, without opening anything, what this machine can run at speed:

```rust
let free = chatrun::gpu_memory_free();
for entry in library.tagged("mem-4k")? {
    let tags = library.tags(&entry)?;
    let needs = chatrun::parse_size(tags.value("mem-4k").unwrap());
    let speed = if needs <= free { "on the GPU" } else { "partly on the CPU" };
    println!("{:<40} {} {:>8}  {}", entry.id, tags.value("arch").unwrap_or("?"), tags.value("params").unwrap_or("?"), speed);
}
```

The tag holds a fact about the model (it needs 5.1 GiB with a 4k context), and the program compares it with this
machine's memory when it runs, so the tag stays true on any machine. A measured speed is a fact about the model *and*
the machine; chatrun keeps one under a key that names the machine's GPU, `tps@rtx4090=48.2`, so that a
benchmark on one machine is never mistaken for another's.

The tags are chatrun's: it opened the library as their *owner*, so it writes only its own through tenstag, and
needs no prefix on its keys. When chatrun learns to read something new, it opens the library at version 3. Its version-2 tags then count
as missing, and every model is worked out again once, by the same loop, with no version tag of its own to keep.

### An image tool, like ComfyUI

`imagenode` builds image pipelines from model files. It keeps them in its standard folder, `~/imagenode/models`,
in sub-folders the person arranged: `checkpoints/`, `unet/`, `text_encoders/`, `vae/`, `loras/`. File names say
little, and the person needs to know which pieces go together: which text encoders a diffusion model needs, which
VAE, which LoRAs were trained for it.

At start-up it scans its folder and works out each file's place from the file's own header (a safetensors file
begins with a table of its tensors, whose names and shapes say what it is):

```rust
let mut locations = tenstag::Locations::bare();                          // imagenode's own folder only
locations.add(tenstag::Location::folder(imagenode::models_folder()).depth(4).min_size(0));
let mut library = tenstag::Library::new(locations);
library.set_owner("com.example.imagenode", 1)?;

for entry in library.entries().to_vec() {
    if library.tags(&entry)?.has("role") {
        continue;
    }
    match imagenode::identify(&entry)? {                                  // imagenode's own code
        Kind::Diffusion { family, encoders, vae } => {
            library.tag(&entry, "role=diffusion")?;
            library.tag(&entry, &format!("family={family}"))?;            // flux1
            library.tag(&entry, &format!("needs-encoders={encoders}"))?;  // t5xxl,clip-l
            library.tag(&entry, &format!("needs-vae={vae}"))?;            // flux-ae
        }
        Kind::TextEncoder { name } => {
            library.tag(&entry, "role=text-encoder")?;
            library.tag(&entry, &format!("encoder={name}"))?;             // t5xxl
        }
        Kind::Lora { base } => {
            library.tag(&entry, "role=lora")?;
            library.tag(&entry, &format!("lora-for={base}"))?;            // sdxl
        }
        Kind::Unknown => library.tag(&entry, "role=unknown")?,            // looked at: nothing to say
    }
}
```

Then, when the person picks a diffusion model, imagenode offers only what fits it, without opening a file:

```rust
let unet = library.resolve("unet/flux1-dev-Q4_K_S")?;
let needs = library.tags(&unet)?;
for encoder in needs.value_set("needs-encoders") {
    let candidates = library.tagged(&format!("encoder={encoder}"))?;    // the files that are this encoder
    // ...offer them
}
let loras = library.tagged_with("lora-for", "flux1")?;
```

Another program on the machine can read these tags too, by imagenode's name. A chat runner looking for language
models can find the files imagenode has tagged `encoder=qwen2.5-vl-7b`, a full language model, without reading them,
and then decide for itself whether to offer them:

```rust
let encoders = library.tagged_by("com.example.imagenode", "encoder=qwen2.5-vl-7b")?;
```

## What it does for your program

The examples show the pattern: *look up, and if missing, work it out and tag*. tenstag takes care of the parts
around your program's own knowledge:

- **Finding the models.** The Hugging Face cache, llama.cpp's cache, LM Studio, Ollama, GPT4All, ModelScope, Jan,
  Docker Model Runner and RamaLama each keep models in their own folder and layout, many behind hashed names and
  manifests. `library.entries()` is every model on the machine, with an id and the path to open, alongside the
  folders your program gives.
- **Turning names into models.** People name models as a Hugging Face repository with a quantisation
  (`Qwen/Qwen3-0.6B-GGUF:Q8_0`), an Ollama name (`ollama:qwen3:0.6b`), a path, or a few words (`qwen3 0.6 q8`).
  `library.resolve(name)` turns any of them into one model, picks the same file llama.cpp would pick for a
  repository name, and refuses to guess when a few words match several models.
- **Knowing a model again.** A model's identity is a fingerprint of its contents, read once and remembered, so your
  tags follow it through moves, renames and copies between stores, and the same file in two stores is one model.
- **A shared, safe cache.** Tags are small files any program, in any language, can read and write, with locking, so
  several programs can tag at once.

## What tags are for, and what they are not for

Tags are a **cache**. They hold what a program can work out again from the model's contents and what it knows of
the formats: an architecture, a parameter count, a context length, a chat template, the memory a model needs, the
encoders it takes, the base a LoRA was trained for. They live in the cache folder, and **a person may delete them at
any time**; tenstag may clean them up too. A program that finds a tag missing works it out again, then and there or at
its next scan, and the person loses nothing but a moment.

So tags are **not the place for anything only a person can say**: favourites, ratings, notes, "the one I use for
code". If a person deletes the cache, those would be gone for good. Keep them in your program's own settings. If you
want other programs to see them, write them as tags as well, and write them again whenever they are missing, so that
the tags are always a copy, never the original.

Every tag has an **owner**, the program that wrote it, named when the program opens the library
(`Library::open_as("com.example.chatrun", 2)`). Through tenstag a program writes only its own tags, so programs that
each use their own name do not overwrite each other by mistake, and it reads any other program's by name
(`tags.of("com.example.imagenode")`, `library.tagged_by("com.example.imagenode", ...)`).

An owner is a courtesy between well-behaved programs, not a protection. Nothing checks an owner name: a program could
give another's, and the tag files are plain files that any program running as the person can change or delete. So
treat every tag you read, your own included, as unchecked input: parse its value carefully, and when it makes no sense
to you, work it out again, as you would if it were missing.

The owner name must be one no other program will choose, or two programs would overwrite each other's tags. Use
either:
- a **reverse domain name** you control, then the program: `com.example.chatrun` if you own `example.com`. This is the
  convention for program identifiers (Java packages, Android, Flatpak and Apple application ids), and it keeps one
  maker's programs together;
- your program's **GitHub repository**, `user/repository` in lower case: `example/chatrun`.

A plain name such as `chatrun` is fine for trying things out, not for a program others will run.

Two habits keep tags useful:
- **Raise your version** when your way of working things out changes: your older tags then count as missing, and
  every model is worked out again once.
- **Keep facts about the model apart from facts about the machine**: tag what the model needs, and compare with the
  machine when you run; put the machine in the key when you must (`tps@rtx4090`).

## What it is not

- **Not a downloader.** It never uses the network. When a model is not on the machine, `resolve` says so; fetching
  it is your program's job (Hugging Face's `huggingface_hub`, or the `hf-hub` crate in Rust, write the same cache
  tenstag reads, so a model you download is found by every program).
- **Not a model reader.** It never parses a GGUF or safetensors file and never loads weights: working out what a
  model is, is your program's knowledge. tenstag reads names, sizes and the stores' own bookkeeping, and to fingerprint
  a model it hashes a sample of its bytes without interpreting them.
- **Not a judge of what a model is for.** It gives facts (the format, the path, the file names) and never guesses
  whether a file is a chat model, a diffusion model or a text encoder.
- **Not a server or a daemon.** It is a library in your process.
- **Not a store.** It moves, copies and deletes no model. Every model folder is read-only to it.

## A first look at the calls

The examples are in Rust. The Python implementation, tenstag-python, follows the same specification with the same
calls in Python's style, and reads and writes the same files:

```python
library = tenstag.Library.open(owner="com.example.chatrun", version=2)
entry = library.resolve("qwen3 0.6 q8")
if not library.tags(entry).has("arch"):
    library.tag(entry, f"arch={read_architecture(entry.path)}")
```

```rust
let mut library = tenstag::Library::open_as("com.example.chatrun", 2)?; // chatrun owns its tags, version 2
let entry = library.resolve("qwen3 0.6 q8")?;           // a path, a repository name, an Ollama name, or words
println!("{} at {}", entry.id, entry.path.display());  // what your program opens

let tags = library.tags(&entry)?;                       // what programs worked out about this model
tags.value("context");                                  // Some("32768"): chatrun's own, exactly as written
tags.of("com.example.imagenode").value_set("needs-encoders");       // {"clip-l", "t5xxl"}: another owner's, as items

library.tag(&entry, "context=32768")?;                   // a key has one value: setting it again replaces it
library.untag(&entry, "context")?;
library.untag_all(&entry)?;                             // all of chatrun's tags of the model, nobody else's
library.tagged("arch")?;                                // every model chatrun tagged with the key
library.tagged("arch=qwen3")?;                          // with exactly that value
library.tagged_with("needs", "t5xxl")?;                 // with that item in the value
library.tagged_by("com.example.imagenode", "role=lora")?;           // another owner's tags
library.search("qwen3 32768");                          // words in ids, file names and every owner's tags
```

## The ideas, one at a time

**Locations.** A location is a folder that may hold models, with a *kind* saying how to read it: `directory` (a
folder of your own, or a cache in the Hugging Face or llama.cpp layout, walked a few levels deep), or one of the
stores, `ollama`, `lmstudio`, `gpt4all`, `modelscope`, `jan`, `docker`, `ramalama`, each read by its own layout.
They come from the person's configuration file, from `TENSTAG_PATH`, from the built-in list of places those programs
use by default, and from your program.

**Entries.** Each model found is an entry: an `id` unique on the machine (`Qwen/Qwen3-0.6B-GGUF:Q8_0`,
`ollama:qwen3:0.6b`, `loras/style/ink.safetensors`), the `path` your program opens, its `format` (a GGUF file, a
Hugging Face model folder, a single safetensors or checkpoint file, a diffusers pipeline, an adapter), its quant tag
if its name has one, its size, and `files()`, every file that belongs to it. A split model is one entry. The same
file reached twice, through two locations or a link, is one entry.

**Names.** `resolve` tries a name as a path, then a nickname from the configuration, then an exact id, then a Hugging
Face repository name (the model the cache holds, chosen as llama.cpp chooses), then a search where every word must
match. It never downloads and never guesses between matches.

**Identity.** A model's identity is a fingerprint of its contents, `tfp1:` and 64 hex digits. Hashing a whole 40 GB
file takes minutes on a hard disk, so the fingerprint reads at most about 33 MiB: the file's size, its first 16 MiB
(where a GGUF file keeps its names, quantisation and tokenizer), its last 1 MiB, and 4,096 small blocks spread evenly
between. A model of several files is identified by its files together, leaving out model cards and licences.
Fingerprints are remembered by path, size and modification time, and on Linux and macOS by the file's identity on
disk, so a model is read once, and a model moved on the same disk is not read again.

**Tags.** A tag is a word or a key and a value (`arch=qwen3`), with an owner, the program that wrote it (a reverse
domain name or a GitHub `user/repository`), and that program's version. Each of an owner's keys has one value. `value` gives it exactly as written; `value_set` gives its
comma-separated items. Owner names are lowercase letters, digits, `-`, `_`, `.` and `/`; keys are free text without
spaces.

**One cache folder.** Fingerprints and tags are both kept in the cache folder (`~/.cache/tenstag` on Linux), as plain,
documented files that any program, in any language, can read: one small JSON file per tagged model, and one file of
fingerprints.

## Questions developers ask

**How much of a model does it read, and when?** Listing and naming read no model data at all, only file names, sizes,
links and the stores' manifests (and four bytes of an Ollama blob, to tell a GGUF file). Fingerprinting reads at most
about 33 MiB per file, once, when you first ask for something that needs the identity: `tags`, `tag`, `identity`,
`tagged`. `search` reads tags only for models already fingerprinted, so it never reads a model. `verify` reads every
byte, because that is what it is for.

**What if the cache is deleted?** Every model's tags are gone, and the fingerprints with them. Your program's next
scan finds the tags missing and works them out again, reading each model once more. That is the design: nothing in
the cache is the only copy of anything.

**What happens when a model changes?** A model whose bytes change is a different model, with a new identity and no
tags, and your program works its tags out again, as it should, because the old ones described other bytes. A
fingerprint that samples cannot see every byte: an edit in place that keeps the size and falls only between the
sampled blocks is missed. Models are not edited in place in practice (a fine-tune or a requantisation is a new file),
but when every byte matters, `verify` computes a full SHA-256.

**The same model in two places?** One identity, one set of tags. A model downloaded through LM Studio and the same
file in the Hugging Face cache share their tags, because they are the same bytes, so your program works it out once.

**Can two programs tag at once?** Yes. Each write takes a lock on that model's tag file, rereads it, changes only that
program's own tags, and replaces the file whole, so readers never see half a file, and one program's write does not
change another's tags.

**Where does my program's own folder of models fit?** Give it to tenstag with no configuration at all:
`Locations::bare()`, then `locations.add(Location::folder("/srv/myapp/models").depth(3))`. Your models are found,
named and tagged like everyone else's, and nothing in the person's configuration can break your program's view of
its own folder. Or start from `Locations::load()` and add your folder to the person's places, as chatrun does.

**How fast is it?** Listing is file system work (folder listings, sizes, a few small manifest files), with no model
data read. A first fingerprint takes well under a second per file on an SSD, and longer on a hard disk (not yet
measured); after that it is a lookup. Measured: a 4 GiB file fingerprinted in 0.55 s from an NVMe disk with nothing in
memory, against 9.4 s for a full SHA-256.

**What about the store layouts changing?** Each store's layout is written down, with the source it was read from, in
[specs/stores/](specs/stores/README.md), and every rule the code follows cites it. When a program changes its layout,
the document changes first, and the implementations follow. Each release pins the commit it follows.

**Which languages and systems?** Rust and Python (pure Python, the standard library only), both written to this
specification and run against the same test cases, so both read and write the same files; a program in one language
sees the tags a program in the other wrote. Linux is where it is run and tested today; Windows and macOS builds
are compiled and checked on every change, and their folder rules come from the specifications, but they have not yet
been run there.

**Does it send anything anywhere?** No. It opens no network connection.

## One configuration for many programs

Everything so far works with no configuration: tenstag finds the places the common tools use by default. When a
person runs several programs that use models (a chat runner, an image tool, a benchmark), tenstag is also the one
place to tell all of them where the models are. The person writes one configuration file, and every program using
tenstag sees the same models under the same names, and the same cache of what has been worked out about them.

### The configuration file

It is `~/.config/tenstag/config.toml` (`$XDG_CONFIG_HOME/tenstag/config.toml` if that is set, or the file named by
`TENSTAG_CONFIG`). Everything in it is optional:

```toml
# Also look in the places the common tools use by default (the Hugging Face cache, llama.cpp's cache,
# LM Studio, Ollama, GPT4All, ModelScope, Jan, Docker Model Runner, RamaLama). false: only what is listed here.
defaults = true

# A big disk of models arranged by hand.
[[location]]
path = "/mnt/nas/models"
depth = 8                 # how many folder levels to look down (6 by default)

# An image tool's models folder: each file listed with its path below the folder,
# such as unet/flux1-dev-Q4_K_S.gguf or loras/style/ink.safetensors.
[[location]]
path = "~/imagenode/models"
depth = 8
min_size = 0              # also list safetensors files under 1 MiB (small LoRAs, embeddings)

# Another program's store somewhere other than its default.
[[location]]
path = "/srv/ollama/models"
kind = "ollama"           # or lmstudio, gpt4all, modelscope, jan, docker, ramalama

# Nicknames: a short name for any name, used in every program.
[names]
small = "Qwen/Qwen3-0.6B-GGUF:Q8_0"
coder = "qwen2.5 coder 7b q4"
```

A mistake in the file (a key it does not have, a value of the wrong type, `depth` on a store read by its own layout)
is an error that names the file and the key, never silently ignored: the file says what the person wants, so tenstag
does not half-do it.

A program can also change the file for the person: add a folder (`tensrun models --add /data/models`, say), remove
one, or turn the defaults off. tenstag changes only the lines it must, keeps the person's comments and order, and
refuses a file it cannot change safely rather than rewrite it. A folder a program adds records which program and when:

```toml
[[location]]
path = "/data/models"
added_by = "goldnode/tensrun"
added = 2026-11-24T18:48:18Z
```

so another program, or the person, can see where it came from before removing it. Whether to ask first is each
program's choice.

### Environment variables

| variable | what it does |
|---|---|
| `TENSTAG_CONFIG` | use this configuration file |
| `TENSTAG_PATH` | more folders of your own, `:`-separated (`;` on Windows), read after the file's |
| `TENSTAG_CACHE_DIR` | keep fingerprints and tags here (an absolute path) |

The tools' own variables are respected too, so tenstag looks where they put things: `HF_HUB_CACHE` and `HF_HOME`,
`LLAMA_CACHE`, `OLLAMA_MODELS`, `MODELSCOPE_CACHE`, `JAN_DATA_FOLDER`, `MODELS_PATH` for Docker, `RAMALAMA_STORE`,
and the settings files of LM Studio, GPT4All, Jan and RamaLama.

### Where it looks, in order

1. the configuration file's locations, as written;
2. `TENSTAG_PATH`'s folders;
3. the built-in places, unless `defaults = false`: the Hugging Face cache, llama.cpp's cache, LM Studio, GPT4All,
   ModelScope, Jan, Docker Model Runner, RamaLama, then Ollama (and on Linux the Ollama service's own store);
4. the folders each program adds for itself.

A folder listed twice is read once. A model reached through two locations is listed once, under its first name. Two
different models with the same name in two locations are told apart by the folder's path in front of the second
one's id. Programs can describe all of this for a person (each location, which layer gave it, whether it exists),
which is the first thing to look at when a model is not where someone expects.

### What the shared cache gives a system of programs

Because every program's tags are kept in one cache, programs benefit from each other's work without knowing about each
other: imagenode's `encoder=qwen2.5-vl-7b` tells a chat runner what that file is; a benchmark's `tps@rtx4090`, read
by its owner's name, lets a runner pick the fastest quantisation. Each program still works out, and tags again, what
it needs when it finds it missing, so no program depends on another having run first.

Clearing the cache folder is always safe: each program works out its tags again at its next scan. Moving a model to
another folder, renaming it, or copying it to another disk keeps its tags, because they belong to its contents.

## Where to go next

- The specification, in [specs/](specs/): exactly what every implementation does, with test vectors. Start with
  [listing.md](specs/listing.md) and [names.md](specs/names.md) for what a program sees, and [tags.md](specs/tags.md)
  for tags.
- tenstag-rust: its README to add it to a program, and its USAGE.md for every call.
- tenstag-python: its README to add it to a program (`pip install`), and its USAGE.md for every call.
