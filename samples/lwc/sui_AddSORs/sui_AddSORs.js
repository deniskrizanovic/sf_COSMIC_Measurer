import { LightningElement,api, wire , track } from 'lwc';
import save from "@salesforce/apex/SUI_AddSORController.save";
import saveSupplementaryWoli from "@salesforce/apex/SUI_AddSORController.saveSupplementaryWoli";
import fetchAllSORList from "@salesforce/apex/SUI_AddSORController.fetchAllSORList";
import fetchSOLRList from "@salesforce/apex/SUI_AddSORController.fetchSOLRList";
import getWorkOrderDetails from "@salesforce/apex/SUI_AddSORController.getWorkOrderDetails";
import updateComment from "@salesforce/apex/SUI_AddSORController.updateComments";
import fetchMetadataRecs from '@salesforce/apex/SUI_AddSORController.fetchMetadataRecs';
import fetchScopCompId from '@salesforce/apex/SUI_AddSORController.fetchScopCompId';

import checkIfEvidenceRequired from "@salesforce/apex/SUI_AddSORController.checkIfEvidenceRequired";
import LightningConfirm from 'lightning/confirm';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import SUI_ADDSOR_Subtitle from '@salesforce/label/c.SUI_ADDSOR_Subtitle';
import SUI_ADDSOR_Title from '@salesforce/label/c.SUI_ADDSOR_Title';
import SUI_ADDSupplementarySOR_Title from '@salesforce/label/c.SUI_ADDSupplementarySOR_Title';
import SUI_ADDSOR_Note from '@salesforce/label/c.SUI_ADDSOR_Note';
import SUI_ADDSOR_Search_Label from '@salesforce/label/c.SUI_ADDSOR_Search_Label';
import SUI_ADDSOR_Lookup_Label from '@salesforce/label/c.SUI_ADDSOR_Lookup_Label';
import SUI_ADDSORNoRecordHeading from '@salesforce/label/c.SUI_ADDSORNoRecordHeading';
import SUI_ADDSORNoRecordMessage from '@salesforce/label/c.SUI_ADDSORNoRecordMessage';
import SUI_ADDSupplementarySOR_SaveMessage from '@salesforce/label/c.SUI_ADDSupplementarySOR_SaveMessage';
import SUI_ADDSOR_SaveMessage from '@salesforce/label/c.SUI_ADDSOR_SaveMessage';
import SUI_ADDSOR_SaveLabel from '@salesforce/label/c.SUI_ADDSOR_SaveLabel';
import SUI_ADDSOR_LocationRequired from '@salesforce/label/c.SUI_Add_SOR_Location_Required';
import SUI_ADDSOR_QuantityNotValid from '@salesforce/label/c.SUI_ADDSOR_QuantityNotValid';
import SUI_ADDSOR_Page_Size from '@salesforce/label/c.SUI_ADDSOR_Page_Size';
import isPortalEnabled from '@salesforce/schema/User.IsPortalEnabled';
import { getRecord, getFieldValue } from 'lightning/uiRecordApi';
import userId from '@salesforce/user/Id';
import { registerListener, unregisterAllListeners } from 'c/pubsub';
import { CurrentPageReference } from 'lightning/navigation';
import getLocations from '@salesforce/apex/SUI_AddSORController.getLocations';


export default class Sui_AddSORs extends LightningElement {

    //Column Header with class values for respective Column
    headers = [{ header: 'Service Item Code', class: 'slds-is-resizable slds-is-sortable slds-cell_action-mod extra-medium-size' },
    { header: 'Description', class: 'slds-has-button-menu slds-is-resizable slds-is-sortable slds-cell_action-mod extra-medium-size' },
    { header: 'Component', class: 'slds-is-resizable slds-is-sortable slds-cell_action-mod small-size' },
    { header: 'Component Type', class: 'slds-is-resizable slds-is-sortable slds-cell_action-mod small-size' },
    { header: 'Sub Component', class: 'slds-is-resizable slds-is-sortable slds-cell_action-mod small-size' },
    { header: 'Quantity', class: 'slds-is-resizable slds-is-sortable slds-cell_action-mod extra-small-size' },
    { header: 'Location Type', class: 'slds-is-resizable slds-is-sortable slds-cell_action-mod medium-size' }
    ];

    @track searchKey = '';
    @track data = [];
    @track error;
    @track showLoader = false;
    @track isPortalEnabled = isPortalEnabled;
    @track isPortalUser;
    @track errorMessage;
    @track showOnlyError;

