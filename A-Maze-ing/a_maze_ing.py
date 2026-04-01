"""a_maze_ing.py - Main entry point for the A-Maze-ing maze generator.

Usage::

    python3 a_maze_ing.py config.txt

The program reads a configuration file, generates a maze, displays it in the
terminal with interactive controls, and writes the result to an output file.

Interactive controls (terminal mode):
    r  - Re-generate a new maze (random seed)
    p  - Show / hide the shortest path
    c  - Cycle through wall colour themes
    h  - Toggle '42' pattern highlighting
    q  - Quit
"""
from __future__ import annotations

import sys
import os
import tty
import termios
from typing import List, Optional, Tuple, Dict, Any

from mazegen import MazeGenerator

# ---------------------------------------------------------------------------
# ANSI colour helpers
# ---------------------------------------------------------------------------

THEMES: List[Dict[str, str]] = [
    {"wall": "\033[37m", "path": "\033[32m", "entry": "\033[33m",
     "exit": "\033[31m", "42": "\033[35m", "reset": "\033[0m"},
    {"wall": "\033[36m", "path": "\033[33m", "entry": "\033[32m",
     "exit": "\033[35m", "42": "\033[31m", "reset": "\033[0m"},
    {"wall": "\033[34m", "path": "\033[36m", "entry": "\033[33m",
     "exit": "\033[32m", "42": "\033[31m", "reset": "\033[0m"},
    {"wall": "\033[0m", "path": "\033[0m", "entry": "\033[0m",
     "exit": "\033[0m", "42": "\033[0m", "reset": "\033[0m"},
]


def coloured_display(
    mg: MazeGenerator,
    theme: Dict[str, str],
    path: Optional[List[str]],
    show_path: bool,
    show_42: bool,
) -> None:
    """Render the maze to stdout with ANSI colours.

    Args:
        mg: A generated MazeGenerator instance.
        theme: Colour mapping dictionary from ``THEMES``.
        path: Pre-computed solution path (direction strings).
        show_path: Whether to overlay the solution path.
        show_42: Whether to highlight '42' pattern cells.
    """
    path_cells = mg._path_to_cells(path) if (path and show_path) else set()
    pattern_cells = mg._get_42_cells() if show_42 else set()
    W = theme["wall"]
    P = theme["path"]
    E = theme["entry"]
    X = theme["exit"]
    F = theme["42"]
    R = theme["reset"]

    for y in range(mg.height):
        row_top = ""
        for x in range(mg.width):
            h_wall = "-" if mg.maze[y][x] & mg.WALL_N else " "
            row_top += W + "+" + R + W + h_wall + R
        print(row_top + W + "+" + R)

        row_mid = ""
        for x in range(mg.width):
            v_wall = "|" if mg.maze[y][x] & mg.WALL_W else " "
            row_mid += W + v_wall + R
            if (x, y) == mg.entry:
                row_mid += E + "E" + R
            elif (x, y) == mg.exit_:
                row_mid += X + "X" + R
            elif (x, y) in path_cells:
                row_mid += P + "*" + R
            elif (x, y) in pattern_cells:
                row_mid += F + "#" + R
            else:
                row_mid += " "
        v_wall_r = "|" if mg.maze[y][mg.width - 1] & mg.WALL_E else " "
        row_mid += W + v_wall_r + R
        print(row_mid)

    bottom = ""
    for x in range(mg.width):
        h_wall = "-" if mg.maze[mg.height - 1][x] & mg.WALL_S else " "
        bottom += W + "+" + R + W + h_wall + R
    print(bottom + W + "+" + R)


def print_help(show_path: bool, show_42: bool, theme_idx: int) -> None:
    """Print the interactive controls legend.

    Args:
        show_path: Current path-visibility state.
        show_42: Current '42'-highlight state.
        theme_idx: Current colour theme index.
    """
    print(
        f"\n  [r] Re-generate  "
        f"[p] Path: {'ON ' if show_path else 'OFF'}  "
        f"[c] Theme: {theme_idx + 1}/{len(THEMES)}  "
        f"[h] 42 highlight: {'ON ' if show_42 else 'OFF'}  "
        f"[q] Quit"
    )


def getch() -> str:
    """Read a single character from stdin without echoing.

    Returns:
        The character pressed by the user.
    """
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch


# ---------------------------------------------------------------------------
# Config parsing
# ---------------------------------------------------------------------------

REQUIRED_KEYS = {"WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"}


