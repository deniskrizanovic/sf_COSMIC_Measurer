## 4 MAPPING PHASE.
> Manual: part-1-mm-principles-definitions-rules-v5-0-aug-2021



### 4.1 General – Mapping the FUR to the Generic Software Model.
> Manual: part-1-mm-principles-definitions-rules-v5-0-aug-2021

Figure 4.1 shows the steps of the process for mapping the FUR as in the available software
artefacts to the form required by the COSMIC Generic Software Model.
Figure 4.1 –The process of the COSMIC Mapping Phase.
4.2
Identification of functional processes.
RULE 10: Identification of functional processes.
Each functional process identified in the scope of the FSM shall:
a) be derived from at least one identifiable FUR,
b) be initiated by an Entry data movement from a functional user informing the functional
process that it has detected a triggering event,
c) comprise at least two data movements, namely always one Entry plus either an Exit or a
Write.
d) belongs to one, and only one layer,
e) be complete when a point of asynchronous timing is required to be reached according to
its FUR.
NOTE 1:  the COSMIC Group has subsequently clarified sub-clause e) above as the
equivalent of the following statement:  ‘the set of all data movements that is needed to meet
its FUR for all the possible responses to its triggering Entry’.
COSMIC Measurement Manual- version 5.0 – Part 1: Principles, Definitions & Rules                     Copyright © 2021
13
NOTE 2:  The Generic Software Model is a logical model. A functional process occurrence
may start processing before data has been entered e.g. when a human user clicks on a
menu to display a blank screed for data entry.
NOTE 3:  In a set of FUR, each event which causes a functional user to trigger a functional
process
-
cannot be sub-divided for that set of FUR,
-
has either happened or it has not happened.
4.3
Identification of objects of interest and data groups.
RULE 11: Identification of objects of interest and data groups.
Each data group identified in the scope of the FSM shall:
a) be unique and distinguishable through its unique collection of data attributes,
b) be directly related to one object of interest described in the software’s FUR.
NOTE 1:
An object of interest can be any physical thing, as well as any conceptual thing or
part of a conceptual thing in the world of a functional user.
NOTE 2:
Examples of 'thing' include, but are not limited to, software applications, humans,
sensors, or other hardware.
NOTE 3:
The term object of interest is used in order to avoid terms related to specific
software engineering methods. The term does not imply objects in the sense used in Object
Oriented methods. Similarly, the word Entity is avoided because of its use in Data Modelling.
NOTE 4:
Constants or variables which are internal to the functional process, or
intermediate results in a calculation, or data stored by a functional process resulting only form
the implementation, rather than the FUR, are not data groups.
4.4
Identification of data movements.
This step consists in identifying the data movements (Entry, Exit, Read and Write) of each
functional process. Figure 4.2 illustrates the overall relationship between the four types of data
movement, the functional process to which they belong and the boundary of the measured
software.
RULE 12: Identification of data movements.
Each functional process identified in 4.2 shall be partitioned into its component data
movements.
NOTE:
The COSMIC method defines a data movement type as a BFC.
COSMIC Measurement Manual- version 5.0 – Part 1: Principles, Definitions & Rules                     Copyright © 2021
14
Functional
process
Functional users:
• Humans
• Other software
• Hardware devices
Boundary
1 entering
data group
1 exiting
data group
1 data group
to be stored
1 retrieved
data group
Persistent
storage
Functional
Sub-processes
Entry
Exit
Read
Write
Figure 4.2 – The four types of data movement & their relationship with a functional process.
RULE 13: Functional Process – Single Entry.
For any one functional process, a single Entry data movement shall be identified and counted
for the entry of all data describing a single object of interest that the FUR require to be entered,
unless the FUR explicitly require data describing the same single object of interest to be entered
more than once in the same functional process.
RULE 14: Functional Process – Single Exit, Read or Write.
Similarly, a single Exit, Read or Write data movement shall be identified and counted for the
movement of all data describing a single object of interest that the FUR requires of that type (e.g.
Exit, Read or Write, respectively), unless the FUR explicitly require data describing the same
singe object of interest to be moved more than once in the same functional process by a data
movement of the same type (e.g. Exit, Read or Write, respectively).
RULE 15: Functional Process – Occurrences.
If a data movement of a particular type (Entry, Exit, Read or Write) occurs multiple times with
different data values when a functional process is executed, only one data movement of that
type shall be identified and counted in that functional process.
4.5
Classification of data movements.
RULE 16: Entry.
An Entry shall:
a) receive a single data group which originates from the functional user side of the
boundary,
b) account for all required formatting and presentation manipulations along with all
associated validations of the entered data attributes, to the extent that these data
manipulations do not involve another type of data movement.
NOTE:
An Entry accounts for all manipulations that might be required to validate
some entered codes or to obtain some associated descriptions. However, if one of more
Reads are required as part of the validation process, these are identified and counted as
separate Read data movements.
COSMIC Measurement Manual- version 5.0 – Part 1: Principles, Definitions & Rules                     Copyright © 2021
15
c) include any ‘request to receive the Entry data’ functionality, where it is unnecessary to
specify what data should be entered.
RULE 17: Exit.
An Exit shall:
a) send data attributes from a single data group to the functional user side of the boundary,
b) account for all required data formatting and presentation manipulations, including
processing required to send the data attributes to the functional user, to the extent that
these manipulations do not involve another type of data movement.
RULE 18: Read.
A Read shall:
a) retrieve a single data group from persistent storage.
b) account for all logical processing and⁄or mathematical computation needed to read the
data, to the extent that these manipulations do not involve another type of data
movement,
c) include any ‘request to read’ functionality.
RULE 19: Write.
A Write shall:
a) move data attributes from a single data group to persistent storage.
b) account for all logical processing and⁄or mathematical computation to create the data
attributes to be written, to the extent that these manipulations do not involve another type
of data movement.
RULE 20: Write – Delete.
A requirement to delete a data group from persistent storage shall be a single Write data
movement.
