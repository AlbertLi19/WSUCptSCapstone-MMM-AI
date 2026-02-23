# Client Meetings Report

## Agenda (12/3/2025)
There was no meeting on Wednesday December 3rd as our client double-booked a meeting and had to cancel. Documentation from our Teams channel is below: <br>
<img width="1089" height="94" alt="image" src="https://github.com/user-attachments/assets/7448d853-53e7-400b-9614-f23fd4052c63" />
<img width="1229" height="386" alt="image" src="https://github.com/user-attachments/assets/31082955-944d-4538-a65a-2a0bf93a4d0d" />

---

## Agenda (11/26/2025)
There was no meeting on Wednesday, November 26th as it was Thanksgiving break - a University holiday.

---

## Agenda (11/19/2025)
* Discuss the executable implementation
* Discuss any changes required for the Comparison tab
* Plan future work items that extend to the end of the semester
  
## Minutes (11/19/2025)
Our team met with Dr. Zare this week to discuss and demonstrate the polishing items we completed, as well as discuss some changes we made to the Comparison tab. We demonstrated the working Analysis/Comparison functionality and confirmed the data pipeline of the application. After this, we talked about the future of documentation for the project as it related to a future Capstone team. It was determined it would be possible that a future team would take over a different aspect of this project, but uncertain. We then finalized a plan for Thanksgiving break, delivering a series of more manually annotated images and our finalized executable. We discussed the expectation for documentation as it related to all work completed up to this point, and then made a plan to meet Wednesday, December 3rd as next week would be Thanksgiving break.

## Retrospective Summary (11/19/2025)
Here's what went well:
* Successfully communicated GUI changes as it relates to Analysis/Comparison
* Successfully communicated challenges with executable deliverable
* Make a very clear plan for the next week of work

Here's what we'd like to improve:

* Better document the changes we have made in the project board
* Further improve documentation as it relates to completed work, for future teams
  
Here are changes we plan to implement as soon as possible:

* Additional work with ROBOFLOW to created Ground-Truth annotated masks to compare results
* Complete final changes to the downloadable executable
* Complete final GUI and repo polishing

---

## Agenda (11/12/2025)
* Discuss how the final application should be distributed
* Discuss anything relating to SAM vs Otsu vs Ground-Truth
* Plan future work items that extend to the end of the semester
  
## Minutes (11/12/2025)
Our team met with Dr. Zare this week to discuss the future of the application. We agreed that as the end of semester was approaching, we would identify final work items and final project deliverables. We started by demonstrated the large GUI changes as it related to removing depreciated tabs and reorganizing our structure for process tabs (Segmentation, Analysis, Comparison, About). We then discussed the future of the project as it relates to research applications. We agreed that we could either create a downloadable executable for the application that would be easy for single-use download and would dynamically update with repository changes, or create a simpler repository for cloning with explicit dependencies and only core functionality for cleanliness. We decided to implement the executable, as this would be easier for others to get to use the application practically. We then brought up a few polishing items we would like to complete before the following week.

## Retrospective Summary (11/12/2025)
Here's what went well:
* Successfully communicated GUI changes
* Successfully determined plan for an executable
* Make a very clear plan for the next week of work
  
Here's what we'd like to improve:

* Better document the changes we have made in the project board
* Further improve documentation as it relates to completed work, for future teams
  
Here are changes we plan to implement as soon as possible:

* Additional work with ROBOFLOW to created Ground-Truth annotated masks to compare results
* Confirm accuracy of Comparison tab functionality
* Complete final GUI and repo polishing

---

## Agenda (11/5/2025)
* Share results from our new Analysis implementation
* Discuss changes and problems with the new Comparison Tab
* Plan future work items that extend to the end of the semester
  
## Minutes (11/5/2025)
Our team met with Daniel this week, as Dr. Zare was out of town at a conference. We talked about our technical implementations over the previous week. We successfully made the major GUI changes as it relates to adding and removing different process tabs, but we still wanted to discuss the best way to explicitly save data from the Analysis tab so that the User may select their desired files in the Comparison tab. We implemented all the back-end logic for the computations. We worked through a demonstration of our Analysis process, and where we had used all generated probabilities to create the PDF charts, it was expressed we need only generated a list of probabilities from the PDF with the greatest accuracy. From here, saving data and plotting the average PDF would be much simpler for the KL Divergence computation. It was a shorter meeting than most as we demonstrated our progress, got some feedback for what we should change, and developed a clear plan for completing the 2-3 week long task by next meeting.  

## Retrospective Summary (11/5/2025)
Here's what went well:
* Successfully communicated Analysis results
* Successfully gathered additional information for the Comparison Tab
* Make a very clear plan for the next week of work
  
Here's what we'd like to improve:

* Better document the changes we have made in the project board
* Make a more comprehensive plan regarding the end of semester deadlines
  
Here are changes we plan to implement as soon as possible:

* Additional work with ROBOFLOW to created Ground-Truth annotated masks to compare results
* Out of all our segmentation processess, determine the most accurate for implementation
* Complete the Comparison Tab

---

## Agenda (10/29/2025)
* Discuss our preliminary implementation of new analysis code
* Discuss major GUI changes that the new analysis may require
* Move forward with establishing work items for the following week
  
