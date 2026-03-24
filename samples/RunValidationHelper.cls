/**
* ─────────────────────────────────────────────────────────────────────────────────────────────────┐
* RunValidationHelper
* ──────────────────────────────────────────────────────────────────────────────────────────────────
* @author         Sauce Consulting
* @modifiedBy     
* @version        1.0
* @created        2023-09-20
* @modified       YYYY-MM-DD
* @description    Helper class for RunValidationBatch
* ──────────────────────────────────────────────────────────────────────────────────────────────────
* @changes
* vX.X            name@sauceconsulting.com.au
* YYYY-MM-DD      Explanation of the change.  Multiple lines can be used to explain the change, but
*                 each line should be indented till left aligned with the previous description text.
* ─────────────────────────────────────────────────────────────────────────────────────────────────┘
*/

public class RunValidationHelper {
    
    public static Map<String, Facility__c> facilityMap { get; set; }
    public static Set<String> serviceItemCodes { get; set; }
    public static Set<String> serviceItemCodesScoping { get; set; }
    public static Set<String> serviceItemCodesDef { get; set; }
    public static Set<String> locationTypeMasterDataDef { get; set; }
    public static Set<String> locationTypeMasterData { get; set; }
    public static Set<String> workPriorityMasterData { get; set; }
    public static Map<String, String> workClassificationMasterData { get; set; }
    public static Map<String, String> defectWorkClassificationMasterData { get; set; }
    public static Map<Id,String> woSSTMap = new Map<Id,String>();
    public static List<String> sstList = new List<String>();
    public static MAP<String,Defect__c> finalCodeMAP =  new MAP<String,Defect__c>();
    public static List<Defect__c> defectlst;
    public static MAP<String,Defect__c> defectcodeMap = new MAP<String,Defect__c>();
    public static List<String> defectLocationlst = new List<String>();
    public static List<Survey__c> surveyAllLst;
    public static List<Master_Data__c> scopingID;
    public static Map<String, String> workProgramMasterData { get; set; }
    public static List<Survey__c> surveyLst = new List<Survey__c>();
    
     
    //#0A Fetch all the required data in init method for all the subsequent validation methods
    public static void init(List<WorkOrder> woList){
        facilityMap = new Map<String, Facility__c>();
        serviceItemCodesDef= new Set<String>();
        locationTypeMasterDataDef= new Set<String>();
        serviceItemCodes = new Set<String>();
        serviceItemCodesScoping = new Set<String>();
        locationTypeMasterData = new Set<String>();
        workPriorityMasterData = new Set<String>();
        workClassificationMasterData = new Map<String, String>();
        workProgramMasterData = new Map<String, String>();
        defectWorkClassificationMasterData = new Map<String, String>();
        Set<String> uniqueSoRs = new Set<String>();
      
       //Fetch only the records referenced in related Jobs
        Set<String> wofacilityRefNums = new Set<String>(); 
        Set<String> woServiceItemCodes = new Set<String>();
        Set<String> woLocationTypes = new Set<String>();
        Set<String> woWorkPriorities = new Set<String>(); 

       //Defect Lists 
       //Fetch only the records referenced in related Jobs
        Set<String> defServiceItemCodes = new Set<String>();
        Set<String> defLocationTypes = new Set<String>();
        
        //Populating these sets so that only record-specific data will be fetched from the org
        for(WorkOrder wo : woList){
            if(String.isNotBlank(wo.Prog_Facility__c)){
                wofacilityRefNums.add(wo.Prog_Facility__c);
            }
            if(String.isNotBlank(wo.Prog_Priority__c)){
                woWorkPriorities.add(wo.Prog_Priority__c);
            }
            //get all the ServItemcodes in Prog_Scoping_SORs__c, Prog_SORs__c for each record and store in woServiceItemCodes
            if(String.isNotBlank(wo.Prog_SORs__c)){
                woServiceItemCodes = extractValuesfromField(wo.Prog_SORs__c, woServiceItemCodes);
            }else{
                woServiceItemCodes = extractValuesfromField(wo.Prog_Scoping_SORs__c, woServiceItemCodes);
            }
            //get all location types stored in Prog_LocationType__c field for each Work Order
            if(String.isNotBlank(wo.Prog_LocationType__c)){
                woLocationTypes = extractValuesfromField(wo.Prog_LocationType__c, woLocationTypes);
            }
            //get the sst reference value from work order
            if(String.isNotBlank(wo.Prog_SSTRef__c)){
                woSSTMap.put(wo.Id,wo.Prog_SSTRef__c);
                sstList.add(wo.Prog_SSTRef__c);
            }
        }
           
        //Fetch Facility Data
        for(Facility__c fac : [SELECT Id, Facility_Reference_Number__c, Responsible_for_Maintenance__c 
                               FROM Facility__c 
                               WHERE Facility_Reference_Number__c != NULL 
                               AND Responsible_for_Maintenance__c != NULL 
                               AND Facility_Reference_Number__c IN :wofacilityRefNums]){
            if(fac.Facility_Reference_Number__c != NULL){
                facilityMap.put(fac.Facility_Reference_Number__c, fac);
            }            
        }
        
         //Fetch Scoping Record type details
        scopingID = [SELECT Id, Name FROM Master_Data__c WHERE Name =: GlobalConstants.WORK_ORDER_CONTRACT_TYPE_SCOPING];

        //Fetch all Service_Catalogue__c data
        for(Service_Catalogue__c sSC : [SELECT Id, Service_Item_Code__c 
                                            FROM Service_Catalogue__c
                                            WHERE Service_Item_Code__c IN :woServiceItemCodes]){
            if(String.isNotBlank(sSC.Service_Item_Code__c)){
                serviceItemCodes.add(sSC.Service_Item_Code__c);
            }
        }
         
        //Fetch all Service_Catalogue__c data of Contract Type Scoping
        if((scopingID !=null && !scopingID.isEmpty()) && (woServiceItemCodes!=null && !woServiceItemCodes.isEmpty())){    
            List<Service_Catalogue__c> serviceCatList =  [SELECT Id, Service_Item_Code__c 
                                                              FROM Service_Catalogue__c
                                                              WHERE Component__c =:scopingID[0].Id  AND Service_Item_Code__c IN :woServiceItemCodes];
            if(serviceCatList !=null && !serviceCatList.isEmpty()){
                for(Service_Catalogue__c sSC : serviceCatList){
                    if(String.isNotBlank(sSC.Service_Item_Code__c)){
                        serviceItemCodesScoping.add(sSC.Service_Item_Code__c);
                    }
                }
            }
        }
        
       
        //Fetch all the Location Type records from SUI Master Data object where RT is LocationType
        for(Master_Data__c sMD : [SELECT Id, Name, RecordType.DeveloperName 
                                      FROM Master_Data__c 
                                      WHERE RecordType.DeveloperName =: GlobalConstants.MASTER_DATA_RECORD_TYPE_LOCATION_TYPE
                                      AND Name IN :woLocationTypes]){
            locationTypeMasterData.add(sMD.Name);
        }
        
        //Fetch all the Work Priority records from SUI Master Data object where RT is WorkPriority
        for(Master_Data__c sMD : [SELECT Id, Code__c, RecordType.DeveloperName 
                                      FROM Master_Data__c 
                                      WHERE RecordType.DeveloperName =: GlobalConstants.MASTER_DATA_RECORD_TYPE_WORK_PRIORITY
                                      AND Code__c IN :woWorkPriorities]){
            workPriorityMasterData.add(sMD.Code__c);
        }
        
        //Fetch all the Service_Catalogue__c records with their Work classification
        uniqueSoRs = getUniqueSORs(woList);
        for(Service_Catalogue__c sSC : [SELECT Id, Service_Item_Code__c, Work_Classification__c,Work_Program__c 
                                            FROM Service_Catalogue__c
                                            WHERE Service_Item_Code__c IN :uniqueSoRs] ){
            workClassificationMasterData.put(sSC.Service_Item_Code__c, sSC.Work_Classification__c);
            workProgramMasterData.put(sSC.Service_Item_Code__c, sSC.Work_Program__c);
            System.debug(workClassificationMasterData);
        }
     
        //-------------------Preparing Defect related data--------------------------------------------------
        // get the survey details mathcing SSt reference number
        surveyLst=[SELECT Id, Name,Survey_Reference_Number__c,Status__c 
                                    FROM Survey__c
                                    WHERE (Name IN:sstList OR Survey_Reference_Number__c IN:sstList)
                                    AND Status__c =: GlobalConstants.SURVEY_STATUS_FINALISED];
        defectlst = [SELECT Id,Defect_Code__c,Survey__c,Defect_Quantity__c,Location__c,Survey__r.Name 
                    FROM Defect__c 
                    WHERE Survey__r.Name IN: sstList];
        List<String> defectName = new List<String>();
        //get the defect code and location list            
        for(Defect__c def:defectlst){
            defectcodeMap.put(def.Id,def);
            defectName.add(def.Defect_Code__c);
            defectLocationlst.add(def.Location__c);
        }
        //Fetch all service Item code data matching with Defect code
        for(Service_Catalogue__c sSC : [SELECT Id, 
                        Service_Item_Code__c 
                        FROM Service_Catalogue__c
                        WHERE Service_Item_Code__c IN :defectName]){
            if(String.isNotBlank(sSC.Service_Item_Code__c)){
                serviceItemCodesDef.add(sSC.Service_Item_Code__c);
            }
        }
        //Fetch all the Location Type matching with Defect Location
        for(Master_Data__c sMD : [SELECT Id, Name, RecordType.DeveloperName 
                    FROM Master_Data__c 
                    WHERE RecordType.DeveloperName =: GlobalConstants.MASTER_DATA_RECORD_TYPE_LOCATION_TYPE]){
            locationTypeMasterDataDef.add(sMD.Name);
        }

        for(Service_Catalogue__c sSC : [SELECT Id, Service_Item_Code__c, Work_Classification__c 
                                            FROM Service_Catalogue__c] ){
            defectWorkClassificationMasterData.put(sSC.Service_Item_Code__c, sSC.Work_Classification__c);
            System.debug(defectWorkClassificationMasterData.size());
        }
  
      /*  surveyAllLst =[SELECT Id,Name,Survey_Reference_Number__c,Status__c from Survey__c
                            WHERE Status__c =: GlobalConstants.SURVEY_STATUS_FINALISED];*/
                            
    }
    
