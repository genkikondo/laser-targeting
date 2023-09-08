import PySimpleGUI as sg
import cv2 as cv
import imutils
import dac
import camera
import calibration
import numpy as np

sg.theme("DarkAmber")


def find_cameras():
    """Find all available cameras.

    Note that if multiple cameras are available, their indices are not necessarily sequential.
    We stop looking if we have checked several indices in a row without available cameras.
    """
    camera_idx = 0
    available_camera_indices = []
    sequential_unavailable_indices = 0
    while sequential_unavailable_indices <= 5:
        camera = cv.VideoCapture(camera_idx)
        if camera.isOpened():
            available_camera_indices.append(camera_idx)
            sequential_unavailable_indices = 0
        else:
            sequential_unavailable_indices += 1
        camera_idx += 1

    return available_camera_indices


available_cameras = find_cameras()
cam = camera.Webcam(available_cameras[0])

available_dacs = []

laser = None
helios_dac = dac.HeliosDAC()
helios_dac.set_color(1, 0, 0, 0.1)
num_helios_dacs = helios_dac.initialize()
for i in range(num_helios_dacs):
    available_dacs.append((f"Helios DAC: {i}", "helios", i))
if num_helios_dacs > 0:
    laser = helios_dac

etherdream_dac = dac.EtherDreamDAC()
etherdream_dac.set_color(1, 0, 0, 0.1)
num_etherdream_dacs = etherdream_dac.initialize()
for i in range(num_helios_dacs):
    available_dacs.append((f"Ether Dream DAC: {i}", "etherdream", i))
if laser is None and num_etherdream_dacs > 0:
    etherdream_dac.connect(0)
    laser = etherdream_dac

camera_to_laser_transform = np.identity(3)

# Calculate camera preview size
camera_frame_size = cam.get_frame_size()
print(f"Camera frame size: {camera_frame_size}")
camera_aspect_ratio = camera_frame_size[0] / camera_frame_size[1]
camera_preview_size = (round(camera_aspect_ratio * 480), 480)

layout = [
    [
        sg.Text("Camera"),
        sg.Combo(
            available_cameras,
            default_value=(
                available_cameras[0] if len(available_cameras) > 0 else None
            ),
            enable_events=True,
            key="-CAMERA_SELECTION-",
        ),
        sg.Text("Laser DAC"),
        sg.Combo(
            list(map(lambda dac: dac[0], available_dacs)),
            default_value=(available_dacs[0][0] if len(available_dacs) > 0 else None),
            enable_events=True,
            key="-DAC_SELECTION-",
        ),
    ],
    [
        sg.Text(
            "Uncalibrated. Click Calibrate to begin calibration.",
            key="-CALIBRATION_TEXT-",
        )
    ],
    [sg.Button("Calibrate")],
    [
        sg.Text(
            "1. Click Play to start the laser.\n2. Click below to add points. Drag to track the cursor.\n3. Click Undo to remove last point.\n4. Click Clear to clear points.\n5. Click Stop to stop the laser."
        )
    ],
    [
        sg.Button("Play"),
        sg.Button("Undo"),
        sg.Button("Clear"),
        sg.Button("Stop"),
        sg.Button("Quit"),
    ],
    [
        sg.Graph(
            canvas_size=camera_preview_size,
            graph_bottom_left=(0, 0),
            graph_top_right=camera_preview_size,
            enable_events=True,
            drag_submits=True,
            key="-WEBCAM_FRAME-",
        )
    ],
]

# Create the Window
window = sg.Window("Laser Targeting PoC", layout)


def update_available_cameras():
    available_camera_indices = find_cameras()
    window["-CAMERA_SELECTION-"].update(available_camera_indices)


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
    window["-WEBCAM_FRAME-"].erase()
    window["-WEBCAM_FRAME-"].draw_image(
        data=imgbytes, location=(0, camera_preview_size[1])
    )


isTracking = False

# GUI event loop
while True:
    event, values = window.read(
        timeout=33
    )  # Blocking. Timeout ensures 30 fps updates for webcam preview

    if event == sg.WIN_CLOSED or event == "Quit":
        laser.stop()
        break

    elif event == "-CAMERA_SELECTION-":
        cam = camera.Webcam(values[event])
    elif event == "-DAC_SELECTION-":
        for dac_name, dac_type, dac_idx in available_dacs:
            if dac_name == values[event]:
                if dac_type == "helios":
                    laser = helios_dac
                    laser.set_dac_idx(dac_idx)
                elif dac_type == "etherdream":
                    laser = etherdream_dac
                    laser.connect(dac_idx)
    elif event == "-WEBCAM_FRAME-":
        # Transform preview coordinates to camera frame coordinates
        # Preview coordinates have (0, 0) at bottom left
        # Camera frame coordinates have (0, 0) at top left
        x, y = values[event]
        camera_pt = (
            camera_frame_size[0] / camera_preview_size[0] * x,
            -camera_frame_size[1] / camera_preview_size[1] * y + camera_frame_size[1],
        )
        # Transform camera frame coordinates to laser coordinates
        laser_pt = camera_to_laser(camera_pt)

        if laser.in_bounds(laser_pt[0], laser_pt[1]):
            if isTracking:
                # This is an existing point, so remove the last point
                laser.remove_point()

            isTracking = True
            laser.add_point(laser_pt[0], laser_pt[1])
    elif event == "-WEBCAM_FRAME-+UP":
        isTracking = False
    elif event == "Calibrate":
        # TODO: run calibration on background thread
        camera_to_laser_transform = calibration.calibrate(cam, laser)
        window["-CALIBRATION_TEXT-"].update("Calibrated")
    elif event == "Play":
        laser.clear_points()
        laser.play()
    elif event == "Undo":
        laser.remove_point()
    elif event == "Clear":
        laser.clear_points()
    elif event == "Stop":
        laser.stop()

    update_camera_frame(cam)


laser.close()
window.close()
