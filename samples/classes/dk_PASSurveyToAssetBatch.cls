/**
 * @description Batch to create and reconcile Location/Component Asset records from Finalised PAS Survey Line Items.
 * Hierarchy: Facility Asset (existing) -> Location Asset -> Component Asset.
 * Requires: Facility Assets created first via dk_FacilityToAssetBatch.
 * Supports optional Facility scope filter for testing.
 * Use forSurveys(Set<Id>) to process specific Surveys instead of Facilities.
 * Reconciliation: Location/Component Assets not in survey -> Status Inactive (ParentId retained for Components).
 * NOTE: Contains temporary [DEBUG] Application Logs for troubleshooting - remove after debugging.
 */
public class dk_PASSurveyToAssetBatch implements Database.Batchable<sObject> {

    private static final String FACILITY_RT = 'Facility';
    private static final String LOCATION_RT = 'Location';
    private static final String COMPONENT_RT = 'Component';
    private static final String STATUS_FINALIZED = 'Finalized';
    private static final String STATUS_INACTIVE = 'Inactive';
    private static final String QUESTION_OVERALL_CONDITION = 'Overall Condition';
    private static final String COMPONENT_CONDITION_OVERALL = 'Condition-Overall';
    private static final String COMPONENT_CONDITION_OVERALL_KITCHEN = 'Condition-Overall-Kitchen';
    private static final String COMPONENT_BATHROOM_OVERALL = 'Bathroom Overall';
    private static final String QUESTION_CONDITION = 'Condition';
    private static final String LOCATION_DATA_MIGRATION = 'Data Migration';
    private static final String LOCATION_ACES = 'ACES';
    private static final String CONDITION_PREFIX = 'Condition-';

    private Set<Id> facilityIds;
    private Set<Id> surveyIds;
    private Id locationRecordTypeId;
    private Id componentRecordTypeId;

    public dk_PASSurveyToAssetBatch() {
        this((Set<Id>) null);
    }

    public dk_PASSurveyToAssetBatch(Set<Id> facilityIds) {
        this.facilityIds = facilityIds;
        loadRecordTypeIds();
    }

    public static dk_PASSurveyToAssetBatch forSurveys(Set<Id> surveyIds) {
        dk_PASSurveyToAssetBatch b = new dk_PASSurveyToAssetBatch();
        b.surveyIds = surveyIds;
        return b;
    }

    private void loadRecordTypeIds() {
        for (RecordType rt : [
                SELECT Id, DeveloperName
                FROM RecordType
                WHERE SObjectType = 'Asset'
                AND DeveloperName IN (:LOCATION_RT, :COMPONENT_RT)
        ]) {
            if (rt.DeveloperName == LOCATION_RT) locationRecordTypeId = rt.Id;
            else if (rt.DeveloperName == COMPONENT_RT) componentRecordTypeId = rt.Id;
        }
        ApplicationLogHandler.addCustomLog('dk_PASSurveyToAssetBatch', 'constructor', '[DEBUG] RecordTypes loaded: Location=' + (locationRecordTypeId != null) + ', Component=' + (componentRecordTypeId != null));
    }

    public Database.QueryLocator start(Database.BatchableContext bc) {
        String filterMsg = isNotEmpty(surveyIds) ? surveyIds.size() + ' surveys' : (isNotEmpty(facilityIds) ? facilityIds.size() + ' facilities' : 'none (all)');
        ApplicationLogHandler.addCustomLog('dk_PASSurveyToAssetBatch', 'start', '[DEBUG] filter=' + filterMsg);
        ApplicationLogHandler.saveLog();
        String query = 'SELECT Id, Name, Facility__c FROM Survey__c ' +
                'WHERE RecordType.DeveloperName = \'PAS\' ' +
                'AND Status__c = :STATUS_FINALIZED ' +
                'and createdby.name != \'Data Migration User\'' +
                'AND Facility__c != null ';
        if (isNotEmpty(surveyIds)) {
            query += 'AND Id IN :surveyIds ';
        } else if (isNotEmpty(facilityIds)) {
            query += 'AND Facility__c IN :facilityIds ';
        }
        query += 'ORDER BY Survey_Date__c DESC';
        return Database.getQueryLocator(query);
    }