    //#0B Set Validation Outcome and Validation Message to blank
    public static void resetValidationOutcomes(WorkOrder woRecord){
        //Set the Validation Outcome and Validation Message to blank everytime user restarts the validation on the same record
            woRecord.Prog_Val_Message__c = '';
            woRecord.Prog_Val_Outcome__c = '';
    }
    
    //#1 Function to validate if the given Facility is present in the Org
    public static void validateFacility(WorkOrder woRecord){
        //validate if the Facility is present (Facility_Reference_Number__c) and Responsible_for_Maintenance__c is Y
        if( facilityMap == NULL){
            woRecord.Prog_Val_Message__c = System.Label.VM_FacilityRespForMaintenance;
            woRecord.Prog_Val_Outcome__c = 'Error';
            return;
        }
        if( !facilityMap.containsKey(woRecord.Prog_Facility__c) 
            || (!((facilityMap.get(woRecord.Prog_Facility__c).Responsible_for_Maintenance__c).toUpperCase() == 'Y')
            && !((facilityMap.get(woRecord.Prog_Facility__c).Responsible_for_Maintenance__c).toUpperCase() == 'PD'))){
            woRecord.Prog_Val_Message__c = System.Label.VM_FacilityRespForMaintenance;
            woRecord.Prog_Val_Outcome__c = 'Error';    
            }
    }
    
