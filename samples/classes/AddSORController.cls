/**
* ─────────────────────────────────────────────────────────────────────────────────────────────────┐
* This is the controller class for AddSor lwc component
* ──────────────────────────────────────────────────────────────────────────────────────────────────
* @author         Swapnil Barad (swapnil.barad@sauceconsulting.com.au)
* @modifiedBy     
* @version        1.0
* @created        2023-18-07
* @modified       YYYY-MM-DD
* @testClass      AddSORController_Test
* ──────────────────────────────────────────────────────────────────────────────────────────────────
* @changes
* v1.0            swapnil.barad@sauceconsulting.com.au
* 2023-06-15      This is initial version of the implemantation. This class is used in AddSOR lwc
                  component.
                  
  v2.0            pradeep.gupta@sauceconsulting.com.au
  2024-02-21      Added method to fetch SUI_SOR_With_Create_RIIS_Survey_Flag__mdt records that contains 
                  Service Item Code with Create RIIS Survey flag. This method called inside save and 
                  saveSupplementaryWoli methods
                  
  v2.1            pradeep.gupta@sauceconsulting.com.au
  2024-04-03      Removed everything added under v2.0

  v2.2            gaurav.tanwar@dcj.nsw.gov.au, satya.singh@homes.nsw.gov.au
  2025-09-01      Added two new methods fetchAllSORList and fetchSOLRList for additional filters and search.
* ─────────────────────────────────────────────────────────────────────────────────────────────────┘
*/
public class AddSORController {

    /**   
    * Custom exception class
    */
   public class CustomException extends Exception {}
   
   /**
    * @description            This method is responsible to fetch all  Service Catalouge for the given component, component 
    *                         type and sub componant. It will also include already added work order line item for that work order.
                              this method implemented for MA-51045
    * @param  workOrderId     This is work order Id required to check which service catalouge already added under this work order.
    * @param  componentId     Filter value for - component 
    * @param  componentTypeId Filter value for - component type 
    * @param  subComponentId  Filter value for - sub component 
    * @param  contractType    Filter value for - contract type
    * @param  activityType    Filter value for - contract type
    * @param  financeCat      Filter value for - financeCat
    * @param  tradeName       Filter value for - tradeName
    * @param  shortDescription     Filter value for - shortDescription
    * @return                 return description
    */ 
    @AuraEnabled 
    public static list<serviceCatalougeWrapper> fetchSOLRsList(String workOrderId, String componentId, String componentTypeId, 
                                                            String subComponentId, String contractType, String activityType,
                                                            String financeCat,String tradeName, String shortDescription) {
             
        WorkOrder currentWO = [SELECT Id, RecordTypeId,SUI_Record_Type_developer_Name__c,SUI_Work_Program__c,SUI_Prog_Work_Classification__c,SUI_Work_Priority__r.name FROM WorkOrder Where ID =: workOrderId];    
        String scopingContract =GlobalConstants.WORK_ORDER_CONTRACT_TYPE_SCOPING;
        
        //Create a query 
        String query = '';
        String scopingComponent= GlobalConstants.SERVICE_CATALOGUE_COMPONENT_SCOPING;
        system.debug(currentWO.SUI_Work_Priority__r.name);
        
        if(currentWo.SUI_Record_Type_developer_Name__c != GlobalConstants.WORK_ORDER_RECORD_TYPE_SCOPING){
        query = 'SELECT Id,Name,SUI_Activity_Type__c,SUI_Trade_Name__c,SUI_Service_Item_Code__c,SUI_Service_Item_Long_Description__c,SUI_Service_Item_Short_Description__c,SUI_Component__c,SUI_Component__r.Name,SUI_Component_Type__c,SUI_Finance_Category__c,SUI_Finance_Category_Threshold_Quantity__c,SUI_Component_Type__r.Name,SUI_Sub_Component__r.Name,SUI_Sub_Component__c'+ 
                        ' FROM SUI_Service_Catalogue__c'+  
                        ' WHERE SUI_Contract_Type__c=:contractType AND SUI_Work_Classification__c includes (\''+currentWO.SUI_Prog_Work_Classification__c+'\') AND SUI_Work_Program__c  includes (\''+currentWO.SUI_Work_Program__c+'\') AND SUI_Work_Priority__c includes (\''+currentWO.SUI_Work_Priority__r.name+'\')';
        }
        else {
                query = 'SELECT Id,Name,SUI_Activity_Type__c,SUI_Trade_Name__c,SUI_Service_Item_Code__c,SUI_Service_Item_Long_Description__c,SUI_Service_Item_Short_Description__c,SUI_Component__c,SUI_Component__r.Name,SUI_Component_Type__c,SUI_Finance_Category__c,SUI_Finance_Category_Threshold_Quantity__c,SUI_Component_Type__r.Name,SUI_Sub_Component__r.Name,SUI_Sub_Component__c'+ 
                            ' FROM SUI_Service_Catalogue__c'+  
                            ' WHERE SUI_Contract_Type__c=:contractType AND SUI_Component__r.Name=:scopingComponent AND SUI_Work_Classification__c includes (\''+currentWO.SUI_Prog_Work_Classification__c+'\') AND SUI_Work_Program__c  includes (\''+currentWO.SUI_Work_Program__c+'\') AND SUI_Work_Priority__c includes (\''+currentWO.SUI_Work_Priority__r.name+'\')';
        }
        query += prepareSOQL(componentId, componentTypeId, subComponentId, contractType, activityType,
                                financeCat, tradeName, shortDescription);
        System.debug('query='+query);
        //Query the service catalouge records
        List<SUI_Service_Catalogue__c> serviceCatalougeList = database.query(query);
        system.debug('serviceCatalougeList='+serviceCatalougeList);
        List<serviceCatalougeWrapper> serviceCatalougeWrapperList = new List<serviceCatalougeWrapper>();
        for(SUI_Service_Catalogue__c catalogue : serviceCatalougeList){
            serviceCatalougeWrapperList.add(new serviceCatalougeWrapper(catalogue,null,null));
        }
        system.debug('serviceCatalougeWrapperList='+serviceCatalougeWrapperList);
        return serviceCatalougeWrapperList;
    }

