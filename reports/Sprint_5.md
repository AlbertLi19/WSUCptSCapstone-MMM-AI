# Sprint 5 Report (8/24/25 - 9/13/2025)
## What's New (User Facing)
* Repository src file has a new folder for UNET + MicroSAM annotation prototype
* Repository src file has a new folder for Large SAM prototype 
* Added a brief file reflecting MicroSAM research in the reports repository folder
 
## Work Summary (Developer Facing)
During this sprint, the team primarily did standalone research into computer vision AI/ML models for our client that was not accurately reflected in this repository. The project plan for moving forward was changed by our client, and we spent this Sprint narrowing down a large number of viable computer vision models to just two recommended models, for which we developed prototypes. From these prototypes we selected the most accurate model in regards to our application's context and will move forward with this model for development and integration with our existing application. The two initial prototypes, UNET and SAM, have been added to respective folders in the src directory of our repository. There is also a report that reflects the research into just one of the many models we proceeded to discuss and analyze under the reports folder in the repository. Please note this sprint was only 2.5-3 weeks long given it was the first sprint of the semester and we did not hold our first client meeting until the middle of the second week (8/27), and that our client is satisfied with our progress even if not much technical work has been represented in the repository. 

## Unfinished Work
We have successfully completed all target goals for this sprint as laid out by our client. We spent the sprint primarily doing individual research and team discussion as directed by our client. Moving forward, we have a clear list of items to begin work for the next sprints. These include the total development of a SAM model we prototyped this sprint, testing the SAM model with a variety of Canny edge detection, Gaussian Blurring, and Otsu's Thresholding parameters for the best fitting model, extracting key metadata from the predicted impurity masks created by the model, and finally implementing the model into the existing application. This is work that is just starting near the deadline of Sprint 5, which is why it has been included in this report under the Unfinished Work section. The Completed/Incomplete Stories and Code Files below will reflect our research and prototypes in the repository as best we can. 

## Completed Issues/User Stories
Here are links to the issues that we completed in this sprint:
* [#1](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=127470133&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C48)
* [#2](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=128565647&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C51)
* [#3](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=128565707&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C52)


## Incomplete Issues/User Stories
Here are links to issues we worked on but did not complete in this sprint: <br>(Note - These are items that we did not expect to work on this Sprint but were brought up just two days before the Sprint deadline, which is why we decided to include them in this report.)
* [#1](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=104779656&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C37) <General item for the development of our selected LargeSAM model + integration with the application. Next Sprint this will become a deliverable/priority for our team.>
* [#2](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=128557928&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C49)<Test Canny edge detection parameters with the developed LargeSAM model to see if results are more accurate (Including Gaussian Blurring and Otsu's Thresholding subprocesses for Canny).>


## Code Files for Review
There were no code files that were actively developed or created during this sprint as it relates to the project application. Links to both prototype implementations will be provided, but these were created for Dr. Zare only to reflect the efficacy of each model and provide our team recommendation for which model to move forward with pursuing. You may review the following prototype files, but note they do not reflect explicit application changes. <br>

* [LargeSAM Prototype](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/META_AI_SAM/SAM_sandbox.py)
* [UNET + MicroSAM Prototype](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/UNET/UNET.ipynb)


## Retrospective Summary
Here's what went well:
* Group and Client communications
* Well-received research into CV models 
* Successful prototype implementations
* Selected a AI/ML Computer Vision segmentation model to implement

Here's what we'd like to improve:
* Better reflect completed work in our repository
* Construct a more cohesive team structure for developing and implenting our CV model
* Develop a long-term (semester duration) plan for the project
  
Here are changes we plan to implement in the next sprint:
* Develop and implement a SAM CV segmentation model into our existing application
* Accurately extract key impurity metadata from the segmentation model to be used for analysis
* Test processing method parameters/locations for the most accurate CV model possible

## Demo Video
This is our demonstration video for the sprint. As this sprint involved minimal technical work and no work in regards to our actual application, this demonstration video will show the created prototypes, their results, and demonstrate research completed over the Sprint duration. 
<br>[Sprint5 - Demo Video](https://www.youtube.com/watch?v=sfMhqAjj1-I)