    componentWhereClause = 'RecordType.DeveloperName = \'SUI_Component\'';
    componentTypeWhereClause = 'RecordType.DeveloperName = \'SUI_Component_Type\'';
    subComponentWhereClause = 'RecordType.DeveloperName = \'SUI_Sub_Component\'';

    @track sorList = [];
    masterSorList;
    saveDraftValues = [];
    @track selectedRows = [];
    @track selectedRowsIds = [];
    @track editArray = [];
    @api recordId;
    @track workOrderDetails;

    //Filter 
    @track selectedComponent = '';
    @track selectedComponentType = '';
    @track selectedSubComponent = '';
    @track contractType = '';
    @track workOrderSubMilestoneStatus = '';
    @track supplementaryWorksFlag = false;
    @track isAllSorChecked = false;

    //Evidence
    @track isValidEvidence = false;
    @track evidenceComment;
    @track isEvidenceRequired = false;

    //location Mandatory
    @track locationRequiredMessage = SUI_ADDSOR_LocationRequired;
    @track quantityNotValidMessage = SUI_ADDSOR_QuantityNotValid;

    //Location, Quantity values and Checkbox status
    @track isButtondisable = true;
    @track quantityData = [];
    @track locationData = [];
    @track checkedRecords = [];
    @track selectedData = [];
    @track maxSelection = 3;
    @track addSORMetavalue;
    @track customClass = 'slds-truncate';
    @track disableComponentFlag = false;
    @track scopeData;
    @track scopeID;

    //Pagination
    @track allSelectedRows = []; //stored all selected Rows in datatable
    isPageChanged = false;
    showPreviousNext = true; //manage visibility of the show and previous button on page
    @track page = 1;
    @track startingRecord = 1;
    @track endingRecord = 0;
    @track pageSize = SUI_ADDSOR_Page_Size;
    @track totalRecountCount = 0;
    @track totalPage = 0;
    @track tempSorList =[];
  
    
    //Custom Labels 
    @track label = {
        SUI_ADDSOR_Title,
        SUI_ADDSOR_Subtitle,
        SUI_ADDSOR_Note,
        SUI_ADDSOR_Search_Label,
        SUI_ADDSOR_Lookup_Label,
        SUI_ADDSupplementarySOR_Title,
        SUI_ADDSORNoRecordMessage,
        SUI_ADDSORNoRecordHeading,
        SUI_ADDSupplementarySOR_SaveMessage,
        SUI_ADDSOR_SaveMessage,
        SUI_ADDSOR_SaveLabel
    };

    //Lookup setup for Location
    matchingInfo = {
    primaryField: { fieldPath: "Name" },
    };
    displayInfo = {
        additionalFields: ["Name"],
    };
    filter = {
        criteria: [
            {
                fieldPath: "SUI_Record_Type_Developer_Name__c",
                operator: "eq",
                value: "SUI_Location_Type",
            }
        ],
    };
    locationTypeOptions = [{label: 'A', value : 'A'}];


    @wire(CurrentPageReference) pageRef;
    @wire(getRecord, { recordId: userId, fields: [isPortalEnabled] })
    userData({ error, data }) {
        if (data) {
            this.isPortalUser = getFieldValue(data, isPortalEnabled);
            console.log('Is Portal User:', this.isPortalUser);
        } else if (error) {
            console.error('Error fetching user data:', error);
        }
    }

    connectedCallback() {
        console.log('The Current User ID is==>', this.recordId);
        registerListener('evidancecommentadded', this.handleEvidanceComment, this);

        registerListener('fileadded', this.handleEvidanceFileUpload, this);
        registerListener('validevidence', this.validateEvidence, this);

        this.fetchLocationTypes();
        this.editArray = [...Array(1000).keys()].map(key => ({ key, readOnly: true, value: null }))
        this.fetchScopeData();
        this.fetchWorkOrderInfo();
        this.fetchEvidenceStatus();

    }

    /*get componentClass(){
        return this.isPortalUser == true ? 'disabled-div' : 'enabled-div';
    }*/

    get isNoData() {
        return this.sorList.length > 0 ? false : true;
    }

    get isEdidenceVisible() {
        return (this.supplementaryWorksFlag == true && this.error == undefined && this.checkedRecords?.length > 0) ? true : false;
    }

    fetchLocationTypes(){
        let options = [];
        getLocations()
        .then((result) => {
            for(let i in result){
                options.push({label: result[i].Name, value : result[i].Id});
            }
            this.locationTypeOptions = options;

        })

    }