    private static String prepareSOQL(String componentId, String componentTypeId, String subComponentId, String contractType, String activityType,
                                     String financeCat,String tradeName, String shortDescription) {
        String query = ' ';
        if(String.isNotBlank(componentId)){
            query += ' AND SUI_Component__c =:componentId ';
        }
        if(String.isNotBlank(componentTypeId)){
            query += ' AND SUI_Component_Type__c =:componentTypeId ';
        }
        if(String.isNotBlank(subComponentId)){
            query += ' AND SUI_Sub_Component__c =:subComponentId ';
        }
        if(String.isNotBlank(activityType)){
            query += '  AND SUI_Activity_Type__c   =:activityType ';
        }
        if(String.isNotBlank(financeCat)) {
            query += '  AND SUI_Finance_Category__c   =:financeCat ';
        }
        if(String.isNotBlank(tradeName)){
            // Filter by Trade Name using LIKE
            query += ' AND SUI_Trade_Name__c LIKE \'%' + String.escapeSingleQuotes(tradeName) + '%\' ';
            System.debug('Filtering by Trade Name (LIKE): ' + tradeName);
        }

        if(String.isNotBlank(shortDescription)){
            // Filter by Short Description using LIKE
            query += ' AND SUI_Service_Item_Short_Description__c LIKE \'%' + String.escapeSingleQuotes(shortDescription) + '%\' ';
            System.debug('Filtering by Short Description (LIKE): ' + shortDescription);
        }
        return query;
    }


   
   /**
    * @description            This method is responsible to fetch all the active Service Catalouge for the given component, component 
    *                         type and sub componant. It will also exclude already added work order line item for that work order. 
    * @param  workOrderId     This is work order Id required to check which service catalouge already added under this work order.
    * @param  componentId     Filter value for - component 
    * @param  componentTypeId Filter value for - component type 
    * @param  subComponentId  Filter value for - sub component 
    * @param  contractType    Filter value for - contract type
    * @return                 return description
    */ 
   
