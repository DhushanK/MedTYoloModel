from ultralytics import YOLO
import cv2
from Vehicle_Class import Vehicle
import time
from gpiozero import DistanceSensor

# YOLO Setup
model = YOLO("yolo11n.pt")
names = model.names

# Camera Setup
from picamera2 import Picamera2
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": "RGB888", "size": (1280, 720)}))
picam2.start()
width = 1280
height = 720

# Ultrasonic Sensor using default GPIO backend
sensor = DistanceSensor(echo=17, trigger=27, max_distance=2.0)

# Sensor Settings
DETECTION_THRESHOLD = 50  # cm

def get_distance():
    try:
        distance = round(sensor.distance * 100, 2)
        if distance == 0:
            print("[DISTANCE WARNING] Invalid reading (0).")
            return 999
        return distance
    except Exception as e:
        print(f"[ULTRASONIC ERROR] {e}")
        return 999

def get_vehicle(box):
    vehicle_list = ["car", "motorcycle", "bicycle", "bus", "truck", "person"]
    classname = names[int(box.cls)]

    if classname in vehicle_list:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        if box.id is None:
            return None
        v_id = int(box.id)
        centre = ((x1 + x2) / 2, (y1 + y2) / 2)
        position = (x2, centre[1]) if centre[0] < width / 2 else (x1, centre[1])
        return Vehicle(v_id, position, (x2 - x1) * (y2 - y1), centre)
    return None

def main():
    while True:
        print(f"[FRAME] Processing frame at {round(time.time(), 2)}")

        frame = picam2.capture_array()
        results = model.track(frame, persist=True, tracker="bytetrack.yaml", verbose=False, conf=0.1)
        annotated_frame = results[0].plot()
        boxes = results[0].boxes

        distance = get_distance()
        print(f"[ULTRASONIC] Distance: {distance} cm")

        for box in boxes:
            vehicle = get_vehicle(box)
            if vehicle:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                classname = names[int(box.cls)].upper()
                label = f"{classname} | Distance: {distance} cm"

                print(f"[YOLO] {label}")

                # Draw bounding box and label
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(annotated_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow("YOLO11 Tracking", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

if __name__ == "__main__":
    main()
