# Sprint 8 Report (11/9/25 - 12/6/2025)
## What's New (User Facing)
* Application has a single, final downloadable executable
* Project Roboflow repository has an entire dataset of manually annotated training data

 
## Work Summary (Developer Facing)
During this sprint, the team continued to manually annotate a ground-truth dataset to determine accuracy of our computer vision models. The team also manually annotated every SEM image available so that a future Capstone team may have a large set of training data. The team then moved forward into specific bug fixes received from our client and other testers. The largest implementation of this Sprint was a downloadable executable that will dynamically update through the repository. The user can download a single, wrapped version of the desktop executable to use all functionality. The final executable items include the Segmentation Process, both algorithmic and computer vision, the Analysis Process for determining best-fitting Probability Distribution Functions, and the Comparison Tab for determining similarity metrics between multiple datasets.

## Unfinished Work
We have successfully completed all target goals for this sprint as laid out by our client. Any primary work to be completed will extend into a further Capstone team developing upon our existing project. All items identified by both this Capstone team and our client have been completed and successfully demonstrated. Future work for a future team includes further manually annotating a training dataset for a more specific computer vision segmentation model, further improving the accuracy and abstractability of the existing algorithmic approach, and adding future statistical or analytical insight.

## Completed Issues/User Stories
Here are links to the primary issues that we completed in this sprint:
* [#1](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=139243393&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C67)
* [#2](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=138768879&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C64)
* [#3](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=138768882&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C66)
* [#4](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=138768877&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C63)


## Incomplete Issues/User Stories
There are no Incomplete Issues on our project board remaining for the project as the scope of deliverables from this year have been completed. The only remaining work for this Capstone team will be completing some manual annotations for our client, agreed upon to be completed during Finals Week. 
A project board item has been created [here](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=143310984&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C68)


## Code Files for Review
Please review the following code files, which were actively developed during this sprint, for quality:<br>
(Please note as we are extending functionality of an existing project, these files have been modified and were originally previously created by this Capstone team or an existing Capstone team).
* [Analysis Tab](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/analysis_scripts/pdf_generator.py)
* [Comparison/KL Divergence](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/comparison_scripts/kl_divergence.py)
* [Main Controller](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/controllers/main_controller.py)
* [Main View](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/views/main_view.py)
* [SAM Segmentation](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/segmentation_scrips/SAM_segmentation.py)
* [Algorithmic Segmentation](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/segmentation_scrips/impurity_segmentation.py)
* [About Tab](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/views/about_view.py)

There were no new code files actively created during this sprint.


## Retrospective Summary
Here's what went well:
* General Group and Client communications
* Successful 'offline' communication between our Capstone group and our client's student researcher as it relates to specific work items
* Successful manual annotations
* Successful deployment of a dynamically updating executable for our application across different operating systems.

Here's what we'd like to improve:
* Better reflect completed work in our repository
* Better document our bug tracking/findings in the code for future work
* Develop a long-term future work plan for a future team, highlighting work we deem feature complete
  
Here are changes we recommend to implement in the next sprint, for a future team:
* Continue testing better SAM parameters as necessary
* Utilize training data to add a more accurate model to microscopic impurities
* Extend analysis functionality

## Demo Video
This is our demonstration video for the sprint. This video is a presentation of the project overview and our design approach. It contains a brief overview of the application and all work completed during this year. 
<br>[Sprint8 - Demo Video](https://www.youtube.com/watch?v=_xYyvrCy5BU)
