import pygame
import random

class Misinformant(pygame.sprite.Sprite):
    def __init__(self, group, all_sprites):
        super().__init__()
        # Load base image (you can pick any running image from Images/)
        self.original_image = pygame.image.load('Images/running_right_1.png').convert_alpha()
        self.image = pygame.transform.scale(self.original_image, (30, 30))
        self.rect = self.image.get_rect(center=(random.randint(50, 900), random.randint(50, 550)))
        self.speed = random.randint(2, 4)  # Possibly faster to represent active spreading
        self.direction = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1])).normalize()
        self.animation_counter = 0
        
        # Misinformation spreading strength: higher than normal believers
        self.influence = random.uniform(1.5, 3.0)
        
    def update(self):
        # Move
        self.rect.centerx += self.direction.x * self.speed
        self.rect.centery += self.direction.y * self.speed
        
        # Bounce off edges
        if self.rect.left < 0 or self.rect.right > 920:
            self.direction.x *= -1
        if self.rect.top < 0 or self.rect.bottom > 575:
            self.direction.y *= -1