    //#2A Function to validate if the number of values in SORs, Quantity and Location Type fields are same in WO(Job) record
    public static void validateSoRQttyLocType(WorkOrder woRecord){
        //Compare number of values in Prog_SORs__c text1000, Prog_Quantity__c text100, Prog_LocationType__c text1000 
             Integer sorCount = countCommaSeparatedValues(woRecord.Prog_SORs__c);
             Integer qttyCount = countCommaSeparatedValues(woRecord.Prog_Quantity__c);
             Integer locTypeCount = countCommaSeparatedValues(woRecord.Prog_LocationType__c);
                
             if( sorCount != qttyCount || qttyCount != locTypeCount ){
                 woRecord.Prog_Val_Message__c = String.isBlank(woRecord.Prog_Val_Message__c) 
                     ? System.Label.VM_SORQuantityLocationType 
                     : woRecord.Prog_Val_Message__c + '; \n' + System.Label.VM_SORQuantityLocationType;
                 woRecord.Prog_Val_Outcome__c = 'Error';
             }
    }
    
    //#2B Function to validate if the number of values in Prog_Scoping_SORs & Prog_Scoping_Quantity are same in WO(Job) record
    public static void validateScopingSoRQuantity(WorkOrder woRecord){
        //Compare number of values in Prog_Scoping_SORs Long Text Area(1000), Prog_Scoping_Quantity__c text100
        Integer sorCount = countCommaSeparatedValues(woRecord.Prog_Scoping_SORs__c);
        Integer qttyCount = countCommaSeparatedValues(woRecord.Prog_Scoping_Quantity__c);
        Integer locTypeCount = countCommaSeparatedValues(woRecord.Prog_LocationType__c);

        if( sorCount != qttyCount || qttyCount != locTypeCount  ){
            woRecord.Prog_Val_Message__c = String.isBlank(woRecord.Prog_Val_Message__c) 
                        ? System.Label.VM_ScopingSORQuantity 
                        : woRecord.Prog_Val_Message__c + '; \n' + System.Label.VM_ScopingSORQuantity;
            woRecord.Prog_Val_Outcome__c = 'Error';
        }
       
    }


