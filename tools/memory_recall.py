#!/usr/bin/env python3
"""memory_recall.py -- Lexical (plus optional dense) semantic recall over Cambium's
curated, committed records, with full provenance for every hit.

This module indexes ONLY already-curated, committed records -- never raw
transcripts or temporary files -- so no verbatim-secret material enters the
index.  Every result carries source file, chunk index, and a short snippet
so any hit is auditable under Cambium governance.

Sources indexed (each skipped gracefully if absent):
  agent_outputs/findings_ledger.csv
  governance/GATES.md
  governance/CONTRIBUTION_LEDGER.csv
  agent_outputs/*.md
  docs/**/*.md

Retrieval approach:
  Primary  -- pure-stdlib BM25 (Okapi BM25 with k1=1.5, b=0.75) over tokenised
              chunks.  Zero external dependencies.
  Optional -- if `sentence-transformers` is importable, a dense rerank is
              applied on the BM25 top-50 candidates.  Its absence is a silent
              no-op; the lexical result is returned unchanged.

Index cache: .cambium_memory/index.json  (never committed; add to .gitignore).

CLI:
  python3 tools/memory_recall.py index
  python3 tools/memory_recall.py query "learning packet" [-k N]
  python3 tools/memory_recall.py --help

Importable API:
  from tools.memory_recall import build_index, query_index
  from tools.memory_recall import query_index_with_graph  # optional graph expansion
"""

# Windows cp1252 guard -- must come before any print()
import sys
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import argparse
import csv
import json
import math
import re
import textwrap
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / ".cambium_memory"
CACHE_FILE = CACHE_DIR / "index.json"

# ---------------------------------------------------------------------------
# Source discovery
# ---------------------------------------------------------------------------

def _source_paths(root: Path) -> List[Path]:
    """Return ordered list of source paths to index.  Missing ones are skipped."""
    candidates: List[Path] = []

    # Explicit files
    for rel in [
        "agent_outputs/findings_ledger.csv",
        "governance/GATES.md",
        "governance/CONTRIBUTION_LEDGER.csv",
    ]:
        p = root / rel
        if p.exists():
            candidates.append(p)

    # agent_outputs/*.md -- guard against missing directory
    ao_dir = root / "agent_outputs"
    if ao_dir.is_dir():
        for p in sorted(ao_dir.glob("*.md")):
            candidates.append(p)

    # docs/**/*.md
    docs_dir = root / "docs"
    if docs_dir.is_dir():
        for p in sorted(docs_dir.rglob("*.md")):
            candidates.append(p)

    return candidates


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

_CHUNK_SIZE = 200   # words per chunk


def _read_safe(path: Path) -> str:
    """Read a file with UTF-8, fall back to latin-1 on decode errors.

    A source that vanishes or cannot be read (a missing file, a permission or
    other OS error) is skipped by returning an empty string, so one bad source
    never aborts the whole index.
    """
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="latin-1")
        except OSError:
            return ""
    except OSError:
        return ""


def _extract_chunks(path: Path, repo_root: Path) -> List[Dict]:
    """Return list of chunk dicts: {source, chunk_idx, line_start, snippet, text}.

    source is the path relative to repo_root, with forward slashes.
    """
    suffix = path.suffix.lower()
    # Compute relative source label once
    try:
        rel_source = str(path.relative_to(repo_root)).replace("\\", "/")
    except ValueError:
        rel_source = str(path).replace("\\", "/")

    if suffix == ".csv":
        return _chunks_from_csv(path, rel_source)
    return _chunks_from_text(path, rel_source)


def _chunks_from_text(path: Path, rel_source: str) -> List[Dict]:
    """Split a text/markdown file into word-window chunks."""
    raw = _read_safe(path)
    lines = raw.splitlines()
    words: List[Tuple[str, int]] = []   # (word, line_number)
    for lineno, line in enumerate(lines, 1):
        for w in line.split():
            words.append((w, lineno))

    chunks: List[Dict] = []
    step = _CHUNK_SIZE
    for i in range(0, max(1, len(words)), step):
        slice_ = words[i : i + _CHUNK_SIZE]
        if not slice_:
            break
        chunk_words = [w for w, _ in slice_]
        line_start = slice_[0][1]
        text = " ".join(chunk_words)
        snippet = textwrap.shorten(text, width=160, placeholder="...")
        chunks.append({
            "source": rel_source,
            "chunk_idx": len(chunks),
            "line_start": line_start,
            "snippet": snippet,
            "text": text,
        })
    return chunks


