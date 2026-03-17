import pyrealsense2 as rs
import numpy as np
import matplotlib.pyplot as plt

def main():
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    pipeline.start(config)

    # Spatial filter helps smooth the 'chain' effect
    spatial = rs.spatial_filter()
    spatial.set_option(rs.option.filter_magnitude, 2)
    
    plt.ion()
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    pc = rs.pointcloud()

    try:
        while True:
            frames = pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            if not depth_frame: continue

            # Pre-processing for a cleaner surface
            filtered_depth = spatial.process(depth_frame)
            points = pc.calculate(filtered_depth)
            v = points.get_vertices()
            data = np.asanyarray(v).view(np.float32).reshape(-1, 3)

            # Masking for reasonable range (0.1m to 4m)
            mask = (data[:, 2] > 0.1) & (data[:, 2] < 4.0)
            data = data[mask]
            
            # Subsampling to keep Matplotlib responsive
            data = data[::70]

            x, y, z = data[:, 0], data[:, 1], data[:, 2]

            # --- ADAPTIVE Z LIMITS ---
            if len(z) > 0:
                z_min, z_max = np.min(z), np.max(z)
                # Ensure a minimum 0.5m window to prevent 'jitter'
                if (z_max - z_min) < 0.5:
                    z_max = z_min + 0.5
                current_z_limit = (z_min, z_max)
            else:
                current_z_limit = (0.2, 2.0)

            ax.clear()

            # --- COLOR BY DEPTH (Z) ---
            # 'c=z' maps the color gradient to the distance from the camera.
            # 'turbo' or 'plasma' provide high contrast for distance.
            ax.scatter(x, y, z, c=z, cmap='turbo', s=10, alpha=0.8)

            ax.set_xlabel('X (Lateral)')
            ax.set_ylabel('Y (Height)')
            ax.set_zlabel('Z (Adaptive Depth)')
            
            # Lock X and Y for a stable view, adapt Z
            ax.set_xlim(-0.7, 0.7)
            ax.set_ylim(-0.4, 0.4) 
            ax.set_zlim(current_z_limit) 
            
            ax.invert_yaxis() 
            plt.pause(0.001)

    except KeyboardInterrupt:
        pass
    finally:
        pipeline.stop()
        plt.close()

if __name__ == "__main__":
    main()
