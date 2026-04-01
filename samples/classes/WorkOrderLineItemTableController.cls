/**
* ─────────────────────────────────────────────────────────────────────────────────────────────────┐
* This is the controller class for WorkOrderLineItemTable LWC
* ──────────────────────────────────────────────────────────────────────────────────────────────────
* @author         Satya Singh
* @modifiedBy     
* @version        1.0
* @created        10/06/2025
* @modified       19/03/2025

* @LasModifiedBY  Ravi Mankani
* @lastModified   15/09/2025
* 
* @LasModifiedBY  gaurav
* @lastModified   27/10/2025 
* Notes           Added new method getSuiApprovalStatusValues to get the picklist value dynamically
* ─────────────────────────────────────────────────────────────────────────────────────────────────┘
*/
public without sharing class WorkOrderLineItemTableController {

    @AuraEnabled(cacheable=true)
    public static List<Map<String, String>> getSuiApprovalStatusPicklist() {
        List<Map<String, String>> picklistOptions = new List<Map<String, String>>();

        // Describe the field
        Schema.DescribeFieldResult fieldResult = WorkOrderLineItem.Approval_Status__c.getDescribe();
        List<Schema.PicklistEntry> picklistEntries = fieldResult.getPicklistValues();

        // Build list of {label, value} maps
        for (Schema.PicklistEntry entry : picklistEntries) {
            picklistOptions.add(new Map<String, String>{
                'label' => entry.getLabel(),
                'value' => entry.getValue()
            });
        }

        return picklistOptions;
    }

    @AuraEnabled(cacheable=false)
    public static List<SObject> getRecords(String objectApi, List<String> fields,String filterField,Boolean contractorPortal, String recId,String orderByField,String orderByDirection) {
        if (String.isBlank(objectApi) || fields == null || fields.isEmpty()) {
            throw new AuraHandledException('Invalid parameters');
        }
        
        String fieldStr = String.join(fields, ',');
        String query ='';
        
        if(contractorPortal){
            query = 'SELECT Id,Location_Type__r.Name,Supplementary_Works_Type__c, ' + fieldStr + 
                ' FROM ' + String.escapeSingleQuotes(objectApi) + 
                ' WHERE ' + String.escapeSingleQuotes(filterField) + ' = :recId ORDER BY ' + orderByField + ' ' + orderByDirection+' ';
                //'LIMIT 100';
        }
        else{
            
            /*Set<String> excludedSORCodes = new Set<String>();
            //  Loop through metadata and collect only non-null codes
            for (SOR_Metadata__mdt meta : [
                SELECT SOR_Code__c 
                FROM SOR_Metadata__mdt 
                WHERE SOR_Code__c != null
            ]) {
                excludedSORCodes.add(meta.SOR_Code__c);
            }
            
            
            //  Prepare NOT IN clause dynamically
            String notInSorCodes = '';
            if (!excludedSORCodes.isEmpty()) {
                List<String> quotedSORCodes = new List<String>();
                for (String code : excludedSORCodes) {
                    quotedSORCodes.add('\'' + String.escapeSingleQuotes(code) + '\'');
                }
                notInSorCodes = ' AND Service_Item_Code__c NOT IN (' + String.join(quotedSORCodes, ',') + ')';
            }*/
            
            //  Ensure Service_Item_Code__c is in fieldStr
            List<String> individualFields = fieldStr.replaceAll('\\s+', '').split(',');
            Boolean alreadyPresentServiceCode = individualFields.contains('Service_Item_Code__c');
            Boolean alreadyPresentStatus = individualFields.contains('Status');

            String finalFieldStr = fieldStr;

            if (!alreadyPresentServiceCode) {
                finalFieldStr = 'Service_Item_Code__c, ' + finalFieldStr;
            }
            if (!alreadyPresentStatus) {
                finalFieldStr = 'Status, ' + finalFieldStr;
            }
            
            // Final query with additional condition (Original_Quantity or Deactivation_Requested)
            query = 'SELECT Id, ' + finalFieldStr +
            ' FROM ' + objectApi +
            ' WHERE ' + filterField + ' = :recId' +
            //' AND Status IN (\'Unapproved\', \'Active\')' +
            // notInSorCodes +
            ' ORDER BY ' + orderByField + ' ' + orderByDirection ;
            //' LIMIT 100';
                
        }
        
        List<SObject> sObjList = Database.query(query);
        List<SObject> sObjUnapprovedList = new List<SObject>();
        List<SObject> sObjActiveList = new List<SObject>();
        List<SObject> sObjInactiveList = new List<SObject>();
        for(SObject sobj : sObjList) {
            if(sobj.get('Status') == 'Unapproved') {
                sObjUnapprovedList.add(sobj);
            }
            else if(sobj.get('Status') == 'Active') {
                sObjActiveList.add(sobj);
            }
            else {
                sObjInactiveList.add(sobj);
            }
        }
        List<SObject> finalSobjList = new List<SObject>();
        finalSobjList.addAll(sObjUnapprovedList);
        finalSobjList.addAll(sObjActiveList);
        finalSobjList.addAll(sObjInactiveList);
        return finalSobjList;
        //return Database.query(query);
    }

    /*  Added by - Ravi Mankani 
        Modified Date - 15/09/2025
        ---Start---
    */
    @AuraEnabled
    public static List<ApprovalWorkItem> getLatestApprovalRequest( String recId, Datetime pollingStartTime){
        List<ApprovalWorkItem> approvalItem = new List<ApprovalWorkItem>();
        try {
            approvalItem = [SELECT Id, Work_Order__c, CreatedDate, Status 
                        FROM ApprovalWorkItem WHERE Work_Order__c =:recId
                        AND Status = 'Assigned'
                        AND CreatedDate > :pollingStartTime
                        ORDER BY CreatedDate DESC
                        LIMIT 1];
        } catch (Exception e) { 
            throw new AuraHandledException(e.getMessage());
        }

        return approvalItem;
    }
    /* ---End--- */
    
    @AuraEnabled
    public static Boolean updateRecords(String objectApi, List<Object> updates, Boolean isDelegationCheckRequired, Boolean isLocationChange, String recId) {

        if (String.isBlank(objectApi) || updates == null || updates.isEmpty()) {
            throw new AuraHandledException('Invalid update parameters');
        }
        try {
        
            Boolean result = false;
        Map<String, Schema.SObjectField> fields = Schema.getGlobalDescribe().get(objectApi).getDescribe().fields.getMap();
        List<SObject> sObjectUpdates = new List<SObject>();
        
        for (Object row : updates) {
            String jsonStr = JSON.serialize(row);
            Map<String, Object> rowMap = (Map<String, Object>) JSON.deserializeUntyped(jsonStr);
            SObject sobj = (SObject) Type.forName('Schema.' + objectApi).newInstance();
            
            for (String key : rowMap.keySet()) {
                if (!fields.containsKey(key)) continue;
                
                Object val = rowMap.get(key);
                Schema.DisplayType dt = fields.get(key).getDescribe().getType();
                
                // If value is String but field expects Decimal, Integer, Boolean, Date, or DateTime, convert it:
                if (val != null && val instanceof String) {
                    String sval = (String) val;
                    
                    try {
                        if (dt == Schema.DisplayType.Integer) {
                            val = Integer.valueOf(sval);
                        } else if (dt == Schema.DisplayType.Boolean) {
                            val = Boolean.valueOf(sval);
                        } else if (dt == Schema.DisplayType.Date) {
                            val = Date.valueOf(sval);
                        } else if (dt == Schema.DisplayType.DateTime) {
                            val = DateTime.valueOf(sval);
                        }
                        else{
                            val = Decimal.valueOf(sval);
                        }
                    } catch (Exception e) {
                        // Ignore conversion errors, keep original val (could log or throw if needed)
                    }
                }
                
                sobj.put(key, val);
            }
            sObjectUpdates.add(sobj);
        }

        if(isDelegationCheckRequired) {
            WorkOrderTriggerHandler.BY_PASS_SUPPDELEGATION_CHECK = true;
        }
        update sObjectUpdates;
        if(isDelegationCheckRequired) {
            WorkOrderTriggerHandler.BY_PASS_SUPPDELEGATION_CHECK = false;
            }

            //Call subsequent update on Work Order
            result = submitForApproval(recId, isLocationChange, isDelegationCheckRequired);

            return result;
        } catch(Exception e) {

            throw new AuraHandledException(e.getMessage());
        }
    }
    
    @AuraEnabled(cacheable=true)
    public static Map<String, String> getFieldLabels(String objectApi, List<String> fields) {
        Map<String, String> labels = new Map<String, String>();
        Schema.SObjectType sObjType = Schema.getGlobalDescribe().get(objectApi);
        if (sObjType == null) return labels;
        
        Map<String, Schema.SObjectField> fieldMap = sObjType.getDescribe().fields.getMap();
        for (String field : fields) {
            if(field.equalsIgnoreCase('Name')) {
                continue;
            }
            if (fieldMap.containsKey(field)) {
                labels.put(field, fieldMap.get(field).getDescribe().getLabel());
            }
        }
        return labels;
    }
    
    @AuraEnabled
    public static void deactivateLine(List<String> rowIds){
        List<WorkOrderLineItem> woliToUpdate = new List<WorkOrderLineItem>();
        for (WorkOrderLineItem woli:[Select Id,Status from WorkOrderLineItem where Id IN :rowIds]){
            woli.Status = 'Inactive';
            woliToUpdate.add(woli);
        }
        update woliToUpdate;
        
    }
    
    @AuraEnabled
    public static Boolean submitForApproval(String recId, Boolean isLocationChange, Boolean isRequiredApproval){
        Boolean updated = false;
        Id userId = userinfo.getUserId();
        User userDetails =[SELECT Id, Name, Email, Profile.Name, UserRole.Name FROM User where Id=:userId ];
        List<WorkOrder> woToUpdate = new List<WorkOrder>();
        if(isRequiredApproval || userDetails.Profile.Name =='External User'){
            WorkOrder wo = new WorkOrder(Id = recId);
                wo.Supplementary_Works_Indicator__c = 'Requested';
                if(isLocationChange) {
                    wo.Is_Non_Cost_Changes__c = true;
                }
                woToUpdate.add(wo);
            
            if(woToUpdate.size()>0){
                update woToUpdate;
                updated= true ;
            }
            
        } else if(!isRequiredApproval) {

            WorkOrder wo = new WorkOrder(Id = recId, Is_Trigger_Approval__c = false);
            woToUpdate.add(wo);
            
            if(woToUpdate.size()>0){
                update woToUpdate;
                //updated= true ;
            }
        }
        return updated;    
        
    }
    
    @AuraEnabled 
    public static Boolean validateUpdates(String workOrderId){
        try{
            WorkOrder workOrderRec = [SELECT Id, Assigned_to__r.Contractor_API_Version__c, Contract_Type__c
                                      FROM WorkOrder 
                                      WHERE Id =: workOrderId];
            User userData = [SELECT ID, Name, Profile.Name FROM User WHERE ID =: userinfo.getUserId()];
            if(workOrderRec != null && userData.Profile.Name == System.label.External_Profile){
                List<CalculationMatrixVersion> decVersion = [SELECT Name, CalculationMatrix.Name 
                                                             FROM CalculationMatrixVersion 
                                                             WHERE CalculationMatrix.UniqueName =: System.label.Calculation_Matrix];
                List<CalculationMatrixRow> rows = [SELECT ID, InputData, OutPutData 
                                                   FROM CalculationMatrixRow 
                                                   WHERE CalculationMatrixVersionId IN: decVersion];
                for(CalculationMatrixRow row : rows){
                    if(row.InputData.contains(workOrderRec.Contract_Type__c) && row.OutPutData.contains('"Active": false')){
                        return False;
                    }
                }
            }
            return true;
        }catch(Exception e){
            return true;
        }
    }
    
    // get SUI SOR Metadata
    @AuraEnabled(cacheable=true)
    public static List<String> getSORCodeSet() {
        Set<String> sorCodes = new Set<String>();
        
        for (SOR_Metadata__mdt meta : [SELECT SOR_Code__c FROM SOR_Metadata__mdt]) {
            if (meta.SOR_Code__c != null) {
                sorCodes.add(meta.SOR_Code__c);
            }
        }
        return new List<String>(sorCodes); // This conversion is key
    }
    @AuraEnabled
    public static Map<String, Boolean> checkFieldEditability( String objectApiName,List<String> fieldApiNames) {
        Map<String, Boolean> result = new Map<String, Boolean>();

        // Describe fields on the given object
        Map<String, Schema.SObjectField> fieldMap =
            Schema.getGlobalDescribe()
                .get(objectApiName)
                .getDescribe()
                .fields
                .getMap();
        
        // Loop through provided field names
        for(String fieldName : fieldApiNames) {
            if(fieldMap.containsKey(fieldName)) {
                Boolean isUpdateable = fieldMap.get(fieldName).getDescribe().isUpdateable();
                result.put(fieldName, isUpdateable);
            } else {
                // Field does not exist, return false or handle custom logic
                result.put(fieldName, false);
            }
        }
        return result;
    }
}