# Neptune Graph Data Model

## Overview

Amazon Neptune is a schema-free graph database — there is no way to enforce a
schema at the database level. The "schema" described here is the implicit
contract enforced by the Flask API's validation layer.

All graph data lives in a single Neptune cluster and is logically partitioned
per tree using the internal `_partitionKey` vertex/edge property (format:
`<userId>_<treeId>`).

---

## Vertices

Only one vertex label exists: **`_Member`**.

### `_Member` properties

| Property | Type | Required | Mutable | Constraints |
|---|---|---|---|---|
| `id` | string | auto-generated | no | Assigned by Neptune |
| `name` | string | yes | yes | Max 50 chars; alphabetic, spaces, hyphens and apostrophes only (`^([a-zA-Z\s'-]+)?$`) |
| `surname` | string | yes | yes | Same rules as `name` |
| `gender` | string | yes | no | `"male"` or `"female"` |
| `description` | string | yes | yes | Max 10 000 characters |
| `born` | string | yes | **no** (immutable) | ISO 8601 datetime `YYYY-MM-DDTHH:MM:SSZ` |
| `died` | string | no (optional) | **no** (immutable) | Same format as `born`; must be after `born` |
| `pic` | string | yes | yes | Valid URL (http / https / ftp / s3). After upload, stored as an S3 URI |
| `photos` | string | yes | yes | Valid URL (http / https / ftp / s3). After upload, stored as an S3 URI pointing to a prefix |
| `profession` | string | no (optional) | yes | Free-text string (e.g. "doctor", "carpenter") |
| `birth_location` | string | no (optional) | yes | Free-text string (e.g. "London", "Madrid") |
| `death_location` | string | no (optional) | yes | Free-text string (e.g. "London", "Madrid") |
| `height` | number | no (optional) | yes | Height in centimetres |
| `documents` | string | no (optional) | yes | S3 URI pointing to a prefix (set after first document upload) |
| `_partitionKey` | string | auto-set | no | Internal system property (`<userId>_<treeId>`) |

> **Note on `born` / `died` immutability:** The `update_member` endpoint
> explicitly rejects any request that includes `born` or `died` in the payload.

---

## Edges

Two edge labels exist: **`parent`** and **`spouse`**.

### `parent` edge

Represents a parent → child relationship.

| Aspect | Detail |
|---|---|
| **Direction** | Parent vertex → Child vertex |
| **User properties** | _none_ |
| **System properties** | `_partitionKey` |