    handleEvidanceComment(event) {
        this.evidenceComment = event.evidenceComment;
        console.log('-- this.evidenceComment--', this.evidenceComment);
    }
    handleEvidanceFileUpload(event) {
        this.NumberOfEvidanceFiles = event.detail.numberOfFiles;
        console.log('-- this.NumberOfEvidanceFiles--', this.NumberOfEvidanceFiles);
    }

    validateEvidence(event) {
        this.isValidEvidence = event.isValid;
    }

    fetchEvidenceStatus() {
        checkIfEvidenceRequired()
            .then(result => {
                this.isEvidenceRequired = result;
                console.log('----isEvidenceRequired---', this.isEvidenceRequired);
                this.error = undefined;
            })
            .catch(error => {
                this.error = error;
                console.error(error);
            }).finally(() => {
                //this.showLoader = false;
            });;
    }

    fetchWorkOrderInfo() {
        this.showLoader=true;
        console.log('Before getWorkOrderDetails =====>');
        console.log('Record Id =====>' + this.recordId);
        getWorkOrderDetails({ workOrderId: this.recordId })
            .then(result => {
                this.workOrderDetails = result;
                this.selectedComponent = '';
                this.selectedComponentType = '';
                this.selectedSubComponent = '';
                let recordType = result?.SUI_Ref__r?.RecordType?.DeveloperName;
                //Check if WorkOrder SubMilestone is Commenced Work or Resume Work
                this.workOrderSubMilestoneStatus = result?.SUI_Sub_Milestone__c;
                console.log('The Work Order Status is===>'+this.workOrderSubMilestoneStatus);
                if(this.workOrderSubMilestoneStatus == 'Commenced Work' || this.workOrderSubMilestoneStatus == 'Resume Work'){
                    this.supplementaryWorksFlag = true;
                    
                }

               this.contractType = result.Contract_Type__c; 
                console.log('=====Work Order Info====',result);
                console.log('=====recordType====',result?.SUI_Ref__r?.RecordType?.DeveloperName);
                if (recordType == 'SUI_Component') {
                    console.log('====SUI_Component=====',result);
                    this.selectedComponent = result?.SUI_Ref__r?.SUI_Master_Component__c;
                }

                if (recordType == 'SUI_Component_Type') {
                    console.log('====SUI_Component_Type=====',result);
                    this.selectedComponent = result?.SUI_Ref__r?.SUI_Reference_Component__r?.SUI_Master_Component__c;
                    this.selectedComponentType = result?.SUI_Ref__r?.SUI_Master_Component_Type__c ;
                }

                if (recordType == 'SUI_Sub_Component') {
                    console.log('====SUI_Sub_Component=====', result);
                    this.selectedComponent = result.SUI_Ref__r?.SUI_Reference_Component_Type__r?.SUI_Reference_Component__r?.SUI_Master_Component__c;
                    this.selectedComponentType = result.SUI_Ref__r?.SUI_Reference_Component_Type__r?.SUI_Master_Component_Type__c;
                    this.selectedSubComponent = result?.SUI_Ref__r?.SUI_Master_Sub_Component__c;
                }
                this.showLoader=false;

            })
            .catch(error => {
                this.error = error;
                console.error('getWorkOrderDetails error' + error);
            }).finally(() => {
                console.log('Inside finally ===>');
                this.showLoader = false;
                if (this.workOrderDetails?.SUI_Record_Type_developer_Name__c == 'SUI_Scoping') {
                    this.disableComponentFlag = true;
                    this.selectedComponent = this.scopeID;
                    this.selectedComponentType = '';
                    this.selectedSubComponent = '';
                }
                //if(this.supplementaryWorksFlag == true || this.workOrderDetails?.SUI_Record_Type_developer_Name__c=='SUI_Scoping'){
                if (this.supplementaryWorksFlag == true) {
                    console.log('Fetching socping or supplimentary service catalouge items');
                    this.fetchSORList();
                } else {
                    console.log('Fetching maintenance service catalouge items');
                    this.fetchFilteredSORList();
                }

            });
        console.log('After getWorkOrderDetails =====>');
    }

    handleShowAllSOR(event) {
        this.isAllSorChecked = !this.isAllSorChecked;
        this.refresh();
    }

    handleComponentChange(event) {
        this.selectedComponent = event.detail.selectedRecord == undefined ? '' : event.detail.selectedRecord.Id;
        this.refresh();
    }

    handleComponentTypeChange(event) {
        this.selectedComponentType = event.detail.selectedRecord == undefined ? '' : event.detail.selectedRecord.Id;
        this.refresh();
    }

    handleSubComponentChange(event) {
        this.selectedSubComponent = event.detail.selectedRecord == undefined ? '' : event.detail.selectedRecord.Id;
        this.refresh();
    }

