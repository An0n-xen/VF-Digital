import os
import cv2
import logging
import numpy as np
import matplotlib.pyplot as plt
from utils.logger_config import setup_logger

logger = setup_logger(__name__, level=logging.INFO)


def visualize_db_entry(db, file_id, frame_idx=0):
    """
    Visualizes a specific frame and its fingerprint from the database.
    Automatically finds the original video file to show the background image.
    """
    # Load Metadata
    if file_id not in db.metadata:
        logger.error(f"Error: ID {file_id} not found in database.")
        return

    meta = db.metadata[file_id]
    video_path = meta["original_path"]
    logger.info(f"Visualizing: {meta['name']} | Frame: {frame_idx}")

    # Load the Fingerprint
    npy_path = os.path.join(db.fp_folder, f"{file_id}.npy")
    # Use mmap to load just the one row we need
    full_fp_array = np.load(npy_path, mmap_mode="r")
    logger.info(f"Loaded fingerprint for ID {file_id}")

    if frame_idx >= len(full_fp_array):
        logger.error(
            f"Error: Frame {frame_idx} exceeds duration ({len(full_fp_array)} frames)"
        )
        return

    fingerprint = full_fp_array[frame_idx]

    timestamp = frame_idx / 10.0

    cap = cv2.VideoCapture(video_path)
    # Jump to the specific time
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        logger.error("Error: Could not read frame from original video file.")
        return

    # Resize to standard analysis size (320x240) to match the grid logic
    frame_resized = cv2.resize(frame, (320, 240))

    # Draw the Visualization
    _draw_overlay(frame_resized, fingerprint, title=f"Frame {frame_idx} ({timestamp}s)")


def _draw_overlay(frame_bgr, fingerprint, title="Fingerprint"):
    """Helper function to draw the grid and arrows."""
    # Convert to RGB for Matplotlib
    viz_img = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

    h, w = viz_img.shape[:2]
    rows, cols = 2, 4
    blk_h, blk_w = h // rows, w // cols

    # Draw Faint Grid
    for r in range(1, rows):
        y = r * blk_h
        cv2.line(viz_img, (0, y), (w, y), (0, 255, 0), 1)
    for c in range(1, cols):
        x = c * blk_w
        cv2.line(viz_img, (x, 0), (x, h), (0, 255, 0), 1)

    # Draw Arrows
    arrow_len = 25
    for i, angle in enumerate(fingerprint):
        r, c = i // cols, i % cols
        cx, cy = c * blk_w + (blk_w // 2), r * blk_h + (blk_h // 2)

        # End point
        end_x = int(cx + arrow_len * np.cos(angle))
        end_y = int(cy + arrow_len * np.sin(angle))

        # Color based on angle (just for fun/clarity)
        # Map angle -pi..pi to Hue 0..179
        hue = int(((angle + np.pi) / (2 * np.pi)) * 179)
        # We need to convert this single color to RGB
        color_hsv = np.uint8([[[hue, 255, 255]]])
        color_rgb = cv2.cvtColor(color_hsv, cv2.COLOR_HSV2RGB)[0][0]
        color_tuple = (int(color_rgb[0]), int(color_rgb[1]), int(color_rgb[2]))

        cv2.arrowedLine(
            viz_img, (cx, cy), (end_x, end_y), color_tuple, 2, tipLength=0.3
        )

    plt.figure(figsize=(6, 4))
    plt.imshow(viz_img)
    plt.title(title)
    plt.axis("off")
    plt.show()


def visualize_search_score(db_fingerprints, query_fingerprints):
    """
    Plots the 'Distance Score' for every position in the video.
    This shows you exactly where the match happened.
    """
    K = len(query_fingerprints)
    scores = []

    # Calculate scores for sliding window
    # (Note: For visualization, we do this un-optimized loop to plot the graph)
    for i in range(len(db_fingerprints) - K + 1):
        window = db_fingerprints[i : i + K]
        diff = window - query_fingerprints
        score = np.mean(diff**2)
        scores.append(score)

    scores = np.array(scores)

    # Find best match
    min_idx = np.argmin(scores)
    min_score = scores[min_idx]

    # Plot
    plt.figure(figsize=(10, 4))
    plt.plot(scores, label="Difference Score", color="gray")

    # Highlight the match
    plt.plot(min_idx, min_score, "ro", label=f"Best Match (Frame {min_idx})")

    # Draw Threshold Line (T=0.4 from paper)
    plt.axhline(y=0.4, color="g", linestyle="--", label="Threshold (0.4)")

    plt.xlabel("Frame Index")
    plt.ylabel("Euclidean Distance")
    plt.title("Search Scan: Lower is Better")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()


if __name__ == "__main__":
    logging.info(f"[+] {"---" * 10} VISUALIZING {"---" * 10} [+]")
    db = VideoDatabase("test_db")

    if len(db.metadata) > 0:
        # Get the first file ID
        test_id = list(db.metadata.keys())[0]

        #  Visualizing the arrows on Frame 100
        logging.info("Visualizing the arrows on Frame 100")
        visualize_db_entry(db, test_id, frame_idx=100)

        # 2. Visualizing the Search Graph
        # Load data to simulate a search
        logging.info(f"[+] {"---" * 10} LOADING DATA {"---" * 10} [+]")
        full_fps = np.load(os.path.join(db.fp_folder, f"{test_id}.npy"))

        # Create a query (Frames 200-300)
        query = full_fps[200:300]

        # Show the plot
        logging.info(f"[+] {"---" * 10} GENERATING SEARCH PLOT {"---" * 10} [+]")
        visualize_search_score(full_fps, query)
