"""
graph_builder.py — Stores extracted graph data into Neo4j (if available)
or networkx in-memory graph as fallback. 
Pattern mirrors Week 5 scanner fallback approach.
"""
import os
from typing import Dict, List, Optional

# In-memory store: repo_id -> networkx DiGraph
_nx_graphs: Dict[str, any] = {}


def _get_neo4j_driver():
    """Return Neo4j driver if credentials are configured, else None."""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not password:
        return None
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        return driver
    except Exception as e:
        print(f"Neo4j not available: {e}")
        return None


# ─── Neo4j store ─────────────────────────────────────────────────────────────

def _store_neo4j(driver, repo_id: str, nodes: List[Dict], edges: List[Dict]):
    with driver.session() as session:
        # Clear previous graph for this repo
        session.run("MATCH (n {repo_id: $repo_id}) DETACH DELETE n", repo_id=repo_id)

        # Create nodes
        for node in nodes:
            session.run(
                """
                MERGE (n:CodeNode {id: $id})
                SET n.name = $name,
                    n.type = $type,
                    n.filepath = $filepath,
                    n.line = $line,
                    n.repo_id = $repo_id
                """,
                id=node["id"],
                name=node["name"],
                type=node["type"],
                filepath=node["filepath"],
                line=node.get("line", 0),
                repo_id=repo_id,
            )

        # Create edges
        for edge in edges:
            session.run(
                """
                MATCH (a:CodeNode {id: $source, repo_id: $repo_id})
                MATCH (b:CodeNode {name: $target, repo_id: $repo_id})
                MERGE (a)-[r:RELATIONSHIP {type: $type}]->(b)
                """,
                source=edge["source"],
                target=edge["target"],
                type=edge["type"],
                repo_id=repo_id,
            )


def _query_neo4j(driver, repo_id: str, node_name: str, depth: int = 2) -> List[Dict]:
    with driver.session() as session:
        result = session.run(
            """
            MATCH (start:CodeNode {repo_id: $repo_id})
            WHERE start.name CONTAINS $name
            MATCH path = (start)-[*1..$depth]-(related)
            RETURN DISTINCT related.name AS name,
                   related.type AS type,
                   related.filepath AS filepath,
                   related.line AS line
            LIMIT 30
            """,
            repo_id=repo_id,
            name=node_name,
            depth=depth,
        )
        return [dict(r) for r in result]


# ─── Networkx in-memory store ─────────────────────────────────────────────────

def _store_networkx(repo_id: str, nodes: List[Dict], edges: List[Dict]):
    try:
        import networkx as nx
    except ImportError:
        _nx_graphs[repo_id] = {"nodes": nodes, "edges": edges}
        return

    G = nx.DiGraph()
    for node in nodes:
        G.add_node(node["id"], **node)
    for edge in edges:
        G.add_edge(edge["source"], edge["target"], type=edge["type"])
    _nx_graphs[repo_id] = G


def _query_networkx(repo_id: str, node_name: str, depth: int = 2) -> List[Dict]:
    graph = _nx_graphs.get(repo_id)
    if graph is None:
        return []

    # If stored as raw dict (no networkx)
    if isinstance(graph, dict):
        nodes = graph.get("nodes", [])
        return [n for n in nodes if node_name.lower() in n["name"].lower()][:30]

    try:
        import networkx as nx
        # Find matching start nodes
        start_nodes = [n for n in graph.nodes if node_name.lower() in n.lower()]
        if not start_nodes:
            return []

        related = set()
        for start in start_nodes[:3]:
            # BFS up to depth
            for node in nx.single_source_shortest_path(graph, start, cutoff=depth):
                related.add(node)
            for node in nx.single_source_shortest_path(graph.reverse(), start, cutoff=depth):
                related.add(node)

        results = []
        for node_id in list(related)[:30]:
            data = graph.nodes[node_id]
            results.append({
                "name": data.get("name", node_id),
                "type": data.get("type", "unknown"),
                "filepath": data.get("filepath", ""),
                "line": data.get("line", 0),
            })
        return results
    except Exception:
        return []


# ─── Public API ───────────────────────────────────────────────────────────────

def store_graph(repo_id: str, graph_data: Dict) -> Dict:
    """Store graph in Neo4j or networkx fallback."""
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    driver = _get_neo4j_driver()
    if driver:
        try:
            _store_neo4j(driver, repo_id, nodes, edges)
            driver.close()
            backend = "neo4j"
        except Exception as e:
            print(f"Neo4j store failed, falling back to networkx: {e}")
            _store_networkx(repo_id, nodes, edges)
            backend = "networkx"
    else:
        _store_networkx(repo_id, nodes, edges)
        backend = "networkx"

    return {
        "backend": backend,
        "nodes_stored": len(nodes),
        "edges_stored": len(edges),
    }


def query_graph(repo_id: str, node_name: str, depth: int = 2) -> List[Dict]:
    """Query related nodes from Neo4j or networkx fallback."""
    driver = _get_neo4j_driver()
    if driver:
        try:
            results = _query_neo4j(driver, repo_id, node_name, depth)
            driver.close()
            return results
        except Exception as e:
            print(f"Neo4j query failed, falling back: {e}")
    return _query_networkx(repo_id, node_name, depth)


def get_full_graph(repo_id: str) -> Dict:
    """Return full graph data for visualization."""
    graph = _nx_graphs.get(repo_id)
    if graph is None:
        return {"nodes": [], "edges": []}

    if isinstance(graph, dict):
        return graph

    try:
        import networkx as nx
        nodes = []
        for node_id, data in graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "name": data.get("name", node_id),
                "type": data.get("type", "unknown"),
                "filepath": data.get("filepath", ""),
                "line": data.get("line", 0),
            })
        edges = []
        for src, dst, data in graph.edges(data=True):
            edges.append({
                "source": src,
                "target": dst,
                "type": data.get("type", "calls"),
            })
        return {"nodes": nodes, "edges": edges}
    except Exception:
        return {"nodes": [], "edges": []}
