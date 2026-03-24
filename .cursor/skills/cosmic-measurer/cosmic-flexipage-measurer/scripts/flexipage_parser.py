"""
XML parser for Salesforce FlexiPage .flexipage-meta.xml files.
Extracts COSMIC data movements from page display metadata (R/X).
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from shared.models import RawMovement

NS = {"sf": "http://soap.sforce.com/2006/04/metadata"}


@dataclass
class FlexiPageMetadata:
    name: str
    master_label: str
    sobject_type: str
    page_type: str


@dataclass
class DynamicRelatedList:
    identifier: str
    related_list_api_name: Optional[str]
    parent_field_api_name: Optional[str]
    related_list_label: Optional[str]


@dataclass
class TabComponentBinding:
    tab_identifier: str
    tab_title: Optional[str]
    body_facet_name: str
    target_component_name: Optional[str]
    target_component_kind: str
    target_component_properties: dict[str, str]


@dataclass
class TabTargetComponent:
    component_name: Optional[str]
    properties: dict[str, str]


def _find_text(element: ET.Element, tag: str) -> Optional[str]:
    child = element.find(f"sf:{tag}", NS)
    if child is not None and child.text:
        return child.text.strip()
    return None


def _normalize_related_list_to_data_group(related_list_api_name: str) -> str:
    ref = related_list_api_name.strip()
    if ref.endswith("__r"):
        return ref[:-3] + "__c"
    return ref


def _extract_action_values(component: ET.Element) -> list[str]:
    actions: list[str] = []
    for prop in component.findall("sf:componentInstanceProperties", NS):
        if _find_text(prop, "name") != "actionNames":
            continue
        for value in prop.findall(".//sf:valueListItems/sf:value", NS):
            if value.text and value.text.strip():
                actions.append(value.text.strip())
    return actions


def _extract_component_property(component: ET.Element, prop_name: str) -> Optional[str]:
    for prop in component.findall("sf:componentInstanceProperties", NS):
        if _find_text(prop, "name") != prop_name:
            continue
        value = _find_text(prop, "value")
        if value:
            return value
    return None


def parse_xml(source: str) -> ET.Element:
    """Parse XML string and return root element. Raises ValueError on bad XML."""
    try:
        return ET.fromstring(source)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid XML: {exc}") from exc


def extract_flexipage_metadata(root: ET.Element, filename: str = "") -> FlexiPageMetadata:
    master_label = _find_text(root, "masterLabel") or "Unknown"
    sobject_type = _find_text(root, "sobjectType") or "Unknown"
    page_type = _find_text(root, "type") or "Unknown"
    stem = Path(filename).stem if filename else master_label
    name = stem.removesuffix(".flexipage-meta") if stem.endswith(".flexipage-meta") else stem
    return FlexiPageMetadata(
        name=name,
        master_label=master_label,
        sobject_type=sobject_type,
        page_type=page_type,
    )


def extract_record_field_bindings(root: ET.Element) -> list[str]:
    """Extract Record.<Field> bindings from fieldInstance/fieldItem tags."""
    fields: list[str] = []
    for field_item in root.findall(".//sf:fieldInstance/sf:fieldItem", NS):
        if field_item.text and field_item.text.strip().startswith("Record."):
            fields.append(field_item.text.strip())
    return fields


def extract_dynamic_related_lists(root: ET.Element) -> list[DynamicRelatedList]:
    """Extract related list component definitions used by record pages."""
    related_lists: list[DynamicRelatedList] = []
    for component in root.findall(".//sf:componentInstance", NS):
        component_name = _find_text(component, "componentName")
        if component_name not in ("lst:dynamicRelatedList", "force:relatedListSingleContainer"):
            continue
        related_lists.append(
            DynamicRelatedList(
                identifier=_find_text(component, "identifier") or "unknownRelatedList",
                related_list_api_name=_extract_component_property(component, "relatedListApiName"),
                parent_field_api_name=_extract_component_property(component, "parentFieldApiName"),
                related_list_label=_extract_component_property(component, "relatedListLabel"),
            )
        )
    return related_lists


def extract_highlights_actions(root: ET.Element) -> list[str]:
    """Extract action names from force:highlightsPanel."""
    actions: list[str] = []
    for component in root.findall(".//sf:componentInstance", NS):
        component_name = _find_text(component, "componentName")
        if component_name == "force:highlightsPanel":
            actions.extend(_extract_action_values(component))
    return actions


def has_highlights_panel(root: ET.Element) -> bool:
    """Return True when force:highlightsPanel is configured on the page."""
    for component in root.findall(".//sf:componentInstance", NS):
        if _find_text(component, "componentName") == "force:highlightsPanel":
            return True
    return False


def extract_tab_labels(root: ET.Element) -> list[str]:
    """Extract tab labels from flexipage:tab component instances."""
    labels: list[str] = []
    for component in root.findall(".//sf:componentInstance", NS):
        component_name = _find_text(component, "componentName")
        if component_name != "flexipage:tab":
            continue
        label = _extract_component_property(component, "title")
        if label:
            labels.append(label)
    return labels


def _classify_component_kind(component_name: Optional[str]) -> str:
    if not component_name:
        return "unknown"
    return "aura" if ":" in component_name else "lwc"


def _extract_component_properties(component: ET.Element) -> dict[str, str]:
    properties: dict[str, str] = {}
    for prop in component.findall("sf:componentInstanceProperties", NS):
        prop_name = _find_text(prop, "name")
        prop_value = _find_text(prop, "value")
        if prop_name and prop_value:
            properties[prop_name] = prop_value
    return properties


def _build_facet_component_index(root: ET.Element) -> dict[str, list[TabTargetComponent]]:
    facet_targets: dict[str, list[TabTargetComponent]] = {}
    for region in root.findall("sf:flexiPageRegions", NS):
        region_name = _find_text(region, "name")
        if not region_name:
            continue
        components: list[TabTargetComponent] = []
        for item in region.findall("sf:itemInstances", NS):
            component = item.find("sf:componentInstance", NS)
            if component is None:
                continue
            components.append(
                TabTargetComponent(
                    component_name=_find_text(component, "componentName"),
                    properties=_extract_component_properties(component),
                )
            )
        facet_targets[region_name] = components
    return facet_targets


def extract_tab_component_bindings(root: ET.Element) -> list[TabComponentBinding]:
    """Resolve each tab body facet to all target components and classify kind."""
    bindings: list[TabComponentBinding] = []
    facet_component_index = _build_facet_component_index(root)
    for component in root.findall(".//sf:componentInstance", NS):
        component_name = _find_text(component, "componentName")
        if component_name != "flexipage:tab":
            continue
        body_facet_name = _extract_component_property(component, "body")
        if not body_facet_name:
            continue
        target_components = facet_component_index.get(body_facet_name) or []
        if not target_components:
            bindings.append(
                TabComponentBinding(
                    tab_identifier=_find_text(component, "identifier") or "unknownTab",
                    tab_title=_extract_component_property(component, "title"),
                    body_facet_name=body_facet_name,
                    target_component_name=None,
                    target_component_kind="unknown",
                    target_component_properties={},
                )
            )
            continue
        for target_component in target_components:
            target_component_name = target_component.component_name
            bindings.append(
                TabComponentBinding(
                    tab_identifier=_find_text(component, "identifier") or "unknownTab",
                    tab_title=_extract_component_property(component, "title"),
                    body_facet_name=body_facet_name,
                    target_component_name=target_component_name,
                    target_component_kind=_classify_component_kind(target_component_name),
                    target_component_properties=target_component.properties,
                )
            )
    return bindings


def _tab_suffix(binding: TabComponentBinding) -> str:
    tab_name = binding.tab_title or binding.tab_identifier
    return f" | tab:{tab_name}"


def _infer_related_record_data_group(
    properties: dict[str, str], sobject_type: str
) -> tuple[str, bool]:
    lookup_field = properties.get("lookupFieldName", "").strip()
    if "." in lookup_field:
        parent_object, field_name = lookup_field.split(".", 1)
        field_name = field_name.strip()
        if field_name == "Id":
            return parent_object, False
        if field_name.endswith("Id") and len(field_name) > 2:
            return field_name[:-2], False
        if field_name.endswith("__c"):
            return field_name, False
        return parent_object, False
    if lookup_field and lookup_field != "Id":
        return lookup_field, False
    action_name = properties.get("updateQuickActionName", "").strip()
    if "." in action_name:
        return action_name.split(".", 1)[0], False
    return sobject_type, True


def extract_tab_bound_component_movements(
    root: ET.Element, sobject_type: str
) -> tuple[list[RawMovement], list[str]]:
    """Build tab-derived movements for non-LWC tab targets and warnings."""
    movements: list[RawMovement] = []
    warnings: list[str] = []
    movement_order_hint = 1000

    for binding in extract_tab_component_bindings(root):
        if binding.target_component_kind == "lwc":
            continue
        component_name = binding.target_component_name or ""
        properties = binding.target_component_properties
        suffix = _tab_suffix(binding)

        if component_name in ("force:relatedListSingleContainer", "lst:dynamicRelatedList"):
            related_list_api_name = properties.get("relatedListApiName", "").strip()
            if not related_list_api_name:
                warnings.append(
                    f"Tab component {binding.tab_title or binding.tab_identifier} ({component_name}) is missing relatedListApiName"
                )
                continue
            data_group = _normalize_related_list_to_data_group(related_list_api_name)
            movements.append(
                RawMovement(
                    movement_type="R",
                    data_group_ref=data_group,
                    name=f"Read related list {related_list_api_name}{suffix}",
                    order_hint=movement_order_hint,
                )
            )
            movements.append(
                RawMovement(
                    movement_type="X",
                    data_group_ref=data_group,
                    name=f"Display related list {related_list_api_name}{suffix}",
                    order_hint=movement_order_hint + 1,
                )
            )
            movement_order_hint += 2
            continue

        if component_name == "flowruntime:interview":
            flow_name = properties.get("flowName", "").strip() or "unknownFlow"
            movements.append(
                RawMovement(
                    movement_type="X",
                    data_group_ref=f"Flow:{flow_name}",
                    name=f"Display flow interview {flow_name}{suffix}",
                    order_hint=movement_order_hint,
                )
            )
            movement_order_hint += 1
            warnings.append(
                f"Tab component {binding.tab_title or binding.tab_identifier} (flowruntime:interview) inferred as X only; inspect flow for additional E/W"
            )
            continue

        if component_name == "console:relatedRecord":
            data_group_ref, used_fallback = _infer_related_record_data_group(properties, sobject_type)
            record_title = properties.get("titleFieldName", "").strip() or "related record details"
            movements.append(
                RawMovement(
                    movement_type="R",
                    data_group_ref=data_group_ref,
                    name=f"Read related record {record_title}{suffix}",
                    order_hint=movement_order_hint,
                )
            )
            movements.append(
                RawMovement(
                    movement_type="X",
                    data_group_ref=data_group_ref,
                    name=f"Display related record {record_title}{suffix}",
                    order_hint=movement_order_hint + 1,
                )
            )
            movement_order_hint += 2
            if used_fallback:
                warnings.append(
                    f"Tab component {binding.tab_title or binding.tab_identifier} (console:relatedRecord) fell back to dataGroupRef {sobject_type}"
                )
            continue

        warnings.append(
            f"Unsupported tab component {binding.tab_title or binding.tab_identifier}: {component_name or 'unknown component'}"
        )

    return movements, warnings


def extract_sidebar_component_movements(
    root: ET.Element, sobject_type: str
) -> tuple[list[RawMovement], list[str]]:
    """Build movements for supported sidebar component instances."""
    movements: list[RawMovement] = []
    warnings: list[str] = []
    movement_order_hint = 2000

    for region in root.findall("sf:flexiPageRegions", NS):
        if (_find_text(region, "name") or "").strip() != "sidebar":
            continue
        for item in region.findall("sf:itemInstances", NS):
            component = item.find("sf:componentInstance", NS)
            if component is None:
                continue
            component_name = _find_text(component, "componentName") or ""
            if component_name != "console:relatedRecord":
                continue
            properties = _extract_component_properties(component)
            data_group_ref, used_fallback = _infer_related_record_data_group(properties, sobject_type)
            record_title = properties.get("titleFieldName", "").strip() or "related record details"
            movements.append(
                RawMovement(
                    movement_type="R",
                    data_group_ref=data_group_ref,
                    name=f"Read related record {record_title}",
                    order_hint=movement_order_hint,
                )
            )
            movements.append(
                RawMovement(
                    movement_type="X",
                    data_group_ref=data_group_ref,
                    name=f"Display related record {record_title}",
                    order_hint=movement_order_hint + 1,
                )
            )
            movement_order_hint += 2
            if used_fallback:
                warnings.append(
                    f"Sidebar component console:relatedRecord fell back to dataGroupRef {sobject_type}"
                )

    return movements, warnings


def find_reads_from_page(
    sobject_type: str,
    record_fields: list[str],
    related_lists: list[DynamicRelatedList],
    *,
    include_highlights_panel: bool = False,
) -> list[RawMovement]:
    reads: list[RawMovement] = []
    hint = 0
    seen_data_groups: set[str] = set()
    if record_fields:
        hint += 1
        seen_data_groups.add(sobject_type)
        reads.append(
            RawMovement(
                movement_type="R",
                data_group_ref=sobject_type,
                name=f"Read page record ({sobject_type})",
                order_hint=hint,
            )
        )
        if include_highlights_panel:
            hint += 1
            reads.append(
                RawMovement(
                    movement_type="R",
                    data_group_ref=sobject_type,
                    name=f"Read highlights panel fields ({sobject_type})",
                    order_hint=hint,
                )
            )
    for rl in related_lists:
        if not rl.related_list_api_name:
            continue
        data_group = _normalize_related_list_to_data_group(rl.related_list_api_name)
        if data_group in seen_data_groups:
            continue
        hint += 1
        seen_data_groups.add(data_group)
        reads.append(
            RawMovement(
                movement_type="R",
                data_group_ref=data_group,
                name=f"Read related list {rl.related_list_api_name}",
                order_hint=hint,
            )
        )
    return reads


def find_exits_from_page(
    sobject_type: str,
    record_fields: list[str],
    related_lists: list[DynamicRelatedList],
    *,
    include_highlights_panel: bool = False,
) -> list[RawMovement]:
    exits: list[RawMovement] = []
    hint = 0
    seen_data_groups: set[str] = set()
    if record_fields:
        hint += 1
        seen_data_groups.add(sobject_type)
        exits.append(
            RawMovement(
                movement_type="X",
                data_group_ref=sobject_type,
                name=f"Display page record ({sobject_type})",
                order_hint=hint,
            )
        )
        if include_highlights_panel:
            hint += 1
            exits.append(
                RawMovement(
                    movement_type="X",
                    data_group_ref=sobject_type,
                    name=f"Display highlights panel fields ({sobject_type})",
                    order_hint=hint,
                )
            )
    for rl in related_lists:
        if not rl.related_list_api_name:
            continue
        data_group = _normalize_related_list_to_data_group(rl.related_list_api_name)
        if data_group in seen_data_groups:
            continue
        hint += 1
        seen_data_groups.add(data_group)
        exits.append(
            RawMovement(
                movement_type="X",
                data_group_ref=data_group,
                name=f"Display related list {rl.related_list_api_name}",
                order_hint=hint,
            )
        )
    return exits


def build_synthetic_page_trigger_entry(sobject_type: str) -> RawMovement:
    """Synthetic COSMIC trigger entry for page-open functional process."""
    return RawMovement(
        movement_type="E",
        data_group_ref=sobject_type,
        name=f"Open record page ({sobject_type})",
        order_hint=0,
    )


def build_synthetic_action_entry(action_name: str, sobject_type: str) -> RawMovement:
    """Synthetic COSMIC trigger entry for an action-specific functional process."""
    return RawMovement(
        movement_type="E",
        data_group_ref=sobject_type,
        name=f"Trigger action {action_name}",
        order_hint=0,
    )


def build_primary_record_edit_entry(sobject_type: str) -> RawMovement:
    """Entry movement representing user edit intent on the primary record."""
    return RawMovement(
        movement_type="E",
        data_group_ref=sobject_type,
        name=f"Edit page record ({sobject_type})",
        order_hint=9999,
    )


def build_primary_record_write_entry(sobject_type: str) -> RawMovement:
    """Write movement for out-of-box Salesforce persistence of primary-record edits."""
    return RawMovement(
        movement_type="W",
        data_group_ref=sobject_type,
        name=f"Write page record ({sobject_type})",
        order_hint=10000,
    )


def parse_flexipage(
    source: str, filename: str = ""
) -> tuple[FlexiPageMetadata, list[RawMovement], list[str], list[str]]:
    """Parse a FlexiPage XML string and return metadata, movements, actions, and tab labels."""
    root = parse_xml(source)
    metadata = extract_flexipage_metadata(root, filename=filename)
    record_fields = extract_record_field_bindings(root)
    related_lists = extract_dynamic_related_lists(root)
    actions = extract_highlights_actions(root)
    has_highlights = has_highlights_panel(root)
    tab_labels = extract_tab_labels(root)

    # Record pages inherently read and display the primary record even when fieldItem
    # bindings are not explicitly present (e.g., force:detailPanel-driven layouts).
    has_primary_record_context = bool(record_fields) or metadata.page_type == "RecordPage"
    primary_record_binding = ["Record.Id"] if has_primary_record_context else []
    reads = find_reads_from_page(
        metadata.sobject_type,
        primary_record_binding,
        related_lists,
        include_highlights_panel=has_highlights,
    )
    exits = find_exits_from_page(
        metadata.sobject_type,
        primary_record_binding,
        related_lists,
        include_highlights_panel=has_highlights,
    )
    primary_record_edits = (
        [
            build_primary_record_edit_entry(metadata.sobject_type),
            build_primary_record_write_entry(metadata.sobject_type),
        ]
        if has_primary_record_context
        else []
    )
    return metadata, reads + primary_record_edits + exits, actions, tab_labels
