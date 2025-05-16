import pygame
import random

class BaseAgent(pygame.sprite.Sprite):
    def handle_collision(self, other):
        """Default collision handling for all agents"""
        self.direction_vector = self.direction_vector.reflect(
            pygame.math.Vector2(random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2))
        ).normalize()
        self.update_direction_facing()

class Believer(pygame.sprite.Sprite):
    
    def __init__(self, group, all_sprites):
        super().__init__()
        self.all_sprites = all_sprites      
        self.emotional_valence = random.uniform(0, 1)  # Add this with other properties   
        self.in_social = False  # <-- Add this line
        
        def tint_surface(surface, color):
            """Apply color tint to a surface while preserving transparency"""
            tint = pygame.Surface(surface.get_size())
            tint.fill(color)
            surface = surface.copy()
            surface.blit(tint, (0, 0), special_flags=pygame.BLEND_MULT)
            return surface

        self.color = (204, 0, 0)
        
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
        self.speed = random.randint(8, 14)
        self.direction_vector = pygame.math.Vector2(random.choice([-1, 1]), random.choice([-1, 1])).normalize()
        self.animation_counter = 0
        self.animation_speed = 8
        
        # Agent properties
        self.influence = random.uniform(0.5, 2.0)
        self.current_zone = None
        self.boundary_padding = 15  # Padding from zone edges
        self.stuck_counter = 0  # To detect if agent is stuck
        self.max_stuck_frames = 10  # Max frames before forcing direction change
    
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
        normal = pygame.math.Vector2(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5))
        if normal.length() < 1e-6:  # Use a small threshold instead of == 0
            normal = pygame.math.Vector2(1, 0)
        self.direction_vector = self.direction_vector.reflect(normal).normalize()
        self.update_direction_facing()
    
    def update(self, zones=None):
        self.handle_movement()
        self.animate()
        
        if zones:
            self.handle_zone_boundaries(zones)
            self.check_if_stuck()
    
    def handle_movement(self):
        # Move first
        self.rect.centerx += self.direction_vector.x * self.speed
        self.rect.centery += self.direction_vector.y * self.speed
        
        # Random direction changes
        if random.random() < 0.01:
            self.change_direction()

    def handle_zone_boundaries(self, zones):
        # Determine current zone
        self.current_zone = None
        for zone_name, zone_rect in zones.items():
            if zone_rect.collidepoint(self.rect.center):
                self.current_zone = zone_rect
                break
        
        if not self.current_zone:
            return

        # Calculate effective boundaries with padding
        left_bound = self.current_zone.left + self.boundary_padding
        right_bound = self.current_zone.right - self.boundary_padding
        top_bound = self.current_zone.top + self.boundary_padding
        bottom_bound = self.current_zone.bottom - self.boundary_padding

        # Check each boundary and handle collisions
        bounced = False
        
        # Left/Right boundaries
        if self.rect.left < left_bound:
            self.rect.left = left_bound
            self.direction_vector.x = abs(self.direction_vector.x)  # Force rightward
            bounced = True
        elif self.rect.right > right_bound:
            self.rect.right = right_bound
            self.direction_vector.x = -abs(self.direction_vector.x)  # Force leftward
            bounced = True
            
        # Top/Bottom boundaries
        if self.rect.top < top_bound:
            self.rect.top = top_bound
            self.direction_vector.y = abs(self.direction_vector.y)  # Force downward
            bounced = True
        elif self.rect.bottom > bottom_bound:
            self.rect.bottom = bottom_bound
            self.direction_vector.y = -abs(self.direction_vector.y)  # Force upward
            bounced = True
        
        # If we bounced, normalize the vector and update facing direction
        if bounced:
            self.direction_vector = self.direction_vector.normalize()
            self.update_direction_facing()
            self.stuck_counter = 0  # Reset stuck counter on bounce
    
    def check_if_stuck(self):
        # Increment stuck counter if velocity is very low
        if abs(self.direction_vector.x) < 0.1 and abs(self.direction_vector.y) < 0.1:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
        
        # Force a direction change if stuck for too long
        if self.stuck_counter > self.max_stuck_frames:
            self.change_direction()
            self.stuck_counter = 0
    
    def change_direction(self):
        # Generate a new direction that points away from edges
        if self.current_zone:
            # Get center of current zone
            zone_center = pygame.math.Vector2(self.current_zone.center)
            
            # Calculate vector from agent to center
            to_center = zone_center - pygame.math.Vector2(self.rect.center)
            
            # If we're very close to center, use random direction
            if to_center.length() < 20:
                new_direction = pygame.math.Vector2(
                    random.uniform(-1, 1),
                    random.uniform(-1, 1))
            else:
                # Bias the new direction towards the center
                bias_strength = 0.3  # How strongly to bias towards center
                random_component = pygame.math.Vector2(
                    random.uniform(-1, 1),
                    random.uniform(-1, 1))
                
                new_direction = (to_center.normalize() * bias_strength + 
                            random_component)
        else:
            # Fallback to completely random direction
            new_direction = pygame.math.Vector2(
                random.uniform(-1, 1),
                random.uniform(-1, 1))
        
        # Ensure we don't get a zero vector
        if new_direction.length() == 0:
            new_direction = pygame.math.Vector2(1, 0)  # Default to right
        
        self.direction_vector = new_direction.normalize()
        self.update_direction_facing()
    
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
    
    def handle_zone_boundaries(self, zones):
        # Determine current zone
        self.current_zone = None
        for zone_name, zone_rect in zones.items():
            if zone_rect.collidepoint(self.rect.center):
                self.current_zone = zone_rect
                break
        
        if self.current_zone:
            # Check and correct boundaries with padding
            if self.rect.left < self.current_zone.left + self.boundary_padding:
                self.rect.left = self.current_zone.left + self.boundary_padding
                self.direction_vector.x *= -1
                self.update_direction_facing()
            elif self.rect.right > self.current_zone.right - self.boundary_padding:
                self.rect.right = self.current_zone.right - self.boundary_padding
                self.direction_vector.x *= -1
                self.update_direction_facing()
            
            if self.rect.top < self.current_zone.top + self.boundary_padding:
                self.rect.top = self.current_zone.top + self.boundary_padding
                self.direction_vector.y *= -1
                self.update_direction_facing()
            elif self.rect.bottom > self.current_zone.bottom - self.boundary_padding:
                self.rect.bottom = self.current_zone.bottom - self.boundary_padding
                self.direction_vector.y *= -1
                self.update_direction_facing()
    
    def change_direction(self):
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