    public void execute(Database.BatchableContext bc, List<Survey__c> scope) {
        try {
            if (!validateRecordTypes()) return;

            Map<Id, Survey__c> surveysToProcess = buildSurveysToProcess(scope);
            if (surveysToProcess.isEmpty()) return;

            Set<Id> facilityIdsToProcess = extractFacilityIds(surveysToProcess);
            Set<Id> surveyIdsForSli = extractSurveyIds(surveysToProcess);
            logSurveyContext(surveysToProcess);

            Map<Id, Facility__c> facilityById = getFacilities(facilityIdsToProcess);
            Map<Id, Id> facilityAssetByFacilityId = getFacilityAssetIds(facilityIdsToProcess);
            logFacilitiesWithNoAsset(facilityIdsToProcess, facilityAssetByFacilityId, surveysToProcess);

            List<Survey_Line_Item__c> sliList = getSurveyLineItems(surveyIdsForSli);
            if (sliList.isEmpty()) return;

            ExtIdSets extIds = collectExternalIds(sliList);
            Map<String, Id> existingLocationByExtId = getExistingAssetsByExtId(extIds.location, locationRecordTypeId);
            Map<String, Id> existingComponentByExtId = getExistingAssetsByExtId(extIds.component, componentRecordTypeId);
            logDebug('execute: existing Location Assets=' + existingLocationByExtId.size() + ', existing Component Assets=' + existingComponentByExtId.size());

            Map<String, Id> locationAssetIdByKey = new Map<String, Id>(existingLocationByExtId);
            LocationLists locationLists = buildLocationAssets(surveysToProcess, sliList, facilityById, facilityAssetByFacilityId, existingLocationByExtId, locationAssetIdByKey);

            processLocationInserts(locationLists.toInsert, locationAssetIdByKey);
            processLocationUpdates(locationLists.toUpdate);

            Map<String, ComponentSliInfo> componentSliInfoByKey = buildComponentSliInfoByKey(sliList);
            ComponentResult componentResult = buildComponentAssets(sliList, facilityAssetByFacilityId, locationAssetIdByKey, existingComponentByExtId, componentSliInfoByKey);
            processComponentInserts(componentResult.toInsert);
            processComponentUpdates(componentResult.toUpdate);

            Map<Id, Set<String>> locationDisplayNamesByFacility = buildLocationDisplayNamesByFacility(surveysToProcess, sliList);
            List<Asset> locationAssetsToInactivate = getLocationAssetsToInactivate(facilityIdsToProcess, locationDisplayNamesByFacility);
            processLocationInactivations(locationAssetsToInactivate);

            List<Asset> componentAssetsToDeactivate = getComponentAssetsToDeactivate(facilityIdsToProcess, componentSliInfoByKey);
            processComponentDeactivations(componentAssetsToDeactivate);

            logDebug('execute: batch complete');
        } catch (Exception ex) {
            ApplicationLogHandler.addLog('dk_PASSurveyToAssetBatch', 'execute', ex);
            logDebug('execute: EXCEPTION - ' + ex.getMessage() + ' at ' + ex.getLineNumber());
        } finally {
            saveLog();
        }
    }

    private Boolean validateRecordTypes() {
        if (locationRecordTypeId == null || componentRecordTypeId == null) {
            logError('Asset record types Location or Component not found.');
            return false;
        }
        return true;
    }

    private Map<Id, Survey__c> buildSurveysToProcess(List<Survey__c> scope) {
        Map<Id, Survey__c> surveysToProcess = new Map<Id, Survey__c>();
        logDebug('execute: scope size=' + scope.size());

        if (isNotEmpty(surveyIds)) {
            for (Survey__c s : scope) {
                if (s.Facility__c != null) {
                    surveysToProcess.put(s.Id, s);
                }
            }
        } else {
            for (Survey__c s : scope) {
                if (s.Facility__c != null && !surveysToProcess.containsKey(s.Facility__c)) {
                    surveysToProcess.put(s.Facility__c, s);
                }
            }
        }

        if (surveysToProcess.isEmpty()) {
            logDebug('execute: no surveys with Facility, skipping batch');
        }
        return surveysToProcess;
    }

    private Set<Id> extractFacilityIds(Map<Id, Survey__c> surveysToProcess) {
        Set<Id> ids = new Set<Id>();
        for (Survey__c s : surveysToProcess.values()) {
            if (s.Facility__c != null) ids.add(s.Facility__c);
        }
        return ids;
    }

    private Set<Id> extractSurveyIds(Map<Id, Survey__c> surveysToProcess) {
        Set<Id> ids = new Set<Id>();
        for (Survey__c s : surveysToProcess.values()) {
            ids.add(s.Id);
        }
        return ids;
    }

    private void logSurveyContext(Map<Id, Survey__c> surveysToProcess) {
        List<String> surveyNumbers = new List<String>();
        for (Survey__c s : surveysToProcess.values()) {
            surveyNumbers.add(s.Name != null ? s.Name : s.Id);
        }
        logDebug('execute: surveysToProcess count=' + surveysToProcess.size() + ', Survey numbers: ' + String.join(surveyNumbers, ', '));
    }

