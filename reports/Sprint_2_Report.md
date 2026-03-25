# Sprint 2 Report (February 23rd 2026 - March 24th 2026) 

 

## https://youtu.be/fonhKR3EcJ8 


 

## What's New (User Facing) 

 * Regression Model built off sample data 

 * Manual value input for scale per pixel 

 * Fixed resetting application button to properly reset 

 * Fixed scaling display in tip window 

 * Fixed the display of blur type and kernel size settings 

 

## Work Summary (Developer Facing) 

During this sprint, our team focused on two separate areas: maintaining/improving the prior code, and working on the forward model. In order to create this model, we needed to create a regression model to convert the data of the segmentation masks obtained from the Segment Anything Model into a prediction of the alloy’s strength. Therefore, we worked on creating such a regression model during this sprint. 

We had some trouble loading dependencies and building the application itself, some of the libraries were out of order in the requirements.txt document and some had been updated since the application was first made. We were eventually able to get it to work and we plan on adding a known working environment description to the project, or updating the code/libraries to their current versions. Additionally, despite the lack of documentation and commenting in the prior code, we were able to make multiple UI changes that the client had requested. 

 

## Unfinished Work 

There remain issues with the GUI that we did not get to finish in time for this sprint. We ran into issues with dependencies and getting the prior code to consistently run, which greatly delayed us. The lack of documentation and commenting in the previous code also meant that we struggled to stay on track dealing with the UI issues. 

 

## Code Files for Review 

Please review the following code files, which were actively developed during this sprint, for quality: 

[heart.csv] (https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/blob/main/heart.csv) 

[main.py (regression model)] (https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/blob/main/main.py) 

[src/app/segmentation_view.py] (https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/blob/main/src/app/views/segmentation_view.py) 

[src/app/widgets/scale_dialog.py] (https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/blob/main/src/app/widgets/scale_dialog.py) 

[src/app/widgets/image_widget.py] (https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/blob/main/src/app/widgets/image_widget.py) 

[.gitignore] (https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/blob/main/.gitignore) 

 
  

## Retrospective Summary 

Here's what went well: 

  * Item 1: Able to deploy and make sure no bug for reset application button 

  * Item 2: Multiple UI bug fixes (multiple settings were not being displayed) 

  * Item 3: Adding a manual input scaling capability 

  

Here's what we'd like to improve: 

   * Item 1: Make sure the project is updated to current dependency libraries 

   * Item 2: Continue working on and improving the Forward Model 

   

Here are changes we plan to implement in the next sprint: 

   * Item 1: Work more on UI bugs and improvements 

   * Item 2: Implement the Forword Model 

   * Item 3: Do more research on and hopefully imlpement a Reverse Model 
