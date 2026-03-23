/**
* ─────────────────────────────────────────────────────────────────────────────────────────────────┐
* This class contains logic to create sObject Share records to provide record access to contractor
  portal users.
* ──────────────────────────────────────────────────────────────────────────────────────────────────
* @author         Pradeep Gupta
* @modifiedBy     
* @version        1.0
* @created        16-02-2024
* @modified       YYYY-MM-DD
* @testClass      SUI_ManageContrctAreaRelatdObjShare_Test
* ──────────────────────────────────────────────────────────────────────────────────────────────────
* @changes
* ─────────────────────────────────────────────────────────────────────────────────────────────────┘
*/

public with sharing class SUI_ManageContractAreaRelatedObjectShare {

    //This method takes the required parameters to create sObject_Share records
    @InvocableMethod
    Public static void createSobjectShareRecord(List<SobjectShareParametersWrapper> sObjectShareParams){
        String jsonString = JSON.serialize(sObjectShareParams);
        insertShareRecords(jsonString);
    }

    //Inserting sObjectShare records inside Future method to avoid mixed DML
    @future
    private static void insertShareRecords(String jsonParameter){
        List<SobjectShareParametersWrapper> sObjectShareParams = (List<SobjectShareParametersWrapper>)JSON.deserialize(jsonParameter, List<SobjectShareParametersWrapper>.class);
        List<sObject> objectShareRecordsToCreate = new List<sObject>();
        String shareSObjectName;

        //Check if incoming sObject is standard or custom and append Share accordingly
        if(Schema.getGlobalDescribe().get(String.valueOf(sObjectShareParams[0].parentId.getSObjectType())).getDescribe().isCustom()){
            shareSObjectName = sObjectShareParams[0].objectAPIName.replace('__c','__Share');
        }
        else{
            shareSObjectName = sObjectShareParams[0].objectAPIName + 'Share';
        }
		
        Schema.SObjectType sObjectShareType = Schema.getGlobalDescribe().get(shareSObjectName);

        //Create sObject Share record instance and add into list
        for(SobjectShareParametersWrapper objectDetails : sObjectShareParams){           
            SObject sObjectShareRecord = sObjectShareType.newSObject();
            if(objectDetails.objectAPIName == GlobalConstants.OBJECT_ACCOUNT_NAME){
                sObjectShareRecord.put('AccountId', objectDetails.parentId);
            	sObjectShareRecord.put('UserOrGroupId', objectDetails.userOrGroupId);
            	sObjectShareRecord.put('AccountAccessLevel', objectDetails.accessLevel);
                sObjectShareRecord.put('OpportunityAccessLevel', 'None');
            	sObjectShareRecord.put('RowCause', 'Manual');
            }
            else{
                sObjectShareRecord.put('ParentId', objectDetails.parentId);
            	sObjectShareRecord.put('UserOrGroupId', objectDetails.userOrGroupId);
            	sObjectShareRecord.put('AccessLevel', objectDetails.accessLevel);
            	sObjectShareRecord.put('RowCause', 'Manual');
            }
            
            objectShareRecordsToCreate.add(sObjectShareRecord);
        }
        
        //Insert sObject Share records
        try{
            insert objectShareRecordsToCreate;
        }catch(exception ex){
            ApplicationLogHandler.addLog('SUI_ManageContractAreaRelatedObjectShare','craeteSobjectShareRecord',ex);
            ApplicationLogHandler.saveLog();
        }
    }
    //Wrapper class to manage incoming sObject share parameters
    public class SobjectShareParametersWrapper{
        @invocablevariable(description='If any prefix is there, It should be in API Name' required=true) public String objectAPIName;
        @invocablevariable(required=true) public String accessLevel;
        @invocablevariable(required=true) public Id parentId;
        @invocablevariable(required=true) public Id userOrGroupId;
    }
}