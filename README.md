# Retro 3D Fighting Game

A retro-style 3D fighting game built with Python, PyOpenGL, and Pygame. Features two characters in a 3D arena with projectile combat and special effects.

## Features

- 3D graphics with OpenGL rendering
- Real-time combat mechanics
- Character movement and jumping physics
- Projectile system with collision detection
- Health bars and score tracking
- Sound effects for actions
- Explosion animations
- 60 FPS smooth gameplay

## Setup

### Prerequisites
- Python 3.10 or higher
- uv (for virtual environment and package management)

### Installation

1. Install uv if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone the repository:
```bash
git clone <your-repo-url>
cd <repo-name>
```

3. Create and activate virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Unix/MacOS
# or
.venv\Scripts\activate  # On Windows
```

4. Install dependencies:
```bash
uv pip install -r requirements.txt
```

## Playing the Game

Start the game:
```bash
python game.py
```

### Controls

Player 1 (Blue):
- **LEFT/RIGHT Arrow Keys**: Move
- **UP Arrow**: Jump
- **M**: Punch
- **N**: Kick
- **B**: Shoot

Player 2 (Red):
- **A/D**: Move left/right
- **W**: Jump
- **Q**: Punch
- **E**: Kick
- **R**: Shoot

General:
- **ESC**: Quit game

### Characters
- **Captain Destructor** (Blue) - Player character with ranged attacks
- **Villain** (Red) - Enemy character with health tracking

## Project Structure

```
.
├── .gitignore          # Git ignore file
├── README.md           # Documentation
├── requirements.txt    # Python dependencies
├── game.py            # Game launcher
├── sounds/            # Sound effects directory
│   ├── explosion.wav
│   ├── hit.wav
│   ├── jump.wav
│   └── shoot.wav
└── src/               # Source code
    ├── __init__.py
    ├── game.py        # Main game logic
    ├── characters.py  # Character classes
    └── sound_manager.py # Sound management
```

## Technical Details

### Graphics
- OpenGL for 3D rendering
- Custom character models
- Real-time lighting
- 2D overlay for UI elements

### Physics
- Basic gravity simulation
- Collision detection
- Projectile trajectory calculation

### Audio
- Sound effects for actions:
  - Jumping
  - Shooting
  - Hit detection
  - Explosions

## Development

### Current Features
- 3D environment with ground plane
- Character movement and jumping
- Projectile combat system
- Health tracking
- Score system
- Sound effects
- Explosion animations

### Planned Features
- Additional character moves
- Power-ups
- Multiple levels
- Menu system
- High score tracking
- More special effects

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- PyGame community for the game development framework
- OpenGL for 3D graphics capabilities
- Python community for support and resources