def parse_config(filename: str) -> Dict[str, Any]:
    """Parse a KEY=VALUE configuration file.

    Args:
        filename: Path to the configuration file.

    Returns:
        A dictionary with typed configuration values.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file has bad syntax or missing/invalid keys.
    """
    cfg: Dict[str, str] = {}
    try:
        with open(filename) as f:
            for lineno, raw in enumerate(f, start=1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    raise ValueError(
                        f"{filename}:{lineno}: expected KEY=VALUE, "
                        f"got: {line!r}"
                    )
                key, _, value = line.partition("=")
                cfg[key.strip().upper()] = value.strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: '{filename}'")

    missing = REQUIRED_KEYS - cfg.keys()
    if missing:
        keys_str = ', '.join(sorted(missing))
        raise ValueError(f"Missing required config keys: {keys_str}")

    try:
        width = int(cfg["WIDTH"])
        height = int(cfg["HEIGHT"])
    except ValueError as exc:
        raise ValueError(f"WIDTH and HEIGHT must be integers: {exc}") from exc

    if width < 2 or height < 2:
        raise ValueError(
            f"WIDTH and HEIGHT must be >= 2, got {width}x{height}."
        )

    def parse_coord(raw: str, label: str) -> Tuple[int, int]:
        """Parse 'x,y' string into a tuple of ints."""
        parts = raw.split(",")
        if len(parts) != 2:
            raise ValueError(
                f"{label} must be 'x,y', got {raw!r}"
            )
        try:
            return int(parts[0].strip()), int(parts[1].strip())
        except ValueError as exc:
            msg = f"{label} coordinates must be integers: {exc}"
            raise ValueError(msg) from exc

    entry = parse_coord(cfg["ENTRY"], "ENTRY")
    exit_ = parse_coord(cfg["EXIT"], "EXIT")
    perfect = cfg.get("PERFECT", "True").lower() in ("true", "1", "yes")
    seed_raw = cfg.get("SEED", "").strip()
    seed: Optional[int] = (
        int(seed_raw)
        if seed_raw.lstrip("-").isdigit()
        else None
    )
    algorithm = cfg.get("ALGORITHM", "recursive_backtracker").strip()
    animate_raw = cfg.get("ANIMATE", "False").strip()
    animate = animate_raw.lower() in ("true", "1", "yes")

    return {
        "WIDTH": width,
        "HEIGHT": height,
        "ENTRY": entry,
        "EXIT": exit_,
        "OUTPUT_FILE": cfg["OUTPUT_FILE"],
        "PERFECT": perfect,
        "SEED": seed,
        "ALGORITHM": algorithm,
        "ANIMATE": animate,
    }


# ---------------------------------------------------------------------------
# Interactive loop
# ---------------------------------------------------------------------------

def interactive_loop(
    cfg: Dict[str, Any],
    mg: MazeGenerator,
    path: List[str],
) -> None:
    """Run the interactive terminal display loop.

    Args:
        cfg: Parsed configuration dictionary.
        mg: A fully generated MazeGenerator instance.
        path: Pre-computed solution path.
    """
    theme_idx = 0
    show_path = False
    show_42 = False
    generation_seed = cfg["SEED"]

    while True:
        os.system("clear")
        coloured_display(mg, THEMES[theme_idx], path, show_path, show_42)
        print_help(show_path, show_42, theme_idx)

        ch = getch().lower()
        if ch == "q":
            print("\nBye!")
            break
        elif ch == "p":
            show_path = not show_path
        elif ch == "h":
            show_42 = not show_42
        elif ch == "c":
            theme_idx = (theme_idx + 1) % len(THEMES)
        elif ch == "r":
            # Re-generate with a fresh random seed
            generation_seed = None
            try:
                mg = MazeGenerator(
                    cfg["WIDTH"],
                    cfg["HEIGHT"],
                    cfg["ENTRY"],
                    cfg["EXIT"],
                    cfg["PERFECT"],
                    seed=generation_seed,
                )
                mg.generate(algorithm=cfg["ALGORITHM"], animate=cfg["ANIMATE"])
                path = mg.solve()
                mg.to_hex_file(cfg["OUTPUT_FILE"], path=path)
            except Exception as exc:  # noqa: BLE001
                print(f"\nError re-generating maze: {exc}")
                getch()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Parse config, generate maze, write output, and start display loop."""
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]

    try:
        cfg = parse_config(config_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        mg = MazeGenerator(
            cfg["WIDTH"],
            cfg["HEIGHT"],
            cfg["ENTRY"],
            cfg["EXIT"],
            cfg["PERFECT"],
            seed=cfg["SEED"],
        )
        mg.generate(algorithm=cfg["ALGORITHM"], animate=cfg["ANIMATE"])
    except (ValueError, RecursionError) as exc:
        print(f"Maze generation error: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        path = mg.solve()
    except RuntimeError as exc:
        print(f"Solver error: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        mg.to_hex_file(cfg["OUTPUT_FILE"], path=path)
    except OSError as exc:
        print(f"Output error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Maze written to '{cfg['OUTPUT_FILE']}'.")
    if not path:
        print("Warning: no path found from entry to exit.")
    else:
        print(f"Shortest path length: {len(path)} steps.")

    try:
        interactive_loop(cfg, mg, path)
    except Exception as exc:  # noqa: BLE001
        # Fallback: if terminal control fails just show static ASCII
        print(f"Interactive mode unavailable ({exc}); showing static maze.")
        mg.display_ascii(path=path if path else None)


if __name__ == "__main__":
    main()
