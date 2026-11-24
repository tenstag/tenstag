#!/usr/bin/env python3
"""The reference implementation of tenstag's specifications, and the generator of their test vectors.

  python3 tools/reference.py fingerprint <file>...     print each file's tfp1 identity
  python3 tools/reference.py vectors                   rewrite specs/test-vectors/*.json
  python3 tools/reference.py check                     check specs/test-vectors/*.json against this code

It follows specs/fingerprint.md (TFP), specs/tags.md (TAG) and specs/tag-store.md (TGS) as written, as plainly as
possible, so that an implementation in another language can be compared with it line by line. It is not fast.

Test files are generated, not stored (some are over 33 MiB): `content(seed, size)` is the SHA-256 of the seed and a
block counter, each as an unsigned 64-bit little-endian integer, for block 0, 1, 2 ..., joined and cut to `size`
bytes. An implementation's tests generate the same bytes into a temporary file and compare its identity.
"""
import hashlib
import json
import os
import pathlib
import struct
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
VECTORS = ROOT / "specs" / "test-vectors"

# TFP-002
HEAD = 16 << 20
TAIL = 1 << 20
BLOCK = 4096
SAMPLES = 4096
WHOLE = HEAD + TAIL + SAMPLES * BLOCK
MASK = (1 << 64) - 1


def u64(n):
    return struct.pack("<Q", n)


def splitmix64(state):
    """TFP-005: the generator, seeded with `state`; yields its outputs."""
    while True:
        state = (state + 0x9E3779B97F4A7C15) & MASK
        z = state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        yield z ^ (z >> 31)


def sample_offsets(size):
    """TFP-004: the offsets of the chosen blocks of a file of `size` bytes (more than WHOLE), in order."""
    m = (size - HEAD - TAIL) // BLOCK
    rng = splitmix64(size)
    offsets = []
    for i in range(SAMPLES):
        lo, hi = i * m // SAMPLES, (i + 1) * m // SAMPLES
        offsets.append(HEAD + (lo + next(rng) % (hi - lo)) * BLOCK)
    return offsets


def read_exactly(f, n):
    data = f.read(n)
    if len(data) != n:
        raise OSError("the file is shorter than its size (TFP-006)")
    return data


def fingerprint_digest(path):
    """TFP-003, TFP-004: the 32-byte digest of the file at `path`."""
    with open(path, "rb") as f:
        size = os.fstat(f.fileno()).st_size
        h = hashlib.sha256(b"tfp1" + u64(size))
        if size <= WHOLE:
            h.update(read_exactly(f, size))
        else:
            h.update(read_exactly(f, HEAD))
            for offset in sample_offsets(size):
                f.seek(offset)
                h.update(read_exactly(f, BLOCK))
            f.seek(size - TAIL)
            h.update(read_exactly(f, TAIL))
        if os.fstat(f.fileno()).st_size != size:
            raise OSError("the file changed while it was read (TFP-006)")
    return h.digest()


def fingerprint(path):
    """TFP-001: the identity of the file at `path`."""
    return "tfp1:" + fingerprint_digest(path).hex()


def is_member(name):
    """TFP-007: whether a file with this name (the last part of its path) is a member of a model of several files."""
    lower = name.lower()
    return not (lower.endswith(".md") or lower.startswith("license") or lower.startswith("licence")
                or name.startswith("."))


def set_identity(members):
    """TFP-007: the identity of a model whose members have the identities `members` (already filtered)."""
    if not members:
        return None
    if len(members) == 1:
        return members[0]
    digests = sorted(bytes.fromhex(m.removeprefix("tfp1:")) for m in members)
    return "tfp1:" + hashlib.sha256(b"tfp1-set" + u64(len(digests)) + b"".join(digests)).hexdigest()


