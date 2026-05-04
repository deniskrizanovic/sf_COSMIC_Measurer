# metadata-to-measure

Scratch directory for downloaded Salesforce metadata that you want to measure
with the COSMIC measurers (Apex, Flow, FlexiPage, LWC).

Everything in this folder is gitignored (except this README and `.gitkeep`).
Drop retrieved metadata here, run the measurers, then clear it out when done.

Typical contents:

- `force-app/main/default/classes/*.cls`
- `force-app/main/default/flows/*.flow-meta.xml`
- `force-app/main/default/flexipages/*.flexipage-meta.xml`
- `force-app/main/default/lwc/<component>/`
