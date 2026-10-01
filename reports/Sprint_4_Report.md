# Sprint 4 Report ( to September 30th)
## Sprint 4 Video https://youtu.be/QNALxLIwfHw 
## What's New (User Facing)
* Added pop-in locator tab to existing program
* Added indentation crack length tab to existing program  
## Work Summary (Developer Facing)
During this sprint, we pivoted away from modeling the segmentation images due to the client being unable to obtain training data. Instead, we focused on two new features to be added as tabs to the existing program, one to locate the pop-in in a load/depth curve, and one to estimate indentation crack lengths from microscopic images. We were able to add the pop in tab and create an algorithm to locate the first candidate point as per client request. This will need client provided data, provided they can obtain said data in time, for ML to be implemented. The client provided us with a dataset for the indentation crack images, which we were able to label for training. This was tedious since it had to be done manually, labeled and annotated using CVAT (computer vision annotation tool) to facilitate their use in training a model for use in indentation crack measurement. In time, we may need more images from the client for training purposes. A prototype of such an indentation tab has been written with conventional image processing techniques, but it is quite inaccurate since these images have a lot of noise. As per client request, we have modified the prototype to allow user manipulation of the crack lines, and the prototype will update the line lengths in real time. It was a bit difficult adjusting our goals for the project due to pivoting, but we are in a good place now. 
## Unfinished Work
The indentation crack length measurement model has not yet been completed. Progress has been made and the training data has been labeled/annotated, but the machine learning algorithm is not complete nor trained. Objectives were changed from last sprint and as such training data was not immediately available. As a result, other issues (the pop-in indicator and a traditional crack length algorithm without machine learning) were able to be worked first and given a higher priority. There are also some small bugs we plan to iron out next sprint, in addition to any new issues that might arise. If the client can provide pop-in training images, work can also be started on a pop-in machine learning model.
## Completed Issues/User Stories
* https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/pull/13 
* https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/issues/14
* https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/issues/19
* https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/issues/21
* https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/issues/22
* https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/issues/23
* https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/issues/15 
* We have also included a live demo of the current application in the Sprint 4 YouTube video, demonstrating the new features. 
## Incomplete Issues/User Stories
Here are links to issues we worked on but did not complete in this sprint (explanation in a comment on the issue): 
* https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/issues/16 
## Code Files for Review
Please review the following code files, which were actively developed during this
sprint, for quality:
* [popin_locator.py](https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/blob/main/src/app/analysis_scripts/popin_locator.py)
* [IndentationCrackMeasurementQt.py](https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/blob/test_indentation/IndentationCrackMeasurementQt.py)
* [Labels.json](https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/blob/main/data/Indentation_Image_Labels/Labels.json)
## Retrospective Summary
Here's what went well: 
* Making the pop in identification algorithm without machine learning.
* Making the crack length measurement algorithm without machine learning.
* Preparing the crack length machine learning model’s training data. 
Here's what we'd like to improve: 
* Team coordination and communication. 
Here are changes we plan to implement in the next sprint: 
* We plan to finish the crack length measurement model and begin training it. 
* If training data for a pop in identification machine learning model is provided, we plan to start preparing it and working on a model to use it. 
