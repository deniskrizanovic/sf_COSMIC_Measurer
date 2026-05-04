## 5 MEASUREMENT PHASE.
> Manual: part-1-mm-principles-definitions-rules-v5-0-aug-2021

5.1
The measurement phase process.
The general method for measuring a piece of software when its FUR have been expressed in
terms of the COSMIC Generic Software Model is summarized in Figure 5.1.
COSMIC Measurement Manual- version 5.0 – Part 1: Principles, Definitions & Rules                     Copyright © 2021
16
Figure 5.1 – The process of the COSMIC Measurement Phase.
5.2
Calculation of the functional size.
RULE 21: Size of a data movement.
A unit of measurement, 1 CFP1, shall be assigned to each data movement (Entry, Exit, Read or
Write) identified in each functional process.
RULE 22: Size of a functional process.
The results of 5.2, as applied to all identified data movements within the identified functional
process, shall be aggregated into a single functional size value for that functional process by:
a) multiplying the number of data movements of each type by its unit size,
b) totaling the sizes from step a) for each of the data movement types in the functional
process.
Size (functional process) = Σ size(Entries) + Σ size(Exits) + Σ size(Reads) +  Σ size(Writes).
RULE 23: Functional size of the identified FUR of each piece of software to be measured.
The size of each piece of software to be measured within a layer shall be obtained by
aggregating the size of the functional processes within the identified FUR for each piece of
software.
NOTE:
Within each identified layer, the aggregation function is fully scalable. Therefore a
sub-total can be generated for individual functional processes, individual software pieces or for
the whole layer, depending on the purpose and scope of the FSM.
RULE 24: Functional size of changes to the FUR.
Within each identified layer, the functional size of changes to the FUR within each piece of
software within the scope of the FSM shall be calculated by aggregating the sizes of the
corresponding impact data movement according to the following formula:
1The unit of measurement was known as a ‘Cfsu’ (COSMIC functional size unit) prior to v3.0 of COSMIC method.
COSMIC Measurement Manual- version 5.0 – Part 1: Principles, Definitions & Rules                     Copyright © 2021
17
Size (Changes to a piece of software) = Σ size (added data movements) +
Σ size (changed data movements) +
Σ size (deleted data movements)
summed over all functional processes for the piece of software.
NOTE:
A data movement is considered to be changed if any of the attributes of the data
group are changed, or if any changes are needed to the data manipulation associated with the
data movement.
