"""
XML parser for Salesforce Flow .flow-meta.xml files.
Extracts COSMIC data movements: Entry (E), Read (R), Write (W), Exit (X).
"""

import sys
import xml.etree.ElementTree as ET
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent
_COSMIC_MEASURER_DIR = _SCRIPTS_DIR.parent.parent
if str(_COSMIC_MEASURER_DIR) not in sys.path:
    sys.path.insert(0, str(_COSMIC_MEASURER_DIR))

from shared.models import RawMovement  # noqa: E402

NS = {"sf": "http://soap.sforce.com/2006/04/metadata"}

PRIMITIVE_DATA_TYPES = frozenset({
    "String", "Number", "Currency", "Boolean", "Date", "DateTime",
})
MERGE_FIELD_PATTERN = re.compile(r"\{!([^}]+)\}")


@dataclass
class VariableInfo:
    name: str
    data_type: str
    object_type: Optional[str]
    is_input: bool
    is_output: bool
    is_collection: bool


@dataclass
class FlowMetadata:
    name: str
    label: str
    process_type: str
    api_version: str
    status: str
    trigger_type: Optional[str]
    trigger_object: Optional[str]


@dataclass
class InvocableApexCall:
    element_name: str
    label: str
    action_name: str


def _find_text(element: ET.Element, tag: str) -> Optional[str]:
    child = element.find(f"sf:{tag}", NS)
    if child is not None and child.text:
        return child.text.strip()
    return None


def parse_xml(source: str) -> ET.Element:
    """Parse XML string and return root element. Raises ValueError on bad XML."""
    try:
        return ET.fromstring(source)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML: {e}") from e


def extract_flow_metadata(root: ET.Element, filename: str = "") -> FlowMetadata:
    label = _find_text(root, "label") or Path(filename).stem if filename else "Unknown"
    if not label or label == "Unknown":
        label = _find_text(root, "label") or "Unknown"
    process_type = _find_text(root, "processType") or "Unknown"
    api_version = _find_text(root, "apiVersion") or "Unknown"
    status = _find_text(root, "status") or "Unknown"

    trigger_type = None
    trigger_object = None
    start_el = root.find("sf:start", NS)
    if start_el is not None:
        trigger_type = _find_text(start_el, "triggerType")
        trigger_object = _find_text(start_el, "object")

    raw_stem = Path(filename).stem if filename else label
    name = raw_stem.removesuffix(".flow-meta") if raw_stem.endswith(".flow-meta") else raw_stem
    return FlowMetadata(
        name=name,
        label=label,
        process_type=process_type,
        api_version=api_version,
        status=status,
        trigger_type=trigger_type,
        trigger_object=trigger_object,
    )


def extract_variables(root: ET.Element) -> dict[str, VariableInfo]:
    """Extract all <variables> into a name -> VariableInfo map."""
    result: dict[str, VariableInfo] = {}
    for var_el in root.findall("sf:variables", NS):
        vname = _find_text(var_el, "name")
        if not vname:
            continue
        data_type = _find_text(var_el, "dataType") or "String"
        object_type = _find_text(var_el, "objectType")
        is_input = (_find_text(var_el, "isInput") or "").lower() == "true"
        is_output = (_find_text(var_el, "isOutput") or "").lower() == "true"
        is_collection = (_find_text(var_el, "isCollection") or "").lower() == "true"
        result[vname] = VariableInfo(
            name=vname,
            data_type=data_type,
            object_type=object_type,
            is_input=is_input,
            is_output=is_output,
            is_collection=is_collection,
        )
    return result


def find_record_lookups(root: ET.Element) -> list[RawMovement]:
    """Extract Read movements from <recordLookups> elements."""
    movements: list[RawMovement] = []
    for i, rl in enumerate(root.findall("sf:recordLookups", NS)):
        element_name = _find_text(rl, "name") or f"recordLookup_{i}"
        label = _find_text(rl, "label") or element_name
        obj = _find_text(rl, "object")
        if not obj:
            continue
        movements.append(RawMovement(
            movement_type="R",
            data_group_ref=obj,
            name=f"Read {obj} ({label})",
            order_hint=i + 1,
        ))
    return movements


