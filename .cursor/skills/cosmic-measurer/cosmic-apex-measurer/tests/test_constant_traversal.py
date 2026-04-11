"""Unit tests for cross-class constant resolution in parser.py and measure_apex.py."""

import pytest
from parser import (
    find_external_constant_calls,
    _parse_record_type_string_constants,
    _infer_record_type_from_bind,
    find_reads
)

def test_find_external_constant_calls_detects_qualified_names():
    src = """
    public class Caller {
        void run() {
            String rt = GlobalConstants.LOCATION_RT;
            String other = OtherClass.SOME_CONSTANT;
        }
    }
    """
    calls = find_external_constant_calls(src)
    assert calls == {"GlobalConstants", "OtherClass"}

def test_parse_record_type_string_constants_supports_modifiers():
    src = """
    public class C {
        public static final String PUB_RT = 'Pub';
        global static final String GLB_RT = 'Glb';
        protected static final String PRT_RT = 'Prt';
        private static final String PRV_RT = 'Prv';
    }
    """
    constants = _parse_record_type_string_constants(src)
    assert constants["PUB_RT"] == "Pub"
    assert constants["GLB_RT"] == "Glb"
    assert constants["PRT_RT"] == "Prt"
    assert constants["PRV_RT"] == "Prv"

def test_infer_record_type_from_bind_with_external_constants():
    src = "public class X { }"
    external = {
        "GlobalConstants.LOCATION_RT": "Location",
        "Other.THING_RT": "Thing"
    }
    
    # Qualified bind
    assert _infer_record_type_from_bind("GlobalConstants.LOCATION_RT", src, external) == "Location"
    # Unqualified bind matching external stem
    assert _infer_record_type_from_bind("locationRecordTypeId", src, external) == "Location"
    # Unqualified bind matching other external stem
    assert _infer_record_type_from_bind("thingId", src, external) == "Thing"

def test_find_reads_with_external_constants():
    src = """
    public class C {
        void run() {
            List<Asset> a = [SELECT Id FROM Asset WHERE RecordTypeId = :GlobalConstants.LOCATION_RT];
        }
    }
    """
    external = {"GlobalConstants.LOCATION_RT": "Location"}
    reads = find_reads(src, external_constants=external)
    assert len(reads) == 1
    assert reads[0].data_group_ref == "Asset::Location"

def test_infer_record_type_from_bind_stem_logic():
    src = "public class X { }"
    # Test stem with and without underscores and case sensitivity
    external = {"My_Class.SOME_LONG_NAME_RT": "Val"}
    assert _infer_record_type_from_bind("someLongNameId", src, external) == "Val"
    assert _infer_record_type_from_bind("SOMELONGNAME", src, external) == "Val"
