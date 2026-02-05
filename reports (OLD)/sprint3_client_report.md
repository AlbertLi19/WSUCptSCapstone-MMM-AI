# Client Meetings Report

## Agenda (3/04/2024)
 * Project progress
 * Next steps
 * Questions

## Minutes (3/04/2024)
In this Zoom meeting, the WSUM-Python team went over our progress on both impurities and pore images. For the impurities, Daniel Lee was able to compile and execute the program and began working on replicating the results of the previous calculations that Dr. Zare's team had calculated manually. For progress on the pore images, Daniel Book was previously working through Mason's program for the watershed algorithm. As it turns out, the program was not implementing the watershed algorithm to analyze the pores. So Daniel Book developed his ownwatershed python script and showed a demonstration of how his program works during the meeting. Finally, Doug was introduced to other deep-learning segmentation models that we could potentially use.

## Retrospective Summary (3/04/2024)
Here's what went well:
 * Project progress
 * Next steps on project
Here's what we'd like to improve:
 * More frequent communication with the client
Here are changes we plan to implement as soon as possible:
 * Message more frequently on Teams
 * Continue working on impurity script
 * Continue working on pore script
 * Create a slideshow of a summary of our project progress
 * Create a in-depth document of each project progress and details


 ## Agenda (3/20/2024)
 * Project progress
 * Next steps
 * Questions

## Minutes (3/20/2024)
In this meeting, the WSUM-Python team went over the progress of our project. Because of our Spring break, we had not worked on the project very much so we delayed the meeting a couple of days. For the Pore analysis, Daniel Books has kept working on the watershed algorithm and was questioning if the watershed was the best algorithm to detect pores. He suggested looking into other segmentation methods, such as edge-based segmentation and other methods. For the impurity project, Daniel Lee updated the team and Dr. Zare on his progress. After this, Daniel Lee and Dr. Zare worked on the next steps on what to focus on next. Based on Dr. Zare's feedback, she would like the impurity Python script to replicate the data values that were manually calculated. Finally, Doug talked about Roboflow and the segmenting model that he is looking into - Segment Anything Model (SAM). Due to the resources intensiveness of the program he is having trouble developing images for the pore images. However, Doug was able to display the output for the impurity image and how it segments the image.

## Retrospective Summary (3/20/2024)
Here's what went well:
 * Project progress
 * Next steps on project
 
Here's what we'd like to improve:
 * More frequent communication with the client
  
Here are changes we plan to implement as soon as possible:
 * Continue working on impurity script
 * Continue working on pore script
 * Continue working on deep learning models for segmentation

 ## Agenda (3/28/2024)
 * Project progress
 * Next steps
 * Questions

## Minutes (3/28/2024)
In this meeting, the WSUM-Python team went over the progress of our project. From the feedback that the WSUM-Python team received last meeting, Dr. Zare would like us to provide more detailed documentation on each component of our project. The WSUM-Python team developed a PowerPoint presentation that has an overview of each component of the project and our progress. The beginning of the meeting consisted of the WSUM-Python team presenting each of the components of the project and what they have accomplished, how their algorithms work, and what they are working on next. Daniel Lee's findings since our last meeting were that Edge-based segmenting is not very accurate, and Watershed is looking more attractive for what we are trying to do. This was due to another parameter that increased the accuracy of the model. Dr. Zare would like to see the optimal set of parameters for the most accurate identification of the pores and compare these calculations with manual calculations. Daniel Lee showed how his current algorithm works. Dr. Zare would like to see the implementation of impurity size, spacing, aspect ratio, and orientation in Python, and try to compare these results with the previously calculated results. Finally, Doug explained the barriers that he is encountering in his portion of the project. The end goal for this would be to segment the pore images to see if it is any more accurate than the watershed algorithm.

## Retrospective Summary (3/28/2024)
Here's what went well:
 * Project progress
 * Next steps on project
 * Roadmap of which features to prioritize first
 
Here's what we'd like to improve:
 * More frequent communication with the client
  
Here are changes we plan to implement as soon as possible:
 * Continue working on impurity script
 * Continue working on pore script
 * Continue working on deep learning models for segmentation