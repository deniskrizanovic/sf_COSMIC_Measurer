## 3 THE MAPPING PHASE.
> Manual: part-2-mm-guidelines-v5-0-sep-2024

Functional processes are composed of sub-processes that move data (‘data movements’)
and optionally, may manipulate data (‘data manipulation’).

### 3.1 Mapping the FUR to the Generic Software Model.
> Manual: part-2-mm-guidelines-v5-0-sep-2024

Figure 3.1 shows the steps for mapping the FUR in the available software artefacts to the
form required by the COSMIC Generic Software Model.
Figure 3.1 –The process of the COSMIC Mapping Phase.
Several guidelines are available that describe how to map from various data-analysis and
requirements-determination methods, used in different domains to the concepts of the
COSMIC method:
•
Guideline for Sizing Business Application Software,
•
Guideline for Sizing Data Warehouse Application Software,
•
Guideline for Sizing Service-Oriented Architecture Software, and
•
Guideline for Sizing Real-time Software.
For the business and real-time domains there are also Quick Reference Guides available
that give an overview of the process in a few pages.
3.2
Identifying functional processes.
The first step of the Measurement Phase is to identify the set of functional processes of the
piece of software to be measured, from its FUR.
The relationships between a triggering event, the functional user and the Entry data
movement that triggers a functional process being measured are presented in Figure 3.2
where: a triggering event causes a functional user to generate a data group that is moved by
the triggering Entry of a functional process to start the functional process.
COSMIC Measurement Manual -  version 5.0 – Part 2: Guidelines                      Copyright © 2024
11
Triggering
Event
causes
a
that is moved
into a FP by
the FP’s
Triggering
Entry
Boundary
Functional
Process
Functional
User
to
generate
a
Data
group
Figure 3.2 – Relationships between a triggering event, a functional user & a functional process.
NOTE:
For ease of reading, the reference to the data group is omitted when stating
that a functional user initiates a triggering Entry that starts a functional process, or even more
simply that a functional user initiates a functional process.
Guidance on Rule 10: Identification of Functional Processes
The process of identifying functional processes, after the functional users have been
identified, given the FUR for the software being measured follows the chain of Figure 3.2:
1. Identify the separate events in the world of the functional users that the software being
measured must respond to – the ‘triggering events’
NOTE: Triggering events can be identified in state diagrams and in entity life-cycle
diagrams, since some state transitions and entity life-cycle transitions correspond to
triggering events to which the software must react.
2. Identify which functional user(s) of the software may respond to each triggering event;
3. Identify the data group(s) (i.e. the triggering Entry or Entries) that each functional user
may initiate in response to the event;
4. Identify the functional process started by each triggering Entry.
Use the following checks to ensure that candidate functional processes (FP) have been
properly identified:
1. Do all the identified FPs of the piece of software measured reside in the same layer?
2. Are all the identified FPs comprised of an Entry and at least 1 Write or Exit data
movement?
3.3
Identification of data groups.

#### 3.3.1 Identification of data groups.
> Manual: part-2-mm-guidelines-v5-0-sep-2024

Having identified the functional processes, the next step is to identify their data movements.
The following guidance assists in the identification of data groups and hence objects of
interest particularly in the output of functional processes.
GUIDANCE on Rule 11: Identifying different data groups moved in the same one
functional process.
For all the data attributes appearing in an Entry-Exit-Read-Write of a functional process:
a) sets of data attributes that have different frequencies of occurrence describe different
objects of interest;
b) sets of data attributes that have the same frequency of occurrence but different
identifying key attribute(s) describe different objects of interest;
c)
all the data attributes in a set resulting from applying parts a) and b) of this guidance
belong to the same one data group, unless the FUR specify that there may be more than
COSMIC Measurement Manual -  version 5.0 – Part 2: Guidelines                      Copyright © 2024
12
one data group describing the same object of interest  (see the Guidance on Rules 13
and 14 – Data Movements Uniqueness, cases b) and c)).
NOTE 1:
A functional user of the software being measured may be the object of interest
of a data group sent or received by the functional user.
NOTE 2:
In theory, a data group might contain only one data attribute if this is all that is
required, from the perspective of the FURs, to describe the object of interest. In practice,
such cases occur commonly in real-time application software (e.g. the data group entered to
convey the tick of a real-time clock or the entry of the state of a sensor); they are less
common in business application software.
NOTE 3:
There is nothing absolute about an object of interest, i.e. identify the objects of
interest per functional process. A ‘thing’ may be an object ‘of interest’ to a functional user via
one or more functional processes, but not be an object ‘of interest’ to another functional user
via other functional processes, even in the same software being measured.
The origin of a data group can be of many forms, e.g.:
a) A physical record structure on a hardware storage device (file, database table, ROM
memory, etc.).
b) A physical structure within the computer’s volatile memory (data structure allocated
dynamically or through a pre-allocated block of memory space).
c)
A clustered presentation of functionally-related data attributes on an input/output device
(display screen, printed report, control panel display, etc.).
d) A message in transmission between a device and a computer, or over a network, etc.

