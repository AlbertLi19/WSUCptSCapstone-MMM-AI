# Sprint 2 Report (2/3/25 - 3/2/2025)
## What's New (User Facing)
* GUI refactored to darker mode with different button/font themes
* GUI contains new buttons for the new functionality we added in batch segmentation and multi-image analysis
* GUI contains an entirely new tab for statistical analysis generation

  
## Work Summary (Developer Facing)
In this sprint, our focus was extending functionality of the existing project to implement a few core changes as requested by Dr. Zare. We successfully met with our client for each set meeting and our project team met multiple times per week to track progress and continually update the group plan. We added our initial implementation of batch segmentation for multi-image analysis, first adding the ability for the program take multiple images or a folder of images as input. All images will be loaded and processed individually with the ability to click through and view each image, segmented image, and histogram output through added arrow buttons. The ability to apply current settings to all uploaded images was added for a quality-of-life update. We refactored the GUI to create a more intuitive layout and add aesthetic changes to locations, color schemes, and fonts. Buttons were added as necessary to support entirely new functionality (clicking through multiple images, applying segmentation settings to all images). We added a multi-image statistical analysis to create histograms and probability distribution functions on the dataset created by all processed images, so that entire datasets can be interpreted at a time. This has been shifted to its own tab in the GUI and extended from single image analysis in the previous project. 

## Unfinished Work
We are still actively working to implement a more traditional batch-segmentation. While we have completed our initial multi-image implementation, we have continually been researching optimization techniques for the computationally heavy parts of the project. As outlined by our project team and project client, Dr. Zare, the focus of this sprint was to add functionality for uploading multiple images to the program for segmentation analysis, and outputting intrepretable histogram and PDF graphs for the entire dataset, which we completed. We also are continuing to work on optimizing the PDF generation functions. All User Stories with the intent of being completed for this sprint have been finished successfully. 


## Completed Issues/User Stories
Here are links to the issues that we completed in this sprint:
* [#1](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=99779569&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C15)
* [#2](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=99998680&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C19)
* [#3](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=96146476&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C7)


## Incomplete Issues/User Stories
Here are links to issues we worked on but did not complete in this sprint:
* [#1](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=99779641&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C16) <This will be an ongoing optimization process as we continue to look for ways to speed up the PDF generation and general statistical analysis process - we intended for this to be ongoing past this sprint.>
* [#2](https://github.com/orgs/WSUCptSCapstone-S25-F25/projects/1/views/1?pane=issue&itemId=99998634&issue=WSUCptSCapstone-S25-F25%7C-wsum-fullstackapp-%7C18)<This is the second edition of our multi-image segmentation process, we are looking to implement a more traditional pipelined batch segmentation process to further optimize the segmentation on large datasets. We intended this for next sprint but were able to begin earlier.>


## Code Files for Review
Please review the following code files, which were actively developed during this sprint, for quality:
(Please note as we are extending functionality of an existing project, we have modified these files the most from an existing Capstone team as opposed to creating entirely new files ourselves)
* [Main View](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/views/main_view.py)
* [Main Controller](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/controllers/main_controller.py) 
* [Impurity Segmentation](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/segmentation_scrips/impurity_segmentation.py)
* [PDF Generator](https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-/blob/main/src/app/analysis_scripts/pdf_generator.py)


## Retrospective Summary
Here's what went well:
* Group and Client communications
* Implementing functionality requested by client
* Repository branch management for structuring group work

Here's what we'd like to improve:
* Understand the detailed exporting/output expectations of our client, post image processing 
* Updated functionality priority for our client (optimization, gui, multi-image, more algorithms, etc.)
* Continue to structure our repository for clearer, smaller goals/stories
  
Here are changes we plan to implement in the next sprint:
* Implementing the next rendition of multi-image batch segmentation for faster processing
* Adding additional algorithms to extend functionality of image analysis
* Further increase the speed of the PDF generation process


## Demo Video
[Sprint 2 - Demo Video](https://www.youtube.com/watch?v=Z8xBOdtd0HI)