    private void logFacilitiesWithNoAsset(Set<Id> facilityIdsToProcess, Map<Id, Id> facilityAssetByFacilityId, Map<Id, Survey__c> surveysToProcess) {
        logDebug('execute: facilities found=' + facilityIdsToProcess.size() + ', facilityAssets found=' + facilityAssetByFacilityId.size());
        Set<Id> facilitiesWithNoAsset = new Set<Id>();
        for (Id fid : facilityIdsToProcess) {
            if (!facilityAssetByFacilityId.containsKey(fid)) facilitiesWithNoAsset.add(fid);
        }
        if (!facilitiesWithNoAsset.isEmpty()) {
            List<String> skipDetails = new List<String>();
            for (Id fid : facilitiesWithNoAsset) {
                String surveyNames = '';
                for (Survey__c sv : surveysToProcess.values()) {
                    if (sv.Facility__c == fid) surveyNames += (String.isNotBlank(surveyNames) ? ',' : '') + sv.Name;
                }
                skipDetails.add('Facility=' + fid + (String.isNotBlank(surveyNames) ? ' Surveys=' + surveyNames : ''));
            }
            logDebug('execute: facilities with NO Facility Asset (will skip): ' + String.join(skipDetails, '; '));
        }
    }

    private ExtIdSets collectExternalIds(List<Survey_Line_Item__c> sliList) {
        Set<String> locationExtIds = new Set<String>();
        Set<String> componentExtIds = new Set<String>();
        for (Survey_Line_Item__c sli : sliList) {
            Id facilityId = sli.Survey__r.Facility__c;
            if (facilityId == null) continue;
            String locKey = facilityId + '_' + sli.Location__c;
            locationExtIds.add(locKey);
            if (isComponentSli(sli) || isOverallConditionSli(sli)) {
                componentExtIds.add(locKey + '_' + sli.Component__c);
            }
        }
        logDebug('execute: SLI count=' + sliList.size());
        return new ExtIdSets(locationExtIds, componentExtIds);
    }

    private LocationLists buildLocationAssets(Map<Id, Survey__c> surveysToProcess, List<Survey_Line_Item__c> sliList,
            Map<Id, Facility__c> facilityById, Map<Id, Id> facilityAssetByFacilityId,
            Map<String, Id> existingLocationByExtId, Map<String, Id> locationAssetIdByKey) {
        List<Asset> toInsert = new List<Asset>();
        Map<String, Asset> toUpdateByKey = new Map<String, Asset>();
        Integer facilitiesSkippedNoAsset = 0;

        for (Survey__c survey : surveysToProcess.values()) {
            Id facilityId = survey.Facility__c;
            Id facilityAssetId = facilityAssetByFacilityId.get(facilityId);
            if (facilityAssetId == null) {
                logError('No Facility Asset for Facility ' + facilityId + ', Survey ' + (String.isNotBlank(survey.Name) ? survey.Name : survey.Id) + ', skipping.');
                facilitiesSkippedNoAsset++;
                continue;
            }
            Facility__c facility = facilityById.get(facilityId);
            Set<String> allLocationsInSurvey = collectLocationsForSurvey(sliList, survey.Id);
            Set<String> seenLocations = new Set<String>();

            for (Survey_Line_Item__c sli : sliList) {
                if (sli.Survey__c != survey.Id) continue;
                String locName = sli.Location__c;
                if (String.isBlank(locName)) continue;
                String locKey = facilityId + '_' + locName;
                Id existingLocId = existingLocationByExtId.get(locKey);
                if (existingLocId == null) existingLocId = locationAssetIdByKey.get(locKey);

                if (existingLocId != null) {
                    if (!startsWithKitchenOrBathroom(locName)) continue;
                    Decimal conditionRating = resolveLocationCondition(sli, sliList, locName);
                    if (conditionRating != null && !toUpdateByKey.containsKey(locKey)) {
                        toUpdateByKey.put(locKey, new Asset(Id = existingLocId, dk_Condition_Rating__c = conditionRating, dk_LastUpdatingPAS_Survey__c = survey.Id));
                    }
                    continue;
                }
                if (seenLocations.contains(locName)) continue;
                seenLocations.add(locName);

                String displayName = resolveLocationDisplayName(locName, allLocationsInSurvey);
                Decimal conditionRating = resolveLocationCondition(sli, sliList, locName);
                Asset locAsset = buildLocationAsset(displayName, facilityAssetId, facilityId, facility, survey.Id, conditionRating, locKey);
                if (locAsset != null) toInsert.add(locAsset);
            }
        }
        if (facilitiesSkippedNoAsset > 0) {
            logDebug('execute: facilities skipped (no Facility Asset)=' + facilitiesSkippedNoAsset);
        }
        logDebug('execute: locationsToInsert count=' + toInsert.size());
        return new LocationLists(toInsert, toUpdateByKey);
    }