#### 3.3.2 About the identification of objects of interest and data groups.
> Manual: part-2-mm-guidelines-v5-0-sep-2024

The definition and principles of objects of interest and of data groups are intentionally broad
in order to be applicable to the widest possible range of software: this sometimes results in it
being difficult to apply the definition and principles when measuring a specific piece of
software.  See Part 3 for examples to assist in the application of the principles to specific
cases
When faced with a need to analyze a group of data attributes that is moved in or out of a
functional process or is moved by a functional process to or from persistent storage, it is
critically important to decide if the attributes all convey data about a single ‘object of interest’,
since it is the latter that determine the number of separate ‘data groups’ as defined by the
COSMIC method that will be moved by data movements.
For instance, if the data attributes to be input to a functional process are attributes of three
separate objects of interest, then three separate ‘Entry’ data movements must be identified.
Deciding on the number of data groups can be difficult when analyzing the output of a
functional process of a business application which may include:
•
multiple data groups, each describing a different object of interest, e.g. a report showing
totals at various levels of aggregation;
•
the results of enquiries where the output will vary depending on the input;
•
data groups that may even be unrelated to each other, e.g. an invoice which includes an
advertisement for an unrelated service.
When analyzing complex output, e.g. reports with data describing several objects of interest,
consider each separate candidate data group as if it were output by one separate functional
process. Each of the data group types identified this way must also be distinguished and
counted when measuring the complex report.
COSMIC Measurement Manual -  version 5.0 – Part 2: Guidelines                      Copyright © 2024
13

#### 3.3.3 Data or groups of data that are not candidates for data groups.
> Manual: part-2-mm-guidelines-v5-0-sep-2024

Any data appearing on input or output screens or reports that are not related to an object of
interest to a functional user should not be identified as indicating a data group.
The COSMIC Generic Software Model assumes that all manipulation of data within a
functional process is associated with the four data movement types. Hence no data groups
may be identified arising from data manipulation within a functional process in addition to the
data groups moved by the Entries, Exits, Reads and Writes of the functional process.

#### 3.3.4 Identification of data attributes (optional).
> Manual: part-2-mm-guidelines-v5-0-sep-2024

