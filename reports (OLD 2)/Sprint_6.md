# Sprint 6 Report (9/14/25 - 10/11/2025)
## What's New (User Facing)
* Application has a new 'SAM Segmentation' button that will utilize the new SAM segmentation process
* Application scaling parameter is better reflected on the user setting display
 
## Work Summary (Developer Facing)
During this sprint, the team primarily developed the SAM segmentation process within the existing application. We researched, tested, and implemented a robust SAM model that we believe performs more accurate segmentation using advanced computer vision when compared to the existing process that is more algorithmic in nature. We implemented multiple SAM methods in our code files and dropped an actual SAM_segmentation() function into the existing metadata extraction pipeline. This means as we adjust our SAM mode or decide to use a different SAM model, our modular approach to the code files allows this to be a simple adjustment programmatically. We ensured this SAM process worked well with our existing funcionality, such as the file/image downloads, the histogram creations, and the general analysis process. In terms of application implementation, we added a seperate button for the SAM segmentation process while leaving the current algorithmic segmentation button. This may be further polished later in the semester as we move into GUI polishing. 

## Unfinished Work
We have successfully completed almost all target goals for this sprint as laid out by our client. The primary work to be completed was this SAM segmentation model which we successfully researched, tested, and implemented within our existing desktop application. However, we still feel that we have more work to do in regards to testing the metadata extraction pipeline as it pairs with our new SAM processes. We are finding previous errors that had gone undiscovered as it relates to the user-input scaling factors, and we are currently working on tracking and changing this process entirely. It is unsure if we should considered this "Unfinished Work" as this was not a work item we expected to complete that was not completed - it was a work item that came up during other implementations that became a priority and is still actively under development. Regardless, we decided to include it in this section for documentation.  

## Completed Issues/User Stories
Here are links to the issues that we completed in this sprint:
* [#1](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=128557928&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C49)
* [#2](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=129898857&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C53)
* [#3](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=102952209&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C23)
* [#4](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=104779656&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C37)


## Incomplete Issues/User Stories
Here are links to issues we worked on but did not complete in this sprint: <br>(Note - These are items that we did not expect to work on this Sprint but were brought up just two days before the Sprint deadline, which is why we decided to include them in this report.)
* [#1](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=129898889&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C54) <General item for the comparison of the traditional algorithmic segmentation approach and our recently implemented CV SAM approach, using KL Convergence and distribution analysis.>
* [#2](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=133047045&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C55)<Manually annotate a dataset so that we have confident results as we compare all implementations and decide which approach to move forward with. Use ROBOFLOW to manually annotate each impurity and extract the sizing/spacing metadata.>
* [#3](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=133284992&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C56)<Confirm the calculations and general process for the user-input scaling value. Refactor the logic to put all units in pixels (until a final conversion at the very end).>


## Code Files for Review
Please review the following code files, which were actively developed during this sprint, for quality:<br>
(Please note as we are extending functionality of an existing project, these files have been modified and were originally previously created by this Capstone team or an existing Capstone team).
* [Impurity Segmentation](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/segmentation_scrips/impurity_segmentation.py)
* [Main Controller](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/controllers/main_controller.py)
* [Main View](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/views/main_view.py)
* [Segmentation View](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/views/segmentation_view.py)

Please review the following code files, which were actively created during this sprint, for quality:<br>
* [SAM Segmentation Script](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/segmentation_scrips/SAM_segmentation.py)
* [SAM View](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/views/SAM_view.py)


## Retrospective Summary
Here's what went well:
* General Group and Client communications
* Successful 'offline' communication between our Capstone group and our client's student researcher as it relates to specific work items
* Successful prototype implementations
* Successful implementation of CV model into existing application

Here's what we'd like to improve:
* Better reflect completed work in our repository
* Better document our bug tracking/findings in the code for future work
* Develop a long-term (semester duration) plan for the project
  
Here are changes we plan to implement in the next sprint:
* Continue testing better SAM parameters as necessary
* More accurately extract key impurity metadata from the segmentation model to be used for analysis
* Solve scaling issue that causes metadata extraction results to be scaled incorrectly
* Begin the final step of our project in GUI polishing and final fixes as directed by our Client

## Demo Video
This is our demonstration video for the sprint. This video demonstrates our desktop application with the new SAM segmentation process. Demonstrated is the existing process for traditional algorithmic segmentation, our SAM segmentation process, and an additional SAM process currently in development for the metadata extraction. The video also briefly highlights the scaling issue that has been mentioned in this report. Note that for some larger computations, the video has been stitched to save time (which will be noted in the video).  
<br>[Sprint6 - Demo Video](https://www.youtube.com/watch?v=l3Q9yJ56vBI)