def _chunks_from_csv(path: Path, rel_source: str) -> List[Dict]:
    """Each CSV row becomes one chunk."""
    chunks: List[Dict] = []
    raw = _read_safe(path)
    try:
        reader = csv.DictReader(raw.splitlines())
        for row_idx, row in enumerate(reader, 1):
            text = " ".join(str(v) for v in row.values() if v)
            snippet = textwrap.shorten(text, width=160, placeholder="...")
            chunks.append({
                "source": rel_source,
                "chunk_idx": row_idx - 1,
                "line_start": row_idx + 1,   # +1 for header row
                "snippet": snippet,
                "text": text,
            })
    except Exception:
        # Fallback: treat as plain text
        chunks = _chunks_from_text(path, rel_source)
    return chunks


# ---------------------------------------------------------------------------
# BM25 (pure stdlib, Okapi BM25)
# ---------------------------------------------------------------------------

_K1 = 1.5
_B  = 0.75
_STOP = frozenset([
    "a", "an", "the", "and", "or", "of", "to", "in", "is", "it",
    "that", "this", "for", "with", "as", "on", "at", "by", "from",
    "be", "was", "are", "has", "have", "not", "but", "we", "you",
])


def _tokenize(text: str) -> List[str]:
    return [
        t.lower()
        for t in re.findall(r"[a-zA-Z0-9_-]+", text)
        if t.lower() not in _STOP and len(t) > 1
    ]


def _build_bm25_index(chunks: List[Dict]) -> Dict:
    """Build BM25 index: per-document TF, document lengths, and IDF."""
    N = len(chunks)
    tf_list: List[Dict[str, int]] = []
    dl_list: List[int] = []
    df: Dict[str, int] = {}

    for chunk in chunks:
        tokens = _tokenize(chunk["text"])
        tf: Dict[str, int] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        tf_list.append(tf)
        dl_list.append(len(tokens))
        for t in set(tokens):
            df[t] = df.get(t, 0) + 1

    avgdl = (sum(dl_list) / N) if N else 1.0

    idf: Dict[str, float] = {}
    for term, freq in df.items():
        idf[term] = math.log((N - freq + 0.5) / (freq + 0.5) + 1)

    return {
        "tf_list": tf_list,
        "dl_list": dl_list,
        "idf": idf,
        "avgdl": avgdl,
        "N": N,
    }


def _bm25_score(query_tokens: List[str], doc_idx: int, bm25: Dict) -> float:
    tf_list = bm25["tf_list"]
    dl_list = bm25["dl_list"]
    idf = bm25["idf"]
    avgdl = bm25["avgdl"]
    score = 0.0
    dl = dl_list[doc_idx]
    tf = tf_list[doc_idx]
    for t in query_tokens:
        if t not in idf:
            continue
        f = tf.get(t, 0)
        score += idf[t] * (f * (_K1 + 1)) / (
            f + _K1 * (1 - _B + _B * dl / avgdl)
        )
    return score


# ---------------------------------------------------------------------------
# Optional dense rerank
# ---------------------------------------------------------------------------

def _try_dense_rerank(
    query: str,
    candidates: List[Tuple[int, float]],
    chunks: List[Dict],
    top_k: int,
) -> Optional[List[Tuple[int, float]]]:
    """Attempt dense reranking with sentence-transformers.  Returns None if unavailable."""
    try:
        from sentence_transformers import SentenceTransformer, util  # type: ignore
        model = SentenceTransformer("all-MiniLM-L6-v2")
        texts = [chunks[i]["text"] for i, _ in candidates]
        q_emb = model.encode(query, convert_to_tensor=True)
        c_embs = model.encode(texts, convert_to_tensor=True)
        sims = util.cos_sim(q_emb, c_embs)[0].tolist()
        reranked = sorted(
            [(candidates[i][0], float(s)) for i, s in enumerate(sims)],
            key=lambda x: x[1],
            reverse=True,
        )
        return reranked[:top_k]
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_index(root: Optional[Path] = None) -> Dict:
    """Scan curated sources, build BM25 index, persist to cache, return index dict."""
    root = root or ROOT
    paths = _source_paths(root)

    chunks: List[Dict] = []
    for p in paths:
        chunks.extend(_extract_chunks(p, root))

    bm25 = _build_bm25_index(chunks)

    index = {
        "chunks": chunks,
        "bm25": {
            "tf_list": bm25["tf_list"],
            "dl_list": bm25["dl_list"],
            "idf": bm25["idf"],
            "avgdl": bm25["avgdl"],
            "N": bm25["N"],
        },
        "sources": [str(p.relative_to(root)).replace("\\", "/") for p in paths],
        "chunk_count": len(chunks),
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=2)

    return index


