import cv2 as cv
import numpy as np
import time


def calibrate(camera, laser):
    """Use image correspondences to compute the transformation matrix from camera to laser

    1. Shoot the laser at predetermined points
    2. For each laser point, capture an image from the camera
    3. Identify the corresponding point in the camera frame
    4. Compute the transformation matrix from camera to laser
    """

    print("Calibrating...")
    laser.stop()
    laser.clear_points()
    laser.set_color(100, 0, 0, 10)
    calibration_points = (
        laser.get_bounds() + laser.get_bounds(500) + laser.get_bounds(1000)
    )

    bg_frame = camera.get_frame()
    if bg_frame is None:
        return

    # Get image correspondences
    laser_points = []
    camera_points = []
    for calibration_point in calibration_points:
        res = get_camera_point_for_laser_point(
            camera, laser, calibration_point, bg_frame
        )
        if res is not None:
            print(
                f"Point correspondence found: laser = {calibration_point}, camera = {res}"
            )
            laser_points.append(calibration_point)
            camera_points.append(res)
        else:
            print(f"Failed to find point correspondence: laser = {calibration_point}")

    print(f"{len(laser_points)} point correspondences found.")

    transform = dlt(laser_points, camera_points)

    print("Calibration successful")

    return transform


def get_mask(frame, bg_frame=None):
    # Get binary mask
    # TODO: try different filters and thresholds. This is very sensitive to the calibration environment

    if bg_frame is not None:
        frame = cv.absdiff(frame, bg_frame)

    mask = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    _, mask = cv.threshold(mask, 100, 255, cv.THRESH_BINARY)

    """
    frame_hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    thresh_min = np.array([0, 0, 128], np.uint8)
    thresh_max = np.array([32, 115, 255], np.uint8)
    mask = cv.inRange(frame_hsv, thresh_min, thresh_max)
    """

    return mask


def get_best_centroid(mask):
    # Find centroid
    contours, _ = cv.findContours(mask, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)

    # There may have been more than one contour detected. Find the best candidate
    max_circularity = 0
    best_contour = None
    for contour in contours:
        area = cv.contourArea(contour)
        perimeter = cv.arcLength(contour, True)

        # TODO: this value is sensitive to the calibration environment
        if area < 100:
            continue

        circularity = (4 * np.pi * area) / (perimeter**2)
        if circularity > max_circularity:
            best_contour = contour
            max_circularity = circularity

    if best_contour is None:
        return None

    # Calculate the moments of the contour
    M = cv.moments(best_contour)

    # Calculate the centroid coordinates
    if M["m00"] == 0:
        return None

    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])
    return (cx, cy)


def get_camera_point_for_laser_point(camera, laser_dac, laser_point, bg_frame=None):
    """Reads a frame from the camera and returns the camera coordinates of the laser point"""
    laser_dac.clear_points()
    laser_dac.add_point(laser_point[0], laser_point[1])
    laser_dac.play()

    time.sleep(2)

    try:
        frame = camera.get_frame()
        if frame is None:
            return

        # Get binary mask
        mask = get_mask(frame, bg_frame)

        # Find best centroid
        return get_best_centroid(mask)
    finally:
        laser_dac.stop()


def dlt(laser_points, camera_points):
    """Estimate the transformation matrix between camera and laser using the Direct Linear Transform algorithm"""

    # Normalize the points to help stabilize DLT
    laser_points, laser_points_normalization_matrix = normalize_points(
        np.array(laser_points)
    )
    camera_points, camera_points_normalization_matrix = normalize_points(
        np.array(camera_points)
    )

    # Construct list of points in homogeneous coordinates
    laser_points = np.hstack((laser_points, np.ones((laser_points.shape[0], 1))))
    camera_points = np.hstack((camera_points, np.ones((camera_points.shape[0], 1))))

    # Construct the linear equation matrix A
    A = []
    for i in range(len(camera_points)):
        x1, y1, z1 = camera_points[i]
        x2, y2, z2 = laser_points[i]
        A.append([0, 0, 0, -z2 * x1, -z2 * y1, -z2 * z1, y2 * x1, y2 * y1, y2 * z1])
        A.append([z2 * x1, z2 * y1, z2 * z1, 0, 0, 0, -x2 * x1, -x2 * y1, -x2 * z1])
    A = np.array(A)

    # Perform Singular Value Decomposition (SVD) to obtain the transformation matrix P
    _, _, V = np.linalg.svd(A)
    P = V[-1].reshape(3, 3)

    # Denormalize the transformation matrix P
    P_denormalized = np.dot(
        np.linalg.inv(laser_points_normalization_matrix),
        np.dot(P, camera_points_normalization_matrix),
    )

    return P_denormalized


def normalize_points(points):
    # Calculate the centroid of the points
    centroid = np.mean(points, axis=0)

    # Calculate the average distance from the centroid
    avg_distance = np.mean(np.linalg.norm(points - centroid, axis=1))

    # Scale and translate the points
    scale_factor = np.sqrt(2) / avg_distance
    translation_vector = -scale_factor * centroid

    # Create the transformation matrix for normalization
    T = np.array(
        [
            [scale_factor, 0, translation_vector[0]],
            [0, scale_factor, translation_vector[1]],
            [0, 0, 1],
        ]
    )

    # Apply the transformation to the points
    normalized_points = np.dot(T, np.vstack((points.T, np.ones(len(points)))))
    normalized_points = normalized_points[:2, :].T

    return normalized_points, T
