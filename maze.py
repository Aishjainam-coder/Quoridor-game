import pygame
import numpy as np
import sys
import random
from pygame import gfxdraw
from typing import List, Tuple, Dict, Set, Optional
from collections import deque

class QuoridorGame:
    def __init__(self):
        pygame.init()
        
        # Game constants
        self.BOARD_SIZE = 9
        self.SQUARE_SIZE = 70
        self.WALL_THICKNESS = 12
        self.PAWN_SIZE = 28
        self.PADDING = 60
        
        # Screen calculations
        self.GAME_SIZE = self.BOARD_SIZE * self.SQUARE_SIZE + self.PADDING * 2
        self.PANEL_WIDTH = 320
        self.WIDTH = self.GAME_SIZE + self.PANEL_WIDTH
        self.HEIGHT = self.GAME_SIZE
        
        # Colors
        self.BACKGROUND = (242, 235, 225)
        self.BOARD_COLOR = (210, 197, 180)
        self.GRID_COLOR = (150, 137, 120)
        self.TEXT_COLOR = (80, 70, 60)
        self.DARK_TEXT = (50, 45, 40)
        self.BUTTON_COLOR = (110, 85, 65)
        self.BUTTON_HOVER = (140, 108, 85)
        self.BUTTON_TEXT = (245, 240, 230)
        
        self.PLAYER_COLORS = [
            (215, 90, 80),   # Red
            (80, 160, 225),  # Blue
            (95, 195, 130),  # Green
            (155, 105, 200)  # Purple
        ]
        self.WALL_COLORS = [
            (215, 90, 80, 200),   # Red walls
            (80, 160, 225, 200),  # Blue walls
            (95, 195, 130, 200),  # Green walls
            (155, 105, 200, 200)  # Purple walls
        ]
        self.POSSIBLE_MOVE = (245, 210, 100, 180)  # Highlighted moves
        
        # Screen setup
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Quoridor")
        self.clock = pygame.time.Clock()
        
        # Load and scale wood texture for board
        try:
            self.wood_texture = pygame.image.load("wood_texture.jpg")
            self.wood_texture = pygame.transform.scale(self.wood_texture, (self.GAME_SIZE, self.GAME_SIZE))
        except:
            self.wood_texture = None
        
        # Create rounded button surfaces
        self.button_surfaces = {}
        
        # Fonts
        self.title_font = pygame.font.SysFont("Arial", 38, bold=True)
        self.heading_font = pygame.font.SysFont("Arial", 28, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 22)
        self.small_font = pygame.font.SysFont("Arial", 18)
        
        # Game state
        self.num_players = 2
        self.initialize_game()

    def initialize_game(self):
        # Player positions on the board (row, col)
        self.player_positions = [
            (self.BOARD_SIZE - 1, self.BOARD_SIZE // 2),  # Player 1 (bottom)
            (0, self.BOARD_SIZE // 2),                    # Player 2 (top)
            (self.BOARD_SIZE // 2, 0),                    # Player 3 (left)
            (self.BOARD_SIZE // 2, self.BOARD_SIZE - 1)   # Player 4 (right)
        ][:self.num_players]
        
        # Keeps track of player's original side for win condition
        self.win_rows = [0, self.BOARD_SIZE - 1, None, None][:self.num_players]
        self.win_cols = [None, None, self.BOARD_SIZE - 1, 0][:self.num_players]
        
        # Walls per player
        self.walls_remaining = [10, 10, 5, 5][:self.num_players]
        
        # Player wall tracking - keep track of which player placed which wall
        self.player_walls = {i: [] for i in range(self.num_players)}
        
        # Horizontal and vertical walls on the board
        # We use (r, c) format to represent the intersection where the wall starts
        self.horizontal_walls: Set[Tuple[int, int]] = set()
        self.vertical_walls: Set[Tuple[int, int]] = set()
        
        # Game state
        self.current_player = 0
        self.game_over = False
        self.winner = None
        self.message = f"Player {self.current_player + 1}'s turn"
        
        # UI state
        self.selected_wall_type = "horizontal"  # or "vertical"
        self.wall_placement_mode = False
        self.possible_moves = self.get_possible_moves()
        self.hover_position = None
        self.hover_wall = None
        self.button_states = {}
    
    def get_possible_moves(self) -> List[Tuple[int, int]]:
        """Get all possible moves for the current player."""
        r, c = self.player_positions[self.current_player]
        possible = []
        
        # Check all four directions
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right
        
        for dr, dc in directions:
            new_r, new_c = r + dr, c + dc
            
            # Check if the move is within the board
            if not (0 <= new_r < self.BOARD_SIZE and 0 <= new_c < self.BOARD_SIZE):
                continue
            
            # Check if there's a wall blocking the move
            if dr == -1 and (r-1, c) in self.horizontal_walls:  # Moving up
                continue
            if dr == 1 and (r, c) in self.horizontal_walls:  # Moving down
                continue
            if dc == -1 and (r, c-1) in self.vertical_walls:  # Moving left
                continue
            if dc == 1 and (r, c) in self.vertical_walls:  # Moving right
                continue
            
            # Check if there's an opponent in the new position
            if (new_r, new_c) in self.player_positions:
                # Jump over opponent logic
                opponent_idx = self.player_positions.index((new_r, new_c))
                jump_r, jump_c = new_r + dr, new_c + dc
                
                # Check if jump position is valid (within board)
                if not (0 <= jump_r < self.BOARD_SIZE and 0 <= jump_c < self.BOARD_SIZE):
                    # Can't jump off board, try diagonal jumps
                    for side_dr, side_dc in [(-dr, dc), (dr, -dc)] if dr != 0 and dc != 0 else [(dr+1, dc), (dr-1, dc)] if dr != 0 else [(dr, dc+1), (dr, dc-1)]:
                        diag_r, diag_c = new_r + side_dr, new_c + side_dc
                        if 0 <= diag_r < self.BOARD_SIZE and 0 <= diag_c < self.BOARD_SIZE:
                            # Check wall blockage for diagonal move
                            if side_dr == -1 and (new_r-1, new_c) in self.horizontal_walls:
                                continue
                            if side_dr == 1 and (new_r, new_c) in self.horizontal_walls:
                                continue
                            if side_dc == -1 and (new_r, new_c-1) in self.vertical_walls:
                                continue
                            if side_dc == 1 and (new_r, new_c) in self.vertical_walls:
                                continue
                            if (diag_r, diag_c) not in self.player_positions:
                                possible.append((diag_r, diag_c))
                    continue
                
                # Check if there's a wall blocking the jump
                if dr == -1 and (new_r-1, new_c) in self.horizontal_walls:
                    continue
                if dr == 1 and (new_r, new_c) in self.horizontal_walls:
                    continue
                if dc == -1 and (new_r, new_c-1) in self.vertical_walls:
                    continue
                if dc == 1 and (new_r, new_c) in self.vertical_walls:
                    continue
                
                # Check if there's another player in the jump position
                if (jump_r, jump_c) in self.player_positions:
                    continue
                
                possible.append((jump_r, jump_c))
            else:
                possible.append((new_r, new_c))
        
        return possible
    
    def find_path_to_goal(self, player_idx, test_walls_h=None, test_walls_v=None):
        """Check if player can reach their goal with BFS pathfinding."""
        if test_walls_h is None:
            test_walls_h = self.horizontal_walls.copy()
        if test_walls_v is None:
            test_walls_v = self.vertical_walls.copy()
        
        p_r, p_c = self.player_positions[player_idx]
        
        # BFS to find a path to the goal
        queue = deque([(p_r, p_c)])
        visited = set([(p_r, p_c)])
        
        while queue:
            curr_r, curr_c = queue.popleft()
            
            # Check if at goal
            if (self.win_rows[player_idx] is not None and curr_r == self.win_rows[player_idx]) or \
               (self.win_cols[player_idx] is not None and curr_c == self.win_cols[player_idx]):
                return True
            
            # Try all four directions
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right
            
            for dr, dc in directions:
                new_r, new_c = curr_r + dr, curr_c + dc
                
                # Check if the move is within the board
                if not (0 <= new_r < self.BOARD_SIZE and 0 <= new_c < self.BOARD_SIZE):
                    continue
                
                # Check if there's a wall blocking the move
                if dr == -1 and (curr_r-1, curr_c) in test_walls_h:  # Moving up
                    continue
                if dr == 1 and (curr_r, curr_c) in test_walls_h:  # Moving down
                    continue
                if dc == -1 and (curr_r, curr_c-1) in test_walls_v:  # Moving left
                    continue
                if dc == 1 and (curr_r, curr_c) in test_walls_v:  # Moving right
                    continue
                
                # Process the new position
                if (new_r, new_c) not in visited:
                    queue.append((new_r, new_c))
                    visited.add((new_r, new_c))
        
        return False  # No path found
    
    def is_valid_wall_placement(self, r, c, wall_type):
        """Check if placing a wall at (r, c) is valid."""
        # Check board boundaries
        if not (0 <= r < self.BOARD_SIZE - 1 and 0 <= c < self.BOARD_SIZE - 1):
            return False
        
        # Check if wall already exists
        if wall_type == "horizontal":
            if (r, c) in self.horizontal_walls or (r, c+1) in self.horizontal_walls:
                return False
        else:  # vertical
            if (r, c) in self.vertical_walls or (r+1, c) in self.vertical_walls:
                return False
        
        # Check for intersecting walls
        if wall_type == "horizontal" and ((r, c) in self.vertical_walls and (r+1, c) in self.vertical_walls):
            return False
        if wall_type == "vertical" and ((r, c) in self.horizontal_walls and (r, c+1) in self.horizontal_walls):
            return False
        
        # Check if wall cuts off a player's path to goal (critically important!)
        test_walls_h = self.horizontal_walls.copy()
        test_walls_v = self.vertical_walls.copy()
        
        if wall_type == "horizontal":
            test_walls_h.add((r, c))
            test_walls_h.add((r, c+1))
        else:
            test_walls_v.add((r, c))
            test_walls_v.add((r+1, c))
        
        # Check if each player can reach their goal
        for p_idx in range(self.num_players):
            # Skip if player has already won
            if (self.win_rows[p_idx] is not None and self.player_positions[p_idx][0] == self.win_rows[p_idx]) or \
               (self.win_cols[p_idx] is not None and self.player_positions[p_idx][1] == self.win_cols[p_idx]):
                continue
            
            if not self.find_path_to_goal(p_idx, test_walls_h, test_walls_v):
                return False
        
        return True
    
    def place_wall(self, r, c, wall_type):
        """Place a wall at position (r, c)."""
        if self.walls_remaining[self.current_player] <= 0:
            self.message = "No walls remaining!"
            return False
        
        if not self.is_valid_wall_placement(r, c, wall_type):
            self.message = "Invalid wall placement! Can't block all paths."
            return False
        
        if wall_type == "horizontal":
            self.horizontal_walls.add((r, c))
            self.horizontal_walls.add((r, c+1))
            self.player_walls[self.current_player].append(("h", r, c))
        else:  # vertical
            self.vertical_walls.add((r, c))
            self.vertical_walls.add((r+1, c))
            self.player_walls[self.current_player].append(("v", r, c))
        
        self.walls_remaining[self.current_player] -= 1
        self.next_turn()
        return True
    
    def move_player(self, r, c):
        """Move the current player to position (r, c)."""
        if (r, c) not in self.get_possible_moves():
            self.message = "Invalid move!"
            return False
        
        self.player_positions[self.current_player] = (r, c)
        
        # Check for win condition
        p_r, p_c = r, c
        if (self.win_rows[self.current_player] is not None and p_r == self.win_rows[self.current_player]) or \
           (self.win_cols[self.current_player] is not None and p_c == self.win_cols[self.current_player]):
            self.game_over = True
            self.winner = self.current_player
            self.message = f"Player {self.current_player + 1} wins!"
            return True
        
        self.next_turn()
        return True
    
    def next_turn(self):
        """Move to the next player's turn."""
        if not self.game_over:
            self.current_player = (self.current_player + 1) % self.num_players
            self.message = f"Player {self.current_player + 1}'s turn"
            self.possible_moves = self.get_possible_moves()
            self.hover_position = None
            self.hover_wall = None

    def draw_rounded_rect(self, surface, rect, color, radius=0.4):
        """Draw a rounded rectangle on the given surface."""
        rect = pygame.Rect(rect)
        color = pygame.Color(*color)
        alpha = color.a
        color.a = 0
        pos = rect.topleft
        rect.topleft = 0, 0
        rectangle = pygame.Surface(rect.size, pygame.SRCALPHA)
        
        circle = pygame.Surface([min(rect.size)*3]*2, pygame.SRCALPHA)
        pygame.draw.ellipse(circle, (0, 0, 0), circle.get_rect(), 0)
        circle = pygame.transform.smoothscale(circle, [int(min(rect.size)*radius)]*2)
        
        radius = rectangle.blit(circle, (0, 0))
        radius.bottomright = rect.bottomright
        rectangle.blit(circle, radius)
        radius.topright = rect.topright
        rectangle.blit(circle, radius)
        radius.bottomleft = rect.bottomleft
        rectangle.blit(circle, radius)
        
        rectangle.fill((0, 0, 0), rect.inflate(-radius.w, 0))
        rectangle.fill((0, 0, 0), rect.inflate(0, -radius.h))
        
        rectangle.fill(color, special_flags=pygame.BLEND_RGBA_MAX)
        rectangle.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MIN)
        
        return surface.blit(rectangle, pos)
    
    def draw_board(self):
        """Draw the game board with improved visuals."""
        self.screen.fill(self.BACKGROUND)
        
        # Draw board background
        board_rect = pygame.Rect(
            self.PADDING - 20, 
            self.PADDING - 20, 
            self.BOARD_SIZE * self.SQUARE_SIZE + 40, 
            self.BOARD_SIZE * self.SQUARE_SIZE + 40
        )
        
        if self.wood_texture:
            self.screen.blit(self.wood_texture, (self.PADDING - 20, self.PADDING - 20))
        else:
            self.draw_rounded_rect(self.screen, board_rect, self.BOARD_COLOR, 0.1)
        
        # Draw grid
        for i in range(self.BOARD_SIZE + 1):
            x = self.PADDING + i * self.SQUARE_SIZE
            y = self.PADDING + i * self.SQUARE_SIZE
            
            # Draw horizontal lines
            pygame.draw.line(
                self.screen, 
                self.GRID_COLOR, 
                (self.PADDING, y), 
                (self.PADDING + self.BOARD_SIZE * self.SQUARE_SIZE, y), 
                2
            )
            
            # Draw vertical lines
            pygame.draw.line(
                self.screen, 
                self.GRID_COLOR, 
                (x, self.PADDING), 
                (x, self.PADDING + self.BOARD_SIZE * self.SQUARE_SIZE), 
                2
            )
        
        # Draw horizontal walls
        for r, c in self.horizontal_walls:
            x = self.PADDING + c * self.SQUARE_SIZE
            y = self.PADDING + (r + 1) * self.SQUARE_SIZE - self.WALL_THICKNESS // 2
            
            # Find which player placed this wall
            wall_owner = 0  # Default to first player
            for player_idx, walls in self.player_walls.items():
                if ("h", r, c) in walls or ("h", r, c-1) in walls:
                    wall_owner = player_idx
                    break
            
            # Draw wall with rounded corners
            self.draw_rounded_rect(
                self.screen,
                (x, y, self.SQUARE_SIZE * 2, self.WALL_THICKNESS),
                self.WALL_COLORS[wall_owner],
                0.5
            )
        
        # Draw vertical walls
        for r, c in self.vertical_walls:
            x = self.PADDING + (c + 1) * self.SQUARE_SIZE - self.WALL_THICKNESS // 2
            y = self.PADDING + r * self.SQUARE_SIZE
            
            # Find which player placed this wall
            wall_owner = 1  # Default to second player
            for player_idx, walls in self.player_walls.items():
                if ("v", r, c) in walls or ("v", r-1, c) in walls:
                    wall_owner = player_idx
                    break
            
            # Draw wall with rounded corners
            self.draw_rounded_rect(
                self.screen,
                (x, y, self.WALL_THICKNESS, self.SQUARE_SIZE * 2),
                self.WALL_COLORS[wall_owner],
                0.5
            )
        
        # Draw hovering wall if in wall placement mode
        if self.wall_placement_mode and self.hover_wall:
            r, c, wall_type = self.hover_wall
            
            if 0 <= r < self.BOARD_SIZE - 1 and 0 <= c < self.BOARD_SIZE - 1:
                is_valid = self.is_valid_wall_placement(r, c, wall_type)
                color = (100, 200, 100, 150) if is_valid else (200, 100, 100, 150)
                
                if wall_type == "horizontal":
                    x = self.PADDING + c * self.SQUARE_SIZE
                    y = self.PADDING + (r + 1) * self.SQUARE_SIZE - self.WALL_THICKNESS // 2
                    self.draw_rounded_rect(
                        self.screen,
                        (x, y, self.SQUARE_SIZE * 2, self.WALL_THICKNESS),
                        color,
                        0.5
                    )
                else:  # vertical
                    x = self.PADDING + (c + 1) * self.SQUARE_SIZE - self.WALL_THICKNESS // 2
                    y = self.PADDING + r * self.SQUARE_SIZE
                    self.draw_rounded_rect(
                        self.screen,
                        (x, y, self.WALL_THICKNESS, self.SQUARE_SIZE * 2),
                        color,
                        0.5
                    )
        
        # Draw possible moves
        if not self.wall_placement_mode and not self.game_over:
            for r, c in self.possible_moves:
                x = self.PADDING + c * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
                y = self.PADDING + r * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
                
                # Draw highlighted move circle
                pygame.draw.circle(
                    self.screen,
                    self.POSSIBLE_MOVE,
                    (x, y),
                    self.PAWN_SIZE // 2
                )
        
        # Draw pawns (players)
        for i, (r, c) in enumerate(self.player_positions):
            x = self.PADDING + c * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
            y = self.PADDING + r * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
            
            # Draw pawn shadow (for 3D effect)
            pygame.draw.circle(
                self.screen,
                (50, 50, 50, 100),
                (x+2, y+2),
                self.PAWN_SIZE
            )
            
            # Draw pawn body
            pygame.draw.circle(
                self.screen,
                self.PLAYER_COLORS[i],
                (x, y),
                self.PAWN_SIZE
            )
            
            # Draw pawn highlight
            pygame.draw.circle(
                self.screen,
                (255, 255, 255, 180),
                (x-5, y-5),
                self.PAWN_SIZE//3
            )
            
            # Draw player number
            text = self.heading_font.render(str(i + 1), True, (255, 255, 255))
            text_rect = text.get_rect(center=(x, y))
            self.screen.blit(text, text_rect)
    
    def create_button(self, rect, text, color, hover_color):
        """Create a button surface with hover effect."""
        key = (rect.x, rect.y, rect.width, rect.height, text)
        
        # Check if mouse is hovering over button
        mouse_pos = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mouse_pos)
        
        # Set button color based on hover state
        button_color = hover_color if hovered else color
        
        # Store button state
        self.button_states[key] = hovered
        
        # Draw the button
        self.draw_rounded_rect(self.screen, rect, button_color, 0.3)
        
        # Draw the button text
        text_surf = self.text_font.render(text, True, self.BUTTON_TEXT)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)
        
        return rect
    
    def draw_ui(self):
        """Draw the game UI panel with improved visuals."""
        panel_x = self.GAME_SIZE
        panel_y = 0
        
        # Draw panel background
        pygame.draw.rect(
            self.screen,
            (220, 210, 200),
            (panel_x, panel_y, self.PANEL_WIDTH, self.HEIGHT)
        )
        
        # Draw decorative header bar
        pygame.draw.rect(
            self.screen,
            self.BUTTON_COLOR,
            (panel_x, 0, self.PANEL_WIDTH, 75)
        )
        
        # Draw title
        title = self.title_font.render("QUORIDOR", True, self.BUTTON_TEXT)
        title_rect = title.get_rect(center=(panel_x + self.PANEL_WIDTH // 2, 37))
        self.screen.blit(title, title_rect)
        
        # Draw current player info with colored indicator
        y_pos = 95
        player_indicator = pygame.Rect(panel_x + 25, y_pos, 15, 30)
        pygame.draw.rect(
            self.screen,
            self.PLAYER_COLORS[self.current_player],
            player_indicator,
            0,
            5
        )
        
        player_text = self.heading_font.render(
            f"Player {self.current_player + 1}'s Turn" if not self.game_over else f"Player {self.winner + 1} Wins!",
            True,
            self.PLAYER_COLORS[self.current_player]
        )
        self.screen.blit(player_text, (panel_x + 50, y_pos))
        
        # Draw message with status background
        message_bg = pygame.Rect(panel_x + 25, y_pos + 40, self.PANEL_WIDTH - 50, 40)
        self.draw_rounded_rect(self.screen, message_bg, (240, 230, 220), 0.3)
        
        message_text = self.text_font.render(self.message, True, self.TEXT_COLOR)
        message_rect = message_text.get_rect(center=(panel_x + self.PANEL_WIDTH // 2, y_pos + 60))
        self.screen.blit(message_text, message_rect)
        
        # Draw walls remaining with colored indicators
        y_offset = y_pos + 100
        walls_title = self.heading_font.render("Walls Remaining", True, self.TEXT_COLOR)
        self.screen.blit(walls_title, (panel_x + 25, y_offset))
        
        y_offset += 40
        for i in range(self.num_players):
            # Player indicator
            player_dot = pygame.Rect(panel_x + 25, y_offset, 15, 15)
            pygame.draw.rect(
                self.screen,
                self.PLAYER_COLORS[i],
                player_dot,
                0,
                7
            )
            
            # Player wall count
            walls_text = self.text_font.render(f"Player {i + 1}: {self.walls_remaining[i]}", True, self.TEXT_COLOR)
            self.screen.blit(walls_text, (panel_x + 50, y_offset - 3))
            
            # Wall remaining indicators
            for w in range(min(10, self.walls_remaining[i])):
                wall_x = panel_x + 180 + (w % 5) * 20
                wall_y = y_offset + (w // 5) * 10
                pygame.draw.rect(
                    self.screen,
                    self.PLAYER_COLORS[i],
                    (wall_x, wall_y, 15, 5),
                    0,
                    2
                )
            
            y_offset += 30
        
        # Draw mode buttons
        y_offset += 20
        mode_title = self.heading_font.render("Game Mode", True, self.TEXT_COLOR)
        self.screen.blit(mode_title, (panel_x + 25, y_offset))
        y_offset += 40
        
        move_button = pygame.Rect(panel_x + 25, y_offset, 125, 45)
        move_button = self.create_button(
            move_button,
            "Move Mode",
            (150, 150, 150) if not self.wall_placement_mode else self.BUTTON_COLOR,
            (170, 170, 170) if not self.wall_placement_mode else self.BUTTON_HOVER
        )
        
        wall_button = pygame.Rect(panel_x + 165, y_offset, 125, 45)
        wall_button = self.create_button(
            wall_button,
            "Wall Mode",
            (150, 150, 150) if self.wall_placement_mode else self.BUTTON_COLOR,
            (170, 170, 170) if self.wall_placement_mode else self.BUTTON_HOVER
        )
        
        
        # Draw wall type buttons (only when in wall placement mode)
        if self.wall_placement_mode:
            h_wall_button = pygame.Rect(panel_x + 30, y_offset + 90, 110, 40)
            pygame.draw.rect(
                self.screen,
                (200, 200, 200) if self.selected_wall_type != "horizontal" else (150, 150, 150),
                h_wall_button,
                0,
                5
            )
            h_wall_text = self.text_font.render("Horizontal", True, self.TEXT_COLOR)
            h_wall_text_rect = h_wall_text.get_rect(center=h_wall_button.center)
            self.screen.blit(h_wall_text, h_wall_text_rect)
            
            v_wall_button = pygame.Rect(panel_x + 160, y_offset + 90, 110, 40)
            pygame.draw.rect(
                self.screen,
                (200, 200, 200) if self.selected_wall_type != "vertical" else (150, 150, 150),
                v_wall_button,
                0,
                5
            )
            v_wall_text = self.text_font.render("Vertical", True, self.TEXT_COLOR)
            v_wall_text_rect = v_wall_text.get_rect(center=v_wall_button.center)
            self.screen.blit(v_wall_text, v_wall_text_rect)
        
        # Draw instructions
        instructions_y = y_offset + 150
        instructions = [
            "Instructions:",
            "1. Move your pawn to the opposite side",
            "2. Place walls to block opponents",
            "3. You can't completely block paths",
            "4. You can jump over adjacent pawns"
        ]
        
        for i, instruction in enumerate(instructions):
            instr_text = self.small_font.render(instruction, True, self.TEXT_COLOR)
            self.screen.blit(instr_text, (panel_x + 30, instructions_y + i * 25))
        
        # Draw restart button
        restart_button = pygame.Rect(panel_x + 30, self.HEIGHT - 70, self.PANEL_WIDTH - 60, 40)
        pygame.draw.rect(
            self.screen,
            (52, 152, 219),
            restart_button,
            0,
            5
        )
        restart_text = self.heading_font.render("New Game", True, (255, 255, 255))
        restart_text_rect = restart_text.get_rect(center=restart_button.center)
        self.screen.blit(restart_text, restart_text_rect)
        
        return {
            "move_button": move_button,
            "wall_button": wall_button,
            "h_wall_button": h_wall_button if self.wall_placement_mode else None,
            "v_wall_button": v_wall_button if self.wall_placement_mode else None,
            "restart_button": restart_button
        }
    
    def run(self):
        """Main game loop."""
        running = True
        
        while running:
            ui_elements = self.draw_board()
            ui_buttons = self.draw_ui()
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Check UI button clicks
                    if ui_buttons["move_button"].collidepoint(mouse_pos):
                        self.wall_placement_mode = False
                    elif ui_buttons["wall_button"].collidepoint(mouse_pos):
                        self.wall_placement_mode = True
                    elif ui_buttons["restart_button"].collidepoint(mouse_pos):
                        self.initialize_game()
                    elif ui_buttons["h_wall_button"] and ui_buttons["h_wall_button"].collidepoint(mouse_pos):
                        self.selected_wall_type = "horizontal"
                    elif ui_buttons["v_wall_button"] and ui_buttons["v_wall_button"].collidepoint(mouse_pos):
                        self.selected_wall_type = "vertical"
                    
                    # Check game board clicks
                    elif self.PADDING <= mouse_pos[0] <= self.GAME_SIZE - self.PADDING and \
                         self.PADDING <= mouse_pos[1] <= self.GAME_SIZE - self.PADDING:
                        
                        # Convert mouse position to board coordinates
                        c = (mouse_pos[0] - self.PADDING) // self.SQUARE_SIZE
                        r = (mouse_pos[1] - self.PADDING) // self.SQUARE_SIZE
                        
                        if not self.game_over:
                            if not self.wall_placement_mode:
                                # Move player
                                self.move_player(r, c)
                            else:
                                # Place wall at intersection
                                # Find the nearest intersection
                                x_remainder = (mouse_pos[0] - self.PADDING) % self.SQUARE_SIZE
                                y_remainder = (mouse_pos[1] - self.PADDING) % self.SQUARE_SIZE
                                
                                if x_remainder < self.SQUARE_SIZE // 2:
                                    wall_c = c
                                else:
                                    wall_c = c
                                
                                if y_remainder < self.SQUARE_SIZE // 2:
                                    wall_r = r
                                else:
                                    wall_r = r
                                
                                # Adjust wall coordinates to be in valid range
                                wall_r = max(0, min(wall_r, self.BOARD_SIZE - 2))
                                wall_c = max(0, min(wall_c, self.BOARD_SIZE - 2))
                                
                                self.place_wall(wall_r, wall_c, self.selected_wall_type)
            
            self.clock.tick(60)


if __name__ == "__main__":
    game = QuoridorGame()
    game.run()