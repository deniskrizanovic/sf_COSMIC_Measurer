"""Integration tests for constant traversal in measure_apex.py."""

import json
from pathlib import Path
from measure_apex import measure_file

CONSTANTS_SRC = """
public class MyConstants {
    public static final String LOCATION_RT = 'Location';
    public static final String COMPONENT_RT = 'Component';
}
"""

CALLER_SRC = """
public class MyCaller {
    public void run() {
        Id locId;
        List<Asset> assets = [SELECT Id FROM Asset WHERE RecordTypeId = :MyConstants.LOCATION_RT];
    }
}
"""

def test_measure_file_resolves_external_constants(tmp_path):
    (tmp_path / "MyConstants.cls").write_text(CONSTANTS_SRC, encoding="utf-8")
    (tmp_path / "MyCaller.cls").write_text(CALLER_SRC, encoding="utf-8")
    
    out = measure_file(tmp_path / "MyCaller.cls", search_paths=[tmp_path])
    
    # Check that it resolved to Asset::Location instead of Asset::unknown RT
    movements = out["dataMovements"]
    read_asset = next(m for m in movements if m["movementType"] == "R" and "Asset" in m["dataGroupRef"])
    assert read_asset["dataGroupRef"] == "Asset::Location"

def test_measure_file_reports_missing_constant_provider(tmp_path):
    # Don't provide MyConstants.cls
    (tmp_path / "MyCaller.cls").write_text(CALLER_SRC, encoding="utf-8")
    
    out = measure_file(tmp_path / "MyCaller.cls", search_paths=[tmp_path])
    
    assert "MyConstants" in (out.get("calledClassesNotFound") or [])
    movements = out["dataMovements"]
    read_asset = next(m for m in movements if m["movementType"] == "R" and "Asset" in m["dataGroupRef"])
    assert read_asset["dataGroupRef"] == "Asset::unknown RT"