   @AuraEnabled 
   public static list<serviceCatalougeWrapper> fetchSOLRList(String workOrderId, String componentId, String componentTypeId, String subComponentId, String contractType){
             
       WorkOrder currentWO = [SELECT Id, RecordTypeId,SUI_Record_Type_developer_Name__c,SUI_Work_Program__c,SUI_Prog_Work_Classification__c,SUI_Work_Priority__r.name FROM WorkOrder Where ID =: workOrderId];    
       String scopingContract =GlobalConstants.WORK_ORDER_CONTRACT_TYPE_SCOPING;
      
       //Create a query 
       String query = '';
       String scopingComponent= GlobalConstants.SERVICE_CATALOGUE_COMPONENT_SCOPING;
       system.debug(currentWO.SUI_Work_Priority__r.name);
      
       if(currentWo.SUI_Record_Type_developer_Name__c != GlobalConstants.WORK_ORDER_RECORD_TYPE_SCOPING){
        query = 'SELECT Id,Name,SUI_Activity_Type__c,SUI_Trade_Name__c,SUI_Service_Item_Code__c,SUI_Service_Item_Long_Description__c,SUI_Service_Item_Short_Description__c,SUI_Component__c,SUI_Component__r.Name,SUI_Component_Type__c,SUI_Finance_Category__c,SUI_Finance_Category_Threshold_Quantity__c,SUI_Component_Type__r.Name,SUI_Sub_Component__r.Name,SUI_Sub_Component__c'+ 
                          ' FROM SUI_Service_Catalogue__c'+  
                          ' WHERE SUI_Contract_Type__c=:contractType AND SUI_Work_Classification__c includes (\''+currentWO.SUI_Prog_Work_Classification__c+'\') AND SUI_Work_Program__c  includes (\''+currentWO.SUI_Work_Program__c+'\') AND SUI_Work_Priority__c includes (\''+currentWO.SUI_Work_Priority__r.name+'\')';
              if(componentId != '' && componentId != null){
               query += ' AND SUI_Component__c =:componentId ';
           }

           if(componentTypeId != ''  && componentTypeId != null){
               query += ' AND SUI_Component_Type__c =:componentTypeId ';
           }

           if(subComponentId != ''  && subComponentId != null){
               query += ' AND SUI_Sub_Component__c =:subComponentId ';
           }
          
       }else{
             query = 'SELECT Id,Name,SUI_Activity_Type__c,SUI_Trade_Name__c,SUI_Service_Item_Code__c,SUI_Service_Item_Long_Description__c,SUI_Service_Item_Short_Description__c,SUI_Component__c,SUI_Component__r.Name,SUI_Component_Type__c,SUI_Finance_Category__c,SUI_Finance_Category_Threshold_Quantity__c,SUI_Component_Type__r.Name,SUI_Sub_Component__r.Name,SUI_Sub_Component__c'+ 
                           ' FROM SUI_Service_Catalogue__c'+  
                           ' WHERE SUI_Contract_Type__c=:contractType AND SUI_Component__r.Name=:scopingComponent AND SUI_Work_Classification__c includes (\''+currentWO.SUI_Prog_Work_Classification__c+'\') AND SUI_Work_Program__c  includes (\''+currentWO.SUI_Work_Program__c+'\') AND SUI_Work_Priority__c includes (\''+currentWO.SUI_Work_Priority__r.name+'\')';
                    if(componentTypeId != ''  && componentTypeId != null){
                    query += ' AND SUI_Component_Type__c =:componentTypeId ';
                    }
        
                    if(subComponentId != ''  && subComponentId != null){
                    query += ' AND SUI_Sub_Component__c =:subComponentId ';
                    }
        
       } 

   
       //Query the service catalouge records
       list<SUI_Service_Catalogue__c> serviceCatalougeList = database.query(query);
       system.debug(serviceCatalougeList);
       list<serviceCatalougeWrapper> serviceCatalougeWrapperList = new list<serviceCatalougeWrapper>();
       for(SUI_Service_Catalogue__c catalogue : serviceCatalougeList){
           serviceCatalougeWrapperList.add(new serviceCatalougeWrapper(catalogue,null,null));
       }
       return serviceCatalougeWrapperList;
   }

    /**
    * @description            This method is responsible to fetch all  Service Catalouge for the given component, component 
    *                         type and sub componant. It will also include already added work order line item for that work order. 
    * @param  workOrderId     This is work order Id required to check which service catalouge already added under this work order.
    * @param  componentId     Filter value for - component 
    * @param  componentTypeId Filter value for - component type 
    * @param  subComponentId  Filter value for - sub component 
    * @param  contractType    Filter value for - contract type
    * @param  supplementaryWorksFlag    
    * @return                 return description
    */ 
   @AuraEnabled 
   public static list<serviceCatalougeWrapper> fetchAllSORList(String workOrderId, String componentId, String componentTypeId, String subComponentId, String contractType,boolean isSupplementaryWorksFlag){
       WorkOrder currentWO = [SELECT Id, RecordTypeId,SUI_Record_Type_developer_Name__c,SUI_Work_Program__c,SUI_Prog_Work_Classification__c,SUI_Work_Priority__r.name FROM WorkOrder Where ID =: workOrderId];    
    
       String scopingContract =GlobalConstants.WORK_ORDER_CONTRACT_TYPE_SCOPING;
       String scopingComponent= GlobalConstants.SERVICE_CATALOGUE_COMPONENT_SCOPING;

       //Create a query 
       String query = '';
        if(currentWo.SUI_Record_Type_developer_Name__c != GlobalConstants.WORK_ORDER_RECORD_TYPE_SCOPING){
           query = 'SELECT Id,Name,SUI_Activity_Type__c,SUI_Trade_Name__c,SUI_Service_Item_Code__c,SUI_Service_Item_Long_Description__c,SUI_Service_Item_Short_Description__c,SUI_Component__c,SUI_Component__r.Name,SUI_Component_Type__c,SUI_Finance_Category__c,SUI_Finance_Category_Threshold_Quantity__c,SUI_Component_Type__r.Name,SUI_Sub_Component__r.Name,SUI_Sub_Component__c,SUI_Work_Program__c,SUI_Work_Classification__c'+ 
                   ' FROM SUI_Service_Catalogue__c'+  
                   ' WHERE SUI_Contract_Type__c=:contractType AND SUI_Work_Classification__c includes (\''+currentWO.SUI_Prog_Work_Classification__c+'\') AND SUI_Work_Program__c  includes (\''+currentWO.SUI_Work_Program__c+'\') AND SUI_Work_Priority__c includes (\''+currentWO.SUI_Work_Priority__r.name+'\') AND SUI_Supplementary_Works_Flag__c =' + isSupplementaryWorksFlag;
           if(componentId != '' && componentId != null){
               query += ' AND SUI_Component__c =:componentId ';
           }

           if(componentTypeId != ''  && componentTypeId != null){
               query += ' AND SUI_Component_Type__c =:componentTypeId ';
           }

           if(subComponentId != ''  && subComponentId != null){
               query += ' AND SUI_Sub_Component__c =:subComponentId ';
           }
          
       }else{
           query = 'SELECT Id,Name,SUI_Activity_Type__c,SUI_Trade_Name__c,SUI_Service_Item_Code__c,SUI_Service_Item_Long_Description__c,SUI_Service_Item_Short_Description__c,SUI_Component__c,SUI_Component__r.Name,SUI_Component_Type__c,SUI_Finance_Category__c,SUI_Finance_Category_Threshold_Quantity__c,SUI_Component_Type__r.Name,SUI_Sub_Component__r.Name,SUI_Sub_Component__c,SUI_Work_Program__c,SUI_Work_Classification__c'+ 
           ' FROM SUI_Service_Catalogue__c'+  
           ' WHERE SUI_Contract_Type__c=:contractType AND SUI_Component__r.Name =:scopingComponent AND SUI_Work_Classification__c includes (\''+currentWO.SUI_Prog_Work_Classification__c+'\') AND SUI_Work_Program__c  includes (\''+currentWO.SUI_Work_Program__c+'\') AND SUI_Work_Priority__c includes (\''+currentWO.SUI_Work_Priority__r.name+'\') AND SUI_Supplementary_Works_Flag__c =' + isSupplementaryWorksFlag;
           if(componentTypeId != ''  && componentTypeId != null){
            query += ' AND SUI_Component_Type__c =:componentTypeId ';
            }

           if(subComponentId != ''  && subComponentId != null){
            query += ' AND SUI_Sub_Component__c =:subComponentId ';
            }
       } 


       System.debug('The query is'+query);
       //Query the service catalouge records
       list<SUI_Service_Catalogue__c> serviceCatalougeList = database.query(query);
       
       list<serviceCatalougeWrapper> serviceCatalougeWrapperList = new list<serviceCatalougeWrapper>();
       for(SUI_Service_Catalogue__c catalogue : serviceCatalougeList){
           serviceCatalougeWrapperList.add(new serviceCatalougeWrapper(catalogue,null,null));
       }
       return serviceCatalougeWrapperList;
   } 

