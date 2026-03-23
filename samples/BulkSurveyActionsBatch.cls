public class BulkSurveyActionsBatch implements Database.Batchable<sObject> {

  String action;
  List<Id> surveyIds;
  String rejectedReason;
  Id loggedInUserId= UserInfo.getUserId(); 

    //Constructor
    public BulkSurveyActionsBatch(List<Id> surveyIds, String action, Integer chunkSize, string rejectedReason){

       this.action = action;
       this.surveyIds=surveyIds;
       this.rejectedReason=rejectedReason;
       //System.debug('Passed Action '+action);
       //System.debug('Passed List of Selected Surveys '+surveyIds);
}

   //Start Method
   public Database.QueryLocator start(Database.BatchableContext bc) {

      //Query all survey records which are selected for bulk action from flow
      return Database.getQueryLocator([SELECT Id, Status__c, Inspection_Schedule_Approved__c, Inspection_Schedule_Reject_Reason__c, OwnerId FROM Survey__c
                                        WHERE Id IN: surveyIds
                                        LIMIT 50000]);
}

   //Update statuses of surveys queried in start method.
   public void execute(Database.BatchableContext bc, List<Survey__c> surveys){

      if(action==GlobalConstants.APPROVED){
          For(Survey__c survey : surveys){
          //Update Surveys status to Assigned
                survey.Status__c = GlobalConstants.SURVEY_STATUS_ASSIGNED;
                survey.OwnerId= loggedInUserId;
                survey.Inspection_Schedule_Approved__c=true;
        }
    }

     else if(action==GlobalConstants.REJECTED){

         For(Survey__c survey : surveys){
         //Update Survey status to  inspection schedule rejected
              survey.Status__c = GlobalConstants.SURVEY_STATUS_INSPECTION_SEHEDULE_REJECTED;  
              survey.Inspection_Schedule_Reject_Reason__c=rejectedReason;
              survey.OwnerId= loggedInUserId;
        }
    }

        // Update surveys
        database.update(surveys,false);
    }

public void finish(Database.BatchableContext bc){

}
}