## Minutes (10/29/2025)
Our team met with Dr. Zare to discuss our questions with the new analysis process, and make some larger-scale changes to the application. This week changed a lot of the expectations regarding our application and removed some existing work we had completed in prior Sprints. We discussed removing the Crater Analysis tab, as the new application would further focus on dataset comparisons between microscopy datasets. We then decided to add a comparison tab, to handle the logic for generating compared PDF overlays and final KL Divergence values between a pair of datasets. Over the previous week we had implemented a new strategy for generating the PDF probabilities, but we were asked to adhere closely to the provided script and hardcode a small group of preselected PDFs (Weibull, Exponential, and Lognormal, just to name a few). We discussed some GUI logic regarding what the user would be able to select and where, and settled on the Analysis tab acting as the primary single-dataset generation process where the Comparison tab would compare two PDF curves and calculate their KL Divergence value.  

## Retrospective Summary (10/29/2025)
Here's what went well:
* Successfully completed a preliminary analysis implementation
* Discussed some existing metadata analysis code provided for our application
* Make a very clear plan for the next week of work items
  
Here's what we'd like to improve:

* Better document the changes we have made
* Better understand the code provided by the laboratory so we may ask better questions regarding implementation
  
Here are changes we plan to implement as soon as possible:

* Begin work implementing the new analysis process (probability bar graph, plotted PDF)
* Out of all our segmentation processess, determine the most accurate for implementation

---

## Agenda (10/22/2025)
* Discuss results of our manual annotations
* Discuss our work regarding reestablishing pixel measurements
* Move forward with establishing work items for the following week
  
## Minutes (10/22/2025)
Our team met with Dr. Zare to discuss and demonstrate our results with the manual annotations with ROBOFLOW. We also had been working on solving a computation bug in the application, which we discussed. Instead of converting the pixel lengths to Nano  Meters and then doing an additional conversion at the end, depending on what measurement the User selected, we left all computations in their pixel form for a final, single computation at the end. This cleared up a few errors we discovered and made some coding notation more readable. We moved on to Daniel discussing where he was with extracting the metadata from the manual masks we had annotated. We then discussed some possible changes to the Analysis tab in the application. Instead of our existing best PDF generation, we discussed possibly using the program to generate a bar graph of all the most probable PDFs for a specific dataset. With one specific PDF generated, we may be able to calculate a single KL-Divergence value for overall PDF comparison between datasets. We received an existing hardcoded script that performed the KL Divergence calculation for another application that we may use as a framework. We decided to spend the week working on refactoring our Analysis tab, implementing the newer PDF probability generation. From here, we would be able to further implement the PDF and KL Divergence analysis in a future week. 

## Retrospective Summary (10/22/2025)
Here's what went well:
* Successfully implemented a measurement change which uses pixels instead of the error-prone NM measurement
* Successfully demonstrated success with our current SAM model
* Successfully manually annotated all required images on ROBOFLOW 
  
Here's what we'd like to improve:

* Better document the changes we have made on the project board tab
* Add our manually annotated images to the repository
  
Here are changes we plan to implement as soon as possible:

* Begin working with KL Divergence and understanding the new analysis process we may be implementing
* Additional work with fixing a few annotated images that were not up to standard

---

## Agenda (10/15/2025)
* Share results from our implemented SAM
* Discuss the ROBOFLOW expectations
* Move forward with establishing work items for the following week
  
## Minutes (10/15/2025)
Our team met with Dr. Zare to discuss the compared results between the SAM, OTSU, and Canny implementations. The SAM model performed the best, which was expected as it was a pretrained CV model, but we decided to prove this accuracy by manually annotating a dataset and running these models again. This way, we would know for certain the accuracy of an automated segmentation implementation. Daniel, Dr. Zare's research assistant, provided us with a link to a ROBOFLOW project. We discussed creating accounts and joining the project, and each taking some images from the selected dataset so we may use ROBOFLOW annotation tools to create manually annotated masks. Our project team would be responsible for the annotations, and Daniel would work towards using the data from these annotations to create the ground-truth. We were given a brief tutorial with ROBOFLOW and what the impurity selection expecations would be. The entire meeting was related to these manual annotations, and we left with a clear requirement for work over the next week. 

## Retrospective Summary (10/15/2025)
Here's what went well:
* Successfully communicated model results
* Created ROBOFLOW accounts and understand the tools necessary for work
* Make a very clear plan for the next week of work items
  
Here's what we'd like to improve:

* Better understand our SAM model so we may describe the accuracy comparisons between SAM, Canny, OTSU, and other algorithms
* Decide if we should annotate masks or bounding boxes, for both ground-truth analysis and possible CV model training data 
  
Here are changes we plan to implement as soon as possible:

* Begin the manual annotation of ROBOFLOW mask images

---

## Agenda (10/8/2025)
* Share results from our implemented SAM
* Compile a CSV of iamge metadata for accuracy/comparison
* Move forward with establishing work items for the following week
  
## Minutes (10/8/2025)
Our team met with Dr. Zare to discuss and demonstrate the tabulized results we gathered regarding image metadata (sizing, spacing, distances, etc.) using our automated segmentation process with SAM. Dr. Zare's research assistant looked over the results and noted they looked more accurate than previous results. Dr. Zare then asked if we could add this SAM implementation to our desktop application, which we had already completed. We then discussed creating a dataset of manual annotations so we could compare the different segmentation processes we had been implementing to a specific, ground-truth dataset. We discussed ROBOFLOW vs AutoSAM for annotations, before settling on ROBOFLOW. We would then need to make ROBOFLOW accounts for working as a group to annotate these masks. After this, we discussed our calculation issue with units in pixels versus microns versus nanometers. We decided to leave all units in pixels and do a final conversion at the very end where necessary. We left the meeting with a plan to confirm our SAM results, work through the pixel/micron calculation errors in the program, and working with Dr. Zare's research assistant to manually annotate a dataset for confirmation when comparing segmentation processes to find the most accurate. After we complete this step, we will move on to general GUI polishining and final touches for the rest of the semester. 

