"""Static parsing helpers for LWC COSMIC measurement."""

from __future__ import annotations

import re
from dataclasses import dataclass, field as dc_field
from html.parser import HTMLParser
from pathlib import Path

from shared.models import LwcRawMovement, RawMovement

# ---------------------------------------------------------------------------
# Regex helpers (kept for wire/LDS/schema/Apex detection)
# ---------------------------------------------------------------------------

_APEX_IMPORT_RE = re.compile(
    r"@salesforce/apex/(?P<class_name>[A-Za-z_][A-Za-z0-9_]*)\.(?P<method_name>[A-Za-z_][A-Za-z0-9_]*)"
)
_TEMPLATE_BINDING_RE = re.compile(r"\{[A-Za-z_][A-Za-z0-9_.]*\}")
_LDS_READ_RE = re.compile(r"\b(getRecord|getListUi|getRecordUi|getObjectInfo)\s*\(")
_LDS_WRITE_RE = re.compile(r"\b(createRecord|updateRecord|deleteRecord)\s*\(")

_APEX_IMPORT_VAR_RE = re.compile(
    r"import\s+(?P<var>\w+)\s+from\s+['\"]@salesforce/apex/"
)
_APEX_IMPORT_VAR_CLASS_RE = re.compile(
    r"import\s+(?P<var>\w+)\s+from\s+['\"]@salesforce/apex/"
    r"(?P<class>[A-Za-z_][A-Za-z0-9_]*)\."
)
_SCHEMA_IMPORT_RE = re.compile(
    r"import\s+(?P<var>\w+)\s+from\s+['\"]@salesforce/schema/"
    r"(?P<object>[A-Za-z_][A-Za-z0-9_]*)\.(?P<field>[A-Za-z_][A-Za-z0-9_]*)['\"]"
)
_WIRE_CALL_RE = re.compile(
    r"@wire\s*\(\s*(?P<adapter>[A-Za-z_][A-Za-z0-9_]*)(?:\s*,\s*\{(?P<args>[^}]*)\})?\s*\)"
)
_WIRE_FIELDS_RE = re.compile(r"fields\s*:\s*\[(?P<fields>[^\]]*)\]")

_IGNORED_LWC_ADAPTERS = {"CurrentPageReference", "PageReference"}
_IGNORED_LWC_OBJECTS = {"User", "PageReference"}

_HANDLER_BINDING_RE = re.compile(r"^\{([A-Za-z_][A-Za-z0-9_]*)\}/?$")
_SAVE_LABELS_RE = re.compile(r"\b(save|submit|confirm|done|cancel)\b", re.IGNORECASE)
_PAGINATION_LABELS_RE = re.compile(r"\b(previous|next|prev)\b", re.IGNORECASE)

_METHOD_DEF_RE = re.compile(
    r"(?:^|\n)\s{0,8}(?:async\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\([^)\n]*\)\s*\{",
    re.MULTILINE,
)
_JS_KEYWORDS = frozenset({
    "if", "else", "for", "while", "switch", "catch", "function", "return",
    "constructor", "connectedCallback", "disconnectedCallback", "renderedCallback",
    "get", "set", "class", "import", "export", "const", "let", "var", "new",
    "try", "finally", "do", "typeof", "instanceof",
})

# ---------------------------------------------------------------------------
# HTML element tree
# ---------------------------------------------------------------------------

@dataclass
class _HtmlNode:
    tag: str
    attrs: dict
    children: list = dc_field(default_factory=list)
    is_for_each: bool = False

    def handlers(self) -> dict[str, str]:
        """Return {event_attr: handler_method_name} for on* attributes."""
        result: dict[str, str] = {}
        for k, v in self.attrs.items():
            if not k.startswith("on"):
                continue
            m = _HANDLER_BINDING_RE.match(v or "")
            if m:
                result[k] = m.group(1)
        return result


class _HtmlTreeBuilder(HTMLParser):
    _VOID = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }

    def __init__(self) -> None:
        super().__init__()
        self._root = _HtmlNode("__root__", {})
        self._stack: list[_HtmlNode] = [self._root]

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attr_dict = dict(attrs)
        node = _HtmlNode(
            tag=tag,
            attrs=attr_dict,
            is_for_each="for:each" in attr_dict,
        )
        self._stack[-1].children.append(node)
        if tag not in self._VOID:
            self._stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        if len(self._stack) > 1:
            self._stack.pop()

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        attr_dict = dict(attrs)
        node = _HtmlNode(
            tag=tag,
            attrs=attr_dict,
            is_for_each="for:each" in attr_dict,
        )
        self._stack[-1].children.append(node)

    @property
    def root(self) -> _HtmlNode:
        return self._root


# ---------------------------------------------------------------------------
# Handler collection
# ---------------------------------------------------------------------------

@dataclass
class _HandlerInfo:
    event: str
    handler_name: str
    element_tag: str
    element_attrs: dict
    inside_for_each: bool