    private void processLocationInserts(List<Asset> records, Map<String, Id> locationAssetIdByKey) {
        if (records.isEmpty()) return;
        Database.SaveResult[] results = Database.insert(records, false);
        processInsertResults(records, results, 'Location Asset', locationAssetIdByKey);
    }

    private void processLocationUpdates(Map<String, Asset> toUpdateByKey) {
        if (toUpdateByKey.isEmpty()) return;
        List<Asset> records = new List<Asset>(toUpdateByKey.values());
        Database.SaveResult[] results = Database.update(records, false);
        processUpdateResults(records, results, 'Location Asset update (condition)');
    }

    private Map<String, ComponentSliInfo> buildComponentSliInfoByKey(List<Survey_Line_Item__c> sliList) {
        Map<String, ComponentSliInfo> result = new Map<String, ComponentSliInfo>();
        for (Survey_Line_Item__c sli : sliList) {
            Boolean isComponent = isComponentSli(sli);
            Boolean isOverall = isOverallConditionSli(sli);
            if (!isComponent && !isOverall) continue;
            Id facilityId = sli.Survey__r.Facility__c;
            if (facilityId == null) continue;
            String locKey = facilityId + '_' + sli.Location__c;
            String compKey = locKey + '_' + sli.Component__c;
            Decimal conditionRating = isOverall ? resolveConditionRatingFromSli(sli) : sli.Condition_Rating__c;
            String componentType = translateComponentType(
                    String.isNotBlank(sli.Component_Description__c) ? sli.Component_Description__c : sli.Component__c);
            result.put(compKey, new ComponentSliInfo(conditionRating, sli.Survey__c, componentType));
        }
        return result;
    }

    private ComponentResult buildComponentAssets(List<Survey_Line_Item__c> sliList, Map<Id, Id> facilityAssetByFacilityId,
            Map<String, Id> locationAssetIdByKey, Map<String, Id> existingComponentByExtId, Map<String, ComponentSliInfo> componentSliInfoByKey) {
        List<Asset> toInsert = new List<Asset>();
        Map<String, Asset> toUpdateByKey = new Map<String, Asset>();
        Set<String> compKeysQueuedForInsert = new Set<String>();
        Integer compSkippedNoLocAsset = 0;

        for (Survey_Line_Item__c sli : sliList) {
            Boolean isComponent = isComponentSli(sli);
            Boolean isOverall = isOverallConditionSli(sli);
            if (!isComponent && !isOverall) continue;
            Id facilityId = sli.Survey__r.Facility__c;
            if (facilityId == null) continue;
            Id facilityAssetId = facilityAssetByFacilityId.get(facilityId);
            if (facilityAssetId == null) continue;
            String locKey = facilityId + '_' + sli.Location__c;
            Id locationAssetId = locationAssetIdByKey.get(locKey);
            if (locationAssetId == null) {
                compSkippedNoLocAsset++;
                String surveyNum = (sli.Survey__r != null && String.isNotBlank(sli.Survey__r.Name)) ? sli.Survey__r.Name : String.valueOf(sli.Survey__c);
                logDebug('Component SLI skipped (no Location Asset): Survey=' + surveyNum + ', Location=' + sli.Location__c + ', Component=' + sli.Component__c + ', SLI=' + sli.Id);
                continue;
            }

            String compKey = locKey + '_' + sli.Component__c;
            ComponentSliInfo info = componentSliInfoByKey.get(compKey);
            Id existingCompId = existingComponentByExtId.get(compKey);
            if (existingCompId != null && info != null && !toUpdateByKey.containsKey(compKey)) {
                Asset toUpdate = new Asset(Id = existingCompId, dk_Condition_Rating__c = info.conditionRating, dk_LastUpdatingPAS_Survey__c = info.surveyId);
                if (String.isNotBlank(info.componentType)) toUpdate.dk_Component_Type__c = info.componentType;
                toUpdateByKey.put(compKey, toUpdate);
                continue;
            }

            if (compKeysQueuedForInsert.contains(compKey)) continue;
            compKeysQueuedForInsert.add(compKey);

            Decimal conditionRating = info != null ? info.conditionRating : (isOverall ? resolveConditionRatingFromSli(sli) : sli.Condition_Rating__c);
            Asset compAsset = buildComponentAsset(sli, locationAssetId, facilityId, sli.Survey__c, compKey, conditionRating);
            if (compAsset != null) toInsert.add(compAsset);
        }
        if (compSkippedNoLocAsset > 0) {
            logDebug('Component SLIs skipped: noLocationAsset=' + compSkippedNoLocAsset);
        }
        logDebug('execute: componentsToInsert count=' + toInsert.size() + ', componentsToUpdate count=' + toUpdateByKey.size());
        return new ComponentResult(toInsert, toUpdateByKey);
    }