    //#3-A Function to validate if each Scoping SOR is present in SUI Service Catalogue
    public static void validateScopingSoRs(WorkOrder woRecord, String fieldName){
        
        Boolean soRErrorIndicator = FALSE;
        String fieldVal = (String)woRecord.get(fieldName);
        
        if( serviceItemCodesScoping != NULL && !String.isBlank(fieldVal) ){
            List<String> sorCodes = fieldVal.split(',');
            for(String sorCode : sorCodes){
                if(!serviceItemCodesScoping.contains(sorCode.trim())){
                    soRErrorIndicator = TRUE;
                    break;
                }        
            }
        }
        
        if(soRErrorIndicator){
            woRecord.Prog_Val_Message__c = String.isBlank(woRecord.Prog_Val_Message__c) 
                        ? System.Label.VM_ScopingSoR
                        : woRecord.Prog_Val_Message__c + '; \n' + System.Label.VM_ScopingSoR;
            woRecord.Prog_Val_Outcome__c = 'Error';
        }
    }
                   




    
    //#3 Function to validate if each SOR is present in SUI Service Catalogue
    public static void validateSoRs(WorkOrder woRecord, String fieldName){
        
        Boolean soRErrorIndicator = FALSE;
        
        String fieldVal = (String)woRecord.get(fieldName);
        
        if( serviceItemCodes != NULL && !String.isBlank(fieldVal) ){
            List<String> sorCodes = fieldVal.split(',');
            for(String sorCode : sorCodes){
                if(!serviceItemCodes.contains(sorCode.trim())){
                    soRErrorIndicator = TRUE;
                    break;
                }        
            }
        }
        
        if(soRErrorIndicator){
            woRecord.Prog_Val_Message__c = String.isBlank(woRecord.Prog_Val_Message__c) 
                        ? System.Label.VM_SoRs 
                        : woRecord.Prog_Val_Message__c + '; \n' + System.Label.VM_SoRs;
            woRecord.Prog_Val_Outcome__c = 'Error';
        }
    }
    
