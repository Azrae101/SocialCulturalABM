import pygame
import random

class BaseAgent(pygame.sprite.Sprite):
    def handle_collision(self, other):
        """Default collision handling for all agents"""
        self.direction_vector = self.direction_vector.reflect(
            pygame.math.Vector2(random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2))
        ).normalize()
        self.update_direction_facing()

class Susceptible(pygame.sprite.Sprite):
    
    def __init__(self, group, all_sprites):
        super().__init__()
        self.all_sprites = all_sprites 
        self.emotional_valence = random.uniform(0, 1)  # Add this with other properties
        self.in_social = False  # <-- Add this line

        # In susceptible.py, add to __init__:
        self.emotional_valence = random.uniform(0, 1)  # Add this with other properties

        def tint_surface(surface, color):
            """Apply color tint to a surface while preserving transparency"""
            tint = pygame.Surface(surface.get_size())
            tint.fill(color)
            surface = surface.copy()
            surface.blit(tint, (0, 0), special_flags=pygame.BLEND_MULT)
            return surface

        self.color = (106, 168, 79)
        
        # Animation scale factors - uniform size for all directions
        self.sprite_scale = (40, 70)  # Same size as other agents
        
        # Load and scale animation frames for all directions
        self.image_list_down = [
            tint_surface(pygame.transform.scale(
                pygame.image.load(f'Images/running_down_{i}.png').convert_alpha(),
                self.sprite_scale
            ), self.color) for i in range(1, 4)
        ]
        self.image_list_up = [
            tint_surface(pygame.transform.scale(
                pygame.image.load(f'Images/running_up_{i}.png').convert_alpha(),
                self.sprite_scale
            ), self.color) for i in range(1, 4)
        ]
        self.image_list_left = [
            tint_surface(pygame.transform.scale(
                pygame.image.load(f'Images/running_left_{i}.png').convert_alpha(),
                self.sprite_scale
            ), self.color) for i in range(1, 4)
        ]
        self.image_list_right = [
            tint_surface(pygame.transform.scale(
                pygame.image.load(f'Images/running_right_{i}.png').convert_alpha(),
                self.sprite_scale
            ), self.color) for i in range(1, 4 )
        ]
        
        # Set initial image and rect
        self.current_direction = "right"
        self.animation_index = 0
        self.image = self.image_list_right[self.animation_index]
        self.rect = self.image.get_rect(center=(random.randint(50, 900), random.randint(50, 550)))
        
        # Movement properties
        self.speed = random.randint(2, 4)
        self.direction_vector = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1])).normalize()
        self.animation_counter = 0
        self.animation_speed = 5 # Faster animation to appear more "nervous"
        
        # Susceptibility properties
        self.skepticism = random.uniform(0.2, 0.8)  # Individual skepticism level
        self.last_direction_change = 0
        
    def update(self):
        self.handle_movement()
        self.animate()
        self.handle_boundaries()
        self.check_collisions()  # New collision check

    def check_collisions(self):
        collisions = pygame.sprite.spritecollide(
            self, 
            self.all_sprites, 
            False,
            collided=pygame.sprite.collide_rect_ratio(0.8)  # Add collision threshold
        )
        for other in collisions:
            if other != self:
                self.handle_collision(other)  # Match renamed method
                break

    def handle_collision(self, other):
        # Defensive: avoid zero-length normal or direction_vector
        normal = pygame.math.Vector2(self.rect.centerx - other.rect.centerx, self.rect.centery - other.rect.centery)
        if normal.length_squared() == 0:
            # Assign a random normal if overlap is perfect
            normal = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1]))
        if self.direction_vector.length_squared() == 0:
            self.direction_vector = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1])).normalize()
        self.direction_vector = self.direction_vector.reflect(normal).normalize()
        self.update_direction_facing()
    
    def handle_movement(self):
        # Move first
        self.rect.centerx += self.direction_vector.x * self.speed
        self.rect.centery += self.direction_vector.y * self.speed
        
        # Susceptible agents change direction more frequently (appear more erratic)
        if random.random() < 0.03 + (0.02 * (1 - self.skepticism)):  # More skeptical = slightly less direction changes
            self.change_direction()
    
    def animate(self):
        self.animation_counter += 1
        if self.animation_counter >= self.animation_speed:
            self.animation_counter = 0
            self.animation_index = (self.animation_index + 1) % 3
            self.update_image()
    
    def update_image(self):
        # Select the correct image based on direction
        if self.current_direction == "down":
            self.image = self.image_list_down[self.animation_index]
        elif self.current_direction == "up":
            self.image = self.image_list_up[self.animation_index]
        elif self.current_direction == "left":
            self.image = self.image_list_left[self.animation_index]
        else:  # right
            self.image = self.image_list_right[self.animation_index]
        
        # Update the rect to match the new image while maintaining position
        old_center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = old_center
    
    def handle_boundaries(self):
        if self.rect.left < 0 or self.rect.right > 920:
            self.direction_vector.x *= -1
            self.update_direction_facing()
        if self.rect.top < 0 or self.rect.bottom > 575:
            self.direction_vector.y *= -1
            self.update_direction_facing()
    
    def change_direction(self):
        # Susceptible agents make more dramatic direction changes
        self.direction_vector = pygame.math.Vector2(
            random.uniform(-1, 1), 
            random.uniform(-1, 1)
        ).normalize()
        self.update_direction_facing()
    
    def update_direction_facing(self):
        if abs(self.direction_vector.x) > abs(self.direction_vector.y):
            self.current_direction = "left" if self.direction_vector.x < 0 else "right"
        else:
            self.current_direction = "up" if self.direction_vector.y < 0 else "down"