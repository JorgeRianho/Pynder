from rdflib import Graph, Namespace
import psycopg
import re
from io import StringIO   # 👉 para capturar salida en archivo


# ==========================
# Namespaces
# ==========================
RML = Namespace("http://w3id.org/rml/")
RR  = Namespace("http://www.w3.org/ns/r2rml#")


class RMLProcessor:
    def __init__(self, mapping_path, db_url):
        self.graph = Graph()
        self.graph.parse(mapping_path, format="turtle")

        # Conexión a PostgreSQL
        self.db_url = db_url.replace("postgresql+psycopg://", "postgresql://")
        self.conn = psycopg.connect(self.db_url)

    def get_predicates_from_mapping(self):
        predicates = set()
        predicate_map_props = [RML.predicateObjectMap, RR.predicateObjectMap]
        predicate_value_props = [RML.predicateMap, RR.predicateMap]

        for pom_prop in predicate_map_props:
            for pom in self.graph.objects(None, pom_prop):
                for pm_prop in predicate_value_props:
                    for pm in self.graph.objects(pom, pm_prop):
                        # rr:constant
                        for const in self.graph.objects(pm, RR.constant):
                            predicates.add(str(const))
                        # rml:constant
                        for const in self.graph.objects(pm, RML.constant):
                            predicates.add(str(const))
                        # rml:reference
                        for ref in self.graph.objects(pm, RML.reference):
                            predicates.add(f"reference:{ref}")
        return predicates

    def get_subjects_from_db_with_templates(self):
        """
        Genera sujetos reales usando los templates del mapping.
        """
        subjects_by_predicate = {}
        predicates = self.get_predicates_from_mapping()

        for pred in predicates:
            if pred.startswith("reference:"):
                subjects_by_predicate[pred] = "→ Predicado dinámico basado en columna (no consultable aún)."
                continue

            sql_subjects = set()

            # Buscar predicateObjectMap con este predicado
            for pom in self.graph.subjects(RML.predicateObjectMap, None):
                for pm in self.graph.objects(pom, RML.predicateMap):
                    pred_constants = set(str(c) for c in self.graph.objects(pm, RML.constant))
                    pred_constants.update(str(c) for c in self.graph.objects(pm, RR.constant))
                    if pred not in pred_constants:
                        continue

                    # Obtener logicalSource y query SQL
                    for ls in self.graph.objects(pom, RML.logicalSource):
                        queries = list(self.graph.objects(ls, RML.query))

                        # Obtener template
                        templates = []
                        for sm in self.graph.subjects(RML.subjectMap, ls):
                            templates.extend(str(t) for t in self.graph.objects(sm, RML.template))

                        if not templates:
                            templates = ["http://example.org/{row}"]  # fallback

                        for q in queries:
                            sql = str(q).strip()
                            try:
                                with self.conn.cursor() as cur:
                                    cur.execute(sql)
                                    rows = cur.fetchall()
                                    columns = [desc[0] for desc in cur.description]

                                    for row in rows:
                                        row_dict = dict(zip(columns, row))
                                        for template in templates:
                                            uri = template
                                            for col, val in row_dict.items():
                                                uri = re.sub(rf"\{{{col}\}}", str(val), uri)
                                            sql_subjects.add(uri)

                            except Exception as e:
                                output_buffer.write(f"⚠ Error ejecutando query para {pred}: {e}\n")

            subjects_by_predicate[pred] = sql_subjects or "No matching subjects found."

        return subjects_by_predicate

    def close(self):
        self.conn.close()


# ==========================
# Uso
# ==========================
if __name__ == "__main__":
    # Archivo donde escribir TODO
    output_buffer = StringIO()

    mapping_file = "prueba.ttl"
    db_url = "postgresql+psycopg://postgres:1234@localhost:5432/lubm4obda"

    processor = RMLProcessor(mapping_file, db_url)

    output_buffer.write("\n👉 Predicados extraídos del mapping:\n")
    predicates = processor.get_predicates_from_mapping()
    output_buffer.write(str(predicates) + "\n\n")

    output_buffer.write("\n👉 Sujetos reales generados para cada predicado (usando templates del mapping):\n")
    result = processor.get_subjects_from_db_with_templates()

    for pred, subjects in result.items():
        output_buffer.write(f"\n🔹 {pred}\n")
        if isinstance(subjects, set):
            for s in subjects:
                output_buffer.write(f"  {s}\n")
        else:
            output_buffer.write(f"  {subjects}\n")

    processor.close()

    # Guardar en archivo TTL
    with open("output_templates.ttl", "w") as f:
        f.write(output_buffer.getvalue())

    print("\n📌 Archivo guardado como: output_templates.ttl")