## Retrospective Summary (10/8/2025)
Here's what went well:
* Successfully communicated model results
* Shared CSV files and created segmentation mask images over Onedrive
* Make a very clear plan for the next week of work items
  
Here's what we'd like to improve:

* Better document the changes we have made
* Continue to work with our SAM implementation and tune parameters to pick up smaller impurities
  
Here are changes we plan to implement as soon as possible:

* Begin working with ROBOFLOW to created Ground-Truth annotated masks to compare results
* Out of all our segmentation processess, determine the most accurate for implementation

---

## Agenda (10/1/2025)
* Lack of meeting Agenda this week given the meeting was not held. 

  
## Minutes (10/1/2025)
Dr. Zare had to cancel our weekly meeting for the week. The following is a Teams screenshot reflecting this communication: <br>

<img width="700" height="102" alt="image" src="https://github.com/user-attachments/assets/7d65288f-aa0f-4f91-9d10-9d24b997e47c" />


## Retrospective Summary (10/1/2025)
The meeting was not held, but we had an initial plan to communicate with Daniel as we moved forward continuing work from the previous week. 

---

## Agenda (9/24/2025)
* Demonstrate our results from the previous week
* Compare result efficacy and discuss how to move forward
  
## Minutes (9/24/2025)
Our team met with Dr. Zare and Daniel to discuss our results from the previous week. It was a slightly shorter meeting compared to our normal 45 minute blocks. We started by sharing the created Excel files of our sizing/spacing data, which appeared to be wildly different from what Daniel and Dr. Zare were expecting for values. After communicating our process and data pipeline, we realized our sizing file was in units squared, whereas the expected sizing value from Dr. Zare was the length of longest line withinin an impurity. Our sizings were similar in scale yet we had thousands of sizing values instead of the expected hundreds. The primary difference in our values was we extracted this metadata using built-in functionality from the SAM model we implemented. However, this metadata was fundamentally different than the more specialized metadata Dr. Zare was aiming to achieve. We made a plan moving forward to use the existing data pipeline in the application for extracting sizings and spacings, as these calculation functions had already been tested and confirmed to be accurate. We then moved forward with this plan to utilize the mask created by our SAM implementation, and then inserting the mask(s) into the existing calculations. This way, we would benefit from the segmentation accuracy of SAM and the specific metadata extraction/calculation that we had previously worked through. 

## Retrospective Summary (9/24/2025)
Here's what went well:
* Successfully communicated SAM results
* Understood the issues with our SAM results
  
Here's what we'd like to improve:

* Find other smaller issues to solve to continue progressing the application besides the one work item up to this point
* Develop semester-long expecations for the project, not just week-by-week
  
Here are changes we plan to implement as soon as possible:

* Utilize metadata extraction from the existing pipeline instead of provided SAM metadata files
* Solve scaling issue that causes inaccurately large resultant metadata
* Implement the SAM model into the desktop application

---

## Agenda (9/17/2025)
* Continue to share prototype results
* Discuss Canny implementation
* Talk about fine-tuning a SAM model
  
## Minutes (9/17/2025)
Our team met with Dr. Zare to discuss and demonstrate our research and practical implementations from the previous week. We started discussing the benefits of Canny Edge detection when compared and/or paired with Otsu's Thresholding as algorithmic segmentation was concerned. We brought up further SAM and Canny models we had researched (SAM2, Canny Script, CannySAM), and how we might fine-tune a custom SAM model for the application. We agreed this would take quite a bit of time and decided to move forward with the preexisting models that appeared to be sufficient. Daniel, Dr. Zare's research assistant, attended the meeting and dicussed his current work with creating ROBOFLOW annotations. He had been working with bounding boxes using a smart-polygon tool and would take about 20 minutes per image to fully annotate. We then went further into detail discussing our practical implementations with our algorithmic watershed approach with a SAM computervision model. We decided we would pursue our SAM models while Daniel worked through the Canny approach, and we would come together in a few weeks to compare our results using KL Divergence (compares distributions for similar/difference metrics). This way, we could quantify the differences between Otsu, Canny, and SAM. From here we moved forward with our plan for the following week, which was extracting image metadata (sizing, spacing) from our SAM model. Daniel indicated a specific folder that was giving him the most trouble for us to try. The work for the week would be attempting to extract this key metadata and then comparing our results to Daniels results for an overall comparison of the methods.

## Retrospective Summary (9/17/2025)
Here's what went well:
* Successfully communicated prototyping results
* Made a clear plan for the following week
* Became more aware of the other processes that were in development for the application
  
Here's what we'd like to improve:

* Further extract key metadata from SAM models in a way that would work with our current data pipeline.
* Develop semester-long expecations for the project, not just week-by-week
  
Here are changes we plan to implement as soon as possible:

* Work with Canny Edge Detection, Gaussian Blurring, and Otsu's Thresholding with our SAM model to find best results
* Find a way to extract sizing/spacing/orientation data from either the SAM model itself, or from the predictive mask
* Begin consideration into how this may be implemented in the existing application

---