   /**
    * @description            This method is responsible to fetch all  Service Catalouge for the given component, component 
    *                         type and sub componant. It will also include already added work order line item for that work order.
                              this method implemented for MA-045 
    * @param  workOrderId     This is work order Id required to check which service catalouge already added under this work order.
    * @param  componentId     Filter value for - component 
    * @param  componentTypeId Filter value for - component type 
    * @param  subComponentId  Filter value for - sub component 
    * @param  contractType    Filter value for - contract type
    * @param  activityType    Filter value for - contract type
    * @param  financeCat      Filter value for - financeCat
    * @param  tradeName       Filter value for - tradeName
    * @param  shortDescription     Filter value for - shortDescription    
    * @return                 return description
    * Created By              Satya and Gaurav
    * CreatedDate             1st Sept. 2025
    * Version       
    */ 
   @AuraEnabled 
   public static list<serviceCatalougeWrapper> fetchAllSORsList(String workOrderId, String componentId, String componentTypeId, String subComponentId, String contractType, String activityType,String financeCat,String tradeName, boolean isSupplementaryWorksFlag, String shortDescription){
    System.debug('In fetchAllSORListNew ');
    WorkOrder currentWO = [SELECT Id, RecordTypeId,SUI_Record_Type_developer_Name__c FROM WorkOrder Where ID =: workOrderId];    
    String scopingContract = GlobalConstants.WORK_ORDER_CONTRACT_TYPE_SCOPING;
    String scopingComponent = GlobalConstants.SERVICE_CATALOGUE_COMPONENT_SCOPING;

    //Create a query 
    String query = '';
    if(currentWo.SUI_Record_Type_developer_Name__c != GlobalConstants.WORK_ORDER_RECORD_TYPE_SCOPING){
        query = 'SELECT Id,Name,SUI_Activity_Type__c,SUI_Trade_Name__c,SUI_Service_Item_Code__c,SUI_Service_Item_Long_Description__c,SUI_Service_Item_Short_Description__c,SUI_Component__c,SUI_Component__r.Name,SUI_Component_Type__c,SUI_Finance_Category__c,SUI_Finance_Category_Threshold_Quantity__c,SUI_Component_Type__r.Name,SUI_Sub_Component__r.Name,SUI_Sub_Component__c'+
                ' FROM SUI_Service_Catalogue__c'+
                ' WHERE SUI_Contract_Type__c=:contractType AND SUI_Supplementary_Works_Flag__c =' + isSupplementaryWorksFlag;
    }
    else{
        query = 'SELECT Id,Name,SUI_Activity_Type__c,SUI_Trade_Name__c,SUI_Service_Item_Code__c,SUI_Service_Item_Long_Description__c,SUI_Service_Item_Short_Description__c,SUI_Component__c,SUI_Component__r.Name,SUI_Component_Type__c,SUI_Finance_Category__c,SUI_Finance_Category_Threshold_Quantity__c,SUI_Component_Type__r.Name,SUI_Sub_Component__r.Name,SUI_Sub_Component__c'+
        ' FROM SUI_Service_Catalogue__c'+
        ' WHERE SUI_Contract_Type__c=:contractType AND SUI_Component__r.Name =:scopingComponent AND SUI_Supplementary_Works_Flag__c =' + isSupplementaryWorksFlag;
    }
    query += prepareSOQL(componentId, componentTypeId, subComponentId, contractType, activityType,
                                financeCat, tradeName, shortDescription);

    System.debug('The query is'+query);
    //Query the service catalouge records
    list<SUI_Service_Catalogue__c> serviceCatalougeList = database.query(query);
    list<serviceCatalougeWrapper> serviceCatalougeWrapperList = new list<serviceCatalougeWrapper>();
    for(SUI_Service_Catalogue__c catalogue : serviceCatalougeList){
        serviceCatalougeWrapperList.add(new serviceCatalougeWrapper(catalogue,null,null));
    }
    return serviceCatalougeWrapperList;
}


