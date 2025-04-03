import math, time, threading
from Headphones import play_sound


class Vehicle:
    width = 1280
    fov = 160

    tracked_vehicles = {}

    def __init__(
        self, v_id: int, position: tuple, area: float, centre: tuple, classname: str
    ):
        self.v_id = v_id
        self.positions = [position]
        self.areas = [area]
        self.centres = [centre]
        self.distances = []
        self.classname = classname

        if self.centres[0][0] < Vehicle.width / 2:
            self.direction = "left"
        else:
            self.direction = "right"

        if v_id in Vehicle.tracked_vehicles:
            vehicle = Vehicle.tracked_vehicles[v_id]
            self.update_vehicle(vehicle)

        Vehicle.tracked_vehicles[v_id] = self

    def get_positions(self):
        return self.positions

    def get_areas(self):
        return self.areas

    def get_direction(self):
        return self.direction

    def get_centres(self):
        return self.centres

    def update_vehicle(self, vehicle):
        """
        Takes an existing object of Vehicle class and adds its positions and areas to itself.
        """
        self.positions = vehicle.get_positions() + self.positions
        self.areas = vehicle.get_areas() + self.areas
        self.centres = vehicle.get_centres() + self.centres

        if self.centres[-1][0] < Vehicle.width / 2:
            self.direction = "left"
        else:
            self.direction = "right"

    def get_position_change(self) -> float:
        if len(self.positions) < 2:
            return 0.0
        x1, y1 = self.positions[-2]
        x2, y2 = self.positions[-1]

        distance = math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)
        return distance

    def get_area_change(self) -> float:
        if len(self.areas) < 2:
            return 0.0
        elif len(self.areas) < 5:
            return self.areas[-1] - self.areas[-2]
        else:
            # Get area change with an average of the last 4 areas
            areas_avg = []
            for i in range(len(self.areas) - 3):
                average = sum(self.areas[i : i + 4]) / 4
                areas_avg.append(average)
            return areas_avg[-1] - areas_avg[-2]

    @staticmethod
    def play_distance_sound(depth):
        if depth < 20:
            threading.Thread(
                target=play_sound, args=(False, "sound_near.mp3"), daemon=True
            ).start()
        elif depth < 30:
            threading.Thread(
                target=play_sound, args=(False, "sound_1.mp3"), daemon=True
            ).start()
        else:
            threading.Thread(
                target=play_sound, args=(False, "sound_far.mp3"), daemon=True
            ).start()

    def get_warning(self) -> str:
        distance = self.get_position_change()
        area = self.get_area_change()
        direction = self.get_direction()
        # speed = 50 * self.get_distance_change()

        print(f"Distance: {distance}, Area: {area}")

        if distance > 10 or area > 1000:  # area threshold may have to change
            return (
                False,
                f"Warning, vehicle id {self.v_id} moving in {direction} direction, Distance: {distance}, Area: {area}\n",
            )
        else:
            return True, "Safe to cross"

    def append_distance(self, distance):
        self.distances.append(distance)

    def get_distance_change(self):
        if len(self.distances) < 2:
            return 0
        else:
            theta1 = (
                (self.centres[-2][0] - Vehicle.width / 2) / Vehicle.width * Vehicle.fov
            )
            theta1 = math.radians(theta1)
            theta2 = (
                (self.centres[-1][0] - Vehicle.width / 2) / Vehicle.width * Vehicle.fov
            )
            theta2 = math.radians(theta2)

            dist1 = self.distances[-2]
            dist2 = self.distances[-1]

            x1 = dist1 * math.sin(theta1)
            x2 = dist2 * math.sin(theta2)

            dist_change = x2 - x1

            return dist_change
