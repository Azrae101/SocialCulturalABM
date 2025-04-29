import pygame
import random

class Believer(pygame.sprite.Sprite):
    def __init__(self, group, all_sprites):
        super().__init__()
        self.images = [
            pygame.image.load('Images/running_right_1.png'),
            pygame.image.load('Images/running_right_2.png'),
            pygame.image.load('Images/running_right_3.png')
        ]
        self.image_index = 0
        self.image = pygame.transform.scale(self.images[self.image_index], (30, 30))
        self.rect = self.image.get_rect(center=(random.randint(50, 900), random.randint(50, 550)))
        self.speed = random.randint(1, 3)
        self.direction = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1])).normalize()
        self.animation_counter = 0
        self.influence = random.uniform(0.5, 2.0)

    def update(self):
        self.animation_counter += 1
        if self.animation_counter % 10 == 0:
            self.image_index = (self.image_index + 1) % len(self.images)
            self.image = pygame.transform.scale(self.images[self.image_index], (30, 30))
        self.rect.centerx += self.direction.x * self.speed
        self.rect.centery += self.direction.y * self.speed
        if self.rect.left < 0 or self.rect.right > 920:
            self.direction.x *= -1
        if self.rect.top < 0 or self.rect.bottom > 575:
            self.direction.y *= -1
