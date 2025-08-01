# Stereo Camera Calibration Module

This module handles the stereo calibration process for Silo-Sight deepfake detection.

## Purpose

Stereo calibration establishes the mathematical relationship between two cameras, enabling 3D point triangulation from 2D observations. This is the foundation for detecting geometric inconsistencies in deepfakes.

## Files

- `stereo_calibrate.py` - Main calibration script
- `validate_calibration.py` - Validates calibration quality
- `README.md` - This file

## Quick Start

### 1. Prepare Checkerboard Pattern

You have a checkerboard with:
- 8 rows × 11 columns of squares
- 15mm square size
- Board dimensions: 279mm × 216mm

This gives 10×7 internal corners for detection.

### 2. Capture Calibration Video

**Setup:**
1. Position Camera 1 directly facing the user (front view)
2. Position Camera 2 at 30° angle from Camera 1 (side view)
3. **IMPORTANT:** Fix both cameras in place - they must NOT move after calibration
4. Ensure good, even lighting

**Recording:**
1. Hold the checkerboard pattern in front of both cameras
2. Record 10-15 seconds while moving the checkerboard:
   - Different distances (close and far)
   - Different angles (tilt, rotate)
   - Different positions (left, right, up, down)
   - Keep checkerboard flat and fully visible in both camera views
3. Save videos as `calibration_cam1.mp4` and `calibration_cam2.mp4`

**Tips:**
- Move slowly and smoothly
- Ensure checkerboard is fully in frame for both cameras
- Get at least 15-20 good poses
- Avoid motion blur (hold steady for a moment at each position)

### 3. Run Calibration

```bash
cd "Calibration"

python stereo_calibrate.py \
  --cam1 calibration_cam1.mp4 \
  --cam2 calibration_cam2.mp4 \
  --output ../stereo_calibration.npz
```

This will:
1. Extract frames from both videos
2. Detect checkerboard corners in each frame
3. Calibrate each camera individually
4. Perform stereo calibration
5. Save calibration data to `stereo_calibration.npz`

**Expected output:**
```
Stereo calibration complete
RMS error: 0.45 pixels  (should be < 1.0)
Baseline: 25.3 cm
```

### 4. Validate Calibration

```bash
python validate_calibration.py --calibration ../stereo_calibration.npz
```

**Validation checks:**
- ✓ RMS error < 1.0 pixels
- ✓ Valid camera matrices
- ✓ Orthogonal rotation matrix
- ✓ Reasonable baseline distance
- ✓ Valid projection matrices

If validation fails, recalibrate with more/better checkerboard images.

## Alternative: Use Image Directories

If you already have extracted frame pairs:

```bash
python stereo_calibrate.py \
  --cam1_dir /path/to/cam1/images \
  --cam2_dir /path/to/cam2/images \
  --output ../stereo_calibration.npz
```

Images should be:
- Same number in both directories
- Corresponding frames (synchronized captures)
- Named in sorted order (e.g., `frame_0001.png`, `frame_0002.png`, ...)

## Calibration Output

The `stereo_calibration.npz` file contains:

- `K1`, `K2` - Camera intrinsic matrices (3×3)
- `dist1`, `dist2` - Distortion coefficients
- `R` - Rotation matrix between cameras (3×3)
- `T` - Translation vector between cameras (3×1)
- `P1`, `P2` - Projection matrices (3×4)
- `E`, `F` - Essential and Fundamental matrices
- `image_size` - Image dimensions
- `rms_error` - Calibration quality metric

## Troubleshooting

### "Checkerboard not detected"
- Ensure checkerboard is flat and fully visible
- Improve lighting (avoid shadows and glare)
- Check that internal corner count matches config (10×7)
- Try extracting frames manually and inspect them

### "Not enough synchronized pairs"
- Checkerboard must be visible in BOTH cameras simultaneously
- Adjust camera positions or checkerboard placement
- Capture more video footage

### "RMS error too high (>1.0 pixels)"
- Capture more calibration images (20-30 recommended)
- Ensure checkerboard is truly flat (not warped paper)
- Get better variety of angles and distances
- Use better lighting
- Ensure cameras are stable during capture

### "Baseline seems unusual"
- Verify cameras are appropriately spaced apart
- Check camera positions haven't moved
- Consider recalibrating

## Next Steps

After successful calibration:

1. **DO NOT move the cameras** - calibration is only valid for fixed camera positions
2. Proceed to frame capture (real human + deepfake)
3. Run detection pipeline with calibrated parameters

## Advanced Options

### Custom Checkerboard Size

If using a different checkerboard, edit `config.py`:

```python
CHECKERBOARD_SIZE = (width_corners, height_corners)
SQUARE_SIZE = size_in_meters
```

### Frame Extraction Interval

Extract more/fewer frames from video:

```bash
python stereo_calibrate.py --frame_interval 10  # Every 10th frame instead of 15
```

### Visualize Epipolar Geometry

Verify calibration quality visually:

```bash
python validate_calibration.py \
  --calibration ../stereo_calibration.npz \
  --img1 test_image_cam1.png \
  --img2 test_image_cam2.png
```

This creates `epipolar_lines.png` showing that points in one view lie on corresponding epipolar lines in the other view.


Print Checkerboard at: https://calib.io/pages/camera-calibration-pattern-generator 