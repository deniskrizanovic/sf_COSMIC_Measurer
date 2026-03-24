

public class InvokeRunValidation {

     public static String generateQueryforId(Id programId){
        return 'SELECT Id, RecordType.Name, Prog_Facility__c, Prog_Val_Message__c, Prog_Val_Outcome__c, ' +
               'Prog_LocationType__c,Work_Program__c,Prog_SSTRef__c, Prog_Priority__c, Prog_Quantity__c, Prog_Work_Classification__c,' +
               'Prog_SORs__c, Total_Incl_GST__c, Prog_Start_Date__c, Prog_End_Date__c, Prog_Program__r.Is_Run_Validation_In_Progress__c, ' + 
               'Prog_Program__r.Scoping_Required__c, Prog_Program__r.Status__c, Prog_Scoping_Quantity__c, Prog_Scoping_SORs__c ' +
               'FROM WorkOrder WHERE RecordType.DeveloperName = \'Jobs\' ' +
               'AND Prog_Val_Outcome__c != \'Success\' '  +
               'AND Prog_Program__c = :programId ' +
               'AND Prog_Program__r.Is_Run_Validation_In_Progress__c = FALSE ';
   }

    /**
     * @description           This Method is used to Invoke the RunValidationBatch
     *                        Method get invoked from SUI Program - After Insert and Update
     * @param  programIds     This is required to retrieve the Work Orders data 
     * @return                       
    */ 
   
   @InvocableMethod
   public static void callRunValidationBatch(List<Id> programIds){
       Id programId = programIds.isEmpty() ? null : programIds[0];
       if(programId != null) {
           String query = generateQueryforId(programId);
           Id jobId = Database.executeBatch(new RunValidationBatch(query, programId));
       }
   }
}