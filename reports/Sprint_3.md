# Sprint 3 Report (3/3/25 - 4/2/2025)
## What's New (User Facing)
* Added 'About' tab to GUI with comprehensive application information, added button information ribbons on button hover
* Added a Reset button, ability to add additional images to existing uploaded dataset, and additional error check dialog boxes to Segmentation
* Added the ability to generate resultant data histograms or resultant data histograms with an overlay of statistical distribution
* Added the ability for the user to select which distributions to perform on the resultant dataset and set how long each distribution can run
* Added progress bars for the segmentation and analysis processes to indicate an active computation and reflect computational progress
* Added robust Download button for both segmentation and analysis so the user may select which specific files to download and where

  
## Work Summary (Developer Facing)
During this sprint, the team worked a lot on refactoring the code base. The reason for this was the separation of concern was not clear within the project, there was one mega class that controlled everything, causing complications within testing and unreadable code. So, the next course of action was for us to separate the concerns into their own classes / subsystem, with the refactoring, it now creates a clear streamlined idea of what each class is doing and the functionality tied to it. The significant learning experience from the team was to ensure that the code we write is not highly coupled and to separate things when appropriate, this ensures future scalability and readability. 

## Unfinished Work
We have successfully completed all items on our list of deliverables for this sprint. As outlined by our project team and project client, Dr. Zare, the focus of this sprint was to add specific features to enhance the usability of the application. While items such as implementing a machine learning model, adjusting segmentation for more generalized datasets (ie, impact testing dataset), and an executable download for simple program distribution have been discussed all sprint, we performed research on these topics and they were never expected to be complete this sprint. All User Stories with the intent of being completed for this sprint have been successfully finished.


## Completed Issues/User Stories
Here are links to the issues that we completed in this sprint: <br>(Note - These are just the five primary issues that we completed)
* [#1](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=104778136&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C33)
* [#2](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=104778230&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C34)
* [#3](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=104778340&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C35)
* [#4](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=104778416&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C36)
* [#5](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=104590328&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C30)


## Incomplete Issues/User Stories
Here are links to issues we worked on but did not complete in this sprint: <br>(Note - None of these were expected to be completed this sprint. These were simply worked on or brought to attention during this Sprint.)
* [#1](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=98459668&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C14) <Researching the Deep Learning approach to creating a Probability Distribution Model has been worked on all semester. Next Sprint this will become a deliverable/priority for our team.>
* [#2](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=104778058&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C32)<Creating an executable for the program so the user will not have to clone a repository and run python scripts with the necessary dependencies has been discussed but not implemented - to become a priority/deliverable for next Sprint.>
* [#3](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=104777969&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C31)<Adding the mathematic formulas for the distributions was mentioned by our client earlier this Sprint, but has since become a priority for implementation next Sprint.>


## Code Files for Review
Please review the following code files, which were actively developed during this sprint, for quality:<br>
(Please note as we are extending functionality of an existing project, we have modified these files the most from an existing Capstone team as opposed to creating entirely new files ourselves)
* [Main.py](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/main.py)
* [Main View](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/views/main_view.py)
* [Main Controller](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/controllers/main_controller.py) 
* [Impurity Segmentation](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/segmentation_scrips/impurity_segmentation.py)
* [PDF Generator](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/analysis_scripts/pdf_generator.py)

Please review the following code files, which were actively created during this sprint, for quality:<br>
(Please note these files were explicitly created during this sprint with the intent of refactoring the MainView class which had become too large for its scope, and the files mostly contain blocks from the original Main View file.)
* [About View](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/views/about_view.py)
* [Analysis View](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/views/analysis_view.py)
* [Segmentation View](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/views/segmentation_view.py)
* [Download/Export](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/utility/download_handler.py)

## Retrospective Summary
Here's what went well:
* Group and Client communications
* Implementing functionality requested by client
* Repository branch management for structuring group work

Here's what we'd like to improve:
* Asking qualitative questions in client meetings to clarify specific implementation expectations
* Work closer with our client to implement a machine learning model and crater reconstruction process as our client sees fit
* Continue to structure our repository for clearer, smaller goals/stories
  
Here are changes we plan to implement in the next sprint:
* Implementing the initial machine learning model framework for predictive analysis
* Adding additional algorithms to extend functionality of image segmentation for more generalized datasets
* Develop a simple executable for distributing the application (as opposed to sharing/cloning a github repository)


## Demo Video
[Sprint 3 - Demo Video](https://www.youtube.com/watch?v=86fq7HC_81E)
