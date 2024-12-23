import numpy as np
from OpenGL.GL import *
from pygame.math import Vector3

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

        # Update AI behavior if this is an AI character
        if self.is_ai:
            self.update_ai()

        # Update attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

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
        if not self.is_jumping:
            self.velocity.y = self.jump_speed
            self.is_jumping = True
            return True
        return False

    def shoot(self):
        if self.shoot_cooldown <= 0 and self.pistols > 0:
            direction = (1.0 if self.position[0] < 0 else -1.0, 0, 0)
            start_pos = (
                self.position[0] + direction[0],
                self.position[1] + 0.5,  # Adjust height to shoot from chest
                self.position[2]
            )
            projectile = Projectile(
                position=start_pos,
                direction=direction,
                speed=0.1
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
        
        glPopMatrix()

    def draw_head(self):
        glPushMatrix()
        glTranslatef(0, 1.2, 0)
        
        # Head cube
        glColor3f(*self.color)
        self.draw_cube(0, 0, 0, 0.4)
        
        # Face features
        glColor3f(0, 0, 0)  # Black for face features
        
        # Eyes
        glBegin(GL_TRIANGLES)
        # Left eye
        glVertex3f(-0.1, 0.1, 0.21)
        glVertex3f(-0.2, 0, 0.21)
        glVertex3f(0, 0, 0.21)
        # Right eye
        glVertex3f(0.1, 0.1, 0.21)
        glVertex3f(0.2, 0, 0.21)
        glVertex3f(0, 0, 0.21)
        glEnd()
        
        # Mouth
        glBegin(GL_LINES)
        glVertex3f(-0.1, -0.1, 0.21)
        glVertex3f(0.1, -0.1, 0.21)
        glEnd()
        
        # Horns
        glColor3f(0.7, 0.7, 0.7)  # Gray horns
        glBegin(GL_TRIANGLES)
        # Left horn
        glVertex3f(-0.2, 0.3, 0)
        glVertex3f(-0.3, 0.5, 0)
        glVertex3f(-0.1, 0.3, 0)
        # Right horn
        glVertex3f(0.2, 0.3, 0)
        glVertex3f(0.3, 0.5, 0)
        glVertex3f(0.1, 0.3, 0)
        glEnd()
        
        glPopMatrix()

    def draw_arms(self):
        # Left arm
        glPushMatrix()
        glTranslatef(-0.6, 0.5, 0)
        if self.is_punching and self.punch_frame < 10:
            glRotatef(45 * self.punch_frame/10, 0, 0, 1)
        self.draw_limb(0.2, 0.6)
        glPopMatrix()
        
        # Right arm
        glPushMatrix()
        glTranslatef(0.6, 0.5, 0)
        if self.is_punching and self.punch_frame < 10:
            glRotatef(-45 * self.punch_frame/10, 0, 0, 1)
        self.draw_limb(0.2, 0.6)
        glPopMatrix()

    def draw_legs(self):
        # Left leg
        glPushMatrix()
        glTranslatef(-0.3, -1, 0)
        if self.is_kicking and self.kick_frame < 10:
            glRotatef(-60 * self.kick_frame/10, 0, 0, 1)
        self.draw_limb(0.2, 0.8)
        glPopMatrix()
        
        # Right leg
        glPushMatrix()
        glTranslatef(0.3, -1, 0)
        if self.is_kicking and self.kick_frame < 10:
            glRotatef(60 * self.kick_frame/10, 0, 0, 1)
        self.draw_limb(0.2, 0.8)
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
        # Draw the main body cube
        glPushMatrix()
        glTranslatef(0, 0, 0)
        
        # Main body
        glColor3f(*self.color)
        self.draw_cube(0, 0, 0, 0.8)  # Bigger cube for torso
        
        glPopMatrix()

    def draw_limb(self, width, length):
        # Draw a limb (arm or leg) as an elongated cube
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
        # Left face
        glVertex3f(-width/2, 0, -width/2)
        glVertex3f(-width/2, 0, width/2)
        glVertex3f(-width/2, -length, width/2)
        glVertex3f(-width/2, -length, -width/2)
        # Right face
        glVertex3f(width/2, 0, -width/2)
        glVertex3f(width/2, 0, width/2)
        glVertex3f(width/2, -length, width/2)
        glVertex3f(width/2, -length, -width/2)
        glEnd()

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