    setWrapCell() {
        if (this.customClass == 'slds-cell-wrap') {
            this.customClass = 'slds-truncate';
        }
        else {
            this.customClass = 'slds-cell-wrap';
        }
    }

    fetchFilteredSORList() {
        console.log('Inside fetchFilteredSORList');
        this.showLoader = true;
        this.showLoader = true;
        fetchSOLRList({
            workOrderId: this.recordId,
            componentId: this.selectedComponent,
            componentTypeId: this.selectedComponentType,
            subComponentId: this.selectedSubComponent,
            contractType: this.contractType
        })
            .then(result => {
                this.sorList = result;
                this.masterSorList = result;
                this.processRecords(this.sorList);
                this.displayRecordPerPage(1); 
                console.log('=====this.sorList====', this.sorList);
            })
            .catch(error => {
                console.error(error);
            }).finally(() => {
                this.showLoader = false;
            });
   
    }

    fetchSORList() {
        console.log('Inside fetchSORList');
        this.showLoader = true;
        fetchAllSORList({
            workOrderId: this.recordId,
            componentId: this.selectedComponent,
            componentTypeId: this.selectedComponentType,
            subComponentId: this.selectedSubComponent,
            contractType: this.contractType,
            isSupplementaryWorksFlag: this.supplementaryWorksFlag,
        })
            .then(result => {
                this.sorList = result;
                this.masterSorList = result;
                this.processRecords(this.sorList);
                this.displayRecordPerPage(1);
                console.log('=====this.AllList====', this.sorList);
            })
            .catch(error => {
                console.error(error);
                this.error = error;
            }).finally(() => {
                this.showLoader = false;
            });
    }


    //this method is used to refresh the list 
    refresh() {
        // Remove draft values
        this.saveDraftValues = [];
        this.selectedRowsIds = [];
        if (this.supplementaryWorksFlag == true) {
            this.fetchSORList();
        } else {
            this.fetchFilteredSORList();
        }
    }

    //Retrieve the Custom Metadata value of Max SOR number
    @wire(fetchMetadataRecs)
    metadatarecord(value) {
        const { data, error } = value;
        if (data) {
            this.addSORMetavalue = data;
            this.maxSelection = this.addSORMetavalue[0].SUI_Value__c;
        } else if (error) {
            this.error = error;
        }
    }

    //Fetch the Component Id of Scoping Component from Master Data
    fetchScopeData() {
        fetchScopCompId()
            .then(result => {
                this.scopeData = result;
                this.scopeID = this.scopeData[0]?.Id;
                this.error = undefined;
            })
            .catch(error => {
                this.error = error;
                console.error(error);
            }).finally(() => {
            });;
    }

    //Handle edit click to disable Read-Only of Quantity Input
    handleQuantityEditClick(event) {
        let datasetId = event.target.dataset.id;
        this.template.querySelector(`*[data-id="${datasetId}"][data-type="Quantity"]`).readOnly = false;
        this.template.querySelector(`*[data-id="${datasetId}"][data-type="Quantity"]`).focus();
    }

    //make the input cell readonly after releasing focus of the cell
    handleQuantityReadOnly(event) {
        let datasetId = event.target.dataset.id;
        this.template.querySelector(`*[data-id="${datasetId}"][data-type="Quantity"]`).readOnly = true;
    }

    //Handle the input of Quantity 
    handleQtyInput(event) {
        //event.target.readOnly = true;
        //Manage the Checkbox on Quantity entry
        let datasetId = event.target.dataset.id;
        const indexlocation = this.locationData.findIndex(record => record.Id === datasetId);

        const input = event.target;
        const value = parseFloat(input.value);
        this.errorMessage = this.template.querySelector(`.error-message[data-id="${datasetId}"]`);
        
        if (value < 0) {
            this.errorMessage.style.display = 'block';
            //return;
        } else {
            this.errorMessage.style.display = 'none';
        }
    

        if ((event.target.value == null || event.target.value == '') && indexlocation != -1) {
            event.target.value = 1;
        }

        let checkSelector = this.template.querySelector(`*[data-id="${datasetId}"][data-type="SelectionCheckbox"]`);
        const indexLoc = this.locationData.findIndex(record => record.Id === datasetId);

        ((event.target.value != null || event.target.value != '')) ? checkSelector.checked = true : '';
        ((event.target.value == null || event.target.value == '') && (indexLoc == -1)) ? checkSelector.checked = false : '';
        //store the Quantity Input
        const index = this.quantityData.findIndex(record => record.Id === datasetId);
        if (index !== -1 && event.target.value != '') {
            this.quantityData.splice(index, 1);
            this.quantityData.push({ Id: event.target.dataset.id, quantity: event.target.value });
        } else if (index !== -1 && (event.target.value == null || event.target.value == '')) {
            this.quantityData.splice(index, 1);
        } else {
            this.quantityData.push({ Id: event.target.dataset.id, quantity: event.target.value });
        }
        this.manageCheckboxQtyLoc(checkSelector, event.target.dataset.id);
    }

