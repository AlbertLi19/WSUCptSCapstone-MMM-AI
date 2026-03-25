# Machine Learning–Driven Materials Design for Additive Manufacturing

## Project summary

### One-sentence description of the project

An interface for uploading, segmenting, and analyzing images of material impurities and impact tests.

### Additional information about the project

Our project is designed to take images of materials (with a focus on porous regions) and perform a series of image segmentations to accurately identify and illustrate every pore. Various measurements are taken on the pores and then statistical analysis is conducted to create sets of data on their attributes. The data is then provided to researchers for a better understanding of breakage patterns and how the materials can be strengthened for more extreme environments. Additionally, we have implimented a feature that allows the 
user to analyze 'crater' impacts through uploading a series of images of material slices. The user can generate 

## Installation

### Prerequisites

•	Git 
•	Python  
•	pip (or package manager of choice)

### Installation Steps

Install Git from https://git-scm.com/downloads

Install Python from https://www.python.org/downloads/  

Once the software has been downloaded, open up a new command window and run these steps:

•   Clone the repository by navigating to the desired directory and run: git clone https://github.com/WSUCptSCapstone-S25-F25/-wsum-fullstackapp-.git
•   navigate to the newly cloned directory: cd -wsum-fullstackapp-
•   To create a new virtual enviornment, run command: python -m venv capstonevenv
•   Run command capstonvenv/Scripts/activate to activate the virtual enviornment 
•	pip install -r requirements.txt
Finally to run the app, just run this command (make sure you are in the -wsum-fullstackapp- directory):
python .\src\app\main.py

After a few seconds, the app should start in a new window

## Building an Executable

### For Distribution with Auto-Update Feature

The application includes an auto-update system that allows executables to automatically check for and install updates from the release branch.

#### Building the Executable:

**macOS/Linux:**
```bash
./build.sh
```

**Windows:**
```cmd
build.bat
```

The executable will be created in `dist/SegmentationApp/` and can be distributed to users.

#### Running with Auto-Update:
```bash
# macOS/Linux
./SegmentationApp --auto-update

# Windows
SegmentationApp.exe --auto-update
```

For detailed information about the auto-update system, see:
- `AUTO_UPDATE_README.md` - Complete documentation

## Functionality

navigate to the project directory
run the command python .\src\app\main.py

**Only works after all requirements are installed, doing this in a virtual enviornment is recommended (see installation steps)**

## Known Problems

Minor bug fixes required in crater analysis

There is a possibility of errors due to dependency downloads, should this occur attempt downloading each requirement listed in requirements.txt individually. Versions can be ignored if this is required, simply download whichever one you can.

More recent Python version might cause failures as well, currently unknown. Python version 3.9.13 confirmed to work.

## Additional Documentation

Sprint Reports:  
https://github.com/AlbertLi19/WSUCptSCapstone-MMM-AI/tree/main/reports

User Links:  
https://git-scm.com/
https://code.visualstudio.com/  
https://www.python.org/downloads/  
https://scikit-image.org/  
https://matplotlib.org/  
https://numpy.org/  
https://pandas.pydata.org/  
https://opencv.org/
https://scipy.org/
https://pypi.org/project/fitter/
https://pypi.org/project/PyQt5/
