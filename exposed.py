import pygame
import random

class Exposed(pygame.sprite.Sprite):
    
    def __init__(self, group, all_sprites):
        super().__init__()
        
        def tint_surface(surface, color):
            """Apply color tint to a surface while preserving transparency"""
            tint = pygame.Surface(surface.get_size())
            tint.fill(color)
            surface = surface.copy()
            surface.blit(tint, (0, 0), special_flags=pygame.BLEND_MULT)
            return surface

        self.color = (255, 255, 0)

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
            ), self.color) for i in range(1, 4)
        ]
        
        # Set initial image and rect
        self.current_direction = "right"
        self.animation_index = 0
        self.image = self.image_list_right[self.animation_index]
        self.rect = self.image.get_rect(center=(random.randint(50, 900), random.randint(50, 550)))
        
        # Movement properties
        self.speed = random.randint(1, 3)  # Moderate speed
        self.direction_vector = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1])).normalize()
        self.animation_counter = 0
        self.animation_speed = 8  # Slightly slower animation to appear "conflicted"
        
        # Exposure properties
        self.skepticism = random.uniform(0.2, 0.8)
        self.exposure_time = 0
        self.conflict_level = 0  # Visual indicator of internal conflict
        
        # Visual effect properties
        self.flash_counter = 0
        self.original_images = {
            "down": self.image_list_down.copy(),
            "up": self.image_list_up.copy(),
            "left": self.image_list_left.copy(),
            "right": self.image_list_right.copy()
        }
        
    def update(self):
        # First update exposure time and visual effects
        self.update_exposure()
        
        # Then handle movement
        self.handle_movement()
        
        # Then update animation
        self.animate()
        
        # Finally handle boundaries
        self.handle_boundaries()
        
        # Increment exposure time
        self.exposure_time += 1
    
    def update_exposure(self):
        # Increase conflict level over time
        self.conflict_level = min(1.0, self.exposure_time / 90)  # 0-1 scale over 90 frames
        
        # Visual effect - occasional flashing when conflicted
        self.flash_counter += 1
        if self.conflict_level > 0.5 and self.flash_counter % 10 == 0:
            # Flash yellow while maintaining base color
            flash_color = (255, 255, 0)  # Yellow
            blend_color = (
                min(255, self.color[0] + flash_color[0]),
                min(255, self.color[1] + flash_color[1]),
                min(255, self.color[2] + flash_color[2])
            )
            
            for direction, frames in self.original_images.items():
                for i in range(3):
                    surf = frames[i].copy()
                    surf.fill(blend_color, special_flags=pygame.BLEND_MULT)
                    getattr(self, f'image_list_{direction}')[i] = surf
        elif self.flash_counter % 15 == 0:
            # Reset to original images
            self.image_list_down = self.original_images["down"].copy()
            self.image_list_up = self.original_images["up"].copy()
            self.image_list_left = self.original_images["left"].copy()
            self.image_list_right = self.original_images["right"].copy()
    
    def handle_movement(self):
        # Move first
        self.rect.centerx += self.direction_vector.x * self.speed
        self.rect.centery += self.direction_vector.y * self.speed
        
        # More conflicted agents change direction more frequently
        if random.random() < 0.02 + (0.03 * self.conflict_level):
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
        # More conflicted agents make more erratic direction changes
        if self.conflict_level > 0.7:
            self.direction_vector = pygame.math.Vector2(
                random.uniform(-1, 1), 
                random.uniform(-1, 1)
            ).normalize()
        else:
            self.direction_vector = pygame.math.Vector2(
                random.uniform(-0.7, 0.7), 
                random.uniform(-0.7, 0.7)
            ).normalize()
        self.update_direction_facing()
    
    def update_direction_facing(self):
        if abs(self.direction_vector.x) > abs(self.direction_vector.y):
            self.current_direction = "left" if self.direction_vector.x < 0 else "right"
        else:
            self.current_direction = "up" if self.direction_vector.y < 0 else "down"