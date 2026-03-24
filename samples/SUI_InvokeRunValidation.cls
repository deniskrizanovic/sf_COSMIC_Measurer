

public class SUI_InvokeRunValidation {

     public static String generateQueryforId(Id programId){
        return 'SELECT Id, RecordType.Name, SUI_Prog_Facility__c, SUI_Prog_Val_Message__c, SUI_Prog_Val_Outcome__c, ' +
               'SUI_Prog_LocationType__c,SUI_Work_Program__c,SUI_Prog_SSTRef__c, SUI_Prog_Priority__c, SUI_Prog_Quantity__c, SUI_Prog_Work_Classification__c,' +
               'SUI_Prog_SORs__c, SUI_Total_Incl_GST__c, SUI_Prog_Start_Date__c, SUI_Prog_End_Date__c, SUI_Prog_Program__r.SUI_Is_Run_Validation_In_Progress__c, ' + 
               'SUI_Prog_Program__r.SUI_Scoping_Required__c, SUI_Prog_Program__r.SUI_Status__c, SUI_Prog_Scoping_Quantity__c, SUI_Prog_Scoping_SORs__c ' +
               'FROM WorkOrder WHERE RecordType.DeveloperName = \'SUI_Jobs\' ' +
               'AND SUI_Prog_Val_Outcome__c != \'Success\' '  +
               'AND SUI_Prog_Program__c = :programId ' +
               'AND SUI_Prog_Program__r.SUI_Is_Run_Validation_In_Progress__c = FALSE ';
   }

    /**
     * @description           This Method is used to Invoke the SUI_RunValidationBatch
     *                        Method get invoked from SUI Program - After Insert and Update
     * @param  programIds     This is required to retrieve the Work Orders data 
     * @return                       
    */ 
   
   @InvocableMethod
   public static void callRunValidationBatch(List<Id> programIds){
       Id programId = programIds.isEmpty() ? null : programIds[0];
       if(programId != null) {
           String query = generateQueryforId(programId);
           Id jobId = Database.executeBatch(new SUI_RunValidationBatch(query, programId));
       }
   }
}