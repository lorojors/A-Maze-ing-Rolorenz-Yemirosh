# A-Maze-ing

This project has been created as part of the 42 curriculum by **rolorenz** and **yemirosh**.

## Overview

**A-Maze-ing** is a sophisticated maze generation and solving library written in Python. It implements two state-of-the-art maze generation algorithms (Recursive Backtracker and Prim's algorithm) with support for both perfect and imperfect mazes. The project includes both a reusable module (`mazegen.py`) for programmatic use and an interactive terminal application (`a_maze_ing.py`) for visualizing and exploring generated mazes.

---

## Features

- **Dual Algorithm Support**: Choose between Recursive Backtracker and Prim's algorithm for maze generation
- **Perfect & Imperfect Mazes**: Generate perfect mazes (exactly one path between any two cells) or add additional passages for complexity
- **Pathfinding**: Automatic shortest path solving using Breadth-First Search (BFS)
- **Interactive Terminal UI**: Navigate, regenerate, visualize paths, and toggle visual themes in real-time
- **ASCII & Hexadecimal Output**: Display mazes in multiple formats for flexibility
- **Reproducible Results**: Use seed values for consistent maze generation
- **42 Easter Egg**: Special pattern detection and visualization for the 42 School theme
- **Animation Support**: Watch the maze generation algorithm in action
- **Extensively Documented**: Full docstrings and examples for developers

---

## Project Structure

```
a_maze_ing/
├── a_maze_ing.py          # Main interactive application entry point
├── mazegen.py            # Core maze generation module (reusable)
├── config.txt            # Configuration file for maze parameters
├── maze.txt              # Output file with generated maze (hexadecimal format)
├── pyproject.toml        # Python project metadata and build configuration
├── setup.py              # Package setup and installation script
├── Makefile              # Convenience commands for building and running
└── README.md             # This file
```

### File Responsibilities

| File | Purpose |
|------|---------|
| `a_maze_ing.py` | Interactive terminal application with colourized display and keyboard controls |
| `mazegen.py` | Reusable module for maze generation, solving, and manipulation |
| `config.txt` | User-configurable parameters for maze dimensions, entry/exit, algorithms |
| `maze.txt` | Generated maze output in hexadecimal format (one hex nibble per cell) |

---

## Installation & Setup

### Prerequisites

- Python 3.10 or higher
- No external dependencies (uses only Python standard library)

### Quick Start

1. **Clone or download the project**:
   ```bash
   cd /path/to/A-Maze-ing
   ```

2. **Run with default configuration**:
   ```bash
   python3 a_maze_ing.py config.txt
   ```

3. **Using the Makefile** (if available):
   ```bash
   make run          # Run the application
   make build        # Build the Python package
   make clean        # Clean build artifacts
   ```

### Installation as a Package

For use in other Python projects:

```bash
pip install -e .
```

Then import in your code:
```python
from mazegen import MazeGenerator
```

---

## Configuration Guide

Edit `config.txt` to customize maze generation parameters:

### Mandatory Parameters

```ini
WIDTH=60              # Maze width in cells (must be >= 2)
HEIGHT=20             # Maze height in cells (must be >= 2)
ENTRY=0,0             # Entry cell as x,y (0-based coordinates; must be inside bounds)
EXIT=40,14            # Exit cell as x,y (0-based; must differ from ENTRY and be inside bounds)
OUTPUT_FILE=maze.txt  # Path where the generated maze will be saved
PERFECT=False         # True = perfect maze (one path between any two cells)
                      # False = imperfect maze (additional passages exist)
```

### Optional Parameters

```ini
SEED=42                     # Integer seed for reproducible mazes (omit for random)
ALGORITHM=recursive_backtracker  # Generation algorithm:
                            # - recursive_backtracker (default, faster)
                            # - prim (often produces fewer dead-ends)
ANIMATE=False               # Show generation animation in real-time
```

### Example Configurations

**Small Perfect Maze**:
```ini
WIDTH=15
HEIGHT=10
ENTRY=0,0
EXIT=14,9
PERFECT=True
SEED=12345
```

**Large Imperfect Maze with Animation**:
```ini
WIDTH=100
HEIGHT=50
ENTRY=0,0
EXIT=99,49
PERFECT=False
ANIMATE=True
ALGORITHM=prim
```

---

## Usage Guide

### Running the Interactive Application

```bash
python3 a_maze_ing.py config.txt
```

#### Keyboard Controls

| Key | Action |
|-----|--------|
| `r` | Regenerate a new maze with a random seed |
| `p` | Show or hide the shortest path (marked with `*`) |
| `c` | Cycle through wall colour themes (4 themes available) |
| `h` | Toggle '42' pattern highlighting |
| `q` | Quit the application |

#### Colour Theme Guide

The application cycles through multiple colour themes:
1. **Theme 1**: Colourful (white walls, green path, yellow entry, red exit)
2. **Theme 2**: Cyan & Gold (cyan walls, yellow path, green entry, magenta exit)
3. **Theme 3**: Blue Aqua (blue walls, cyan path, yellow entry, green exit)
4. **Theme 4**: Monochrome (no colours; useful for terminal limitations)

#### Output

- The maze is displayed in the terminal with:
  - `█` or coloured blocks for **walls**
  - Space (` `) for **open passages**
  - `S` marking the **entry** (start)
  - `E` marking the **exit** point

---

## Programming Guide for Developers

### Basic Usage Example

```python
from mazegen import MazeGenerator

# Create a generator instance
mg = MazeGenerator(
    width=20,
    height=15,
    entry=(0, 0),
    exit_=(19, 14),
    perfect=True,
    seed=42  # Use None for random seed
)

# Generate the maze
mg.generate(algorithm="recursive_backtracker", animate=False)

# Display the maze
mg.display_ascii()

# Solve and display path
path = mg.solve()  # Returns list of 'N', 'E', 'S', 'W' steps
print(f"Path length: {len(path)} steps")
mg.display_ascii(path=path, highlight_42=True)

# Save to file
mg.to_hex_file("output.txt", path=path)
```

### Understanding Maze Structure

The maze is stored as a 2D list of integers (`mg.maze`):

- **Shape**: `[height][width]` → `[y][x]`
- **Cell Values**: 4-bit integers encoding wall states (0-15)
- **Wall Encoding**:
  - Bit 0 (LSB, value 1): North wall
  - Bit 1 (value 2): East wall
  - Bit 2 (value 4): South wall
  - Bit 3 (value 8): West wall
  - **1 = wall closed**, **0 = wall open**

**Example**: Cell value `5` = `0101` binary = North wall open, East wall closed, South wall open, West wall closed

### Key Methods

```python
# Generation
mg.generate(algorithm="recursive_backtracker"|"prim", animate=False)

# Solving
path = mg.solve()  # Returns: ['N', 'E', 'S', 'W', ...]

# Display
mg.display_ascii(path=None, highlight_42=False)

# File I/O
mg.to_hex_file(filename, path=None)
mg.from_hex_file(filename)

# Utilities
cells = mg._path_to_cells(path)  # Convert direction list to cell coordinates
```

### Algorithm Explanation

#### Recursive Backtracker

1. **Start** at the entry cell
2. **Mark** current cell as visited
3. **Randomly choose** an unvisited neighboring cell
4. **Carve** a passage (remove wall) between current and neighbor
5. **Recursively** continue from the neighbor
6. **Backtrack** when no unvisited neighbors remain
7. **Repeat** until all cells are visited

*Advantages*: Faster generation, creates deep mazes with long corridors  
*Characteristics*: Often produces more linear maze structures

#### Prim's Algorithm

1. **Start** with the entry cell in a "visited" set and add its neighbors to a "frontier"
2. **Randomly pick** a cell from the frontier
3. **Connect** it to a random visited neighbor (carve passage)
4. **Add** the new cell to visited set
5. **Add** its unvisited neighbors to the frontier
6. **Repeat** until frontier is empty

*Advantages*: More balanced mazes with better connectivity distribution  
*Characteristics*: Often creates more branching paths

---

## Guide for Future Students

### Learning Objectives

By studying this project, you'll learn:

1. **Data Structures**: 2D arrays, bit manipulation, queue/stack usage
2. **Algorithms**: Depth-first search (backtracking), Breadth-first search (pathfinding)
3. **Graph Theory**: Spanning trees, perfect graphs, tree traversal
4. **Python Conventions**: Docstrings, type hints, modular design
5. **Terminal Programming**: ANSI colour codes, raw input handling
6. **File I/O**: Parsing configuration, writing binary formats

### Code Study Path

1. **Start with `mazegen.py`**:
   - Review class initialization and validation (robustness)
   - Study the `_generate_backtracker()` method (DFS algorithm)
   - Understand the wall bitmask system
   - Examine `_bfs_solve()` for pathfinding

2. **Then examine `a_maze_ing.py`**:
   - See how to integrate the module
   - Learn about ANSI colour handling
   - Understand terminal input management

3. **Try modifications**:
   - Add a new maze topology (hexagonal, triangular)
   - Implement a third algorithm (recursive division)
   - Create visual statistics about maze properties
   - Add difficulty rating based on path length vs maze size

### Best Practices Demonstrated

- **Type Hints**: Used throughout for code clarity and IDE support
- **Docstrings**: Comprehensive documentation following Google style
- **Separation of Concerns**: Module (`mazegen`) separate from UI (`a_maze_ing`)
- **Error Handling**: Input validation with informative error messages
- **Constants**: Clearly named (WALL_N, WALL_E, etc.)
- **Bit Operations**: Efficient wall encoding/decoding
- **Reproducibility**: Seed support for deterministic output

### Debugging Tips

- Use `mg.display_ascii()` to visualize maze state at any time
- Add print statements in generation loops to trace algorithm progress
- Use the `seed` parameter to debug specific maze patterns
- Enable `animate=True` to watch generation step-by-step
- Check the hexadecimal output format for cell corruption issues

### Extension Ideas

**Easy**:
- Add maze statistics (number of dead-ends, average path width)
- Create ASCII animation of pathfinding
- Add difficulty ratings

**Medium**:
- Implement Kruskal's algorithm for maze generation
- Add maze solving visualization (show search progress)
- Support rectangular cells vs square cells (for artistic control)

**Hard**:
- Implement 3D or layered maze generation
- Add obstacle placement with pathfinding around them
- Create maze weaving (paths can cross over/under)
- Implement domain-specific visualization (castle dungeons, space stations)

---

## Technical Details

### Maze File Format (Hexadecimal)

Output hexadecimal format stores one nibble (4 bits) per cell:
- Each hex digit (0-F) represents the wall configuration
- Row-major order (left to right, top to bottom)
- Can be imported back using `from_hex_file()`

**Example** (4x4 maze):
```
F E E E
8 8 8 4
B B B 6
D C C 5
```

Each hex digit encodes walls as: North=bit0, East=bit1, South=bit2, West=bit3

### Performance Characteristics

- **Generation Time**: O(width × height) for both algorithms
- **Memory Usage**: O(width × height) for the maze grid
- **Path Solving**: O(width × height) for BFS
- **Scalability**: Handles 1000× 1000 mazes on modern hardware

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Entry/Exit outside bounds" | Ensure coordinates are 0-based and within WIDTH×HEIGHT |
| Maze too small | Increase WIDTH and HEIGHT in config.txt |
| Path not showing | Ensure `perfect=False` or regenerate with `-s` flag |
| Terminal colours don't display | Try a different theme with `c` key or use monochrome theme |
| Input not responding | Ensure terminal is in raw/interactive mode (may need to disable line buffering) |

---

## License

MIT License — See project files for details.

---

## Authors

- **rolorenz** – Main implementation, algorithms, and optimization
- **yemirosh** – Collaboration and testing

---

## Acknowledgments

This project was developed as part of the 42 School curriculum, emphasizing:
- Clean code practices
- Algorithm understanding
- Problem-solving methodology
- Collaborative development

---

## Quick Reference

```bash
# Generate maze with current config
python3 a_maze_ing.py config.txt

# Generate and exit (no interactive mode)
python3 a_maze_ing.py config.txt < /dev/null

# Import as module
from mazegen import MazeGenerator

# Create 50x30 perfect maze with seed
mg = MazeGenerator(50, 30, (0, 0), (49, 29), perfect=True, seed=999)
mg.generate(algorithm="prim")
mg.display_ascii()
print(mg.solve())
```

---

**Happy maze exploring! 🌀**
