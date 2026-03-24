
public class SUI_RunValidationBatch implements Database.Batchable<SObject>, Database.Stateful{
    
    private String soqlQuery;
    private Id programId;
    private Boolean programValidateStatus = FALSE; //added default value, for zero records
    
    public SUI_RunValidationBatch(String query, Id programId) {
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
          woList[0].SUI_Prog_Program__r.SUI_Is_Run_Validation_In_Progress__c = TRUE;
          SUI_RunValidationHelper.init(woList);
            
            for(WorkOrder woRecord : woList){ 
                SUI_RunValidationHelper.resetValidationOutcomes(woRecord);
                SUI_RunValidationHelper.validateFacility(woRecord);
                if(woRecord.SUI_Prog_Program__r.SUI_Scoping_Required__c){
                    SUI_RunValidationHelper.validateScopingSoRQuantity(woRecord);
                    SUI_RunValidationHelper.validateScopingSoRs(woRecord, 'SUI_Prog_Scoping_SORs__c');
                    SUI_RunValidationHelper.validateQuantity(woRecord, 'SUI_Prog_Scoping_Quantity__c');
                    SUI_RunValidationHelper.validateWorkPriority(woRecord);
                    SUI_RunValidationHelper.validateLocationType(woRecord);
                    SUI_RunValidationHelper.validateStartEndDate(woRecord); 
                    SUI_RunValidationHelper.updateForSuccess(woRecord);
                    }else{
                    //Program Validation with SSTref value 
                    if(woRecord.SUI_Prog_SSTRef__c!=null){
                      Boolean invalid =SUI_RunValidationHelper.validateSSTRef(woRecord);
                      if(!(invalid==TRUE)){
                        SUI_RunValidationHelper.validateDefectcode(woRecord);
                        SUI_RunValidationHelper.validateDefectLocation(woRecord);
                        SUI_RunValidationHelper.validateDefectQuantity(woRecord);
                        SUI_RunValidationHelper.validateSoRQttyLocType(woRecord);
                        SUI_RunValidationHelper.validateDefectWorkClassification(woRecord);
                        SUI_RunValidationHelper.validateWorkPriority(woRecord);
                        SUI_RunValidationHelper.validateStartEndDate(woRecord); 
                      }    
                    }
                    ////Program Validation When SOR value are available with Work Order
                    else{  
                      SUI_RunValidationHelper.validateSoRQttyLocType(woRecord); 
                      SUI_RunValidationHelper.validateSoRs(woRecord, 'SUI_Prog_SORs__c');
                      SUI_RunValidationHelper.validateLocationType(woRecord);
                      SUI_RunValidationHelper.validateQuantity(woRecord, 'SUI_Prog_Quantity__c');
                      SUI_RunValidationHelper.validateWorkClassification(woRecord);
                      SUI_RunValidationHelper.validateWorkPriority(woRecord);
                      SUI_RunValidationHelper.validateStartEndDate(woRecord); 
                      SUI_RunValidationHelper.updateForSuccess(woRecord);
                   } 
                } 
                
                if(woRecord.SUI_Prog_Val_Outcome__c == 'Error'){
                    programValidateStatus = FALSE;
                }
              }
           
        }
        //Update woList
        if(woList != NULL && woList.size() > 0){
           try{
                update woList;
           } catch(Exception e){
             ApplicationLogHandler.addLog('SUI_RunValidationBatch','execute',e);
             ApplicationLogHandler.saveLog();
           }
        }
        for(WorkOrder woRecord : woList){ 
          if(woRecord.SUI_Prog_SSTRef__c!=null || String.isNotBlank(woRecord.SUI_Prog_SSTRef__c)){
              SUI_RunValidationHelper.updateForSuccess(woRecord);
          }
        }  
        if(woList != NULL && woList.size() > 0){
           try{
                update woList;
           } catch(Exception e){
             ApplicationLogHandler.addLog('SUI_RunValidationBatch','execute',e);
             ApplicationLogHandler.saveLog();
           }
        }
      
    }
    
    public void finish(Database.BatchableContext bc){
      
        //Update the SUI_Is_Run_Validation_In_Progress__c field to False for the Program record 
        SUI_Program__c prgm = new SUI_Program__c(Id = programId, SUI_Is_Run_Validation_In_Progress__c = FALSE, SUI_Status__c = 'Validation Completed' );

        if(programValidateStatus){
            prgm.SUI_Jobs_Successfully_Validated__c = TRUE;
        }else{
            prgm.SUI_Jobs_Successfully_Validated__c = FALSE;
        }
        
        try{ 
             update prgm;
           } catch(Exception e){
             ApplicationLogHandler.addLog('SUI_RunValidationBatch','finish',e);
             ApplicationLogHandler.saveLog();
           }
    }
}