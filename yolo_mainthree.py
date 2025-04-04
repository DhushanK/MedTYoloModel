import time, threading
from ultralytics import YOLO
import cv2
from Vehicle_Class import Vehicle
from Headphones import play_sound  # new
from gpiozero import DistanceSensor
from gpiozero.pins.pigpio import PiGPIOFactory

# Use pigpio for better ultrasonic accuracy
factory = PiGPIOFactory()

# YOLO Setup
model = YOLO("yolo11n.pt")
names = model.names

# Camera Setup
from picamera2 import Picamera2

picam2 = Picamera2()
picam2.configure(
    picam2.create_preview_configuration(main={"format": "RGB888", "size": (1280, 720)})
)
picam2.start()
width = 1280
height = 720

# Ultrasonic Sensors
sensorA = DistanceSensor(echo=17, trigger=27, max_distance=5, pin_factory=factory)
sensorB = DistanceSensor(echo=22, trigger=23, max_distance=5, pin_factory=factory)
sensorC = DistanceSensor(echo=24, trigger=25, max_distance=5, pin_factory=factory)

# Sensor Settings
DETECTION_THRESHOLD = 50  # cm
DISTANCE_TOLERANCE = 5  # cm


def get_distance(sensor):
    try:
        if not sensor.distance_available:
            print("[DISTANCE WARNING] No echo — skipping.")
            return 999

        distance = round(sensor.distance * 100, 2)
        if distance == 0:
            print("[DISTANCE WARNING] Invalid reading (0).")
            return 999
        return distance
    except Exception as e:
        print(f"[ULTRASONIC ERROR] {e}")
        return 999


def is_same_object(d1, d2):
    return abs(d1 - d2) <= DISTANCE_TOLERANCE


def get_ultrasonic_zone():
    d1 = get_distance(sensorA)
    time.sleep(0.001)
    d2 = get_distance(sensorB)
    time.sleep(0.001)
    d3 = get_distance(sensorC)

    obj1 = d1 < DETECTION_THRESHOLD
    obj2 = d2 < DETECTION_THRESHOLD
    obj3 = d3 < DETECTION_THRESHOLD

    if obj1 and obj2 and obj3 and is_same_object(d1, d2) and is_same_object(d2, d3):
        return "center_overlap", round((d1 + d2 + d3) / 3, 2)
    elif obj1 and obj2 and is_same_object(d1, d2):
        return "between_left_middle", round((d1 + d2) / 2, 2)
    elif obj2 and obj3 and is_same_object(d2, d3):
        return "between_middle_right", round((d2 + d3) / 2, 2)
    elif obj1 and obj3 and is_same_object(d1, d3):
        return "upper_left_overlap", round((d1 + d3) / 2, 2)
    elif obj1:
        return "left_only", d1
    elif obj2:
        return "middle_only", d2
    elif obj3:
        return "right_only", d3
    else:
        return "none", 999


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
        return Vehicle(v_id, position, (x2 - x1) * (y2 - y1), centre, classname)
    return None


# new----------------
def safe_warning():
    # do warning stuff
    threading.Thread(
        target=play_sound, args=(False, "safe_sound.mp3"), daemon=True
    ).start()
    time.sleep(10)
    # lat, lon = 0, 0
    # if get_distance(lat, lon) > 40:
    #     pass


# new----------------


def main():
    last_zone_name = "none"
    last_distance = 999
    last_ultra_time = time.time()
    ultra_interval = 0.5  # 500ms

    while True:
        print(f"[FRAME] Processing frame at {round(time.time(), 2)}")

        frame = picam2.capture_array()
        results = model.track(
            frame, persist=True, tracker="bytetrack.yaml", verbose=False, conf=0.1
        )
        annotated_frame = results[0].plot()
        boxes = results[0].boxes

        current_time = time.time()
        if current_time - last_ultra_time >= ultra_interval:
            last_zone_name, last_distance = get_ultrasonic_zone()
            last_ultra_time = current_time
            print(f"[ULTRA] Zone: {last_zone_name} | Distance: {last_distance} cm")

        zone_name = last_zone_name
        distance = last_distance

        pixel_to_ultrasonic_map = {
            "left": [
                "left_only",
                "upper_left_overlap",
                "between_left_middle",
                "center_overlap",
            ],
            "middle": [
                "center_overlap",
                "middle_only",
                "between_left_middle",
                "between_middle_right",
            ],
            "right": ["right_only", "between_middle_right", "center_overlap"],
        }

        # new---------
        safe_time = time.time()
        # new---------

        for box in boxes:
            vehicle = get_vehicle(box)
            if vehicle:
                x = vehicle.centres[-1][0]

                if x < width / 3:
                    pixel_zone = "left"
                elif x < 2 * width / 3:
                    pixel_zone = "middle"
                else:
                    pixel_zone = "right"

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                print(
                    f"[YOLO] Detected {vehicle.classname.upper()} ID:{vehicle.v_id} in pixel zone: {pixel_zone}"
                )
                print(f"[DEBUG] YOLO zone: {pixel_zone} | Ultrasonic zone: {zone_name}")

                label = f"{vehicle.classname.upper()}"

                if zone_name in pixel_to_ultrasonic_map[pixel_zone]:
                    print(
                        f"[✓] MATCH — {vehicle.classname.upper()} in {pixel_zone} — {distance} cm"
                    )
                    label += f" | Distance: {distance} cm"
                else:
                    print(
                        f"[NO MATCH] — {vehicle.classname.upper()} in {pixel_zone} | Sensor zone: {zone_name} | Distance: {distance} cm"
                    )

                print("test")
                # new----------------
                vehicle.append_distance(distance)
                safe_check, warning_message = vehicle.get_warning()

                if not safe_check:
                    safe_time = time.time()
                    Vehicle.play_distance_sound(distance)
                    print(warning_message)

                # Draw bounding box and label on annotated frame
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    annotated_frame,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )
            if time.time() - safe_time >= 5:
                safe_warning()
                safe_time = time.time()
            # new------------

        cv2.imshow("YOLO11 Tracking", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


if __name__ == "__main__":
    main()
