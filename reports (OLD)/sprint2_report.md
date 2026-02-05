# Sprint 2 Report (2/04/2024 - 3/04/2024)

## What's New (User Facing)

- User input through commandline in impurity Python file

## Work Summary (Developer Facing)

In this sprint, our focus was on understanding and adding to previously developed Python programs for pore and impurity analysis. We did so by meeting with our client Dr. Zare and dividing tasks among the team. In addition, we researched the previous Python files to understand Watershed processing and traditional thresholding. Some of the barriers that we encountered were implementation errors in the watershed algorithm, cluttered outputs, and measurement verification. We were able to implement our version of the watershed algorithm now labeled as watershed.py. With this new implementation, the results are directly from the watershed algorithm instead of traditional thresholding. For both the impurity analysis and pore analysis program, we discovered the cluttered results that were confusing to interpret. To solve this issue, both programs now label the pore by number on the image and save all relevant data into a CSV file for further analysis.

## Unfinished Work

One of the barriers encountered was determining the accuracy of measurements for both the impurity and pore analysis. In this sprint, we were unable to solve this issue due to the scale of the problem.

## Completed Issues/User Stories

Here are links to the issues that we completed in this sprint:

https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/8
https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/9
https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/12
https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/14
https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/15
https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/issues/16

## Incomplete Issues/User Stories

Here are links to issues we worked on but did not complete in this sprint:
NA
## Code Files for Review

Please review the following code files, which were actively developed during this sprint, for quality:
[SpallFracture_HoleFinder.py](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/blob/master/src/SpallFracture_HoleFinder.py)
[Mason_ConvertedSEMIMAGECode.py](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/blob/master/src/Mason_ConvertedSEMIMAGECode.py)
[main.py](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/blob/master/src/main.py)
[watershed.py](https://github.com/WSUCptSCapstone-S24-F24/-wsum-pythonapps/blob/master/src/watershed.py)
## Retrospective Summary

Here's what went well:
 * Meeting to assign each person a task until the next time we meet or until it is due
 * Communicating through Microsoft Teams
 * Meeting in person with the team and Dr. Zare
 
Here's what we'd like to improve:
 * Spending less time on writing assignments and more on the project itself
 * Have a more consistant contact with Dr. Zare

Here are changes we plan to implement in the next sprint:
 * commit and pull more frequently on github
 * More open communication with Dr. Zare over Teams Message

## Demo video

https://youtu.be/4G2MHvZt52I