    private void processComponentInserts(List<Asset> records) {
        if (records.isEmpty()) return;
        Database.SaveResult[] results = Database.insert(records, false);
        processInsertResults(records, results, 'Component Asset', null);
    }

    private void processComponentUpdates(Map<String, Asset> toUpdateByKey) {
        if (toUpdateByKey.isEmpty()) return;
        List<Asset> records = new List<Asset>(toUpdateByKey.values());
        Database.SaveResult[] results = Database.update(records, false);
        processUpdateResults(records, results, 'Component Asset update (condition)');
    }

    private Map<Id, Set<String>> buildLocationDisplayNamesByFacility(Map<Id, Survey__c> surveysToProcess, List<Survey_Line_Item__c> sliList) {
        Map<Id, Set<String>> result = new Map<Id, Set<String>>();
        Map<Id, Set<String>> locationsByFacility = new Map<Id, Set<String>>();
        for (Survey_Line_Item__c sli : sliList) {
            Id facilityId = sli.Survey__r.Facility__c;
            if (facilityId == null) continue;
            if (!locationsByFacility.containsKey(facilityId)) {
                locationsByFacility.put(facilityId, new Set<String>());
            }
            if (String.isNotBlank(sli.Location__c)) {
                locationsByFacility.get(facilityId).add(sli.Location__c.trim());
            }
        }
        for (Id facilityId : locationsByFacility.keySet()) {
            Set<String> allLocations = locationsByFacility.get(facilityId);
            Set<String> displayNames = new Set<String>();
            for (String loc : allLocations) {
                displayNames.add(resolveLocationDisplayName(loc, allLocations));
            }
            result.put(facilityId, displayNames);
        }
        return result;
    }

    private List<Asset> getLocationAssetsToInactivate(Set<Id> facilityIds, Map<Id, Set<String>> locationDisplayNamesByFacility) {
        List<Asset> result = new List<Asset>();
        if (facilityIds.isEmpty()) return result;
        for (Asset a : [
                SELECT Id, Name, dk_Facility__c
                FROM Asset
                WHERE RecordTypeId = :locationRecordTypeId
                AND dk_Facility__c IN :facilityIds
                AND Status != :STATUS_INACTIVE
        ]) {
            Set<String> validNames = locationDisplayNamesByFacility.get(a.dk_Facility__c);
            if (validNames == null || !validNames.contains(a.Name)) {
                result.add(new Asset(Id = a.Id, Status = STATUS_INACTIVE));
            }
        }
        logDebug('execute: locationAssetsToInactivate count=' + result.size());
        return result;
    }

    private void processLocationInactivations(List<Asset> records) {
        if (records.isEmpty()) return;
        Database.SaveResult[] results = Database.update(records, false);
        processUpdateResults(records, results, 'Location Asset inactivate');
    }

    private List<Asset> getComponentAssetsToDeactivate(Set<Id> facilityIds, Map<String, ComponentSliInfo> componentSliInfoByKey) {
        List<Asset> result = new List<Asset>();
        if (facilityIds.isEmpty()) return result;
        Set<String> componentsInSurvey = componentSliInfoByKey.keySet();
        for (Asset a : [
                SELECT Id, ExternalIdentifier
                FROM Asset
                WHERE RecordTypeId = :componentRecordTypeId
                AND dk_Facility__c IN :facilityIds
                AND Status != :STATUS_INACTIVE
        ]) {
            String compKey = String.isNotBlank(a.ExternalIdentifier) ? a.ExternalIdentifier : null;
            if (compKey == null) continue;
            if (!componentsInSurvey.contains(compKey)) {
                result.add(new Asset(Id = a.Id, Status = STATUS_INACTIVE));
            }
        }
        logDebug('execute: componentAssetsToDeactivate count=' + result.size());
        return result;
    }

    private void processComponentDeactivations(List<Asset> records) {
        if (records.isEmpty()) return;
        Database.SaveResult[] results = Database.update(records, false);
        processUpdateResults(records, results, 'Component Asset deactivate');
    }

    private void processInsertResults(List<Asset> records, Database.SaveResult[] results, String type, Map<String, Id> extIdMap) {
        Integer successCount = 0;
        Integer failCount = 0;
        for (Integer i = 0; i < results.size(); i++) {
            if (results[i].isSuccess()) {
                if (extIdMap != null && String.isNotBlank(records[i].ExternalIdentifier)) {
                    extIdMap.put(records[i].ExternalIdentifier, records[i].Id);
                }
                successCount++;
            } else {
                logInsertErrors(type, records[i], results[i].getErrors());
                failCount++;
            }
        }
        logDebug('execute: ' + type + ' insert result: success=' + successCount + ', failed=' + failCount);
    }

