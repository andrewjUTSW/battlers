import numpy as np
from OpenGL.GL import *
from pygame.math import Vector3
import pygame

class Character:
    def __init__(self, name, position=(0, 0, 0), color=(1, 1, 1), strength=100, pistols=0, is_ai=False):
        self.name = name
        self.position = list(position)  # Changed to list for mutability
        self.color = color
        self.strength = strength
        self.pistols = pistols
        self.projectiles = []
        
        # Jumping properties
        self.velocity = Vector3(0, 0, 0)
        self.is_jumping = False
        self.jump_speed = 0.3
        self.gravity = 0.015
        self.jumps_left = 2  # Track available jumps
        self.max_jumps = 2   # Maximum number of jumps
        
        # Explosion properties
        self.is_exploding = False
        self.explosion_time = 0
        self.explosion_duration = 60
        self.explosion_particles = []

        self.is_ai = is_ai
        self.ai_state = 'idle'
        self.ai_timer = 0
        self.ai_move_direction = 1
        self.move_speed = 0.1
        self.attack_cooldown = 0
        self.attack_cooldown_max = 60  # frames (1 second at 60 FPS)

        # Combat properties
        self.is_punching = False
        self.is_kicking = False
        self.punch_frame = 0
        self.kick_frame = 0
        self.melee_cooldown = 0
        self.melee_damage = 15
        self.shoot_cooldown = 0
        self.shoot_cooldown_max = 20  # Frames between shots

        # Fire breath properties
        self.is_breathing_fire = False
        self.fire_breath_duration = 0
        self.fire_breath_max = 30  # Half second at 60 FPS
        self.fire_breath_particles = []
        self.fire_breath_damage = 1  # Damage per frame
        self.fire_breath_cooldown = 0
        self.fire_breath_cooldown_max = 120  # 2 second cooldown

    def start_explosion(self):
        self.is_exploding = True
        self.explosion_time = 0
        # Create explosion particles
        for _ in range(20):  # 20 particles
            angle = np.random.uniform(0, 2 * np.pi)
            speed = np.random.uniform(0.05, 0.15)
            self.explosion_particles.append({
                'position': list(self.position),
                'velocity': [np.cos(angle) * speed, np.sin(angle) * speed, 0],
                'color': [1.0, np.random.uniform(0.0, 0.5), 0.0],  # Random orange-red
                'size': np.random.uniform(0.1, 0.3)
            })

    def update_explosion(self):
        if not self.is_exploding:
            return

        self.explosion_time += 1
        if self.explosion_time >= self.explosion_duration:
            self.is_exploding = False
            return

        # Update particle positions
        for particle in self.explosion_particles:
            for i in range(3):
                particle['position'][i] += particle['velocity'][i]
            # Add gravity effect
            particle['velocity'][1] -= 0.01
            # Fade out
            particle['size'] *= 0.95

    def update(self):
        if self.is_exploding:
            self.update_explosion()
            return

        # Update combat cooldowns
        if self.melee_cooldown > 0:
            self.melee_cooldown -= 1
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        # Update punch animation
        if self.is_punching:
            self.punch_frame += 1
            if self.punch_frame >= 10:
                self.is_punching = False
                self.punch_frame = 0

        # Update kick animation
        if self.is_kicking:
            self.kick_frame += 1
            if self.kick_frame >= 10:
                self.is_kicking = False
                self.kick_frame = 0

        # Apply gravity and update vertical position
        self.velocity.y -= self.gravity
        self.position[1] = max(self.position[1] + self.velocity.y, 0)
        
        # Check if landed
        if self.position[1] == 0 and self.velocity.y <= 0:
            self.velocity.y = 0
            self.is_jumping = False
            self.jumps_left = self.max_jumps  # Reset jumps when landing

        # Update AI behavior if this is an AI character
        if self.is_ai:
            self.update_ai()

        # Update attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        # Update fire breath
        if self.fire_breath_cooldown > 0:
            self.fire_breath_cooldown -= 1
            
        if self.is_breathing_fire:
            self.fire_breath_duration += 1
            if self.fire_breath_duration >= self.fire_breath_max:
                self.is_breathing_fire = False
                self.fire_breath_duration = 0
                self.fire_breath_cooldown = self.fire_breath_cooldown_max
            
            # Update fire particles
            self.update_fire_breath()

    def update_ai(self):
        self.ai_timer += 1

        # Get more aggressive when player is in range
        target_distance = abs(self.position[0] - (-3))  # Distance to player (at -3)
        
        # Change state more frequently when player is closer
        state_change_interval = 60 if target_distance < 5 else 120  # Every 1 or 2 seconds
        if self.ai_timer % state_change_interval == 0:
            self.choose_ai_state(target_distance)

        # Execute current state
        if self.ai_state == 'move':
            # Move towards player with some randomness
            target_x = -3  # Player position
            direction = -1 if self.position[0] > target_x else 1
            
            # Add some tactical movement
            if target_distance < 3:  # If too close, sometimes back away
                if np.random.random() < 0.3:
                    direction *= -1
            
            new_pos = self.position[0] + (self.move_speed * direction)
            if abs(new_pos) < 8:  # Stay within bounds
                self.position[0] = new_pos

        elif self.ai_state == 'attack':
            # Attack more frequently when closer to player
            attack_chance = 0.2 if target_distance < 5 else 0.1
            if self.attack_cooldown <= 0 and np.random.random() < attack_chance:
                self.shoot()
                self.attack_cooldown = self.attack_cooldown_max // 2  # Faster cooldown

        elif self.ai_state == 'dodge':
            # Jump to dodge incoming projectiles
            if not self.is_jumping:
                self.jump()
                # Move sideways while jumping
                direction = 1 if np.random.random() < 0.5 else -1
                new_pos = self.position[0] + (self.move_speed * direction)
                if abs(new_pos) < 8:
                    self.position[0] = new_pos

    def choose_ai_state(self, target_distance):
        # Adjust probabilities based on distance to player
        if target_distance < 4:  # Close range
            if np.random.random() < 0.6:  # 60% chance to attack when close
                self.ai_state = 'attack'
            elif np.random.random() < 0.3:  # 30% chance to dodge
                self.ai_state = 'dodge'
            else:  # 10% chance to move
                self.ai_state = 'move'
        else:  # Long range
            if np.random.random() < 0.5:  # 50% chance to move closer
                self.ai_state = 'move'
            elif np.random.random() < 0.4:  # 40% chance to attack
                self.ai_state = 'attack'
            else:  # 10% chance to dodge
                self.ai_state = 'dodge'

    def jump(self):
        # Allow jump if we have jumps left
        if self.jumps_left > 0:
            self.velocity.y = self.jump_speed
            if self.jumps_left == 1:  # Second jump
                self.velocity.y *= 0.8  # Slightly lower second jump
            self.is_jumping = True
            self.jumps_left -= 1
            return True
        return False

    def shoot(self):
        if self.shoot_cooldown <= 0 and self.pistols > 0:
            direction = (1.0 if self.position[0] < 0 else -1.0, 0, 0)
            start_pos = (
                self.position[0] + direction[0],  # Start slightly in front
                self.position[1] + 0.5,           # Shoot from chest height
                self.position[2]
            )
            projectile = Projectile(
                position=start_pos,
                direction=direction,
                speed=0.1  # Consistent speed
            )
            self.projectiles.append(projectile)
            self.shoot_cooldown = self.shoot_cooldown_max
            return True
        return False

    def draw(self):
        if self.is_exploding:
            self.draw_explosion()
            return
            
        glPushMatrix()
        glTranslatef(*self.position)
        glColor3f(*self.color)
        
        # Draw body
        self.draw_torso()
        
        # Draw head with face and horns
        self.draw_head()
        
        # Draw limbs
        self.draw_arms()
        self.draw_legs()
        
        # Draw fire breath if active
        if self.is_breathing_fire:
            self.draw_fire_breath()
        
        glPopMatrix()

    def draw_head(self):
        glPushMatrix()
        glTranslatef(0, 1.2, 0)
        
        # Skull base (blend with character color)
        skull_color = [0.8 + c * 0.2 for c in self.color]  # Blend white with character color
        glColor3f(*skull_color)
        self.draw_cube(0, 0, 0, 0.45)
        
        # Skull features
        glColor3f(0.1, 0.1, 0.1)  # Darker black for depth
        
        # Deep eye sockets (more realistic)
        glBegin(GL_QUADS)
        # Left eye socket
        glVertex3f(-0.15, 0.1, 0.23)
        glVertex3f(-0.05, 0.1, 0.23)
        glVertex3f(-0.05, -0.05, 0.23)
        glVertex3f(-0.15, -0.05, 0.23)
        # Add depth to left socket
        glColor3f(0, 0, 0)  # Pure black for depth
        glVertex3f(-0.14, 0.09, 0.231)
        glVertex3f(-0.06, 0.09, 0.231)
        glVertex3f(-0.06, -0.04, 0.231)
        glVertex3f(-0.14, -0.04, 0.231)
        
        # Right eye socket
        glColor3f(0.1, 0.1, 0.1)
        glVertex3f(0.15, 0.1, 0.23)
        glVertex3f(0.05, 0.1, 0.23)
        glVertex3f(0.05, -0.05, 0.23)
        glVertex3f(0.15, -0.05, 0.23)
        # Add depth to right socket
        glColor3f(0, 0, 0)
        glVertex3f(0.14, 0.09, 0.231)
        glVertex3f(0.06, 0.09, 0.231)
        glVertex3f(0.06, -0.04, 0.231)
        glVertex3f(0.14, -0.04, 0.231)
        glEnd()
        
        # Nasal cavity (more detailed)
        glBegin(GL_TRIANGLES)
        glVertex3f(-0.03, -0.1, 0.23)
        glVertex3f(0.03, -0.1, 0.23)
        glVertex3f(0, -0.15, 0.23)
        # Nasal bridge
        glVertex3f(-0.02, -0.05, 0.23)
        glVertex3f(0.02, -0.05, 0.23)
        glVertex3f(0, -0.1, 0.23)
        glEnd()
        
        # Animated jaw
        time = pygame.time.get_ticks() / 1000.0
        jaw_angle = 20 * np.sin(time * 2)  # Oscillating jaw movement
        
        glPushMatrix()
        glTranslatef(0, -0.2, 0)  # Move to jaw pivot point
        glRotatef(jaw_angle, 1, 0, 0)  # Rotate around x-axis
        
        # Lower jaw bone
        glColor3f(0.9, 0.9, 0.9)  # Slightly darker than skull
        glBegin(GL_QUADS)
        # Front of jaw
        glVertex3f(-0.2, 0, 0.23)
        glVertex3f(0.2, 0, 0.23)
        glVertex3f(0.2, -0.15, 0.23)
        glVertex3f(-0.2, -0.15, 0.23)
        # Bottom of jaw
        glVertex3f(-0.2, -0.15, 0.23)
        glVertex3f(0.2, -0.15, 0.23)
        glVertex3f(0.15, -0.15, 0)
        glVertex3f(-0.15, -0.15, 0)
        glEnd()
        
        # Lower teeth
        glColor3f(1, 1, 1)
        glBegin(GL_QUADS)
        for i in range(4):
            x = -0.15 + i * 0.1
            glVertex3f(x, 0, 0.231)
            glVertex3f(x + 0.08, 0, 0.231)
            glVertex3f(x + 0.08, 0.05, 0.231)
            glVertex3f(x, 0.05, 0.231)
        glEnd()
        glPopMatrix()
        
        # Upper teeth (fixed in place)
        glColor3f(1, 1, 1)
        glBegin(GL_QUADS)
        for i in range(4):
            x = -0.15 + i * 0.1
            glVertex3f(x, -0.2, 0.231)
            glVertex3f(x + 0.08, -0.2, 0.231)
            glVertex3f(x + 0.08, -0.15, 0.231)
            glVertex3f(x, -0.15, 0.231)
        glEnd()
        
        # Cranial details (suture lines)
        glColor3f(0.8, 0.8, 0.8)
        glBegin(GL_LINES)
        # Coronal suture
        glVertex3f(-0.22, 0.1, 0.23)
        glVertex3f(0.22, 0.1, 0.23)
        # Sagittal suture
        glVertex3f(0, -0.1, 0.23)
        glVertex3f(0, 0.22, 0.23)
        glEnd()
        
        # Draw flames
        self.draw_flames()
        
        # Horns - now darker and more menacing
        glColor3f(0.2, 0.2, 0.2)  # Even darker gray for horns
        glBegin(GL_TRIANGLES)
        # Left horn
        glVertex3f(-0.2, 0.3, 0)
        glVertex3f(-0.4, 0.9, 0)  # Made horns longer
        glVertex3f(-0.1, 0.3, 0)
        
        # Right horn
        glVertex3f(0.2, 0.3, 0)
        glVertex3f(0.4, 0.9, 0)  # Made horns longer
        glVertex3f(0.1, 0.3, 0)
        glEnd()
        
        # Add wings
        self.draw_wings()
        
        glPopMatrix()

    def draw_wings(self):
        # Wing base color (blend with character color)
        wing_color = [0.9 + c * 0.1 for c in self.color]
        
        # Animation
        time = pygame.time.get_ticks() / 1000.0
        wing_flap = np.sin(time * 2) * 15  # Slower, subtler flap
        
        # Left wing
        glPushMatrix()
        glColor3f(*wing_color)
        # Move wing lower and further back
        glTranslatef(-0.4, -0.3, -0.3)
        glRotatef(wing_flap - 40, 0, 1, 0)  # Base angle + animation
        
        # Draw main wing segments with curved shape
        for i in range(4):  # Four segments for longer wings
            glBegin(GL_TRIANGLES)
            # Main wing membrane with curved shape
            glVertex3f(0, 0, 0)
            glVertex3f(-1.0 - i * 0.5, 0.4 + np.sin(i * 0.8) * 0.3, -0.6 - i * 0.3)
            glVertex3f(-0.8 - i * 0.5, -0.4 + np.sin(i * 0.8) * 0.3, -0.5 - i * 0.3)
            
            # Wing details (darker shade)
            glColor3f(*[c * 0.7 for c in wing_color])
            # Additional membrane details
            glVertex3f(-0.2 - i * 0.4, 0.1 + np.sin(i * 0.8) * 0.2, -0.2 - i * 0.2)
            glVertex3f(-0.7 - i * 0.5, 0.3 + np.sin(i * 0.8) * 0.2, -0.5 - i * 0.3)
            glVertex3f(-0.6 - i * 0.5, -0.3 + np.sin(i * 0.8) * 0.2, -0.4 - i * 0.3)
            glEnd()
            
            # Wing bones and veins
            glColor3f(*[c * 0.6 for c in wing_color])
            glBegin(GL_LINES)
            # Main bone
            glVertex3f(0, 0, 0)
            glVertex3f(-1.2 - i * 0.5, np.sin(i * 0.8) * 0.3, -0.7 - i * 0.3)
            # Secondary veins
            for j in range(3):
                t = j / 2.0
                glVertex3f(-0.3 - i * 0.4 * t, 0.2 * t, -0.2 - i * 0.2 * t)
                glVertex3f(-0.8 - i * 0.5 * t, -0.2 + np.sin(i * 0.8) * 0.3, -0.5 - i * 0.3 * t)
            glEnd()
            
            glColor3f(*wing_color)  # Reset color for next segment
        glPopMatrix()
        
        # Right wing (mirrored)
        glPushMatrix()
        glColor3f(*wing_color)
        glTranslatef(0.4, -0.3, -0.3)
        glRotatef(-wing_flap + 40, 0, 1, 0)
        
        for i in range(4):
            glBegin(GL_TRIANGLES)
            # Main wing membrane
            glVertex3f(0, 0, 0)
            glVertex3f(1.0 + i * 0.5, 0.4 + np.sin(i * 0.8) * 0.3, -0.6 - i * 0.3)
            glVertex3f(0.8 + i * 0.5, -0.4 + np.sin(i * 0.8) * 0.3, -0.5 - i * 0.3)
            
            # Wing details
            glColor3f(*[c * 0.7 for c in wing_color])
            glVertex3f(0.2 + i * 0.4, 0.1 + np.sin(i * 0.8) * 0.2, -0.2 - i * 0.2)
            glVertex3f(0.7 + i * 0.5, 0.3 + np.sin(i * 0.8) * 0.2, -0.5 - i * 0.3)
            glVertex3f(0.6 + i * 0.5, -0.3 + np.sin(i * 0.8) * 0.2, -0.4 - i * 0.3)
            glEnd()
            
            # Wing bones and veins
            glColor3f(*[c * 0.6 for c in wing_color])
            glBegin(GL_LINES)
            # Main bone
            glVertex3f(0, 0, 0)
            glVertex3f(1.2 + i * 0.5, np.sin(i * 0.8) * 0.3, -0.7 - i * 0.3)
            # Secondary veins
            for j in range(3):
                t = j / 2.0
                glVertex3f(0.3 + i * 0.4 * t, 0.2 * t, -0.2 - i * 0.2 * t)
                glVertex3f(0.8 + i * 0.5 * t, -0.2 + np.sin(i * 0.8) * 0.3, -0.5 - i * 0.3 * t)
            glEnd()
            
            glColor3f(*wing_color)
        glPopMatrix()

    def draw_flames(self):
        # Base of flames
        flame_colors = [
            (1.0, 0.0, 0.0),  # Red
            (1.0, 0.5, 0.0),  # Orange
            (1.0, 0.8, 0.0)   # Yellow
        ]
        
        # Current time for animation
        time = pygame.time.get_ticks() / 200.0
        
        for i, color in enumerate(flame_colors):
            glColor3f(*color)
            glBegin(GL_TRIANGLES)
            
            # Multiple flame tongues with wave effect
            for j in range(6):
                x_offset = 0.1 * np.sin(time + j)
                height = 0.3 + 0.1 * np.sin(time * 2 + j)
                width = 0.15 - i * 0.03  # Flames get thinner towards the center
                
                # Main flame
                glVertex3f(-width + x_offset, 0.2, 0)
                glVertex3f(width + x_offset, 0.2, 0)
                glVertex3f(0 + x_offset, 0.2 + height, 0)
                
                # Side flames
                glVertex3f(-width*0.7 + x_offset, 0.2, width)
                glVertex3f(width*0.7 + x_offset, 0.2, width)
                glVertex3f(0 + x_offset, 0.2 + height*0.8, width*0.5)
            glEnd()

    def draw_arms(self):
        # Left arm with bicep
        glPushMatrix()
        glTranslatef(-0.6, 0.5, 0)
        if self.is_punching and self.punch_frame < 10:
            glRotatef(45 * self.punch_frame/10, 0, 0, 1)
            # Flex bicep more during punch
            bicep_flex = 0.3 + 0.1 * (self.punch_frame/10)
        else:
            bicep_flex = 0.3
        
        # Upper arm (bicep)
        glColor3f(*[c * 0.9 for c in self.color])
        self.draw_bicep(0, -0.2, 0, bicep_flex)
        
        # Tricep
        glColor3f(*[c * 0.85 for c in self.color])
        self.draw_tricep(0, -0.2, 0, 0.2)
        
        # Lower arm with muscles
        glColor3f(*self.color)
        self.draw_limb(0.2, 0.6, True)
        glPopMatrix()
        
        # Right arm (mirror of left)
        glPushMatrix()
        glTranslatef(0.6, 0.5, 0)
        if self.is_punching and self.punch_frame < 10:
            glRotatef(-45 * self.punch_frame/10, 0, 0, 1)
            bicep_flex = 0.3 + 0.1 * (self.punch_frame/10)
        else:
            bicep_flex = 0.3
        
        glColor3f(*[c * 0.9 for c in self.color])
        self.draw_bicep(0, -0.2, 0, bicep_flex)
        
        glColor3f(*[c * 0.85 for c in self.color])
        self.draw_tricep(0, -0.2, 0, 0.2)
        
        glColor3f(*self.color)
        self.draw_limb(0.2, 0.6, True)
        glPopMatrix()

    def draw_legs(self):
        # Left leg
        glPushMatrix()
        glTranslatef(-0.3, -1, 0)
        if self.is_kicking and self.kick_frame < 10:
            glRotatef(-90 * self.kick_frame/10, 0, 0, 1)
            glTranslatef(0, 0.3 * self.kick_frame/10, 0)
            # Flex leg muscles during kick
            muscle_flex = 1.2
        else:
            muscle_flex = 1.0
        
        glColor3f(*self.color)
        self.draw_limb(0.25 * muscle_flex, 0.8, False)  # Wider leg with muscle definition
        glPopMatrix()
        
        # Right leg
        glPushMatrix()
        glTranslatef(0.3, -1, 0)
        if self.is_kicking and self.kick_frame < 10:
            glRotatef(90 * self.kick_frame/10, 0, 0, 1)
            glTranslatef(0, 0.3 * self.kick_frame/10, 0)
            muscle_flex = 1.2
        else:
            muscle_flex = 1.0
        
        glColor3f(*self.color)
        self.draw_limb(0.25 * muscle_flex, 0.8, False)
        glPopMatrix()

    def punch(self):
        if self.melee_cooldown <= 0 and not self.is_punching:
            self.is_punching = True
            self.punch_frame = 0
            self.melee_cooldown = 20
            return True
        return False

    def kick(self):
        if self.melee_cooldown <= 0 and not self.is_kicking:
            self.is_kicking = True
            self.kick_frame = 0
            self.melee_cooldown = 30
            return True
        return False

    def draw_torso(self):
        glPushMatrix()
        glTranslatef(0, 0, 0)
        
        # Main body (torso)
        glColor3f(*self.color)
        self.draw_cube(0, 0, 0, 0.8)  # Base torso
        
        # Add chest muscles
        glColor3f(*[c * 0.8 for c in self.color])  # Slightly darker shade
        glPushMatrix()
        glTranslatef(0, 0.2, 0.41)  # Move slightly forward
        
        # Left pec
        glBegin(GL_TRIANGLES)
        glVertex3f(-0.3, 0.2, 0)
        glVertex3f(-0.1, 0, 0)
        glVertex3f(-0.3, -0.1, 0)
        glEnd()
        
        # Right pec
        glBegin(GL_TRIANGLES)
        glVertex3f(0.3, 0.2, 0)
        glVertex3f(0.1, 0, 0)
        glVertex3f(0.3, -0.1, 0)
        glEnd()
        
        glPopMatrix()
        glPopMatrix()

    def draw_limb(self, width, length, is_arm=True):
        # Base limb shape
        glBegin(GL_QUADS)
        # Front face
        glVertex3f(-width/2, 0, width/2)
        glVertex3f(width/2, 0, width/2)
        glVertex3f(width/2, -length, width/2)
        glVertex3f(-width/2, -length, width/2)
        # Back face
        glVertex3f(-width/2, 0, -width/2)
        glVertex3f(width/2, 0, -width/2)
        glVertex3f(width/2, -length, -width/2)
        glVertex3f(-width/2, -length, -width/2)
        # Side faces
        glVertex3f(-width/2, 0, -width/2)
        glVertex3f(-width/2, 0, width/2)
        glVertex3f(-width/2, -length, width/2)
        glVertex3f(-width/2, -length, -width/2)
        
        glVertex3f(width/2, 0, -width/2)
        glVertex3f(width/2, 0, width/2)
        glVertex3f(width/2, -length, width/2)
        glVertex3f(width/2, -length, -width/2)
        glEnd()

        # Add muscle definition
        glColor3f(*[c * 0.85 for c in self.color])  # Slightly darker for muscles
        
        if is_arm:
            # Forearm muscle bulge
            glBegin(GL_TRIANGLES)
            # Front bulge
            glVertex3f(-width/3, -length*0.3, width/2 + 0.05)
            glVertex3f(width/3, -length*0.3, width/2 + 0.05)
            glVertex3f(0, -length*0.6, width/2 + 0.08)
            glEnd()
        else:
            # Calf muscle
            glBegin(GL_TRIANGLES)
            # Back calf bulge
            glVertex3f(-width/2, -length*0.3, -width/2 - 0.05)
            glVertex3f(width/2, -length*0.3, -width/2 - 0.05)
            glVertex3f(0, -length*0.6, -width/2 - 0.1)
            # Side calf bulges
            glVertex3f(-width/2 - 0.05, -length*0.3, 0)
            glVertex3f(-width/2 - 0.05, -length*0.6, 0)
            glVertex3f(-width/2, -length*0.45, 0)
            
            glVertex3f(width/2 + 0.05, -length*0.3, 0)
            glVertex3f(width/2 + 0.05, -length*0.6, 0)
            glVertex3f(width/2, -length*0.45, 0)
            glEnd()

    def draw_bicep(self, x, y, z, size):
        # Draw a bulging bicep
        glPushMatrix()
        glTranslatef(x, y, z)
        
        # Main bicep bulge
        glBegin(GL_TRIANGLES)
        # Front bulge
        glVertex3f(-size, 0, size)
        glVertex3f(size, 0, size)
        glVertex3f(0, size*1.5, size*0.8)
        # Back bulge
        glVertex3f(-size, 0, -size)
        glVertex3f(size, 0, -size)
        glVertex3f(0, size*1.5, -size*0.8)
        # Side bulges
        glVertex3f(-size, 0, -size)
        glVertex3f(-size, 0, size)
        glVertex3f(0, size*1.5, 0)
        
        glVertex3f(size, 0, -size)
        glVertex3f(size, 0, size)
        glVertex3f(0, size*1.5, 0)
        glEnd()
        
        glPopMatrix()

    def draw_tricep(self, x, y, z, size):
        glPushMatrix()
        glTranslatef(x, y, z)
        
        glBegin(GL_TRIANGLES)
        # Back tricep bulge
        glVertex3f(-size, 0, -size)
        glVertex3f(size, 0, -size)
        glVertex3f(0, -size*1.2, -size*1.2)
        glEnd()
        
        glPopMatrix()

    def draw_cube(self, x, y, z, size=1.0):
        # Helper function to draw a cube of given size
        glPushMatrix()
        glTranslatef(x, y, z)
        glBegin(GL_QUADS)
        # Front face
        glVertex3f(-size/2, -size/2, size/2)
        glVertex3f(size/2, -size/2, size/2)
        glVertex3f(size/2, size/2, size/2)
        glVertex3f(-size/2, size/2, size/2)
        # Back face
        glVertex3f(-size/2, -size/2, -size/2)
        glVertex3f(-size/2, size/2, -size/2)
        glVertex3f(size/2, size/2, -size/2)
        glVertex3f(size/2, -size/2, -size/2)
        # Top face
        glVertex3f(-size/2, size/2, -size/2)
        glVertex3f(-size/2, size/2, size/2)
        glVertex3f(size/2, size/2, size/2)
        glVertex3f(size/2, size/2, -size/2)
        # Bottom face
        glVertex3f(-size/2, -size/2, -size/2)
        glVertex3f(size/2, -size/2, -size/2)
        glVertex3f(size/2, -size/2, size/2)
        glVertex3f(-size/2, -size/2, size/2)
        # Right face
        glVertex3f(size/2, -size/2, -size/2)
        glVertex3f(size/2, size/2, -size/2)
        glVertex3f(size/2, size/2, size/2)
        glVertex3f(size/2, -size/2, size/2)
        # Left face
        glVertex3f(-size/2, -size/2, -size/2)
        glVertex3f(-size/2, -size/2, size/2)
        glVertex3f(-size/2, size/2, size/2)
        glVertex3f(-size/2, size/2, -size/2)
        glEnd()
        glPopMatrix()

    def draw_explosion(self):
        # Draw explosion particles
        for particle in self.explosion_particles:
            glPushMatrix()
            glTranslatef(*particle['position'])
            
            # Draw particle as a colored quad
            glColor3f(*particle['color'])
            size = particle['size']
            glBegin(GL_QUADS)
            glVertex3f(-size, -size, 0)
            glVertex3f(size, -size, 0)
            glVertex3f(size, size, 0)
            glVertex3f(-size, size, 0)
            glEnd()
            
            glPopMatrix()

    def breathe_fire(self):
        if not self.is_breathing_fire and self.fire_breath_cooldown <= 0:
            self.is_breathing_fire = True
            self.fire_breath_duration = 0
            return True
        return False

    def update_fire_breath(self):
        # Add new particles
        direction = 1.0 if self.position[0] < 0 else -1.0
        for _ in range(3):  # Add 3 new particles per frame
            spread = np.random.uniform(-0.2, 0.2)
            speed = np.random.uniform(0.3, 0.5)
            self.fire_breath_particles.append({
                'position': [
                    self.position[0] + direction * 0.5,  # Start from mouth
                    self.position[1] + 1.2,  # Head height
                    self.position[2]
                ],
                'velocity': [
                    direction * speed,
                    spread * 0.2,
                    spread
                ],
                'size': np.random.uniform(0.1, 0.3),
                'life': 20  # Particle lifetime in frames
            })

        # Update existing particles
        for particle in self.fire_breath_particles:
            particle['position'][0] += particle['velocity'][0]
            particle['position'][1] += particle['velocity'][1]
            particle['position'][2] += particle['velocity'][2]
            particle['life'] -= 1
            particle['size'] *= 0.95

        # Remove dead particles
        self.fire_breath_particles = [p for p in self.fire_breath_particles if p['life'] > 0]

    def draw_fire_breath(self):
        for particle in self.fire_breath_particles:
            glPushMatrix()
            
            # Move to particle position
            pos = particle['position']
            glTranslatef(pos[0] - self.position[0], pos[1] - self.position[1], pos[2] - self.position[2])
            
            # Calculate color based on particle life
            life_ratio = particle['life'] / 20.0
            glColor3f(1.0, life_ratio * 0.7, life_ratio * 0.2)  # Red to orange gradient
            
            # Draw particle as billboard quad
            size = particle['size']
            glBegin(GL_TRIANGLES)
            glVertex3f(-size, -size, 0)
            glVertex3f(size, -size, 0)
            glVertex3f(0, size, 0)
            glEnd()
            
            glPopMatrix()