    //#4 Function to validate if the Work Classification on a given WO matches the Work classification given on the Program
    public static void validateWorkClassification(WorkOrder woRecord){
        Boolean workClassifErrorIndicator = TRUE;
        List<String> woSoRValues = new list<String>();
        List<String> servCatalogueWorkClassif = new list<String>();
        List<String> servCatalogueWorkProg = new list<String>();
        system.debug(workProgramMasterData);
        if(woRecord.Prog_SORs__c!=null && String.isNotBlank(woRecord.Prog_SORs__c)){
            woSoRValues = woRecord.Prog_SORs__c.split(',');
            for(String woSOR : woSoRValues){
                woSOR = woSOR.trim();
                system.debug(woSOR);
                if( workClassificationMasterData != NULL && workClassificationMasterData.containsKey(woSOR) && String.isNotBlank(workClassificationMasterData.get(woSOR)) &&
                    workProgramMasterData != NULL && workProgramMasterData.containsKey(woSOR) && String.isNotBlank(workProgramMasterData.get(woSOR))){
                    servCatalogueWorkClassif = workClassificationMasterData.get(woSOR).split(';');
                    servCatalogueWorkProg = workProgramMasterData.get(woSOR).split(';');
                    system.debug(servCatalogueWorkProg);
                    system.debug(woRecord.Prog_Program__c);
                } 
                if(String.isNotBlank(woRecord.Prog_Work_Classification__c) && servCatalogueWorkClassif.contains(woRecord.Prog_Work_Classification__c) &&
                    String.isNotBlank(woRecord.Work_Program__c) && servCatalogueWorkProg.contains(woRecord.Work_Program__c)){
                    workClassifErrorIndicator = FALSE;
                }else{
                    workClassifErrorIndicator = TRUE;
                    break;
                }
            }
        }
        system.debug(workClassifErrorIndicator);
        if(workClassifErrorIndicator){
            woRecord.Prog_Val_Message__c = String.isBlank(woRecord.Prog_Val_Message__c) 
                        ? System.Label.VM_WorkClassification 
                        : woRecord.Prog_Val_Message__c + '; \n' + System.Label.VM_WorkClassification;
            woRecord.Prog_Val_Outcome__c = 'Error';
        }
    }
    
    //#5 Function to validate if the Location Type on WOs is present in the Org in SUI Master Data Object
    public static void validateLocationType(WorkOrder woRecord){
        //LocationType in the file: LivingRoom,Kitchen to be matched with Master_Data__c.Name of RT:Location Type
        Boolean locTypeErrorIndicator = FALSE;
        
        if( locationTypeMasterData != NULL && !String.isBlank(woRecord.Prog_LocationType__c)){
            List<String> locTypeNames = woRecord.Prog_LocationType__c.split(',');
            for(String locTypeName : locTypeNames){
                if(!locationTypeMasterData.contains(locTypeName.trim())){
                    locTypeErrorIndicator = TRUE;
                    break;
                }        
            }
        }
        
        if(locTypeErrorIndicator){
            woRecord.Prog_Val_Message__c = String.isBlank(woRecord.Prog_Val_Message__c) 
                        ? System.Label.VM_LocationType 
                        : woRecord.Prog_Val_Message__c + '; \n' + System.Label.VM_LocationType;
            woRecord.Prog_Val_Outcome__c = 'Error';
        }
        
    }
    
    //#6 Function to validate if the Work Priority on WOs is present in the Org in SUI Master Data Object
    public static void validateWorkPriority(WorkOrder woRecord){
        //Work Priority in the file: RP4D on a given job record to be matched with Master_Data__c.Code__c of RT:Work Priority
        if( workPriorityMasterData != NULL && String.isNotBlank(woRecord.Prog_Priority__c) 
           && !workPriorityMasterData.contains(woRecord.Prog_Priority__c.trim())){
            woRecord.Prog_Val_Message__c = String.isBlank(woRecord.Prog_Val_Message__c) 
                        ? System.Label.VM_WorkPriority 
                        : woRecord.Prog_Val_Message__c + '; \n' + System.Label.VM_WorkPriority;
            woRecord.Prog_Val_Outcome__c = 'Error';
        }
    }
    