    private void processUpdateResults(List<Asset> records, Database.SaveResult[] results, String type) {
        Integer successCount = 0;
        Integer failCount = 0;
        for (Integer i = 0; i < results.size(); i++) {
            if (results[i].isSuccess()) {
                successCount++;
            } else {
                logInsertErrors(type, records[i], results[i].getErrors());
                failCount++;
            }
        }
        logDebug('execute: ' + type + ' result: success=' + successCount + ', failed=' + failCount);
    }

    private Boolean isNotEmpty(Set<Id> ids) {
        return ids != null && !ids.isEmpty();
    }

    private Boolean isComponentSli(Survey_Line_Item__c sli) {
        return QUESTION_CONDITION.equals(sli.Question_Label__c)
                && String.isNotBlank(sli.Component__c)
                && sli.Condition_Rating__c != null;
    }

    private Boolean isOverallConditionSli(Survey_Line_Item__c sli) {
        if (String.isBlank(sli.Location__c) || String.isBlank(sli.Component__c)) return false;
        String qLabel = String.isNotBlank(sli.Question_Label__c) ? sli.Question_Label__c.trim() : '';
        if (!QUESTION_OVERALL_CONDITION.equals(qLabel) || qLabel.contains('Mandatory Photo')) return false;
        String loc = sli.Location__c.trim();
        String comp = sli.Component__c.trim();
        if (loc.startsWith('Kitchen')) {
            return COMPONENT_CONDITION_OVERALL.equals(comp) || COMPONENT_CONDITION_OVERALL_KITCHEN.equals(comp);
        }
        if (loc.startsWith('Bathroom')) {
            return COMPONENT_BATHROOM_OVERALL.equals(comp);
        }
        return false;
    }

    private Decimal resolveLocationCondition(Survey_Line_Item__c sli, List<Survey_Line_Item__c> allSli, String locName) {
        if (!startsWithKitchenOrBathroom(locName)) return null;
        Boolean isKitchen = locName.startsWith('Kitchen');
        String locNameNorm = locName.trim();
        for (Survey_Line_Item__c s : allSli) {
            if (s.Survey__c != sli.Survey__c) continue;
            if (String.isBlank(s.Location__c) || !s.Location__c.trim().equals(locNameNorm)) continue;
            String qLabel = String.isNotBlank(s.Question_Label__c) ? s.Question_Label__c.trim() : '';
            String comp = String.isNotBlank(s.Component__c) ? s.Component__c.trim() : '';
            if (!QUESTION_OVERALL_CONDITION.equals(qLabel)) continue;
            if (isKitchen && (COMPONENT_CONDITION_OVERALL.equals(comp) || COMPONENT_CONDITION_OVERALL_KITCHEN.equals(comp))) {
                return resolveConditionRatingFromSli(s);
            }
            if (!isKitchen && locName.startsWith('Bathroom') && COMPONENT_BATHROOM_OVERALL.equals(comp)) {
                if (qLabel.contains('Mandatory Photo')) continue;
                return resolveConditionRatingFromSli(s);
            }
        }
        return null;
    }

    private Decimal resolveConditionRatingFromSli(Survey_Line_Item__c sli) {
        Decimal rating = parseAnswerTextAsNumber(sli.Answer_Text__c);
        return rating != null ? rating : parseAnswerTextAsNumber(sli.Condition__c);
    }

    private Set<String> collectLocationsForSurvey(List<Survey_Line_Item__c> sliList, Id surveyId) {
        Set<String> result = new Set<String>();
        for (Survey_Line_Item__c sli : sliList) {
            if (sli.Survey__c != surveyId || String.isBlank(sli.Location__c)) continue;
            result.add(sli.Location__c.trim());
        }
        return result;
    }

    /**
     * @description Resolves display name for Location Asset. When location has no numeric suffix, is single-word,
     * and is the only instance of that type in the facility, adds " 1" suffix. Multi-word types (e.g. "Bedroom Master")
     * are left unchanged.
     */
    private String resolveLocationDisplayName(String locName, Set<String> allLocationsInSurvey) {
        if (String.isBlank(locName)) return locName;
        String trimmed = locName.trim();
        if (hasNumericSuffix(trimmed)) return trimmed;
        if (trimmed.split(' ').size() > 1) return trimmed;
        String baseType = getBaseLocationType(trimmed);
        Integer sameTypeCount = 0;
        for (String other : allLocationsInSurvey) {
            if (getBaseLocationType(other).equals(baseType)) sameTypeCount++;
        }
        return sameTypeCount == 1 ? trimmed + ' 1' : trimmed;
    }

