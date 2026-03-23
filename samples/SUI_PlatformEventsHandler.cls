/**
* ─────────────────────────────────────────────────────────────────────────────────────────────────┐
* This class contains invocable methods responsible for publishing platform event
  and returns back the response success/failure with the actual details
* ──────────────────────────────────────────────────────────────────────────────────────────────────
* @author         Geetesh Bhalerao (geetesh.bhalerao@sauceconsulting.com.au)
* @modifiedBy     
* @version        1.0
* @created        2023-12-18
* @modified       YYYY-MM-DD
* ──────────────────────────────────────────────────────────────────────────────────────────────────
* @changes
* vX.X            name@sauceconsulting.com.au
* YYYY-MM-DD      

* ─────────────────────────────────────────────────────────────────────────────────────────────────┘
*/
public without sharing class SUI_PlatformEventsHandler {
  
    /* 
    @description: this method accepts platform event name and related record details and publishes those and returns back outcomes
    @param requestList list of wrapper objects containing name of platform events and related record details
    */
    @InvocableMethod(label='Publish Dynamic Platform Events' 
                     description='call this method to dynamically publish platform events')
    public static void execute (List<Request> requestList) {

            handleEvents(JSON.serialize(requestList));
        
    }
    
    //get platform event metadata information
    public static SUI_Platform_Event__mdt getPlatformEventMetadataInfo(String platformEventMetadataName){
        return SUI_Platform_Event__mdt.getInstance(platformEventMetadataName);
    }

   // Check if platform event use case is disabled
    public static Boolean checkPlatformEventUseCaseDisabled(String platformEventMetadataName){
        return Test.isRunningTest() ? false : !SUI_Platform_Event_Use_Case__mdt.getInstance(platformEventMetadataName).SUI_Enabled__c;
    }
    
    //check if platform event framework switch is on or off
    public static Boolean isFrameworkDisabled(){
        return Test.isRunningTest() ? false : !SUI_Integration_Framework_Switch__mdt.getInstance('SUI_Platform_Event_Framework').SUI_Enabled__c;
    }
    
    public static void handleEvents(String requestString){
         
         List<Request> requestList = (List<Request>)JSON.deserialize(requestString, List<Request>.class); 

         try{
            
            //if framework switch is off, do not execute
            if(isFrameworkDisabled()){ return; }
                        
            //initialise variables
            List<String> eventPayloads = new List<String>();
            List<String> platformEventNames = new List<String>();
            List<String> relatedRecordIds = new List<String>();
            SObject eventRec;
            Map<String, Object> eventPayload;
            List<SObject> eventList = new List<SObject>();
            List<Database.SaveResult> results;
           	SUI_Platform_Event__mdt metadataInfo;
            SUI_Platform_Event_Use_Case__mdt useCaseMetadataInfo;
           
           //get platform event name list and related record ids
            for(Request req : requestList){
                metadataInfo = getPlatformEventMetadataInfo(req.platformEventMetadataName);

                //if platform event is disabled, do not continue;
                if(metadataInfo == null || metadataInfo.SUI_Enabled__c == false){ continue; }

                if(checkPlatformEventUseCaseDisabled(req.platformEventMetadataUseCaseName) == true){ continue; }

                req.platformEventName = metadataInfo.SUI_Platform_Event_Name__c;
                platformEventNames.add(metadataInfo.SUI_Platform_Event_Name__c);
                relatedRecordIds.add(req.relatedRecordId);
                            } 

            //use the metadata handler class to get configuration metadata for the platform events
            SUI_PlatformEventsMetadataHandler metadataHandler = new SUI_PlatformEventsMetadataHandler(platformEventNames);
                       
            //query the related record information based on the metadata configurations
            //so a single query is formed with all fields which are setup in the custom metadata of platform event configurations
            //and the fields are queried with a single query
            metadataHandler.queryRelatedRecords(relatedRecordIds);

            for(Request req : requestList){
                
                if(String.isBlank(req.platformEventName)){ continue; }
                
                //map the sobject details as per the custom metadata setup of this platform event configuration
                eventRec = metadataHandler.getPayloadforNewPublish(req.platformEventName, req.platformEventMetadataName, req.relatedRecordId);

                //convert sobject to map to save payload in JSON format
                eventPayload = SUI_PlatformEventsHandlerUtility.convertSObjecttoMap(eventRec);
                //add extra paramater of unique external identifier
                eventPayload.put('uniqueExternalId', '<<unique_ID>>');

                //generate event payload and put it as point in time information on the platform event log record
                eventPayloads.add(JSON.serialize(eventPayload));

                eventList.add(eventRec);  
            }  

            
            // Call method to publish events
            results = EventBus.publish(eventList);

            for(Integer i = 0 ; i < results.size(); i++){
                
                String payload = eventPayloads[i];
                String operationId = EventBus.getOperationId(results[i]);
                if(!String.isBlank(payload) && !String.isBlank(operationId)){
                    payload = payload.replace('<<unique_ID>>', operationId);
                }
                
                //in case of successful publish operation, create a platform event log with success stage
                if (results[i].isSuccess()) {
                    SUI_PlatformEventLogsHandler.addLog(requestList[i].platformEventName, 
                                                        operationId, 
                                                        requestList[i].relatedRecordId, 
                                                        payload,
                                                        SUI_PlatformEventFrameworkConstants.PLATFORM_EVENT_LOG_STATUS_PUBLISHED, 
                                                        null, System.now(), 0
                    );
                } 
                //in case of failure, create a platform event log for failure
                else {
                    String errorMessages = '';
                    
                    //join all the error message and form a single string
                    for(Database.Error err : results[i].getErrors()) {
                        errorMessages += err.getStatusCode() + '-' + err.getMessage() + ';';
                    }
                    
                    SUI_PlatformEventLogsHandler.addLog(requestList[i].platformEventName, 
                                                        getUniqueIdentifier(requestList[i].relatedRecordId), 
                                                        requestList[i].relatedRecordId, 
                                                        eventPayloads[i],
                                                        SUI_PlatformEventFrameworkConstants.PLATFORM_EVENT_LOG_STATUS_FAILED,
                                                        errorMessages, System.now(), 0
                                                        );
                }   
            }
            

        }
        
        //in case of apex exception, store it in "Error Messages" field of platform event log record
        catch(Exception e){
            for(Request req : requestList){
                SUI_PlatformEventLogsHandler.addLog(req.platformEventName, 
                                                    getUniqueIdentifier(req.relatedRecordId), req.relatedRecordId, null,
                                                    SUI_PlatformEventFrameworkConstants.PLATFORM_EVENT_LOG_STATUS_FAILED, 
                                                    e.getStackTraceString() + ' : ' + e.getMessage(), System.now(), 0
                                                    );
            }
        } 
        

        //update or insert the platform event log records
        SUI_PlatformEventLogsHandler.upsertLogs();
    } 
    
    //incoming request to the invocable method
    public class Request {
        @InvocableVariable(label='Platform Event Metadata Name' description='API Name of the platform event custom metadata' required=true)
        public String platformEventMetadataName;
        
        @InvocableVariable(label='Related Record Id' description='Id of related record' required=true)
        public Id relatedRecordId; 
        
        @InvocableVariable(label='Platform Event Use Case Metadata Name' description='API Name of the platform event custom metadata of use case' required=true)
        public String platformEventMetadataUseCaseName;
        
        public String platformEventName; //local variable populated in this apex
    }
    
    public static String getUniqueIdentifier(Id relatedRecordId){
        return relatedRecordId + '' + DateTime.now().getTime();
    }
          

}