import numpy as np
from OpenGL.GL import *
from pygame.math import Vector3

class Character:
    def __init__(self, name, position=(0, 0, 0), color=(1, 1, 1), strength=100, pistols=0):
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
        
        # Apply gravity and update vertical position
        self.velocity.y -= self.gravity
        self.position[1] = max(self.position[1] + self.velocity.y, 0)  # Don't go below ground
        
        # Check if landed
        if self.position[1] == 0 and self.velocity.y <= 0:
            self.velocity.y = 0
            self.is_jumping = False

    def jump(self):
        if not self.is_jumping:
            self.velocity.y = self.jump_speed
            self.is_jumping = True
            return True
        return False

    def shoot(self):
        if self.pistols > 0:
            direction = (1.0 if self.position[0] < 0 else -1.0, 0, 0)
            start_pos = (
                self.position[0] + direction[0],
                self.position[1],
                self.position[2]
            )
            projectile = Projectile(
                position=start_pos,
                direction=direction,
                speed=0.2
            )
            self.projectiles.append(projectile)

    def draw(self):
        if self.is_exploding:
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
        else:
            # Normal character drawing code
            glPushMatrix()
            glTranslatef(*self.position)
            
            # Set character color
            glColor3f(*self.color)
            
            # Draw body (cube)
            glBegin(GL_QUADS)
            # Front face
            glVertex3f(-0.5, -1, 0.5)
            glVertex3f(0.5, -1, 0.5)
            glVertex3f(0.5, 1, 0.5)
            glVertex3f(-0.5, 1, 0.5)
            # Back face
            glVertex3f(-0.5, -1, -0.5)
            glVertex3f(-0.5, 1, -0.5)
            glVertex3f(0.5, 1, -0.5)
            glVertex3f(0.5, -1, -0.5)
            # Top face
            glVertex3f(-0.5, 1, -0.5)
            glVertex3f(-0.5, 1, 0.5)
            glVertex3f(0.5, 1, 0.5)
            glVertex3f(0.5, 1, -0.5)
            # Bottom face
            glVertex3f(-0.5, -1, -0.5)
            glVertex3f(0.5, -1, -0.5)
            glVertex3f(0.5, -1, 0.5)
            glVertex3f(-0.5, -1, 0.5)
            glEnd()
            
            glPopMatrix()

class Projectile:
    def __init__(self, position, direction, speed=0.2):
        self.position = list(position)
        self.direction = direction
        self.speed = speed
        self.active = True

    def update(self):
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
        glTranslatef(*self.position)
        
        # Draw projectile as a small yellow cube
        glColor3f(1.0, 1.0, 0.0)  # Yellow color
        
        # Make the projectile smaller than characters but still visible
        size = 0.2
        glBegin(GL_QUADS)
        # Front face
        glVertex3f(-size, -size, size)
        glVertex3f(size, -size, size)
        glVertex3f(size, size, size)
        glVertex3f(-size, size, size)
        # Back face
        glVertex3f(-size, -size, -size)
        glVertex3f(-size, size, -size)
        glVertex3f(size, size, -size)
        glVertex3f(size, -size, -size)
        # Top face
        glVertex3f(-size, size, -size)
        glVertex3f(-size, size, size)
        glVertex3f(size, size, size)
        glVertex3f(size, size, -size)
        # Bottom face
        glVertex3f(-size, -size, -size)
        glVertex3f(size, -size, -size)
        glVertex3f(size, -size, size)
        glVertex3f(-size, -size, size)
        glEnd()
        
        glPopMatrix()