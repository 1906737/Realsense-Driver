import pyrealsense2 as rs
import numpy as np
import cv2

# 1. Pipeline Setup
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
pipeline.start(config)

align = rs.align(rs.stream.color)
pc = rs.pointcloud()

try:
    while True:
        frames = pipeline.wait_for_frames()
        aligned_frames = align.process(frames)
        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()

        if not depth_frame or not color_frame:
            continue

        # 2. Extract Point Cloud & ROI
        points = pc.calculate(depth_frame)
        vtx = np.asanyarray(points.get_vertices())
        vertices = vtx.view(np.float32).reshape(480, 640, 3)
        
        # Middle 50% Box (Z-values only)
        roi_array = vertices[120:360, 160:480, 2]

        # 3. Create Visualization
        color_image = np.asanyarray(color_frame.get_data())
        
        # Create a black background for the "Data Box"
        data_display = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(data_display, "Depth Array (Meters):", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # 4. Subsample the array to display as text
        # We take a sample every 40 pixels so the text fits on screen
        step = 40 
        for i, y in enumerate(range(0, roi_array.shape[0], step)):
            for j, x in enumerate(range(0, roi_array.shape[1], step)):
                val = roi_array[y, x]
                # Format: 0.00m or "N/A" if 0
                txt = f"{val:.2f}" if val > 0 else "0.0"
                
                # Draw the number in the data_display box
                pos = (50 + j*80, 100 + i*60)
                cv2.putText(data_display, txt, pos, 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # 5. UI elements
        # Draw the ROI rectangle on the live feed
        cv2.rectangle(color_image, (160, 120), (480, 360), (0, 255, 0), 2)
        
        # Combine the live camera and the data box side-by-side
        combined_view = np.hstack((color_image, data_display))
        cv2.imshow('RealSense Live Depth Matrix', combined_view)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
