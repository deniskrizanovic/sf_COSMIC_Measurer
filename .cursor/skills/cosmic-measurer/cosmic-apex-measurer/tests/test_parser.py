"""Unit tests for parser.py with minimal Apex-shaped strings."""

from parser import (
    _collect_entry_point_params,
    _get_entry_point_method_names,
    _infer_object_from_param,
    extract_class_name,
    find_entries,
    find_exits,
    find_reads,
    find_writes,
    format_data_group_ref,
    get_entry_points,
    parse,
)


def test_format_data_group_ref_composite_and_unspec():
    assert format_data_group_ref("Asset", "Location") == "Asset::Location"
    assert format_data_group_ref("Asset", None, unspec=True) == "Asset::*"
    assert format_data_group_ref("Case", None) == "Case"


def test_find_reads_record_type_id_bind_maps_to_rt_constant():
    src = """
public class RT {
    private static final String LOCATION_RT = 'Location';
    void q() {
        Id locationRecordTypeId;
        List<Asset> rows = [
            SELECT Id FROM Asset WHERE RecordTypeId = :locationRecordTypeId
        ];
    }
}
"""
    reads = find_reads(src)
    assert any(r.data_group_ref == "Asset::Location" for r in reads)


def test_find_writes_skips_insert_keyword_inside_string_literal():
    src = """
public class W3 {
    void m() {
        logDebug('execute: ' + type + ' insert result: ok');
        List<Thing__c> records = new List<Thing__c>();
        update records;
    }
}
"""
    writes = find_writes(src)
    assert len(writes) == 1
    assert writes[0].data_group_ref == "Thing__c"


def test_find_reads_database_query_string():
    src = """
public class DbQ {
    void run() {
        Database.query('SELECT Id FROM Case WHERE x = 1');
    }
}
"""
    reads = find_reads(src)
    assert any(r.data_group_ref == "Case" for r in reads)


def test_find_writes_skips_dml_when_comment_before_statement_on_same_line():
    src = """
public class W {
    void m() {
        List<Thing__c> records = new List<Thing__c>();
        // foo   update records;
        update records;
    }
}
"""
    writes = find_writes(src)
    assert len(writes) == 1
    assert writes[0].data_group_ref == "Thing__c"


def test_find_writes_database_dml_from_var_decl():
    src = """
public class W2 {
    void m() {
        List<Z__c> rows = new List<Z__c>();
        Database.update(rows, false);
    }
}
"""
    writes = find_writes(src)
    assert any(w.data_group_ref == "Z__c" and "Update" in w.name for w in writes)


def test_infer_map_param_with_custom_object():
    src = "public class X { }"
    assert (
        _infer_object_from_param("m", "Map<Id, Custom__c>", src) == "Custom__c"
    )


def test_infer_map_unknown_returns_unknown():
    src = "public class X { }"
    assert _infer_object_from_param("m", "Map<Id, String>", src) == "Unknown"


def test_infer_set_inner_type():
    src = "public class X { }"
    assert _infer_object_from_param("s", "Set<Account>", src) == "Account"


def test_infer_list_id_survey_ids():
    src = "public class X { }"
    assert _infer_object_from_param("surveyIds", "List<Id>", src) == "Survey__c"


def test_infer_usage_bind_variable():
    src = """
public class X {
    void m(Id fpId) {
        cfp_FunctionalProcess__c = :fpId;
    }
}
"""
    assert _infer_object_from_param("fpId", "Id", src) == "cfp_FunctionalProcess__c"


def test_infer_single_id_suffix_custom():
    src = "public class X { }"
    assert _infer_object_from_param("customObjId", "Id", src) == "customObj__c"


def test_infer_list_inner_not_framework():
    src = "public class X { }"
    assert _infer_object_from_param("rows", "List<Invoice__c>", src) == "Invoice__c"


def test_get_entry_points_batch_constructor_and_factory():
    src = """
public class JobBatch implements Database.Batchable {
    public JobBatch(List<Id> surveyIds) { }
    public static JobBatch forSurveys() { return null; }
    public Database.QueryLocator start(Database.BatchableContext bc) { return null; }
    public void execute(Database.BatchableContext bc, List<SObject> scope) { }
    public void finish(Database.BatchableContext bc) { }
}
"""
    eps = get_entry_points(src)
    params = {e["param"] for e in eps}
    assert "surveyIds" in params


def test_get_entry_points_aura_enabled():
    src = """
public class AuraCls {
    @AuraEnabled
    public static void save(List<Id> surveyIds) { }
}
"""
    eps = get_entry_points(src)
    assert any(e["param"] == "surveyIds" for e in eps)


def test_get_entry_points_invocable():
    src = """
public class Inv {
    @InvocableMethod
    public static List<Account> run() { return null; }
}
"""
    eps = get_entry_points(src)
    assert len(eps) == 0


def test_get_entry_points_fallback_public_static():
    src = """
public class FB {
    public static void doWork(List<Id> surveyIds) { }
}
"""
    eps = get_entry_points(src)
    assert any(e["param"] == "surveyIds" for e in eps)


def test_collect_skips_batchable_context_and_sobject_list_and_string():
    src = """
public class Sk implements Database.Batchable {
    public Sk(String name, Integer n, Boolean b) { }
    public Database.QueryLocator start(Database.BatchableContext bc) { return null; }
    public void execute(Database.BatchableContext bc, List<SObject> scope) { }
    public void finish(Database.BatchableContext bc) { }
}
"""
    coll = _collect_entry_point_params(src)
    assert not any(p[0] == "bc" for p in coll)


