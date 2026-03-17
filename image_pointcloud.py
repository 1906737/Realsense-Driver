import pyrealsense2 as rs
import numpy as np
import open3d as o3d

def main():
    # 1. Pipeline Setup
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    profile = pipeline.start(config)

    # Get Intrinsics
    intr = profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()
    pinhole_intrinsics = o3d.camera.PinholeCameraIntrinsic(
        intr.width, intr.height, intr.fx, intr.fy, intr.ppx, intr.ppy)

    # 2. Visualization Setup
    vis = o3d.visualization.Visualizer()
    vis.create_window("D435i - Optimized Cloud", width=1280, height=720)
    
    # Add a Coordinate Frame (X=Red, Y=Green, Z=Blue)
    # This acts as your "numbers/axis" reference in 3D space
    axes = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.5, origin=[0, 0, 0])
    vis.add_geometry(axes)

    # Create a Grid Floor
    grid_size = 2.0
    grid_steps = 10
    grid = o3d.geometry.LineSet.create_from_axis_aligned_bounding_box(
        o3d.geometry.AxisAlignedBoundingBox(min_bound=(-1, -1, 0), max_bound=(1, 1, 2))
    )
    vis.add_geometry(grid)

    pcd = o3d.geometry.PointCloud()
    vis.add_geometry(pcd)
    
    align = rs.align(rs.stream.color)

    try:
        while True:
            frames = pipeline.wait_for_frames()
            aligned_frames = align.process(frames)
            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()

            if not depth_frame or not color_frame:
                continue

            # Convert to Open3D format
            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())
            
            rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
                o3d.geometry.Image(color_image),
                o3d.geometry.Image(depth_image),
                convert_rgb_to_intensity=False
            )

            # Generate Cloud
            temp_pcd = o3d.geometry.PointCloud.create_from_rgbd_image(rgbd, pinhole_intrinsics)
            
            # --- PERFORMANCE BOOST: DOWNSAMPLING ---
            # voxel_size=0.02 means it merges points within a 2cm cube into one point
            downsampled_pcd = temp_pcd.voxel_down_sample(voxel_size=0.02)
            
            # Standard Orientation Flip
            downsampled_pcd.transform([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])

            # Update geometry
            pcd.points = downsampled_pcd.points
            pcd.colors = downsampled_pcd.colors
            
            vis.update_geometry(pcd)
            vis.poll_events()
            vis.update_renderer()

    finally:
        pipeline.stop()
        vis.destroy_window()

if __name__ == "__main__":
    main()
