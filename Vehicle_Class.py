import math, winsound

class Vehicle:
    tracked_vehicles = {}

    def __init__(self, v_id: int, position: tuple, area: float, centre: tuple):
        self.v_id = v_id
        self.positions = [position]
        self.areas = [area]
        self.centres = [centre]
        
        width = 1280 # Might have to change
        if self.centres[0][0] < width / 2:
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
        
        width = 1280 # Might have to change
        if self.centres[-1][0] < width / 2:
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

    def get_warning(self) -> str:
        distance = self.get_position_change()
        area = self.get_area_change()
        direction = self.get_direction()
        print(f"Distance: {distance}, Area: {area}")

        if distance > 10 or area > 1000:  # area threshold may have to change
            #frequency = 2500  # Set Frequency To 2500 Hertz
            #duration = 100  # Set Duration To 1000 ms == 1 second
            #winsound.Beep(frequency, duration)

            return False, f"Warning, vehicle id {self.v_id} moving in {direction} direction, Distance: {distance}, Area: {area}\n"
        else:
            self.signal_safe()
            return True, "Safe to cross"
