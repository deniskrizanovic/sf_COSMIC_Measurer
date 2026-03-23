/**
 * Created by dkrizanovic on 22/10/2024.
 */

public with sharing class cfp_getDataMovements {

    @AuraEnabled
    public static List<cfp_Data_Movements__c> getSteps(Id fpId) {
        List<cfp_Data_Movements__c> allSteps = [SELECT Name, cfp_order__c, cfp_movementtype__c, cfp_is_API_Call__c, cfp_FunctionalProcess__r.Name FROM cfp_Data_Movements__c WHERE cfp_FunctionalProcess__c = :fpId ORDER BY cfp_order__c ASC];


        return allSteps;
    }
}