def _load_index() -> Dict:
    """Load cached index.  Raises FileNotFoundError if not yet built."""
    with open(CACHE_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def query_index(
    query_text: str,
    top_k: int = 5,
    index: Optional[Dict] = None,
    use_dense: bool = True,
) -> List[Dict]:
    """Return top-k results with provenance.  Loads cache if index not supplied.

    Each result dict: {source, chunk_idx, line_start, snippet, score}.
    """
    if index is None:
        index = _load_index()

    chunks = index["chunks"]
    bm25 = index["bm25"]
    N = bm25["N"]
    if N == 0:
        return []

    q_tokens = _tokenize(query_text)
    if not q_tokens:
        return []

    scores = [_bm25_score(q_tokens, i, bm25) for i in range(N)]

    # Top-50 candidates for optional dense rerank
    candidate_k = min(50, N)
    top_indices = sorted(range(N), key=lambda i: scores[i], reverse=True)[:candidate_k]
    candidates = [(i, scores[i]) for i in top_indices]

    if use_dense:
        reranked = _try_dense_rerank(query_text, candidates, chunks, top_k)
        if reranked is not None:
            candidates = reranked

    final = candidates[:top_k]
    results = []
    for chunk_idx, score in final:
        c = chunks[chunk_idx]
        results.append({
            "source": c["source"],
            "chunk_idx": c["chunk_idx"],
            "line_start": c["line_start"],
            "snippet": c["snippet"],
            "score": round(score, 4),
        })
    return results


# ---------------------------------------------------------------------------
# Optional graph-expansion adapter
# (thin wrapper -- does NOT break existing query_index behavior)
# ---------------------------------------------------------------------------

def query_index_with_graph(
    query_text: str,
    top_k: int = 5,
    graph_k: int = 2,
    index: Optional[Dict] = None,
    use_dense: bool = True,
) -> Dict:
    """BM25 recall PLUS optional k-hop graph expansion of the top hit.

    Returns:
      {
        "recall_results": [...],   # same as query_index()
        "graph_neighbors": [...],  # k-hop neighbors from concept_graph (may be [])
        "graph_available": bool,   # False if graph cache absent or import failed
      }

    Behavior is IDENTICAL to query_index() when use_graph=False or the graph
    cache is absent. Existing callers of query_index() are completely unaffected.
    """
    recall_results = query_index(query_text, top_k=top_k, index=index, use_dense=use_dense)

    graph_neighbors: List[Dict] = []
    graph_available = False

    try:
        # Lazy import to avoid hard dependency on concept_graph
        import importlib
        import sys as _sys
        import os as _os
        _tools_dir = str(Path(__file__).resolve().parent)
        if _tools_dir not in _sys.path:
            _sys.path.insert(0, _tools_dir)
        cg = importlib.import_module("concept_graph")

        top_snippet = recall_results[0]["snippet"] if recall_results else ""
        graph_neighbors = cg.expand_with_graph(top_snippet, k=graph_k)
        graph_available = True
    except Exception:
        # Graph cache absent, concept_graph not importable, or any other error:
        # degrade gracefully, return empty graph neighbors
        pass

    return {
        "recall_results": recall_results,
        "graph_neighbors": graph_neighbors,
        "graph_available": graph_available,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cmd_index(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve() if args.root else ROOT
    print(f"[memory_recall] Indexing curated records under: {root}")
    idx = build_index(root)
    n_sources = len(idx["sources"])
    n_chunks = idx["chunk_count"]
    print(f"[memory_recall] Indexed {n_sources} source(s), {n_chunks} chunk(s).")
    print(f"[memory_recall] Cache written to: {CACHE_FILE}")
    return 0


def _cmd_query(args: argparse.Namespace) -> int:
    if not CACHE_FILE.exists():
        print(
            "[memory_recall] ERROR: no index found. Run `memory_recall.py index` first.",
            file=sys.stderr,
        )
        return 1

    results = query_index(args.query, top_k=args.k)
    if not results:
        print("[memory_recall] No results found.")
        return 0

    print(f"[memory_recall] Top {len(results)} result(s) for: {args.query!r}\n")
    for rank, r in enumerate(results, 1):
        print(f"  [{rank}] source  : {r['source']}")
        print(f"       line    : {r['line_start']}")
        print(f"       chunk   : {r['chunk_idx']}")
        print(f"       score   : {r['score']}")
        print(f"       snippet : {r['snippet']}")
        print()
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="memory_recall",
        description=(
            "Cambium in-house semantic recall: lexical BM25 (plus optional dense rerank) "
            "over curated, committed records only. Every result carries provenance."
        ),
    )
    parser.add_argument("--root", default=None, help="Repo root (default: auto-detect).")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("index", help="Build or rebuild the in-memory index cache.")

    q_sub = sub.add_parser("query", help="Query the index and print top-k results.")
    q_sub.add_argument("query", help="Free-text query string.")
    q_sub.add_argument("-k", type=int, default=5, help="Number of results (default: 5).")

    args = parser.parse_args(argv)

    if args.cmd == "index":
        return _cmd_index(args)
    elif args.cmd == "query":
        return _cmd_query(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