def find_record_mutations(
    root: ET.Element, variables: dict[str, VariableInfo]
) -> list[RawMovement]:
    """Extract Write movements from recordCreates/Updates/Deletes."""
    movements: list[RawMovement] = []
    mutation_tags = [
        ("recordCreates", "Create"),
        ("recordUpdates", "Update"),
        ("recordDeletes", "Delete"),
    ]
    hint = 0
    for tag, verb in mutation_tags:
        for el in root.findall(f"sf:{tag}", NS):
            element_name = _find_text(el, "name") or tag
            label = _find_text(el, "label") or element_name
            obj = _find_text(el, "object")
            if not obj:
                input_ref = _find_text(el, "inputReference")
                if input_ref and input_ref in variables:
                    obj = variables[input_ref].object_type
            if not obj:
                obj = "Unknown"
            hint += 1
            movements.append(RawMovement(
                movement_type="W",
                data_group_ref=obj,
                name=f"{verb} {obj} ({label})",
                order_hint=hint,
            ))
    return movements


def _infer_record_id_object(
    root: ET.Element, variables: dict[str, VariableInfo]
) -> Optional[str]:
    """Infer object for a 'recordId' input by checking the first recordLookup that filters by Id."""
    for rl in root.findall("sf:recordLookups", NS):
        for filt in rl.findall("sf:filters", NS):
            field = _find_text(filt, "field")
            value_el = filt.find("sf:value", NS)
            if value_el is not None:
                ref = _find_text(value_el, "elementReference")
                if field == "Id" and ref == "recordId":
                    obj = _find_text(rl, "object")
                    if obj:
                        return obj
    return None


def find_entries(
    root: ET.Element,
    metadata: FlowMetadata,
    variables: dict[str, VariableInfo],
) -> list[RawMovement]:
    """Extract Entry movements from input variables and trigger context."""
    movements: list[RawMovement] = []
    hint = 0

    if metadata.trigger_object and metadata.trigger_type:
        hint += 1
        movements.append(RawMovement(
            movement_type="E",
            data_group_ref=metadata.trigger_object,
            name=f"Trigger record ({metadata.trigger_object})",
            order_hint=hint,
        ))

    for var in variables.values():
        if not var.is_input:
            continue
        if var.data_type == "SObject" and var.object_type:
            hint += 1
            movements.append(RawMovement(
                movement_type="E",
                data_group_ref=var.object_type,
                name=f"Receive {var.name} ({var.object_type})",
                order_hint=hint,
            ))
        elif var.name == "recordId":
            obj = _infer_record_id_object(root, variables)
            if obj:
                hint += 1
                movements.append(RawMovement(
                    movement_type="E",
                    data_group_ref=obj,
                    name=f"Receive recordId ({obj})",
                    order_hint=hint,
                ))

    return movements


def find_exits(variables: dict[str, VariableInfo]) -> list[RawMovement]:
    """Extract Exit movements from output variables with SObject type."""
    movements: list[RawMovement] = []
    hint = 0
    for var in variables.values():
        if not var.is_output:
            continue
        if var.data_type == "SObject" and var.object_type:
            hint += 1
            movements.append(RawMovement(
                movement_type="X",
                data_group_ref=var.object_type,
                name=f"Output {var.name} ({var.object_type})",
                order_hint=hint,
            ))
    return movements


def _lookup_object_map(root: ET.Element) -> dict[str, str]:
    """Build recordLookup name -> object map."""
    result: dict[str, str] = {}
    for rl in root.findall("sf:recordLookups", NS):
        name = _find_text(rl, "name")
        obj = _find_text(rl, "object")
        if name and obj:
            result[name] = obj
    return result


def _resolve_data_group_ref(
    ref: str,
    variables: dict[str, VariableInfo],
    lookup_objects: dict[str, str],
    component_bindings: dict[str, str],
) -> Optional[str]:
    """Resolve elementReference-like value to an SObject data group."""
    token = ref.strip()
    if not token:
        return None
    base = token.split(".", 1)[0]

    if base in variables and variables[base].object_type:
        return variables[base].object_type
    if base in lookup_objects:
        return lookup_objects[base]
    if base in component_bindings:
        return component_bindings[base]
    if base.endswith("__c"):
        return base
    return None


def _screen_component_table_bindings(
    screen_el: ET.Element,
    variables: dict[str, VariableInfo],
    lookup_objects: dict[str, str],
) -> dict[str, str]:
    """Map screen component field name -> data group for table-like bindings."""
    bindings: dict[str, str] = {}
    for field in screen_el.findall(".//sf:fields", NS):
        if _find_text(field, "fieldType") != "ComponentInstance":
            continue
        field_name = _find_text(field, "name")
        if not field_name:
            continue

        bound_group: Optional[str] = None
        for param in field.findall("sf:inputParameters", NS):
            pname = _find_text(param, "name")
            if pname != "tableData":
                continue
            value_el = param.find("sf:value", NS)
            if value_el is None:
                continue
            ref = _find_text(value_el, "elementReference")
            if not ref:
                continue
            bound_group = _resolve_data_group_ref(
                ref, variables, lookup_objects, component_bindings={}
            )
            if bound_group:
                break
        if bound_group:
            bindings[field_name] = bound_group

    return bindings


