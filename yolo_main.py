from ultralytics import YOLO
import cv2
from Vehicle_Class import Vehicle

import time

# model there is also yolo11n yolo11s yolo11m yolo11l yolo11x, dunno which is best
model = YOLO("yolo11n.pt")
names = model.names
# print(names)
ESP32_URL = "http://192.168.1.100/video"  # change as needed
# cap = cv2.VideoCapture(ESP32_URL)
cap = cv2.VideoCapture(0)  # Change to 0 for camera
width = 1280
height = 720
cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)


def get_vehicle(box):
    """
    Checks if the box is a vehicle and creates a vehicle class.
    """
    vehicle_list = ["car", "motorcycle", "bicycle", "bus", "truck", "person"]
    classname = names[int(box.cls)]

    if classname in vehicle_list:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        v_id = int(box.id)
        centre = ((x1 + x2) / 2, (y1 + y2) / 2)
        area = (x2 - x1) * (y2 - y1)

        if centre[0] < width / 2:
            # left side of the screen, use middle right for position
            position = (x2, centre[1])
        else:
            # right side of the screen, use middle left pixel for position
            position = (x1, centre[1])

        vehicle = Vehicle(v_id, position, area, centre)

        return vehicle
    return None


def safe_warning():
    pass
    # do warning stuff
    # lat, lon = 0, 0
    # if get_distance(lat, lon) > 40:
    #     pass


def main():
    # -------------------
    # lat, lon = 0, 0  # change accordingly
    # while get_distance(lat, lon) > 40:
    #     pass
    # -------------------

    while cap.isOpened():
        safe_time = time.time()
        success, frame = cap.read()
        if success:
            results = model.track(
                frame, persist=True, tracker="bytetrack.yaml", verbose=False, conf=0.1
            )
            annotated_frame = results[0].plot()
            boxes = results[0].boxes

            for box in boxes:
                vehicle = get_vehicle(box)
                if vehicle:
                    safe_check, warning_message = vehicle.get_warning()

                    if not safe_check:
                        safe_time = time.time()
                        print(warning_message)

            if time.time() - safe_time >= 5:
                safe_warning()
                safe_time = time.time()

            cv2.imshow("YOLO11 Tracking", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        else:
            # Break the loop if the end of the video is reached
            break
    cap.release()

if __name__ == "__main__":
    main()