    private Boolean hasNumericSuffix(String locName) {
        if (String.isBlank(locName)) return false;
        List<String> parts = locName.trim().split(' ');
        if (parts.isEmpty()) return false;
        try {
            Integer.valueOf(parts[parts.size() - 1]);
            return true;
        } catch (TypeException e) {
            return false;
        }
    }

    private String getBaseLocationType(String locName) {
        if (String.isBlank(locName)) return locName;
        List<String> parts = locName.trim().split(' ');
        if (parts.size() < 2) return locName.trim();
        try {
            Integer.valueOf(parts[parts.size() - 1]);
            List<String> baseParts = new List<String>();
            for (Integer i = 0; i < parts.size() - 1; i++) baseParts.add(parts[i]);
            return String.join(baseParts, ' ');
        } catch (TypeException e) {
            return locName.trim();
        }
    }

    /**
     * @description Removes "Condition-" prefix from component name per SLI mapping rules.
     * @param component Raw value from Survey Line Item Component__c.
     * @return Component name with prefix stripped (e.g. "Condition-Floor Finish" -> "Floor Finish").
     */
    private String stripConditionPrefix(String component) {
        if (String.isBlank(component)) return component;
        String trimmed = component.trim();
        if (trimmed.startsWith(CONDITION_PREFIX)) {
            return trimmed.substring(CONDITION_PREFIX.length()).trim();
        }
        return trimmed;
    }

    /**
     * @description Translation layer for component type. Placeholder for future extensions (e.g. mapping, normalization).
     * @param rawComponentType Source value from Survey Line Item (Component_Description__c or Component__c).
     * @return Translated component type for dk_Component_Type__c.
     */
    private String translateComponentType(String rawComponentType) {
        return rawComponentType;
    }

    private Boolean startsWithKitchenOrBathroom(String locName) {
        return String.isNotBlank(locName) && (locName.startsWith('Kitchen') || locName.startsWith('Bathroom'));
    }

    private Decimal parseAnswerTextAsNumber(String answerText) {
        if (String.isBlank(answerText)) return null;
        try {
            String trimmed = answerText.trim();
            return String.isBlank(trimmed) ? null : Decimal.valueOf(trimmed);
        } catch (TypeException e) {
            return null;
        }
    }

    private Asset buildLocationAsset(String locName, Id facilityAssetId, Id facilityId, Facility__c facility,
            Id surveyId, Decimal conditionRating, String extId) {
        Asset asset = new Asset();
        asset.RecordTypeId = locationRecordTypeId;
        asset.ParentId = facilityAssetId;
        asset.Name = locName;
        asset.ExternalIdentifier = extId;
        asset.dk_Facility__c = facilityId;
        asset.dk_LastUpdatingPAS_Survey__c = surveyId;
        asset.Status = 'Installed';
        if (conditionRating != null) asset.dk_Condition_Rating__c = conditionRating;
        if (facility != null) {
            asset.Street = buildStreetAddress(facility.Unit_Number__c, facility.Street_Number__c, facility.Street_Name__c);
            asset.City = facility.Suburb__c;
            asset.PostalCode = facility.Postcode__c;
            asset.State = facility.State__c;
            if (String.isNotBlank(facility.State__c)) asset.Country = 'Australia';
        }
        return asset;
    }

    private Asset buildComponentAsset(Survey_Line_Item__c sli, Id locationAssetId, Id facilityId, Id surveyId, String extId, Decimal conditionRating) {
        Asset asset = new Asset();
        asset.RecordTypeId = componentRecordTypeId;
        asset.ParentId = locationAssetId;
        asset.Name = stripConditionPrefix(sli.Component__c);
        asset.ExternalIdentifier = extId;
        asset.dk_Facility__c = facilityId;
        asset.dk_Condition_Rating__c = conditionRating;
        asset.dk_Component_Type__c = translateComponentType(
                String.isNotBlank(sli.Component_Description__c) ? sli.Component_Description__c : sli.Component__c);
        asset.dk_LastUpdatingPAS_Survey__c = surveyId;
        asset.Status = 'Installed';
        return asset;
    }

    private String buildStreetAddress(String unitNumber, String streetNumber, String streetName) {
        List<String> parts = new List<String>();
        if (String.isNotBlank(unitNumber)) parts.add(unitNumber);
        if (String.isNotBlank(streetNumber)) parts.add(streetNumber);
        if (String.isNotBlank(streetName)) parts.add(streetName);
        if (parts.isEmpty()) return null;
        if (String.isNotBlank(unitNumber) && String.isNotBlank(streetNumber)) {
            return unitNumber + '/' + streetNumber + ' ' + streetName;
        }
        return String.join(parts, ' ');
    }

