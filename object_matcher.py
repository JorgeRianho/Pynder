from rdflib import Graph, Namespace

# Namespaces
RML = Namespace("http://w3id.org/rml/")
RR = Namespace("http://www.w3.org/ns/r2rml#")

OUTPUT_FILE = "predicate_object_grouped_report.txt"


def extract_predicate_object_pairs(graph: Graph):
    """
    Returns a dictionary where:
    key = predicate URI
    value = list of object mappings (template, reference or constant)
    """
    query = """
    SELECT DISTINCT ?predicate ?valueType ?object WHERE {
        ?tm rml:predicateObjectMap ?pom .
        ?pom rml:predicateMap ?pm .
        ?pm ?pType ?predicate .

        ?pom rml:objectMap ?om .
        ?om ?valueType ?object .

        FILTER(?pType IN (rml:constant, rml:template, rml:reference))
        FILTER(?valueType IN (rml:constant, rml:template, rml:reference))
    }
    """

    grouped = {}

    for row in graph.query(query, initNs={"rml": RML, "rr": RR}):
        predicate, value_type, obj = map(str, row)

        if predicate not in grouped:
            grouped[predicate] = []

        grouped[predicate].append({
            "object": obj,
            "type": value_type.split("#")[-1] if "#" in value_type else value_type
        })

    return grouped


def generate_report(graph: Graph):
    grouped = extract_predicate_object_pairs(graph)

    with open(OUTPUT_FILE, "w") as f:
        f.write("📌 Grouped Predicate → ObjectMap Report\n")
        f.write("===========================================\n\n")

        if not grouped:
            f.write("⚠️ No predicate/object mappings found.\n")
            return

        for predicate, objects in grouped.items():
            f.write(f"🔹 Predicate: {predicate}\n")

            for obj in objects:
                f.write(f"   • {obj['object']}   ({obj['type']})\n")

            f.write("\n----------------------------------------------------\n\n")

    print(f"📄 Report generated: {OUTPUT_FILE}")


if __name__ == "__main__":
    graph = Graph()
    graph.parse("prueba.ttl", format="turtle")
    generate_report(graph)
