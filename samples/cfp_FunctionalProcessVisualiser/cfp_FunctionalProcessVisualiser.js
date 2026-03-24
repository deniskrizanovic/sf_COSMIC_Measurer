/**
 * Created by dkrizanovic on 22/10/2024.
 */

import {LightningElement, api} from 'lwc'
import getSteps from '@salesforce/apex/cfp_getDataMovements.getSteps';

export default class CfpFunctionalProcessVisualiser extends LightningElement {

    results;
    @api recordId;
    fpName;
    numberOfSteps;

    coords = {
        lineXStart: 100,
        lineXEnd: 300,
        lineY: 100,
        textX: 100,
        sizeOfArrow: 7,
        textAnchor: 'middle',
        get lineYText() {
            return this.lineY + 5;
        },
        get leftSideEntryArrow() {
            return this.lineXEnd + ","
                + this.lineY + ","
                + (this.lineXEnd - this.sizeOfArrow) + ","
                + (this.lineY - this.sizeOfArrow) + ","
                + (this.lineXEnd - this.sizeOfArrow) + ","
                + (this.lineY + this.sizeOfArrow);
        },
        get leftSideExitArrow() {
            return this.lineXStart + ","
                + this.lineY + ","
                + (this.lineXStart + this.sizeOfArrow) + ","
                + (this.lineY - this.sizeOfArrow) + ","
                + (this.lineXStart + this.sizeOfArrow) + ","
                + (this.lineY + this.sizeOfArrow);
        },
        get rightSideEntryArrow() {

            return this.lineXEnd + ","
                + this.lineY + ","
                + (this.lineXEnd + this.sizeOfArrow) + ","
                + (this.lineY - this.sizeOfArrow) + ","
                + (this.lineXEnd + this.sizeOfArrow) + ","
                + (this.lineY + this.sizeOfArrow);
        },
        get rightSideExitArrow() {
            return this.lineXStart + ","
                + this.lineY + ","
                + (this.lineXStart - this.sizeOfArrow) + ","
                + (this.lineY - this.sizeOfArrow) + ","
                + (this.lineXStart - this.sizeOfArrow) + ","
                + (this.lineY + this.sizeOfArrow);
        }
    };



    get setLeftSideLine() {
        console.log('in left side line');
        this.coords.lineXStart = 50;
        this.coords.textX = 40;
        this.textAnchor = 'end';

    }

    get setRightSideLine() {
        console.log('in right side line');
        this.coords.lineXStart = 500;
        this.coords.textX = 510;
        this.textAnchor = 'start';
    }

    get setRightSideLineWithExtraLength(){
        this.setRightSideLine;
        this.coords.lineXStart = 550;
        this.coords.textX = 560;
    }

    get nextLine() {
        this.coords.lineY += 30;
    }

    get calculateLengthOfFunctionalProcess() {
        return this.numberOfSteps * 30 + 100;
    }

    connectedCallback() {

        getSteps({fpId: this.recordId})
            .then((result) => {
                if (result) {
                    console.log("getSteps():result");
                    console.log(JSON.stringify(result));
                    this.numberOfSteps = result.length;

                    this.results = result.map(item => {

                        this.fpName = item.cfp_FunctionalProcess__r.Name;
                        if (item.cfp_movementtype__c === 'E') {
                            item.isEntry = true;
                        }
                        if (item.cfp_movementtype__c === 'R') {
                            item.isRead = true;
                        }
                        if (item.cfp_movementtype__c === 'W') {
                            item.isWrite = true;
                        }
                        if (item.cfp_movementtype__c === 'X') {
                            item.isExit = true;
                        }
                        return item;
                    });
                }
            });
        console.log("after the map");
        console.log(JSON.stringify(this.results));
    }
}