## 1 INTRODUCTION.
> Manual: part-1-mm-principles-definitions-rules-v5-0-aug-2021

1.1
Purpose.
The purpose of this document is to state the Principles, Definitions and Rules of the COSMIC
Functional Size Measurement method (the ‘COSMIC Method’), as well as the COSMIC
measurement process.
This Part 1 of the COSMIC Measurement Manual document contains only reference material,
i.e. what to do, as described in ISO 19761 [3]. For guidance developed by the COSMIC Group
as to how to apply COSMIC to different situations refer to Part 2, and for examples, refer to Part
3. The COSMIC Group has also published additional documents to illustrate its use in various
contexts contexts (Agile, Business Applications, Real-time, etc.) and technologies (SOA, Mobile,
etc.)
1.2
Overview.
The COSMIC method involves applying a set of models, principles, rules and processes to
measure the Functional User Requirements (or ‘FUR’) of a given piece of software.
The result is a numerical ‘value of a quantity’ (as defined by ISO) representing the functional size
of the piece of software according to the COSMIC method. This numerical value is on a ratio
scale: therefore valid mathematical operations can be performed using the values.
The COSMIC method adopts the ISO definition of Functional User Requirements (FUR).
1.3
The models and principles of the COSMIC method.
The COSMIC method is based on software engineering principles categorized in two models:
The COSMIC Software Context Model: it contains the principles that pertain to identifying the
nature and structure of the Software to be measured as required by the COSMIC method,
leading to the identification of its FUR.
The Generic Software Model: it contains the principles to be applied to the FUR in order to
extract and measure the elements that contribute to the functional size using the COSMIC
method.
PRINCIPLES - The COSMIC Software Context Model.
1. A software application is typically structured into layers.
2. A layer may contain one or more separate pieces of software.
3. A piece of software is described by its Functional User Requirements (FUR).
4. The FUR are expressed at a level of granularity that exposes its functional processes.
5. A piece of software delivers functionality to its functional users as identified in the FUR.
6. A piece of software to be measured is defined by the scope of the functional size
measurement (FSM), which is confined wholly within a single layer.
7. The scope of the FSM defines the functional processes to be measured, and depends on the
purpose of the measurement.
COSMIC Measurement Manual- version 5.0 – Part 1: Principles, Definitions & Rules                     Copyright © 2021
5
PRINCIPLES - The COSMIC Generic Software Model.
1. A piece of software interacts with its functional users across a boundary, and with persistent
storage within this boundary.
2. A functional process consists of sub-processes called data movements.
3. There are four data movement sub-types: Entry, Exit, Write and Read. A data movement
sub-type includes any associated data manipulation.
4. A data movement moves a single data group.
5. A data group consists of a unique set of data attributes that describe a single object of
interest.
6. Each functional process is initiated by a triggering event, detected by a Functional User and
which in turn initiates a data movement called the triggering Entry.
7. The functional size is based on the types of the elements used for measurement, not on the
number of occurrences.
8. The size of a functional process is equal to the number of its data movements where one
data movement has a size of 1 COSMIC Function Point.
9. The size of a piece of software is the sum of the sizes of the functional processes within the
scope of the FSM.
NOTE: The principles are written using the terminology of the COSMIC method.
1.4
Definitions.
In this sub-section:
•
the definitions from ISO documents are reproduced ‘as is’ but without the ISO NOTES
that have been transferred to the main body of the text;
•
texts underlined refer to terms defined in this sub-section.
application.
software system for collecting, saving, processing, and presenting data by means of a computer. [Adapted
from [4]]
Base Functional Component.
(BFC).
elementary unit of Functional User Requirements defined by and used by an FSM method for
measurement purposes. [1]
boundary.
conceptual interface between the software being measured and its functional users.
component.
any part of a software system that is separate for reasons of the software architecture, and⁄or that was
specified, designed or developed separately.
control command.
command that enables human functional users to control their use of the software but which does not
involve any movement of data about an object of interest of the FUR of the software being measured.
COSMIC unit of measurement.
1 CFP (COSMIC Function Point), which is defined as the size of one data movement.
COSMIC Measurement Manual- version 5.0 – Part 1: Principles, Definitions & Rules                     Copyright © 2021
6
data attribute.
smallest parcel of information, within an identified data group, carrying a meaning from the perspective of
the software’s Functional User Requirements. [3]
data group.
data group type.
distinct, non-empty, non-ordered and non redundant set of data attributes where each included data
attribute describes a complementary aspect of the same one object of interest. [3]
data manipulation.
any processing of the data  other than a movement of the data into or out of a functional process, or
between a functional process and persistent storage. [3]
data movement.
data movement type.
Base Functional Component which moves a single data group. [3]
E - Abbreviation for Entry type.
Entry.
Entry type.
data movement that moves a data group from a functional user across the boundary into the functional
process where it is required. [3]
error/confirmation message.
Exit issued by a functional process to a human user that either confirms only that entered data has been
accepted, or only that there is an error in the entered data.
Exit.
Exit type.
data movement that moves a data group from a functional process across the boundary to the functional
user that requires it. [3]
event.
something that happens.
functional process.
functional process type.
elementary component of a set of Functional User Requirements, comprising a unique, cohesive and
independently executable set of data movements. [3]
functional process level of granularity.
level of granularity of the description of a piece of software at which
•
the functional user (-types) are individual humans or engineered devices or pieces of software (and
not any groups of these) AND
•
single event (-types) occur that the piece of software must respond to (and not any level of granularity
at which groups of events are defined).
functional size.
size of the software derived by quantifying the Functional User Requirements. [1]
COSMIC Measurement Manual- version 5.0 – Part 1: Principles, Definitions & Rules                     Copyright © 2021
7
Functional Size Measurement
FSM.
process of measuring Functional Size. [1]
Functional Size Measurement method.
FSM method
specific implementation of FSM defined by a set of rules, which conforms to the mandatory features of
ISO/IEC 14143-1:2007. [1]
functional user.
user that is a sender and/or an intended recipient of data in the Functional User Requirements of a piece
of software. [3]
Functional User Requirements.
FUR.
sub-set of the user requirements describing what the software shall do, in terms of tasks and services. [1]
input.
data moved by all the Entries of a given functional process.
layer.
partition resulting from the functional division of a software system. [3]
level of decomposition.
any level resulting from dividing a piece of software into components (named ‘Level 1’, for example), then
from dividing components into sub-components (‘Level 2’), then from dividing sub-components into sub-
sub components (Level 3’), etc.
level of granularity.
any level of expansion of the description of any part of a single piece of software (e.g. a statement of its
requirements, or a description of the structure of the piece of software) such that at each increased level of
expansion, the description of the functionality of the piece of software is at an increased and uniform level
of detail.
measurement method
logical sequence of operations, describe generically, used in the performance of measurements. [5]
measurement process.
process of establishing, planning, performing and evaluating software measurement within an overall
project or organizational measurement structure. [3]
measurement (strategy) patterns.
standard template that may be applied when measuring a piece of software from a given software
functional domain, that defines the types of functional user that may interact with the software, the level of
decomposition of the software and the types of data movements that the software may handle.
model.
description or analogy used to help visualize a concept that cannot be directly observed.
OOI -  Abbreviation for object of interest
object of interest.
object of interest type.
any ‘thing’ that is identified from the point of  view of the Functional User Requirements about which the
software is required to process and⁄or store data. [3]
COSMIC Measurement Manual- version 5.0 – Part 1: Principles, Definitions & Rules                     Copyright © 2021
8
output.
data moved by all the Exits of a given functional process.
peer software.
piece of software that reside in the same layer as, and exchanges data with, another piece of software. [3]
persistent storage.
storage which enables a functional process to store data beyond the life of the functional process and/or
which enables a functional process to retrieve data stored by another functional process, or stored by an
earlier occurrence of the same functional process, or stored by some other process. [3]
purpose of measurement.
statement that defines why a measurement is being made, and what the result will be used for.
R  – Abbreviation for Read type.
Read.
Read type.
data movement that moves a data group from persistent storage within reach of the functional process
which requires it. [3]
scope.
scope of the FSM.
set of Functional User Requirements to be included in a specific functional size measurement instance. [3]
software
set of computer instructions, data, procedures and maybe documentation operating as a whole, to fulfill a
specific set of purposes, all of which can be described from a functional perspective through a finite set of
Functional User Requirements, technical and quality requirements.
software system.
system that consists only of software.
sub-process type.
part of a functional process that either moves data (into the software from a functional user or out of the
software to a functional user, or to or from persistent storage) or that manipulates data.
system.
combination of hardware, software and manual procedures organized to achieve stated purposes.
[adapted from [2]]
triggering Entry.
triggering Entry type.
the Entry data movement of a functional process that moves a data group generated by a functional user
that the functional process needs to start processing.
triggering Event.
triggering event type.
event that causes a functional user of the piece of software to initiate (‘trigger’) one or more functional
processes. [3]
unit of measurement.
particular quantity, defined and adopted by convention, with which other quantities of the same kind are
compared in order to express their magnitudes relative to that quantity. [5]
COSMIC Measurement Manual- version 5.0 – Part 1: Principles, Definitions & Rules                     Copyright © 2021
9
user
any person or thing that communicates or interacts with the software at any time. [3]
value (of a quantity)
magnitude of a particular quantity, generally expressed as a unit of measurement multiplied by a number.
W - Abbreviation for Write type.
Write.
Write type.
data movement that moves a data group from a functional process to persistent storage. [3]
X – Abbreviation for Exit type.
See Exit.