## Agenda (9/10/2025)
* Demonstrate our two prototypes and share results
* Meet Dr. Zare's research assistant and discuss his contributions
* Select a final model to move forward with more serious technical implementation
  
## Minutes (9/10/2025)
Our team met with Dr. Zare to discuss and demonstrate the two prototypes we created over the previous week. We had a lengthy and eventful meeting joined by Daniel, the researcher with Dr. Zare's laboratory. We demonstrated the prototypes, selected our target model, discussed Daniel's research and how it may integrate with our plan moving forward, and made a plan for the next week. 

We began the meeting by introducing ourselves to Daniel, Dr. Zare's research assistant who had been working with our application over the summer. We then presented our models. We started with the UNET + MicroSAM annotation model. As we were developing this model without any pretraining, we needed to create a full dataset of annotated masks. We only annotated three masks before creating the UNET model, and therefore the final UNET model was very inaccurate. It was ghosting, creating masks with scratches and impurities that didn't exist. The primary problems with this model was the lack of quality training data. We would want hundreds of annotated training data at a minimum for an effective UNET model, which isn't possible given the number of images we have. It would require carefully annotated every image with serious data augmentation to even get close to 200 images for training data. We then moved on to the SAM model. This was pretrained, 'out of the box', and with extreme accuracy was able to detect almost all impurities when creating a predictive mask. Dr. Zare expressed the quality of this model and how it exceeded all Computer Vision work she and her laboraty had been working towards up to this point. We decided to select this model to move forward with our CV implementation for the application. We decided to test this model on all sorts of images from all our data folders to confirm working accuracy, as well as tweak parameters where necessary. We then discussed how we might extract key data from the predictive mask (impurity size, shape, orientation, etc.). Daniel then gave a presentation regarding his research into Canny edge detection. He discussed that we may want to use Canny edge detection in combination with our selected SAM model to see if the results become even more accurate. He discussed best parameters and where we may want to run Canny (before vs after initial SAM segmentation). We decided to play around with parameters and location to find best results. We briefly discussed Gaussian blurring and Otsu's thresholding, which we already have implemented in our application. The meeting ended with Daniel letting us know that he would send a list of images that the existing model struggled with, so we may test the accuracy of our selected SAM segmentation model. 

## Retrospective Summary (9/10/2025)
Here's what went well:
* Successfully communicated prototyping results
* Shared a quality model with impressive CV results
* Selected a target model and made a clear plan moving forward
  
Here's what we'd like to improve:

* Begin developing technical work in regards to the application itself
* Develop semester-long expecations for the project, not just week-by-week
  
Here are changes we plan to implement as soon as possible:

* Work with Canny Edge Detection, Gaussian Blurring, and Otsu's Thresholding with our SAM model to find best results
* Find a way to extract sizing/spacing/orientation data from either the SAM model itself, or from the predictive mask
* Begin consideration into how this may be implemented in the existing application

---


## Agenda (9/3/2025)
* Discuss our research
* Decide on a few viable models to begin prototyping
* Discuss integration with current application
## Minutes (9/3/2025)
Our team met with Dr. Zare to discuss a week's worth of research into computer vision models that could effectively segment microscopic images. We did not complete any technical work this week, as expected. We narrowed down a large set of models to a few key options that would be the primary discussion for the meeting. 

We began the meeting with discussing Dr. Zare's research assistant who had been working with our application over the summer. She mentioned that he may be joining us next week to discuss his findings in detail. We then presented our research, breaking down all the models we looked into and why, before settling on our two primary recommendations with SAM (Segment Anything Model) and UNET. A pretrained SAM model would not need annotated training data, as we would look for existing, pretrained models on Hugging Face. The UNET model would require annotated training data (used with a Micro-SAM program for annotations) as the model would be developed with custom training data, only using a general model backbone. UNET is a good use case due to it's use in high-resolution microscopic medical images. Dr. Zare discussed the importance of starting simply and then increasingly becoming more complex as the project unfolds. We discussed putting together a collection of resultant images of our prototypes for the next week so we may discuss the accuracy of our presented models. We were told to take note of computing specifications and to keep any model local so that it may work with our preexisting application. We left the meeting with goals of creating two dedicated prototypes, a standalone SAM model and a UNET + MicroSAM annotated model. We would come back next week to compare the results, select a final model to move forward with, and discuss changes Dr. Zare's research assistant made to our program over the summer.

## Retrospective Summary (9/3/2025)
Here's what went well:
* Successfully communicated research results
* Clearly laid out expectations for the next week of work
  
Here's what we'd like to improve:

* Begin developing technical work for the sake of project/repo health
* Develop semester-long expecations for the project, not just week-by-week
  
Here are changes we plan to implement as soon as possible:

* Begin implementing prototypes for a standalone SAM model and a UNET + MicroSAM model to compare accuracies
* Continue consideration into how we might extract key impurity information and integrate with the existing application

---

## Agenda (8/27/2025)
* Reconvene for the first meeting of the semester
* Discuss expectations for general semester goals
* Discuss Dr Zare's findings regarding the application
## Minutes (8/27/2025)
Our team met with Dr. Zare for the first meeting of the semester. We held a few meetings over the summer that we chose to not include in this document, as we decided to not consider work completed over the summer towards a dedicated summer sprint. The primary meeting agenda was discussing findings Dr. Zare and her laboratory discovered during usage of the application throughout the summer. 