    //Manage the scenario- if checkbox is unchecked and there is input to quantity or location
    manageCheckboxQtyLoc(chceckSelector, eID) {
        const indexLoc = this.locationData.findIndex(record => record.Id === eID);
        const indexQty = this.quantityData.findIndex(record => record.Id === eID);

        // const indexQty = this.quantityData.findIndex(record => record.Id === chceckSelector.value);
        const index = this.checkedRecords.findIndex(record => record.Id === chceckSelector.value);

        if (index != -1 && chceckSelector.checked == false) {
            this.checkedRecords.splice(index, 1);
        } else if (index == -1 && this.checkedRecords.length < this.maxSelection && chceckSelector.checked) {
            this.checkedRecords.push({ Id: chceckSelector.value, checked: chceckSelector.checked });
        } else if (this.checkedRecords.length > this.maxSelection) {
            const evt = new ShowToastEvent({
                title: 'Warning',
                message: 'You can add a maximum of ' + this.maxSelection + ' records in a single transaction. Please complete current transaction and initiate a new one for additional entries.!!',
                variant: 'error',
                mode: 'dismissable',
            });
            this.dispatchEvent(evt);
            chceckSelector.checked = false;
        }
        this.isButtondisable = (this.checkedRecords.length > 0 ? false : true);
    }

    //handle the Location input for the SOR
    handleLocationInput(event) {
        console.log(JSON.stringify(event.detail));
        let datasetId = event.detail.id;
        let checkSelector = this.template.querySelector(`*[data-id="${datasetId}"][data-type="SelectionCheckbox"]`);
        let QuantityCell = this.template.querySelector(`*[data-id="${datasetId}"][data-type="Quantity"]`);
        if ((QuantityCell.value == null || QuantityCell.value == '')) {
            QuantityCell.value = 1;
            const index = this.quantityData.findIndex(record => record.Id === QuantityCell.dataset.id);
            if (index !== -1) {
                this.quantityData.splice(index, 1);
                this.quantityData.push({ Id: QuantityCell.dataset.id, quantity: QuantityCell.value });
            } else {
                this.quantityData.push({ Id: QuantityCell.dataset.id, quantity: QuantityCell.value });
            }
        }

        const indexQty = this.quantityData.findIndex(record => record.Id === datasetId);
        (event.detail.recordId != null || event.detail.recordId != '') ? checkSelector.checked = true : '';
        ((event.detail.recordId == null || event.detail.recordId == '') && indexQty == -1) ? checkSelector.checked = false : '';
        const index = this.locationData.findIndex(record => record.Id === datasetId);
        if (index !== -1 && event.detail.recordId != null) {
            this.locationData.splice(index, 1);
            this.locationData.push({ Id: datasetId, location: event.detail.recordId });
        } else if (index !== -1 && (event.detail.recordId == null || event.detail.recordId == '')) {
            this.locationData.splice(index, 1);
        } else {
            this.locationData.push({ Id: datasetId, location: event.detail.recordId });
        }
        this.manageCheckboxQtyLoc(checkSelector, event.detail.id);
    }

    //Handle the scenario while check box from header row is selected
    handleAllCheck(event) {
        let allcheckboxes = this.template.querySelectorAll(".selectionCheckbox");
        let allQuantities = this.template.querySelectorAll(".quantityInput");
        let allLocationInput = this.template.querySelectorAll(".locationInput");
        if (allcheckboxes.length < this.maxSelection) {
            if (event.target.checked == true) {
                allcheckboxes.forEach(item => {
                    item.checked = (event.target.checked == true ? true : false);
                    this.manageCheckboxQtyLoc(item);
                });
                allQuantities.forEach(item => {
                    item.value = 1;
                    const index = this.quantityData.findIndex(record => record.Id === item.name);
                    if (index !== -1) {
                        this.quantityData.splice(index, 1);
                        this.quantityData.push({ Id: item.name, quantity: item.value });
                    } else {
                        this.quantityData.push({ Id: item.name, quantity: item.value });
                    }
                });
            } else {
                this.handleCancel();
            }
        } else {
            const evt = new ShowToastEvent({
                title: 'Warning',
                message: 'You can add a maximum of ' + this.maxSelection + ' records in a single transaction. Please complete current transaction and initiate a new one for additional entries.!!',
                variant: 'error',
                mode: 'dismissable',
            });
            this.dispatchEvent(evt);
            event.target.checked = false;
        }
    }

