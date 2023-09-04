import PySimpleGUI as sg
import cv2 as cv
import imutils
import dac
import camera
import calibration
import numpy as np

sg.theme("DarkAmber")

# TODO: make camera selectable
cam = camera.Webcam(0)

# TODO: make DAC selectable
laser = dac.HeliosDAC()
laser.initialize()
laser.set_color(255, 0, 0, 10)

camera_to_laser_transform = np.identity(3)

# Calculate camera preview size
camera_frame_size = cam.get_frame_size()
print(f"Camera frame size: {camera_frame_size}")
camera_aspect_ratio = camera_frame_size[0] / camera_frame_size[1]
camera_preview_size = (round(camera_aspect_ratio * 480), 480)

layout = [
    [
        sg.Text(
            "Uncalibrated. Click Calibrate to begin calibration.",
            key="-CALIBRATION_TEXT-",
        )
    ],
    [sg.Button("Calibrate")],
    [
        sg.Text(
            "1. Click Play to start the laser.\n2. Click below to add points.\n3. Click Clear to clear points.\n4. Click Stop to stop the laser."
        )
    ],
    [sg.Button("Play"), sg.Button("Clear"), sg.Button("Stop"), sg.Button("Quit")],
    [
        sg.Graph(
            canvas_size=camera_preview_size,
            graph_bottom_left=(0, 0),
            graph_top_right=camera_preview_size,
            enable_events=True,
            key="-WEBCAM_FRAME-",
        )
    ],
]

# Create the Window
window = sg.Window("Laser Targeting PoC", layout)


def camera_to_laser(point):
    # Construct homogenous coordinates
    camera_pt = np.array([point[0], point[1], 1])
    laser_pt = np.dot(camera_to_laser_transform, camera_pt)
    # Normalize the result
    laser_pt /= laser_pt[2]
    return (laser_pt[0], laser_pt[1])


def update_camera_frame(cam):
    frame = cam.get_frame()
    if frame is None:
        return

    frame = imutils.resize(
        frame, width=camera_preview_size[0], height=camera_preview_size[1]
    )
    imgbytes = cv.imencode(".png", frame)[1].tobytes()
    window["-WEBCAM_FRAME-"].draw_image(
        data=imgbytes, location=(0, camera_preview_size[1])
    )


# GUI event loop
while True:
    event, values = window.read(
        timeout=33
    )  # Blocking. Timeout ensures 30 fps updates for webcam preview

    if event == sg.WIN_CLOSED or event == "Quit":
        laser.stop()
        break

    elif event == "-WEBCAM_FRAME-":
        # Transform preview coordinates to camera frame coordinates
        # Preview coordinates have (0, 0) at bottom left
        # Camera frame coordinates have (0, 0) at top left
        x, y = values[event]
        print(f"Preview coord: {x}, {y}")
        camera_pt = (
            camera_frame_size[0] / camera_preview_size[0] * x,
            -camera_frame_size[1] / camera_preview_size[1] * y + camera_frame_size[1],
        )
        print(f"Camera frame coord: {camera_pt[0]}, {camera_pt[1]}")
        # Transform camera frame coordinates to laser coordinates
        laser_pt = camera_to_laser(camera_pt)
        print(f"Laser coord: {laser_pt[0]}, {laser_pt[1]}")
        laser.add_point(laser_pt[0], laser_pt[1])
    elif event == "Calibrate":
        # TODO: run calibration on background thread
        camera_to_laser_transform = calibration.calibrate(cam, laser)
        window["-CALIBRATION_TEXT-"].update("Calibrated")
    elif event == "Play":
        laser.clear_points()
        laser.play()
    elif event == "Clear":
        laser.clear_points()
    elif event == "Stop":
        laser.stop()

    update_camera_frame(cam)


laser.close()
window.close()