The main laboratory findings were that the original algorithmic segmentation process that had been used in this application all semester was incorrectly segmenting/annotating. Created masks were missing certain components and the process struggled in poor lighting or with images that had scratches/excess noise. We attributed this to the difference in our 'clean' development environment to the practical use case of Dr. Zare's laboratory. Instead of moving forward with our expected plan, Dr. Zare wanted to shift all of our focus towards creating a new, better segmentation process. She met with a few other industry professionals who said a ML Computer Vision model is the only way to consistently segment her microscopy images. The meeting adjurned with weekly plan to research viable Computer Vision models and develop a comprehensive plan for moving foward. There was no expectation of technical work to be done. We discussed new methods, such as Canny edge detection, Roboflow, YOLO, SAM, and other pretrained CV models. We discussed the importance of Garbage In, Garbage Out as it comes to CV models. We were told that more datasets for training and a few annotated images would be coming. We discussed a few softwares that Dr. Zare's laboratory had been working with that may or may not be promising. 

## Retrospective Summary (8/27/2025)
Here's what went well:
* Successfully held a meeting and set a concurrent meeting time
* Expectations were clearly laid out for the following week
* Shared interest in the nexts being the pursuit of AI/ML for the application
  
Here's what we'd like to improve:

* Better understand some of the work Dr. Zare's laboratory completed over the summer
* Develop semester-long expecations for the project, not just week-by-week
  
Here are changes we plan to implement as soon as possible:

* Begin research into a large variety of CV models for our impurity purpose
* Begin consideration how we might extract key impurity information and integrate with the existing application

---

## Agenda (4/28/2025)
We did not have a meeting this week (Finals week), as discussed and confirmed by our client and professor throughout this sprint. There was no required Teams update or in-person meeting. 

---

## Agenda (4/21/2025)
* Teams Summary
* Share weekly progress
* Confirm expectations for work to be done the following week
## Minutes (4/21/2025)
Dr. Zare had to cancel our typical weekly meeting for 4/21/2025. We were asked to again provide a summary of our progress for the week, and we remembered discussing that this would be our final meeting of the semester and we would not be meeting during finals, 4/28/2025. The following screenshot is the Teams message between our group and our client, Dr. Zare, for the week. 

