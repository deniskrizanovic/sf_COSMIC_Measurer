/**
 * Application Log handling utility class.  
 * @author - Sauce Consulting
 * 
 */

 public without sharing class ApplicationLogHandler {
	
	/**Exception log list*/	
	private static list<Application_Log__c> lstException = new list<Application_Log__c>();

	/**Add exception in log list 
	* @param className - class name which cause exception
	* 	     methodName - method name which cause exception
	*		 ex - exception object 	
	*/
	public static void addLog(String className, String methodName, Exception ex){
	    Application_Log__c log = new Application_Log__c(
	        Class_Name__c = className,
	        Method_Name__c = methodName,
	        Error_Line__c = ex.getLineNumber(),
	        Error_Message__c = ex.getMessage(),
	        Stack_Trace__c = ex.getStackTraceString(),
            recordTypeId = Schema.SObjectType.Application_Log__c.getRecordTypeInfosByName().get('Salesforce').getRecordTypeId()
	    );
	    lstException.add(log); 
	}

	/**Add exception in log list 
	* @param className - class name which cause exception
	* 	     methodName - method name which cause exception
	*		 ex - exception object 	
	*		 errorSource - source of error
	*/
	public static void addLog(String className, String methodName, Exception ex, String errorSource){
	    Application_Log__c log = new Application_Log__c(
	        Class_Name__c = className,
	        Method_Name__c = methodName,
	        Error_Line__c = ex.getLineNumber(),
	        Error_Message__c = ex.getMessage(),
	        Stack_Trace__c = ex.getStackTraceString(),
			Error_Source__c = errorSource,
            recordTypeId = Schema.SObjectType.Application_Log__c.getRecordTypeInfosByName().get('Salesforce').getRecordTypeId()
	    );
	    lstException.add(log); 
	}

    /**Add exception in log list 
	* @param className - class name which cause exception
	* 	     methodName - method name which cause exception
	*		 message - custom message to diplay on UI to User 	
	*/
	public static void addCustomLog(String className, String methodName,String message){
	    Application_Log__c log = new Application_Log__c(
	        Class_Name__c = className,
	        Method_Name__c = methodName,
	        Error_Message__c = message,
            recordTypeId = Schema.SObjectType.Application_Log__c.getRecordTypeInfosByName().get('Salesforce').getRecordTypeId()
	    );
	    lstException.add(log); 
	}

	/**Clear log list*/
	public static void clear(){
		lstException.clear();
	}

	/**Save exception log in database*/
	public static void saveLog(){
		/**Insert exception records*/
	    if(!lstException.isEmpty())
	    {
	        upsert lstException; 
	    }
  	}
}