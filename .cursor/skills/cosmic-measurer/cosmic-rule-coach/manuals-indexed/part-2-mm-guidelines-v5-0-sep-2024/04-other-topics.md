## 4 OTHER TOPICS.
> Manual: part-2-mm-guidelines-v5-0-sep-2024

4.1
Extending the COSMIC measurement method – Local extension.
The COSMIC method of measuring a functional size does not presume to measure all
possible aspects of software ‘size’. Thus the method is currently not designed to measure
separately and explicitly the size of the FUR of data manipulation sub-processes. The
influence on size of data manipulation sub-processes is taken into account via a simplifying
assumption that is valid for a wide range of software domains.
Nevertheless, the COSMIC size measure is considered to be a good approximation for the
method’s stated purpose and domains of applicability. Yet, it may be that within the local
environment of an organization using the COSMIC measurement method, it is desired to
account for such functionality in a way which is meaningful as a local standard. When such
local extensions are used, the measurement results must be reported according to the
special convention presented in section 6.
4.2
COSMIC in Agile.
The COSMIC method is being used successfully to measure the size of User Stories in Agile
software developments, which may have very few data movements. This practice is well-
established, with many reports of the CFP sizes of Agile iterations (or ‘sprints’), aggregated
from the sizes of individual User Stories, that correlate very well with the effort to develop the
iteration (and much better than the correlation with effort of sizes measured using Story
Points). See (https://cosmic-sizing.org/publications/guideline-for-sizing-agile-projects-with-
cosmic/)
COSMIC Measurement Manual -  version 5.0 – Part 2: Guidelines                      Copyright © 2024
18