     //handles the selection of checkboxes
    handlecheck(event) {
        //Manage the scenario when Record is selected without Quantity
        let datasetId = event.target.dataset.id;
        let QuantityCell = this.template.querySelector(`*[data-id="${datasetId}"][data-type="Quantity"]`);
        let locationCell = this.template.querySelector(`*[data-id="${datasetId}"][data-type="LocationType"]`);
        if ((QuantityCell.value == null || QuantityCell.value == '') && event.target.checked == true && this.checkedRecords.length < this.maxSelection) {
            QuantityCell.value = 1;
            const index = this.quantityData.findIndex(record => record.Id === QuantityCell.dataset.id);
            if (index !== -1) {
                this.quantityData.splice(index, 1);
                this.quantityData.push({ Id: QuantityCell.dataset.id, quantity: QuantityCell.value });
            } else {
                this.quantityData.push({ Id: QuantityCell.dataset.id, quantity: QuantityCell.value });
            }
        }
        else if (event.target.checked == false) {
           QuantityCell.value = 1;
            const index = this.quantityData.findIndex(record => record.Id === QuantityCell.dataset.id);
            this.quantityData.splice(index, 1);
            QuantityCell.value = '';
            
            locationCell.required=false;
            window.setTimeout(() => {
                locationCell.clearSelection();
                locationCell.reportValidity();
                locationCell.required=true;
            }, 200);
            if(locationCell.value !=null && locationCell.value !=undefined && locationCell.value !=''){
                const indexlocation = this.locationData.findIndex(record => record.Id === locationCell.dataset.id);
                this.locationData.splice(indexlocation, 1);
            }
    
        }

        // Stores the selected Records
        const index = this.checkedRecords.findIndex(record => record.Id === event.target.value);
        if (index !== -1) {
            this.checkedRecords.splice(index, 1);
        } else if (this.checkedRecords.length < this.maxSelection) {
            this.checkedRecords.push({ Id: event.target.value, checked: event.target.checked });
        } else {
            const evt = new ShowToastEvent({
                title: 'Warning',
                message: 'You can add a maximum of ' + this.maxSelection + ' records in a single transaction. Please complete current transaction and initiate a new one for additional entries.!!',
                variant: 'error',
                mode: 'dismissable',
            });
            this.dispatchEvent(evt);
            event.target.checked = false;
        }
        //Manage Button visibility based on Record selection
        this.isButtondisable = (this.checkedRecords.length > 0 ? false : true);
    }

    //Create Final List of the selected records to process the save operation
    handlefinalSelection() {
        const mergedData = this.checkedRecords.map(checkedRecord => {
            const quantityRecord = this.quantityData.find(qty => qty.Id === checkedRecord.Id);
            const locationRecord = this.locationData.find(loc => loc.Id === checkedRecord.Id);
            return {
                ...checkedRecord,
                quantity: quantityRecord ? quantityRecord.quantity : null,
                location: locationRecord ? locationRecord.location : null
            };
        });
        this.selectedData = [...mergedData];
        this.sorList.forEach(sor => {
            this.selectedData.forEach(item => {
                if (item.Id == sor.Id) {
                    sor.quantity = (sor.quantity == undefined ? 1 : item.quantity);
                }
            });
        });
   }

