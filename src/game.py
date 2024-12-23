import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

from src.sound_manager import SoundManager
from src.characters import Character, Projectile

class FightingGame:
    def __init__(self, width=800, height=600):
        pygame.init()
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Retro Fighting Game")
        
        # Set up the 3D perspective
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        gluPerspective(45, (width/height), 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
        # Move camera back and up slightly to see the scene better
        glTranslatef(0.0, -1.0, -15.0)
        
        # Enable depth testing
        glEnable(GL_DEPTH_TEST)
        
        # Add basic lighting
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, (5, 5, 5, 1))
        
        # Set material properties
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # Initialize characters
        self.initialize_characters()

        # Game state
        self.running = True
        self.clock = pygame.time.Clock()

        # Add sound manager
        self.sound_manager = SoundManager()
        
        # Add score
        self.score = 0
        
        # Add font for score display
        pygame.font.init()
        self.font = pygame.font.Font(None, 36)

        # List to manage all projectiles in the game
        self.all_projectiles = []

    def initialize_characters(self):
        self.player1 = Character(
            name="Captain Destructor", 
            position=(-3, 0, 0),
            color=(0, 0, 1),
            strength=100,
            pistols=2,
            is_ai=False
        )
        self.player2 = Character(
            name="Villain",
            position=(3, 0, 0),
            color=(1, 0, 0),
            strength=100,
            pistols=2,  # Give the villain some pistols
            is_ai=True  # Make the villain AI-controlled
        )

    def handle_events(self):
        keys = pygame.key.get_pressed()
        
        # Movement
        if keys[pygame.K_LEFT]:
            self.player1.position[0] -= 0.1
        if keys[pygame.K_RIGHT]:
            self.player1.position[0] += 0.1
        if keys[pygame.K_UP]:
            if self.player1.jump():
                self.sound_manager.play('jump')
        
        # Combat controls
        if keys[pygame.K_z]:  # Z for punch
            if self.player1.punch():
                self.sound_manager.play('punch')
        if keys[pygame.K_x]:  # X for kick
            if self.player1.kick():
                self.sound_manager.play('kick')
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.player1.shoot()
                    self.sound_manager.play('shoot')

    def update(self):
        # Update characters
        self.player1.update()
        self.player2.update()
        
        # Update all active projectiles and check collisions
        for projectile in self.all_projectiles:
            projectile.update()
            
            # Determine projectile owner and target
            if projectile in self.player1.projectiles:
                target = self.player2
                shooter = self.player1
            else:
                target = self.player1
                shooter = self.player2
                
            if self.check_collision(projectile, target):
                print(f"{target.name} was hit by {shooter.name}'s projectile!")
                target.strength -= 10
                projectile.active = False
                self.sound_manager.play('hit')
                
                if target.strength <= 0:
                    print(f"{target.name} has been defeated!")
                    target.start_explosion()
                    self.sound_manager.play('explosion')
                    if target == self.player2:
                        self.score += 50

        # Add new projectiles from both players to the main list
        for projectile in self.player1.projectiles + self.player2.projectiles:
            self.all_projectiles.append(projectile)
        self.player1.projectiles.clear()
        self.player2.projectiles.clear()
        
        # Remove inactive projectiles
        self.all_projectiles = [p for p in self.all_projectiles if p.active]

    def draw_score(self):
        glPushMatrix()
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Disable lighting and depth testing for 2D elements
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        
        # Render score text
        score_surface = self.font.render(f'Score: {self.score}', True, (255, 255, 255))
        score_data = pygame.image.tostring(score_surface, 'RGBA', True)
        
        glRasterPos2f(-0.9, -0.9)
        glDrawPixels(score_surface.get_width(), score_surface.get_height(), 
                    GL_RGBA, GL_UNSIGNED_BYTE, score_data)
        
        # Restore state
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def draw(self):
        # Clear the screen and set background color to dark blue
        glClearColor(0.1, 0.1, 0.2, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Reset modelview matrix
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Move camera back and up slightly
        glTranslatef(0.0, -1.0, -15.0)
        
        # Draw ground plane
        glBegin(GL_QUADS)
        glColor3f(0.2, 0.5, 0.2)  # Green color for ground
        glVertex3f(-10, -2, -10)
        glVertex3f(-10, -2, 10)
        glVertex3f(10, -2, 10)
        glVertex3f(10, -2, -10)
        glEnd()

        # Draw a reference cube
        self.draw_cube(0, 0, 0)
        
        # Draw ground plane and characters
        self.player1.draw()
        self.player2.draw()

        # Draw all active projectiles
        for projectile in self.all_projectiles:
            projectile.draw()

        # Draw health bars and score
        self.draw_health_bars()
        self.draw_score()
        
        pygame.display.flip() 

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)  # 60 FPS
        pygame.quit() 

    def draw_cube(self, x, y, z):
        # Helper function to draw a small cube
        glPushMatrix()
        glTranslatef(x, y, z)
        glBegin(GL_QUADS)
        # Front face (red)
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(-0.5, -0.5, 0.5)
        glVertex3f(0.5, -0.5, 0.5)
        glVertex3f(0.5, 0.5, 0.5)
        glVertex3f(-0.5, 0.5, 0.5)
        # Back face (blue)
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f(-0.5, 0.5, -0.5)
        glVertex3f(0.5, 0.5, -0.5)
        glVertex3f(0.5, -0.5, -0.5)
        # Top face (green)
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(-0.5, 0.5, -0.5)
        glVertex3f(-0.5, 0.5, 0.5)
        glVertex3f(0.5, 0.5, 0.5)
        glVertex3f(0.5, 0.5, -0.5)
        # Bottom face (yellow)
        glColor3f(1.0, 1.0, 0.0)
        glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f(0.5, -0.5, -0.5)
        glVertex3f(0.5, -0.5, 0.5)
        glVertex3f(-0.5, -0.5, 0.5)
        glEnd()
        glPopMatrix()

    def check_collision(self, projectile, character):
        # Simple collision detection based on distance
        distance = np.linalg.norm(np.array(projectile.position) - np.array(character.position))
        return distance < 1.0  # Threshold distance for collision

    def draw_health_bars(self):
        # Save current matrix and set up orthographic projection for 2D
        glPushMatrix()
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Disable lighting and depth testing for 2D elements
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        
        # Draw player 1 health bar (left side)
        glColor3f(0, 0, 1)  # Blue
        glBegin(GL_QUADS)
        glVertex3f(-0.9, 0.8, 0)
        glVertex3f(-0.9 + (self.player1.strength/100) * 0.8, 0.8, 0)
        glVertex3f(-0.9 + (self.player1.strength/100) * 0.8, 0.9, 0)
        glVertex3f(-0.9, 0.9, 0)
        glEnd()
        
        # Draw player 2 health bar (right side)
        glColor3f(1, 0, 0)  # Red
        glBegin(GL_QUADS)
        glVertex3f(0.1, 0.8, 0)
        glVertex3f(0.1 + (self.player2.strength/100) * 0.8, 0.8, 0)
        glVertex3f(0.1 + (self.player2.strength/100) * 0.8, 0.9, 0)
        glVertex3f(0.1, 0.9, 0)
        glEnd()
        
        # Restore previous state
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        
        # Restore matrices
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()