import pygame
import random
import numpy as np

class Agent(pygame.sprite.Sprite):
    STATES = {
        "Susceptible": (0, 0, 255),      # Blue
        "Exposed": (255, 255, 0),        # Yellow
        "Believer": (255, 0, 0),         # Red
        "Doubter": (0, 255, 0),          # Green
        "Recovered": (128, 128, 128)     # Gray
    }
    
    def __init__(self, group, all_sprites):
        super().__init__()
        self.state = "Susceptible"
        self.image = pygame.Surface((20, 20))
        self.image.fill(self.STATES[self.state])
        self.rect = self.image.get_rect(center=(random.randint(50, 1100), random.randint(50, 600)))
        self.speed = random.randint(1, 3)
        self.direction = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1])).normalize()
        self.influence = random.uniform(0.5, 2.0)  # Social influence multiplier [4][7]
        self.skepticism = random.uniform(0.1, 0.9) # Cognitive resistance [4][9]
        self.exposure_time = 0

        # Model parameters from epidemiological studies [4][7][9]
        self.α = 0.3  # Base transmission rate
        self.β1 = 0.2 # Doubt development rate
        self.β2 = 0.5 # Belief adoption rate
        self.γ = 0.1  # Doubter-to-believer rate
        self.μ = 0.1  # Recovery rate

    def update(self):
        # Movement mechanics
        self.rect.centerx += self.direction.x * self.speed
        self.rect.centery += self.direction.y * self.speed
        
        # Bounce off walls
        if self.rect.left < 0 or self.rect.right > 1140:
            self.direction.x *= -1
        if self.rect.top < 0 or self.rect.bottom > 680:
            self.direction.y *= -1

        # State transitions
        if self.state == "Exposed":
            self.exposure_time += 1
            # Cognitive processing window [4][9]
            if self.exposure_time > 60:  # ~1 second at 60 FPS
                if random.random() < self.β1 * self.skepticism:
                    self.change_state("Doubter")
                elif random.random() < self.β2 * (1 - self.skepticism):
                    self.change_state("Believer")
                    
        elif self.state == "Believer":
            # Natural recovery process [7]
            if random.random() < self.μ:
                self.change_state("Recovered")

        elif self.state == "Doubter":
            # Possible belief adoption or recovery [4]
            if random.random() < self.γ:
                self.change_state("Believer")
            elif random.random() < self.μ:
                self.change_state("Recovered")

    def change_state(self, new_state):
        self.state = new_state
        self.image.fill(self.STATES[self.state])
