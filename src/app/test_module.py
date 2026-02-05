from Databases.database_handler import DatabaseHandler
import analysis_scripts.pdf_generator
import sys
import os
import pandas as pd
import numpy as np
from segmentation_scrips import segment_impurity_image
from loguru import logger



# Import functions to test from files/classes
# Create specific functions for each test
# Add each test function to the test wrapper
# Note the verbose bool for printing output success
# Optionally add the wrapper to main.py to run tests on launch

# ============================ EXAMPLE TEST CASE ============================
def test_name_of_test(verbose=False):

    # Test concepts to gather explicit, expected resultant data

    assert 1 == 1 # assert gathered value == expected value
    if verbose:
        print("test_name_of_test: x/x cases pass") # Print name of test and number of asserts tested
# ============================ EXAMPLE TEST CASE ============================

def test_database_retrieval(verbose=False):
    db = DatabaseHandler()
    db._parse_distributions()
    res = db._get_all_distributions()

    # Should be 112, however the database may not be updated on your local machine if you ran the Database implementation before the Distributions.csv was updated (may still be 116).
    # If getting an error in this test case: Go to 'Databases/database_handler.py', uncomment the 'db._reset_database()' function, run the program, and comment it out again.  
    assert len(res) == 112

    for row in res:
        for val in row: # assert no null or missing
            assert val is not None
            if isinstance(val, str):
                assert val.strip() != ""

    if verbose:
         print("test_database_retrieval: 3/3 cases pass")

def test_distribution_selection(verbose=False):
    def resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller .exe """
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if getattr(sys, 'frozen', False):
            # If we're running in a PyInstaller bundle
            distribution_csv_path = resource_path("app/analysis_scripts/distributions.csv")
    else:
            distribution_csv_path = os.path.join(base_dir, "app", "analysis_scripts", "distributions.csv") 
        
    df = pd.read_csv(distribution_csv_path)

    for index, row in df.iterrows():
        distribution = row['Distribution'] # same here this is our dist formula
        formula = row['Formula'] # this is our pandas df formula

    missing_values = df.isnull().sum().sum()
    df_length = len(df)
    assert df_length == 112
    assert missing_values == 0
    if verbose:
        print("test_distribution_selection: 3/3 cases pass")


def test_analysis_calculation(results, verbose=False):
    data = np.array(results[0])
    selected_distributions = ['alpha', 'gamma']
    data_dist, data_params = analysis_scripts.pdf_generator.fit_distribution_sample(data, selected_distributions)

    assert data_dist == results[1]
    assert data_params == results[2]

    data_train = np.abs(data.reshape(-1, 1))
    data_test = np.linspace(min(data_train), max(data_train), len(data_train)).reshape(-1, 1)
    log_dens = analysis_scripts.pdf_generator.KDE_calculator(data_train, data_test, 2)
    x_peak = analysis_scripts.pdf_generator.MLE_calculator(log_dens, data_test)
    half_max, above_half_max, fwhm = analysis_scripts.pdf_generator.FWHM_calculator(log_dens, data_test)

    assert np.isclose(log_dens, results[3]).all() == True
    assert np.isclose(x_peak, results[4]).all() == True
    assert half_max == results[5]
    assert np.isclose(above_half_max, results[6]).all() == True
    assert np.isclose(fwhm, results[7]).all() == True

    if verbose:
        print(f"test_analysis_calculation - {results[8]}: 7/7 cases pass")

"""Testing to see if we can properly upload an image"""
def test_image_upload(verbose=False):
    """LOADING IN THE IMAGE PATH"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up TWO levels from src/app to reach -wsum-fullstackapp-
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    image_path = os.path.join(project_root, 'src', 'res', 'Impurity_SEM_Images', '63020B_TP_08_53x40_IBSE', '63020B_TP_08_53x40_IBSE_02.tif')
    """==================="""

    # CHECKING TO MAKE SURE OUR IMAGE LOADED IN
    image_exists = os.path.exists(image_path)
    assert image_exists, f"Test image not found."

    if verbose:
        print(f"test_image_upload: 1/1 case passes Image Found!")

"""testing the segmentation output. 
   segment_impurity_image gives us a nice dataframe to work with
   
    
   Steps: 
   1. Load in an image
   2. Set parameters
   3. Run the segmentation
   4. Check if data is consistent """

