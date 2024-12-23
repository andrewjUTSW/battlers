import pygame
import os

class SoundManager:
    def __init__(self):
        pygame.mixer.init()
        self.sounds = {}
        self._load_sounds()

    def _load_sounds(self):
        sound_dir = os.path.join(os.path.dirname(__file__), '..', 'sounds')
        sound_files = {
            'shoot': 'shoot.wav',
            'jump': 'jump.wav',
            'explosion': 'explosion.wav',
            'hit': 'hit.wav',
            'punch': 'hit.wav',
            'kick': 'hit.wav'
        }
        
        for name, file in sound_files.items():
            try:
                path = os.path.join(sound_dir, file)
                if os.path.exists(path):
                    self.sounds[name] = pygame.mixer.Sound(path)
                else:
                    print(f"Warning: Sound file not found: {file}")
            except Exception as e:
                print(f"Warning: Could not load sound {file}: {e}")

    def play(self, sound_name):
        if sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except:
                print(f"Warning: Could not play sound: {sound_name}") 