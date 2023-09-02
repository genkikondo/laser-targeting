import PySimpleGUI as sg
import cv2 as cv
import imutils
from dac import HeliosDAC

sg.theme("DarkAmber")

# TODO: get canvas size from webcam frame size
canvas_size = (480, 270)

layout = [
    [sg.Button("Play"), sg.Button("Clear"), sg.Button("Stop"), sg.Button("Quit")],
    [
        sg.Text(
            "1. Click Play to start the laser.\n2. Click below to add points.\n3. Click Clear to clear points.\n4. Click Stop to stop the laser."
        )
    ],
    [
        sg.Graph(
            canvas_size=canvas_size,
            graph_bottom_left=(0, 0),
            graph_top_right=canvas_size,
            enable_events=True,
            key="-WEBCAM_FRAME-",
        )
    ],
]

# Create the Window
window = sg.Window("Laser Targeting PoC", layout)


def update_coordinates(x, y):
    window["-COORDINATES-"].update(f"Coordinates: ({x}, {y})")


cap = cv.VideoCapture(0)


def update_camera_frame():
    if not cap:
        return

    result, frame = cap.read()
    if not result:
        return

    frame = imutils.resize(frame, width=canvas_size[0], height=canvas_size[1])
    imgbytes = cv.imencode(".png", frame)[1].tobytes()
    window["-WEBCAM_FRAME-"].draw_image(data=imgbytes, location=(0, canvas_size[1]))


# TODO: make DAC selectable
helios = HeliosDAC()
helios.initialize()
helios.set_color(255, 0, 0, 10)

# GUI event loop
while True:
    event, values = window.read(
        timeout=33
    )  # Blocking. Timeout ensures 30 fps updates for webcam frame

    if event == sg.WIN_CLOSED or event == "Quit":
        break

    elif event == "-WEBCAM_FRAME-":
        x, y = values[event]
        # TODO: transform point to laser projector coordinates
        helios.add_point(x, y)
    elif event == "Play":
        helios.clear_points()
        helios.play()
    elif event == "Clear":
        helios.clear_points()
    elif event == "Stop":
        helios.stop()

    update_camera_frame()

helios.close()
window.close()