In the COSMIC method, it is not mandatory to identify the data attributes. However,
understanding the concept of a ‘data attribute’ is necessary to understand how to measure
changes’. A requirement to change a data attribute can result in the data movement to which
the attribute belongs being indicated as ‘changed’.
Also, it may be helpful to analyze and identify data attributes in the process of distinguishing
data groups and objects of interest.
3.4
Identification of data movements.
This step consists in identifying the data movements (Entry, Exit, Read and Write) of each
functional process.
GUIDANCE on Rule 12: Data Movements
The following guidance helps to confirm the status of a candidate Entry data movement:
GUIDANCE on Rule 16: Entry (E).
a) The data group of a triggering Entry may consist of only one data attribute which simply
informs the software that ‘an event Y has occurred’.
b) For clock-ticks that are triggering events identify an Entry from a functional user, in this
case the Clock.
c)
Unless a specific functional process is necessary, obtaining the date and/or time from the
system’s clock is not considered an Entry or any other COSMIC data movement.
NOTE:
Very often, especially in business application software, the data group of the
triggering Entry has several data attributes which inform the software that ‘an event Y has
occurred and here is the data about that particular event’.
GUIDANCE on Rule 17: Exit (X).
a) For an enquiry which outputs fixed text, (where ‘fixed’ means the message contains no
variable data values), identify an Exit for the fixed text output.
b) When identifying Exits, ignore all fields and other headings that enable human users to
understand the output data.
GUIDANCE on Rule 18: Read (R).
Do not identify a Read when the FUR of the software being measured specify any software
or hardware functional user as the source of a data group, or as the means of moving the
data group to persistent storage. Interaction with other functional users is by definition across
a boundary (Generic Software Model, principle 1), which is handled by an Entry data
movement. The actual Read takes place within the boundary of the software being
measured.
COSMIC Measurement Manual -  version 5.0 – Part 2: Guidelines                      Copyright © 2024
14
GUIDANCE on Rule 19: Write (W).
Do not identify a Write when the FUR of the software being measured specify any software
or hardware functional user as the destination of the data group or as the means of retrieving
a persistently-stored data group. Interaction with other functional users is by definition across
a boundary (Generic Software Model, principle 1), which is handled by an eXit data
movement. The actual Write takes place within the boundary of the software being
measured.
NOTE:
When the FUR require data to be stored or to be retrieved from storage, the
measurer must investigate whether the data can be stored or retrieved within its own
boundary, i.e. to/from ‘persistent storage’, or whether data is required to be stored/retrieved
with help of a functional user of the software being measured (i.e. via some other piece of
software, or directly to or from a hardware device).
GUIDANCE on Rules 16 to 19 – Data manipulation associated with data movements.
The data manipulation associated with any of these data movements does not include any
data manipulation that is needed after the data movement has been successfully completed,
nor does it include any data manipulation associated with any other data movement.
The following guidance cover the most common situation (guidance a)) and other possible
valid cases (guidance b) and c)):
• In a) the occurrences of the data group are subject to the same FUR: so one data
group and one data movement is identified.
• In b) and c) the same applies to each different data group separately: so one data
group and one data movement per different data group is identified.
GUIDANCE on Rules 13 and 14 – Data Movements Uniqueness.
a) Unless the FUR are as given in guidance b) or c), all data describing any one object of
interest that is required to be entered into one functional process is identified as one data
group moved by one Entry.
NOTE 1:  A functional process may, of course, have multiple Entries, each moving data
describing a different object of interest.
NOTE 2: The same equivalent guidance applies to any Read, Write or Exit data
movement in any one functional process.
b) If FUR specify that different data groups must be entered into one functional process,
each from a different functional user, where each data group describes the same object
of interest, then one Entry is identified for each of these different data groups.
NOTE 1: The same equivalent guidance applies for Exits of data to different functional
users from any one functional process.
NOTE 2: Any one functional process has only one triggering Entry.
c) If FUR specify that different data groups must be moved from persistent storage into one
functional process, each describing the same object of interest, then one Read is
identified for each of these different data groups.
NOTE 1: The same equivalent guidance applies for Writes in any given functional
process.
NOTE 2: This guidance is analogous to rule b). In the case of the FUR to read different
data groups describing the same object of interest, they will likely have originated from
different functional users. In the case of the FUR to write different data groups, they will
likely be made available to be read by different functional users.
COSMIC Measurement Manual -  version 5.0 – Part 2: Guidelines                      Copyright © 2024
15
GUIDANCE on Rules 16-17: Functional process requiring data from a functional user.
a) When the functional process does not need to tell the functional user what data to send,
a single Entry is sufficient (per object of interest).
b) When the functional process needs to tell the functional user what data to send, an Exit
followed by an Entry are necessary.
GUIDANCE on Rules 16-19: Control commands in applications with a human interface.
In an application with a human interface ’control commands’ are ignored as they do not
involve any movement of data about an object of interest.
Error and confirmation messages are specific forms of an Exit and the Rules governing
identification apply.
GUIDANCE on Rules 16-19: Error/confirmation messages & other indications of error
conditions.
a) One Exit is identified to account for all types of error/confirmation messages issued by
any one functional process of the software being measured from all possible causes
according to its FUR.
b) If a message to a human functional user provides data in addition to confirming that
entered data has been accepted, or that entered data is in error, then this additional data
is identified as a separate data group moved by an Exit in the normal way.
c) All other data, issued or received by the software being measured, to/from its hardware
or software functional users should be analyzed according to the FUR as Exits or Entries
respectively, according to the normal COSMIC rules, regardless of whether or not the
data values indicate an error condition.
d) Reads and Writes are considered to account for any associated reporting of error
conditions. Therefore, no Entry to the functional process being measured is identified for
any error indication received as a result of a Read or Write of persistent data.
e) No Entry or Exit is identified for any message indicating an error condition that might be
issued whilst using the software being measured but which is not required to be
processed in any way by the FUR of that software, e.g. an error message issued by the
operating system.
3.5
Measuring the components of a distributed software system.
When the purpose of a measurement is to measure separately the size of each component
of a distributed software system, a separate scope of FSM must be defined for each
component.  In such a case the sizing of the functional processes of each component follows
all the rules as already described.
From the process for each measurement (… define the scope, then the functional users and
boundary, etc. …) it follows that if a piece of software consists of two or more components,
there cannot be any overlap between the scope of FSM of each component. The scope of
FSM for each component must define a set of complete functional processes.  For example,
there cannot be a functional process with part in one scope and part in another. Likewise, the
functional processes within the measurement scope for one component do not have any
information about the functional processes within the scope of another component, even
though the two components exchange messages.
COSMIC Measurement Manual -  version 5.0 – Part 2: Guidelines                      Copyright © 2024
16
The functional user(s) of each component is/are determined by examining where the events
occur that trigger functional processes in the component being examined. (Triggering events
can only occur in the world of a functional user.)
3.6
Re-use of software.
Any two or more functional processes in the same software being measured may have some
functionality that is identical or very similar in each process and is described separately
elsewhere in the requirements. This phenomenon is referred to as ‘functional commonality’,
or functional ‘similarity’.
However, each functional process is defined, modelled and measured independently of, i.e.
without reference to any other FUR in the same software being measured.
Therefore, if the FUR for a given functional process makes a reference to FUR elsewhere in
the requirements then the size of that referenced functionality is to be included in the size of
the functional process being measured.
3.7
Measurement of the size of changes to software.
A ‘functional change’ to existing software is interpreted in the COSMIC method as ‘any
combination of additions of new data movements or of modifications or deletions of existing
data movements, including to the associated data manipulation’. The terms ‘enhancement’
and ‘maintenance’1 are often used for what we here call a ‘functional change’.
The need for a change to software may arise from either:
•
a new FUR (i.e. only additions to the existing functionality), or
•
from a change to the FUR (perhaps involving additions, modifications and deletions) or
•
from a ‘maintenance’ need to correct a defect.
The rules for sizing any of these changes are the same but the measurer is alerted to
distinguish the various circumstances when making performance measurements and
estimates.
GUIDANCE on Rule 24: – Functional size of changes to the FUR.
a) Adding an existing functional process amounts to adding its triggering Entry, i.e. the size
of the change is 1 CFP:
• the size of the FUR increases by the size of the functional process.
b) Deleting a functional process amounts to removing its triggering Entry, i.e. the size of the
change is 1 CFP:
• the size of the FUR decreases by the size of the functional process.
Note. When a functional process has more than one Entry, these other Entry data
movements have no bearing on adding or deleting the functional process.
c)
A data movement is considered to be functionally modified if at least one of the following
applies:
•  the data group moved is modified.
•  the associated data manipulation is modified.
d) A data group is modified if at least one of the following applies:
•  one or more new attributes are added to the data group.
COSMIC Measurement Manual -  version 5.0 – Part 2: Guidelines                      Copyright © 2024
17
•  one or more existing attributes are removed from the data group.
•  one or more existing attributes are modified, e.g. in meaning or format (but not in their
values).
e) A data manipulation is modified if it is functionally changed in any way.
f)
If a data movement must be modified due to a change of the data manipulation
associated with the data movement and/or due to a change in the number or type of the
attributes in the data group moved, one changed CFP is measured, regardless of the
actual number of modifications in the one data movement.
g) If a data group must be modified, data movements moving the modified data group
whose functionality is not affected by the modification to the data group is not identified
as changed data movements.
NOTE:  A modification to any data appearing on input or output screens that are not related
to an object of interest to a functional user is not identified as a changed CFP.
h) A normal measurement convention is that the functional size of a piece of software does
not change if the software must be changed to correct a defect so as to bring the
software in line with its FUR.  The functional size of the software does change if the
change is to correct a defect in the FUR.
Modified data movements have no influence on the size of the piece of software as they exist
both before and after the modifications have been made.
When a piece of software is completely replaced, for instance by re-writing it, with or without
extending and/or omitting functionality, the functional size of this change is the size of the
replacement software, measured according to the normal rules for sizing new software.
NOTE Usually, the size of a functional change (discussed here) and the change in the
functional size of the software differ.
