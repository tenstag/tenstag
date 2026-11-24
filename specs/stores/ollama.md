<!-- Generated from tensdataspecs d71a1f0a5f5f by the maintainers' stores.py. Do not edit by hand. -->

# Ollama's model store

Rules OLM-nnn. Formats: gguf, safetensors. Certainty: verified-source.

```text
Where Ollama keeps the models it pulls or creates: named manifests that point at content-addressed blobs. Added
2026-11-22. Read in Ollama v0.40.17 (envconfig/config.go, types/model/name.go, types/model/config.go,
manifest/paths.go, manifest/manifest.go, manifest/layer.go, server/images.go, server/create.go,
server/create_split_gguf.go, server/download.go, docs/faq.mdx). Read, not run: Ollama is not installed here.
Ollama's store is its own implementation detail, not a published format; it changed in recent releases
(manifests-v2, manifest lists, safetensors tensor layers) and may change again, so a reader names the Ollama version
it follows.
```

## Sources

- `ollama`: [Ollama source at release v0.40.17](https://github.com/ollama/ollama/tree/23b94a2daf2cd1fbf6b4dcfbfd3efbaca424b7bf) (v0.40.17 = 23b94a2daf2c (2026-11-20; release published 2026-11-10), read 2026-11-22), reference-implementation

## Rules

### OLM-001

Level IMPL, source `ollama`, verified-source.

```text
The directory (envconfig Models): OLLAMA_MODELS when set and not empty (surrounding spaces and quotes removed), else
<home>/.ollama/models, where <home> is the home directory of the user the server runs as. The documentation
(docs/faq.mdx) lists macOS ~/.ollama/models, Windows C:\Users\%username%\.ollama\models, and Linux
/usr/share/ollama/.ollama/models, the last because the Linux install script runs the server as a user 'ollama' whose
home is /usr/share/ollama. Under it: manifests/, manifests-v2/ and blobs/.
```

### OLM-002

Level IMPL, source `ollama`, verified-source.

```text
Names (types/model/name.go): [host/][namespace/]model[:tag][@digest], with defaults host registry.ollama.ai,
namespace library, tag latest. Parts: host [A-Za-z0-9_][A-Za-z0-9_.:-]* up to 350 characters (a port is allowed);
namespace [A-Za-z0-9_][A-Za-z0-9_-]* up to 80; model and tag [A-Za-z0-9_][A-Za-z0-9_.-]* up to 80 each. Names
compare without regard to case. registry.ollama.ai and ollama.com are the same public host. A model pulled from the
Hugging Face Hub as hf.co/<org>/<repo>[:tag] has host hf.co, namespace <org> and model <repo>.
```

### OLM-003

Level IMPL, source `ollama`, verified-source.

```text
Where a name's manifest is (manifest/paths.go resolveManifestPath). First
manifests-v2/<host>/<namespace>/<model>/<tag>, with the public host written ollama.com and ':' in a host written
%3A; this path is a relative symbolic link to the manifest's blob (a copy of it on Windows, or when a link cannot be
made). Else the legacy manifests/<host>/<namespace>/<model>/<tag>, a plain file, where the public host is tried as
registry.ollama.ai and then as ollama.com. A new write goes to manifests-v2 and normally removes the legacy file.
Each manifest is also stored as blob sha256-<sha256 of its bytes>.
```

### OLM-004

Level IMPL, source `ollama`, verified-source.

```text
Blobs (manifest/paths.go BlobsPath): blobs/sha256-<64 hex>, the digest's ':' written '-'; the name is the sha256 of
the content. A download in progress is <blob>-partial, with its progress in <blob>-partial-<N> files (one per part),
renamed to <blob> when complete (server/download.go). A reader ignores names that do not match
^sha256-[0-9a-f]{64}$.
```

### OLM-005

Level IMPL, source `ollama`, verified-source.

```text
A manifest (manifest/manifest.go) is JSON of one of two kinds. A single manifest: schemaVersion 2, mediaType
application/vnd.docker.distribution.manifest.v2+json, config (a layer), layers, and optional runner (ggml, llamacpp
or mlx) and format (gguf or safetensors). A manifest list: mediaType application/vnd.ollama.manifest.list.v2+json
and manifests, entries each with mediaType, digest (of a single manifest kept as a blob), runner and format; Ollama
chooses the first entry, in its runner order (mlx, llamacpp, ggml on Apple silicon; llamacpp, ggml, mlx elsewhere),
whose manifest blob is present. A layer has mediaType, digest (sha256:<hex>), size, and optional from and name.
```

### OLM-006

Level IMPL, source `ollama`, verified-source.

```text
Layer media types, all application/vnd.ollama.image.<kind>: model (weights), projector, adapter, draft, embed,
tensor, json, template, system, license, params, messages, prompt; and the config layer
application/vnd.docker.container.image.v1+json. The config blob is JSON with model_format (gguf or safetensors;
empty in older models, meaning gguf), model_family, model_type (the parameter size shown), file_type (the
quantization shown), and more.
```

### OLM-007

Level IMPL, source `ollama`, verified-source.

```text
The weights are not always one GGUF file. When the config's model_format is gguf or empty, the model layers are GGUF
files: one, or several for a split GGUF model (since Ollama 0.35.0: the first model layer is the first part, the
others its remaining parts in manifest order; server/images.go ModelShardPaths). When model_format is safetensors,
the weights are in tensor layers, each blob a safetensors file holding one or more tensors, its layer name a tensor
name (create/writer.go); such a model has no GGUF file. A projector layer is GGUF too (server/create.go types a GGUF
as projector from its metadata).
```

### OLM-008

Level SHOULD, source `ollama`, verified-source, suggestion SUG-041 (suggestions.md).

```text
Suggestion SUG-041. A reader that offers Ollama's GGUF models takes, for each manifest (resolving a manifest list to
the entry whose format is gguf), the config's model_format; when it is gguf or empty, it lists the model layers as
the model (several layers in order as a split set) and the projector layer as its projector, and checks each blob's
GGUF magic before use. Other formats are listed as not GGUF rather than read as GGUF.
```

### OLM-009

Level IMPL, source `ollama`, verified-source.

```text
Blob names as digests (added 2026-11-23). Every blob is named sha256-<64 hex> (OLM-004; no other algorithm is
accepted, manifest/paths.go ValidateDigest), the SHA-256 of its bytes: Ollama computes it when it creates a blob
from local data (manifest/layer.go) and, after a pull, hashes each newly downloaded layer and deletes a blob whose
bytes do not match (server/images.go verifyBlob; a layer that was already present is not hashed again). Files ending
in -partial or -partial-<N> are not blobs.
```

## Open questions

### OLM-Q1

Status: open. Impact: all rules.

```text
Not run: no Ollama store was read here. The layout is from source at v0.40.17; older stores may hold only the legacy
manifests/ tree, which this release still reads.
```
