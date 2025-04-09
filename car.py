import math
import pygame

# A simple controls class to store key states
class Controls:
    def __init__(self):
        self.forward = False
        self.reverse = False
        self.left = False
        self.right = False

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
        top_right = pygame.math.Vector2(self.right, self.top)
        bottom_left = pygame.math.Vector2(self.left, self.bottom)
        bottom_right = pygame.math.Vector2(self.right, self.bottom)

        self.borders = [
            [top_left, top_right],
            [bottom_left, bottom_right]
        ]

    def draw(self,screen, offset_y=0):
        white = (255, 255, 255)
        border_width = 5 

        dynamic_top = self.top + offset_y
        dynamic_bottom = self.bottom + offset_y

        pygame.draw.line(screen, white, (self.left, dynamic_top), (self.left, dynamic_bottom), border_width)
        pygame.draw.line(screen, white, (self.right, dynamic_top), (self.right, dynamic_bottom), border_width)

        for i in range(1, self.lane_count):
            x = lerp(self.left, 
                     self.right, 
                     i / self.lane_count
                     )
            draw_dashed_line(screen, white, (x, dynamic_top), (x, dynamic_bottom), width=border_width, dash_length=20, space_length=20)
            self.borders.append([pygame.math.Vector2(x, dynamic_top), pygame.math.Vector2(x, dynamic_bottom)])


    def get_lane_center(self, lane_index):
        lane_width = self.width / self.lane_count
        min_x = min(lane_index,self.lane_count - 1)
        return self.left + (lane_width/2) + min_x * lane_width

def lerp(a, b, t):
    return a + (b - a) * t

# The Car class replicates the JavaScript logic
class Car:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.speed = 0.0
        self.acceleration = .6
        self.maxSpeed = 5.0
        self.friction = 0.2
        self.angle = 0.0

        self.controls = Controls()

    def update(self):
        self.move()

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

    def draw(self, screen, offset_y=0):
        # Create a surface for the car
        car_surface = pygame.Surface((self.height, self.width), pygame.SRCALPHA)
        car_surface.fill((0, 0, 0))  # fill with red color
        
        # Rotate the surface according to the car's angle (converted to degrees)
        rotated_surface = pygame.transform.rotate(car_surface, math.degrees(self.angle))
        
        # Center the rotated surface at the car's current position
        rect = rotated_surface.get_rect(center=(self.x, self.y + offset_y))
        screen.blit(rotated_surface, rect.topleft)

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
    car = Car(road.get_lane_center(1), canvas_height // 2, 50, 30)

    
    running = True
    while running:
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update control states based on key presses
        keys = pygame.key.get_pressed()
        car.controls.forward = keys[pygame.K_UP]
        car.controls.reverse = keys[pygame.K_DOWN]
        car.controls.left = keys[pygame.K_LEFT]
        car.controls.right = keys[pygame.K_RIGHT]
        
        # Update car physics
        car.update()

        # Draw everything
        screen.fill((169, 169, 169))  # light gray background, similar to your CSS
        canvas.fill((211, 211, 211))  # white canvas

        offset_y = -car.y + canvas_height *.6

        road.draw(canvas, offset_y)
        car.draw(canvas, offset_y)


        screen.blit(canvas, ((screen_width - canvas_width) // 2, 0))

        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()
