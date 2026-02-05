import numpy as np
import pytest
from CraterVolume_BCShot4_python import calculate_depth, calculate_volume, calculate_diamater, CraterImg


def test_calculate_depth_returns_correct_mm():
    """
    Test that calculate_depth correctly converts the maximum heatmap value in voxels to millimeters.
    """
    heatmap = np.array([[0, 2], [4, 1]])  # Max voxel value is 4
    depth_mm = calculate_depth(heatmap, VZ=50)
    # 4 voxels * 50 microns = 200 microns = 0.2 mm
    assert pytest.approx(depth_mm, rel=1e-6) == 0.2


def test_calculate_volume_with_heatmap():
    """
    Test that calculate_volume returns the correct total volume and updates the heatmap counts for black pixels.
    """
    img1 = CraterImg(img_path="slice1", binarized_img=np.array([[0, 1]]))
    img2 = CraterImg(img_path="slice2", binarized_img=np.array([[1, 0]]))
    processed_images = [img1, img2]
    heatmap = np.zeros((1, 2))
    # Use small voxel dims for easy calculation
    volume = calculate_volume(processed_images, heatmap, roi=None, vx=1, vy=1, vz=1)
    # Each black pixel contributes 1*1*1*1 *1e-9 = 1e-9 mm^3, two slices => 2e-9
    assert pytest.approx(volume, rel=1e-6) == 2e-9
    assert heatmap[0, 0] == 1
    assert heatmap[0, 1] == 1


def test_calculate_diamater_returns_none_for_empty_heatmap():
    """
    Test that calculate_diamater returns None when no crater contour exists.
    """
    heatmap = np.zeros((10, 10))
    result = calculate_diamater(heatmap, vx=1, vy=1, fitting_threshold=0.5, contor_threshold=0.3)
    assert result is None


def run_all_tests():
    """Run all crater analysis tests and print results."""
    print("\nRunning Crater Analysis Tests\n" + "="*25 + "\n")
    
    test_functions = [
        test_calculate_depth_returns_correct_mm,
        test_calculate_volume_with_heatmap,
        test_calculate_diamater_returns_none_for_empty_heatmap
    ]
    
    for test in test_functions:
        try:
            test()
            print(f"✓ {test.__name__}")
        except AssertionError as e:
            print(f"✗ {test.__name__}")
            print(f"  Error: {str(e)}")

if __name__ == '__main__':
    run_all_tests()