class Projectile:
    def __init__(self, position, direction, speed=0.1):
        self.position = list(position)
        self.direction = direction
        self.speed = speed
        self.active = True
        # Enhance trail effect
        self.trail = []
        self.trail_length = 15
        self.trail_fade = 0.8

    def update(self):
        # Add current position to trail
        self.trail.append(list(self.position))
        # Keep trail at fixed length
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)
        
        # Update position based on direction and speed
        self.position[0] += self.direction[0] * self.speed
        self.position[1] += self.direction[1] * self.speed
        self.position[2] += self.direction[2] * self.speed
        
        # Deactivate if too far from origin
        if abs(self.position[0]) > 10 or abs(self.position[1]) > 10:
            self.active = False

    def draw(self):
        if not self.active:
            return
            
        glPushMatrix()
        
        # Draw trail with enhanced effect
        glBegin(GL_QUAD_STRIP)
        for i, pos in enumerate(self.trail):
            # Calculate fade based on position in trail
            alpha = (i / len(self.trail)) * self.trail_fade
            # Trail color: brighter orange/red gradient
            glColor3f(1.0, alpha * 0.8, alpha * 0.2)
            
            # Create width for trail with pulsing effect
            trail_width = 0.15 * alpha * (1 + 0.2 * np.sin(i * 0.5))
            glVertex3f(pos[0], pos[1] + trail_width, pos[2])
            glVertex3f(pos[0], pos[1] - trail_width, pos[2])
        glEnd()
        
        # Draw missile body
        glTranslatef(*self.position)
        
        # Rotate missile to face direction of travel
        if self.direction[0] < 0:
            glRotatef(180, 0, 1, 0)
        
        # Draw missile body (elongated shape)
        glColor3f(0.8, 0.8, 0.8)  # Metallic gray
        
        # Main body (cylinder-like)
        glBegin(GL_QUADS)
        size = 0.1
        length = 0.4
        
        # Body
        glVertex3f(-length, -size, size)
        glVertex3f(length, -size, size)
        glVertex3f(length, size, size)
        glVertex3f(-length, size, size)
        
        glVertex3f(-length, -size, -size)
        glVertex3f(-length, size, -size)
        glVertex3f(length, size, -size)
        glVertex3f(length, -size, -size)
        
        glVertex3f(-length, size, -size)
        glVertex3f(-length, size, size)
        glVertex3f(length, size, size)
        glVertex3f(length, size, -size)
        
        glVertex3f(-length, -size, -size)
        glVertex3f(length, -size, -size)
        glVertex3f(length, -size, size)
        glVertex3f(-length, -size, size)
        glEnd()
        
        # Nose cone (red tip)
        glColor3f(1.0, 0.0, 0.0)  # Red
        glBegin(GL_TRIANGLES)
        glVertex3f(length, 0, 0)  # Tip
        glVertex3f(length-0.2, size, size)  # Base
        glVertex3f(length-0.2, -size, size)
        
        glVertex3f(length, 0, 0)  # Tip
        glVertex3f(length-0.2, -size, -size)
        glVertex3f(length-0.2, size, -size)
        
        glVertex3f(length, 0, 0)  # Tip
        glVertex3f(length-0.2, size, size)
        glVertex3f(length-0.2, size, -size)
        
        glVertex3f(length, 0, 0)  # Tip
        glVertex3f(length-0.2, -size, -size)
        glVertex3f(length-0.2, -size, size)
        glEnd()
        
        # Fins
        glColor3f(0.7, 0.7, 0.7)  # Lighter gray
        glBegin(GL_TRIANGLES)
        fin_size = 0.2
        
        # Top fin
        glVertex3f(-length, size, 0)
        glVertex3f(-length+0.2, size+fin_size, 0)
        glVertex3f(-length+0.4, size, 0)
        
        # Bottom fin
        glVertex3f(-length, -size, 0)
        glVertex3f(-length+0.2, -size-fin_size, 0)
        glVertex3f(-length+0.4, -size, 0)
        
        # Side fins
        glVertex3f(-length, 0, size)
        glVertex3f(-length+0.2, 0, size+fin_size)
        glVertex3f(-length+0.4, 0, size)
        
        glVertex3f(-length, 0, -size)
        glVertex3f(-length+0.2, 0, -size-fin_size)
        glVertex3f(-length+0.4, 0, -size)
        glEnd()
        
        glPopMatrix()