def _collect_handlers(node: _HtmlNode, inside_for_each: bool = False) -> list[_HandlerInfo]:
    """Recursively collect all event handler info from a node and its descendants."""
    is_for_each = inside_for_each or node.is_for_each
    result: list[_HandlerInfo] = []
    for event, handler in node.handlers().items():
        result.append(_HandlerInfo(
            event=event,
            handler_name=handler,
            element_tag=node.tag,
            element_attrs=node.attrs,
            inside_for_each=is_for_each,
        ))
    for child in node.children:
        result.extend(_collect_handlers(child, is_for_each))
    return result


# ---------------------------------------------------------------------------
# Block classification
# ---------------------------------------------------------------------------

@dataclass
class _BlockInfo:
    block_label: str
    e_name: str
    data_group: str
    handler_names: list[str]
    order_hint: int


def _classify_node(node: _HtmlNode, base_order_hint: int) -> list[_BlockInfo]:
    """Classify a structural container node into 0 or more interaction blocks."""
    handlers = _collect_handlers(node)
    if not handlers:
        return []

    row_edit_handlers = [h for h in handlers if h.inside_for_each]
    select_all_handlers = [
        h for h in handlers
        if not h.inside_for_each
        and h.element_tag == "input"
        and h.element_attrs.get("type", "").lower() == "checkbox"
        and h.event in ("onclick", "onchange")
    ]
    filter_handlers = [h for h in handlers if h.event == "oncustomlookupupdateevent"]
    button_handlers = [
        h for h in handlers
        if h.element_tag in ("lightning-button", "button") and h.event == "onclick"
    ]
    save_handlers = [
        h for h in button_handlers
        if _SAVE_LABELS_RE.search(h.element_attrs.get("label", ""))
        or _SAVE_LABELS_RE.search(h.element_attrs.get("value", ""))
    ]
    pagination_handlers = [
        h for h in button_handlers
        if _PAGINATION_LABELS_RE.search(h.element_attrs.get("label", ""))
        or _PAGINATION_LABELS_RE.search(h.element_attrs.get("value", ""))
    ]

    blocks: list[_BlockInfo] = []
    hint = base_order_hint

    if filter_handlers:
        all_names = list(dict.fromkeys(h.handler_name for h in handlers))
        blocks.append(_BlockInfo("filter", "Receive filter criteria", "FilterCriteria", all_names, hint))
        hint += 1

    if select_all_handlers and not filter_handlers:
        names = list(dict.fromkeys(
            h.handler_name for h in handlers if not h.inside_for_each
        ))
        blocks.append(_BlockInfo("select-all", "Receive select-all", "RowSelection", names, hint))
        hint += 1

    if row_edit_handlers:
        names = list(dict.fromkeys(h.handler_name for h in row_edit_handlers))
        blocks.append(_BlockInfo("row-edit", "Receive row edits", "RowData", names, hint))
        hint += 1

    if pagination_handlers and not save_handlers:
        names = list(dict.fromkeys(h.handler_name for h in handlers))
        blocks.append(_BlockInfo("pagination", "Receive page navigation", "PageNavigation", names, hint))
        hint += 1

    if save_handlers:
        names = list(dict.fromkeys(h.handler_name for h in handlers))
        blocks.append(_BlockInfo("save-command", "Receive save command", "SaveCommand", names, hint))
        hint += 1

    if not blocks:
        names = list(dict.fromkeys(h.handler_name for h in handlers))
        blocks.append(_BlockInfo("generic", "Receive user interaction", "User", names, hint))

    return blocks


def _classify_html_blocks(html_source: str) -> list[_BlockInfo]:
    """Parse HTML template and return classified interaction blocks in DOM order."""
    builder = _HtmlTreeBuilder()
    builder.feed(html_source)

    template_node: _HtmlNode | None = None
    for child in builder.root.children:
        if child.tag == "template":
            template_node = child
            break

    if template_node is None:
        return []

    blocks: list[_BlockInfo] = []
    order_hint = 1
    for child in template_node.children:
        child_blocks = _classify_node(child, order_hint)
        blocks.extend(child_blocks)
        order_hint += len(child_blocks) + 1

    return blocks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_apex_imports(js_source: str) -> list[tuple[str, str]]:
    """Return unique (class_name, method_name) imports from @salesforce/apex."""
    seen: set[tuple[str, str]] = set()
    imports: list[tuple[str, str]] = []
    for match in _APEX_IMPORT_RE.finditer(js_source):
        key = (match.group("class_name"), match.group("method_name"))
        if key in seen:
            continue
        seen.add(key)
        imports.append(key)
    return imports


def detect_apex_import_vars(js_source: str) -> set[str]:
    """Return the local variable names used for all @salesforce/apex imports."""
    return {m.group("var") for m in _APEX_IMPORT_VAR_RE.finditer(js_source)}


def _detect_apex_import_var_map(js_source: str) -> dict[str, str]:
    """Return {local_var_name: class_name} for all @salesforce/apex imports."""
    return {
        m.group("var"): m.group("class")
        for m in _APEX_IMPORT_VAR_CLASS_RE.finditer(js_source)
    }


