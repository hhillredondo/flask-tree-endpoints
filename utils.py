from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from gremlin_python.process.graph_traversal import __, elementMap, otherV
from gremlin_python.process.traversal import T

fmt = "%Y-%m-%dT%H:%M:%SZ"


def _coerce_vertex_property_value(value):
    if isinstance(value, list):
        if len(value) == 1:
            return value[0]
        return value
    if isinstance(value, dict) and "value" in value:
        return value.get("value")
    return value


def normalize_vertex(vertex):
    try:
        if vertex is None:
            return None

        if isinstance(vertex, dict):
            normalized_data = {}
            if "id" in vertex:
                normalized_data["id"] = str(vertex.get("id"))
            elif T.id in vertex:
                normalized_data["id"] = str(vertex.get(T.id))

            if "label" in vertex:
                normalized_data["label"] = vertex.get("label")
            elif T.label in vertex:
                normalized_data["label"] = vertex.get(T.label)

            for key, value in vertex.items():
                if key in ("id", "label", T.id, T.label):
                    continue
                normalized_data[str(key)] = _coerce_vertex_property_value(value)
            return normalized_data

        normalized_data = {
            "id": str(vertex.id),
            "label": vertex.label,
        }

        properties = {}
        properties_iter = getattr(vertex, "properties", None)
        if properties_iter:
            for prop in properties_iter:
                key = getattr(prop, "key", None)
                value = getattr(prop, "value", None)
                if key is None:
                    continue
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
    born = g.V(vertex_id).values("born").next()
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
    return g.V(vertex_id).out("parent").values("born").toList()


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
        .where(__.in_("parent").hasId(parent2_id))
        .elementMap()
        .toList()
    )
    return common_children


def get_common_children_birth_dates(parent1_id: int, parent2_id: int, g):
    common_children_born = (
        g.V(parent1_id)
        .out("parent")
        .where(__.in_("parent").hasId(parent2_id))
        .values("born")
        .toList()
    )
    return common_children_born


def check_date_is_in_period(date: str, start: str, end: Optional[str]):
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
        g.V(husband_id).bothE("spouse").where(__.otherV().hasId(wife_id)).id_().next()
    )

    return marriage_id


def get_marriage_date(husband_id: int, wife_id: int, g):
    marriage_date = (
        g.V(husband_id)
        .bothE("spouse")
        .where(__.otherV().hasId(wife_id))
        .values("married")
        .next()
    )

    return marriage_date


def get_divorce_date(husband_id: int, wife_id: int, g):
    try:
        divorced_date = (
            g.V(husband_id)
            .bothE("spouse")
            .where(__.otherV().hasId(wife_id))
            .values("divorced")
            .next()
        )
        return divorced_date
    except Exception:
        return None