   /**
    * @description        This method is responsible to return the work order details based on given work order Id
    * @param  workOrderId Work order Id to get the details
    * @return             return Work order record
    */ 
   @AuraEnabled
   public static boolean checkIfParentWo(String workOrderId){
       boolean isParentWo=false;
       List<Workorder> wo=[SELECT Id, ParentWorkOrderId, Status FROM WorkOrder where ParentWorkOrderId=:workOrderId
                           AND recordType.developerName=:GlobalConstants.WORK_ORDER_RECORD_TYPE_SCOPING
                           AND (Status =: GlobalConstants.WORK_ORDER_STATUS_ADDITIONAL_INFO_REQUIRED
                           OR Status =: GlobalConstants.WORK_ORDER_STATUS_WORK_IN_PROGRESS)];

       if(wo.size()==1 && wo.IsEmpty()==false){
           isParentWo=true;
       }
       return isParentWo;
   }

       /**
    * @description        This method is responsible to return the Scoping work order details based on given work order Id
    * @param  workOrderId Work order Id to get the details
    * @return             return Boolean 
    */ 
   @AuraEnabled
   public static boolean statusAdditionalInfoReq(String workOrderId){
       boolean isStausAdditionalInfoReq=false;
       List<Workorder> workOrderList=[SELECT Id, ParentWorkOrderId FROM WorkOrder where ParentWorkOrderId=:workOrderId
                           AND recordType.developerName=:GlobalConstants.WORK_ORDER_RECORD_TYPE_SCOPING
                           AND (Status =: GlobalConstants.WORK_ORDER_STATUS_ADDITIONAL_INFO_REQUIRED
                           OR Status =: GlobalConstants.WORK_ORDER_STATUS_WORK_IN_PROGRESS)                            
                           ];

       if(workOrderList.size()==1 && workOrderList.IsEmpty()==false){
           isStausAdditionalInfoReq=true;
       }
       return isStausAdditionalInfoReq;
   }


   /**
    * @description        This method is responsible to return the work order details based on given work order Id
    * @param  workOrderId Work order Id to get the details
    * @return             return Work order record
    */ 
   @AuraEnabled
   public static WorkOrder getWorkOrderDetails(String workOrderId ){
       WorkOrder workOrderData=[SELECT Id,CaseId,SUI_ref__r.recordType.DeveloperName,Status,SUI_Sub_Milestone__c,SUI_Record_Type_developer_Name__c,
                               SUI_Supplementary_Works_Indicator__c,ParentWorkOrderId,ParentWorkOrder.SUI_Record_Type_developer_Name__c,
                               /*Component*/
                               SUI_Ref__r.SUI_Master_Component__c,Contract_Type__c,
                               
                               /*Component Type*/
                               SUI_Ref__r.SUI_Reference_Component__r.SUI_Master_Component__c,
                               SUI_Ref__r.SUI_Master_Component_Type__c,
                               
                               /*Sub Component*/
                               SUI_Ref__r.SUI_Reference_Component_Type__r.SUI_Reference_Component__r.SUI_Master_Component__c,
                               SUI_Ref__r.SUI_Reference_Component_Type__r.SUI_Master_Component_Type__c,
                               SUI_Ref__r.SUI_Master_Sub_Component__c,
                               SUI_Add_SOR_Visibility__c,
                               Case.SUI_Ref__c, Case.SUI_Ref__r.SUI_Master_Component__c,Case.SUI_Ref__r.SUI_Master_Component_Type__c
                               FROM WorkOrder Where Id=: workOrderId LIMIT 1];
       return workOrderData;
   }

