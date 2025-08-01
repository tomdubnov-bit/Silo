Technical Stack

1. Video Recording
    a. Two MacBooks
    b. Container: .mp4
    c. Codec: H.264
    d. Resolution: 720p
    e. Frame rate: 30 FPS
    f. Compression: Medium Quality (CRF = 23, ffmpeg)
2. Video Ingestion: Frame Extraction/Pairing
    a. Goal: Pair frames that belong to the same moment in time
    b. Tools: cv2.VideoCapture from OpenCV
    c. Open both cameras
        cap1.read()
        cap2.read()
    d. Output: Frame Pairs
3. Stereo Calibration: Camera Positioning Mapping
    a. Goal: Teach system how the cameras see the world: focal lengths, optical centers, relative position
    b. Tools: OpenCV Calibration functions
        cv2.calibrateCamera
        cv2.stereoCalibrate
        cv2.stereoRectify
        NumPy for matrix handling
    c. Output
        Camera Intrinsics (K1, K2): how each camera maps 3D to 2D
        Distortion Coefficients (dist1, dist2)
        Rotation R and translation T between cameras
        Projection Matrices:
            P1 = K1 [I|0]
            P2 = K2 [R|T]
    d. Return the mathematical relationship to turn 2D noise points into a 3D coordinate
    e. Store in a .npz file
4. Landmark Detection
    a. Goal: Locate the nose tip in each frame_pair
    b. Tools: Mediapipe Face Mesh (Google's lightweight facial landmark detector)
        Returns 468 landmarks with (x,y,z) per face
        Isolate the coordinate of the noise tip
        Alternative (abandoned): Dlib facial landmarks (slower)
    c. Convert frame to RGB
    d. Output: 2D points p_HeadOn = (x1, y1), p_Profile = (x2, y2)
5. Triangulation
    a. Goal: Compute where the nose actually is in space
    b. Tools: OpenCV
        cv2.triangulatePoints(P1, P2, pts1, pts2)
        NumPy for math
    c. Undistort 2D points using calibration data to normalized coordinates
    d. Feed both camera projection matrices and the two 2D nose points in triangulatePoints
    e. Function spits out a 4D homogeneous vector: divide by last value to get a 3D point (X, Y, Z)
    f. Intuition: If both cameras see the same real object, their nose lines intersect at one consistent 3D location
6. Reprojection & Error Calculation
    a. Goal: Check whether the 3D nose you found matches the camera views
    b. Tools
        OpenCV matrix operations
    c. Formula: p_proj = (P @ [X, Y, Z, 2])/depth
    d. Steps
        i. Take 3D nose point
        ii. Project point back onto the camera's image plane using P1, P2
        iii. Compute 2D projection: (x_proj, y_proj) for each camera
        iv. Measure pixel distance between actual detected nose and reprojected nose.
    e. Intuition: Real nose should deviate by no more than 2px from projection
7. Temporal Smoothing & Scoring
    a. Goal: Stabilize noisy frame-by-frame measurements and convert to confidence score
    b. Tools
        NumPy for rolling averages
        Optional: SciPy filters for smoothing
    c. Identify errors per frame
    d. Compute mean error
    e. Map E_mean to a 0-100 confidence score S_c
8. Confidence Visualization
    a. Log the result
    b. Tools
        Optional: OpenCV draws on video windows (overlay text-- Confidence Score: XX)
        Optional: Matplotlib or Dash for live charts
        CSV logging via Pandas for quantitative analysis



