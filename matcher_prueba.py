from rdflib import Graph, Namespace
import re

RML = Namespace("http://w3id.org/rml/")
RR  = Namespace("http://www.w3.org/ns/r2rml#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")


def extract_predicates_with_triplesmap(mapping_graph: Graph):
    results = []

    query = """
    SELECT DISTINCT ?tm ?predicateValue WHERE { 
        ?tm rml:predicateObjectMap ?pom .
        ?pom rml:predicateMap ?pm .
        ?pm ?valueType ?predicateValue .

        FILTER(?valueType IN (rml:constant, rml:template, rml:reference))
    }
    """

    for row in mapping_graph.query(query, initNs={"rml": RML}):
        results.append({
            "triplesMap": str(row[0]),
            "predicate": str(row[1])
        })

    return results



def extract_subject_templates(mapping_graph: Graph):
    query = """
    SELECT DISTINCT ?tm ?template WHERE {
        ?tm rml:subjectMap ?sm .
        ?sm rml:template ?template .
    }
    """
    templates = []
    for row in mapping_graph.query(query, initNs={"rml": RML}):
        templates.append({"triplesMap": str(row[0]), "template": str(row[1])})
    return templates



def template_to_example_uri(template: str) -> str:
    """
    Converts a template like:
      http://example.com/{ID}/{TYPE}
    into a test URI:
      http://example.com/1/1
    """
    return re.sub(r"\{[^}]+\}", "1", template)



def match_uri_to_template(uri: str, template: str) -> bool:
    """
    Checks whether a URI matches an RML template pattern.
    """
    regex = re.escape(template)
    regex = re.sub(r"\\\{[^}]+\\\}", r"(.+)", regex)
    return re.fullmatch(regex, uri) is not None



if __name__ == "__main__":
    mapping = Graph()
    mapping.parse("prueba.ttl", format="turtle")

    output_file = "resultado_matching.txt"

    with open(output_file, "w", encoding="utf-8") as f:

        # ---- SECTION 1: Predicates ----
        f.write("🔍 Predicados y TriplesMap asociados:\n\n")
        predicate_matches = extract_predicates_with_triplesmap(mapping)

        for entry in predicate_matches:
            f.write(f" ✔ TriplesMap: {entry['triplesMap']}\n")
            f.write(f"    ↳ Predicate: {entry['predicate']}\n\n")

        # ---- SECTION 2: Subject Templates ----
        subject_templates = extract_subject_templates(mapping)

        f.write("\n🔍 Subject Templates registradas:\n\n")
        for s in subject_templates:
            f.write(f" ✔ TM: {s['triplesMap']} → Template: {s['template']}\n")

        # ---- SECTION 3: Auto Matching Between Templates ----
        f.write("\n\n🔎 Matching automático entre subject templates:\n\n")

        for template_entry in subject_templates:

            test_uri = template_to_example_uri(template_entry["template"])
            f.write(f"\n➡ URI generada: `{test_uri}` (a partir de {template_entry['template']})\n")

            match_found = False

            for target in subject_templates:
                if match_uri_to_template(test_uri, target["template"]):
                    f.write(f"   ✓ MATCH con template: {target['template']}  (TM: {target['triplesMap']})\n")
                    match_found = True

            if not match_found:
                f.write("   ✗ No hay coincidencias.\n")

    print(f"\n📁 Resultado generado en: {output_file}\n")