def store_sha256(path, folders=()):
    """TFC-006: the SHA-256 the store names the file at the real path `path` by (a '/'-separated text), or None.

    `folders` are the folders that exist beside the file's `blobs` folder's parent: what tells Ollama from RamaLama.
    """
    parts = path.split("/")
    if len(parts) < 3:
        return None
    name, parent, grand = parts[-1], parts[-2], parts[-3]
    hex64 = lambda t: len(t) == 64 and all(c in "0123456789abcdef" for c in t)
    if parent == "blobs" and grand.startswith("models--") and hex64(name):
        return name
    if parent == "blobs" and name.startswith("sha256-") and hex64(name[7:]) and "manifests" in folders:
        return name[7:]
    if parent == "sha256" and grand == "blobs" and hex64(name):
        return name
    return None


# TAG-002: the characters no key may hold (besides "="), and no value may hold (CONTROLS only).
CONTROLS = {chr(c) for c in [*range(0x00, 0x20), 0x7F, *range(0x80, 0xA0)]}
SPACES = {chr(c) for c in [0x20, 0xA0, 0x1680, *range(0x2000, 0x200B), 0x2028, 0x2029, 0x202F, 0x205F, 0x3000]}


def parse_tag(text):
    """TAG-001 to TAG-003: (key, value or None), or raise ValueError saying why the text is not a tag."""
    key, sep, value = text.partition("=")
    if not 1 <= len(key.encode()) <= 256:
        raise ValueError("a key is 1 to 256 bytes")
    if any(c in CONTROLS or c in SPACES for c in key):
        raise ValueError("a key holds no space or control character")
    if not sep:
        return key, None
    if not 1 <= len(value.encode()) <= 4096:
        raise ValueError("a value is 1 to 4096 bytes")
    if any(c in CONTROLS for c in value):
        raise ValueError("a value holds no control character")
    return key, value


def is_owner(name):
    """TAG-009: whether `name` is an owner name."""
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_./")
    return (1 <= len(name.encode()) <= 128 and set(name) <= allowed and name[0] not in "-_./"
            and not name.endswith("/") and "//" not in name)


def value_set(value):
    """TAG-006: the value set of `value` (None for a word)."""
    if value is None:
        return set()
    return {part.strip(" ") for part in value.split(",")} - {""}


def apply(tags, text):
    """TAG-004: `tags` (a dict) with the tag `text` set."""
    key, value = parse_tag(text)
    return {**tags, key: value}


def content(seed, size):
    """The bytes of a generated test file (the module's docstring)."""
    out = bytearray()
    i = 0
    while len(out) < size:
        out += hashlib.sha256(u64(seed) + u64(i)).digest()
        i += 1
    return bytes(out[:size])


def generated(seed, size, edit=None):
    """A temporary file of `content(seed, size)`, with `edit` ({offset, byte}) applied; its path."""
    data = bytearray(content(seed, size))
    if edit:
        data[edit["offset"]] = edit["byte"]
    f = tempfile.NamedTemporaryFile(delete=False, prefix="tenstag-vector-")
    f.write(data)
    f.close()
    return f.name


FILES = [
    # name, seed, size, edit, why
    ("empty", 1, 0, None, "an empty file: the prefix and a size of 0"),
    ("one byte", 2, 1, None, "a file read whole"),
    ("one block", 3, 4096, None, "a file read whole"),
    ("whole", 4, WHOLE, None, "the largest file read whole (TFP-003)"),
    ("whole + 1", 5, WHOLE + 1, None, "the smallest file sampled (TFP-004): every run is one block"),
    ("40 MiB + 123", 6, (40 << 20) + 123, None, "a sampled file whose tail is not aligned to a block"),
    ("40 MiB + 123, edited in a sampled block", 6, (40 << 20) + 123, "sampled",
     "one byte changed in the first chosen block: a different identity"),
    ("40 MiB + 123, edited between samples", 6, (40 << 20) + 123, "unsampled",
     "one byte changed in a block no run chose: the same identity (fingerprint.md, What it misses)"),
    ("100 MiB", 7, 100 << 20, None, "a larger sampled file"),
]


