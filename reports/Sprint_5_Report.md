# Sprint 5 Report (September 30th to October 31st)
## Sprint 5 Video (video link here)
## What's New (User Facing)
*	CI and deployment workflow
*	Pop-in algorithm identifies displacement rather than depth, with the pop-in start and end points being identified and allowing for manual adjustment
*	Real time updating of coordinates of data points, and exporting to structured data file
*	Set scale by drawing a known length or entering FOV (µm)
*	Implemented client requested pop-in features such as manipulatable start and end points
*	Train U-Net on labeled indentation JSONs and generate estimated crack lengths
*	Edit suggested cracks: move endpoints, rotate lines, add missed cracks
*	Export reviewed crack measurements JSON (each / longest / total in µm)
## Work Summary (Developer Facing)
(work summary here)
## Unfinished Work
Most of the work for this project is complete, there is some training data that still needs to be annotated and some small bug fixes here and there, but the majority of the project is complete.
* (more unfinished work here)
## Completed Issues/User Stories
* https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/issues/16
* https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/issues/17
* https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/issues/28
* https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/issues/29
* We have also included a live demo of the current application in the Sprint 5 YouTube video, demonstrating the new features. 
## Incomplete Issues/User Stories
Here are links to issues we worked on but did not complete in this sprint (These are the Final Report and Final Review Kanban Board issues): 
* https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/issues/18
* https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/issues/27
## Code Files for Review
Please review the following code files, which were actively developed during this
sprint, for quality:
* [build-release.yml](https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/blob/main/.github/workflows/build-release.yml)
## Retrospective Summary
Here's what went well: 
* Adding the pop-in locator tab to the GUI.
* Adding the indentation crack length tab to the GUI.
* Preparing training data for the different models.

Here's what we'd like to improve: 
* Team coordination and communication.

Here are changes we plan to implement in the next sprint: 
* Iron out all remaining bugs and issues.
* Finish annotating all new training data.
* additional changes here
