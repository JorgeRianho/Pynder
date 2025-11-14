from rdflib import Graph, Namespace

RML = Namespace("http://w3id.org/rml/")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")

def extract_output_predicates(mapping_graph: Graph):
    """
    Extracts only predicates defined inside rml:predicateMap blocks
    that will generate RDF triples.
    """
    predicates = set()

    query = """
    SELECT DISTINCT ?predicateValue WHERE {
        ?pom rml:predicateMap ?pm .
        ?pm ?valueType ?predicateValue .

        FILTER(?valueType IN (rml:constant, rml:template, rml:reference))
    }
    """

    for row in mapping_graph.query(query, initNs={"rml": RML}):
        predicates.add(str(row[0]))

    return sorted(predicates)


if __name__ == "__main__":
    mapping = Graph()
    mapping.parse("prueba.ttl", format="turtle")

    print("🔍 Predicados reales encontrados en el mapping:")
    preds = extract_output_predicates(mapping)

    for p in preds:
        print(f"   ✔ {p}")
