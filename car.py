import math
import pygame

# A simple controls class to store key states
class Controls:
    def __init__(self):
        self.forward = False
        self.reverse = False
        self.left = False
        self.right = False

# The Car class replicates the JavaScript logic
class Car:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.speed = 0.0
        self.acceleration = 0.2
        self.maxSpeed = 3.0
        self.friction = 0.05
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

    def draw(self, screen):
        # Create a surface for the car
        car_surface = pygame.Surface((self.height, self.width), pygame.SRCALPHA)
        car_surface.fill((0, 0, 0))  # fill with red color
        
        # Rotate the surface according to the car's angle (converted to degrees)
        rotated_surface = pygame.transform.rotate(car_surface, math.degrees(self.angle))
        
        # Center the rotated surface at the car's current position
        rect = rotated_surface.get_rect(center=(self.x, self.y))
        screen.blit(rotated_surface, rect.topleft)

    def draw(self, screen):
        # Draw the road as a rectangle
        pygame.draw.rect(screen, (50, 50, 50), (0, 0, self.width, self.height))

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
    def draw(self,screen):
        screen.lineWidth = 5
        screen.strokeStyle = "white"

        screen.beginPath()
        screen.moveTo(self.left, self.top)
        screen.lineTo(self.left, self.bottom)
        screen.stroke()

        screen.beginPath()
        screen.moveTo(self.right, self.top)
        screen.lineTo(self.right, self.bottom)
        screen.stroke()

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

    car = Car(canvas_width // 2, canvas_height // 2, 50, 30)
    road = Road(canvas_width // 2, canvas_width)
    
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
        
        road.draw(canvas)
        car.draw(canvas)
        

        screen.blit(canvas, ((screen_width - canvas_width) // 2, 0))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()
