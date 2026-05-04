## 3 MEASUREMENT STRATEGY PHASE.
> Manual: part-1-mm-principles-definitions-rules-v5-0-aug-2021

3.1
Deriving the measurement strategy from the software context model.
This section describes the key parameters that must be considered in the Measurement Strategy
phase before actually starting to measure. The sub-sections give the rules to help the Measurer
through the process of determining a measurement strategy, as shown in Figure 3.1.
COSMIC Measurement Manual- version 5.0 – Part 1: Principles, Definitions & Rules                     Copyright © 2021
10
Figure 3.1 - The process of determining a Measurement Strategy.
RULE 1: Measurement activities.
The determination of the COSMIC functional size shall involve all of the activities and rules
described in Sections 3.2 to 3.6.
3.2
Determination of the purpose and scope of the FSM.
RULE 2: Purpose and scope.
The purpose and the scope of the FSM shall be determined before commencing a particular
measurement exercise.
NOTE:  Once the purpose of the FSM has been determined, the process of determining the
scope(s) of the FSM, the functional users, the layers and the boundaries may require some
iterations.

### 3.3 Identification of the FUR.
> Manual: part-1-mm-principles-definitions-rules-v5-0-aug-2021

RULE 3: Identification of the FUR.
The FUR identified to be within the scope of the FSM shall be used as the exclusive source from
which the functional size of the software is to be measured.
NOTE:
The term ‘FUR’ means those functional user requirements that are completely
defined so that a COSMIC functional size measurement is possible.

### 3.4 Identification of the layers.
> Manual: part-1-mm-principles-definitions-rules-v5-0-aug-2021



#### 3.4.1 The scope of the FSM and layers
> Manual: part-1-mm-principles-definitions-rules-v5-0-aug-2021

Software may have components of its functionality that exist in different layers of the software’s
operating environment.
COSMIC Measurement Manual- version 5.0 – Part 1: Principles, Definitions & Rules                     Copyright © 2021
11
RULE 4: If required for the purpose of the measurement exercise, each such layer shall be
identified.
RULE 5: A single piece of software to be measured shall not have its scope defined to extend
over more than one layer.
NOTE 1:
FUR may state explicitly, may imply, or the measurer may infer, that the FUR
apply to software in different layers or to different peer items whose size must be measured
separately. Alternatively, the measurement analyst may be faced with sizing existing software
which appears to be in different layers or to consist of separate peer items. In both cases,
guidance is needed to help decide if the FUR of the software comprise one or more layers or
peer items.
NOTE 2:
Layer identification is an iterative activity. The exact identification of layers can be
refined as the measurement activity progresses.

#### 3.4.2 Characteristics of layers
> Manual: part-1-mm-principles-definitions-rules-v5-0-aug-2021

RULE 6: Characteristics of layers.
Layers identified within the scope of the FSM shall have the following characteristics:
a) Software in each layer shall deliver functionality to its functional users.
b) Software in a subordinate layer shall provide functional services to software in a layer
using its services.
c) Software that shares data with other software shall not be considered to be in different
layers if they identically interpret the data attributes that they share.

### 3.5 Identification of the functional users.
> Manual: part-1-mm-principles-definitions-rules-v5-0-aug-2021

RULE 7: Functional Users.
All functional users that trigger, provide information to, or receive information from functional
processes in the FUR of the software within the scope of the FSM shall be identified.
NOTE 1:
This rule above corrects an omission in ISO 19761. An amendment to the
standard is in preparation.
NOTE 2:
As persistent storage is on the software side of the boundary, it is not considered
to be a functional user of the software being measured.

### 3.6 Identification of software boundaries
> Manual: part-1-mm-principles-definitions-rules-v5-0-aug-2021

RULE – Identification of boundaries.
RULE 8: The boundary of each piece of software within each layer and in the scope of the FSM
shall be identified.
RULE 9: Once the boundaries have been identified, each FUR within the scope of the FSM shall
be allocated to a piece of software.
COSMIC Measurement Manual- version 5.0 – Part 1: Principles, Definitions & Rules                     Copyright © 2021
12