![Image](https://github.com/user-attachments/assets/8c08578e-964b-4d5a-be89-1d1813450917)

## Retrospective Summary (4/21/2025)
Here's what went well:
* Quick and qualitative summary of our weekly progress over Teams
* Our completed work in regards to Database, EXE, and Crater Analysis
  
Here's what we'd like to improve:

* Determine client expecations for the client demonstration
* Determine client expectations for the summer meetings
* Develop our team's meeting availability for the summer
  
Here are changes we plan to implement as soon as possible:

* Collect our team meeting availability for our professor and client
* Make a plan for what our client should receive for client demo, assuming no response to our Teams message

---

## Agenda (4/14/2025)
* Demonstrate completion of all deliverables
* Discuss expectations for summer plan
* Demonstrate Crater Analysis implementation
* Develop plan for rest of semester
## Minutes (4/14/2025)
Our team met with Dr. Zare for a comprehensive meeting regarding extensive work completed over the past week. We discussed our near-completion of the Crater Analysis subsection, and then discussed our Database implementation and future plan. We further agreed to a meeting the following week to confirm the end of semester and create a dedicated summer plan. 

Our Crater Analysis subsection was fundamentally complete apart from particular thresholding settings that were easy adjustments programatically (ie, use general voxels over MM), how to select the region of interest in images, and how to select the .tif images in the impact testing dataset for reconstruction and analysis. We then discussed the database implementation in detail regarding the working distribution formula retrieval, which was necessary for a working EXE as writing to internal files (our previous structure) was no longer possible. We decided to extend the Database implementation to allow for saving a wider range of user data (segmentation parameters, analysis thresholds, and even output images). We then discussed the expected output from the Crater Analysis subsection (diameters vary from 17mm to 30mm, depths 3mm to 7mm) and how we might compare our values to deterministic, accurate values from our client's laboratory. We further discussed next meeting would be a more comprehensive summer plan regarding summer meetings and demonstrations. 

## Retrospective Summary (4/14/2025)
Here's what went well:
* Crater Analysis functionalty works (minus particular thresholding settings)
* Database expectations were enhanced and aligned between client and our group
* Completed all deliverables discussed up to this point
* Demonstrating current program functionality
  
Here's what we'd like to improve:

* Prepare a concrete plan for summer meetings
* Prepare a concrete plan for client demonstration slides/documents
  
Here are changes we plan to implement as soon as possible:

* Begin research into the mixed density models for predictive analyses
* Complete the final items for Crater Analysis and Database implementation
* Complete all testing implementations for course requirement

---

## Agenda (4/07/2025)
* Thoroughly discuss Crater Analaysis subsection
* Discuss our summer plan
* Discuss Mixed Density Model research paper
## Minutes (4/07/2025)
Our team met with Dr. Zare for the first meeting of our final sprint of the semester. We had a comprehensive meeting about expectations regarding the Crater Analysis subsection, our current database implementation/future plan, and how we intend to complete work over the summer. We demonstrated brief functionality of what we had thus far, and discussed what we intended to extend in the future week. We also received good feedback in regards to our Crater Analysis subsection regarding our client expectations. We then discussed a Mixed Density Model research paper for our future machine learning approach, and finally discussed wrapping up the final semester and how we may need to slow down work the final weeks of April given the uptick in course load and general course finals. 

We explicitly discussed the usefulness of generalized plots (in Crater Analysis), but the crater volume, diameter, depth are the three primary deliverables for the subsection. We talked about the heatmap recreation and shape graph outputs. The X and Y dimension depths and diameters are the most contextually import outputs. We discussed the nature of the dataset, how the images are taken in temporal succession. We further expanded upon particular implementations of voxel sizes, region areas, and pixel sizes. We then briefly expressed our intent to complete a working EXE deliverable for the application. Then, our client agreed with our plan to complete two sprints over the summer to maintain continuity and familiarity with the project. We then discussed next semester's plan regarding the machine learning implementation of Mixed Density Models to analyze material microstructure, the impact response, and extract meaningful correlation. The focus of the model will be the study of microstructure and material after impact. We then confirmed a client video demonstration would not be required given our qualitative demonstrations all semester, and a brief slidedeck/document would be sufficient. 

## Retrospective Summary (4/07/2025)
Here's what went well:
* Expectations for the next steps in the project are aligned. 
* Completed all deliverables discussed up to this point
* Demonstrating current program functionality
  
Here's what we'd like to improve:

* Clarify end of semester deliverables and portray our summer plan
* Prepare more questions for better clarity in regards to specific implementations
  
Here are changes we plan to implement as soon as possible:

* Begin research into the mixed density models for predictive analyses
* Complete the Database, EXE, and Crater Analysis subsections before end of semester

---

## Agenda (3/31/2025)
* Demonstrate completion of all deliverables
* Discuss expectations for machine learning model
* Discuss nature of impact testing dataset
* Develop plan for rest of semester
## Minutes (3/31/2025)
Our team met with Dr. Zare for a comprehensive meeting regarding work completed over the past few weeks and shifting expectations for the next large-scale goals for implementation. We discussed our completion of every previous item listed in our most recent application. We demonstrated the functionality of the application to Dr. Zare for review, for which we recieved feedback in regards to adding specific distribution formulas in the analysis tab. We discussed the remaining goals for the semester would be the initial implementation of machine learning models and generalizing segmentation for the impact testing dataset. 

The new dataset is in regards to impact testing of small ceramic plates. Given the brittle nature of ceramics, we made note to disregard cracks and focus on the specific impact crater made. Each impact has a large number of image 'slices' for the x, y, and z euclidean dimensions (computer tomography). We should expect to be able to recreate a heatmap of the impact, an algorithmic crater reconstruction. Challenges would be handling such a large number of images per single impact, identifying the start and stop frames, and the non-circular nature of a ceramic plate post-impact crater. We agreed to share a small part of the large dataset for initial implementation accompanied with the corresponding MatLab code. Dr. Zare then discussed a pannel from her convention the previous week that might be helpful in regards to a mixed density model implementation. This model should predict strengths based on microstructure while capturing all variations of experimental results.

At the end of our meeting, we added our repository to Dr. Zare's laboratory github and agreed to focus on creating a specific executable for our project to avoid constant reconstruction of python files/dependencies. We left the meeting with a clear plan for moving forward for the next week and rest of semester.

## Retrospective Summary (3/31/2025)
Here's what went well:
* Expectations for the next steps in the project are aligned. 
* Completed all deliverables discussed up to this point
* Demonstrating current program functionality
  
Here's what we'd like to improve:

* Continue to increase our communicative skills as a group in client meetings
* Prepare more questions for better clarity in regards to specific implementations
  
Here are changes we plan to implement as soon as possible:

* Begin research into the mixed density models for predictive analyses
* Work with provided impact testing dataset and MatLab code for segmentation integration

---

## Agenda (3/24/2025)
* Teams Summary
* Share weekly progress
* Confirm expectations for work to be done the following week
## Minutes (3/24/2025)
Dr. Zare had to cancel our typical weekly meeting for 3/24/2025. We were asked to again provide a summary of our progress for the week, with note to return to standard in-person weekly meetings starting again on 3/31/2025. The following screenshot is the Teams message between our group and our client, Dr. Zare, for the week. 

![Image](https://github.com/user-attachments/assets/4782fc0b-8357-4482-a667-00c297618676)

## Retrospective Summary (3/24/2025)
Here's what went well:
* Quick and qualitative summary of our weekly progress over Teams
* Our completed work in regards to computation tracking and divide-by-zero errors
* Success in export/download button and robust 'About' tab
  
Here's what we'd like to improve:

* Determine the next set of large-scale deliverables to be implemented
  
Here are changes we plan to implement as soon as possible:

* Finish implementing our Reset button and ability to add new images to datasets
* Research Mixed Density Probability neural network
* Prepare segmentation for new impact testing dataset

---

## Agenda (3/17/2025)
* Complete smaller checklist of items to complete
* Complete further bug fixes
* Discuss nature of impact testing dataset
## Minutes (3/17/2025)
Our team met with Dr. Zare to discuss the current state of the project. This was a very brief meeting with a focus on determining any additional criteria for which the client would evaluate our project. We discussed the feasibility of obtaining the impact testing dataset and corresponding MatLab code (MatLab code would be meaningless without first receiving the dataset). We also briefly discussed what cloning our repository to Dr. Zare's laboratory repository would look like in regards to dynamic updates. We decided to continue moving forward with completing the long list of items discussed in our previous group meeting. 

## Retrospective Summary (3/17/2025)
Here's what went well:
* Expectations for the next steps in the project are aligned. 
* Gathered required information regarding additional criteria for evaluation
  
Here's what we'd like to improve:

* Continue to increase our communicative skills as a group in client meetings
  
Here are changes we plan to implement as soon as possible:

* Allow the user to set custom analysis 'timeout' value
* Look into optimizing existing code mega-classes and working through list of known bugs

---

## Agenda (3/10/2025)
* Teams Summary
* Brief communication in regards to work completed before spring break
## Minutes (3/10/2025)
This was the week of spring break. Dr. Zare asked for a brief writeup update for our progress on the week, for which we sent the monday after break with plans to return to standard in-person weekly meetings starting again on 3/17/2025. The following screenshot is the Teams message between our group and our client, Dr. Zare, for the week. 


![Image](https://github.com/user-attachments/assets/f611ca1b-8e47-42ce-a260-a187a23a7a2f)



## Retrospective Summary (3/10/2025)
Here's what went well:
* Completed our set goals for the week from the prior meeting
* Goals met were in line with our client's expectations
* Completed progress/loading bars for both segmentation and analysis
* Implemented ability for user to select which distributions they would prefer for analysis
  
Here's what we'd like to improve:

* Ask more qualitative questions regarding objective, desirable deliverables
* Determine the next set of large-scale deliverables to be implemented
* Faster updates to our client in Teams communiation
  
Here are changes we plan to implement as soon as possible:

* Develop a more robust plan for future goals to complete
* Begin working through our list of general bugs and minor application problems

---

## Agenda (3/03/2025)
* Work to develop quantitative list of deliverables for the next few weeks
* Discuss optimizing SciPy analysis process
## Minutes (3/03/2025)
Our team met with Dr. Zare to discuss the state of our project. We demonstrated our current progress and further developed the plan for future updates. In the 'Analysis' portion of our project, we discussed adding the ability for the user to select which distributions to perform on the dataset, as many of the SciPy distributions are unnecessary and unrelated to the project. Similarly, we discussed adding the distribution formulas to the Excel output file. We talked about adding loading bars for both segmentation and analysis to portray to the user that a computational process was happening and where that process currently stood. 

Dr. Zare then demonstrated a new dataset regarding impact testing and a heat map reconstruction of the impact. We talked about further extending the segmentation functionality to allow for a wider variety of input datasets, such as with the impact testing. We also briefly discussed what a machine learning model might look like in regards to finding correlation between mechanical material testing and impact segmentation data. 


## Retrospective Summary (3/03/2025)
Here's what went well:
* Expectations for the next steps in the project are aligned. 
* Our completed work in regards to GUI, batch segmentation, and analysis met our client's expectations.
* Understanding the impact testing dataset and new required segmentation parameters
  
Here's what we'd like to improve:

* Continue to increase our communicative skills as a group in client meetings
* Ask more qualitative questions regarding objective, desirable deliverables
* Create visual demonstrations of our progress for the client
  
Here are changes we plan to implement as soon as possible:

* Implement loading bars for both segmentation and analysis
* Look into optimizing the existing segmentation and statistical analyses methods through multi-threading functionality

---

## Agenda (2/24/2025)
* Teams Summary
* Completed Initial Multi-Image Statistical Analysis
* Optimized Segmentation Process
* Updated GUI
## Minutes (2/24/2025)
Dr. Zare had to cancel our typical weekly meeting for 2/24/2025. We were asked to again provide a summary of our progress for the week, with note to return to standard in-person weekly meetings starting again on 3/3/2025. The following screenshot is the Teams message between our group and our client, Dr. Zare, for the week. 


![Image](https://github.com/user-attachments/assets/be167cdf-ff26-40e7-a0e5-443e93ebe349)


## Retrospective Summary (2/24/2025)
Here's what went well:
* Expectations for the next steps in the project are aligned. 
* Our completed work in regards to GUI, batch segmentation, and analysis met our client's expectations.
* Quick update to our client in Teams communiation
  
Here's what we'd like to improve:

* Ask more qualitative questions regarding objective, desirable deliverables
* Determine the next set of large-scale deliverables to be implemented
  
Here are changes we plan to implement as soon as possible:

* Develop a more robust plan for increasing the speed of segmentation and analysis generation
* Continue our development of a more traditional multi-batch segmentation
* Look into creating an executable application for the program

---

## Agenda (2/17/2025)
* Teams Summary
* Completed Lazy-Batch Segmentation
* Updated GUI
## Minutes (2/17/2025)
As 2/17/2025 was a University Holiday, Dr. Zare expressed we would not hold our typical weekly meeting that day. We were asked to provide a summary of our progress for the week, adding any supplementary images as necessary. The following screenshot is the Teams message between our group and our client, Dr. Zare, for the week. 


![Image](https://github.com/user-attachments/assets/9a79ba18-4186-4882-9215-7d608024fbe4)


## Retrospective Summary (2/17/2025)
Here's what went well:
* Expectations for the next steps in the project are aligned. 
* Our completed work in regards to GUI, batch segmentation, and analysis met our client's expectations.
* Supplemented weekly summary with visual reflection of our progress.
  
Here's what we'd like to improve:

* Increase our speed of communication for our Teams channel
* Ask more qualitative questions regarding objective, desirable deliverables
  
Here are changes we plan to implement as soon as possible:

* Create a faster statistical analysis generation
* Implement statistical generation for the total set of images uploaded/segmented
* Look into multithreading or other optimization techniques to increase speed of segmentation and generation
* Continue our development of a more traditional multi-batch segmentation

---

## Agenda (2/10/2025)
* Noticeable GUI Problems
* Plotting/Fitter Length
* Lazy-Batch Segmentation
## Minutes (2/10/2025)
Our team met briefly with Dr. Zare this week where we discussed our 'Lazy-Batch' segmentation, which allows for uploading a set of images and running individual segmentation on each one. We talked about our plans for a more typical batch segmentation to integrate images into a staggered pipeline of segmentation for an overall faster implementation. We talked about the GUI changes we had begun to implement and our intended additions, before asking for any GUI requests or noticeable issues. We asked possible preferences with the output of Probability Distribution Functions (PDFs) for the dataset, regarding speed versus accuracy. 


We discussed next steps and desired outcomes for the week. Dr Zare expressed interest in sharing her lab's Github repository login information for us to upload the working project. We asked if Dr. Zare would prefer our group coming into meetings with better reflections of completed work for the week, such as live demonstrations or a few presentation slides, to which she agreed.


## Retrospective Summary (2/10/2025)
Here's what went well:
* Expectations for the next steps in the project are aligned. 
* Our completed work in regards to GUI, batch segmentation, and analysis met our client's expectations.
* Gaining access to the lab's Github repository login information
  
Here's what we'd like to improve:

* Continue to increase our communicative skills as a group in client meetings
* Ask more qualitative questions regarding objective, desirable deliverables
* Create visual demonstrations of our progress for the client
  
Here are changes we plan to implement as soon as possible:

* Finish our initial 'Lazy Batch' segmentation and move into traditional batch segmentation.
* Continue to update the GUI to better match our expectations and added batch segmentation functionality
* Further optimize the existing statistical analyses methods for faster generation

---

## Agenda (2/3/2025)
* Batch Segmentation Questions
* Application Demonstration
* Microscopic Image Dataset Transfer
## Minutes (2/3/2025)
Our team met with Dr. Zare for the second time as we spent the first few minutes walking through the existing application, demonstrating the full functionality and likes/dislikes of the current implementation. We then talked about gaining access to a OneDrive folder of microscopic images to use for testing and ultimately as a dataset. 


We then discussed the current paramters in the application, starting with loading/scaling/cropping an image. While image metadata exists in dedicated files, Dr. Zare expressed it was unlikely researchers would be diligently saving and uploading these files and that we should expect to scale and crop our images using pixel sizes and the image reference. We then discussed the plotted analysis graphs, the desired outcomes, and the format/content of exported data. A general walkthrough of circular/ovaloid shapes, threshold algorithms, and desire for extended probability distribution functions was discussed. We then talked about multi-image analysis, how this should impact the plotted histograms and probability graphs, and content of exported CSV and TXT files. Nearing the end, we discussed machine learning frameworks we discovered during our research, and Dr. Zare expressed interest in hearing more about the pre-trained models and how they might be implemented in the application.


Lastly, we discussed next steps and desired outcomes for the week. Dr Zare shared the OneDrive image dataset with our project team and we agreed to focus on batch segmentation and modifying the existing GUI to support the new segentation implementation.


## Retrospective Summary (2/3/2025)
Here's what went well:
* Further undstanding the extend of the existing application
* Setting clear, prioritized goals for what to accomplish over the next week(s)
* Gaining access to dataset resources
  
Here's what we'd like to improve:

* Gathering measureable deliverables for the week
* Take a leadership role in managing the client meeting
* Have visual demonstrations of progress for the client
  
Here are changes we plan to implement as soon as possible:

* Implement initial batch segmentation for the existing application
* Update the GUI to better match our expectations and added batch segmentation functionality
* Optimize the existing statistical analyses methods for faster generation

---
  
## Agenda (1/27/2025)
* Client/Team Introduction
* Project Introduction
* Preliminary Resource Transfer
## Minutes (1/27/2025)
Our team met with Dr. Zare for the first time as we spent the first 20 minutes introducing ourselves, our experiences, and how our unique skills may best contribute to the project. We were then given a detailed explanation of the work Dr. Zare's laboratory performs, and an abstract overview of what we would be expected to contribute over the coming year. 


The project aims to improve an existing application to support multi-image analysis, create an automated system for analyzing microstructural images of high-impact collisions, identify optimal impact conditions, and add additional/optional segmentation and statistical analyses methods. We then discussed later project goals, in creating a trained machine learning model capable of predicting material performance and a predictive framework utilizing training data and material parameters to design resilient materials for aerospace, defense, and space travel applications.


We broke down the work the previous Capstone team had completed (a general application for single image analysis with footprint, thresholding, blur, and smoothing algorithms) and our immediate next steps for getting started; batch-segmentation for multi-image analyses and extending functionality of algorithmic parameters.


Lastly, we set a recurring weekly in-person meeting time and location, as well as adding Dr. Zare to our Microsoft Teams channel for communication. We were also given access to the previous teams’ Github repository and final report. 


## Retrospective Summary (1/27/2025)
Here's what went well:
* Initial Introductions
* Setting up a meeting/communication structure
* Getting access to the existing project
  
Here's what we'd like to improve:

* Better understanding the detailed algorithmic expectations of our Client
* Functionality priority for our client (speed, gui, multi-image, more algorithms, etc.)
* Team meeting and communication moving forward
  
Here are changes we plan to implement as soon as possible:

* Initializing our team's Github repository
* Adding batch segmentation for multi-image analyses
* Understanding the existing pipeline for image segmentation and analysis for future improvements