def find_screen_movements(
    root: ET.Element, variables: dict[str, VariableInfo]
) -> tuple[list[RawMovement], list[RawMovement]]:
    """Extract screen-based Entry and Exit movements per distinct data group."""
    entries: list[RawMovement] = []
    exits: list[RawMovement] = []

    entry_hint = 0
    exit_hint = 0
    lookup_objects = _lookup_object_map(root)

    for screen_idx, screen_el in enumerate(root.findall("sf:screens", NS), start=1):
        screen_name = _find_text(screen_el, "name") or f"Screen {screen_idx}"
        component_bindings = _screen_component_table_bindings(
            screen_el, variables, lookup_objects
        )

        entry_data_groups: set[str] = set()
        exit_data_groups: set[str] = set()

        for field in screen_el.findall(".//sf:fields", NS):
            field_type = (_find_text(field, "fieldType") or "").strip()
            refs = [
                ref.text.strip()
                for ref in field.findall(".//sf:elementReference", NS)
                if ref.text and ref.text.strip()
            ]
            field_text = _find_text(field, "fieldText") or ""
            refs.extend(match.strip() for match in MERGE_FIELD_PATTERN.findall(field_text) if match.strip())
            resolved_data_groups = {
                resolved
                for ref in refs
                if (resolved := _resolve_data_group_ref(
                    ref, variables, lookup_objects, component_bindings
                ))
            }
            if not resolved_data_groups:
                continue

            is_entry_field = field_type == "InputField"
            if field_type == "ComponentInstance":
                has_output_storage = (
                    (_find_text(field, "storeOutputAutomatically") or "").lower() == "true"
                )
                is_entry_field = has_output_storage

            is_exit_field = field_type in {"DisplayText", "ComponentInstance"}

            if is_entry_field:
                entry_data_groups.update(resolved_data_groups)
            if is_exit_field:
                exit_data_groups.update(resolved_data_groups)

        for dg in sorted(entry_data_groups):
            entry_hint += 1
            entries.append(RawMovement(
                movement_type="E",
                data_group_ref=dg,
                name=f"Screen input ({screen_name}) ({dg})",
                order_hint=entry_hint,
            ))
        for dg in sorted(exit_data_groups):
            exit_hint += 1
            exits.append(RawMovement(
                movement_type="X",
                data_group_ref=dg,
                name=f"Screen display ({screen_name}) ({dg})",
                order_hint=exit_hint,
            ))

    return entries, exits


def find_invocable_apex_calls(root: ET.Element) -> list[InvocableApexCall]:
    """Extract Apex invocable action calls from <actionCalls>."""
    calls: list[InvocableApexCall] = []
    for idx, action_call in enumerate(root.findall("sf:actionCalls", NS), start=1):
        action_type = (_find_text(action_call, "actionType") or "").strip().lower()
        if action_type != "apex":
            continue
        action_name = _find_text(action_call, "actionName")
        if not action_name:
            continue
        element_name = _find_text(action_call, "name") or f"actionCall_{idx}"
        label = _find_text(action_call, "label") or element_name
        calls.append(
            InvocableApexCall(
                element_name=element_name,
                label=label,
                action_name=action_name,
            )
        )
    return calls


def parse_flow(
    source: str, filename: str = ""
) -> tuple[FlowMetadata, list[RawMovement]]:
    """Parse a flow XML string and return metadata + all raw movements."""
    root = parse_xml(source)
    metadata = extract_flow_metadata(root, filename)
    variables = extract_variables(root)

    entries = find_entries(root, metadata, variables)
    screen_entries, screen_exits = find_screen_movements(root, variables)
    reads = find_record_lookups(root)
    writes = find_record_mutations(root, variables)
    exits = find_exits(variables)

    return metadata, entries + screen_entries + reads + writes + exits + screen_exits


def parse_flow_with_invocables(
    source: str, filename: str = ""
) -> tuple[FlowMetadata, list[RawMovement], list[InvocableApexCall]]:
    """Parse a flow XML string and include invocable Apex action call metadata."""
    root = parse_xml(source)
    metadata = extract_flow_metadata(root, filename)
    variables = extract_variables(root)

    entries = find_entries(root, metadata, variables)
    screen_entries, screen_exits = find_screen_movements(root, variables)
    reads = find_record_lookups(root)
    writes = find_record_mutations(root, variables)
    exits = find_exits(variables)
    invocable_apex_calls = find_invocable_apex_calls(root)

    movements = entries + screen_entries + reads + writes + exits + screen_exits
    return metadata, movements, invocable_apex_calls