def _extract_schema_object_map(js_source: str) -> dict[str, str]:
    return {m.group("var"): m.group("object") for m in _SCHEMA_IMPORT_RE.finditer(js_source)}


def _resolve_wire_reads(js_source: str, apex_import_names: set[str]) -> list[tuple[str, str]]:
    """Return (name, data_group_ref) per LWC-native @wire call, skipping Apex and ignored wires."""
    schema_map = _extract_schema_object_map(js_source)
    results: list[tuple[str, str]] = []
    for m in _WIRE_CALL_RE.finditer(js_source):
        adapter = m.group("adapter")
        if adapter in apex_import_names or adapter in _IGNORED_LWC_ADAPTERS:
            continue
        if adapter == "getRecord":
            args_text = m.group("args") or ""
            fields_match = _WIRE_FIELDS_RE.search(args_text)
            if fields_match:
                field_vars = [v.strip() for v in fields_match.group("fields").split(",") if v.strip()]
                objects = []
                for v in field_vars:
                    if v in schema_map:
                        obj = schema_map[v]
                        if obj not in _IGNORED_LWC_OBJECTS and obj not in objects:
                            objects.append(obj)
                for obj in objects:
                    results.append((f"Read {obj} record", obj))
                if not objects and not any(schema_map.get(v) in _IGNORED_LWC_OBJECTS for v in field_vars):
                    results.append(("Read record via getRecord", "Unknown"))
            else:
                results.append(("Read record via getRecord", "Unknown"))
        else:
            results.append((f"Read {adapter}", adapter))
    return results


def _extract_method_body(source: str, open_brace_pos: int) -> str:
    """Extract the body of a JS method starting from its opening brace."""
    depth = 0
    body_start: int | None = None
    for i in range(open_brace_pos, len(source)):
        ch = source[i]
        if ch == "{":
            depth += 1
            if depth == 1:
                body_start = i + 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and body_start is not None:
                return source[body_start:i]
    return source[body_start:] if body_start is not None else ""


def extract_handler_apex_calls(
    js_source: str,
    apex_import_vars: dict[str, str],
) -> dict[str, list[str]]:
    """Map each JS handler method name to the Apex class names it calls.

    Uses brace-depth counting to extract method bodies, then checks which
    Apex import variable names are called within each body.
    Returns {handler_method_name: [apex_class_name, ...]}.
    """
    result: dict[str, list[str]] = {}
    for m in _METHOD_DEF_RE.finditer(js_source):
        method_name = m.group(1)
        if method_name in _JS_KEYWORDS:
            continue
        brace_search_start = m.start() + len(m.group(0)) - 1
        body = _extract_method_body(js_source, brace_search_start)
        called_classes: list[str] = []
        for var_name, class_name in apex_import_vars.items():
            if re.search(r"\b" + re.escape(var_name) + r"\s*\(", body):
                if class_name not in called_classes:
                    called_classes.append(class_name)
        result[method_name] = called_classes
    return result


def parse_lwc_native_movements(
    js_source: str,
    html_source: str,
    apex_import_names: set[str] | None = None,
) -> list[LwcRawMovement]:
    """Extract native LWC E/R/W/X movement candidates from JS/HTML."""
    movements: list[LwcRawMovement] = []
    known_apex = apex_import_names or set()

    blocks = _classify_html_blocks(html_source)
    for block in blocks:
        movements.append(LwcRawMovement(
            movement_type="E",
            data_group_ref=block.data_group,
            name=block.e_name,
            order_hint=block.order_hint,
            tier=2,
            tier_label="Interactions",
            block_label=block.block_label,
            handler_names=list(block.handler_names),
        ))

    wire_order_hint = (max(b.order_hint for b in blocks) + 1) if blocks else 1
    for name, data_group_ref in _resolve_wire_reads(js_source, known_apex):
        movements.append(LwcRawMovement(
            movement_type="R",
            data_group_ref=data_group_ref,
            name=name,
            order_hint=wire_order_hint,
        ))
        wire_order_hint += 1

    if _LDS_READ_RE.search(js_source):
        movements.append(LwcRawMovement(
            movement_type="R",
            data_group_ref="Unknown",
            name="Read data via LWC data services",
            order_hint=wire_order_hint,
        ))
        wire_order_hint += 1

    if _LDS_WRITE_RE.search(js_source):
        movements.append(LwcRawMovement(
            movement_type="W",
            data_group_ref="Unknown",
            name="Write data via LWC data services",
            order_hint=wire_order_hint,
        ))
        wire_order_hint += 1

    if _TEMPLATE_BINDING_RE.search(html_source):
        movements.append(LwcRawMovement(
            movement_type="X",
            data_group_ref="User",
            name="Display LWC output to user",
            order_hint=wire_order_hint,
        ))

    return movements


def infer_bundle_name(bundle_dir: Path) -> str:
    return bundle_dir.name