    //handles the SOR Save process to add the SOR and to create the work order line item
    async handleSave(event) {
        this.handlefinalSelection();
        const requiredFields = this.template.querySelectorAll('c-sui_searchable-combobox');
        const allcheckboxes = this.template.querySelectorAll(".selectionCheckbox");
        const selectedCheck = Array.from(allcheckboxes).filter(checkbox => checkbox.checked !== false);
        selectedCheck.forEach(field => {
            let datasetId = field.dataset.id;
            let locfield = this.template.querySelector(`*[data-id="${datasetId}"][data-type="LocationType"]`);
            locfield.reportValidity();
        });
      
        for (let item = 0; item < this.selectedData.length; item++) {
             if (!(this.selectedData[item].location)) {
                const result = await LightningConfirm.open({
                    message: this.locationRequiredMessage,
                    label: 'Location Type Missing',
                    theme: 'Error',
                });
               return;
            }

            //Check for negative quantity
            if ((this.selectedData[item].quantity < 0 || this.selectedData[item].quantity == null)) {
                const result = await LightningConfirm.open({
                    message: this.quantityNotValidMessage,
                    label: 'Quantity is not valid',
                    theme: 'Error',
                });
               return;
            }
        }

        this.showLoader = true;
        //Check if evidance is required and files or comment are not added 
        let comp = this.template.querySelector("c-sui_-upload-evidence");
        if (comp) {
            if (this.isEvidenceRequired == true) {
                comp?.validate();
            }
            //if evidance is not valid show message to add the file or comment
            if (this.isEvidenceRequired == true && this.isValidEvidence == false) {
                this.showLoader = false;
                return;
            }
        }
        const result = await LightningConfirm.open({
            message: this.supplementaryWorksFlag == true ? this.label.SUI_ADDSupplementarySOR_SaveMessage : this.label.SUI_ADDSOR_SaveMessage,
            label: this.label.SUI_ADDSOR_SaveLabel,
            theme:'warning',
        });
        if (result) {
          //Update the comment on the work order if any 
            if (this.evidenceComment != '' && this.evidenceComment != undefined) {
                await updateComment({ workOrderId: this.recordId ,comment: this.evidenceComment })
                    .then(result => {
                       // alert('comment updated successfully on the work order');
                    })
                    .catch(error => {
                        this.error = error;
                        console.error(error);
                    });
            }
            try {
                //Save Evidence
                await comp?.saveEvidence();
            } catch(error) { 
                this.error = error;
                return;
            } finally {
                this.showLoader = false;
            };
            this.showLoader = true;
            // Save the selected SORs as Work Order Line Items
            if (this.supplementaryWorksFlag == true) {
                setTimeout(async () => {
                    console.log('Delayed action after 4 seconds');
                    await saveSupplementaryWoli({ selectedServiceCatalougeJSONString: JSON.stringify(this.selectedData), workOrderId: this.recordId })
                        .then(result => {
                            this.refresh(); // Refresh the data table after saving
                            this.showLoader = true;
                            const evt = new ShowToastEvent({
                                title: 'SUCCESS',
                                message: 'SORs added successfully!!',
                                variant: 'success',
                                mode: 'dismissable',
                            });
                            this.dispatchEvent(evt);
                            comp?.resetEvidence();
                            this.isPortalUser == true ? location.reload() : '';
                            //  location.reload();
                        }).catch(error => {
                            this.showOnlyError=true;
                            this.error = error;
                            console.error(error);
                            return;
                        })
                        .finally(() => {
                            this.showLoader = false;
                        });
                }, 3200);
            } else {
                await save({ selectedServiceCatalougeJSONString: JSON.stringify(this.selectedData), workOrderId: this.recordId })
                    .then(result => {
                        const evt = new ShowToastEvent({
                            title: 'SUCCESS',
                            message: 'SORs added successfully!!',
                            variant: 'success',
                            mode: 'dismissable',
                        });
                        this.dispatchEvent(evt);
                        comp?.resetEvidence();
                        this.isPortalUser == true ?  location.reload() : '';
                      //  location.reload();
                    }).catch(error => {
                        this.showOnlyError=true;
                        this.error = error;
                        console.error(error);
                        return;
                    })
                    .finally(() => {
                        this.showLoader = false;
                    });
            }
        } else {
            // If the user cancels the confirmation dialog
            this.showLoader = false;
        }

        if (this.supplementaryWorksFlag != true) {
            this.handleCancel();
            this.fetchFilteredSORList();
        } else {
            this.handleCancel();
            this.fetchSORList();
        }
    }

    //handle the cancel button functionality
    handleCancel() {
        this.checkedRecords = [];
        this.quantityData = [];
        this.locationData = [];
        this.isButtondisable = true;
        let headercheck = this.template.querySelectorAll(".headerCheckbox");
        headercheck.forEach(item => {
            item.checked = false;
        });
        let allcheckboxes = this.template.querySelectorAll(".selectionCheckbox");
        allcheckboxes.forEach(item => {
            item.checked = false;
        });
        let allQuantityInput = this.template.querySelectorAll(".quantityInput");
        allQuantityInput.forEach(item => {
            item.value = null;
        });
        let allLocationInput = this.template.querySelectorAll("c-sui_searchable-combobox");
        allLocationInput.forEach(item => {
           // item.clearSelection();
            item.clearSelection();
            item.required=false;
            window.setTimeout(() => {
                item.reportValidity();
                item.required=true;
            }, 200);
        });
    }

    //---------------------------------Pagination changes----------------------
 
