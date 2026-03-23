"""
Regex-based parser for Apex .cls files.
Extracts SOQL (Read), DML (Write), method params (Entry), returns (Exit).
Scope: single entry point per class (batch constructor+execute vs @AuraEnabled/@InvocableMethod).
"""

import re
from dataclasses import dataclass
from typing import Optional

# Sentinel DeveloperName when record types are in play but unresolved (never merges with qualified RT rows).
RT_UNSPECIFIED = "*"


# Static method call: ClassName.methodName(
STATIC_CALL = re.compile(r"\b([A-Z][a-zA-Z0-9_]*)\s*\.\s*([a-zA-Z0-9_]+)\s*\(")


@dataclass
class RawMovement:
    movement_type: str  # E, R, W, X
    data_group_ref: str
    name: str
    order_hint: int  # for ordering
    source_line: Optional[int] = None
    execution_order: Optional[int] = None  # for batch: call order in execute()
    via_class: Optional[str] = None  # when movement comes from traversed callee


# SOQL: [SELECT ... FROM ObjectName ...] — object after FROM
SOQL_FROM = re.compile(
    r"\[\s*SELECT\s+[\w\s,\.\(\):]+FROM\s+(\w+)\s+",
    re.IGNORECASE | re.DOTALL,
)

# Database.getQueryLocator([SELECT ... FROM X ...])
GET_QUERY_LOCATOR = re.compile(
    r"Database\.getQueryLocator\s*\(\s*\[\s*SELECT\s+[\w\s,\.\(\):]+FROM\s+(\w+)\s+",
    re.IGNORECASE | re.DOTALL,
)

