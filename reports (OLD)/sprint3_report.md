# Sprint 2 Report (3/04/2024 - 4/04/2024)

## What's New (User Facing)

- User input through commandline in impurity Python file

## Work Summary (Developer Facing)

In this sprint, our focus was on creating new programs and adding to previous programs for pore and impurity analysis. Our secondary focus was on developing more detailed documentation for our client to better understand our progress and what we are working on next. This will also help our client answer any questions by being able to look through the documentation. We researched the previous Python files to understand Watershed processing and traditional thresholding. Some of the barriers that we encountered were implementation errors in the watershed algorithm and incomplete implementation of the pore analysis script. Daniel Book was able to create his version of the watershed algorithm now labeled watershed.py. With this new implementation, the results are directly from the watershed algorithm instead of traditional thresholding. For the impurity analysis, the calculations of the pores seem to be incorrect. Thus Daniel Lee worked closely with Dr. Zare on calculations and measurements to make progress toward comparing current automated calculations with the previous manual calculations. Doug started researching and working on deep-learning segmenting models and seeing if the results of these models are more accurate than the segmenting methods we are using now.

## Unfinished Work

One of the barriers of this sprint was being able to have deep learning models to process the pore images. Doug was encountering a lot of difficulty processing the images due to the image size, memory limitations, and processing complexity.

## Completed Issues/User Stories

Here are links to the issues that we completed in this sprint:

https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/20
https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/21
https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/22
https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/24
https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/25
https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/26

## Incomplete Issues/User Stories

Here are links to issues we worked on but did not complete in this sprint:

https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/23

## Code Files for Review

Please review the following code files, which were actively developed during this sprint, for quality:
[Mason_ConvertedSEMIMAGECode.py](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/tree/master/src/Mason_ConvertedSEMIMAGECode.py)
[watershed.py](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/tree/master/src/watershed.py)
[testing.ipynb](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/tree/master/src/testing.ipynb)
[FastSAM.ipynb](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/tree/master/src/FastSAM.ipynb)

## Retrospective Summary

Here's what went well:

- Meeting to assign each person a task until the next time we meet or until it is due
- Communicating through Microsoft Teams
- Meeting in person with the team and Dr. Zare

Here's what we'd like to improve:

- Spending less time on writing assignments and more on the project itself
- Have a more consistant contact with Dr. Zare

Here are changes we plan to implement in the next sprint:

- commit and pull more frequently on github
- More open communication with Dr. Zare over Teams Message

## Demo video
https://youtu.be/kR2cMhj-rts
https://drive.google.com/file/d/1L_gGIn5BiDrB7SnnS7-vWv9Yg_--v6gw/view?usp=drive_link
https://youtu.be/10KFfTW9TSU