def test_find_entries_entry_param_filter():
    src = """
public class Multi {
    public static void go(Id fpId, Id surveyIds) { }
}
"""
    all_e = find_entries(src)
    one = find_entries(src, entry_param_filter="fpId")
    assert len(one) == 1
    assert one[0].name.startswith("Receive fpId")


def test_find_exits_aura_list_return():
    src = """
public class Ex {
    @AuraEnabled
    public static List<Opportunity> listOpps() { return null; }
}
"""
    xs = find_exits(src)
    assert any(x.movement_type == "X" and x.data_group_ref == "Opportunity" for x in xs)


def test_find_exits_skips_void():
    src = """
public class Vo {
    public static void noop() { }
}
"""
    assert find_exits(src) == []


def test_find_exits_skips_map_return():
    src = """
public class Mp {
    @AuraEnabled
    public static Map<Id, Account> m() { return null; }
}
"""
    assert find_exits(src) == []


def test_find_exits_skips_boolean_wrapper_return():
    src = """
public class Bw {
    @AuraEnabled
    public static Boolean ok() { return true; }
}
"""
    assert find_exits(src) == []


def test_parse_batch_constructor_with_brace_in_string():
    src = """
public class BraceBatch implements Database.Batchable {
    public BraceBatch() {
        String s = '{';
        load();
    }
    void load() {
        List<User> u = [SELECT Id FROM User WHERE Id != null];
    }
    public Database.QueryLocator start(Database.BatchableContext bc) { return null; }
    public void execute(Database.BatchableContext bc, List<SObject> scope) { }
    public void finish(Database.BatchableContext bc) { }
}
"""
    _, movements = parse(src)
    assert any(m.data_group_ref == "User" for m in movements)


def test_parse_batch_sets_execution_order_on_reads():
    src = """
public class BatchR implements Database.Batchable {
    public BatchR() {
        innerRead();
        loadAccounts();
    }
    void innerRead() {
        List<Contact> cs = [SELECT Id FROM Contact WHERE Id != null];
    }
    void loadAccounts() {
        List<Account> rows = [SELECT Id FROM Account WHERE Id != null];
    }
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([SELECT Id FROM User WHERE Id != null]);
    }
    public void execute(Database.BatchableContext bc, List<SObject> scope) {
    }
    public void finish(Database.BatchableContext bc) { }
}
"""
    _, movements = parse(src)
    reads = [m for m in movements if m.movement_type == "R"]
    by_obj = {m.data_group_ref: m for m in reads}
    assert by_obj["Contact"].execution_order is not None
    assert by_obj["Account"].execution_order is not None


def test_get_entry_points_empty_class():
    assert get_entry_points("public class Empty { }") == []


def test_infer_set_id_survey_ids_branch():
    src = "public class X { }"
    assert _infer_object_from_param("surveyIds", "Set<Id>", src) == "Survey__c"


def test_infer_single_id_custom_field_suffix():
    src = "public class X { }"
    assert _infer_object_from_param("customObj__cId", "Id", src) == "customObj__c"


def test_infer_returns_unknown_when_no_match():
    src = "public class X { }"
    assert _infer_object_from_param("m", "Blob", src) == "Unknown"


def test_find_exits_skips_primitive_return():
    src = """
public class Pr {
    @AuraEnabled
    public static Integer count() { return 0; }
}
"""
    assert find_exits(src) == []


def test_get_entry_point_method_names_invocable():
    src = """
public class InvOnly {
    @InvocableMethod
    public static void run() { }
}
"""
    names = _get_entry_point_method_names(src, extract_class_name(src))
    assert names == frozenset({"run"})


def test_get_entry_points_invocable_only_method():
    src = """
public class InvOnly {
    @InvocableMethod
    public static void run() { }
}
"""
    assert get_entry_points(src) == []


def test_infer_facility_ids_list():
    src = "public class X { }"
    assert _infer_object_from_param("facilityIds", "List<Id>", src) == "Facility__c"


def test_infer_usage_binds_first_matching_param():
    src = """
public class X {
    void m(Id z) {
        First__c = :z;
        Second__c = :z;
    }
}
"""
    assert _infer_object_from_param("z", "Id", src) == "First__c"


def test_collect_constructor_skips_unknown_param():
    src = """
public class UnkCtor implements Database.Batchable {
    public UnkCtor(Blob raw) { }
    public Database.QueryLocator start(Database.BatchableContext bc) { return null; }
    public void execute(Database.BatchableContext bc, List<SObject> scope) { }
    public void finish(Database.BatchableContext bc) { }
}
"""
    coll = _collect_entry_point_params(src)
    assert not any(p[0] == "raw" for p in coll)


def test_find_exits_skips_query_locator_return():
    src = """
public class Ql {
    @AuraEnabled
    public static Database.QueryLocator loc() { return null; }
}
"""
    assert find_exits(src) == []


def test_parse_with_entry_filter():
    src = """
public class F {
    public static void go(Id fpId, Id accId) { }
}
"""
    _, movements = parse(src, entry_param_filter="fpId")
    es = [m for m in movements if m.movement_type == "E"]
    assert len(es) == 1
