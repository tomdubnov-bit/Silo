POC Workflow - Stereo Vision Deepfake Detection

SETUP (One-Time Calibration)
1. Hardware Setup
    a. Two cameras positioned at ~30 degree angle
    b. Cameras fixed in position (do not move after calibration)

2. Stereo Calibration
    a. Print checkerboard calibration pattern (e.g., 9x6 squares)
    b. Record 10-15 seconds of checkerboard from various angles/positions with both cameras
    c. Extract synchronized frame pairs from calibration video
    d. Run cv2.stereoCalibrate() to compute:
        i. Camera intrinsics: K1, K2 (focal lengths, optical centers)
        ii. Distortion coefficients: dist1, dist2
        iii. Rotation matrix R and translation vector T (camera extrinsics)
        iv. Projection matrices: P1 = K1[I|0], P2 = K2[R|T]
    e. Save calibration data to stereo_calibration.npz
    Output: P1, P2, K1, K2, dist1, dist2, R, T


TESTING (Per Frame Pair)
1. Frame Ingestion
    a. Load one frame_pair_real (real human screenshot)
    b. Load one frame_pair_fake (deepfake screenshot)
    c. Convert to BGR format for OpenCV
    Output: frame_fv, frame_sv

2. Landmark Detection
    a. Use MediaPipe Face Mesh on both frames
    b. Detect 468 facial landmarks in each view
    c. Extract key landmarks (nose tip, chin, eye corners, mouth corners, etc.)
    d. Store 2D pixel coordinates for ~10-20 key points
    Output: FV_landmarks (array of (x,y) points), SV_landmarks (array of (x,y) points)

3. 3D Triangulation
    a. Load calibration data (P1, P2)
    b. For each landmark pair:
        i. Undistort 2D points using K and dist coefficients
        ii. Call cv2.triangulatePoints(P1, P2, FV_point, SV_point)
        iii. Convert homogeneous 4D result to 3D: (X, Y, Z) = (X/W, Y/W, Z/W)
    c. Store 3D coordinates for all landmarks
    Output: landmarks_3D (array of (X, Y, Z) points)

4. Reprojection
    a. For each 3D landmark:
        i. Reproject to front-view using P1: point_fv_proj = P1 @ [X, Y, Z, 1]
        ii. Normalize: (x_fv_proj, y_fv_proj) = (point_fv_proj[0]/point_fv_proj[2], point_fv_proj[1]/point_fv_proj[2])
        iii. Reproject to side-view using P2: point_sv_proj = P2 @ [X, Y, Z, 1]
        iv. Normalize: (x_sv_proj, y_sv_proj) = (point_sv_proj[0]/point_sv_proj[2], point_sv_proj[1]/point_sv_proj[2])
    Output: FV_reprojected, SV_reprojected

5. Error Calculation
    a. For each landmark in front-view:
        error_fv = sqrt((FV_observed - FV_reprojected)^2)
    b. For each landmark in side-view:
        error_sv = sqrt((SV_observed - SV_reprojected)^2)
    c. Calculate mean reprojection error across all landmarks and both views:
        mean_error = mean([error_fv_all, error_sv_all])
    Output: mean_error (in pixels)

6. Authenticity Scoring
    a. Real human threshold: mean_error < 5 pixels
    b. Deepfake threshold: mean_error > 15 pixels
    c. Convert to confidence score:
        if mean_error < 5: confidence = 100
        elif mean_error > 15: confidence = 0
        else: confidence = 100 - ((mean_error - 5) * 10)
    d. Determine authenticity:
        if confidence > 70: isDeepfake = False
        else: isDeepfake = True
    Output: confidence_score (0-100), isDeepfake (True/False), mean_error (pixels)


EXPECTED RESULTS
- Real human frame: Low reprojection error (~2-5 pixels), high confidence (>90)
- Deepfake frame: High reprojection error (>15 pixels), low confidence (<30)
