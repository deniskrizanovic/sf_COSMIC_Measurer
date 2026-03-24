/**
* ─────────────────────────────────────────────────────────────────────────────────────────────────┐
* A Utility called by object triggers to recalculate sharing for Comment__c records
* ──────────────────────────────────────────────────────────────────────────────────────────────────
* @author         Heidi Mack
* @modifiedBy     
* @version        1.0
* @created        10-03-2024
* @modified       YYYY-MM-DD
* @testClass      CommentSharingUtility_Test
* ──────────────────────────────────────────────────────────────────────────────────────────────────
* @changes
* ─────────────────────────────────────────────────────────────────────────────────────────────────┘
*/

public with sharing class CommentSharingUtility {

    //Main method
        //Build a map of Comments and the Contractor Public Groups to share them with
        //Delete existing Comment Share records
        //Create new Comment Share records
    public static void recalculate(String sourceObject, Set<Id> sourceIds){
        //Id sets for objects, sourceObject is populated with sourceIds, all others are blank
        Set<Id> commentIds = sourceObject == 'Comment__c' ? sourceIds : new Set<Id>();
        Set<Id> workOrderIds = sourceObject == 'WorkOrder' ? sourceIds : new Set<Id>();
        Set<Id> noticeIds = sourceObject == 'Notice__c' ? sourceIds : new Set<Id>();
        
        //Map of Comment Id to a set of Contractor Public Group Ids, can include null sets where no parents exist
            //Contractor Public Group Id is in field Account.Contractor_Portal_Public_Group__c
        Map<Id,Set<Id>> commentContractorMap = new Map<Id,Set<Id>>();

        //Map of Work Order Id to a set of Comment Ids, used to query Scoping Work Order details and add them to commentContractorMap
        Map<Id,Set<Id>> workOrderCommentMap = new Map<Id,Set<Id>>();

        //Master SOQL Query, build the commentContractorMap
            //Because all share records will be deleted, all Contractors must be queried by this search
            //Do not filter query by Visible to Contractors, we will need to delete Share records for those Comments
        for(Comment__c c : [SELECT Id, Visible_to_Contractor__c, 
                        Work_Order__c, Work_Order__r.Linked_Contractor__c, Work_Order__r.Linked_Contractor__r.Contractor_Portal_Public_Group__c,
                        Notice__c, Notice__r.Linked_Contractor__c, Notice__r.Linked_Contractor__r.Contractor_Portal_Public_Group__c
                        FROM Comment__c WHERE Id in :commentIds OR Work_Order__c in :workOrderIds OR NOtice__c in :noticeIds]){
            
            Set<Id> contractorGroupIds = new Set<Id>();
            //Comments will only be shared where they have been approved to be visibile to contractors.
            //If this checkbox field is false, add the empty set to the map to ensure existing Share records are deleted.
            if(c.Visible_to_Contractor__c == true){
                //get Work Order Contractor Public Group Id
                if(c.Work_Order__c != null && c.Work_Order__r.Linked_Contractor__c != null 
                    && c.Work_Order__r.Linked_Contractor__r.Contractor_Portal_Public_Group__c != null){
                        contractorGroupIds.add(Id.valueOf(c.Work_Order__r.Linked_Contractor__r.Contractor_Portal_Public_Group__c));
                }
                        
                //get Notice Contractor Public Group Id
                if(c.Notice__c != null && c.Notice__r.Linked_Contractor__c != null 
                    && c.Notice__r.Linked_Contractor__r.Contractor_Portal_Public_Group__c != null){
                        contractorGroupIds.add(Id.valueOf(c.Notice__r.Linked_Contractor__r.Contractor_Portal_Public_Group__c));
                }

                //Add Work Order Id and Comment Id to workOrderCommentMap for the Scoping Query
                if(c.Work_Order__c != null){
                    Set<Id> workOrderCommentIds = workOrderCommentMap.containsKey(c.Work_Order__c) ? workOrderCommentMap.get(c.Work_Order__c) : new Set<Id>();
                    workOrderCommentIds.add(c.Id);
                    workOrderCommentMap.put(c.Work_Order__c,workOrderCommentIds);
                }
            }
            commentContractorMap.put(c.id,contractorGroupIds);
        }
        
        if(workOrderCommentMap.keyset().size() > 0){
            //Scoping Contractors need to be queried separately
            for(WorkOrder wo : [SELECT Id, ParentWorkOrderId, Linked_Contractor__c, Linked_Contractor__r.Contractor_Portal_Public_Group__c 
                                        FROM WorkOrder WHERE ParentWorkOrderId in :workOrderCommentMap.keyset()]){
                //Add Contractor Portal Group Id to commentContractorMap
                if(wo.Linked_Contractor__c != null && wo.Linked_Contractor__r.Contractor_Portal_Public_Group__c != null){
                    for(Id i : workOrderCommentMap.get(wo.ParentWorkOrderId)){
                        Set<Id> contractorIds = commentContractorMap.get(i);
                        contractorIds.add(Id.valueOf(wo.Linked_Contractor__r.Contractor_Portal_Public_Group__c));
                        commentContractorMap.put(i,contractorIds);
                    }
                }
            }
        }
                
        //Delete existing Share Records
        deleteShares(commentContractorMap.keyset());

        //Create new Shares
        createShares(commentContractorMap);
    } 

    //Query existing Comment__Share records and delete them
    public static void deleteShares(Set<Id> commentIds){
        List<Comment__Share> commentShares = [SELECT Id, ParentId, RowCause FROM Comment__Share WHERE ParentId in :commentIds AND RowCause = 'Manual'];
        if (commentShares.size() > 0) delete commentShares;
    }

    //Create new Comment__Share records via ManageContractAreaRelatedObjectShare class
    public static void createShares(Map<Id,Set<Id>> commentContractorMap){
        List<ManageContractAreaRelatedObjectShare.SobjectShareParametersWrapper> shareWrappers = new List<ManageContractAreaRelatedObjectShare.SobjectShareParametersWrapper>();
        for(Id i : commentContractorMap.keyset()){
            for(Id j : commentContractorMap.get(i)){
                ManageContractAreaRelatedObjectShare.SobjectShareParametersWrapper shareWrapper = new ManageContractAreaRelatedObjectShare.SobjectShareParametersWrapper();
                shareWrapper.objectAPIName = 'Comment__c';
                shareWrapper.accessLevel = 'Read';
                shareWrapper.parentId = i;
                shareWrapper.userOrGroupId = j;
                shareWrappers.add(shareWrapper);
            }
        }
        //Calls future method to insert new object share records
        if(shareWrappers.size() > 0) ManageContractAreaRelatedObjectShare.createSobjectShareRecord(shareWrappers);    
    }

}