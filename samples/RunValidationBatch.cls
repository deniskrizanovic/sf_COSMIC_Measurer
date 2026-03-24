
public class RunValidationBatch implements Database.Batchable<SObject>, Database.Stateful{
    
    private String soqlQuery;
    private Id programId;
    private Boolean programValidateStatus = FALSE; //added default value, for zero records
    
    public RunValidationBatch(String query, Id programId) {
        this.soqlQuery = query;
        this.programId = programId;
    }
    
    public Database.QueryLocator start(Database.BatchableContext bc){
        return Database.getQueryLocator(soqlQuery);
    }
    
    public void execute(Database.BatchableContext bc, List<WorkOrder> woList){
        // process each batch of records
        programValidateStatus = TRUE;
        
        if( woList!=NULL && !woList.isEmpty() ){
          woList[0].Prog_Program__r.Is_Run_Validation_In_Progress__c = TRUE;
          RunValidationHelper.init(woList);
            
            for(WorkOrder woRecord : woList){ 
                RunValidationHelper.resetValidationOutcomes(woRecord);
                RunValidationHelper.validateFacility(woRecord);
                if(woRecord.Prog_Program__r.Scoping_Required__c){
                    RunValidationHelper.validateScopingSoRQuantity(woRecord);
                    RunValidationHelper.validateScopingSoRs(woRecord, 'Prog_Scoping_SORs__c');
                    RunValidationHelper.validateQuantity(woRecord, 'Prog_Scoping_Quantity__c');
                    RunValidationHelper.validateWorkPriority(woRecord);
                    RunValidationHelper.validateLocationType(woRecord);
                    RunValidationHelper.validateStartEndDate(woRecord); 
                    RunValidationHelper.updateForSuccess(woRecord);
                    }else{
                    //Program Validation with SSTref value 
                    if(woRecord.Prog_SSTRef__c!=null){
                      Boolean invalid =RunValidationHelper.validateSSTRef(woRecord);
                      if(!(invalid==TRUE)){
                        RunValidationHelper.validateDefectcode(woRecord);
                        RunValidationHelper.validateDefectLocation(woRecord);
                        RunValidationHelper.validateDefectQuantity(woRecord);
                        RunValidationHelper.validateSoRQttyLocType(woRecord);
                        RunValidationHelper.validateDefectWorkClassification(woRecord);
                        RunValidationHelper.validateWorkPriority(woRecord);
                        RunValidationHelper.validateStartEndDate(woRecord); 
                      }    
                    }
                    ////Program Validation When SOR value are available with Work Order
                    else{  
                      RunValidationHelper.validateSoRQttyLocType(woRecord); 
                      RunValidationHelper.validateSoRs(woRecord, 'Prog_SORs__c');
                      RunValidationHelper.validateLocationType(woRecord);
                      RunValidationHelper.validateQuantity(woRecord, 'Prog_Quantity__c');
                      RunValidationHelper.validateWorkClassification(woRecord);
                      RunValidationHelper.validateWorkPriority(woRecord);
                      RunValidationHelper.validateStartEndDate(woRecord); 
                      RunValidationHelper.updateForSuccess(woRecord);
                   } 
                } 
                
                if(woRecord.Prog_Val_Outcome__c == 'Error'){
                    programValidateStatus = FALSE;
                }
              }
           
        }
        //Update woList
        if(woList != NULL && woList.size() > 0){
           try{
                update woList;
           } catch(Exception e){
             ApplicationLogHandler.addLog('RunValidationBatch','execute',e);
             ApplicationLogHandler.saveLog();
           }
        }
        for(WorkOrder woRecord : woList){ 
          if(woRecord.Prog_SSTRef__c!=null || String.isNotBlank(woRecord.Prog_SSTRef__c)){
              RunValidationHelper.updateForSuccess(woRecord);
          }
        }  
        if(woList != NULL && woList.size() > 0){
           try{
                update woList;
           } catch(Exception e){
             ApplicationLogHandler.addLog('RunValidationBatch','execute',e);
             ApplicationLogHandler.saveLog();
           }
        }
      
    }
    
    public void finish(Database.BatchableContext bc){
      
        //Update the Is_Run_Validation_In_Progress__c field to False for the Program record 
        Program__c prgm = new Program__c(Id = programId, Is_Run_Validation_In_Progress__c = FALSE, Status__c = 'Validation Completed' );

        if(programValidateStatus){
            prgm.Jobs_Successfully_Validated__c = TRUE;
        }else{
            prgm.Jobs_Successfully_Validated__c = FALSE;
        }
        
        try{ 
             update prgm;
           } catch(Exception e){
             ApplicationLogHandler.addLog('RunValidationBatch','finish',e);
             ApplicationLogHandler.saveLog();
           }
    }
}