    //#7 Function to validate if all the Quantity comma separated values provided is a number
    public static void validateQuantity(WorkOrder woRecord, String fieldName){
        //Loop over all the quantity values provided for a single job(WO) and check if it is a non-zero, positive integer
        String validationMessage;
        String fieldVal = (String)woRecord.get(fieldName);
        
        if(!String.isBlank(fieldVal)){
            
            Boolean qttyErrorIndicator = FALSE;
            
            List<String> quantityList = fieldVal.split(',');
            
            //Check if the quantity is a non zero, non negative integer
            for(String qtty : quantityList){
                qtty = qtty.trim();
                Pattern p = Pattern.compile('^[1-9]\\d*$');
                Matcher m = p.matcher(qtty);
                if(!m.matches()){
                    //Not a valid positive number(zero, negative or non-numeric) then set the boolean to true
                    qttyErrorIndicator = TRUE;
                    break;
                }
            }
            
            if(fieldName == 'Prog_Quantity__c'){
                validationMessage = System.Label.VM_Quantity;
            }else{
                validationMessage = System.Label.VM_ScopingQuantity;
            }
            
            if(qttyErrorIndicator){
                woRecord.Prog_Val_Message__c = String.isBlank(woRecord.Prog_Val_Message__c) 
                        ? validationMessage 
                        : woRecord.Prog_Val_Message__c + '; \n' + validationMessage;
                woRecord.Prog_Val_Outcome__c = 'Error';
            }
        }
    }
    
    //#8 Function to validate Start and End Date on WorkOrder
    public static void validateStartEndDate(WorkOrder woRecord){
        //To check if the Prog_Start_Date__c is prior to the Prog_End_Date__c and Start Date is not in Future
        
        if( woRecord.Prog_Start_Date__c == NULL || woRecord.Prog_End_Date__c == NULL){
            woRecord.Prog_Val_Message__c = String.isBlank(woRecord.Prog_Val_Message__c) 
                        ? System.Label.VM_StartDateEndDate 
                        : woRecord.Prog_Val_Message__c + '; \n' + System.Label.VM_StartDateEndDate;
            woRecord.Prog_Val_Outcome__c = 'Error';
            return;
        }
        
        if(woRecord.Prog_Start_Date__c > woRecord.Prog_End_Date__c || woRecord.Prog_Start_Date__c < Date.Today()){
            woRecord.Prog_Val_Message__c = String.isBlank(woRecord.Prog_Val_Message__c) 
                        ? System.Label.VM_StartDateEndDate 
                        : woRecord.Prog_Val_Message__c + '; \n' + System.Label.VM_StartDateEndDate;
            woRecord.Prog_Val_Outcome__c = 'Error';
        }
    }    
    
    //#9 Function to set Validation status as success if there are no validation errors
    public static void updateForSuccess(WorkOrder woRecord){
            if(woRecord.Prog_Val_Outcome__c != 'Error'){
				woRecord.Prog_Val_Message__c = '';
            	woRecord.Prog_Val_Outcome__c = 'Success';                
            }
    }
    
    //Helper Function to get the unique SoR codes to fetch data from SUI Service Catalogue in init method
    private static Set<String> getUniqueSORs(List<WorkOrder> woList){
        set<String> sorValues = new set<String>();
        
        for(WorkOrder woRecord : woList){
            if(String.isNotBlank(woRecord.Prog_SORs__c)){
                for(String sorValue : woRecord.Prog_SORs__c.split(',')){
                    sorValues.add(sorValue.trim());
                }
            }
        }
        return sorValues;
    }
    
    //Helper Function to count commma separated values in a given string
    private static Integer countCommaSeparatedValues(String stringValue){
        if(String.isBlank(stringValue)){
            return 0;
        }
        List<String> splitValues = stringValue.split(',');
        
        Integer count = 0;
        for(String sValue : splitValues){
            if(String.isNotBlank(sValue)){
                count++;
            }
        }
        return count;
    }
    
    //Helper Function to extract unique values in comma separated text field
    public static Set<String> extractValuesfromField(String fieldValue, Set<String> existingValues){
        if(String.isNotBlank(fieldValue)){
            for(String singleValue : fieldValue.split(',')){
                String trimmedValue = singleValue.trim();
                if(String.isNotBlank(trimmedValue)){
                    existingValues.add(trimmedValue);
                }
            }
        }
        return existingValues;
    }


    //------------------------------------ Validation of Programmed Work order with SST Reference----------------------

