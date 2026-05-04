## 5 MEASUREMENT PHASE.
> Manual: part-2-mm-guidelines-v5-0-sep-2024

The general process for measuring a piece of software when its Functional User
Requirements have been expressed in terms of the COSMIC Generic Software Model is
summarized in Figure 5.1 below.
Figure 5.1 – The process for the COSMIC Measurement Phase.
GUIDANCE on Rule 23: Aggregation of functional sizes.
a) Sizes of pieces of software or of changes to pieces of software may be added together
only if measured at the same functional process level of granularity of their FUR.
b) Sizes of pieces of software and/or changes in the sizes of pieces of software within any
one layer or from different layers are added together only if it makes sense to do so, for
the purpose of the measurement.
c) The size of a piece of software is obtained by adding up the sizes of its components
(regardless of how the piece is decomposed) and eliminating the size contributions of
inter-component data movements.
Within each identified layer, the aggregation function is fully scalable. A sub-total can be
generated for individual functional processes or for all the functional processes of the
software, depending on the purpose and scope of the measurement exercise.
