# Sprint 6 Report (9/14/2024 - 10/13/2024)

## What's New (User Facing)
* Additional compressive strength/impurity data mined from research reports
* Image cropping feature for the UI
* MLE/FWHM best fit script

## Work Summary (Developer Facing)
In this sprint, we were able to complete developing the script that allows us to find the best fit distribution of data to find the MLE and FWHM for any feature given a excel/csv file. 
We are then able to use these values to map them to strength values in Orange to determine the best ML model to use for future predictions.
Data mining academic research reports for peak compressive strength data continued as we aim to further expand our dataset for training the ML model, but this time we also looked for more impurity data regarding measurements such as size and spacing, typically obtained from histograms.
On top of that, we improved the user friendliness of the GUI by adding image scaling and cropping functionalities, while also integrating the impurity segmentation script.


## Unfinished Work
Issue #53 could not be completed because it was a more broader goal of improving upon the image segmentation script which requires a lot of research and testing of the code libraries used, thus more time being needed, especially since much of the sprint was spent on data mining.
Issue #58 could not be completed because we decided to put more time into deciding which parameters should be editable by the user.


## Completed Issues/User Stories
Here are links to the issues that we completed in this sprint:

* [#43](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/43)
* [#51](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/51)
* [#52](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/52)
* [#54](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/54)
* [#55](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/55)
* [#56](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/56)
* [#57](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/57)
 
## Incomplete Issues/User Stories
Here are links to issues we worked on but did not complete in this sprint:

* [#53](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/53)
* [#58](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/58)

## Code Files for Review
Please review the following code files, which were actively developed during this sprint, for quality:
* [dist_MLE_FWHM.py]() 
* [Compressive Strength Research Data.xlsx]()
* [Mason_ConvertedSEMIMAGECode.py]()
* [main_controller.py](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/blob/master/src/app/controllers/main_controller.py)
* [impurity_script.py](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/blob/master/src/app/segmentation_scrips/impurity_script.py)
* [main_view.py](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/blob/master/src/app/views/main_view.py)
* [image_widget.py](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/blob/master/src/app/widgets/image_widget.py)
 
## Retrospective Summary
Here's what went well:
* Data mining produced more usable research data for the client
* Understanding/practice with Orange
* GUI now supports basic functionality of loading and segmenting images
 
Here's what we'd like to improve:
* More consistent, online communication with the client
* Meet with team members more frequently
* Produce more consistent commits to the repo
* Accuracy of the image segmentation script
  
Here are changes we plan to implement in the next sprint:
* Combining our individual works together where relevant
* Determine why MLE values are significantly higher than expected results
* Change GUI functionality to be more specific to segmentation needs

## Demo Videos
* [sprint-6-takada](https://youtu.be/IcJlgTLNvko)
* [sprint-6-book](https://youtu.be/Uu2Kbji9b0k)
* [sprint-6-lee](https://drive.google.com/file/d/1XTBPXSTjSPb-Yxzfnd2J_TWxKY_VADoD/view?usp=sharing)