def file_vectors():
    out = []
    for name, seed, size, edit, why in FILES:
        if edit == "sampled":
            edit = {"offset": sample_offsets(size)[0] + 7, "byte": 0}
        elif edit == "unsampled":
            chosen = set(sample_offsets(size))
            block = next(o for o in range(HEAD, size - TAIL - BLOCK, BLOCK) if o not in chosen)
            edit = {"offset": block + 7, "byte": 0}
        if edit:
            edit["byte"] = content(seed, size)[edit["offset"]] ^ 0xFF
        path = generated(seed, size, edit)
        try:
            vector = {"name": name, "why": why, "seed": seed, "size": size}
            if edit:
                vector["edit"] = edit
            vector["identity"] = fingerprint(path)
            if size > WHOLE:
                offsets = sample_offsets(size)
                vector["samples"] = {"first": offsets[:4], "last": offsets[-4:]}
            out.append(vector)
        finally:
            os.unlink(path)
    return out


def fingerprint_vectors():
    files = file_vectors()
    ids = {v["name"]: v["identity"] for v in files}
    sets = [
        {"why": "no members: no identity", "members": [], "identity": None},
        {"why": "one member: its own identity", "members": [ids["one byte"]], "identity": ids["one byte"]},
        {"why": "two members", "members": [ids["one byte"], ids["one block"]],
         "identity": set_identity([ids["one byte"], ids["one block"]])},
        {"why": "the same two in the other order: the same identity", "members": [ids["one block"], ids["one byte"]],
         "identity": set_identity([ids["one byte"], ids["one block"]])},
        {"why": "a member twice counts twice", "members": [ids["one byte"], ids["one byte"]],
         "identity": set_identity([ids["one byte"], ids["one byte"]])},
    ]
    names = [
        ("model.safetensors", True), ("config.json", True), ("README.md", False), ("notes.MD", False),
        ("LICENSE", False), ("license.txt", False), ("LICENCE-MIT", False), (".gitattributes", False),
        ("tokenizer.json", True), ("my.md.bin", True),
    ]
    assert all(is_member(n) == m for n, m in names)
    rng = splitmix64(0)
    first = [next(rng) for _ in range(3)]
    return {
        "about": "specs/fingerprint.md; files are generated as tools/reference.py `content` describes",
        "splitmix64": {"seed": 0, "first": [str(x) for x in first]},
        "files": files,
        "sets": sets,
        "members": [{"name": n, "member": m} for n, m in names],
    }


def tag_vectors():
    cases = [
        "favourite", "lang=en,fr", "a=b=c", "tensrun/architecture=qwen3", "Lang=EN", "key=with spaces inside",
        "", "=x", "lang=", "two words", "tab\there", "nbsp key", "k=line\nbreak", "k" * 256, "k" * 257,
        "k=" + "v" * 4096, "k=" + "v" * 4097, "ключ=значение", "é" * 128, "é" * 129,
    ]
    parsed = []
    for text in cases:
        try:
            key, value = parse_tag(text)
            parsed.append({"text": text, "key": key, "value": value})
        except ValueError as e:
            parsed.append({"text": text, "error": str(e)})
    sets = [(v, sorted(value_set(v))) for v in [None, "en", "en,fr", "en, fr,,en", " , ", "a b, c", "x=y,z"]]
    steps, tags, applied = ["lang=en,fr", "favourite", "lang=de", "lang", "lang=x", "favourite=yes"], {}, []
    for step in steps:
        tags = apply(tags, step)
        applied.append({"set": step, "tags": dict(sorted(tags.items()))})
    owners = [(o, is_owner(o)) for o in ["chatrun", "image-node", "com.example.chatrun", "example/chatrun",
                                          "example-org/chat.run_2", "a_1", "9b", "Chatrun", "Example/Chatrun", "-x",
                                          ".x", "_x", "/x", "x/", "a//b", "", "a b", "é", "a" * 128, "a" * 129,
                                          "a/" + "b" * 126, "a/" + "b" * 127]]
    # TAG-010: what an owner at a version sees of its own tags, written at another.
    versions = [{"written": 2, "reading": 2, "sees": True}, {"written": 1, "reading": 2, "sees": False},
                {"written": 3, "reading": 2, "sees": False}]
    return {
        "about": "specs/tags.md",
        "parse": parsed,
        "owners": [{"name": o, "owner": ok} for o, ok in owners],
        "versions": versions,
        "value_set": [{"value": v, "set": s} for v, s in sets],
        "replace": applied,
    }


