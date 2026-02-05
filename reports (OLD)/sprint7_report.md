# Sprint 7 Report (10/14/2024 - 11/13/2024)

## What's New (User Facing)
* New thread for running segmentation in the GUI
* More accurate user-specified GUI parameters
* Data visualization incorporated in the GUI
* Data CSV created for each individual image
* More image blur and thresholding options
* Data anylsis comaprison for segmented data with original data
* Kernel Density Estimation added for verifying data results

## Work Summary (Developer Facing)
In this sprint we enhanced the functionality of the GUI so it supports even more functionality of the existing impurity segmentation script. Users can now control more parameters before segmentation, and the collected data can be visualized as histograms in the GUI. We also completed the functionality of the image segmentation script, enhancing the user parameter capability for image segmentation and optimizing the data extraction/visualization, with the focus now being to fully implement it into the GUI. On the Backend, we can now compare segmented results with orginal data and how they differ. Additionally Kernel Density Estimation functionality was added for data verification.

## Unfinished Work


## Completed Issues/User Stories
Here are links to the issues that we completed in this sprint:

* [#58](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/58)
* [#64](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/64)
* [#53](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/53)
* [#65](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/65)
* [#69](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/69)
* [#63](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/63)
 
## Incomplete Issues/User Stories
Here are links to issues we worked on but did not complete in this sprint:


## Code Files for Review
Please review the following code files, which were actively developed during this sprint, for quality:
* [main_controller.py](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/blob/master/src/app/controllers/main_controller.py)
* [Mason_ConvertedSEMIMAGECode.py](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/blob/master/src/app/segmentation_scrips/Mason_ConvertedSEMIMAGECode.py)
* [main_view.py](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/blob/master/src/app/views/main_view.py)
* [parameter_dialogs.py](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/blob/master/src/app/widgets/parameter_dialogs.py)
* [kdeauto.py](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/blob/master/src/Data_Driven_Model/kdeauto.py)
* [kdemanual.py](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/blob/master/src/Data_Driven_Model/kdemanual.py)
* [hist.py](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/blob/master/src/Data_Driven_Model/hist.py)
* [combine.py](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/blob/master/src/Data_Driven_Model/combine.py)
 
## Retrospective Summary
Here's what went well:
* GUI now supports more accurate parameter specification
* GUI has more overall functionality
* Team communication increased
* Finalizing the data and visual outputs of the image segmentation script
* Implementing more blur/thresholding options
* comparison of segmented data and original data
 
Here's what we'd like to improve:
* More dynamic allocation of outputs on the user's system
  
Here are changes we plan to implement in the next sprint:
* Finalize GUI parameter specification
* Full script/GUI integration (important to consider scale factor)
* Find why there is variation in default orientation and segmented orientation

## Demo Videos
* [sprint-7-takada/sprint-7-all](https://www.youtube.com/watch?v=l61HLhI-FLk)
* [sprint-7-book/sprint-7-all](https://youtu.be/XGB65TbrfjU)
* [sprint-7-lee/sprint-7-all](https://drive.google.com/file/d/1A7NNzx45c-Ed-dgF11dMFRqFRGkoMLnG/view?usp=drive_link)