Each child may have **at most 2** incoming `parent` edges (see
[validation rules](#tree-model-validation-rules) below).

### `spouse` edge

Represents a marriage between two members.

| Aspect | Detail |
|---|---|
| **Direction** | Stored as a single edge but always queried with `bothE("spouse")` (treated as bidirectional) |
| **User properties** | see table below |
| **System properties** | `_partitionKey` |

#### `spouse` edge properties

| Property | Type | Required | Constraints |
|---|---|---|---|
| `married` | string | yes | ISO 8601 datetime `YYYY-MM-DDTHH:MM:SSZ` |
| `divorced` | string | yes (can be `null` / empty) | Same format; must be after `married` if present |

---

## Visual Schema

```
  ┌──────────────────────────────────────────┐
  │              _Member                     │
  │──────────────────────────────────────────│
  │  id              (auto, string)          │
  │  name            (string, required)      │
  │  surname         (string, required)      │
  │  gender          (string, required)      │
  │  description     (string, required)      │
  │  born            (string, required)      │
  │  died            (string, optional)      │
  │  pic             (string, required)      │
  │  photos          (string, required)      │
  │  profession      (string, optional)      │
  │  birth_location  (string, optional)      │
  │  death_location  (string, optional)      │
  │  height          (number, optional)      │
  │  documents       (string, optional)      │
  │  _partitionKey   (string, internal)      │
  └────────────┬──────────────┬──────────────┘
             │              │
      parent │              │ spouse
      (no props)            │ (married, divorced)
             │              │
             ▼              ▼
         _Member        _Member
```

---

## Tree Model Validation Rules

The API enforces the following biological and legal plausibility rules.
All validations are applied **before** any write is committed to Neptune.

### Lifespan & dates

| Rule | Detail | Source |
|---|---|---|
| Birth before death | `born` must be earlier than `died` | `validate_life_date_order` |
| Maximum lifespan | A member cannot live longer than **120 years** | `validate_max_lifespan` |
| Date format | All dates must match `YYYY-MM-DDTHH:MM:SSZ` | `validate_date_format` |

### Parentage

| Rule | Detail | Source |
|---|---|---|
| Maximum 2 parents | A member may have at most 2 `parent` edges pointing to it | `validate_parents_number` |
| If 1 parent exists | Adding a second parent must go through the **create-spouse** flow (spouse of the existing parent) | `validate_parents_number` |
| Parent alive at child's birth | The child must be born within the parent's lifetime (between `born` and `died`, or after `born` if the parent is still alive) | `validate_parent_is_alive_and_fertile` |
| Minimum parental age | A parent must be at least **~12 years 9 months** old at the child's birth | `validate_parent_is_alive_and_fertile` |
| Maximum paternal age | A **father** must be under **100 years** old at the child's birth | `validate_parent_is_alive_and_fertile` |
| Maximum maternal age | A **mother** must be under **60 years** old at the child's birth | `validate_parent_is_alive_and_fertile` |

### Sibling spacing

| Rule | Detail | Source |
|---|---|---|
| 9-month gap | Siblings (from the same parent) must be born at least **9 months** apart | `validate_siblings_birth_dates` |
| Same-date births (multiples) | Up to **8 siblings** may share the exact same birth date (i.e. octuplets maximum) | `validate_siblings_birth_dates` |
| Both parents checked | When a child is added, the sibling-spacing rule is validated against **both** the parent's and the spouse's other children | `create_child` |

### Marriage

| Rule | Detail | Source |
|---|---|---|
| Heterosexual only | Spouses must be of **opposite genders** | `validate_heterosexual_marriage` |
| Minimum marriage age | Both parties must be at least **16 years** old at the marriage date | `verify_legal_marriage_age` |
| Marriage before divorce | `divorced` date (if set) must be after `married` date | `verify_marriage_divorce_date_order` |
| No bigamy | Both groom and bride must be **single** (not currently married) at the time of the new marriage | `validate_groom_and_bride_single_status` |
| Children born in marriage | Common children must be born **during the marriage** or up to **9 months after divorce** | `verify_common_children_born_in_marriage` |

### Automatic spouse-child linking

When a spouse is created, the system automatically identifies "common children":
children of the existing spouse who have only 1 parent, were born during the
marriage period, and for whom the new spouse passes the fertility checks. A
`parent` edge is created from the new spouse to each such child automatically.

### Deletion

| Rule | Detail | Source |
|---|---|---|
| Graph connectivity maintained | A member can be deleted as long as the graph remains connected after deletion (all remaining members can still reach each other) | `verify_graph_remains_connected` / `verify_member_is_deletable` / `delete_member_query` |
| Last member deletes tree | If the member being deleted is the **only** member in the partition, the entire tree is deleted instead | `delete_member_query` |

### Data-type validations (applied on create & update)

| Field | Rule | Source |
|---|---|---|
| `name` / `surname` | String, max 50 chars, `^([a-zA-Z\s'-]+)?$` | `validate_member_name` |
| `gender` | Must be `"male"` or `"female"` | `validate_gender` |
| `description` | String, max 10 000 chars | `validate_member_description` |
| `pic` / `photos` | Valid URL with scheme `http`, `https`, `ftp`, or `s3` | `validate_url` |
| Dates | Must parse as `%Y-%m-%dT%H:%M:%SZ` | `validate_date_format` |

