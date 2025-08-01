README:

Silo-Sight Multi-View Deepfake Integrity Check


Motivation
In 2024, the multinational firm Arup suffered a staggering loss of approximately $25 million due to a sophisticated deepfake attack. An employee, initially suspicious of an email request, was convinced to authorize the transfers after attending a fake video conference. During the call, all participants, including the Chief Financial Officer and senior colleagues. were AI-generated deepfakes with convincingly cloned visuals. This is not an isolated case. As deepfake sophistication and access accelerates, businesses suffer financial, operational and reputation damage. Companies currently face a difficult trade-off:
1. Risk Fraud: Rely on current, lax digital protocols where web conferences are easily faked.
2. Slow Operations: Insist on in-person approvals for high stakes meetings, severely impeding operational speed.
Arup's loss proves that relying on visual recognition in 2D web conferencing environments is no longer safe.


Solution: Silo-Sight
Silo-Sight tackles this threat by leveraging a core weakness of deepfake technology: its struggle with geometric and 3D consistency across multiple simultaneous viewing angles.Silo-Sight acts as a "zero-trust" check for a person entering a virtual conference room. The system will use two webcams to verify the physical location of a rigid facial feature. The principle is simple: Facial extremities viewed from two fixed cameras must always triangulate to a single, consistent 3D point in space. A deepfake, generated in 2D, will show measurable geometric inconsistencies when attempting to reconcile the two views.


Scope: Proof of Concept
1. Orient: Mathematically establish the fixed relationship between the two cameras.
2. 2D Detection: Use facial landmark detection to find the 2D pixel coordinates of the nose tip in both frames.
3. 3D Estimation: Given the 2D coordinate of the nose tip in forward view and the camera orientation, calculate the expected coordinate of the nose tip in side view.
4. Comparison: Compare the expected coordinate of the nose tip in sideview with the observed coordinate of the nose tip in sideview.
5. Aggregate Error: Find the mean difference between expected and observed coordinates among available frames.
6. Output a confidence score from 0-100 representing how likely the user is a real human, not a deepfake.


Technical Stack
1. Language: Python
    a. Access to robust computer vision libraries
2. Video Processing: OpenCV
    Camera stream acquisition, synchronization, and the full suite of Stereo Calibration functions (cv.calibrateCamera, cv.stereoCalibrate, etc.).
3. Feature Tracking: Dlib, Mediapipe
    Fast and accurate facial extremity detection
4. Data/Math: NumPy, scipy
    High-performance numerical operations for matrix manipulation and error calculation.


Long-Term Vision:
This POC is the foundation for a more powerful, general-purpose integrity engine. The long term vision includes the following features:
1. Live video ingestion & analysis
2. 3D Modeling
    Progress from a simple geometric consistency check to full 3D head model reconstruction in real-time. By accurately triangulating several facial landmarks (ie. nose tip, chin, ear tips), Silo Safe creates a truth anchor. The system could then:
    Generate a low-fidelity 3D model of the user's head in real-time. Continuously project that 3D model back onto the two camera feeds.
    Assert truth by checking if the live video and audio align perfectly with the derived 3D geometry: a task exponentially harder for deepfake generative models.
3. Real-time confidence score adjustment
4. Comprehensive integrity infastructure for high stakes workflows, including:
    a. Pre-meeting vetting and facial mapping
    b. In-Meeting Deepfake Defense (Secure Room)
    c. Escalation and Alert Protocol
    d. Post-Event Accountability and Audit
    