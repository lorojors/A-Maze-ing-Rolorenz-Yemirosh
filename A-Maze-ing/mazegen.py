"""mazegen - Reusable maze generation module.

Usage example::

    from mazegen import MazeGenerator

    mg = MazeGenerator(
        width=20, height=15, entry=(0, 0),
        exit_=(19, 14), perfect=True, seed=42
    )
    mg.generate(algorithm="recursive_backtracker")
    mg.display_ascii()
    path = mg.solve()          # list of 'N','E','S','W' steps
    mg.to_hex_file("maze.txt", path=path)

Custom parameters:

- ``width`` / ``height``: maze dimensions in cells.
- ``entry`` / ``exit_``: (x, y) tuples; must be inside maze
  bounds and different.
- ``perfect``: if True the generator carves a spanning tree
  (exactly one path between any two cells).
- ``seed``: integer seed for reproducibility; pass ``None`` for
  a random maze each run.
- ``algorithm``: ``"recursive_backtracker"`` (default) or
  ``"prim"``.

Maze structure:

- ``mg.maze`` is a ``List[List[int]]`` of shape
  ``[height][width]``.
- Each cell value is a 4-bit integer encoding **closed** walls:
  bit 0 (LSB) = North, bit 1 = East, bit 2 = South,
  bit 3 = West. A bit set to 1 means the wall is **closed**;
  0 means **open**.
- ``mg.solve()`` returns the shortest path as a list of
  direction characters.
"""

from __future__ import annotations

import os
import random
import time
from collections import deque
from typing import Dict, List, Optional, Tuple


