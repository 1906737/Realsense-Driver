import pyrealsense2 as rs
import numpy as np
import cv2

# 1. Configure the RealSense Pipeline
pipeline = rs.pipeline()
config = rs.config()

# Configure depth and color streams at 640x480
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Start streaming
profile = pipeline.start(config)

# 2. Setup Processing Blocks
# Align depth to color for pixel-perfect matching
align = rs.align(rs.stream.color)

# Pointcloud object
pc = rs.pointcloud()

print("Streaming started. No distance limit applied.")
print("Press 'q' to quit.")

try:
    while True:
        # Wait for frames
        frames = pipeline.wait_for_frames()
        
        # Align depth frame to color frame
        aligned_frames = align.process(frames)
        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()

        if not depth_frame or not color_frame:
            continue

        # 3. Extract Image Data (Raw, no 1m filter applied)
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        # 4. Extract Point Cloud
        points = pc.calculate(depth_frame)
        vtx = np.asanyarray(points.get_vertices())
        
        # Reshape vertices to a grid (480 rows, 640 cols, 3 coordinates: x,y,z)
        vertices = vtx.view(np.float32).reshape(480, 640, 3)

        # 5. ROI: Middle 50% Box Calculation
        # Vertical: 120 to 360 | Horizontal: 160 to 480
        roi_z = vertices[120:360, 160:480, 2]
        
        # Calculate Average Distance (ignoring 0 values/invalid depth)
        valid_depths = roi_z[roi_z > 0]
        if valid_depths.size > 0:
            avg_dist = np.mean(valid_depths)
            # Printing distance in meters
            print(f"Avg Distance in 50% Box: {avg_dist:.3f} m", end="\r")
        else:
            print("Object too close or too far for sensor       ", end="\r")

        # 6. Visualization
        # Draw the ROI box on the color image (Green rectangle)
        cv2.rectangle(color_image, (160, 120), (480, 360), (0, 255, 0), 2)
        
        # Create colormap for depth visualization 
        # (alpha adjusted so far objects are visible)
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
        
        # Stack images horizontally for easy viewing
        images = np.hstack((color_image, depth_colormap))
        cv2.imshow('RealSense D435i - Full Range & ROI', images)

        # Exit on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Stop streaming
    pipeline.stop()
    cv2.destroyAllWindows()
