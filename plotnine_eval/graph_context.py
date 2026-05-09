import json
from collections import deque
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GRAPH_ROOT = PROJECT_ROOT / ".claude" / "skills" / "plotnine-grammar-of-graphics"
GRAPH_PATH = GRAPH_ROOT / "graph" / "graph.json"


INTENT_RULES = [
    ("intent-relationship", ("scatter", "relationship", "correlation", "trend line", "smooth")),
    ("intent-counts", ("bar", "count", "percentage", "frequency")),
    ("intent-distribution", ("histogram", "distribution", "bins")),
    ("intent-group-comparison", ("boxplot", "jitter", "grouped by", "compare")),
    ("intent-trend", ("line chart", "trend by", "time series", "mean score")),
]

DEFAULT_NODES = {
    "concept-ggplot-object",
    "layer-aesthetic-mapping",
    "layer-labels-theme",
    "output-save",
    "grader-plotnine-eval",
}


def load_graph(path: Path = GRAPH_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def infer_intents(case_id: str, category: str, prompt: str) -> list[str]:
    text = f"{case_id} {category} {prompt}".lower()
    intents = [intent for intent, terms in INTENT_RULES if any(term in text for term in terms)]
    return intents or ["intent-relationship"]


def traverse_graph(start_nodes: list[str], graph: dict, max_depth: int = 4) -> list[str]:
    adjacency: dict[str, list[str]] = {}
    for edge in graph["edges"]:
        adjacency.setdefault(edge["from"], []).append(edge["to"])

    seen = set(DEFAULT_NODES)
    queue = deque((node, 0) for node in start_nodes)

    while queue:
        node, depth = queue.popleft()
        if node in seen and depth > 0:
            continue
        seen.add(node)
        if depth >= max_depth:
            continue
        for neighbor in adjacency.get(node, []):
            queue.append((neighbor, depth + 1))

    node_order = [node["id"] for node in graph["nodes"]]
    return [node_id for node_id in node_order if node_id in seen]


def graph_node_map(graph: dict) -> dict[str, dict]:
    return {node["id"]: node for node in graph["nodes"]}


def build_graph_context(case_id: str, category: str, prompt: str, max_chars: int = 7000) -> dict:
    graph = load_graph()
    intents = infer_intents(case_id, category, prompt)
    active_nodes = traverse_graph(intents, graph)
    nodes = graph_node_map(graph)

    sections = []
    for node_id in active_nodes:
        node_file = GRAPH_ROOT / nodes[node_id]["file"]
        if node_file.exists():
            body = node_file.read_text(encoding="utf-8").strip()
            sections.append(f"## {node_id}\n{body}")

    text = "\n\n".join(sections)
    if len(text) > max_chars:
        text = text[:max_chars].rsplit("\n", 1)[0] + "\n\n[graph context truncated]"

    return {
        "intents": intents,
        "active_nodes": active_nodes,
        "context": text,
    }

