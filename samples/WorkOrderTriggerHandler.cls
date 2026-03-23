/**
* ─────────────────────────────────────────────────────────────────────────────────────────────────┐
* Trigger Handler for WorkOrder extending TriggerHandler
* ──────────────────────────────────────────────────────────────────────────────────────────────────
* @author         Tarun Seerani (tarun.seerani@sauceconsulting.com.au)
* @modifiedBy     
* @version        1.0
* @created        14/03/2024
* @modified       14/03/2024
* ──────────────────────────────────────────────────────────────────────────────────────────────────
* @changes
* 
* YYYY-MM-DD      Explanation of the change.  Multiple lines can be used to explain the change, but
*                 each line should be indented till left aligned with the previous description text.
* ─────────────────────────────────────────────────────────────────────────────────────────────────┘
*/
public without sharing class WorkOrderTriggerHandler extends TriggerHandler{
    
    //Trigger context variables
    private Map<Id, WorkOrder> newWorkOrderMap;
    private Map<Id, WorkOrder> oldWorkOrderMap;
    private List<WorkOrder> oldWorkOrderList;
    private List<WorkOrder> newWorkOrderList;
    private String profileName;
    private String profileNameCWO;
    private List<FieldDefinition> rollUpFields;
    private Map<Id, WorkOrder> woIdVsRelatedScopingWo;
    private Boolean isIntegrationUser;
    
    public WorkOrderTriggerHandler() {
        //Trigger context variables
        this.oldWorkOrderList = (List<WorkOrder>) Trigger.old;
        this.newWorkOrderList = (List<WorkOrder>) Trigger.new;
        this.oldWorkOrderMap = (Map<Id, WorkOrder>) Trigger.oldMap;
        this.newWorkOrderMap = (Map<Id, WorkOrder>) Trigger.newMap;
        this.profileName = '';
        this.rollUpFields = new List<FieldDefinition>();
        this.woIdVsRelatedScopingWo = new Map<Id, WorkOrder>(); 
        //Retrieve the profile name
        profileNameCWO = [SELECT Id, Name 
                          FROM Profile 
                          WHERE Id = :UserInfo.getProfileId()].Name;        
        isIntegrationUser = FeatureManagement.checkPermission('SUI_IntegrationPermission');
    }
    
    public override void beforeUpdate(sObject so) {
        
        WorkOrder oldWO = oldWorkOrderMap.get(so.Id);
        WorkOrder newWO = newWorkOrderMap.get(so.Id);

        Boolean isRestrict = Boolean.valueOf(System.Label.SUI_WO_Closed_RestrictEdit);
        if(isRestrict){

            if((oldWO.IsClosed || oldWO.Status == 'Works Completed') && 
                (oldWO.SUI_Current_Milestone_Value__c == newWO.SUI_Current_Milestone_Value__c) &&
                !oldWO.SUI_Record_Type_developer_Name__c.equals('SUI_Jobs')){

            
                //Start: 'Edit of closed Work order' related changes
                List<String> updatedField = new List<String>();
                List<String> allowedProfiles;
                List<String> allowedFields;
               
                WorkOrder oldWorkOrderRec; 
                WorkOrder newWorkOrderRec;
                
                String allowedProfilesList = System.Label.SUI_WO_Closed_AllowedProfiles;
                String allowedFieldsList = System.Label.SUI_WO_Closed_AllowedFields + ',' + System.Label.SUI_WO_Closed_AllowedFields1;
                System.debug('1allowedFieldsList'+allowedFieldsList);
                String warningMessage = System.Label.SUI_WO_Closed_WarningMessage;
                
                allowedProfiles = new List<String>(allowedProfilesList.split(','));
                allowedFields = new List<String>(allowedFieldsList.split(','));
             
                if((allowedProfiles.contains(profileNameCWO)) || isIntegrationUser){
                        oldWorkOrderRec = oldWorkOrderMap.get(so.Id);
                        newWorkOrderRec = newWorkOrderMap.get(so.Id);
                       
                        // Iterate over each field and check if it has been updated
                        for (Schema.SObjectField field : WorkOrder.SObjectType.getDescribe().fields.getMap().values()) {
                            String fieldName = field.getDescribe().getName();
                            Object newValue = newWorkOrderRec.get(fieldName);
                            Object oldValue = oldWorkOrderRec != null ? oldWorkOrderRec.get(fieldName) : null;
                            // Check if the field has been updated
                            if (newValue != oldValue  && !allowedFields.contains(fieldName) && (newValue == null || !newValue.equals(oldValue))) {
                                newWorkOrderRec.addError(warningMessage);
                                break;
                            }                           
                        }                      
                }    
            }
        }    
        //End: 'Edit closed Work order' related changes  
        
        WorkOrder newWorkOrder = (WorkOrder) so;
        // Check if the profile name is "Integration User" or 'External User'   
        if((profileNameCWO == GlobalConstants.PROFILE_INTEGRATION_USER)){
            fieldUpdateValidationForIntegrationUser(newWorkOrder);
        } 
    }
    
    //BulkAfter method
    public override void bulkAfter() {
        if(Trigger.isUpdate){
            Id scopingRecordTypeId = SObjectType.WorkOrder.getRecordTypeInfosByDeveloperName().get('SUI_Scoping').getRecordTypeId();
            
            //Build a set of Work Orders whose Comments need to recalculate their shares
            Set<Id> recalculateCommentShares = new Set<Id>();
            for(Id i : newWorkOrderMap.keyset()){
                //If Linked Contractor has changed, sharing needs to be recalculated
                if(newWorkOrderMap.get(i).SUI_Linked_Contractor__c != oldWorkOrderMap.get(i).SUI_Linked_Contractor__c){
                    recalculateCommentShares.add(i);
                    //If record type = Scoping then add ParentWorkOrder as well.
                    if(newWorkOrderMap.get(i).recordTypeId == scopingRecordTypeId && newWorkOrderMap.get(i).parentWorkOrderId != null) recalculateCommentShares.add(newWorkOrderMap.get(i).parentWorkOrderId);
                }
            }
            if(recalculateCommentShares.size() > 0) SUI_CommentSharingUtility.recalculate('WorkOrder',recalculateCommentshares);
        }
    }
    
    // BulkBefore method
    public override void bulkBefore() {
        
        //for integration user only
        if((profileNameCWO == GlobalConstants.PROFILE_INTEGRATION_USER)){       
            
            // Perform SOQL query to retrieve Roll-Up Summary fields
            rollUpFields = [SELECT Id, ReferenceTo, IsCalculated, DataType, QualifiedApiName 
                            FROM FieldDefinition 
                            WHERE EntityDefinition.QualifiedApiName = 'WorkOrder' 
                            AND (DataType LIKE 'Roll-Up Summary%')];
            String scopingrecordType = GlobalConstants.WORK_ORDER_RECORD_TYPE_SCOPING;
            for(Workorder wo: [SELECT Id, ParentWorkOrderId, SUI_Record_Type_developer_Name__c
                               FROM WorkOrder 
                               WHERE SUI_Record_Type_developer_Name__c =: scopingrecordType
                               AND ParentWorkOrderId IN :newWorkOrderList
                               AND ParentWorkOrderId != null
                              ])
            {
                woIdVsRelatedScopingWo.put(wo.ParentWorkOrderId, wo);
            }
        }
    }
    
    //andFinally method
    public override void andFinally() {}
    
    public void fieldUpdateValidationForIntegrationUser(WorkOrder newWorkOrder){
        // Check if trigger switch is enabled or disabled
        If(!SUI_Validation_Trigger_Switch__mdt.getInstance('SUI_WorkOrder_IntegrationUser_Validation').SUI_Enabled__c){
            return;
        }
        
        //Check if the workorder has a related Scoping WO
        WorkOrder oldWorkOrder = oldWorkOrderMap.get(newWorkOrder.Id);
        
        If(!woIdVsRelatedScopingWo.containsKey(newWorkOrder.Id)){
            return;
        } 
        
        if (newWorkOrder.Status == GlobalConstants.WORK_ORDER_STATUS_RAISED &&
            newWorkOrder.SUI_Skip_Validation__c == false && newWorkOrder.SUI_Issued_Date__c == null &&
            newWorkOrder.SUI_Record_Type_developer_Name__c != GlobalConstants.WORK_ORDER_RECORD_TYPE_SCOPING
           ){
               Map<String, Object> oldMap = oldWorkOrder.getPopulatedFieldsAsMap().clone();
               Map<String, Object> newMap = newWorkOrder.getPopulatedFieldsAsMap().clone(); 
               
               List<SUI_Editable_Fields_For_Integration_User__mdt> edfList = SUI_Editable_Fields_For_Integration_User__mdt.getAll().values();
               //Removing fields that shouldn't be compared
               For(SUI_Editable_Fields_For_Integration_User__mdt edf : edfList){
                   System.debug('edf.SUI_Field_API_Name__c:IN'+edf.SUI_Field_API_Name__c);
                   oldMap.remove(edf.SUI_Field_API_Name__c);
                   newMap.remove(edf.SUI_Field_API_Name__c);
               }
               
               List<String> rollUpFieldNames = new List<String>();
               
               // Iterate through the results and add the QualifiedApiName to the list
               for (FieldDefinition field : rollUpFields) {
                   rollUpFieldNames.add(field.QualifiedApiName);
               }
               
               // Remove roll-up summary fields from the oldMap and newMap
               for (String fieldName : rollUpFieldNames) {
                   oldMap.remove(fieldName);
                   newMap.remove(fieldName);
               }
               //Removing Formula fields from JSON as it might change with respect to above fields 
               Map<String, Schema.SObjectType> globalDescribe = Schema.getGlobalDescribe();
               Schema.SObjectType objectType = globalDescribe.get(GlobalConstants.WORKORDER_OBJECT);
               Map<String, Schema.SObjectField> fieldMap = objectType.getDescribe().fields.getMap();
               
               List<String> formulaFieldNames = new List<String>();
               for (String fieldName : fieldMap.keySet()) {
                   
                   Schema.DescribeFieldResult field = fieldMap.get(fieldName).getDescribe();
                   
                   if (field.getCalculatedFormula() != null) {
                       oldMap.remove(field.getName());
                       newMap.remove(field.getName());
                   }
                   
               }            
               
               // Check if old and new records have different values except formula, rollup fields & removed fields
               If(!oldMap.equals(newMap)){
                   newWorkOrder.addError('Cannot update the Work Order Details');
               }
           }
    }
}