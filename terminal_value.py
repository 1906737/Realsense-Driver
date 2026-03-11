import pyrealsense2 as rs
import numpy as np
import cv2
import os

# Initialize
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
pipeline.start(config)

align = rs.align(rs.stream.color)
pc = rs.pointcloud()

# Clear terminal once at start
os.system('cls' if os.name == 'nt' else 'clear')

try:
    while True:
        frames = pipeline.wait_for_frames()
        aligned_frames = align.process(frames)
        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()

        if not depth_frame or not color_frame:
            continue

        # Extract Point Cloud
        points = pc.calculate(depth_frame)
        vtx = np.asanyarray(points.get_vertices())
        vertices = vtx.view(np.float32).reshape(480, 640, 3)

        # ROI: Middle 50% Box (120:360, 160:480)
        roi_z = vertices[120:360, 160:480, 2]

        # --- TERMINAL PRINTING LOGIC ---
        # Move cursor to top-left (0,0) so we overwrite the previous frame
        print("\033[H", end="") 
        print("--- RealSense Static Depth ROI Matrix (Meters) ---")

        # Step size: 20 means we print a 12x16 grid (fits standard terminals)
        # Decrease this number to see more detail, increase if it scrolls.
        step_y = 20 
        step_x = 20

        output_str = ""
        for y in range(0, roi_z.shape[0], step_y):
            row_str = ""
            for x in range(0, roi_z.shape[1], step_x):
                val = roi_z[y, x]
                if val == 0:
                    row_str += "  0.0  " # No depth detected
                else:
                    row_str += f" {val:5.2f} " # Format to 2 decimal places
            output_str += row_str + "\n"
        
        print(output_str)
        print(f"Avg: {np.mean(roi_z[roi_z > 0]):.3f}m | Press 'q' to quit window")

        # --- VISUALIZATION ---
        color_image = np.asanyarray(color_frame.get_data())
        cv2.rectangle(color_image, (160, 120), (480, 360), (0, 255, 0), 2)
        cv2.imshow('Camera Feed', color_image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