    // process the records with respect to page size
    processRecords(data) {
        this.totalRecountCount = data.length;
        this.showPreviousNext = (this.totalRecountCount > this.pageSize) ? true : false;
        this.totalPage = Math.ceil(this.totalRecountCount / this.pageSize);
        this.tempSorList = this.sorList.slice(0, this.pageSize);
        this.endingRecord = this.pageSize;
    }

    //Method to displays records page by page
    displayRecordPerPage(page) {
        this.startingRecord = ((page - 1) * this.pageSize);
        this.endingRecord = (this.pageSize * page);
        this.endingRecord = (this.endingRecord > this.totalRecountCount) ? this.totalRecountCount : this.endingRecord;
        this.tempSorList = this.sorList.slice(this.startingRecord, this.endingRecord);
        this.startingRecord = this.startingRecord + 1;
    }

     //On previous button click this method will be called
     previousHandler() {
        this.isPageChanged = true;
        if (this.page > 1) {
            this.page = this.page - 1; //decrease page by 1
            this.displayRecordPerPage(this.page);
        }
        this.handlefinalSelection();
        this.maintainSelection();
       
         setTimeout(()=> {
            const allcheckboxes = this.template.querySelectorAll(".selectionCheckbox");
            const selectedCheck = Array.from(allcheckboxes).filter(checkbox => checkbox.checked !== false);
            selectedCheck.forEach(field => {
                let datasetId = field.dataset.id;
                let locfield = this.template.querySelector(`*[data-id="${datasetId}"][data-type="LocationType"]`);
                locfield.reportValidity();
            });
        },300);
    }
    //On next button click this method will be called
    nextHandler() {
        this.isPageChanged = true;
        if ((this.page < this.totalPage) && this.page !== this.totalPage) {
            this.page = this.page + 1; //increase page by 1
            this.displayRecordPerPage(this.page);
        }
          this.handlefinalSelection();
          this.maintainSelection();
          setTimeout(()=> {
                const allcheckboxes = this.template.querySelectorAll(".selectionCheckbox");
                const selectedCheck = Array.from(allcheckboxes).filter(checkbox => checkbox.checked !== false);
                selectedCheck.forEach(field => {
                    let datasetId = field.dataset.id;
                    let locfield = this.template.querySelector(`*[data-id="${datasetId}"][data-type="LocationType"]`);
                    locfield.reportValidity();
                });
         },300);
   }

   //Maintains the selection of Check-box while navigating from one page to another
  maintainSelection(){
    setTimeout(()=> {
    let selectedData = this.selectedData.map(record => record.Id);
    if(selectedData.length > 0){
            this.template.querySelectorAll('.selectionCheckbox').forEach(element => {
                console.log(element);
                if(selectedData.includes(element.value)){
                    element.checked = true;
                }
                else{
                    element.checked = false;
                }
            });
            this.template.querySelectorAll('.quantityInput').forEach(element => {
                console.log(element);
                if(selectedData.includes(element.dataset.id)){
                    let index = selectedData.indexOf(element.dataset.id);
                    element.value=this.selectedData[index].quantity;
                }
             });
            this.template.querySelectorAll('c-sui_searchable-combobox').forEach(element => {
                console.log(element);
                if(selectedData.includes(element.dataset.id)){
                    let index = selectedData.indexOf(element.dataset.id);
                    const selectedLType = Array.from( this.locationTypeOptions).filter(lType=> lType.value == this.selectedData[index].location);
                    element.value=selectedLType[0].label;
                    element.readonly=true;
                }
            });
        }
     }, 300);
    }
   
    
    // Manage the Global search
     handleSearchChange(event) {
        this.searchKey = event.target.value;
        let data=[];
        console.log('----this.searchKey-----', this.searchKey);
        let lowercaseSearchKey = '' + this.searchKey?.toLowerCase();
        data = this.masterSorList.filter(record => {
            return (record.Name?.toLowerCase().includes(lowercaseSearchKey) ||
                record.SUI_Service_Item_Code?.toLowerCase().includes(lowercaseSearchKey) ||
                //record.SUI_Service_Item_Short_Description?.toLowerCase().includes(this.searchKey?.toLowerCase()) || 
                record.SUI_Service_Item_Long_Description?.toLowerCase().includes(lowercaseSearchKey) ||
                record.component?.toLowerCase().includes(lowercaseSearchKey) ||
                record.componentType?.toLowerCase().includes(lowercaseSearchKey) ||
                record.subComponent?.toLowerCase().includes(lowercaseSearchKey));
        });
        this.sorList = data;
        this.processRecords(data);
        this.displayRecordPerPage(1);
        this.maintainSelection();
    }
     
}