def test_segmentation_output_base(verbose=False):

    """LOADING IN THE IMAGE"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    image_path = os.path.join(project_root, 'src', 'res', 'Impurity_SEM_Images', '63020B_TP_08_53x40_IBSE', '63020B_TP_08_53x40_IBSE_02.tif')
    """==================="""

    # CHECKING TO MAKE SURE OUR IMAGE LOADED IN
    if not os.path.exists(image_path):
        assert False, f"Test image not found."

    expected_results = [0.006486292673013369, 5.09238830441569, 43.50495901306325]

    """Segmentation Parameters"""                   
    filename = image_path
    px_per_um = 10000.00
    intensity_threshold = 127
    disk_radius = 1
    thresh_num = 0
    blur_num = 0
    min_particle_area = 60
    blocksize = 11
    c = 2
    smooth_kernel_size = 5
    d = 9
    sigma_color = 75
    sigma_space = 75
    footprint_num = 0
    ellipse_width = 5
    ellipse_height = 3
    _crop_rect = None
    """Segmentation Parameters"""

    """RUNNING SEGMENTATION"""
    test_data = segment_impurity_image(filename, px_per_um, intensity_threshold, disk_radius,
                                                    thresh_num, blur_num, min_particle_area, blocksize, c,
                                                    smooth_kernel_size, d, sigma_color, sigma_space,
                                                    footprint_num, ellipse_width, ellipse_height, _crop_rect)
    
    """ADDING TEST RESULTS TO A LIST"""
    test_results = []
    test_results.append(test_data['Size'].mean())
    test_results.append(test_data['Aspect_Ratio'].mean())
    test_results.append(test_data['Orientation'].mean())

    assert np.isclose(test_results[0], expected_results[0]), f"Mean Size mismatch: Expected {expected_results[0]}, Got {test_results[0]}"
    assert np.isclose(test_results[1], expected_results[1]), f"Mean Aspect Ratio mismatch: Expected {expected_results[1]}, Got {test_results[1]}"
    assert np.isclose(test_results[2], expected_results[2]), f"Mean Orientation mismatch: Expected {expected_results[2]}, Got {test_results[2]}"

    if verbose:
        print("test_segmentation_output_base: 3/3 test cases pass")


"""Load in an image, set all parameters to zero and see if we hit our exception
   if so we have passed our test."""
def test_segmentation_output_exception(verbose=False):
    """LOADING IN THE IMAGE PATH"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    # Use the same image as the base test
    image_path = os.path.join(project_root, 'src', 'res', 'Impurity_SEM_Images', '63020B_TP_08_53x40_IBSE', '63020B_TP_08_53x40_IBSE_02.tif')
    """==================="""

    # CHECKING TO MAKE SURE OUR IMAGE LOADED IN
    if not os.path.exists(image_path):
        assert False, f"Test image not found."

    """Segmentation Parameters causing exception"""
    filename = image_path
    px_per_um = 0.00 # <--- This is what we are setting to zero to cause the exception
    intensity_threshold = 127
    disk_radius = 1
    thresh_num = 3
    blur_num = 1
    min_particle_area = 60
    blocksize = 11
    c = 2
    smooth_kernel_size = 5
    d = 9
    sigma_color = 75
    sigma_space = 75
    footprint_num = 0
    ellipse_width = 5
    ellipse_height = 3
    _crop_rect = None
    """Segmentation Parameters causing exception"""

    exception_caught = False
    try:
        # want to run segmentation with px_per_um = 0
        segment_impurity_image(filename, px_per_um, intensity_threshold, disk_radius,
                               thresh_num, blur_num, min_particle_area, blocksize, c,
                               smooth_kernel_size, d, sigma_color, sigma_space,
                               footprint_num, ellipse_width, ellipse_height, _crop_rect)
        # If the above line runs without error, the test should fail because the error was expected
        assert False, "ZeroDivisionError was expected but not raised."
    except ZeroDivisionError:
        # we caught our exception like we wanted to
        exception_caught = True
        if verbose:
            print("test_segmentation_output_exception: 1/1 test case passes ZeroDivisionError caught")
    except Exception as e:
        assert False, f"Another Unknown exception was found...."

    assert exception_caught, "Expected ZeroDivisionError was not caught."


size_results = [[0.007172, 0.004193, 0.001501, 0.001318], 'gamma', {'a': 0.10829094502148094, 'loc': 0.0013179999999999997, 'scale': 0.0017649021412429297}, [2.07466926, 2.07564343, 2.07509797, 2.07303289], [0.00326933], 3.9848363645505036, [0, 1, 2, 3], [0.005854], "Size"]
aspect_results = [[3.545081, 3.255150, 1.785446, 1.538163], 'alpha', {'a': 8.80656195288525, 'loc': -5.229629444197089, 'scale': 67.4744998318518}, [-1.62411195, -1.48862651, -1.49128415, -1.63201003], [2.20713567], 0.11284120766746825, [0, 1, 2, 3], [2.006918], "Aspect"]
orientation_results = [[61.598566, 83.921581, 43.641542, 0.218608], 'gamma', {'a': 294.603047196852, 'loc': -488.97963999778335, 'scale': 1.8195564202614691}, [ -2.67679645, -59.97304247, -10.07603932,  -2.67679645], [0.218608], 0.034391575896675235, [0, 3], [83.702973], "Orientation"]
spacing_results = [[0.002257, 0.007796, 0.004000, 0.002387], 'gamma', {'a': 0.5882566475969014, 'loc': 0.0022569999999999995, 'scale': 0.001303931931864737}, [2.07511029, 2.07579421, 2.07511727, 2.07307949], [0.00410333], 3.985437249802059, [0, 1, 2, 3], [0.005539], "Spacing"]
logger.remove()  # Remove default logger that prints Fitter output to stderr (Cleaner testing)

def test_wrapper(verbose=False):
    if verbose:
        print("\n============ Begin Test Cases ============\n")

    test_database_retrieval(verbose)
    test_distribution_selection(verbose)
    test_analysis_calculation(size_results, verbose)
    test_analysis_calculation(aspect_results, verbose)
    test_analysis_calculation(orientation_results, verbose)
    test_analysis_calculation(spacing_results, verbose)
    test_image_upload(verbose)
    test_segmentation_output_base(verbose)
    test_segmentation_output_exception(verbose)


    if verbose:
        print("\nAll Test Cases Passed!\n")
        print("============= End Test Cases =============\n")

if __name__ == '__main__':
    test_wrapper(True)