     /**
     * @description      This Method is used to validate survey using sst reference number
     * @param  woRecord  It required to get sst reference number 
     * @return           -          
     */
    public static Boolean validateSSTRef(WorkOrder woRecord){
        Boolean sstRefErrorIndicator = FALSE;
        List<Survey__c> surveyListcheck = new List<Survey__c>();
        system.debug(surveyLst);
        for(Survey__c item :surveyLst){
           if(item.Survey_Reference_Number__c==woRecord.Prog_SSTRef__c || item.Name== woRecord.Prog_SSTRef__c){
            surveyListcheck.add(item);
           }
        }

        //Validate the SST Reference number 
        if(surveyListcheck.size()==0){
            sstRefErrorIndicator = TRUE; 
        } 
        system.debug(woRecord.Prog_SSTRef__c);
        //Error Message for invalid survey
        if(sstRefErrorIndicator){
            woRecord.Prog_Val_Message__c = String.isBlank(woRecord.Prog_Val_Message__c) 
            ? System.Label.VM_SSTRef 
            : woRecord.Prog_Val_Message__c + '; \n' + System.Label.VM_SSTRef;
            woRecord.Prog_Val_Outcome__c = 'Error';
        }
        return sstRefErrorIndicator;
    }

     /**
     * @description      This Method is used to validate Defect code 
     * @param  woRecord  It required to get sst reference number 
     * @return           -          
     */
    public static void validateDefectcode(WorkOrder woRecord){
        String sstId=woRecord.Prog_SSTRef__c;
        Boolean sstdefectcodeErrorIndicator = FALSE;
        String sorsCode='';
        finalCodeMAP= new MAP<String,Defect__c>();
        for (String key : defectcodeMap.keySet()){
            String defectSurvey = defectcodeMap.get(key).Survey__r.Name;
            if(defectSurvey==sstId){
                finalCodeMAP.put(key,defectcodeMap.get(key));
            }
        }   
        List<String> defectCodeName = new List<String>();
        for(Defect__c item :defectlst){
            if(finalCodeMAP.containsKey(item.id)){
                defectCodeName.add(item.Defect_Code__c);
            }
        }
       //Validate the Defect code
        for(String defectcode : defectCodeName){
                sorsCode=sorsCode+''+defectcode+',';
                if(!serviceItemCodesDef.contains(defectcode) || defectcode==null || String.isBlank(defectcode)){
                    sstdefectcodeErrorIndicator = TRUE;
                    break;
                }        
        }
        String finalSors=sorsCode.substring(0,sorsCode.length()-1);
        system.debug(finalSors);
        //Error Message for invalid Defect code
        if(sstdefectcodeErrorIndicator){
            woRecord.Prog_Val_Message__c = String.isBlank(woRecord.Prog_Val_Message__c) 
            ? System.Label.VM_DefectCode 
            : woRecord.Prog_Val_Message__c + '; \n' + System.Label.VM_DefectCode;
            woRecord.Prog_Val_Outcome__c = 'Error';
        }
        else{
            woRecord.Prog_SORs__c=finalSors;
        }
    }
 
     /** 
     * @description      This Method is used to validate Defect Quantity 
     * @param  woRecord  It required to get sst reference number 
     * @return           -          
     */
    public static void validateDefectQuantity(WorkOrder woRecord){
        String sstId=woRecord.Prog_SSTRef__c;
        Boolean defectQtyErrorIndicator = False;
        String progQuantity='';
        List<String> defectQuantitylst = new List<String>();
        for (String key : finalCodeMAP.keySet()){
            defectQuantitylst.add(String.valueOf(finalCodeMAP.get(key).Defect_Quantity__c.format()));
        }   
        //Validate the Defect Quantity
        for(String qtty : defectQuantitylst){
                Pattern p = Pattern.compile('^[1-9]\\d*$');
                Matcher m = p.matcher(qtty);
                progQuantity= progQuantity+''+ qtty+',';
                if(!m.matches()||qtty==null || String.isBlank(qtty)){
                    defectQtyErrorIndicator = TRUE;
                    break;
                }
        }
        String finalQuantity=progQuantity.substring(0,progQuantity.length()-1);
        System.debug(finalQuantity);
        String validationMessage =System.Label.VM_DefectQuantity;
        //Error Message for invalid defect Quantity
        if(defectQtyErrorIndicator){
            woRecord.Prog_Val_Message__c = String.isBlank(woRecord.Prog_Val_Message__c) 
                    ? validationMessage 
                    : woRecord.Prog_Val_Message__c + '; \n' + validationMessage ;
            woRecord.Prog_Val_Outcome__c = 'Error';
        }
        else{
           
            woRecord.Prog_Quantity__c=finalQuantity;
        }
    }

