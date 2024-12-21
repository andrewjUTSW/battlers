# Retro 3D Fighting Game

A retro-style 3D fighting game built with Python, PyOpenGL, and Pygame.

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
.venv\Scriptsctivate  # On Windows
```

4. Install dependencies:
```bash
uv pip install -r requirements.txt
```

### Running the Game

To start the game:
```bash
python game.py
```

Controls:
- ESC: Quit the game
- More controls coming soon...

## Project Structure

```
.
├── .gitignore          # Git ignore file
├── README.md           # This file
├── requirements.txt    # Python dependencies
└── game.py            # Main game file
```

## Development

Currently implemented:
- Basic 3D environment setup
- Ground plane and reference cube
- Basic game loop structure

Coming soon:
- Character models
- Fighting mechanics
- AI opponent
- Game states
- UI elements
- Sound effects

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