def store_vectors():
    identity = "tfp1:" + "ab" * 32
    owners = {"chatrun": {"version": 2, "tags": {"arch": "qwen3", "chat": None}},
              "imagenode": {"version": 1, "tags": {"encoder": "qwen2.5-vl-7b"}}}
    good = {"format": "tenstag-tags/2", "identity": identity, "tags": owners, "bytes": 3,
            "seen": [{"path": "/models/a.gguf", "time": "2026-11-23T14:02:11Z"}]}
    with_owners = lambda o: {**good, "tags": o}
    raw = lambda tags: ('{"format": "tenstag-tags/2", "identity": "%s", "tags": %s, "bytes": 3, "seen": []}'
                        % (identity, tags))
    return {
        "about": "specs/tag-store.md TGS-003, TGS-004: each file text, as read from tags/tfp1/<name>.json; `tags` is "
                 "each owner's version and tags, or null for no tags",
        "files": [
            {"why": "a good file", "name": "ab" * 32, "text": json.dumps(good, indent=2), "tags": owners},
            {"why": "an unknown top-level key is allowed", "name": "ab" * 32,
             "text": json.dumps({**good, "x-other": 1}), "tags": owners},
            {"why": "the identity does not match the name", "name": "cd" * 32, "text": json.dumps(good), "tags": None},
            {"why": "format 1, without owners: no tags (it is replaced at the next write)", "name": "ab" * 32,
             "text": json.dumps({"format": "tenstag-tags/1", "identity": identity, "tags": {"arch": "qwen3"},
                                 "bytes": 3, "seen": []}), "tags": None},
            {"why": "another format", "name": "ab" * 32, "text": json.dumps({**good, "format": "tenstag-tags/3"}),
             "tags": None},
            {"why": "an owner twice", "name": "ab" * 32,
             "text": raw('{"a": {"version": 0, "tags": {}}, "a": {"version": 0, "tags": {}}}'), "tags": None},
            {"why": "a key twice in an owner's tags", "name": "ab" * 32,
             "text": raw('{"a": {"version": 0, "tags": {"k": null, "k": "v"}}}'), "tags": None},
            {"why": "an owner name that is not one", "name": "ab" * 32,
             "text": json.dumps(with_owners({"Chat Run": {"version": 0, "tags": {}}})), "tags": None},
            {"why": "a version that is not a whole number", "name": "ab" * 32,
             "text": json.dumps(with_owners({"a": {"version": "2", "tags": {}}})), "tags": None},
            {"why": "a version out of range", "name": "ab" * 32,
             "text": json.dumps(with_owners({"a": {"version": 4294967296, "tags": {}}})), "tags": None},
            {"why": "a key that is not a key", "name": "ab" * 32,
             "text": json.dumps(with_owners({"a": {"version": 0, "tags": {"two words": None}}})), "tags": None},
            {"why": "an empty value", "name": "ab" * 32,
             "text": json.dumps(with_owners({"a": {"version": 0, "tags": {"lang": ""}}})), "tags": None},
            {"why": "not JSON", "name": "ab" * 32, "text": "{", "tags": None},
        ],
    }


