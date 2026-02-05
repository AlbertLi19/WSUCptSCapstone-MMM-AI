# Client Meetings Report

## Agenda (2/05/2024)
 * Project progress
 * Next steps
 * Questions

## Minutes (2/05/2024)
The WSUM-python team's progress was discussed as well as the next steps. Dr. Zare would like us to create less cluttered results for the output of our pore analysis program. we will achieve this by moving the measurements into a CSV file instead of on the image. Additionally, the pore will only be labeled on the image so the respective pores can be paired with its calculated measurements.

On top of creating less cluttered results, she would also like to see the distribution of measurements through a histogram. This will help us in determining the accuracy of the measurements and the distribution of different images.

Lastly, Dr. Zare would like us to verify that the measurements are accurate by understanding how they are calculated. 

## Retrospective Summary (2/05/2024)
Here's what went well:
 * Project progress
 * Next steps on project
 * Roadmap of which features to prioritize first
 
Here's what we'd like to improve:
 * More frequent communication with the client
  
Here are changes we plan to implement as soon as possible:
 * Create histogram for areas and diameter calcualations
 * Create less cluttered results (map labels to table of values rather than scattering the image with values)
 * verify measurments are correct

## Agenda (2/21/2024)
 * Project progress
 * Next steps
 * Questions

## Minutes (2/21/2024)
In our meeting, we discussed the WSUM-python team's progress and next steps. For the team's progress, we were able to reduce the clutter of the images and develop a histogram of area and diameter for each image. However, the accuracy of the current watershed program is still undetermined. Based on our progress Dr. Zare recommended we start working on the impurity analysis program in parallel with our current pore analysis. She recommended that we take a look at the Python program that was developed by one of her graduate students as a starting point.

In addition to beginning the impurity project, Dr. Zare would like to add documentation on how the current watershed implementation works to further understand the accuracy of the current program. Some questions that she would like to be answered are: how many parameters are there for user input? How is area and diameter calculated? (major and minor axis?).

Lastly, Dr. Zare would like to see a photo script that will run the impurity or pore analysis script based on the inputted images.

## Retrospective Summary (2/21/2024)

Here's what went well:
 * Project progress
 * Next steps on project
 * Roadmap of which features to prioritize first
 
Here's what we'd like to improve:
 * More frequent communication with the client
  
Here are changes we plan to implement as soon as possible:
 * Work on improving pore and impurity python files in parallel
 * Paragraph on how watershed works
 * verify measurments are correct
  * Find how many parameters there are for user input
  * How is area and diameter calculated
 *  Make sense of impurity script
  * Compare calculations with manual calculations
  * Review and improve accuracy
 * python script to combine pore python script with impurity script to improve usability

## Agenda (3/04/2024)
 * Project progress
 * Next steps
 * Questions

## Minutes (3/04/2024)
In our meeting, we went over the impurity project progress. We found that the trends in diameter and area are different. We will want to further analyze how area and diameter are computed. Dr. Zare suggested looking at the previous MATLAB file and trying to fit the impurities into an oval shape instead of a circle.

In addition, Dr. Zare would like us to continue researching the watershed algorithm and apply it to various other images to learn how accurate it is.

## Retrospective Summary (3/04/2024)
Here's what went well:
 * Project progress
 * Next steps on project

Here's what we'd like to improve:
 * More frequent communication with the client

Here are changes we plan to implement as soon as possible:
 * upload python files to onedrive
 * Look into if watershed is still a good algorithm for pore segmentation
 * impliment additional features in the impurities