   /**
    * @description This method is responsible to save the selected SOR on Add SOR lwc hosted on the work order lightning detail page
    *              user select multiple SOR and when they click on save this method will be called to save the selected sor as a 
    *              work order line items.
    * @param  selectedServiceCatalougeJSONString This is the JSON string sent by the ADD SOR lwc component which has list of all the 
    *                                            selected SOR. Using this list we are creating work order line items under work order.
    * @param  workOrderId                        This is the work order Id. All created work order line items will be saved under this work
    *                                            order.
    */
   @AuraEnabled
   public static void save(String selectedServiceCatalougeJSONString ,String workOrderId){
       list<serviceCatalougeWrapper> wrapperList = (list<serviceCatalougeWrapper>) JSON.deserialize(selectedServiceCatalougeJSONString, list<serviceCatalougeWrapper>.Class );
       
       map<Id,SUI_Service_Catalogue__c> idVsServiceCatalougeMap = 
                   new Map<Id,SUI_Service_Catalogue__c>([SELECT Id,Name,SUI_Service_Item_Code__c,SUI_Service_Item_Short_Description__c,
                                                               SUI_Component__c,SUI_Component__r.Name,SUI_Component_Type__c,SUI_Finance_Category__c,
                                                               SUI_Finance_Category_Threshold_Quantity__c,SUI_Component_Type__r.Name,
                                                               SUI_Sub_Component__r.Name,SUI_Sub_Component__c,SUI_Unit_of_Measure__c,SUI_Service_Item_Long_Description__c 
                                                         FROM SUI_Service_Catalogue__c]);
       
       try{
           //Create a work order line item using above wrapper list 
           list<WorkOrderLineItem> workOrderLineItems = new list<WorkOrderLineItem>();

           for(serviceCatalougeWrapper warpper : wrapperList){
               SUI_Service_Catalogue__c catalogue = idVsServiceCatalougeMap.get(warpper.Id);
               WorkOrderLineItem woli = new WorkOrderLineItem();
               woli.workOrderId = workOrderId;
               woli.SUI_Service_Item_Code__c = catalogue.SUI_Service_Item_Code__c;
               woli.SUI_Quantity__c = warpper.quantity;
               woli.SUI_Location_Type__c=warpper.location;
               
              
               if(woli.SUI_Quantity__c !=0){
                   workOrderLineItems.add(woli);
               }
           }
           //insert work order line items 
           if(!workOrderLineItems.isEmpty()){

                WorkOrderTriggerHandler.BY_PASS_SUPPDELEGATION_CHECK = true;
                insert workOrderLineItems;

                WorkOrderTriggerHandler.BY_PASS_SUPPDELEGATION_CHECK = false;
           }
           
           //update the Work Order to Execute the SUI_UpdateContractorPriceBatch
           if(workOrderId != ''){
               WorkOrder workOrderRecord = [SELECT Id, SUI_Price_Refresh_Required__c,SUI_Record_Type_developer_Name__c,status FROM WorkOrder Where Id=: workOrderId];
               if((workOrderRecord.SUI_Record_Type_developer_Name__c == 'SUI_Programmed' && workOrderRecord.status=='Raised') || workOrderRecord.SUI_Record_Type_developer_Name__c == 'SUI_Scoping' && workOrderRecord.status=='Raised'){
                   System.debug('Entered');
                   workOrderRecord.SUI_Price_Refresh_Required__c = true;
                   System.debug(workOrderRecord.SUI_Price_Refresh_Required__c);
                }else{
                   workOrderRecord.SUI_Price_Refresh_Required__c = false;
               }
               update workOrderRecord;
           }    
       }catch(Exception ex){
           ApplicationLogHandler.addLog('AddSORController','save',ex);
           ApplicationLogHandler.saveLog();
           throw new CustomException('Exception occured while saving SoR. Please contact system admin :=> '+ ex.getMessage());
       }

   }

