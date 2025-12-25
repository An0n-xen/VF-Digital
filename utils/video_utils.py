import cv2
import logging
import time
import numpy as np
from utils.logger_config import setup_logger

# Setting up logger
logger = setup_logger(__name__, level=logging.INFO)


def preprocess_video(video_path, target_fps=10, target_size=(320, 240)):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        logger.error(f"Error: Could not open video {video_path}")
        return None

    # Video properties
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    total_src_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Calculate the "Step"
    step = original_fps / target_fps

    logger.info(f"Optimization: Processing 1 out of every {step:.2f} frames...")

    processed_frames = []

    current_src_frame = 0  # Where we are in the source video
    target_frame_count = 0  # How many frames we have captured so far

    while True:
        should_decode = current_src_frame >= (target_frame_count * step)

        if should_decode:
            # RETRIEVE: Actually decode the image
            ret, frame = cap.read()
            if not ret:
                logger.error(f"Error: Could not read frame {current_src_frame}")
                break

            # Process it
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            resized_frame = cv2.resize(
                gray_frame, target_size, interpolation=cv2.INTER_AREA
            )
            processed_frames.append(resized_frame)

            target_frame_count += 1
        else:
            ret = cap.grab()
            if not ret:
                break

        current_src_frame += 1

    cap.release()
    logger.info(f"Done! Processed {len(processed_frames)} frames.")
    return np.array(processed_frames)


def extract_fingerprint(frames):
    """
    Converts a stack of frames into fingerprints.

    Args:
        frames (np.array): Shape (N, 240, 320), grayscale.

    Returns:
        np.array: Shape (N, 8). The fingerprints.
    """

    fingerprints = []

    # Grid parameters
    N_ROWS = 2
    M_COLS = 4

    # Get image dimensions
    if len(frames) == 0:
        return np.array([])
    img_h, img_w = frames[0].shape

    # Calculate block sizes
    blk_h = img_h // N_ROWS
    blk_w = img_w // M_COLS

    logger.info(f"Extracting fingerprints from {len(frames)} frames...")

    for k, frame in enumerate(frames):
        # Compute gradients
        gx = cv2.Sobel(frame, cv2.CV_64F, 1, 0, ksize=1)
        gy = cv2.Sobel(frame, cv2.CV_64F, 0, 1, ksize=1)

        # magnitude (r)
        magnitude = np.sqrt(gx**2 + gy**2)

        # orientation (theta)
        orientation = np.arctan2(gy, gx)

        frame_fingerprint = []

        for n in range(N_ROWS):
            for m in range(M_COLS):
                # Define the slice for this block
                y_start = n * blk_h
                y_end = (n + 1) * blk_h
                x_start = m * blk_w
                x_end = (m + 1) * blk_w

                # Extract r and theta for just this block
                mag_block = magnitude[y_start:y_end, x_start:x_end]
                ori_block = orientation[y_start:y_end, x_start:x_end]

                # Calculate the Centriod
                numerator = np.sum(mag_block * ori_block)
                denominator = np.sum(mag_block)

                # Avoid divide by zero
                if denominator == 0:
                    centroid = 0.0
                else:
                    centroid = numerator / denominator

                frame_fingerprint.append(centroid)

        fingerprints.append(frame_fingerprint)

    return np.array(fingerprints)
