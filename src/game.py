import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import google.generativeai as genai
from PIL import Image
import io
import os
from dotenv import load_dotenv

from src.sound_manager import SoundManager
from src.characters import Character, Projectile

# Load environment variables at startup
load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
print(f"Found API key: {'Yes' if api_key else 'No'}")
# print(f"API key: {api_key}")
if not api_key:
    print("Warning: GEMINI_API_KEY not found in environment variables")

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

        # Melee combat range
        self.melee_range = 1.5

        # Initialize Gemini
        try:
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            print("Gemini model initialized successfully with gemini-2.0-flash-exp")
        except Exception as e:
            print(f"Warning: Could not initialize Gemini: {e}")
            self.gemini_model = None
            
        # Add screenshot analysis cooldown
        self.last_analysis_time = 0
        self.analysis_cooldown = 5000  # 5 seconds between analyses

        # Add analysis display variables
        self.current_analysis = None
        self.analysis_display_time = 0
        self.analysis_display_duration = 5000  # Show for 5 seconds

    def initialize_characters(self):
        self.player1 = Character(
            name="Player 1", 
            position=(-3, 0, 0),
            color=(0, 0, 1),      # Blue
            strength=100,
            pistols=2,
            is_ai=False
        )
        self.player2 = Character(
            name="Player 2",
            position=(3, 0, 0),
            color=(1, 0, 0),      # Red
            strength=100,
            pistols=2,
            is_ai=False          # Changed to False for human player
        )

    def handle_events(self):
        keys = pygame.key.get_pressed()
        
        # Combine all event handling into one loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_TAB:
                    print("Tab pressed - attempting analysis...")  # Debug print
                    analysis = self.analyze_screenshot()
                    if analysis:
                        print("\nGemini Analysis:", analysis)
                        self.current_analysis = analysis
                        self.analysis_display_time = pygame.time.get_ticks()
                    else:
                        print("No analysis returned")  # Debug print
        
        # Player 1 controls
        if keys[pygame.K_LEFT]:
            self.player1.position[0] -= self.player1.move_speed
        if keys[pygame.K_RIGHT]:
            self.player1.position[0] += self.player1.move_speed
        if keys[pygame.K_UP]:
            if self.player1.jump():
                self.sound_manager.play('jump')
        if keys[pygame.K_m]:  # M for punch
            if self.player1.punch():
                self.sound_manager.play('punch')
        if keys[pygame.K_n]:  # N for kick
            if self.player1.kick():
                self.sound_manager.play('kick')
        if keys[pygame.K_b]:  # B for shoot
            if self.player1.shoot():
                self.sound_manager.play('shoot')
        if keys[pygame.K_v]:  # V for fire breath
            if self.player1.breathe_fire():
                self.sound_manager.play('fire')

        # Player 2 controls
        if keys[pygame.K_a]:
            self.player2.position[0] -= self.player2.move_speed
        if keys[pygame.K_d]:
            self.player2.position[0] += self.player2.move_speed
        if keys[pygame.K_w]:
            if self.player2.jump():
                self.sound_manager.play('jump')
        if keys[pygame.K_q]:  # Q for punch
            if self.player2.punch():
                self.sound_manager.play('punch')
        if keys[pygame.K_e]:  # E for kick
            if self.player2.kick():
                self.sound_manager.play('kick')
        if keys[pygame.K_r]:  # R for shoot
            if self.player2.shoot():
                self.sound_manager.play('shoot')
        if keys[pygame.K_f]:  # F for fire breath
            if self.player2.breathe_fire():
                self.sound_manager.play('fire')

    def update(self):
        # Check if either character is already defeated
        if self.player1.strength <= 0 or self.player2.strength <= 0:
            # Wait for explosion animation to finish
            if not self.player1.is_exploding and not self.player2.is_exploding:
                print("Game Over!")
                if self.player2.strength <= 0:
                    print(f"Player 1 wins!")
                else:
                    print(f"Player 2 wins!")
                self.running = False
                return

        # Update characters
        self.player1.update()
        self.player2.update()
        
        # Check melee combat
        self.check_melee_combat()
        
        # Update all active projectiles and check collisions
        for projectile in self.all_projectiles:
            projectile.update()
            
            # Check collision with player2 (Villain)
            if projectile.direction[0] > 0:  # Moving right (from player1)
                if self.check_collision(projectile, self.player2):
                    print(f"{self.player2.name} was hit by a missile!")
                    self.player2.strength -= 15
                    projectile.active = False
                    self.score += 15
                    self.sound_manager.play('hit')
                    
                    if self.player2.strength <= 0:
                        print(f"{self.player2.name} has been defeated!")
                        self.player2.start_explosion()
                        self.sound_manager.play('explosion')
                        self.score += 50
                        self.player2.strength = 0  # Ensure health doesn't go negative
            
            # Check collision with player1 (Captain Destructor)
            elif projectile.direction[0] < 0:  # Moving left (from player2)
                if self.check_collision(projectile, self.player1):
                    print(f"{self.player1.name} was hit by a missile!")
                    self.player1.strength -= 15
                    projectile.active = False
                    self.sound_manager.play('hit')
                    
                    if self.player1.strength <= 0:
                        print(f"{self.player1.name} has been defeated!")
                        self.player1.start_explosion()
                        self.sound_manager.play('explosion')
                        self.player1.strength = 0  # Ensure health doesn't go negative

        # Add new projectiles from both players to the main list
        for projectile in self.player1.projectiles + self.player2.projectiles:
            self.all_projectiles.append(projectile)
        self.player1.projectiles.clear()
        self.player2.projectiles.clear()
        
        # Remove inactive projectiles
        self.all_projectiles = [p for p in self.all_projectiles if p.active]

        # Check fire breath damage
        if self.player1.is_breathing_fire:
            distance = abs(self.player1.position[0] - self.player2.position[0])
            # Only damage if player 1 is to the left of player 2 (facing right)
            is_facing_right = self.player1.position[0] < self.player2.position[0]
            if distance < 4.0 and is_facing_right:  # Fire breath range and correct direction
                damage = 2.0
                self.player2.strength -= damage
                self.score += damage
                
                if pygame.time.get_ticks() % 10 == 0:
                    self.sound_manager.play('hit')
                    print(f"{self.player2.name} is burning! Health: {self.player2.strength}")
                
                if self.player2.strength <= 0:
                    print(f"{self.player2.name} was incinerated!")
                    self.player2.start_explosion()
                    self.sound_manager.play('explosion')
                    self.score += 50
                    self.player2.strength = 0

        # Same for player 2's fire breath
        if self.player2.is_breathing_fire:
            distance = abs(self.player1.position[0] - self.player2.position[0])
            # Only damage if player 2 is to the right of player 1 (facing left)
            is_facing_left = self.player2.position[0] > self.player1.position[0]
            if distance < 4.0 and is_facing_left:
                damage = 2.0
                self.player1.strength -= damage
                
                if pygame.time.get_ticks() % 10 == 0:
                    self.sound_manager.play('hit')
                    print(f"{self.player1.name} is burning! Health: {self.player1.strength}")
                
                if self.player1.strength <= 0:
                    print(f"{self.player1.name} was incinerated!")
                    self.player1.start_explosion()
                    self.sound_manager.play('explosion')
                    self.player1.strength = 0

        # Update eye fire effects
        for player in [self.player1, self.player2]:
            if player.is_eyes_on_fire:
                player.eyes_fire_duration += 1
                if player.eyes_fire_duration >= player.eyes_fire_max:
                    player.is_eyes_on_fire = False

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
        
        # Draw Gemini analysis if active
        current_time = pygame.time.get_ticks()
        if self.current_analysis and current_time - self.analysis_display_time < self.analysis_display_duration:
            self.draw_analysis()
        
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
        # Get the distance between projectile and character
        dx = projectile.position[0] - character.position[0]
        dy = projectile.position[1] - character.position[1]
        dz = projectile.position[2] - character.position[2]
        
        # Calculate 3D distance
        distance = np.sqrt(dx*dx + dy*dy + dz*dz)
        
        # Use a smaller collision radius for more precise hits
        return distance < 0.8  # Reduced from 1.0 for more precise hits

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

    def check_melee_combat(self):
        if self.player1.strength <= 0 or self.player2.strength <= 0:
            return

        distance = abs(self.player1.position[0] - self.player2.position[0])
        
        if distance < self.melee_range:
            # Calculate damage based on velocity and position
            if self.player1.is_punching and self.player1.punch_frame == 5:
                impact = abs(self.player1.velocity.x) * 20
                damage = min(max(5, impact), 15)  # Between 5 and 15 damage
                self.player2.strength -= damage
                # Add knockback
                self.player2.velocity.x += self.player1.velocity.x * 1.5
                self.player2.velocity.y += 0.1
                self.sound_manager.play('hit')
                print(f"{self.player2.name} was hit for {damage:.1f} damage!")
                self.score += damage

    def analyze_screenshot(self):
        if not self.gemini_model:
            print("Gemini model not initialized")
            return "Gemini API not configured"
            
        current_time = pygame.time.get_ticks()
        if current_time - self.last_analysis_time < self.analysis_cooldown:
            print("Analysis on cooldown")
            return None
            
        try:
            print("Attempting to capture screenshot...")
            
            # Get the dimensions of the window
            viewport = glGetIntegerv(GL_VIEWPORT)
            width, height = viewport[2], viewport[3]

            # Read the framebuffer directly from OpenGL
            glPixelStorei(GL_PACK_ALIGNMENT, 1)
            buffer = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
            
            # Convert to PIL Image and flip vertically (OpenGL coordinates are flipped)
            image = Image.frombytes('RGB', (width, height), buffer)
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
            
            print("Sending to Gemini...")
            # Enhanced prompt for more dynamic commentary
            prompt = """
            You're a fighting game commentator! Analyze this screenshot and provide exciting commentary about:
            - The blue fighter (Player 1) and red fighter (Player 2)'s positions
            - Any active special moves (fire breath, missiles, punches)
            - The current state of battle (health bars, who's winning)
            - Any visual effects or explosions
            Keep it brief, energetic, and fun - like a real fighting game announcer!
            """
            
            response = self.gemini_model.generate_content([prompt, image])
            
            self.last_analysis_time = current_time
            return response.text
            
        except Exception as e:
            print(f"Screenshot analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def draw_analysis(self):
        """Draw the Gemini analysis on screen"""
        glPushMatrix()
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Disable lighting and depth testing for 2D text
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        
        # Split analysis into lines for better display
        words = self.current_analysis.split()
        lines = []
        current_line = []
        line_length = 0
        
        for word in words:
            if line_length + len(word) > 50:  # Max chars per line
                lines.append(' '.join(current_line))
                current_line = [word]
                line_length = len(word)
            else:
                current_line.append(word)
                line_length += len(word) + 1
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw semi-transparent background
        glColor4f(0, 0, 0, 0.7)
        glBegin(GL_QUADS)
        glVertex3f(-0.9, 0.5, 0)
        glVertex3f(0.9, 0.5, 0)
        glVertex3f(0.9, -0.5, 0)
        glVertex3f(-0.9, -0.5, 0)
        glEnd()
        
        # Render text lines
        y_pos = 0.3
        for line in lines:
            text_surface = self.font.render(line, True, (255, 255, 255))
            text_data = pygame.image.tostring(text_surface, 'RGBA', True)
            
            glRasterPos2f(-0.85, y_pos)
            glDrawPixels(text_surface.get_width(), text_surface.get_height(), 
                        GL_RGBA, GL_UNSIGNED_BYTE, text_data)
            y_pos -= 0.1
        
        # Restore state
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()