   /**
    * @description This method is responsible to save the selected SOR on Add SOR lwc hosted on the work order lightning detail page
    *              user select multiple SOR and when they click on save this method will be called to save the selected sor as a 
    *              work order line items.
    * @param  selectedServiceCatalougeJSONString This is the JSON string sent by the ADD SOR lwc component which has list of all the 
    *                                            selected SOR. Using this list we are creating work order line items under work order.
    * @param  workOrderId                        This is the work order Id. All created work order line items will be saved under this work
    *                                            order with Status as Unapproved.
    */
   @AuraEnabled
   public static void saveSupplementaryWoli(String selectedServiceCatalougeJSONString ,String workOrderId){
       system.debug(selectedServiceCatalougeJSONString);
       list<serviceCatalougeWrapper> wrapperList = (list<serviceCatalougeWrapper>) JSON.deserialize(selectedServiceCatalougeJSONString, list<serviceCatalougeWrapper>.Class );
       system.debug(wrapperList);
       map<Id,SUI_Service_Catalogue__c> idVsServiceCatalougeMap = 
                   new Map<Id,SUI_Service_Catalogue__c>([SELECT Id,Name,SUI_Service_Item_Code__c,SUI_Service_Item_Short_Description__c,
                                                               SUI_Component__c,SUI_Component__r.Name,SUI_Component_Type__c,SUI_Finance_Category__c,
                                                               SUI_Finance_Category_Threshold_Quantity__c,SUI_Component_Type__r.Name,
                                                               SUI_Sub_Component__r.Name,SUI_Sub_Component__c,SUI_Unit_of_Measure__c ,SUI_Service_Item_Long_Description__c
                                                         FROM SUI_Service_Catalogue__c]);
       
       try{
           //Create a work order line item using above wrapper list 
           list<WorkOrderLineItem> workOrderLineItems = new list<WorkOrderLineItem>();
           for(serviceCatalougeWrapper warpper : wrapperList){
               SUI_Service_Catalogue__c catalogue = idVsServiceCatalougeMap.get(warpper.Id);
               WorkOrderLineItem woli = new WorkOrderLineItem();
               woli.workOrderId = workOrderId;
               woli.SUI_Service_Item_Code__c = catalogue.SUI_Service_Item_Code__c;
               woli.SUI_Quantity__c = warpper.quantity;
               woli.SUI_Location_Type__c=warpper.location;
              
               if(woli.SUI_Quantity__c !=0){
                   workOrderLineItems.add(woli);
               }
           }
           System.debug('Data for Supp Works before saving==>'+workOrderLineItems);
           //insert work order line items 
           if(!workOrderLineItems.isEmpty()){
                WorkOrderTriggerHandler.BY_PASS_SUPPDELEGATION_CHECK = true;
                insert workOrderLineItems;
                WorkOrderTriggerHandler.BY_PASS_SUPPDELEGATION_CHECK = false;
           }
           System.debug('Data for Supp Works after saving==>'+workOrderLineItems);
            //change the  Supplementary Works Indicator value to Requested  && SUI_Price_Refresh_Required__c to true
           if(workOrderId != ''){
               System.debug('Update WorkOrder SUI_Supplementary_Works_Indicator__c');
               WorkOrder wo = new WorkOrder();
               wo.Id = workOrderId;
               wo.SUI_Supplementary_Works_Indicator__c = GlobalConstants.WORK_ORDER_SUPPLEMENTARY_WORKS_INDICATOR_REQUESTED;
               System.debug('The WorkOrder Data is===>'+wo);
               wo.SUI_Price_Refresh_Required__c = false;
               update wo;
           }

       }catch(Exception ex){
           ApplicationLogHandler.addLog('AddSORController','save',ex);
           ApplicationLogHandler.saveLog();
           throw new CustomException('Exception occured while saving SoR. Please contact system admin :=> '+ ex.getMessage());
       }

   }

   /**
    * @description This method is responsible to check if evidence is required basec on the milestone metadata and work order milestone or submilestone 
    * @param  workOrderId                        This is the work order Id. 
    * Test - system.debug('=======' + SUI_Milestone_Metadata__mdt.getInstance('Supplementary_Works_SUP1_SUP2').SUI_Evidence_Required__c);
    */
   @AuraEnabled 
   public static boolean checkIfEvidenceRequired (){

       return SUI_Milestone_Metadata__mdt.getInstance('Supplementary_Works_SUP1_SUP2').SUI_Evidence_Required__c;
       
   }
   
    /**
    * @description : This method is responsible to update the work order with given field. This 
    * @param  workOrderId :This is the work order Id. 
    */
   @AuraEnabled
   public static void updateComments (String workOrderId,String comment){
       WorkOrder wo = new WorkOrder();
       wo.Id = workOrderId; 
       wo.SUI_Supplementary_Work_Comments__c = comment; 
       updateWorkOrder(wo); 
   }

   /**
    * @description : This method is responsible to update the work order.
    * @param  wo   : Work order instance to update 
    */
   private static void updateWorkOrder (WorkOrder wo){
       try {
           update wo;
       } catch(exception ex) {
           ApplicationLogHandler.addLog('AddSORController','updateWorkOrder',ex);
           ApplicationLogHandler.saveLog();
           throw new SUI_CustomException('Exception occured while updating work order. Please contact system admin :=> '+ ex.getMessage());
       }
   }

   /**
    * @description : This method is responsible to retrieve custom metadata which stored the Max Number value to Add SOR
    *                using Add SORs LWC component
   */
   @AuraEnabled(cacheable=true)
   public static List <SUI_Metadata__mdt > fetchMetadataRecs() {
      List < SUI_Metadata__mdt > metavalue=[SELECT Id,MasterLabel,SUI_Text_Value__c,SUI_Value__c FROM SUI_Metadata__mdt where MasterLabel ='SUI Add SOR Max Number'];
      return metavalue;
   }

   /**
    * Get scoping Component Id from Master Data
    * 
    */
   @AuraEnabled(cacheable=true)
   public static List<SUI_Master_Data__c> fetchScopCompId() {
       List<SUI_Master_Data__c> masterScoping= [SELECT Id FROM SUI_Master_Data__c WHERE SUI_Record_Type_Developer_Name__c='SUI_Component' AND Name='Scoping'];
       return masterScoping;
   }