def no_duplicates(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError("a key appears twice")
    return dict(pairs)


def read_store_file(name, text):
    """TGS-004: the owners' tags of a file named `<name>.json` holding `text` ({owner: {version, tags}}), or None
    when it is to be treated as none."""
    try:
        f = json.loads(text, object_pairs_hook=no_duplicates)
        if f.get("format") != "tenstag-tags/2" or f.get("identity") != "tfp1:" + name:
            return None
        owners = f.get("tags")
        if not isinstance(owners, dict):
            return None
        for owner, group in owners.items():
            if not is_owner(owner) or not isinstance(group, dict):
                return None
            version, tags = group.get("version"), group.get("tags")
            if type(version) is not int or not 0 <= version < 1 << 32 or not isinstance(tags, dict):
                return None
            for key, value in tags.items():
                if value is not None and not isinstance(value, str):
                    return None
                if parse_tag(key if value is None else f"{key}={value}") != (key, value):
                    return None
        return owners
    except ValueError:
        return None


def digest_vectors():
    h, g = "ab" * 32, "cd" * 20
    cases = [
        ("the Hugging Face cache, an LFS blob", f"/c/hub/models--Qwen--Qwen3-0.6B-GGUF/blobs/{h}", [], h),
        ("the Hugging Face cache, a git blob (SHA-1)", f"/c/hub/models--Qwen--Qwen3-0.6B-GGUF/blobs/{g}", [], None),
        ("a blobs folder not in a models-- folder", f"/c/other/blobs/{h}", [], None),
        ("upper-case hex", f"/c/hub/models--a--b/blobs/{h.upper()}", [], None),
        ("Ollama", f"/o/models/blobs/sha256-{h}", ["blobs", "manifests"], h),
        ("Ollama, a download in progress", f"/o/models/blobs/sha256-{h}-partial", ["blobs", "manifests"], None),
        ("RamaLama (refs and snapshots, no manifests)", f"/r/store/huggingface/Qwen/M/blobs/sha256-{h}",
         ["blobs", "refs", "snapshots"], None),
        ("Docker Model Runner, sha256", f"/d/models/blobs/sha256/{h}", [], h),
        ("Docker Model Runner, sha512", f"/d/models/blobs/sha512/{h + h}", [], None),
        ("Docker Model Runner, incomplete", f"/d/models/blobs/sha256/{h}.incomplete", [], None),
        ("a plain file", "/m/Qwen3-0.6B-Q8_0.gguf", [], None),
    ]
    out = []
    for why, path, folders, want in cases:
        assert store_sha256(path, folders) == want, why
        out.append({"why": why, "path": path, "beside": folders, "sha256": want})
    return {"about": "specs/fingerprint-cache.md TFC-006: `beside` lists the folders in the folder that holds `blobs`",
            "paths": out}


def all_vectors():
    return {"fingerprint.json": fingerprint_vectors(), "tags.json": tag_vectors(), "tag-store.json": store_vectors(),
            "store-digests.json": digest_vectors()}


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "fingerprint":
        for path in sys.argv[2:]:
            print(fingerprint(path), path)
    elif command in ("vectors", "check"):
        vectors = all_vectors()
        for f in vectors["tag-store.json"]["files"]:
            assert read_store_file(f["name"], f["text"]) == f["tags"], f["why"]
        problems = 0
        for name, value in vectors.items():
            text = json.dumps(value, indent=1, ensure_ascii=False) + "\n"
            path = VECTORS / name
            if command == "vectors":
                VECTORS.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
                print(f"wrote {path.relative_to(ROOT)}")
            elif not path.is_file() or path.read_text() != text:
                print(f"{path.relative_to(ROOT)} differs from what this code gives")
                problems += 1
        if command == "check":
            print(f"{len(vectors)} vector files, {problems} problems")
            sys.exit(1 if problems else 0)
    else:
        print(__doc__, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