class MazeGenerator:
    """Maze generator supporting recursive backtracker and Prim algorithms.

    Attributes:
        width: Number of columns.
        height: Number of rows.
        entry: Entry cell as (x, y).
        exit_: Exit cell as (x, y).
        perfect: Whether to generate a perfect maze (single path).
        seed: Random seed for reproducibility.
        maze: 2-D list [y][x] of cell wall bitmasks.

    Example::

        mg = MazeGenerator(10, 10, (0, 0), (9, 9), perfect=True, seed=1)
        mg.generate()
        print(mg.solve())
    """

    # Wall bitmask constants (bit position = direction index)
    WALL_N: int = 1   # bit 0
    WALL_E: int = 2   # bit 1
    WALL_S: int = 4   # bit 2
    WALL_W: int = 8   # bit 3

    # Direction deltas [N, E, S, W]
    DX: List[int] = [0, 1, 0, -1]
    DY: List[int] = [-1, 0, 1, 0]
    DIR_CHARS: List[str] = ["N", "E", "S", "W"]
    # wall bit of neighbour for each direction [N,E,S,W]
    OPPOSITE: List[int] = [4, 8, 1, 2]
    # wall bit of current cell for each direction [N,E,S,W]
    WALL_BITS: List[int] = [1, 2, 4, 8]

    def __init__(
        self,
        width: int,
        height: int,
        entry: Tuple[int, int],
        exit_: Tuple[int, int],
        perfect: bool = True,
        seed: Optional[int] = None,
    ) -> None:
        """Initialise the generator and validate parameters.

        Args:
            width: Maze width (number of columns, >= 2).
            height: Maze height (number of rows, >= 2).
            entry: Entry cell (x, y); must be inside maze bounds.
            exit_: Exit cell (x, y); must differ from entry
                and be inside bounds.
            perfect: Generate a perfect maze (spanning-tree)
                when True.
            seed: Integer seed for reproducible results;
                None for random.

        Raises:
            ValueError: If any parameter is invalid.
        """
        if width < 2 or height < 2:
            raise ValueError(
                f"Maze dimensions must be at least 2x2, "
                f"got {width}x{height}."
            )
        ex, ey = entry
        xx, xy = exit_
        if not (0 <= ex < width and 0 <= ey < height):
            raise ValueError(
                f"Entry {entry} is outside maze bounds "
                f"({width}x{height})."
            )
        if not (0 <= xx < width and 0 <= xy < height):
            raise ValueError(
                f"Exit {exit_} is outside maze bounds "
                f"({width}x{height})."
            )
        if entry == exit_:
            raise ValueError("Entry and exit must be different cells.")

        self.width: int = width
        self.height: int = height
        self.entry: Tuple[int, int] = entry
        self.exit_: Tuple[int, int] = exit_
        self.perfect: bool = perfect
        self.seed: Optional[int] = seed
        self._rng: random.Random = random.Random(seed)
        # All walls closed initially (bitmask 0b1111 = 15)
        self.maze: List[List[int]] = [[15] * width for _ in range(height)]
        self._generated: bool = False
        self._42_inserted: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        algorithm: str = "recursive_backtracker",
        animate: bool = False,
    ) -> None:
        """Generate the maze using the chosen algorithm.

        Args:
            algorithm: ``"recursive_backtracker"`` or ``"prim"``.
            animate: Print each generation step to the terminal when True.

        Raises:
            ValueError: If an unknown algorithm name is given.
        """
        self.maze = [[15] * self.width for _ in range(self.height)]
        if algorithm == "recursive_backtracker":
            self._generate_backtracker(animate)
        elif algorithm == "prim":
            self._generate_prim(animate)
        else:
            raise ValueError(
                f"Unknown algorithm '{algorithm}'. "
                "Choose 'recursive_backtracker' or 'prim'."
            )
        if not self.perfect:
            self._add_extra_passages()
        self._insert_42_pattern()
        self._generated = True

    def solve(self) -> List[str]:
        """Return the shortest path from entry to exit as direction characters.

        Returns:
            A list of ``'N'``, ``'E'``, ``'S'``, ``'W'`` strings representing
            each step of the shortest path.  Returns an empty list if no path
            exists.

        Raises:
            RuntimeError: If ``generate()`` has not been called yet.
        """
        if not self._generated:
            raise RuntimeError("Call generate() before solve().")
        return self._bfs_solve()

    def display_ascii(
        self,
        path: Optional[List[str]] = None,
        highlight_42: bool = False,
    ) -> None:
        """Print the maze to stdout using ASCII art.

        Args:
            path: Optional list of direction strings from ``solve()``;
                  visited cells are marked with ``*``.
            highlight_42: Mark '42' pattern cells with ``#`` when True.
        """
        path_cells = self._path_to_cells(path) if path else set()
        pattern_cells = self._get_42_cells() if highlight_42 else set()

        for y in range(self.height):
            # Top border of row y
            row_top = ""
            for x in range(self.width):
                wall_char = "-" if self.maze[y][x] & self.WALL_N else " "
                row_top += "+" + wall_char
            print(row_top + "+")
            # Cell content of row y
            row_mid = ""
            for x in range(self.width):
                row_mid += "|" if self.maze[y][x] & self.WALL_W else " "
                if (x, y) == self.entry:
                    row_mid += "E"
                elif (x, y) == self.exit_:
                    row_mid += "X"
                elif (x, y) in path_cells:
                    row_mid += "*"
                elif (x, y) in pattern_cells:
                    row_mid += "#"
                else:
                    row_mid += " "
            wall_char = ("|"
                         if self.maze[y][self.width - 1] & self.WALL_E
                         else " ")
            row_mid += wall_char
            print(row_mid)
        # Bottom border
        bottom = ""
        for x in range(self.width):
            wall_char = (("-"
                         if self.maze[self.height - 1][x] & self.WALL_S
                         else " "))
            bottom += "+" + wall_char
        print(bottom + "+")

    def to_hex_file(
        self,
        filename: str,
        path: Optional[List[str]] = None,
    ) -> None:
        """Write the maze to a file in hexadecimal wall format.

        File structure::

            <hex row 0>
            <hex row 1>
            ...
            <hex row height-1>

            entry_x,entry_y
            exit_x,exit_y
            <path string or empty>

        Args:
            filename: Destination file path.
            path: Solution path from ``solve()``; written as
                a direction string.

        Raises:
            OSError: If the file cannot be written.
        """
        path_str = "".join(path) if path else ""
        try:
            with open(filename, "w") as f:
                for row in self.maze:
                    f.write("".join(f"{cell:X}" for cell in row) + "\n")
                f.write("\n")
                f.write(f"{self.entry[0]},{self.entry[1]}\n")
                f.write(f"{self.exit_[0]},{self.exit_[1]}\n")
                f.write(path_str + "\n")
        except OSError as exc:
            msg = f"Could not write maze file '{filename}': {exc}"
            raise OSError(msg) from exc

    # ------------------------------------------------------------------
    # Generation algorithms
    # ------------------------------------------------------------------

    def _generate_backtracker(self, animate: bool) -> None:
        """Iterative recursive-backtracker (depth-first search) generation."""
        visited: List[List[bool]] = [
            [False] * self.width for _ in range(self.height)
        ]
        stack: List[Tuple[int, int]] = [self.entry]
        visited[self.entry[1]][self.entry[0]] = True

        while stack:
            x, y = stack[-1]
            dirs = list(range(4))
            self._rng.shuffle(dirs)
            moved = False
            for i in dirs:
                nx, ny = x + self.DX[i], y + self.DY[i]
                if (0 <= nx < self.width
                        and 0 <= ny < self.height
                        and not visited[ny][nx]):
                    self.maze[y][x] ^= self.WALL_BITS[i]
                    self.maze[ny][nx] ^= self.OPPOSITE[i]
                    visited[ny][nx] = True
                    stack.append((nx, ny))
                    if animate:
                        self._animate_frame()
                    moved = True
                    break
            if not moved:
                stack.pop()

    def _generate_prim(self, animate: bool) -> None:
        """Randomised Prim's algorithm generation."""
        visited: List[List[bool]] = [
            [False] * self.width for _ in range(self.height)
        ]
        x, y = self.entry
        visited[y][x] = True
        frontier: List[Tuple[int, int, int]] = []
        self._add_frontier(x, y, visited, frontier)

        while frontier:
            idx = self._rng.randrange(len(frontier))
            cx, cy, i = frontier.pop(idx)
            nx, ny = cx + self.DX[i], cy + self.DY[i]
            if (0 <= nx < self.width
                    and 0 <= ny < self.height
                    and not visited[ny][nx]):
                visited[ny][nx] = True
                self.maze[cy][cx] ^= self.WALL_BITS[i]
                self.maze[ny][nx] ^= self.OPPOSITE[i]
                self._add_frontier(nx, ny, visited, frontier)
                if animate:
                    self._animate_frame()

    def _add_frontier(
        self,
        x: int,
        y: int,
        visited: List[List[bool]],
        frontier: List[Tuple[int, int, int]],
    ) -> None:
        """Add unvisited neighbours of (x, y) to the frontier list."""
        for i in range(4):
            nx, ny = x + self.DX[i], y + self.DY[i]
            if (
                0 <= nx < self.width
                and 0 <= ny < self.height
                and not visited[ny][nx]
            ):
                frontier.append((x, y, i))

    def _add_extra_passages(self) -> None:
        """Remove a fraction of walls to create loops for non-perfect mazes."""
        removals = max(1, (self.width * self.height) // 10)
        for _ in range(removals):
            x = self._rng.randrange(self.width - 1)
            y = self._rng.randrange(self.height - 1)
            # Remove east wall between (x,y) and (x+1,y)
            self.maze[y][x] &= ~self.WALL_E
            self.maze[y][x + 1] &= ~self.WALL_W

    # ------------------------------------------------------------------
    # 42 pattern
    # ------------------------------------------------------------------

    def _get_42_cells(self) -> set[Tuple[int, int]]:
        """Return the set of (x, y) cells used by the '42' pattern."""
        pattern_42 = self._build_42_bitmap()
        cells: set[Tuple[int, int]] = set()
        rows = len(pattern_42)
        cols = len(pattern_42[0])
        px = (self.width - cols) // 2
        py = (self.height - rows) // 2
        for dy, row in enumerate(pattern_42):
            for dx, val in enumerate(row):
                if val:
                    cells.add((px + dx, py + dy))
        return cells

    @staticmethod
    def _build_42_bitmap() -> List[List[int]]:
        """Return a 5x9 pixel-art bitmap spelling '42'."""
        return [
            [1, 1, 0, 0, 1, 1, 1, 1, 0],
            [1, 1, 0, 0, 0, 0, 0, 1, 0],
            [1, 1, 1, 0, 0, 1, 1, 1, 0],
            [0, 0, 1, 0, 0, 1, 0, 0, 0],
            [1, 1, 1, 0, 0, 1, 1, 1, 0],
        ]

    def _insert_42_pattern(self) -> None:
        """Insert fully-walled '42' cells, then repair maze connectivity.

        Sealed pattern cells are given all four walls.  The neighbours of
        sealed cells are updated symmetrically so the wall data stays
        coherent.  Afterwards, a BFS check detects any cells that became
        disconnected from the entry; for each disconnected cell a single
        wall is opened to the nearest reachable neighbour, restoring full
        connectivity without removing the visual pattern.
        """
        pattern_42 = self._build_42_bitmap()
        rows = len(pattern_42)
        cols = len(pattern_42[0])
        px = (self.width - cols) // 2
        py = (self.height - rows) // 2

        if self.width < px + cols or self.height < py + rows:
            min_w = px + cols
            min_h = py + rows
            print(
                "Warning: maze is too small to display "
                "the '42' pattern "
                f"(need at least {min_w}x{min_h})."
            )
            self._42_inserted = False
            return

        pattern_set: set[Tuple[int, int]] = set()
        for dy, row in enumerate(pattern_42):
            for dx, val in enumerate(row):
                if val:
                    pattern_set.add((px + dx, py + dy))

        # Step 1: Seal all pattern cells and update neighbours
        # consistently.
        for cx, cy in pattern_set:
            self.maze[cy][cx] = 15
            for i in range(4):
                nx, ny = cx + self.DX[i], cy + self.DY[i]
                if (0 <= nx < self.width
                        and 0 <= ny < self.height):
                    self.maze[ny][nx] |= self.OPPOSITE[i]

        # Step 2: Repair connectivity — open walls from disconnected
        # cells to a reachable neighbour (skip pattern cells themselves).
        self._repair_connectivity(pattern_set)
        self._42_inserted = True

    def _repair_connectivity(
        self, protected: set[Tuple[int, int]]
    ) -> None:
        """Re-open walls to restore connectivity after pattern insertion.

        Runs a BFS from the entry cell.  Any non-pattern cell that is not
        reachable gets one wall opened toward a reachable neighbour.
        The process iterates until every non-pattern cell is connected.

        Args:
            protected: Set of (x, y) cells that must stay fully walled.
        """
        for _ in range(self.width * self.height):
            reachable = self._reachable_cells()
            disconnected = [
                (x, y)
                for y in range(self.height)
                for x in range(self.width)
                if (x, y) not in reachable and (x, y) not in protected
            ]
            if not disconnected:
                break
            # Pick the first disconnected cell and open a wall to any
            # reachable, non-protected neighbour.
            for cx, cy in disconnected:
                for i in range(4):
                    nx, ny = cx + self.DX[i], cy + self.DY[i]
                    if (
                        0 <= nx < self.width
                        and 0 <= ny < self.height
                        and (nx, ny) in reachable
                        and (nx, ny) not in protected
                    ):
                        self.maze[cy][cx] &= ~self.WALL_BITS[i]
                        self.maze[ny][nx] &= ~self.OPPOSITE[i]
                        break

    def _reachable_cells(self) -> set[Tuple[int, int]]:
        """Return the set of cells reachable from the entry via open walls."""
        visited: set[Tuple[int, int]] = set()
        queue: deque[Tuple[int, int]] = deque([self.entry])
        visited.add(self.entry)
        while queue:
            x, y = queue.popleft()
            for i in range(4):
                if self.maze[y][x] & self.WALL_BITS[i]:
                    continue  # wall closed
                nx, ny = x + self.DX[i], y + self.DY[i]
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        return visited

    # ------------------------------------------------------------------
    # Pathfinding
    # ------------------------------------------------------------------

    def _bfs_solve(self) -> List[str]:
        """BFS to find shortest path; returns list of direction."""
        start = self.entry
        goal = self.exit_
        queue: deque[Tuple[int, int]] = deque([start])
        CellParent = Tuple[Tuple[int, int], int]
        came_from: Dict[Tuple[int, int], Optional[CellParent]] = {
            start: None
        }

        while queue:
            x, y = queue.popleft()
            if (x, y) == goal:
                break
            for i in range(4):
                if self.maze[y][x] & self.WALL_BITS[i]:
                    continue  # wall is closed
                nx, ny = x + self.DX[i], y + self.DY[i]
                if (nx, ny) not in came_from:
                    came_from[(nx, ny)] = ((x, y), i)
                    queue.append((nx, ny))

        # Reconstruct path
        if goal not in came_from:
            return []
        path: List[str] = []
        cur: Tuple[int, int] = goal
        while came_from[cur] is not None:
            prev, direction = came_from[cur]  # type: ignore[misc]
            path.append(self.DIR_CHARS[direction])
            cur = prev
        path.reverse()
        return path

    def _path_to_cells(self, path: List[str]) -> set[Tuple[int, int]]:
        """Convert a direction-string path to a set of (x, y) cells visited."""
        dir_map: Dict[str, int] = {"N": 0, "E": 1, "S": 2, "W": 3}
        cells: set[Tuple[int, int]] = set()
        x, y = self.entry
        cells.add((x, y))
        for ch in path:
            i = dir_map[ch]
            x += self.DX[i]
            y += self.DY[i]
            cells.add((x, y))
        return cells

    # ------------------------------------------------------------------
    # Animation helper
    # ------------------------------------------------------------------

    def _animate_frame(self) -> None:
        """Clear terminal and redraw maze for animation."""
        os.system("clear")
        self.display_ascii()
        time.sleep(0.03)