    private Map<Id, Facility__c> getFacilities(Set<Id> facilityIds) {
        Map<Id, Facility__c> result = new Map<Id, Facility__c>();
        for (Facility__c f : [
                SELECT Id, Unit_Number__c, Street_Number__c, Street_Name__c,
                        Suburb__c, Postcode__c, State__c
                FROM Facility__c
                WHERE Id IN :facilityIds
        ]) {
            result.put(f.Id, f);
        }
        return result;
    }

    private Map<Id, Id> getFacilityAssetIds(Set<Id> facilityIds) {
        Map<Id, Id> result = new Map<Id, Id>();
        Id facilityRtId = getFacilityRecordTypeId();
        if (facilityRtId == null) return result;
        for (Asset a : [
                SELECT Id, dk_Facility__c
                FROM Asset
                WHERE dk_Facility__c IN :facilityIds
                AND RecordTypeId = :facilityRtId
        ]) {
            result.put(a.dk_Facility__c, a.Id);
        }
        return result;
    }

    private Id getFacilityRecordTypeId() {
        List<RecordType> rts = [SELECT Id FROM RecordType WHERE SObjectType = 'Asset' AND DeveloperName = :FACILITY_RT LIMIT 1];
        return rts.isEmpty() ? null : rts[0].Id;
    }

    private List<Survey_Line_Item__c> getSurveyLineItems(Set<Id> surveyIds) {
        return [
                SELECT Id, Survey__c, Survey__r.Name, Survey__r.Facility__c, Location__c, Component__c, Component_Description__c,
                        Question_Label__c, Answer_Text__c, Condition_Rating__c, Condition__c
                FROM Survey_Line_Item__c
                WHERE Survey__c IN :surveyIds
                AND Location__c != NULL
                AND Location__c != :LOCATION_DATA_MIGRATION
                AND Location__c != :LOCATION_ACES
        ];
    }

    private Map<String, Id> getExistingAssetsByExtId(Set<String> extIds, Id recordTypeId) {
        Map<String, Id> result = new Map<String, Id>();
        if (extIds.isEmpty()) return result;
        for (Asset a : [
                SELECT Id, ExternalIdentifier
                FROM Asset
                WHERE RecordTypeId = :recordTypeId
                AND ExternalIdentifier IN :extIds
        ]) {
            result.put(a.ExternalIdentifier, a.Id);
        }
        return result;
    }

    private void logDebug(String msg) {
        ApplicationLogHandler.addCustomLog('dk_PASSurveyToAssetBatch', 'execute', '[DEBUG] ' + msg);
    }

    private void logError(String msg) {
        ApplicationLogHandler.addCustomLog('dk_PASSurveyToAssetBatch', 'execute', msg);
    }

    private void logInsertErrors(String type, SObject rec, List<Database.Error> errs) {
        String msgs = '';
        for (Database.Error e : errs) msgs += e.getMessage() + '; ';
        ApplicationLogHandler.addCustomLog('dk_PASSurveyToAssetBatch', 'execute', type + ' insert failed: ' + msgs);
    }

    private void saveLog() {
        ApplicationLogHandler.saveLog();
    }

    public void finish(Database.BatchableContext bc) {
        ApplicationLogHandler.addCustomLog('dk_PASSurveyToAssetBatch', 'finish', '[DEBUG] Batch completed. JobId: ' + bc.getJobId());
        ApplicationLogHandler.saveLog();
    }

    private class ExtIdSets {
        Set<String> location;
        Set<String> component;
        ExtIdSets(Set<String> location, Set<String> component) {
            this.location = location;
            this.component = component;
        }
    }

    private class LocationLists {
        List<Asset> toInsert;
        Map<String, Asset> toUpdate;
        LocationLists(List<Asset> toInsert, Map<String, Asset> toUpdate) {
            this.toInsert = toInsert;
            this.toUpdate = toUpdate;
        }
    }

    private class ComponentResult {
        List<Asset> toInsert;
        Map<String, Asset> toUpdate;
        ComponentResult(List<Asset> toInsert, Map<String, Asset> toUpdate) {
            this.toInsert = toInsert;
            this.toUpdate = toUpdate;
        }
    }

    private class ComponentSliInfo {
        Decimal conditionRating;
        Id surveyId;
        String componentType;
        ComponentSliInfo(Decimal conditionRating, Id surveyId, String componentType) {
            this.conditionRating = conditionRating;
            this.surveyId = surveyId;
            this.componentType = componentType;
        }
    }
}
