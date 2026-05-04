## 2 THE MEASUREMENT STRATEGY PHASE.
> Manual: part-2-mm-guidelines-v5-0-sep-2024

2.1
Overview of the measurement strategy phase.
Figure 2.1 presents graphically the Measurement Strategy Phase.
COSMIC Measurement Manual -  version 5.0 – Part 2: Guidelines                      Copyright © 2024
5
Figure 2.1 - The process of determining a Measurement Strategy.
2.2
Determine purpose and scope of the FSM.
The term ‘purpose’ is used in its normal English meaning. The purpose helps the measurer
to determine:
•
The scope of the measurement and hence the artefacts which will be needed for the
measurement.
•
The functional users.
•
The functional changes.
•
The point in time in the project life-cycle when the measurement will take place.
•
The required accuracy of the measurement, and hence whether the standard COSMIC
method should be used, or whether an approximation technique should be used (e.g.
early in a project’s life-cycle, before the FUR are fully elaborated).
As an aid to determining a measurement strategy, the Guideline for 'Measurement Strategy
Patterns' describes, for each of several different types of software, a standard set of
parameters for measuring software sizes, called a ‘measurement strategy pattern’
(abbreviated to ‘measurement pattern’. Consistent use of the same measurement patterns
should help measurers to ensure that measurements made for the same purpose are made
in a consistent way, may be safely compared with other measurements made using the
same pattern and will be correctly interpreted for all future uses. A side benefit of using a
standard pattern is that the effort to determine the Measurement Strategy parameters is
much reduced.
The COSMIC Group recommends that measurers study and master the COSMIC method,
especially the Measurement Strategy parameters, before using the standard patterns.
2.3
Identification of the FUR from software artefacts.
As illustrated in Figure 2.2, FUR can be derived from software engineering artefacts that are
produced before the software exists. Thus, the functional size of software can be measured
prior to its implementation in a computer system.
COSMIC Measurement Manual -  version 5.0 – Part 2: Guidelines                      Copyright © 2024
6
Requirements
definition artefacts
e.g. Use Cases, User
Stories
Data analysis /
modelling artefacts
e.g. E/R diagrams,
RDA, OO models
Dynamic behaviour
models
e.g. State Transition
Diagrams
Functional User Requirements (‘FUR’) in the
artefacts of the software to be measured
Figure 2.2 – Pre-implementation sources of Functional User Requirements.
NOTE:
Some existing software may need to be measured without there being any, or
with only a few, architecture or design artefacts available, and the functional requirements
might not be documented (e.g. for legacy software). In such circumstances, it is still possible
to derive the FUR from the artefacts of the computer system even after it has been
implemented, as illustrated in Figure 2.3.
Figure 2.3 – Post-implementation sources of Functional User Requirements (FUR).
The process to be used and hence the effort required to extract the FUR from different types
of software engineering artefacts or to derive them from installed software will obviously vary;
these processes cannot be dealt with in the Measurement Manual. The COSMIC method
assumes that the FUR of the software to be measured either exist or that they can be
extracted or derived from its artefacts, in light of the purpose of the measurement.
If the measurer understands these two models, it will always be possible to derive the FUR of
a piece of software to be measured from its available artefacts, though the measurer may
have to make some assumptions due to missing or unclear information.
2.4
Non-Functional Requirements.
System NFR can be very significant for a software project. In extreme cases, a statement of
requirements for a software-intensive system can require as much documentation for the
NFR as for the functional requirements. The COSMIC method can be used to measure some
requirements that may be first expressed as non-functional.  Several studies have shown
that some requirements that initially appear as system NFR evolve as a project progresses
into a mixture of requirements that can be implemented in software functions, and other
requirements or constraints that are truly ‘non-functional’. See Figure 2.4.
COSMIC Measurement Manual -  version 5.0 – Part 2: Guidelines                      Copyright © 2024
7
Functional
Requirements
Non-Functional
Requirements
Functional User
Requirements
‘True’ NFR e.g.
• Technology
• Project &
performance
constraints
Project time-line
Can be measured
by COSMIC
Should be recorded;
may be quantifiable
(First version of
Requirements)
(Later version of
Requirements)
Software
artefacts
(Extracted
by Measurer)
Figure 2.4 - Many requirements initially appearing as NFR evolve into FUR as a project
progresses.
This is true for many system quality constraints, such as response time, ease of use,
maintainability, etc. Once identified, these software functions that have been ‘hidden’ in NFR
at the beginning of a project can be sized using the COSMIC method just as any other
software functions. Not recognizing this ‘hidden’ functional size is one reason why software
sizes can appear to grow as a project progresses.
More in-depth discussions on system and software Non-Functional Requirements (NFR) are
presented in: ‘Guideline on Non-Functional & Project Requirements’.
2.5
Identification of the layers.
Software architectures can be very complex, however COSMIC employs a very simplified
view of the software architecture that is sufficient for the purpose of measurement. It is the
task of the measurer to perform that simplification. This section provides guidance to the
measurer.
Since the scope of a piece of software to be measured must be confined to a single software
layer, the process of defining the scope(s) of FSM may require that the measurer first has to
decide what are the layers of the software’s architecture. This sub-section discusses ‘layers’
of software as these terms are used in the COSMIC method because:
•
the measurer may be faced with measuring some software in a ‘legacy’ environment of
software that evolved over many years without ever having been designed according to
an underlying architecture The measurer may therefore need guidance on how to
distinguish layers according to the COSMIC terminology;
•
the expressions ‘layer’ and ‘layered architecture’ are not used consistently in the software
industry. When the measurer must measure some software that is described as being in
a ‘layered architecture’, it is advisable to check that ‘layers’ in this architecture are
defined in a way that is compatible with the COSMIC method. To do this, the Measurer
should establish the equivalence between specific architectural objects in the ‘layered
architecture’ paradigm and the concept of layers as defined in this manual.
In a defined software architecture, each layer may have the following characteristics:
a) Software in one layer provides a set of services that is cohesive according to some
defined criterion, and that software in other layers can utilize without knowing how
those services are implemented.
b) The relationship between software in any two layers is defined by a
‘correspondence rule’ which may be either:
• ‘hierarchical’, i.e. software in layer A is allowed to use the services provided by
COSMIC Measurement Manual -  version 5.0 – Part 2: Guidelines                      Copyright © 2024
8
software in layer B but not vice versa (commonly referred to as Client-Server);
• ‘bi-directional’, i.e. software in layer A is allowed to use software in layer B, and
vice versa (commonly referred to as peer-to-peer (P2P).
c) Software in one layer exchanges data groups with software in another layer via their
respective functional processes.
d) Software in one layer does not necessarily use all the functional services supplied
by software in another layer.
e) Software in one layer of a defined software architecture may be partitioned into
other layers according to a different defined software architecture.
Guidance on Rule 4: Identification of Layers
If the overall scope of the FSM extends over multiple layers, the measurer should proceed as
follows:
•
If the software to be measured exists within an established architecture of layers that can
be mapped to the COSMIC layering characteristics as defined above, then that
architecture should be used to identify the layers for measurement purposes.
•
If however, the purpose requires that some software is measured that is not structured
according to the COSMIC layering characteristics, the measurer should try to partition the
software into layers by applying the principles defined above.
•
Conventionally, infrastructure software packages such as database management
systems, operating systems or device drivers, that provide services that can be used by
other software in other layers, are each located in separate layers.
Normally in software architectures, the ‘top’ layer, i.e. the layer that is not a subordinate to
any other layer in a hierarchy of layers, is referred to as the ‘application’ layer. Software in
this application layer relies on the services of software in all the other layers for it to perform
properly. Software in this ‘top’ layer may itself be layered, e.g. as in a ‘three-layer
architecture’ of User Interface, Business Rules and Data Services components.
Once identified, each layer can be registered in the Measurement report, with the
corresponding label.
2.6
Identification of the functional users.
GUIDANCE on Rule 7: Identification of the functional users.
The identification of functional user (or users) is determined by the Functional ‘User’
Requirements that must be measured and by the purpose of the measurement.
NOTE:
There is nothing absolute about a functional user, i.e. identify the functional
users per functional process. A sender/receiver of data may be a functional user of one or
more functional processes, but not a functional user of other functional processes, even in
the same software being measured.
2.7
Levels of decomposition.
Size measurements of the components of a piece of software are only directly comparable
for components at the same level of decomposition. This is important because sizes of
pieces of software at different levels of decomposition cannot be simply added up without
taking into account the aggregation rules of chapter 5. Further, as a consequence, the
performance (e.g. the productivity = size/effort) of projects to develop different pieces of
software can only be compared if all the pieces of software are at the same level of
decomposition.
COSMIC Measurement Manual -  version 5.0 – Part 2: Guidelines                      Copyright © 2024
9
Different levels of decomposition of a piece of software may correspond to different ‘views’ of
the software’s layers, e.g., as in Figure 1.3 in Part 3c. However, software may be
decomposed into ‘levels’ regardless of whether or not it is designed using a layered-
architecture model.
2.8
Context diagrams.
It can be helpful when defining a scope of FSM and the functional users to draw a ‘context
diagram’ for the software being measured. Context diagrams show the flows of data between
the piece of software and its functional users (humans, hardware devices or other software)
and also show the flows of data between the piece of software and persistent storage.
A context diagram is an instance of a measurement pattern applied to the software being
measured. Symbols used in context diagrams are presented in Figure 2.5.
Symbol
Interpretation
The piece of software to be measured (box with thick outline) i.e. the definition of a measurement
scope.
Any functional user of the software being measured.
The arrows represent all the movements of data crossing a boundary (the dotted line) between a
functional user and the software being measured.
The arrows represent all the movements of data between the software being measured and
‘persistent storage’. (The flowchart symbol for ‘data storage’ emphasizes that persistent storage is
an abstract concept. This symbol indicates that the software does not interact directly with physical
hardware storage.)
Figure 2.5 - Symbols of context diagrams.
2.9
Identification of the level of granularity.
COSMIC requires the FUR to be expressed at a level of detail sufficient to create the
COSMIC measurement models: this is called the level of granularity.
To derive a functional size using the COSMIC FSM using the RULES of ISO 19761, the
necessary level of granularity is that at which individual functional processes and their data
movements can be identified and defined. When functional details are missing at other levels
of granularity of the requirements, measurements should be made using one of the size
approximation techniques described in the related ‘Early Software Sizing with COSMIC:
Practitioners Guide’.
NOTE 1
In the initial stages of a software development project, actual requirements are
specified ‘at a high level’, that is, in outline, or in little detail.  As the project progresses, the
actual requirements are refined, (e.g., through versions 1, 2, 3 etc.), revealing more and
more detail ‘at lower levels’.  These different degrees of detail of the actual requirements are
known as different ‘levels of granularity’.
NOTE 2:
Measurers should be aware that when requirements are evolving early in the
life of a software project, at any moment different parts of the required software functionality
will typically have been documented at different levels of granularity.
For an example of measuring at varying levels of granularity and of decomposition, see the
telecoms system example in the ‘Guideline for early or rapid COSMIC functional size
measurement using approximation approaches’
COSMIC Measurement Manual -  version 5.0 – Part 2: Guidelines                      Copyright © 2024
10
