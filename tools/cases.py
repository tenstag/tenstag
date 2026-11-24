#!/usr/bin/env python3
"""Writes the hand-written test vectors of configuration.md, locations.md, listing.md and names.md.

  python3 tools/cases.py            rewrite specs/test-vectors/{configuration,config-writing,listing,names}.json
  python3 tools/cases.py check      check they are what this file says

Unlike tools/reference.py, nothing here computes an answer: every expected result is written out by hand from the
specification, and this file only spells the cases in a compact way. An implementation's tests build each case's
files in an empty folder and compare.

Files, in a case's `files`, relative to the case's folder:
  {"path": p, "size": n}       n zero bytes
  {"path": p, "text": t}       the UTF-8 text t
  {"path": p, "json": v}       v as JSON
  {"path": p, "link": t}       a symbolic link to t (relative to the link's folder); cases with links run on Unix only
`{root}` in any string is the case's folder, as an absolute path with `/` separators.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
VECTORS = ROOT / "specs" / "test-vectors"
MIB = 1 << 20


def size(path, n):
    return {"path": path, "size": n}


def text(path, t):
    return {"path": path, "text": t}


def js(path, v):
    return {"path": path, "json": v}


def link(path, target):
    return {"path": path, "link": target}


def entry(id, format, path, files=None, quant="", bytes=0, **more):
    e = {"id": id, "format": format, "quant": quant, "bytes": bytes, "path": path, "files": [path] if files is None else files}
    e.update(more)
    return e


# ---------------------------------------------------------------------------------------------------------- listing

def walk_case():
    m = "models"
    files = [
        size(f"{m}/qwen3-0.6b-Q8_0.gguf", 10),
        size(f"{m}/big/Big-Q4_K_M-00001-of-00002.gguf", 3),
        size(f"{m}/big/Big-Q4_K_M-00002-of-00002.gguf", 4),
        size(f"{m}/big/mmproj-Big-F16.gguf", 2),
        size(f"{m}/big/Big-imatrix.gguf", 2),
        size(f"{m}/half/H-00001-of-00002.gguf", 1),
        size(f"{m}/empty-Q8_0.gguf", 0),
        size(f"{m}/.hidden/x-Q8_0.gguf", 1),
        size(f"{m}/node_modules/y-Q8_0.gguf", 1),
        text(f"{m}/venv/pyvenv.cfg", "home = /usr\n"),
        size(f"{m}/venv/z-Q8_0.gguf", 1),
        size(f"{m}/a/b/c/d/e/f/deep.gguf", 1),
        size(f"{m}/a/b/c/d/e/ok.gguf", 1),
        size(f"{m}/sd/sd_xl.safetensors", MIB),
        size(f"{m}/sd/tiny.safetensors", 5),
        size(f"{m}/sd/v1.CKPT", MIB),
        size(f"{m}/sd/state.pt", MIB),
        size(f"{m}/st/m-00001-of-00002.safetensors", 600_000),
        size(f"{m}/st/m-00002-of-00002.safetensors", 600_000),
        text(f"{m}/tiny/config.json", "{}"),
        size(f"{m}/tiny/model.safetensors", 3),
        size(f"{m}/tiny/inner-Q8_0.gguf", 2),
        text(f"{m}/tiny/README.md", "a card"),
        text(f"{m}/pipe/model_index.json", "{}"),
        size(f"{m}/pipe/unet/diffusion_pytorch_model.safetensors", 4),
        size(f"{m}/pipe/vae/diffusion_pytorch_model.bin", 2),
        size(f"{m}/pipe/.cache/x.safetensors", 9),
        text(f"{m}/lora/adapter_config.json", "{}"),
        size(f"{m}/lora/adapter_model.safetensors", 3),
        link(f"{m}/sub/loop", ".."),
    ]
    entries = [
        entry("a/b/c/d/e/ok", "gguf", f"{m}/a/b/c/d/e/ok.gguf", bytes=1),
        entry("big/Big-Q4_K_M-00001-of-00002", "gguf", f"{m}/big/Big-Q4_K_M-00001-of-00002.gguf",
              [f"{m}/big/Big-Q4_K_M-00001-of-00002.gguf", f"{m}/big/Big-Q4_K_M-00002-of-00002.gguf"],
              quant="Q4_K_M", bytes=7),
        entry("lora", "adapter", f"{m}/lora", [f"{m}/lora/adapter_config.json", f"{m}/lora/adapter_model.safetensors"],
              bytes=3),
        entry("pipe", "diffusers", f"{m}/pipe",
              [f"{m}/pipe/model_index.json", f"{m}/pipe/unet/diffusion_pytorch_model.safetensors",
               f"{m}/pipe/vae/diffusion_pytorch_model.bin"], bytes=6),
        entry("qwen3-0.6b-Q8_0", "gguf", f"{m}/qwen3-0.6b-Q8_0.gguf", quant="Q8_0", bytes=10),
        entry("sd/sd_xl.safetensors", "safetensors", f"{m}/sd/sd_xl.safetensors", bytes=MIB),
        entry("sd/v1.CKPT", "checkpoint", f"{m}/sd/v1.CKPT", bytes=MIB),
        entry("st/m-00001-of-00002.safetensors", "safetensors", f"{m}/st/m-00001-of-00002.safetensors",
              [f"{m}/st/m-00001-of-00002.safetensors", f"{m}/st/m-00002-of-00002.safetensors"], bytes=1_200_000),
        entry("tiny", "hf-directory", f"{m}/tiny",
              [f"{m}/tiny/README.md", f"{m}/tiny/config.json", f"{m}/tiny/inner-Q8_0.gguf", f"{m}/tiny/model.safetensors"],
              bytes=3),
    ]
    resolve = [
        {"name": "qwen3", "id": "qwen3-0.6b-Q8_0"},
        {"name": "q4_k_m", "id": "big/Big-Q4_K_M-00001-of-00002"},
        {"name": "TINY", "id": "tiny"},
        {"name": "sd", "error": "ambiguous"},
        {"name": "mistral", "error": "not found"},
        {"name": "{root}/models/sd/state.pt", "id": "{root}/models/sd/state.pt", "format": "checkpoint"},
        {"name": "{root}/models/sd/tiny.safetensors", "id": "{root}/models/sd/tiny.safetensors",
         "format": "safetensors"},
        {"name": "{root}/models/venv/pyvenv.cfg", "error": "not found"},
    ]
    return {"why": "LST-002 to LST-004, LST-006, LST-017: the walk of a folder of your own",
            "files": files, "locations": [{"path": m, "kind": "directory"}], "entries": entries, "resolve": resolve}


def depth_and_size_case():
    return {
        "why": "CFG-004 depth and LST-004 min_size on a location",
        "files": [size("f/a/b/m.gguf", 1), size("f/a/n.gguf", 1), size("f/small.safetensors", 10)],
        "locations": [{"path": "f", "kind": "directory", "depth": 2, "min_size": 0}],
        "entries": [entry("a/n", "gguf", "f/a/n.gguf", bytes=1),
                    entry("small.safetensors", "safetensors", "f/small.safetensors", bytes=10)],
        "resolve": [],
    }


def hub_case():
    a, b, c, d, e, f, g = ("a" * 40, "b" * 40, "c" * 40, "d" * 40, "e" * 40, "f" * 40, "1" * 40)
    r = "hub/models--Org--M-GGUF"
    files = [
        text(f"{r}/refs/main", a), text(f"{r}/refs/v1", b), text(f"{r}/refs/abc1234", b + "\n"),
        size(f"{r}/blobs/q4", 2), link(f"{r}/snapshots/{a}/M-Q4_K_M.gguf", "../../blobs/q4"),
        size(f"{r}/snapshots/{a}/M-Q8_0.gguf", 3),
        size(f"{r}/snapshots/{a}/M-F16.gguf.incomplete", 1),
        size(f"{r}/snapshots/{a}/mmproj-F16.gguf", 1),
        size(f"{r}/snapshots/{b}/M-Q8_0.gguf", 4),
        size(f"{r}/snapshots/{c}/M-Q8_0.gguf", 5),
        text(f"hub/models--Org--D/refs/main", d),
        text(f"hub/models--Org--D/snapshots/{d}/config.json", "{}"),
        size(f"hub/models--Org--D/snapshots/{d}/model.safetensors", 6),
        text(f"hub/models--Org--Pipe/refs/main", e),
        text(f"hub/models--Org--Pipe/snapshots/{e}/model_index.json", "{}"),
        size(f"hub/models--Org--Pipe/snapshots/{e}/unet/diffusion_pytorch_model.safetensors", 3),
        text(f"hub/models--Org--Single/refs/main", f),
        size(f"hub/models--Org--Single/snapshots/{f}/sd_xl_base.safetensors", 7),
        text(f"hub/models--Org--Single/snapshots/{f}/notes.txt", "x"),
        text(f"hub/models--Org--Two/refs/main", g),
        size(f"hub/models--Org--Two/snapshots/{g}/a/X-Q8_0.gguf", 1),
        size(f"hub/models--Org--Two/snapshots/{g}/b/Y-Q8_0.gguf", 2),
    ]
    s = lambda repo, commit: f"hub/models--{repo}/snapshots/{commit}"
    entries = [
        entry("Org/D", "hf-directory", s("Org--D", d), [f"{s('Org--D', d)}/config.json", f"{s('Org--D', d)}/model.safetensors"],
              bytes=6, hub={"repo": "Org/D", "commit": d, "refs": ["main"], "file": ""}),
        entry("Org/M-GGUF:Q4_K_M", "gguf", f"{s('Org--M-GGUF', a)}/M-Q4_K_M.gguf", quant="Q4_K_M", bytes=2,
              hub={"repo": "Org/M-GGUF", "commit": a, "refs": ["main"], "file": "M-Q4_K_M.gguf"}),
        entry("Org/M-GGUF:Q8_0", "gguf", f"{s('Org--M-GGUF', a)}/M-Q8_0.gguf", quant="Q8_0", bytes=3,
              hub={"repo": "Org/M-GGUF", "commit": a, "refs": ["main"], "file": "M-Q8_0.gguf"}),
        entry("Org/M-GGUF:Q8_0@abc1234", "gguf", f"{s('Org--M-GGUF', b)}/M-Q8_0.gguf", quant="Q8_0", bytes=4,
              hub={"repo": "Org/M-GGUF", "commit": b, "refs": ["abc1234", "v1"], "file": "M-Q8_0.gguf"}),
        entry(f"Org/M-GGUF:Q8_0@{c}", "gguf", f"{s('Org--M-GGUF', c)}/M-Q8_0.gguf", quant="Q8_0", bytes=5,
              hub={"repo": "Org/M-GGUF", "commit": c, "refs": [], "file": "M-Q8_0.gguf"}),
        entry("Org/Pipe", "diffusers", s("Org--Pipe", e),
              [f"{s('Org--Pipe', e)}/model_index.json", f"{s('Org--Pipe', e)}/unet/diffusion_pytorch_model.safetensors"],
              bytes=3, hub={"repo": "Org/Pipe", "commit": e, "refs": ["main"], "file": ""}),
        entry("Org/Single/sd_xl_base.safetensors", "safetensors", f"{s('Org--Single', f)}/sd_xl_base.safetensors", bytes=7,
              hub={"repo": "Org/Single", "commit": f, "refs": ["main"], "file": "sd_xl_base.safetensors"}),
        entry("Org/Two:Q8_0", "gguf", f"{s('Org--Two', g)}/a/X-Q8_0.gguf", quant="Q8_0", bytes=1,
              hub={"repo": "Org/Two", "commit": g, "refs": ["main"], "file": "a/X-Q8_0.gguf"}),
        entry("Org/Two/b/Y-Q8_0.gguf", "gguf", f"{s('Org--Two', g)}/b/Y-Q8_0.gguf", quant="Q8_0", bytes=2,
              hub={"repo": "Org/Two", "commit": g, "refs": ["main"], "file": "b/Y-Q8_0.gguf"}),
    ]
    resolve = [
        {"name": "Org/M-GGUF", "id": "Org/M-GGUF:Q4_K_M"},
        {"name": "hf.co/org/m-gguf", "id": "Org/M-GGUF:Q4_K_M"},
        {"name": "Org/M-GGUF:q8_0", "id": "Org/M-GGUF:Q8_0"},
        {"name": "Org/M-GGUF:Q4_K_M@v1", "error": "not found"},
        {"name": "Org/M-GGUF@v1", "id": "Org/M-GGUF:Q8_0@abc1234"},
        {"name": "Org/M-GGUF@abc1234", "id": "Org/M-GGUF:Q8_0@abc1234"},
        {"name": f"Org/M-GGUF@{c.upper()}", "id": f"Org/M-GGUF:Q8_0@{c}"},
        {"name": "Org/M-GGUF@ccccccc", "error": "not found"},
        {"name": "Org/D", "id": "Org/D"},
        {"name": "Org/Pipe", "id": "Org/Pipe"},
        {"name": "Org/Two:Q8_0", "id": "Org/Two:Q8_0"},
        {"name": "Org/Missing", "error": "not found"},
        {"name": "Org/Single/sd_xl_base.safetensors", "id": "Org/Single/sd_xl_base.safetensors"},
    ]
    return {"why": "LST-005, LST-006, NAM-003, NAM-004: the Hugging Face cache and the cached choice",
            "files": files, "locations": [{"path": "hub", "kind": "directory"}], "entries": entries, "resolve": resolve}


def llama_cpp_case():
    return {
        "why": "LST-014: llama.cpp's old flat files are named through their manifests only",
        "files": [
            size("cache/ggml-org_gemma-3-1b-it-GGUF_gemma-3-1b-it-Q4_K_M.gguf", 3),
            js("cache/manifest=ggml-org=gemma-3-1b-it-GGUF=latest.json",
               {"ggufFile": {"rfilename": "gemma-3-1b-it-Q4_K_M.gguf"}}),
            size("cache/some_user_repo_x-Q8_0.gguf", 2),
            size("cache/model-from-url.gguf", 1),
        ],
        "locations": [{"path": "cache", "kind": "directory"}],
        "entries": [
            entry("ggml-org/gemma-3-1b-it-GGUF:latest", "gguf",
                  "cache/ggml-org_gemma-3-1b-it-GGUF_gemma-3-1b-it-Q4_K_M.gguf", quant="Q4_K_M", bytes=3),
            entry("model-from-url", "gguf", "cache/model-from-url.gguf", quant="URL", bytes=1),  # llama.cpp's rule, LST-006
            entry("some_user_repo_x-Q8_0", "gguf", "cache/some_user_repo_x-Q8_0.gguf", quant="Q8_0", bytes=2),
        ],
        "resolve": [{"name": "ggml-org/gemma-3-1b-it-GGUF:latest", "id": "ggml-org/gemma-3-1b-it-GGUF:latest"}],
    }


def lm_studio_case():
    p = "lms/lmstudio-community/Qwen3-0.6B-GGUF"
    return {
        "why": "LST-007: LM Studio's models, three levels down, projectors left out",
        "files": [size(f"{p}/Qwen3-0.6B-Q8_0.gguf", 2), size(f"{p}/mmproj-Qwen3-0.6B-F16.gguf", 1),
                  size(f"{p}/MMPROJ-Qwen3-Q8_0.gguf", 1), size("lms/loose-Q8_0.gguf", 1),
                  size("lms/a/b/c/deep-Q8_0.gguf", 1)],
        "locations": [{"path": "lms", "kind": "lmstudio"}],
        "entries": [entry("lmstudio-community/Qwen3-0.6B-GGUF/Qwen3-0.6B-Q8_0", "gguf", f"{p}/Qwen3-0.6B-Q8_0.gguf",
                          quant="Q8_0", bytes=2)],
        "resolve": [],
    }


def ollama_case():
    h = lambda ch: ch * 64
    blob = lambda ch: f"o/blobs/sha256-{h(ch)}"
    digest = lambda ch: f"sha256:{h(ch)}"
    def manifest(config, layers):
        return {"schemaVersion": 2, "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                "config": {"digest": digest(config)},
                "layers": [{"mediaType": t, "digest": digest(ch), "size": 1} for t, ch in layers]}
    model, tensor = "application/vnd.ollama.image.model", "application/vnd.ollama.image.tensor"
    files = [
        text(blob("1"), "GGUF-one"), text(blob("2"), "GGUF-part-1"), text(blob("3"), "GGUF-part-2"),
        text(blob("4"), "nope"), text(blob("5"), "safetensors-bytes"),
        js(blob("a"), {"model_format": "gguf", "file_type": "Q4_K_M"}),
        js(blob("b"), {"file_type": "Q8_0"}),
        js(blob("c"), {"model_format": "safetensors", "file_type": "BF16"}),
        js(blob("d"), manifest("a", [(model, "1")])),
        js("o/manifests-v2/ollama.com/library/qwen3/0.6b", manifest("a", [(model, "1")])),
        js("o/manifests-v2/ollama.com/library/big/latest", manifest("a", [(model, "2"), (model, "3")])),
        js("o/manifests-v2/ollama.com/library/listed/latest",
           {"mediaType": "application/vnd.ollama.manifest.list.v2+json",
            "manifests": [{"format": "safetensors", "digest": digest("e")}, {"format": "gguf", "digest": digest("d")}]}),
        js("o/manifests/registry.ollama.ai/library/qwen3/0.6b", manifest("b", [(model, "4")])),
        js("o/manifests/registry.ollama.ai/library/old/7b", manifest("b", [(model, "1")])),
        js("o/manifests/registry.ollama.ai/user/st/latest", manifest("c", [(tensor, "5")])),
        js("o/manifests/registry.ollama.ai/user/st2/latest", manifest("c", [(tensor, "5"), (tensor, "f")])),
        js("o/manifests/example.com%3A5000/ns/m/v1", manifest("a", [(model, "1")])),
        js("o/manifests/example.com%3A5000/ns/bad/v1", manifest("a", [(model, "4")])),
    ]
    entries = [
        entry("ollama:big:latest", "gguf", blob("2"), [blob("2"), blob("3")], quant="Q4_K_M", bytes=22,
              parts=[blob("2"), blob("3")]),
        entry("ollama:listed:latest", "gguf", blob("1"), quant="Q4_K_M", bytes=8),
        entry("ollama:qwen3:0.6b", "gguf", blob("1"), quant="Q4_K_M", bytes=8),
        entry("ollama:example.com:5000/ns/m:v1", "gguf", blob("1"), quant="Q4_K_M", bytes=8),
        entry("ollama:old:7b", "gguf", blob("1"), quant="Q8_0", bytes=8),
        entry("ollama:user/st:latest", "other", "o/blobs", [], quant="BF16", bytes=17,
              note="an Ollama safetensors model, not a GGUF file"),
        entry("ollama:user/st2:latest", "other", "o/blobs", [], quant="BF16", bytes=17,
              note="an Ollama safetensors model, not a GGUF file"),  # LST-008: the missing tensor counts nothing
    ]
    return {"why": "LST-008: Ollama's two trees, a manifest list, a split model, a safetensors model, a blob that is "
                   "not GGUF; one file under several names in one location",
            "files": files, "locations": [{"path": "o", "kind": "ollama"}], "entries": entries,
            "resolve": [{"name": "ollama:QWEN3:0.6b", "id": "ollama:qwen3:0.6b"}]}


def gpt4all_case():
    return {
        "why": "LST-009: GPT4All: every .gguf file within the depth, downloads and remote models left out",
        "files": [size("g/Meta-Llama-3-8B-Instruct.Q4_0.gguf", 2), size("g/mine/phi3.gguf", 1),
                  size("g/incomplete-mistral-7b.Q4_0.gguf", 1), text("g/gpt-4o-capi.rmodel", '{"apiKey": "secret"}')],
        "locations": [{"path": "g", "kind": "gpt4all"}],
        "entries": [entry("Meta-Llama-3-8B-Instruct.Q4_0", "gguf", "g/Meta-Llama-3-8B-Instruct.Q4_0.gguf", quant="Q4_0",
                          bytes=2),
                    entry("mine/phi3", "gguf", "g/mine/phi3.gguf", bytes=1)],
        "resolve": [],
    }


def modelscope_case():
    q = "ms/models/Qwen--Qwen3-0.6B-GGUF/snapshots"
    return {
        "why": "LST-010: ModelScope's current and older layouts, a link read once",
        "files": [
            size(f"{q}/master/Qwen3-0.6B-Q8_0.gguf", 3),
            size(f"{q}/v1/Qwen3-0.6B-Q8_0.gguf", 4),
            link("ms/models/Qwen/Qwen3-0.6B-GGUF", "../Qwen--Qwen3-0.6B-GGUF/snapshots/master"),
            size("ms/models/Qwen/Qwen3___5-GGUF/x-Q4_0.gguf", 5),
            text("ms/hub/models/Old/M/config.json", "{}"),
            size("ms/hub/models/Old/M/model.safetensors", 6),
            size("ms/models/._____temp/t-Q8_0.gguf", 1),
        ],
        "locations": [{"path": "ms", "kind": "modelscope"}],
        "entries": [
            entry("modelscope:Qwen/Qwen3-0.6B-GGUF:Q8_0", "gguf", f"{q}/master/Qwen3-0.6B-Q8_0.gguf", quant="Q8_0",
                  bytes=3),
            entry("modelscope:Qwen/Qwen3-0.6B-GGUF:Q8_0@v1", "gguf", f"{q}/v1/Qwen3-0.6B-Q8_0.gguf", quant="Q8_0",
                  bytes=4),
            entry("modelscope:Qwen/Qwen3.5-GGUF:Q4_0", "gguf", "ms/models/Qwen/Qwen3___5-GGUF/x-Q4_0.gguf",
                  quant="Q4_0", bytes=5),
            entry("modelscope:Old/M", "hf-directory", "ms/hub/models/Old/M",
                  ["ms/hub/models/Old/M/config.json", "ms/hub/models/Old/M/model.safetensors"], bytes=6),
        ],
        "resolve": [{"name": "Qwen/Qwen3-0.6B-GGUF", "error": "not found"}],
    }


def jan_case():
    m = "jan/llamacpp/models"
    return {
        "why": "LST-011, LST-019: Jan's model.yml files; a download in progress is not a model",
        "files": [
            size(f"{m}/Qwen3-0.6B-Q8_0/model.gguf", 3),
            size(f"{m}/Qwen3-0.6B-Q8_0/mmproj.gguf", 1),
            text(f"{m}/Qwen3-0.6B-Q8_0/model.yml",
                 "model_path: llamacpp/models/Qwen3-0.6B-Q8_0/model.gguf\nname: 'Qwen3 0.6B'\nsize_bytes: 3\n"),
            size(f"{m}/unsloth/gemma-3-1b/model.gguf.tmp", 1),
            size("jan/elsewhere/mine.gguf", 5),
            text(f"{m}/imported/mine/model.yml", 'model_path: "{root}/jan/elsewhere/mine.gguf"\n'),
            text(f"{m}/odd/model.yml", "model_path: [1]\n"),
        ],
        "locations": [{"path": "jan", "kind": "jan"}],
        "entries": [
            entry("jan:Qwen3-0.6B-Q8_0", "gguf", f"{m}/Qwen3-0.6B-Q8_0/model.gguf", quant="Q8_0", bytes=3),
            entry("jan:imported/mine", "gguf", "jan/elsewhere/mine.gguf", bytes=5),
        ],
        "resolve": [],
    }


def docker_case():
    a, b, c, d = "a" * 64, "b" * 64, "c" * 64, "d" * 64
    layer = lambda t, h: {"mediaType": t, "digest": f"sha256:{h}"}
    gguf = "application/vnd.docker.ai.gguf.v3"
    return {
        "why": "LST-012: Docker Model Runner: one entry per tag, not while a layer is downloading",
        "files": [
            js("d/layout.json", {"version": "1.0.0"}),
            js("d/models.json", {"models": [{"id": f"sha256:{a}", "tags": ["ai/smollm2:latest", "ai/smollm2:360M-Q4_K_M"]},
                                            {"id": f"sha256:{c}", "tags": ["ai/partial:latest"]}]}),
            js(f"d/manifests/sha256/{a}", {"layers": [layer(gguf, b), layer("application/vnd.docker.ai.license", d)]}),
            text(f"d/blobs/sha256/{b}", "1234"),
            text(f"d/blobs/sha256/{d}", "MIT"),
            js(f"d/manifests/sha256/{c}", {"layers": [layer(gguf, c)]}),
            text(f"d/blobs/sha256/{c}.incomplete", "1"),
        ],
        "locations": [{"path": "d", "kind": "docker"}],
        "entries": [
            entry("docker:ai/smollm2:latest", "gguf", f"d/blobs/sha256/{b}", bytes=4),
            entry("docker:ai/smollm2:360M-Q4_K_M", "gguf", f"d/blobs/sha256/{b}", bytes=4),
        ],
        "resolve": [],
    }


def ramalama_case():
    m = "r/store/huggingface/Qwen/Qwen3-0.6B-GGUF"
    return {
        "why": "LST-013: RamaLama: one entry per tag; a tag's JSON ref before its text ref; a partial model left out",
        "files": [
            size(f"{m}/blobs/sha256-aa", 3),
            size(f"{m}/snapshots/s1/Qwen3-0.6B-Q8_0.gguf", 3),
            size(f"{m}/snapshots/s1/mmproj-F16.gguf", 1),
            size(f"{m}/snapshots/s2/Qwen3-0.6B-Q4_0.gguf", 4),
            js(f"{m}/refs/latest.json", {"hash": "s1", "files": [{"name": "Qwen3-0.6B-Q8_0.gguf", "type": "gguf"},
                                                                 {"name": "mmproj-F16.gguf", "type": "mmproj"}]}),
            text(f"{m}/refs/latest", "s2\nQwen3-0.6B-Q4_0.gguf\n"),
            text(f"{m}/refs/old", "s2\nQwen3-0.6B-Q4_0.gguf\nmmproj-x.gguf\n"),
            js(f"{m}/refs/partial.json", {"hash": "s3", "files": [{"name": "x.gguf", "type": "gguf"}]}),
            size("r/store/ollama/smollm/blobs/x", 1),
            size("r/store/ollama/smollm/snapshots/s/smollm.gguf", 2),
            js("r/store/ollama/smollm/refs/latest.json", {"hash": "s", "files": [{"name": "smollm.gguf", "type": "gguf"}]}),
        ],
        "locations": [{"path": "r", "kind": "ramalama"}],
        "entries": [
            entry("huggingface://Qwen/Qwen3-0.6B-GGUF:latest", "gguf", f"{m}/snapshots/s1/Qwen3-0.6B-Q8_0.gguf",
                  quant="Q8_0", bytes=3),
            entry("ollama://smollm:latest", "gguf", "r/store/ollama/smollm/snapshots/s/smollm.gguf", bytes=2),
        ],
        "resolve": [],
        "note": "refs/old is missing mmproj-x.gguf from snapshot s2, so it has no entry",
    }


def across_case():
    return {
        "why": "LST-015: a file reached twice is listed once; an id two locations share is told apart",
        "files": [size("a/m-Q8_0.gguf", 1), size("b/m-Q8_0.gguf", 2), link("b/same-Q8_0.gguf", "../a/m-Q8_0.gguf")],
        "locations": [{"path": "a", "kind": "directory"}, {"path": "b", "kind": "directory"},
                      {"path": "a", "kind": "directory"}],
        "entries": [entry("m-Q8_0", "gguf", "a/m-Q8_0.gguf", quant="Q8_0", bytes=1),
                    entry("{root}/b:m-Q8_0", "gguf", "b/m-Q8_0.gguf", quant="Q8_0", bytes=2)],
        "resolve": [{"name": "m-q8_0", "id": "m-Q8_0"}],
    }


def nickname_case():
    return {
        "why": "NAM-001 step 2, NAM-002: nicknames, at most four in a row",
        "files": [size("n/qwen3-0.6b-Q8_0.gguf", 1)],
        "locations": [{"path": "n", "kind": "directory"}],
        "names": {"q": "qwen3", "chain1": "chain2", "chain2": "chain3", "chain3": "chain4", "chain4": "chain5",
                  "chain5": "qwen3", "gone": "Org/Missing"},
        "entries": [entry("qwen3-0.6b-Q8_0", "gguf", "n/qwen3-0.6b-Q8_0.gguf", quant="Q8_0", bytes=1)],
        "resolve": [{"name": "q", "id": "qwen3-0.6b-Q8_0"}, {"name": "chain2", "id": "qwen3-0.6b-Q8_0"},
                    {"name": "chain1", "error": "not found"}, {"name": "gone", "error": "not found"}],
    }


def listing():
    return {
        "about": "specs/listing.md and specs/names.md. Each case: build `files` in an empty folder, read `locations` "
                 "(and no others) in order with `names` as the nicknames, and compare the entries in order and each "
                 "`resolve`. Paths are relative to the case's folder; `files` are an entry's files (LST-017).",
        "cases": [walk_case(), depth_and_size_case(), hub_case(), llama_cpp_case(), lm_studio_case(), ollama_case(),
                  gpt4all_case(), modelscope_case(), jan_case(), docker_case(), ramalama_case(), across_case(),
                  nickname_case()],
    }


# ----------------------------------------------------------------------------------------------------- configuration

def linux_defaults(home="{root}/home", hub=None, llama=None, lmstudio=None, gpt4all=None, modelscope=None, jan=None,
                   docker=None, ramalama=None, ollama=None):
    out = [
        {"path": hub or f"{home}/.cache/huggingface/hub", "kind": "directory", "depth": 6},
        {"path": llama or f"{home}/.cache/llama.cpp", "kind": "directory", "depth": 6},
        {"path": lmstudio or f"{home}/.lmstudio/models", "kind": "lmstudio", "depth": None},
        {"path": gpt4all or f"{home}/.local/share/nomic.ai/GPT4All", "kind": "gpt4all", "depth": 8},
        {"path": modelscope or f"{home}/.cache/modelscope", "kind": "modelscope", "depth": None},
        {"path": jan or f"{home}/.local/share/Jan/data", "kind": "jan", "depth": 8},
        {"path": docker or f"{home}/.docker/models", "kind": "docker", "depth": None},
        {"path": ramalama or f"{home}/.local/share/ramalama", "kind": "ramalama", "depth": None},
    ]
    if ollama:
        out.append({"path": ollama, "kind": "ollama", "depth": None})
    else:
        out.append({"path": f"{home}/.ollama/models", "kind": "ollama", "depth": None})
        out.append({"path": "/usr/share/ollama/.ollama/models", "kind": "ollama", "depth": None})
    return out


def configuration():
    home = {"HOME": "{root}/home"}
    cfg = lambda t: [text("config.toml", t)]
    with_cfg = {**home, "TENSTAG_CONFIG": "{root}/config.toml"}
    cases = [
        {"why": "LOC-001, LOC-004: the built-in locations on Linux with nothing set (no /etc/ramalama on the machine)",
         "platform": "linux", "env": home, "files": [],
         "read": linux_defaults(), "cache": "{root}/home/.cache/tenstag"},
        {"why": "LOC-001: the Hugging Face cache's variables; XDG folders; TENSTAG_CACHE_DIR",
         "platform": "linux",
         "env": {**home, "XDG_CACHE_HOME": "{root}/x", "XDG_DATA_HOME": "{root}/xd",
                 "TENSTAG_CACHE_DIR": "{root}/c", "HF_HOME": "$HOME/hf", "HUGGINGFACE_HUB_CACHE": "~/old"},
         "files": [],
         "read": linux_defaults(hub="{root}/home/old", llama="{root}/x/llama.cpp", gpt4all="{root}/xd/nomic.ai/GPT4All",
                                modelscope="{root}/home/.cache/modelscope", jan="{root}/xd/Jan/data",
                                ramalama="{root}/xd/ramalama"),
         "cache": "{root}/c"},
        {"why": "LOC-001: HF_HUB_CACHE first; HF_HOME with a variable; the stores' own settings files",
         "platform": "linux",
         "env": {**home, "HF_HOME": "$HOME/hf", "LLAMA_CACHE": "{root}/llama", "MODELSCOPE_CACHE": "~/ms",
                 "MODELS_PATH": "{root}/docker", "RAMALAMA_STORE": "{root}/rl", "OLLAMA_MODELS": " '~/ollama' "},
         "files": [text("home/.lmstudio-home-pointer", "{root}/studio\n"),
                   js("studio/settings.json", {"downloadsFolder": "{root}/big/models"}),
                   text("home/.config/nomic.ai/GPT4All.ini", '[General]\nmodelPath="{root}/g4a"\n'),
                   js("home/.local/share/Jan/settings.json", {"data_folder": "{root}/jandata"})],
         "read": linux_defaults(hub="{root}/home/hf/hub", llama="{root}/llama", lmstudio="{root}/big/models",
                                gpt4all="{root}/g4a", modelscope="{root}/home/ms", jan="{root}/jandata",
                                docker="{root}/docker", ramalama="{root}/rl", ollama="{root}/home/ollama")},
        {"why": "LOC-002: a GPT4All modelPath in Qt's escaped form is not decoded: the default folder",
         "platform": "linux", "env": home,
         "files": [text("home/.config/nomic.ai/GPT4All.ini", '[General]\nmodelPath="C:\\\\models"\n')],
         "read": linux_defaults()},
        {"why": "LOC-003: RamaLama's store from ramalama.conf, a later file winning",
         "platform": "linux", "env": {**home, "XDG_CONFIG_HOME": "{root}/conf"},
         "files": [text("conf/ramalama/ramalama.conf", '[ramalama]\nstore = "{root}/first"\n'),
                   text("conf/ramalama/ramalama.conf.d/b.conf", '[ramalama]\nstore = "~/second"\n')],
         "read": linux_defaults(ramalama="{root}/home/second")},
        {"why": "CFG-002, CFG-006, CFG-008: the file's locations, then TENSTAG_PATH; a folder given twice read once",
         "platform": "unix",
         "env": {**with_cfg, "TENSTAG_PATH": "{root}/p1::{root}/p2"},
         "files": cfg('defaults = false\n[[location]]\npath = "~/data"\n[[location]]\npath = "{root}/o"\n'
                      'kind = "ollama"\n[[location]]\npath = "{root}/deep"\ndepth = 12\nmin_size = 0\n'
                      '[[location]]\npath = "{root}/p1"\n[names]\nq = "Qwen/Qwen3-0.6B-GGUF:Q8_0"\n'),
         "read": [{"path": "{root}/home/data", "kind": "directory", "depth": 6},
                  {"path": "{root}/o", "kind": "ollama", "depth": None},
                  {"path": "{root}/deep", "kind": "directory", "depth": 12, "min_size": 0},
                  {"path": "{root}/p1", "kind": "directory", "depth": 6},
                  {"path": "{root}/p2", "kind": "directory", "depth": 6}],
         "names": {"q": "Qwen/Qwen3-0.6B-GGUF:Q8_0"}},
        {"why": "CFG-009: who added a location and when; a date, and a date-time given in UTC without fractions",
         "platform": "any", "env": with_cfg,
         "files": cfg('defaults = false\n[[location]]\npath = "{root}/a"\nadded_by = "goldnode/tensrun"\n'
                      'added = 2026-11-24T19:48:18.75+01:00\n[[location]]\npath = "{root}/b"\nadded = 2026-11-24\n'
                      '[[location]]\npath = "{root}/c"\n'),
         "read": [{"path": "{root}/a", "kind": "directory", "depth": 6, "added_by": "goldnode/tensrun",
                   "added": "2026-11-24T18:48:18Z"},
                  {"path": "{root}/b", "kind": "directory", "depth": 6, "added_by": None, "added": "2026-11-24"},
                  {"path": "{root}/c", "kind": "directory", "depth": 6, "added_by": None, "added": None}]},
        {"why": "CFG-001: the file in XDG_CONFIG_HOME", "platform": "any",
         "env": {**home, "XDG_CONFIG_HOME": "{root}/conf"},
         "files": [text("conf/tenstag/config.toml", "defaults = false\n[[location]]\npath = \"{root}/x\"\n")],
         "read": [{"path": "{root}/x", "kind": "directory", "depth": 6}]},
        {"why": "TFC-001: TENSTAG_CACHE_DIR only when absolute", "platform": "linux",
         "env": {**home, "TENSTAG_CACHE_DIR": "relative", "XDG_CACHE_HOME": "{root}/xc"}, "files": [],
         "read": linux_defaults(hub="{root}/xc/huggingface/hub", llama="{root}/xc/llama.cpp"), "cache": "{root}/xc/tenstag"},
        {"why": "CFG-001: only one folder is looked in: with XDG_CONFIG_HOME set, ~/.config is not",
         "platform": "linux", "env": {**home, "XDG_CONFIG_HOME": "{root}/conf"},
         "files": [text("home/.config/tenstag/config.toml", "defaults = false\n")],
         "read": linux_defaults()},
    ]
    for why, body in [
        ("CFG-002: a key the file does not have", "colour = 1\n"),
        ("CFG-002: downloads are gone", 'download = "~/dl"\n'),
        ("CFG-002: class is gone", '[[location]]\npath = "/x"\nclass = "diffusion"\n'),
        ("CFG-003: an unknown kind", '[[location]]\npath = "/x"\nkind = "comfyui"\n'),
        ("CFG-004: depth on a store read by its layout", '[[location]]\npath = "/o"\nkind = "ollama"\ndepth = 3\n'),
        ("CFG-002: a value of the wrong type", "defaults = \"no\"\n"),
        ("CFG-002: not TOML", "[[location]\n"),
        ("CFG-009: added_by that is not an owner name", '[[location]]\npath = "/x"\nadded_by = "Some Program"\n'),
        ("CFG-009: added as a string", '[[location]]\npath = "/x"\nadded = "2026-11-24"\n'),
        ("CFG-009: added as a local date-time", '[[location]]\npath = "/x"\nadded = 2026-11-24T18:48:18\n'),
    ]:
        cases.append({"why": why, "platform": "any", "env": with_cfg, "files": cfg(body), "error": True})
    cases.append({"why": "CFG-001: TENSTAG_CONFIG names a file that is not there", "platform": "any",
                  "env": with_cfg, "files": [], "error": True})
    return {"about": "specs/configuration.md and specs/locations.md. Each case: build `files` in an empty folder, "
                     "read the configuration with exactly `env` as the environment (on `platform`: linux, unix, or "
                     "any), and compare `read` (each location's path, kind, depth, and min_size, added_by and added "
                     "when given; null depth for a store read by its layout), `names`, `data` and `cache` when given, or that it is "
                     "an error.",
            "cases": cases}


# ----------------------------------------------------------------------------------------------- config writing

NOW = "2026-11-24T18:48:18Z"


def config_writing():
    env = {"HOME": "{root}/home", "TENSTAG_CONFIG": "{root}/config.toml"}
    xdg = {"HOME": "{root}/home", "XDG_CONFIG_HOME": "{root}/conf"}
    row = lambda path, kind="directory", depth=6, added_by=None, added=NOW, **more: {  # noqa: E731
        "path": path, "kind": kind, "depth": depth, "added_by": added_by, "added": added, **more}

    def case(why, before, change, after=None, *, result=None, error=False, environment=env,
             file="config.toml", platform="unix"):
        out = {"why": why, "platform": platform, "env": environment, "file": file, "before": before,
               "change": change}
        if error:
            out["error"] = True
        else:
            out["after"] = after
            out["result"] = result
        return out

    three = ('# my models\ndefaults = false   # only these\n\n'
             '[[location]]\npath = "/data/a"\n\n'
             '# the NAS\n[[location]]  # mounted at boot\npath = "/mnt/nas"\ndepth = 10\n\n'
             '# Ollama\n[[location]]\npath = "/srv/ollama"\nkind = "ollama"\n\n'
             '[names]\nsmall = "Qwen/Qwen3-0.6B-GGUF:Q8_0"\n')
    cases = [
        case("CFG-010, CFG-011: adding to a file that is not there creates it, and its folders",
             None, {"add": {"path": "{root}/models", "added_by": "goldnode/tensrun"}},
             '[[location]]\npath = "{root}/models"\nadded_by = "goldnode/tensrun"\nadded = ' + NOW + "\n",
             result={"added": row("{root}/models", added_by="goldnode/tensrun")},
             environment=xdg, file="conf/tenstag/config.toml", platform="any"),
        case("CFG-011: added at the end, after an empty line; comments and [names] kept; a missing final newline added",
             '# mine\ndefaults = true # yes\n\n[names]\nsmall = "x"',
             {"add": {"path": "~/m", "kind": "directory", "depth": 10, "min_size": 0}},
             '# mine\ndefaults = true # yes\n\n[names]\nsmall = "x"\n\n'
             '[[location]]\npath = "~/m"\ndepth = 10\nmin_size = 0\nadded = ' + NOW + "\n",
             result={"added": row("{root}/home/m", depth=10, min_size=0)}),
        case("CFG-011: kind written when not directory; a kind's default depth and min_size are not written",
             "defaults = false\n", {"add": {"path": "/srv/g", "kind": "gpt4all", "depth": 8, "min_size": 1048576,
                                            "added_by": "com.example.app"}},
             'defaults = false\n\n[[location]]\npath = "/srv/g"\nkind = "gpt4all"\nadded_by = "com.example.app"\n'
             'added = ' + NOW + "\n",
             result={"added": row("/srv/g", kind="gpt4all", depth=8, added_by="com.example.app")}),
        case("CFG-011: a store read by its layout has no depth",
             "", {"add": {"path": "/srv/o", "kind": "ollama"}},
             '[[location]]\npath = "/srv/o"\nkind = "ollama"\nadded = ' + NOW + "\n",
             result={"added": row("/srv/o", kind="ollama", depth=None)}),
        case("CFG-011: a string escaped as a TOML basic string",
             None, {"add": {"path": '/data/we"ird\\dir\tx'}},
             '[[location]]\npath = "/data/we\\"ird\\\\dir\\u0009x"\nadded = ' + NOW + "\n",
             result={"added": row('/data/we"ird\\dir\tx')}, environment=xdg, file="conf/tenstag/config.toml"),
        case("CFG-011: a folder the file already lists, written another way: nothing written",
             '[[location]]\npath = "~/data"\nadded_by = "a/b"\nadded = 2026-01-02\n',
             {"add": {"path": "{root}/home/data", "added_by": "goldnode/tensrun"}},
             '[[location]]\npath = "~/data"\nadded_by = "a/b"\nadded = 2026-01-02\n',
             result={"listed": row("{root}/home/data", added_by="a/b", added="2026-01-02")}),
        case("CFG-011: a relative path is an error", "", {"add": {"path": "models"}}, error=True, platform="any"),
        case("CFG-011: an added_by that is not an owner name is an error", "",
             {"add": {"path": "/m", "added_by": "My Program"}}, error=True),
        case("CFG-010: a file breaking CFG-002 is never changed", "colour = 1\n", {"add": {"path": "/m"}},
             error=True),
        case("CFG-010: a form the line rules cannot change safely (an array of inline tables) is refused",
             'location = [{path = "/a"}]\n', {"add": {"path": "/m"}}, error=True),
        case("CFG-010: TENSTAG_CONFIG naming a missing file is an error", None, {"add": {"path": "/m"}},
             error=True, platform="any"),
        case("CFG-012: removing a location, with the comment above it; the next one's comment stays; empty lines "
             "do not pile up", three, {"remove": "/mnt/nas"},
             '# my models\ndefaults = false   # only these\n\n'
             '[[location]]\npath = "/data/a"\n\n'
             '# Ollama\n[[location]]\npath = "/srv/ollama"\nkind = "ollama"\n\n'
             '[names]\nsmall = "Qwen/Qwen3-0.6B-GGUF:Q8_0"\n',
             result={"removed": row("/mnt/nas", depth=10, added=None)}),
        case("CFG-012: removing the first; the comment above the second stays",
             three, {"remove": "/data/a"},
             '# my models\ndefaults = false   # only these\n\n'
             '# the NAS\n[[location]]  # mounted at boot\npath = "/mnt/nas"\ndepth = 10\n\n'
             '# Ollama\n[[location]]\npath = "/srv/ollama"\nkind = "ollama"\n\n'
             '[names]\nsmall = "Qwen/Qwen3-0.6B-GGUF:Q8_0"\n',
             result={"removed": row("/data/a", added=None)}),
        case("CFG-012: removing the last location of a file; empty lines at its end go",
             'defaults = false\n\n[[location]]\npath = "/a"\nadded_by = "x/y"\nadded = 2026-11-01T00:00:00Z\n\n\n',
             {"remove": "/a"}, "defaults = false\n",
             result={"removed": row("/a", added_by="x/y", added="2026-11-01T00:00:00Z")}),
        case("CFG-012: every location with the folder goes; the first is given",
             '[[location]]\npath = "~/data"\n[[location]]\npath = "/b"\n[[location]]\npath = "{root}/home/data"\n'
             'added_by = "x/y"\n',
             {"remove": "{root}/home/data/"}, '[[location]]\npath = "/b"\n',
             result={"removed": row("{root}/home/data", added=None)}),
        case("CFG-012: a folder the file does not list: nothing written", 'defaults = false\n',
             {"remove": "/a"}, 'defaults = false\n', result={"removed": None}),
        case("CFG-010, CFG-012: nothing to remove and no file: no file is created", None, {"remove": "/a"}, None,
             result={"removed": None}, environment=xdg, file="conf/tenstag/config.toml", platform="any"),
        case("CFG-013: turning the defaults off with no defaults line: the first line", "# mine\n[names]\na = \"b\"\n",
             {"defaults": False}, 'defaults = false\n# mine\n[names]\na = "b"\n', result={}, platform="any"),
        case("CFG-013: the value replaced, the comment kept", "  defaults=false # off for now\n[names]\n",
             {"defaults": True}, "  defaults=true # off for now\n[names]\n", result={}, platform="any"),
        case("CFG-013: on, with no defaults line: nothing written", None, {"defaults": True}, None, result={},
             environment=xdg, file="conf/tenstag/config.toml", platform="any"),
        case("CFG-013: a nickname called defaults is not the defaults line",
             '[names]\ndefaults = "Qwen/Qwen3-0.6B-GGUF"\n', {"defaults": False},
             'defaults = false\n[names]\ndefaults = "Qwen/Qwen3-0.6B-GGUF"\n', result={}, platform="any"),
        case("CFG-013: already off: nothing written", "defaults = false\n", {"defaults": False},
             "defaults = false\n", result={}, platform="any"),
    ]
    return {
        "about": "specs/configuration.md CFG-010 to CFG-013. Each case: in an empty folder, write `before` to `file` "
                 "(none when null), make `change` with exactly `env` as the environment and `now` as the time: "
                 "`add` a location (path, kind, depth, min_size as given, the rest as the kind's defaults; "
                 "added_by), `remove` a path, or set `defaults`. Then either it is an `error` and `file` is as it "
                 "was, or `file` holds `after` (missing when null), and `result` is what the program was told: "
                 "`added` or `listed` for an add, `removed` (null when nothing was) for a remove, nothing for "
                 "defaults; locations as configuration.json's `read` rows, with added_by and added. In `before` "
                 "and `after`, {root} is the case's folder written as a TOML basic string would hold it "
                 "(CFG-011); elsewhere, {root} is the folder.",
        "now": NOW,
        "cases": cases,
    }


# ------------------------------------------------------------------------------------------------------------ names

def names():
    ok = lambda name, repo, quant=None, revision=None: {"name": name, "repo": repo, "quant": quant, "revision": revision}
    no = lambda name: {"name": name, "repo": None}
    return {
        "about": "specs/names.md NAM-003: whether each name is a Hugging Face repository name, and its parts",
        "names": [
            ok("Qwen/Qwen3-0.6B-GGUF", "Qwen/Qwen3-0.6B-GGUF"),
            ok("hf.co/Qwen/Qwen3-0.6B-GGUF:q8_0@main", "Qwen/Qwen3-0.6B-GGUF", "q8_0", "main"),
            ok("huggingface.co/a/b@refs/pr/1", "a/b", None, "refs/pr/1"),
            ok("o/m:v1.5", "o/m", "v1.5"),
            ok("o/m:Q4_K_M@" + "c" * 40, "o/m", "Q4_K_M", "c" * 40),
            ok("a_1/b.c-d", "a_1/b.c-d"),
            no("qwen3"), no("a/b/c"), no("/abs"), no("a/.b"), no("a/b-"), no("a/b:"), no("a//b"), no("a/b@"),
            no("a/b:x/y.gguf"), no("a/b@x..y"), no("a/b@x y"), no("a/b:Q4 K"), no("a/b:c:d"), no("ollama:qwen3:0.6b"),
            no("a/" + "b" * 255),
        ],
    }


def main():
    outputs = {"listing.json": listing(), "configuration.json": configuration(), "names.json": names(),
               "config-writing.json": config_writing()}
    problems = 0
    for name, value in outputs.items():
        rendered = json.dumps(value, indent=1, ensure_ascii=False) + "\n"
        path = VECTORS / name
        if len(sys.argv) > 1 and sys.argv[1] == "check":
            if not path.is_file() or path.read_text() != rendered:
                print(f"{path.relative_to(ROOT)} differs from tools/cases.py")
                problems += 1
        else:
            path.write_text(rendered)
            print(f"wrote {path.relative_to(ROOT)}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
