from rdflib import Graph, URIRef

def get_all_predicates(graph: Graph):
    """
    Returns a sorted list of all unique predicates found in the graph.
    """
    query = """
    PREFIX rml: <http://w3id.org/rml/>
    PREFIX rr: <http://www.w3.org/ns/r2rml#>
    PREFIX ub: <http://swat.cse.lehigh.edu/onto/univ-bench.owl#>

    SELECT DISTINCT ?p WHERE {
        ?s ?p ?o .
    }
    """
    return sorted(str(row[0]) for row in graph.query(query))


def match_predicate(graph: Graph, predicate: str):
    predicate_uri = URIRef(predicate)
    return {s for s, p, o in graph.triples((None, predicate_uri, None))}


if __name__ == "__main__":
    g = Graph()
    g.parse("prueba.ttl", format="turtle")

    print("🔍 Buscando predicados...")
    predicates = get_all_predicates(g)

    for pred in predicates:
        print(f"\n📌 Predicado encontrado: {pred}")
        
        subjects = match_predicate(g, pred)
        
        if subjects:
            print("   Sujetos con este predicado:")
            for s in subjects:
                print(f"     - {s}")
        else:
            print("   (ningún sujeto encontrado)")