     /**
     * @description      This Method is used to validate Defect Location value 
     * @param  woRecord  It required to get  sst reference num 
     * @return           -     -       
     */
    public static void validateDefectLocation(WorkOrder woRecord){
        String sstId=woRecord.Prog_SSTRef__c;
        Boolean locTypeErrorIndicator = FALSE;
        String locationType='';
        String finalLocation;
        List<String> finalLocataionList = new List<String>();
        system.debug(finalCodeMAP);
        for (String key : finalCodeMAP.keySet()){
            String locationUpper =finalCodeMAP.get(key).Location__c;
             if(locationTypeMasterDataDef.contains(finalCodeMAP.get(key).Location__c)||locationTypeMasterDataDef.contains(locationUpper.toUpperCase())){
                finalLocataionList.add(finalCodeMAP.get(key).Location__c);
             }
         } 
        system.debug(locationTypeMasterDataDef);

        if( finalLocataionList != NULL){
             for(String defectloc : finalLocataionList){
                locationType=locationType+''+defectloc+',';
                String defectLocUpper = defectloc.toUpperCase();
                system.debug(defectLocUpper);
                if((!locationTypeMasterDataDef.contains(defectloc) && !locationTypeMasterDataDef.contains(defectLocUpper)) || defectloc==null || String.isBlank(defectloc)){
                    locTypeErrorIndicator = TRUE;
                    break;         
                }        
            }
        }
        if(!String.isBlank(locationType)){
            finalLocation=locationType.substring(0,locationType.length()-1);
        }else{
            locTypeErrorIndicator = TRUE;
        }    
        System.debug(finalLocation);
        //Error Message for invalid defect Location
        if(locTypeErrorIndicator){
             woRecord.Prog_Val_Message__c = String.isBlank(woRecord.Prog_Val_Message__c) 
                         ? System.Label.VM_DefectLocation 
                         : woRecord.Prog_Val_Message__c + '; \n' + System.Label.VM_DefectLocation;
             woRecord.Prog_Val_Outcome__c = 'Error';
        }
        else{
            woRecord.Prog_LocationType__c=finalLocation;
        }
    }

    public static void validateDefectWorkClassification(WorkOrder woRecord){
        Boolean workClassifErrorIndicator = TRUE;
        List<String> woSoRValues;
        if(woRecord.Prog_SORs__c!=null && String.isNotBlank(woRecord.Prog_SORs__c)){
            woSoRValues = woRecord.Prog_SORs__c.split(',');
            for(String woSOR : woSoRValues){
                woSOR = woSOR.trim();
                system.debug(woSOR);
                if( defectWorkClassificationMasterData != NULL && defectWorkClassificationMasterData.containsKey(woSOR) && String.isNotBlank(defectWorkClassificationMasterData.get(woSOR)) ){
                    List<String> servCatalogueWorkClassif = defectWorkClassificationMasterData.get(woSOR).split(';');
                    if(String.isNotBlank(woRecord.Prog_Work_Classification__c) && servCatalogueWorkClassif.contains(woRecord.Prog_Work_Classification__c)){
                        workClassifErrorIndicator = FALSE;
                        break;
                    }
                }
            }
        }
        if(workClassifErrorIndicator){
            woRecord.Prog_Val_Message__c = String.isBlank(woRecord.Prog_Val_Message__c) 
                        ? System.Label.VM_WorkClassification 
                        : woRecord.Prog_Val_Message__c + '; \n' + System.Label.VM_WorkClassification;
            woRecord.Prog_Val_Outcome__c = 'Error';
        }
    }
}