import math
import pygame
import random
import os, json, copy

BRAIN_FILE = "best_brain.json"

def save_best_brain(brain): 
    with open(BRAIN_FILE, "w") as f:
        json.dump(brain.to_dict(), f)          # you need a to_dict()/from_dict() on your network
    print(f"Best brain saved to {BRAIN_FILE}")

def load_best_brain():
    if not os.path.exists(BRAIN_FILE):
        return None
    try:
        with open(BRAIN_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # file is empty or corrupted: remove it and treat as “no brain”
        print(f"Warning: {BRAIN_FILE} is corrupted, deleting it.")
        os.remove(BRAIN_FILE)
        return None
 
class Level: 
    def __init__(self, input_size, output_size):
        self.inputs = [0.0] * input_size
        self.outputs = [0.0] * output_size
        self.biases = [0.0] * output_size

        self.weights = [
            [0.0] * output_size for _ in range(input_size)
        ]

        self.randomize_weights()

    def randomize_weights(self):
        for i in range(len(self.inputs)):
            for j in range(len(self.outputs)):
                self.weights[i][j] = random.uniform(-1, 1)
        for i in range(len(self.biases)):
            self.biases[i] = random.uniform(-1, 1)

    def feedforward(given_inputs, level: "Level"):
        for i in range(len(level.inputs)):
            level.inputs[i] = given_inputs[i]
        for j in range(len(level.outputs)):
            sum = 0
            for i in range(len(level.inputs)):
                sum += level.inputs[i] * level.weights[i][j]
            level.outputs[j] = 1.0 if sum > level.biases[j] else 0.0
        return level.outputs


class NeuralNetwork:
    def __init__(self, neuron_count):
        self.levels = []
        for i in range(len(neuron_count) - 1):
            self.levels.append(Level(neuron_count[i], neuron_count[i + 1]))

    def feedforward(given_inputs, network: "NeuralNetwork"):
        outputs = Level.feedforward(given_inputs, network.levels[0])
        for lvl in network.levels[1:]:
            outputs = Level.feedforward(outputs, lvl)
        return outputs
    
    def mutate(network: "NeuralNetwork", mutation_rate=1.0):
        for level in network.levels:
            for i in range(len(level.biases)):
                level.biases[i] = lerp(
                    level.biases[i], 
                    random.uniform(-1, 1), 
                    mutation_rate
                )
            for i in range(len(level.weights)):
                for j in range(len(level.weights[i])):
                    level.weights[i][j] = lerp(
                        level.weights[i][j], 
                        random.uniform(-1, 1), 
                        mutation_rate
                    )

    def to_dict(self):
        return {
            "levels": [
                {"weights": level.weights, "biases": level.biases}
                for level in self.levels
            ]
        }

    @classmethod
    def from_dict(cls, data):
        levels = data["levels"]

        # 1) Reconstruct the neuron-counts from the saved data
        neuron_counts = [ len(lvl["weights"]) for lvl in levels ]
        neuron_counts.append(len(levels[-1]["biases"]))

        # 2) Build a network of exactly that shape
        nn = cls(neuron_counts)

        # 3) Copy in every weight & bias
        for level_obj, saved in zip(nn.levels, levels):
            # deep-copy so future mutations don't bleed over
            level_obj.weights = [ row[:] for row in saved["weights"] ]
            level_obj.biases  = saved["biases"][:]
        return nn
            
class Sensor:
    def __init__(self, car, ray_count=5, ray_length=150, ray_spread=math.pi / 2):
        self.car = car
        self.ray_count = ray_count
        self.ray_length = ray_length
        self.ray_spread = ray_spread
        self.rays = []
        self.readings = []

    def update(self, road_borders, traffic):
        self.cast_rays()
        self.readings = [
            self.get_reading(ray, road_borders, traffic) 
            for ray in self.rays
        ]

    def get_reading(self, ray, road_borders, traffic):
        touches = []
        for border in road_borders:
            collision = get_intersection(ray[0], ray[1], border[0], border[1])
            if collision:
                touches.append(collision)

        for other_car in traffic:
            poly = other_car.polygon
            for i in range(len(poly)):
                p1 = poly[i]
                p2 = poly[(i + 1) % len(poly)]
                hit = get_intersection(ray[0], ray[1], p1, p2)
                if hit:
                    touches.append(hit)

        if not touches:
            return None
        min_offset = min(touch["offset"] for touch in touches)
        for touch in touches:
            if touch["offset"] == min_offset:
                return touch
            
    def cast_rays(self):
        self.rays = []
        for i in range(self.ray_count):
            if self.ray_count == 1:
                fraction = .5
            else:
                fraction = i / (self.ray_count - 1)
            ray_angle = lerp(self.ray_spread/2, -self.ray_spread /2, fraction) + self.car.angle

            start = pygame.math.Vector2(self.car.x, self.car.y)
            end = pygame.math.Vector2(
                self.car.x - math.sin(ray_angle) * self.ray_length,
                self.car.y - math.cos(ray_angle) * self.ray_length
            )
            self.rays.append((start, end))

    def draw(self, screen, offset_y=0):
        for i in range(self.ray_count):
            start, end = self.rays[i]
            reading = self.readings[i]

            if reading: 
                end_point = pygame.math.Vector2(reading["x"], reading["y"] )
            else: 
                end_point = end

            s_pos = (start.x, start.y + offset_y)
            e_pos = (end_point.x, end_point.y + offset_y)
            orig_end_pos = (end.x, end.y + offset_y)
            pygame.draw.line(screen, (255, 255, 0), s_pos, e_pos, 2)
            pygame.draw.line(screen, (0, 0, 0), orig_end_pos, e_pos, 2)
# A simple controls class to store key states

class Controls:
    def __init__(self, control_type):
        self.type = control_type
        self.forward = False
        self.reverse = False
        self.left = False
        self.right = False

    def steer(self):
        # Update control states based on key presses
        if self.type == "keys":
            keys = pygame.key.get_pressed()
            self.forward = keys[pygame.K_UP]
            self.reverse = keys[pygame.K_DOWN]
            self.left = keys[pygame.K_LEFT]
            self.right = keys[pygame.K_RIGHT]
        elif self.type == "dummy":   
            # Dummy control logic for the car
            self.forward = True
            self.left    = False
            self.right   = False
            self.reverse = False

def get_intersection(p1, p2, p3, p4):

    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y
    x3, y3 = p3.x, p3.y
    x4, y4 = p4.x, p4.y

    denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
    if denom == 0:
        return None  # parallel or coincident

    t = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
    u = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom

    if 0 <= t <= 1 and 0 <= u <= 1:
        intersect_x = x1 + t * (x2 - x1)
        intersect_y = y1 + t * (y2 - y1)
        return {
            "x": intersect_x,
            "y": intersect_y,
            "offset": t
        }
    return None

def polys_intersect(poly1, poly2):
    n1 = len(poly1)
    n2 = len(poly2)
    for i in range(n1):
        p1_start = poly1[i]
        p1_end   = poly1[(i + 1) % n1]
        for j in range(n2):
            p2_start = poly2[j]
            p2_end   = poly2[(j + 1) % n2]
            if get_intersection(p1_start, p1_end, p2_start, p2_end):
                return True
    return False

def draw_dashed_line(surf, color, start_pos, end_pos, width=1, dash_length=20, space_length=20):
    """ Draw a dashed line on a Pygame surface.
        This function draws dashes from start_pos to end_pos.
    """
    origin = pygame.math.Vector2(start_pos)
    target = pygame.math.Vector2(end_pos)
    displacement = target - origin
    length = displacement.length()
    # Normalize the displacement vector.
    direction = displacement.normalize()
    # Calculate the number of dashes we will have.
    dash_count = int(length // (dash_length + space_length))
    
    current_pos = pygame.math.Vector2(origin)
    for i in range(dash_count):
        # Compute the end point for the dash.
        dash_end = current_pos + direction * dash_length
        pygame.draw.line(surf, color, current_pos, dash_end, width)
        # Skip the space between dashes.
        current_pos = dash_end + direction * space_length

class Road:
    def __init__(self, x, width, lane_count=3):
        self.width = width
        self.x = x
        self.lane_count = lane_count

        self.left = x - (width // 2)
        self.right = x + (width // 2)

        infinity = 1000000
        self.top = -infinity
        self.bottom = infinity

        top_left = pygame.math.Vector2(self.left, self.top)
        top_right = pygame.math.Vector2(self.left, self.bottom)
        bottom_left = pygame.math.Vector2(self.right, self.top)
        bottom_right = pygame.math.Vector2(self.right, self.bottom)

        self.borders = [
            [top_left, top_right],
            [bottom_left, bottom_right]
        ]

        self.lanes = []
        for i in range(1, lane_count):
            xi = lerp(self.left, self.right, i / lane_count)
            self.lanes.append([pygame.math.Vector2(xi, self.top), pygame.math.Vector2(xi, self.bottom)])

    def draw(self,screen, offset_y=0):
        white = (255, 255, 255)
        border_width = 5 


        dynamic_top = self.top + offset_y
        dynamic_bottom = self.bottom + offset_y

        pygame.draw.line(screen, white, (self.left, dynamic_top), (self.left, dynamic_bottom), border_width)
        pygame.draw.line(screen, white, (self.right, dynamic_top), (self.right, dynamic_bottom), border_width)

        for p_start, p_end in self.borders:
            pygame.draw.line(screen, white,
                             (p_start.x, p_start.y + dynamic_top),
                             (p_end.x,   p_end.y   + dynamic_top), border_width)

        # draw lane dividers
        for start, end in self.lanes:
            x = start.x
            draw_dashed_line(
                screen, white,
                (x, dynamic_top),
                (x, dynamic_bottom),
                width=border_width, dash_length=20, space_length=20
            )

    def get_lane_center(self, lane_index):
        lane_width = self.width / self.lane_count
        min_x = min(lane_index,self.lane_count - 1)
        return self.left + (lane_width/2) + min_x * lane_width

def lerp(a, b, t):
    return a + (b - a) * t

# The Car class replicates the JavaScript logic
class Car:
    def __init__(self, x, y, width, height, control_type, max_speed=3.0, color=(0, 0, 255)):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.speed = 0.0
        self.acceleration = .2
        self.maxSpeed = max_speed
        self.friction = 0.05
        self.angle = 0.0
        self.damaged = False
        self.polygon = []
        self.base_color = color
        self.sensor = None
        self.brain = None

        self.useBrain = (control_type == "AI")

        if control_type != "dummy":
            self.sensor = Sensor(self, ray_count=5, ray_length=100, ray_spread=math.pi/2)
            self.brain = NeuralNetwork([self.sensor.ray_count, 6, 4])

        self.controls = Controls(control_type)

    def update(self, sensor_segments, damage_segments, traffic):
        self.controls.steer()
        if not self.damaged:
            self.move()
            self.polygon = self.get_corners()
            self.damaged = self.assess_damaged(damage_segments, traffic)
        
        if self.sensor is not None and self.useBrain and self.brain is not None:    
            self.sensor.update(sensor_segments, traffic)
        
            offsets = [
                0.0 if reading is None else 1.0 - reading["offset"] 
                for reading in self.sensor.readings]

            outputs = NeuralNetwork.feedforward(offsets, self.brain)

            self.controls.forward = bool(outputs[0])
            self.controls.left = bool(outputs[1])
            self.controls.right = bool(outputs[2])
            self.controls.reverse = bool(outputs[3])

    def assess_damaged(self, road_borders, traffic):
        for border in road_borders:
            if polys_intersect(self.polygon, border):
                return True
            
        for t in traffic:
            if t is self: 
                continue
            if polys_intersect(self.polygon, t.polygon):
                return True
        return False

    def get_corners(self):
        points = []
        rad = math.hypot(self.height, self.width) /2; 
        alpha = math.atan2(self.height, self.width)

        #front left
        points.append(pygame.math.Vector2(self.x - math.sin(self.angle - alpha) * rad, self.y - math.cos(self.angle - alpha) * rad))

        #front right
        points.append(pygame.math.Vector2(self.x - math.sin(self.angle + alpha) * rad, self.y - math.cos(self.angle + alpha) * rad))

        #back right
        points.append(pygame.math.Vector2(self.x - math.sin(math.pi + self.angle  - alpha) * rad, self.y - math.cos(math.pi + self.angle  - alpha) * rad))

        #back left
        points.append(pygame.math.Vector2(self.x - math.sin(math.pi + self.angle  + alpha) * rad, self.y - math.cos(math.pi + self.angle  + alpha) * rad))

        return points

    def move(self):
        # Adjust speed based on controls
        if self.controls.forward:
            self.speed += self.acceleration
        if self.controls.reverse:
            self.speed -= self.acceleration

        # Limit the speed
        if self.speed > self.maxSpeed:
            self.speed = self.maxSpeed
        if self.speed < -self.maxSpeed / 2:
            self.speed = -self.maxSpeed / 2

        # Apply friction
        if self.speed > 0:
            self.speed -= self.friction
        elif self.speed < 0:
            self.speed += self.friction

        # Prevent tiny speeds from causing movement
        if abs(self.speed) < self.friction:
            self.speed = 0

        # Update the angle if the car is moving
        if self.speed != 0:
            flip = 1 if self.speed > 0 else -1
            if self.controls.left:
                self.angle += 0.03 * flip
            if self.controls.right:
                self.angle -= 0.03 * flip

        # Update position (note the negative signs for consistency with JS logic)
        self.x -= math.sin(self.angle) * self.speed
        self.y -= math.cos(self.angle) * self.speed

    def draw(self, screen, offset_y=0, draw_sensor=True):
    # 1) Choose fill color based on damaged state
        color = (128, 128, 128) if self.damaged else self.base_color

    # 2) Build a list of screen‐space points from self.polygon
        pts = [(point.x, point.y + offset_y) for point in self.polygon]

    # 3) Draw the filled polygon
        pygame.draw.polygon(screen, color, pts)

    # 4) (Optional) If you want an outline, you can draw it too:
    # pygame.draw.polygon(screen, (255,255,255), pts, 2)

    # 5) Draw your sensor rays on top
        if draw_sensor and self.sensor:
            self.sensor.draw(screen, offset_y)


# Example usage in a Pygame loop
def main():

    pygame.init()
    screen_width, screen_height = 1500, 1100
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Self-driving Car Simulation")
    
    
    clock = pygame.time.Clock()

    canvas_width = 200
    canvas_height = screen_height

    canvas = pygame.Surface((canvas_width, canvas_height))

    road = Road(canvas_width // 2, canvas_width * 0.9)
    
    #car = Car(road.get_lane_center(1), canvas_height // 2, 50, 30, control_type="AI")

    def generate_traffic(road, start_y):
        return [   
            Car(road.get_lane_center(1),  start_y - 100, 50, 30, control_type="dummy", max_speed = 2.0, color =(255, 0, 0)), 
            Car(road.get_lane_center(0),  start_y - 300, 50, 30, control_type="dummy", max_speed = 2.0, color =(255, 0, 0)),
            Car(road.get_lane_center(2),  start_y - 300, 50, 30, control_type="dummy", max_speed = 2.0, color =(255, 0, 0)),
            Car(road.get_lane_center(0),  start_y - 500, 50, 30, control_type="dummy", max_speed = 2.0, color =(255, 0, 0)),
            Car(road.get_lane_center(1),  start_y - 500, 50, 30, control_type="dummy", max_speed = 2.0, color =(255, 0, 0)),
            Car(road.get_lane_center(1),  start_y  - 700, 50, 30, control_type="dummy", max_speed = 2.0, color =(255, 0, 0)),
            Car(road.get_lane_center(2),  start_y - 700, 50, 30, control_type="dummy", max_speed = 2.0, color =(255, 0, 0)),
]
    
    def create_cars(N):
        cars = []
        for i in range(N):
            cars.append(Car(road.get_lane_center(1), start_y, 50, 30, control_type="AI", max_speed=6.0, color=(0, 0, 255)))
        return cars

    start_y = canvas_height - 100  
    N = 1
    
    cars = create_cars(N)
    best_car = cars[0]

    best_brain = load_best_brain()
    if best_brain is not None:
        for i, car in enumerate(cars):
            brain_data = copy.deepcopy(best_brain)
            car.brain = NeuralNetwork.from_dict(brain_data)
            if i != 0:
                NeuralNetwork.mutate(car.brain, mutation_rate=0.1)

    traffic = generate_traffic(road, start_y)

    running = True
    while running:
        best_car = min(cars, key=lambda c: c.y)

        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:   # “S” to save
                    save_best_brain(best_car.brain)
                elif event.key == pygame.K_d: # “D” to discard
                    if os.path.exists(BRAIN_FILE):
                        os.remove(BRAIN_FILE)

        all_sensor_segments = road.borders + road.lanes
        damaged_segments = road.borders

        traffic_list = traffic
        
        #car.update(all_sensor_segments, damaged_segments, traffic_list)

        for t in traffic_list:
            t.update(road.borders, damaged_segments, traffic_list)
            
        for ai in cars:
            ai.update(road.borders, damaged_segments, traffic_list)
        
        offset_y = -best_car.y + canvas_height * .5

        # Draw everything
        screen.fill((169, 169, 169))  # light gray background, similar to your CSS
        canvas.fill((211, 211, 211))  # white canvas

        road.draw(canvas, offset_y)
    
        #car.draw(canvas, offset_y)

        for t in traffic_list:
            t.draw(canvas, offset_y)

        for ai in cars:
            ai.draw(canvas, offset_y, draw_sensor=False)

        best_car.draw(canvas, offset_y, draw_sensor=True)

        screen.blit(canvas, ((screen_width - canvas_width) // 2, 0))

        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()