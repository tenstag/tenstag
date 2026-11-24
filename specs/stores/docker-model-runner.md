<!-- Generated from tensdataspecs d71a1f0a5f5f by the maintainers' stores.py. Do not edit by hand. -->

# Docker Model Runner's model store

Rules DMR-nnn. Formats: gguf, safetensors. Certainty: verified-source.

```text
Where Docker Model Runner (docker model pull) keeps models: OCI artifacts in a content-addressed store with an index
of tags. Added 2026-11-23. Read in docker/model-runner v1.2.9 (pkg/envconfig, pkg/distribution/internal/store,
internal/partial, internal/bundle, types, oci/reference, cmd/cli/pkg/standalone). Read, not run. Docker Desktop's
own packaging is closed and was not read.
```

## Sources

- `dmr`: [docker/model-runner source at release v1.2.9](https://github.com/docker/model-runner/tree/58f4153e77170d0646681dbe0529ade453002343) (v1.2.9 = 58f4153e7717 (2026-10-21; release published 2026-10-22), read 2026-11-23), reference-implementation

## Rules

### DMR-001

Level IMPL, source `dmr`, verified-source.

```text
The store root (envconfig ModelsPath): MODELS_PATH when set (the server's --models-path sets it), else
~/.docker/models of the user the runner runs as. The macOS sandbox profile of the runner allows ~/.docker/models
(sandbox_darwin.go), consistent with Docker Desktop on macOS running it on the host with the default; Desktop's own
setting was not read. With Docker Engine (the standalone runner installed by the docker model CLI), the runner runs
in a container whose /models is the Docker volume docker-model-runner-models (cmd/cli/pkg/standalone), so the store
is inside that volume, not under the user's home (where Docker keeps the volume's files, normally under
/var/lib/docker/volumes/ and readable only by root, is Docker's own rule, not read here).
```

### DMR-002

Level IMPL, source `dmr`, verified-source.

```text
The layout (internal/store): layout.json, {"version": "1.0.0"} for the current layout, marks a store; models.json is
the index, {"models": [{"id", "tags", "files"}]}, where id is the model's digest, tags the references that name it,
and files the files of the model (their exact form was not checked); manifests/<algorithm>/<hex> holds each
manifest; blobs/<algorithm>/<hex> holds each layer and config; bundles/<algorithm>/<hex>/ holds unpacked runtime
bundles. A download in progress is <blob>.incomplete, renamed to the blob when complete; manifests are written
through <path>.tmp-* files and renamed.
```

### DMR-003

Level IMPL, source `dmr`, verified-source.

```text
Names (oci/reference, registry/client.go): OCI references, with the default registry index.docker.io
(DEFAULT_REGISTRY replaces it), the default organisation ai (so 'smollm2' is index.docker.io/ai/smollm2) and the
default tag latest. The tag is chosen by the publisher; for Docker Hub's ai/ models it commonly names size and
quantization, but the store gives it no meaning.
```

### DMR-004

Level IMPL, source `dmr`, verified-source.

```text
Which layers are what (types/config.go, internal/partial): a GGUF layer has media type
application/vnd.docker.ai.gguf.v3 (or application/vnd.cncf.model.weight.v1.gguf, the CNCF ModelPack form); a model
has one GGUF layer, or several for a split model, in manifest order, which the runner unpacks as
model-00001-of-0000N.gguf and so on. Other layers: application/vnd.docker.ai.mmproj (projector, at most one),
.safetensors, .dduf, .license, .chat.template.jinja, .model.file, .vllm.config.tar, .dir.tar. A layer's annotation
org.cncf.model.filepath, when present, gives its file's relative path. A model whose weights are safetensors has no
GGUF layer.
```

### DMR-005

Level IMPL, source `dmr`, verified-source.

```text
Bundles (internal/bundle): to run a model the runner builds bundles/<digest>/model/ with model.gguf (or the numbered
parts) and model.mmproj, hard-linked to the blobs where it can. So a GGUF file found under bundles/ is the same data
as a blob, under a generic name.
```

### DMR-006

Level SHOULD, source `dmr`, verified-source, suggestion SUG-047 (suggestions.md).

```text
Suggestion SUG-047. A reader takes a store only when layout.json says version 1.0.0, lists one model per models.json
entry, named by its tags, reads that entry's manifest from manifests/, and uses the GGUF layers in manifest order
(blobs/<algorithm>/<hex>) as the model, the mmproj layer as its projector; it skips *.incomplete and *.tmp-* files,
does not list bundles/ separately, and writes nothing in the store.
```

### DMR-007

Level IMPL, source `dmr`, verified-source.

```text
Blob names as digests (added 2026-11-23). blobs/<algorithm>/<hex> accepts the algorithms sha256 (64 hex) and sha512
(128 hex) (internal/store/blobs.go allowedAlgorithms). A blob under blobs/sha256/ is the SHA-256 of its bytes: the
store hashes every completed sha256 download, resumed ones included, and refuses it on a mismatch before renaming it
into place (WriteBlob). A blob under blobs/sha512/ is named by a SHA-512, which the store does not check, and is not
a SHA-256. *.incomplete files are not blobs.
```

## Open questions

### DMR-Q1

Status: open. Impact: DMR-001, DMR-003.

```text
Docker Desktop's location and setting for the store on macOS and Windows (Desktop is closed source), and the exact
written form of tags in models.json, were not checked. Not run.
```
