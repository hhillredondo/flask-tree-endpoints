from typing import List, Dict, Any
from datetime import datetime, timedelta
from gremlin_python.process.graph_traversal import __, elementMap, otherV


fmt = "%Y-%m-%dT%H:%M:%SZ"


def normalize_vertex(vertex):
    try:
        normalized_data = {
            "id": str(vertex.id),
            "label": vertex.label,
        }

        properties = {}
        for prop in vertex.properties:
            key = prop.key
            value = prop.value
            properties[key] = value

        normalized_data.update(properties)
        return normalized_data
    except Exception as e:
        print(f"Error normalizing data: {e}")
        raise


def normalize_edge(edge):
    return {
        "id": str(edge.id),
        "label": edge.label,
        "source_id": str(edge.outV.id),
        "target_id": str(edge.inV.id),
    }


def get_gender(vertex_id: int, g):
    gender = g.V(vertex_id).values("gender").next()
    return gender


def get_born(vertex_id: int, g):
    born = g.V(vertex_id).values("born")
    return born


def get_died(vertex_id: int, g):
    died_iter = g.V(vertex_id).values("died")
    if died_iter.hasNext():
        died = died_iter.next()
        return died
    else:
        return None


def get_potential_spouse_at_child_birth(vertex_id: int, child_born: str, g):
    try:
        child_date = datetime.strptime(child_born, fmt)
    except ValueError:
        return None

    for edge_data in (
        g.V(vertex_id)
        .bothE("spouse")
        .project("edge", "spouse")
        .by(elementMap())
        .by(otherV().elementMap())
        .toList()
    ):
        edge = edge_data["edge"]
        spouse = edge_data["spouse"]

        married_str = edge.get("married")
        divorced_str = edge.get("divorced")

        try:
            married_date = datetime.strptime(married_str, fmt)
            divorced_date = (
                datetime.strptime(divorced_str, fmt) if divorced_str else None
            )
        except (TypeError, ValueError):
            continue

        if married_date <= child_date:
            cutoff_date = (
                divorced_date + timedelta(days=9 * 30) if divorced_date else None
            )
            if not divorced_date or child_date <= cutoff_date:
                return spouse

    return None


def get_parents_number(vertex_id: int, g):
    return g.V(vertex_id).in_("parent").count().next()


def get_parents_other_children_birth_dates(vertex_id: int, g):
    children = g.V(vertex_id).out("parent").toList()

    return [child.valueMap().get("born")[0] for child in children]


def get_marriages(vertex_id: int, g):
    edges = g.V(vertex_id).bothE("spouse").elementMap().toList()

    return [
        {"married": edge.get("married"), "divorced": edge.get("divorced")}
        for edge in edges
    ]


def get_children(vertex_id: int, g) -> List[Dict[str, Any]]:
    children = g.V(vertex_id).out("parent").elementMap().toList()
    return children


def get_common_children(parent1_id: int, parent2_id: int, g):
    common_children = (
        g.V(parent1_id)
        .out("parent")
        .where(__.in_("parent").is_(parent2_id))
        .elementMap()
        .toList()
    )
    return common_children


def get_common_children_birth_dates(parent1_id: int, parent2_id: int, g):
    common_children_born = (
        g.V(parent1_id)
        .out("parent")
        .where(__.in_("parent").is_(parent2_id))
        .values("born")
        .toList()
    )
    return common_children_born


def check_date_is_in_period(date: str, start: str, end: str | None):
    try:
        date_date = datetime.strptime(date, fmt)
        start_date = datetime.strptime(start, fmt)

        if not end and start_date < date_date:
            return True

        end_date = datetime.strptime(end, fmt)

        if start_date < date_date < end_date + timedelta(days=9 * 30):
            return True
        return False
    except ValueError:
        return None


def get_marriage_id(husband_id: int, wife_id: int, g):
    marriage_id = (
        g.V(husband_id).bothE("spouse").where(__.otherV().hasId(wife_id)).id().next()
    )
    return marriage_id
