# Machine Learning–Driven Materials Design for Additive Manufacturing

## Project summary

### One-sentence description of the project

An interface for uploading, segmenting, and analyzing images of material impurities and impact tests.

### Additional information about the project

Our project is designed to take images of materials (with a focus on porous regions) and perform a series of image segmentations to accurately identify and illustrate every pore. Various measurements are taken on the pores and then statistical analysis is conducted to create sets of data on their attributes. The data is then provided to researchers for a better understanding of breakage patterns and how the materials can be strengthened for more extreme environments. Additionally, we have implimented a feature that allows the 
user to analyze 'crater' impacts through uploading a series of images of material slices. The user can generate 

## Installation

The existing **Pop-in Locator** tab offers **Run Detection** for the threshold
algorithm and **Train Shape Model** / **Run Model** for supervised machine learning
using normalized local curve shape.
See [setup, usage, and validation](docs/popin_ml.md).

### Prerequisites

•	Git 
•	Python 3.11 or 3.12
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

### Dependencies

`requirements.txt` is the shared dependency list for the application, standalone
Python scripts, tests, and executable packaging. Use 64-bit Python 3.11 or 3.12.

For CPU-only Windows/Linux installations, install the matching PyTorch packages
before installing the complete list:

```bash
python -m pip install torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
python -m pip check
```

On macOS, install `requirements.txt` directly using the normal package index.
Keep the pinned NumPy, OpenCV, scikit-learn, torch/torchvision, and packaging
versions together: they protect numerical compatibility, saved model loading,
native operations, and frozen imports. The archived research notebooks and
Google Colab setup are not needed by the executable and are excluded.
Legacy Tkinter utilities require a Python installation with Tcl/Tk support;
Linux Qt/OpenCV system libraries are installed separately by CI.

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

## Quick Start on a New Windows Computer

Use the bootstrap script in the project root:

```cmd
setup_and_run.bat
```

What it does automatically:
- creates `.venv` (if missing)
- upgrades pip tooling
- installs `requirements.txt`
- launches `src\app\main.py`

After first setup, you can run the app with:

```cmd
run_app.bat
```

## Known Problems

Minor bug fixes required in crater analysis

If a dependency download fails, retry the install in a fresh virtual environment
using the supported Python version. Keep the versions in `requirements.txt`
rather than substituting arbitrary versions.

Use Python 3.11 or 3.12 with the current requirements. The pinned SciPy version
requires Python 3.11 or newer, and the NumPy requirement (`numpy<2`) supports
Python up to 3.12.

## Continuous integration

[GitHub Actions CI](.github/workflows/ci.yml) runs on every push, pull request,
and manual dispatch from the repository's Actions tab. It checks Python syntax
in `src/app` and `tests` and runs the full `tests/` suite on Ubuntu with Python
3.11 and 3.12, including
the Qt integration tests using the offscreen platform. Dependencies are cached,
and CI installs CPU-only PyTorch to avoid downloading CUDA libraries.

Each test job uploads a JUnit XML report as an Actions artifact, retained for
14 days, including when tests fail. No repository secrets are required.

To run the same checks locally after installing `requirements.txt`:

```bash
python -m compileall -q src/app tests
QT_QPA_PLATFORM=offscreen python -m pytest tests -q --junitxml=test-results/pytest.xml
```

In Windows PowerShell, set `$env:QT_QPA_PLATFORM = "offscreen"` before running
the pytest command without the environment-variable prefix. The SIGINT tests
currently exercise POSIX signal behavior, so CI runs on Linux.

## Windows releases

[Windows release workflow](.github/workflows/build-release.yml) runs when a
stable version tag such as `v1.0.14` is pushed. The tag must match `version.txt`.
It runs both CI test jobs, builds the Windows x64 executable with Python 3.11
and PyInstaller, then publishes a GitHub release with generated release notes,
`SegmentationApp-vX.Y.Z-windows-x64.zip`, and `SHA256SUMS.txt`.
The ZIP contains `SegmentationApp.exe`, `version.txt`, and the license; extract
it before launching the executable. The build uses matching CPU-only PyTorch
and torchvision packages and pinned packaging tools from `requirements.txt`.

Before publishing, the workflow launches the actual executable from an isolated
directory and checks setuptools/backports imports, dependency metadata, PyTorch
and torchvision native operations, SAM imports, the bundled pop-in model, and
the main Qt window. These checks run offline without downloading SAM weights.
Failures block publication. The `windows-build-diagnostics` Actions artifact
contains the smoke-test report (if Python started) and PyInstaller warnings.
`build.bat` uses the same build requirements and executable checks locally.

To release a new version, update and commit `version.txt` with your changes,
push that commit, then create and push the matching tag:

```bash
git tag -a v1.0.14 -m "Release 1.0.14"
git push origin v1.0.14
```

Use your actual new version in place of `1.0.14`. The workflow can also be run
manually against an existing matching tag. It requires GitHub Actions to have
permission to create releases through `GITHUB_TOKEN`; no custom secret is
needed. Builds are unsigned. This workflow currently produces Windows releases
only. Existing releases are preserved; attempting to recreate one fails.
For a packaging fix, commit the changes and an updated `version.txt`, then push
a new matching tag (for example, `v1.1.1` after `v1.1.0`). Rerunning an old tag
uses the old packaging code and does not include later fixes.

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