# Database.query('SELECT ... FROM X ...') — static string
DB_QUERY_STRING = re.compile(
    r"Database\.query\s*\(\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)
FROM_IN_STRING = re.compile(r"FROM\s+(\w+)", re.IGNORECASE)

# DML: insert x; update y; upsert z; delete w;
DML_STATEMENT = re.compile(
    r"\b(insert|update|upsert|delete)\s+(\w+)\b",
    re.IGNORECASE,
)

# Database.insert(list); Database.update(list, false); etc.
DB_DML = re.compile(
    r"Database\.(insert|update|upsert|delete)\s*\(\s*([^,)]+)",
    re.IGNORECASE,
)

# EventBus.publish(listOrSingle) — platform event publish (COSMIC Write)
EVENTBUS_PUBLISH = re.compile(
    r"EventBus\.publish\s*\(\s*([^,)]+)",
    re.IGNORECASE,
)

# Class name: public class ClassName or public with sharing class ClassName
CLASS_NAME = re.compile(
    r"^\s*public\s+(?:with\s+sharing\s+|without\s+sharing\s+)?class\s+(\w+)",
    re.MULTILINE | re.IGNORECASE,
)

# Batch/Queueable detection
IMPLEMENTS_BATCHABLE = re.compile(
    r"implements\s+Database\.Batchable",
    re.IGNORECASE,
)

# Entry-point annotations
AURA_ENABLED = re.compile(r"@AuraEnabled", re.IGNORECASE)
INVOCABLE_METHOD = re.compile(r"@InvocableMethod", re.IGNORECASE)

# Constructor: public ClassName(params) — same as method but no return type before name
CONSTRUCTOR = re.compile(
    r"(?:public|private|global|protected)\s+(\w+)\s*\(([^)]*)\)\s*\{",
    re.MULTILINE | re.IGNORECASE,
)

# Method signature: (Type name, Type2 name2) and return type
# Captures: return_type, method_name, params_str
METHOD_SIGNATURE = re.compile(
    r"(?:@\w+(?:\([^)]*\))?\s*)*\s*"
    r"(?:public|private|global|protected)\s+"
    r"(?:static\s+)?"
    r"(\w+(?:<[^>]+>)?)\s+"  # return type
    r"(\w+)\s*"  # method name
    r"\(([^)]*)\)",  # params
    re.MULTILINE | re.IGNORECASE,
)

# Single param: Type name or Type<Generic> name
PARAM = re.compile(r"(\w+(?:<[^>]+>)?)\s+(\w+)\s*")

# Usage inference: Field__c = :paramName (bind variable)
USAGE_INFER = re.compile(
    r"(\w+)\s*=\s*:(\w+)\b",
    re.IGNORECASE,
)

# Variable declaration: List<X> var = or X[] var = (list/List case-insensitive)
VAR_DECL = re.compile(
    r"(?:[Ll]ist\s*<\s*(\w+)\s*>|(\w+)\s*\[\])\s+(\w+)\s*=",
    re.MULTILINE,
)

# Param name → object heuristics (common patterns)
PARAM_TO_OBJECT: dict[str, str] = {
    "fpid": "cfp_FunctionalProcess__c",
    "surveyids": "Survey__c",
    "facilityids": "Facility__c",
    "accid": "Account",
    "accountid": "Account",
    "contactids": "Contact",
    "opportunityid": "Opportunity",
    "userid": "User",
}

# Primitives and framework types — not COSMIC data groups
PRIMITIVE_TYPES = frozenset(
    {"void", "boolean", "string", "integer", "decimal", "long", "id", "double"}
)
FRAMEWORK_TYPES = frozenset({"querylocator", "database", "object", "sobject"})

# Object API name → human display label (for Entry/Exit names)
OBJECT_DISPLAY: dict[str, str] = {
    "cfp_FunctionalProcess__c": "Functional Process",
    "cfp_Data_Movements__c": "cfp_Data_Movements__c",  # keep as-is
}


def _is_batch_class(source: str) -> bool:
    """True if class implements Database.Batchable."""
    return bool(IMPLEMENTS_BATCHABLE.search(source))


def _get_entry_point_method_names(source: str, class_name: str) -> frozenset[str]:
    """
    Return method names that are entry points. For batch: constructor + static factories.
    For simple: @AuraEnabled/@InvocableMethod method, or first public static.
    """
    if _is_batch_class(source):
        names = {class_name}  # constructor
        # Static factories that return the batch (e.g. forSurveys)
        for sig in METHOD_SIGNATURE.finditer(source):
            return_type, method_name = sig.group(1), sig.group(2)
            if method_name != class_name and return_type and return_type == class_name:
                names.add(method_name)
        return frozenset(names)

    # Find first @AuraEnabled or @InvocableMethod method
    for sig in METHOD_SIGNATURE.finditer(source):
        start = sig.start()
        preceding = source[max(0, start - 200) : start]
        sig_text = sig.group(0)
        if (
            AURA_ENABLED.search(preceding)
            or INVOCABLE_METHOD.search(preceding)
            or AURA_ENABLED.search(sig_text)
            or INVOCABLE_METHOD.search(sig_text)
        ):
            return frozenset({sig.group(2)})

    # Fallback: first public static method (excluding constructor)
    for sig in METHOD_SIGNATURE.finditer(source):
        method_name = sig.group(2)
        if method_name != class_name:
            return frozenset({method_name})

    return frozenset()


def _infer_object_from_param(
    param_name: str, param_type: str, source: str, *, is_entry_point: bool = True
) -> str:
    """Infer data group from param name/type and usage in source."""
    pt_lower = param_type.lower()
    key = param_name.lower()

    if key in PARAM_TO_OBJECT:
        return PARAM_TO_OBJECT[key]

    # List<Id> / Set<Id> xxxIds → infer from name (surveyIds → Survey__c)
    if ("list<id>" in pt_lower or "set<id>" in pt_lower) and key.endswith("ids"):
        base = key[:-3]  # surveyIds -> survey, facilityIds -> facility
        return f"{base.title()}__c" if not base.endswith("__c") else base

    # Map<K,V> params: don't infer from param name (e.g. facilityAssetByFacilityId)
    if "map<" in pt_lower:
        inner = re.search(r"Map\s*<\s*\w+\s*,\s*(\w+)\s*>", param_type, re.IGNORECASE)
        if inner and inner.group(1) and inner.group(1).endswith("__c"):
            return inner.group(1)
        return "Unknown"

    # Set<Entity> where Entity is not Id — use inner type
    if "set<" in pt_lower:
        inner = re.search(r"Set\s*<\s*(\w+)\s*>", param_type, re.IGNORECASE)
        if inner and inner.group(1) and inner.group(1).lower() != "id":
            return inner.group(1)
        if "set<id>" in pt_lower and key.endswith("ids"):
            base = key[:-3]
            return f"{base.title()}__c" if not base.endswith("__c") else base
        return "Unknown"

    # Usage scan: Field__c = :paramName → Field__c (lookup field = param)
    for m in USAGE_INFER.finditer(source):
        field_or_obj = m.group(1)
        pname = m.group(2)
        if pname and pname.lower() == key and field_or_obj:
            return field_or_obj

    # Name convention: xxxId (single) — avoid Map key patterns like xxxByYyyId
    if param_name.endswith("Id") and len(param_name) > 2 and "by" not in key:
        base = param_name[:-2]
        if base.endswith("__c"):
            return base
        return f"{base}__c"  # assume custom

    # List<Entity> or Set<Entity> — use inner type
    inner = re.search(r"List\s*<\s*(\w+)\s*>|Set\s*<\s*(\w+)\s*>", param_type, re.IGNORECASE)
    if inner and (inner.group(1) or inner.group(2)):
        obj = inner.group(1) or inner.group(2)
        if obj not in FRAMEWORK_TYPES and obj.lower() != "id":
            return obj

    return "Unknown"


def extract_class_name(source: str) -> str:
    m = CLASS_NAME.search(source)
    return m.group(1) if m else "Unknown"


def find_static_calls(source: str) -> set[str]:
    """Return unique class names from static method calls (ClassName.methodName)."""
    return {m.group(1) for m in STATIC_CALL.finditer(source)}


def _line_number(source: str, pos: int) -> int:
    """Return 1-based line number for position in source."""
    return source[:pos].count("\n") + 1


def _apex_in_single_quoted_string(source: str, pos: int) -> bool:
    """True if pos is inside an Apex single-quoted string on the same line (toggle on ')."""
    line_start = source.rfind("\n", 0, pos) + 1
    segment = source[line_start:pos]
    in_string = False
    i = 0
    while i < len(segment):
        c = segment[i]
        if c == "'":
            if i + 1 < len(segment) and segment[i + 1] == "'":
                i += 2
                continue
            in_string = not in_string
        i += 1
    return in_string


def _extract_bracket_block(source: str, bracket_open_pos: int) -> str:
    """Return inner text of [...] starting at bracket_open_pos, or '' if unbalanced."""
    if bracket_open_pos >= len(source) or source[bracket_open_pos] != "[":
        return ""
    depth = 0
    i = bracket_open_pos
    while i < len(source):
        c = source[i]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return source[bracket_open_pos + 1 : i]
        i += 1
    return ""


STATIC_STRING_CONST = re.compile(
    r"private\s+static\s+final\s+String\s+(\w+)\s*=\s*'([^']+)'",
    re.IGNORECASE,
)


def _parse_record_type_string_constants(source: str) -> dict[str, str]:
    """Map constant name -> literal (e.g. LOCATION_RT -> Location)."""
    return {m.group(1): m.group(2) for m in STATIC_STRING_CONST.finditer(source)}


def _infer_record_type_from_bind(bind: str, source: str) -> Optional[str]:
    """
    Map :binding to RecordType DeveloperName using private static final String constants.
    E.g. locationRecordTypeId + LOCATION_RT = 'Location' -> 'Location'.
    """
    constants = _parse_record_type_string_constants(source)
    if not constants or not bind:
        return None
    bl = bind.lower()
    for const_name, dev_name in constants.items():
        stem = re.sub(r"_rt$", "", const_name.lower())
        stem = stem.replace("_", "")
        if len(stem) < 3:
            continue
        if stem in re.sub(r"[^a-z0-9]", "", bl):
            return dev_name
        if stem in bl:
            return dev_name
    return None


def _infer_record_type_from_method_name(method_name: str, source: str) -> Optional[str]:
    """Match method name tokens to *_RT string constants (processLocationInserts -> Location)."""
    ml = method_name.lower()
    for const_name, dev_name in _parse_record_type_string_constants(source).items():
        stem = re.sub(r"_rt$", "", const_name.lower())
        stem = stem.replace("_", "")
        if len(stem) < 3:
            continue
        if stem in ml:
            return dev_name
    return None


def _soql_has_record_type_clause(soql: str) -> bool:
    s = soql.upper()
    return "RECORDTYPEID" in s or "RECORDTYPE." in s


def _infer_record_type_from_soql_body(soql: str, source: str) -> Optional[str]:
    """Return DeveloperName from SOQL, or None if not resolved."""
    m_lit = re.search(
        r"RecordType\.DeveloperName\s*=\s*'([^']+)'",
        soql,
        re.IGNORECASE,
    )
    if m_lit:
        return m_lit.group(1)
    m_lit2 = re.search(
        r'RecordType\.DeveloperName\s*=\s*"([^"]+)"',
        soql,
        re.IGNORECASE,
    )
    if m_lit2:
        return m_lit2.group(1)
    m_bind = re.search(r"RecordTypeId\s*=\s*:(\w+)", soql, re.IGNORECASE)
    if m_bind:
        return _infer_record_type_from_bind(m_bind.group(1), source)
    return None


def _call_site_reads_for_parametric_rt(
    method_name: str, obj: str, bind_name: str, source: str
) -> list[tuple[str, int]]:
    """
    When SOQL uses :recordTypeId and bind does not map to constants, infer one Read per
    call site if the second argument maps (e.g. getExistingAssetsByExtId(a, locationRecordTypeId)).
    """
    if _infer_record_type_from_bind(bind_name, source):
        return []
    pat = re.compile(rf"\b{re.escape(method_name)}\s*\(\s*[^,]+,\s*(\w+)\s*\)")
    out: list[tuple[str, int]] = []
    for m in pat.finditer(source):
        arg2 = m.group(1)
        dev = _infer_record_type_from_bind(arg2, source)
        if dev:
            out.append((format_data_group_ref(obj, dev), _line_number(source, m.start())))
    return out


def format_data_group_ref(obj: str, record_type_dev: Optional[str], *, unspec: bool = False) -> str:
    """
    dataGroupRef: Object, Object::DeveloperName, or Object::* (unresolved RT, never merges with qualified).
    """
    if unspec:
        return f"{obj}::{RT_UNSPECIFIED}"
    if record_type_dev and record_type_dev != RT_UNSPECIFIED:
        return f"{obj}::{record_type_dev}"
    return obj


def _class_declares_rt_named_constants(source: str) -> bool:
    """True if class has `private static final String FOO_RT = '...'` style constants."""
    return bool(
        re.search(
            r"private\s+static\s+final\s+String\s+\w+_RT\s*=",
            source,
            re.IGNORECASE,
        )
    )


def _infer_write_data_group_ref(
    obj: str, source_line: int, source: str, boundaries: list[tuple[str, int]]
) -> str:
    """Combine object with RT from method name, or Object::* when RT constants exist but not inferred."""
    method = _method_containing_line(boundaries, source_line)
    if method:
        dev = _infer_record_type_from_method_name(method, source)
        if dev:
            return format_data_group_ref(obj, dev)
    if _class_declares_rt_named_constants(source):
        return format_data_group_ref(obj, None, unspec=True)
    return obj


def find_reads(source: str) -> list[RawMovement]:
    """Collect all reads (including duplicates) so execution_order can pick earliest."""
    movements: list[RawMovement] = []
    boundaries = _get_method_boundaries(source)

    def append_read(data_group_ref: str, line: int):
        movements.append(
            RawMovement(
                movement_type="R",
                data_group_ref=data_group_ref,
                name=f"Read {data_group_ref} list",
                order_hint=len(movements) + 1,
                source_line=line,
            )
        )

    def process_soql_block(obj: str, line: int, soql_body: str) -> None:
        if not obj:
            return
        if soql_body and _soql_has_record_type_clause(soql_body):
            rt = _infer_record_type_from_soql_body(soql_body, source)
            if rt is None:
                m_bind = re.search(
                    r"RecordTypeId\s*=\s*:(\w+)", soql_body, re.IGNORECASE
                )
                if m_bind:
                    meth = _method_containing_line(boundaries, line)
                    if meth:
                        sites = _call_site_reads_for_parametric_rt(
                            meth, obj, m_bind.group(1), source
                        )
                        if sites:
                            for dg, ln in sites:
                                append_read(dg, ln)
                            return
                append_read(format_data_group_ref(obj, None, unspec=True), line)
                return
            append_read(format_data_group_ref(obj, rt), line)
            return
        append_read(obj, line)

    # Inline SOQL [SELECT ... FROM Obj ...]
    for m in SOQL_FROM.finditer(source):
        bracket_start = m.start()
        soql_body = _extract_bracket_block(source, bracket_start)
        process_soql_block(
            m.group(1), _line_number(source, m.start()), soql_body
        )

    # Database.getQueryLocator([SELECT ...])
    for m in GET_QUERY_LOCATOR.finditer(source):
        inner_bracket = source.find("[", m.start())
        soql_body = (
            _extract_bracket_block(source, inner_bracket) if inner_bracket >= 0 else ""
        )
        process_soql_block(
            m.group(1), _line_number(source, m.start()), soql_body
        )

    # Database.query('...')
    for m in DB_QUERY_STRING.finditer(source):
        qstr = m.group(1)
        inner = FROM_IN_STRING.search(qstr)
        if inner:
            obj = inner.group(1)
            process_soql_block(
                obj, _line_number(source, m.start()), qstr
            )

    return movements


def find_writes(source: str) -> list[RawMovement]:
    """Collect all writes (including duplicates) so execution_order can pick earliest."""
    movements: list[RawMovement] = []
    boundaries = _get_method_boundaries(source)

    # Build var name → type map from declarations
    var_types: dict[str, str] = {}
    for m in VAR_DECL.finditer(source):
        list_type = m.group(1)
        array_type = m.group(2)
        var_name = m.group(3)
        obj = list_type or array_type
        if obj:
            var_types[var_name] = obj

    # Also from method params: List<Survey__c> surveys
    for sig in METHOD_SIGNATURE.finditer(source):
        params_str = sig.group(3)
        for pm in PARAM.finditer(params_str):
            ptype, pname = pm.group(1), pm.group(2)
            if "List<" in ptype or "list<" in ptype:
                inner = re.search(r"List\s*<\s*(\w+)\s*>", ptype, re.IGNORECASE)
                if inner:
                    var_types[pname] = inner.group(1)

    def resolve_type(var_name: str) -> str:
        return var_types.get(var_name, "Unknown")

    def add(obj: str, dml: str, line: int):
        if obj and obj != "Unknown":
            dg = _infer_write_data_group_ref(obj, line, source, boundaries)
            movements.append(
                RawMovement(
                    movement_type="W",
                    data_group_ref=dg,
                    name=f"{dml.title()} {dg} records",
                    order_hint=len(movements) + 1,
                    source_line=line,
                )
            )

    # DML statement: insert x; update y; (skip comments and matches inside string literals)
    for m in DML_STATEMENT.finditer(source):
        if _apex_in_single_quoted_string(source, m.start()):
            continue
        line_start = source.rfind("\n", 0, m.start()) + 1
        line = source[line_start : m.end()]
        if "//" in line[: line.find(m.group(0))]:
            continue
        dml, var = m.group(1), m.group(2)
        obj = resolve_type(var)
        add(obj, dml, _line_number(source, m.start()))

    # Database.dml(list, ...)
    for m in DB_DML.finditer(source):
        dml = m.group(1)
        arg = m.group(2).strip().split(".")[-1]  # handle obj.field
        var = re.match(r"(\w+)", arg)
        if var:
            obj = resolve_type(var.group(1))
            add(obj, dml, _line_number(source, m.start()))

    # EventBus.publish(events) — infer data group from List<Event__e> / SObject list var
    for m in EVENTBUS_PUBLISH.finditer(source):
        if _apex_in_single_quoted_string(source, m.start()):
            continue
        line_start = source.rfind("\n", 0, m.start()) + 1
        line_text = source[line_start : m.end()]
        if "//" in line_text[: line_text.find(m.group(0))]:
            continue
        arg = m.group(1).strip().split(".")[-1]
        var = re.match(r"(\w+)", arg)
        if not var:
            continue
        obj = resolve_type(var.group(1))
        if not obj or obj == "Unknown":
            continue
        line = _line_number(source, m.start())
        dg = _infer_write_data_group_ref(obj, line, source, boundaries)
        movements.append(
            RawMovement(
                movement_type="W",
                data_group_ref=dg,
                name=f"EventBus.publish {dg}",
                order_hint=len(movements) + 1,
                source_line=line,
            )
        )

    return movements


BATCH_LIFECYCLE_METHODS = frozenset({"start", "execute", "finish"})


def _collect_entry_point_params(source: str) -> list[tuple[str, str, int]]:
    """Collect (param_name, data_group, source_line) from all entry points. Used by get_entry_points and find_entries."""
    result: list[tuple[str, str, int]] = []
    seen: set[str] = set()
    class_name = extract_class_name(source)
    entry_point_names = _get_entry_point_method_names(source, class_name)

    def process_params(params_str: str, line: int):
        for pm in PARAM.finditer(params_str):
            ptype, pname = pm.group(1), pm.group(2)
            if "BatchableContext" in ptype or "QueueableContext" in ptype:
                continue
            if "List<" in ptype and "sObject" in ptype.lower():
                continue
            if ptype and ptype.upper() in ("STRING", "INTEGER", "BOOLEAN"):
                continue
            obj = _infer_object_from_param(pname, ptype, source)
            if obj == "Unknown":
                continue
            key = f"E:{pname}:{obj}"
            if key not in seen:
                seen.add(key)
                result.append((pname, obj, line))

    if class_name in entry_point_names:
        for m in CONSTRUCTOR.finditer(source):
            ctor_name, params_str = m.group(1), m.group(2)
            if ctor_name == class_name and params_str.strip():
                process_params(params_str, _line_number(source, m.start()))

    for sig in METHOD_SIGNATURE.finditer(source):
        method_name = sig.group(2)
        if method_name not in entry_point_names:
            continue
        if method_name == class_name:
            continue
        params_str = sig.group(3)
        if params_str.strip():
            process_params(params_str, _line_number(source, sig.start()))
        if not _is_batch_class(source):
            break

    return result


def get_entry_points(source: str) -> list[dict[str, str]]:
    """Return list of entry point params for multi-process detection. Each dict has 'param' and 'dataGroup'."""
    return [
        {"param": pname, "dataGroup": obj}
        for pname, obj, _ in _collect_entry_point_params(source)
    ]


def find_entries(source: str, *, entry_param_filter: Optional[str] = None) -> list[RawMovement]:
    """Extract Entry movements from entry points. If entry_param_filter is set, only include that param."""
    params_list = _collect_entry_point_params(source)
    if entry_param_filter:
        filter_lower = entry_param_filter.strip().lower()
        params_list = [(p, o, ln) for p, o, ln in params_list if p.lower() == filter_lower]

    movements: list[RawMovement] = []
    for i, (pname, obj, line) in enumerate(params_list):
        label = OBJECT_DISPLAY.get(obj, obj)
        suffix = f" ({label})" if obj != "Unknown" else ""
        movements.append(
            RawMovement(
                movement_type="E",
                data_group_ref=obj,
                name=f"Receive {pname}{suffix}",
                order_hint=i + 1,
                source_line=line,
            )
        )
    return movements


def find_exits(source: str) -> list[RawMovement]:
    """Extract Exit movements only from entry-point method. Batch has no Exit."""
    movements: list[RawMovement] = []
    seen: set[str] = set()
    if _is_batch_class(source):
        return movements  # execute returns void; start QueryLocator is internal

    class_name = extract_class_name(source)
    entry_point_names = _get_entry_point_method_names(source, class_name)

    for sig in METHOD_SIGNATURE.finditer(source):
        return_type = sig.group(1)
        method_name = sig.group(2)
        if method_name not in entry_point_names:
            continue
        if return_type.upper() in ("VOID", "void"):
            continue

        inner = re.search(
            r"List\s*<\s*(\w+)\s*>|Set\s*<\s*(\w+)\s*>", return_type, re.IGNORECASE
        )
        obj = (inner.group(1) or inner.group(2)) if inner else return_type.strip()
        if not obj:
            continue
        obj_lower = obj.lower()
        if obj_lower in PRIMITIVE_TYPES or obj_lower in FRAMEWORK_TYPES:
            continue
        if obj in ("QueryLocator", "Database", "Object", "sObject", "Boolean", "Map", "Set"):
            continue
        # Skip generic Map/Set return types (Map<Id, Survey__c> etc. — internal)
        if "Map<" in return_type or "Set<" in return_type:
            continue

        key = f"X:{obj}"
        if key not in seen:
            seen.add(key)
            movements.append(
                RawMovement(
                    movement_type="X",
                    data_group_ref=obj,
                    name=f"Return {obj} list",
                    order_hint=len(movements) + 1,
                )
            )

    return movements


def _get_method_boundaries(source: str) -> list[tuple[str, int]]:
    """Return [(method_name, start_line), ...] for each method/constructor, sorted by line."""
    result: list[tuple[str, int]] = []
    for m in CONSTRUCTOR.finditer(source):
        result.append((m.group(1), _line_number(source, m.start())))
    for m in METHOD_SIGNATURE.finditer(source):
        method_name = m.group(2)
        if method_name != extract_class_name(source):  # skip constructor (already in CONSTRUCTOR)
            result.append((method_name, _line_number(source, m.start())))
    return sorted(result, key=lambda x: x[1])


def _method_containing_line(boundaries: list[tuple[str, int]], line: int) -> Optional[str]:
    """Return method name that contains the given line, or None."""
    best: Optional[tuple[str, int]] = None
    for name, start in boundaries:
        if start <= line:
            best = (name, start)
    return best[0] if best else None


def _get_batch_call_order(source: str, class_name: str) -> dict[str, int]:
    """
    For batch classes: return method_name -> first_call_line.
    Constructor calls get order 0; execute() calls get their line number.
    """
    boundaries = _get_method_boundaries(source)
    lines = source.split("\n")
    call_order: dict[str, int] = {}
    method_names = {name for name, _ in boundaries}

    def find_calls_in_range(
        start_line: int, end_line: int, base_order: int, exclude: Optional[set[str]] = None
    ) -> None:
        skip = exclude or set()
        for name in method_names:
            if name in call_order or name in skip:
                continue
            for i in range(start_line - 1, min(end_line, len(lines))):
                if re.search(rf"\b{re.escape(name)}\s*\(", lines[i]):
                    call_order[name] = base_order + i
                    break

    # Constructor bodies (process all to capture loadRecordTypeIds etc.)
    for m in CONSTRUCTOR.finditer(source):
        if m.group(1) == class_name:
            start_line = _line_number(source, m.start())
            brace = source.find("{", m.start())
            depth, end = 1, brace + 1
            while depth and end < len(source):
                if source[end] == "{":
                    depth += 1
                elif source[end] == "}":
                    depth -= 1
                end += 1
            end_line = _line_number(source, end - 1)
            find_calls_in_range(start_line, end_line, 0)

    # Execute method body (allow param names: Database.BatchableContext bc, List<...> scope)
    execute_pattern = re.compile(
        r"\bvoid\s+execute\s*\(\s*Database\.BatchableContext\s+\w+\s*,\s*List<\w+>\s+\w+\s*\)",
        re.IGNORECASE,
    )
    for m in execute_pattern.finditer(source):
        start_line = _line_number(source, m.start())
        brace = source.find("{", m.start())
        depth, end = 1, brace + 1
        while depth and end < len(source):
            if source[end] == "{":
                depth += 1
            elif source[end] == "}":
                depth -= 1
            end += 1
        end_line = _line_number(source, end - 1)
        find_calls_in_range(start_line, end_line, 1000, exclude={"execute"})
        break

    return call_order


def _apply_execution_order(source: str, movements: list[RawMovement], class_name: str) -> None:
    """Set execution_order on R/W movements for batch classes to reflect call order."""
    if not _is_batch_class(source):
        return
    call_order = _get_batch_call_order(source, class_name)
    boundaries = _get_method_boundaries(source)

    for m in movements:
        if m.movement_type not in ("R", "W") or not m.source_line:
            continue
        method = _method_containing_line(boundaries, m.source_line)
        if method and method in call_order:
            m.execution_order = call_order[method]


def parse(source: str, *, entry_param_filter: Optional[str] = None) -> tuple[str, list[RawMovement]]:
    """Parse Apex source; return class name and all raw movements."""
    class_name = extract_class_name(source)
    entries = find_entries(source, entry_param_filter=entry_param_filter)
    reads = find_reads(source)
    writes = find_writes(source)
    exits = find_exits(source)

    all_movements = entries + reads + writes + exits
    _apply_execution_order(source, all_movements, class_name)
    return class_name, all_movements
