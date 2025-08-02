0. Frame Ingestion
    b. Setup: Zoom conference with two cameras at near 90 degree angle
    a. For POC, extract and feed 2 sets of 5 frame_pairs (with head in 5 different positions) using screenshots
        i. frame_pair_set_real
        ii. frame_pair_set_fake
    c. Get into BGR format for OpenCV
2. 2D Detection: Use facial landmark detection to observe the 2D pixel coordinates of the nose tip in both frames.
    a. Store FV_Coord_Obs (x,y) and SV_Coord_Obs (x,y)
3. 3D Triangulation: Given the 2D coordinate of the nose tip in forward view and the camera orientation, estimate the expected coordinate of the nose tip in side view.
    a. Input: FV_Coord_Obs, Position_FC, Position_SC
    b. Output: SV_Coord_Exp
4. Reprojection
5. Comparison: Compare the expected coordinate of the nose tip in sideview with the observed coordinate of the nose tip in sideview.
    a. Diff_Frame_1 = SV_Coord_Exp - SV_Coord_Obs
    b. Array of [Diff_Frame_1, Diff_Frame_2, etc.]
    c. Aggregate Error. Find the mean difference between expected and observed coordinates among available frames: SumArray
6. Output a confidence score from 0-100 representing how likely the user is a real human, not a deepfake.


Main

Upload all 5 frames

AnchorEstablisher(frame_pair_0)
1. Frame Ingestor(frame_pair_0)
    Output: frame_fv, frame_sv
2. 2D_Anchor_Detector(frame_fv) & 2D detection(frame_sv)
    Output: FV_Coord_Obs, SV_Coord_Obs---> for not just the nose point, but 100 other points.
3. 3D Triangulator(FV_Coord_Obs, SV_Coord_Obs)
    Output: offset_side_view: -------> offset_side_view is the relationsip between points in FV and SV: if a point is in (x1, y1) in FV, what (x2, y2) should it be in for SV
4. Reprojector(offset_side_view, FV_Coord_Obs)
    Output: SV_Coord_Exp
5. Differ (SV_Coord_Exp, SV_Coord_Obs)
    Output: coord_diff
6. AnchorChecker(Coord_Diff)
#Ensure that using this 3D triangulation, FV_Coord_Obs_0 leads to a SV_Coord_Exp_0 that is close to SV_Coord_Obs_0
    if coord_diff > 10 (adjust this number to be reasonable)
        anchor_valid = FALSE
    else anchor_valid = TRUE
Output: anchor_valid, offset_side_view


if anchor_valid = TRUE...

#Use Anchor to Evaluate the Rest
RealityChecker(frame_pair, offset_side_view)
1. Frame Ingestion(frame_pair_i)
    Output: frame_fv, frame_sv in GBR form
2. 2D Detection
3. Reprojector(offset_side_view, FV_Coord_Obs)
    Output: SV_Coord_Exp
4. Differ (SV_Coord_Exp, SV_Coord_Obs)
    Output: coord_diff
5. Outputter(coord_diff)
    Output: isDeepfake (T/F)