   /**
     * This method fetch Location Type Data 
    */
    @AuraEnabled 
    public static List<SUI_Master_Data__c> getLocations(){
        List<SUI_Master_Data__c> locationData=[SELECT Id,Name, SUI_Record_Type_Developer_Name__c FROM SUI_Master_Data__c WHERE SUI_Record_Type_Developer_Name__c=:GlobalConstants.SUI_MASTER_DATA_RECORD_TYPE_LOCATION_TYPE];
        return locationData;
    }
   

   /**
    * @description : Wrapper class to bind the quantity with service catalouge record
    */ 
   public class serviceCatalougeWrapper {
       @AuraEnabled public String Id                                        {get;set;}
       @AuraEnabled public String Name                                      {get;set;}
       @AuraEnabled public String SUI_Service_Item_Code                     {get;set;}
       @AuraEnabled public String SUI_Service_Item_Long_Description         {get;set;}
       @AuraEnabled public String SUI_Finance_Category                      {get;set;}
       @AuraEnabled public Decimal SUI_Finance_Category_Threshold_Quantity  {get;set;}
       @AuraEnabled public String component                                 {get;set;}
       @AuraEnabled public String componentType                             {get;set;}
       @AuraEnabled public String subComponent                              {get;set;}
       @AuraEnabled public Decimal quantity                                 {get;set;} 
       @AuraEnabled public String location                                  {get;set;} 
       @AuraEnabled public String activityType                                  {get;set;}
       @AuraEnabled public String financeCat                                  {get;set;}
       @AuraEnabled public String tradeName                                  {get;set;}
       @AuraEnabled public String serviceItemShortDesc                       {get;set;} 
                
       

       public serviceCatalougeWrapper( SUI_Service_Catalogue__c cataloughDetails , Decimal quantity, String location){
           this.Id = cataloughDetails.Id;
           this.Name = cataloughDetails.Name;  
           this.SUI_Service_Item_Code = cataloughDetails.SUI_Service_Item_Code__c;
           this.SUI_Service_Item_Long_Description = cataloughDetails.SUI_Service_Item_Long_Description__c;
           this.SUI_Finance_Category = cataloughDetails.SUI_Finance_Category__c;
           this.SUI_Finance_Category_Threshold_Quantity = cataloughDetails.SUI_Finance_Category_Threshold_Quantity__c;
           this.quantity = quantity;
           this.component = cataloughDetails.SUI_Component__r?.Name;
           this.componentType  = cataloughDetails.SUI_Component_Type__r?.Name;
           this.subComponent = cataloughDetails.SUI_Sub_Component__r?.Name;
           this.location = location;
           this.activityType = cataloughDetails.SUI_Activity_Type__c;
           this.financeCat = cataloughDetails.SUI_Finance_Category__c;
           this.tradeName = cataloughDetails.SUI_Trade_Name__c;
           this.serviceItemShortDesc = cataloughDetails.SUI_Service_Item_Short_Description__c;
           System.debug('this.subComponent='+this.subComponent);
       }
   }
    
    

    
    /**
     * Method to get combined data by WorkOrderLine and Service Catalog
    */
    @AuraEnabled 
    public static List<CombinedData> getCombinedWoliData(Id workOrderId) {
        List<CombinedData> results = new List<CombinedData>();

        // Step 1: Query WorkOrderLineItems
        List<WorkOrderLineItem> lineItems = [
            SELECT Id, SUI_Quantity__c, SUI_Location_Type__r.Name, SUI_Service_Item_Code__c, SUI_Service_Item_Long_Description__c,SUI_Supplementary_Works_Type__c,Status
            FROM WorkOrderLineItem
            WHERE WorkOrderId = :workOrderId
        ];

        // Step 2: Collect service item codes
        Set<String> serviceItemCodes = new Set<String>();
        for (WorkOrderLineItem item : lineItems) {
            if (item.SUI_Service_Item_Code__c != null) {
                serviceItemCodes.add(item.SUI_Service_Item_Code__c);
            }
        }

        // Step 3: Query Service Catalogue records
        Map<String, SUI_Service_Catalogue__c> catalogueMap = new Map<String, SUI_Service_Catalogue__c>();
        if (!serviceItemCodes.isEmpty()) {
            for (SUI_Service_Catalogue__c cat : [
                SELECT Id, SUI_Service_Item_Code__c, SUI_Component__r.Name, SUI_Component_Type__r.Name, SUI_Sub_Component__r.Name
                FROM SUI_Service_Catalogue__c
                WHERE SUI_Service_Item_Code__c IN :serviceItemCodes
            ]) {
                catalogueMap.put(cat.SUI_Service_Item_Code__c, cat);
            }
        }

        // Step 4: Combine data into wrapper
        for (WorkOrderLineItem item : lineItems) {
            CombinedData combined = new CombinedData();
            
            combined.lineItem = item;
            combined.catalogue = catalogueMap.get(item.SUI_Service_Item_Code__c);
            results.add(combined);
        }

            System.debug('##'+results);
        return results;
    }
    // Wrapper class to hold combined data
    public class CombinedData {
        @AuraEnabled public WorkOrderLineItem lineItem { get; set; }
        @AuraEnabled  public SUI_Service_Catalogue__c catalogue { get; set; }
    }


}