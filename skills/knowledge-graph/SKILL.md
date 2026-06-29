# Skill: Knowledge Graph (concept-graph)

**Type:** Reference skill (light anatomy)
**Tier:** Reference
**Trigger on:** "what connects to", "multi-hop", "derived from", "contradicts", "which findings relate to",
"trace the path", "what supports", "what contradicts", "concept graph", "knowledge graph"
**Pairs with:** memory-recall skill, verify-evidence council

Structure adapted from agent-skills (MIT). See /ATTRIBUTION.md.

---

## What this skill does

The concept graph is a locally-built, fully-offline, directed graph over Cambium's own
curated, committed records: findings, gates, agents, and heuristic concept nodes.
It answers structural questions that flat keyword recall cannot, such as:
"which findings derive from a finding that was later contradicted?"
or "what is the 2-hop neighborhood of gate G-fit?"

**Use this skill before reasoning** about connections, derivations, or contradictions.
The graph surfaces structure; the human decides what it means.

---

## When to use / when NOT to use

**Use when:**
- A question requires tracing a chain of relationships (multi-hop).
- You need to know what supports, cites, or contradicts a finding.
- You want the subgraph for a topic (e.g., all findings and gates related to "yield").
- You need to find the shortest path between two nodes.

**Do NOT use when:**
- A simple keyword search suffices (use memory_recall.py instead).
- You need full-text content of a record (use memory_recall.py for that; the graph holds structural metadata and short previews only).
- The question requires temporal ordering within a session (this is a static graph, not a temporal KG).

---

## Exact CLI calls

Build (or rebuild) the graph from committed records:

```
python3 tools/concept_graph.py build --root .
```

Query a node or topic (2-hop default):

```
python3 tools/concept_graph.py query "finding:F1" -k 2
python3 tools/concept_graph.py query "G-fit" -k 3
python3 tools/concept_graph.py query "yield"
```

Run the multi-hop capability demonstration:

```
python3 tools/concept_graph.py demo
```

Use from Python (hybrid recall + graph):

```python
from tools.memory_recall import query_index_with_graph
result = query_index_with_graph("yield treatment effect", top_k=5, graph_k=2)
# result["recall_results"]  -- BM25 hits with provenance
# result["graph_neighbors"] -- k-hop graph expansion of the top hit
# result["graph_available"] -- False if graph cache absent (graceful)
```

Multi-hop query functions (importable):

```python
from tools.concept_graph import load_graph, neighbors, shortest_path
from tools.concept_graph import what_supports, what_contradicts, subgraph_for

G, prov = load_graph()
neighbors(G, "finding:F1", k=2)          # 2-hop neighborhood with provenance
shortest_path(G, "finding:F1", "gate:G4") # path between two nodes
what_supports(G, "gate:G4")              # what cites or reviews this gate
what_contradicts(G, "finding:F1")        # flagged contradictions (UNRESOLVED)
subgraph_for(G, "yield", k=2)            # all nodes within 2 hops of "yield"
```

---

## Contradiction rule (MANDATORY)

The graph DETECTS contradiction edges (relation="contradicts") from two structural signals:

1. An explicit action field: "supersedes F<id>" or "contradicts F<id>"
2. A heuristic: two findings with keyword overlap and opposing statuses (accepted vs. rejected)

**Contradictions are FLAGGED, never auto-resolved.**
The graph surface a contradiction with `resolution="UNRESOLVED -- human gate required"`.
Resolving a contradiction is a human decision at a gate.
Agents MUST NOT auto-write a resolved belief from a contradiction edge.

---

## Cache

The graph is cached at `.cambium_memory/concept_graph.json` (gitignored).
Rebuild is deterministic: `python3 tools/concept_graph.py build` always produces
the same graph for the same committed records.

If the cache is absent, `query` and `expand_with_graph` degrade gracefully (return
empty results, do not raise).

---

## Red flags (stop and escalate)

- A contradiction edge appears in the graph for a finding you are about to cite.
  Stop. Surface the contradiction to the human. Do not cite the finding without
  disclosing the contradiction.
- The graph returns 0 nodes after a build over a repo with records. Check that
  `agent_outputs/findings_ledger.csv` and `governance/GATES.md` exist and are parseable.
- A node labeled "heuristic=True" (concept nodes from keyword overlap) appears in
  a path you are about to cite as structural evidence. Downgrade the claim to
  "heuristically linked" and route to verify-evidence for confirmation.

---

## Limitations (honest)

- Extraction is structural/heuristic, not LLM-grade entity extraction. Concept nodes
  are keyword co-occurrence approximations only.
- This is a static local graph, not a temporal knowledge graph. It does not track
  how beliefs change over time within a session.
- The contradiction heuristic (keyword overlap + opposing status) has false positives.
  All flagged contradictions require human review before action.
- LightRAG is named as the optional upgrade path if richer graph extraction is
  needed in future (see BRAIN_ROADMAP.md).
