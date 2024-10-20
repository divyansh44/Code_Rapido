import pygame
import sys
from collections import deque
import random

# Initialize Pygame
pygame.init()

# Constants
GRID_SIZE = 5
CELL_SIZE = 100
MARGIN = 5
WINDOW_SIZE = (GRID_SIZE * (CELL_SIZE + MARGIN) + MARGIN, GRID_SIZE * (CELL_SIZE + MARGIN) + MARGIN + 150)
BACKGROUND_COLOR = (30, 30, 30)
GRID_COLOR = (60, 60, 60)
PLAYER_COLORS = [(255, 50, 50), (50, 50, 255)]  # Red, Blue
FONT = pygame.font.Font(None, 36)

# Particle animation
PARTICLE_SPEED = 5
PARTICLE_SIZE = 10

class Particle:
    def __init__(self, start, end, color):
        self.pos = list(start)
        self.end = end
        self.color = color
        self.done = False

    def update(self):
        dx = self.end[0] - self.pos[0]
        dy = self.end[1] - self.pos[1]
        distance = (dx**2 + dy**2)**0.5
        if distance < PARTICLE_SPEED:
            self.pos = list(self.end)
            self.done = True
        else:
            self.pos[0] += dx / distance * PARTICLE_SPEED
            self.pos[1] += dy / distance * PARTICLE_SPEED

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.pos[0]), int(self.pos[1])), PARTICLE_SIZE)

class QuantumSquare:
    def __init__(self):
        self.particles = 0
        self.owner = None

    def add_particle(self, player):
        self.particles += 1
        self.owner = player
        return self.particles == 4

    def reset(self):
        self.particles = 0
        self.owner = None

class QuantumSquares:
    def __init__(self, size=GRID_SIZE):
        self.size = size
        self.grid = [[QuantumSquare() for _ in range(size)] for _ in range(size)]
        self.scores = [0, 0]
        self.current_player = 0
        self.game_over = False
        self.particles = []

    def add_particle(self, row, col):
        if self.game_over or not (0 <= row < self.size and 0 <= col < self.size):
            return False

        square = self.grid[row][col]
        if square.add_particle(self.current_player):
            self.scores[self.current_player] += 1
            self.collapse(row, col)
        else:
            center = ((col * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2),
                     (row * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2))
            self.particles.append(Particle(center, center, PLAYER_COLORS[self.current_player]))

        self.check_game_over()
        if not self.game_over:
            self.current_player = 1 - self.current_player
        return True
 
    def collapse(self, row, col):
     queue = deque([(row, col)])
     while queue:
        r, c = queue.popleft()
        particles = self.grid[r][c].particles
        self.grid[r][c].reset()

        center = ((c * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2),
                  (r * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2))

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                square = self.grid[nr][nc]
                old_owner = square.owner

                # Check if the square reaches 4 particles
                if square.add_particle(self.current_player):
                    if old_owner is not None and old_owner != self.current_player:
                        # Decrease the score of the previous owner if the square collapses
                        self.scores[old_owner] -= 1
                    # Increment the score of the current player since they caused the collapse
                    self.scores[self.current_player] += 1
                    queue.append((nr, nc))
                
                # Now, check ownership and keep ownership unchanged if square is already owned
                if old_owner is not None:
                    # If the square is owned, particles moving in will not change ownership
                    square.owner = old_owner
                    particle_color = PLAYER_COLORS[old_owner]  # Keep the existing owner's color
                else:
                    # If not owned, assign ownership to the current player
                    particle_color = PLAYER_COLORS[self.current_player]

                # Add particle animation to the list
                end = ((nc * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2),
                      (nr * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2))
                self.particles.append(Particle(center, end, particle_color))

    def check_game_over(self):
        if max(self.scores) >= 10 or all(square.particles == 4 for row in self.grid for square in row):
            self.game_over = True

    def get_valid_moves(self):
        return [(r, c) for r in range(self.size) for c in range(self.size) if self.grid[r][c].particles < 4]

    def evaluate_board(self):
        score = self.scores[0] - self.scores[1]
        for r in range(self.size):
            for c in range(self.size):
                square = self.grid[r][c]
                if square.owner == 0:
                    score += square.particles * 0.1
                elif square.owner == 1:
                    score -= square.particles * 0.1
        return score

    def update_particles(self):
        self.particles = [p for p in self.particles if not p.done]
        for particle in self.particles:
            particle.update()

class AIPlayer:
    def __init__(self, player_id):
        self.player_id = player_id

    def get_move(self, game):
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            return None
            
        best_move = None
        best_score = float('-inf') if self.player_id == 0 else float('inf')

        for move in valid_moves:
            score = self.evaluate_move(game, move)
            if (self.player_id == 0 and score > best_score) or (self.player_id == 1 and score < best_score):
                best_score = score
                best_move = move

        return best_move

    def evaluate_move(self, game, move):
        game_copy = self.copy_game(game)
        game_copy.add_particle(move[0], move[1])
        
        score = game_copy.evaluate_board()
        
        r, c = move
        square = game_copy.grid[r][c]
        
        if square.particles == 4:
            score += 10 if self.player_id == 0 else -10
        
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < game.size and 0 <= nc < game.size:
                if game_copy.grid[nr][nc].particles == 3 and game_copy.grid[nr][nc].owner != self.player_id:
                    score -= 5 if self.player_id == 0 else 5
        
        center = game.size // 2
        distance_to_center = abs(r - center) + abs(c - center)
        score -= distance_to_center * 0.1
        
        return score

    def copy_game(self, game):
        new_game = QuantumSquares(game.size)
        for r in range(game.size):
            for c in range(game.size):
                new_game.grid[r][c].particles = game.grid[r][c].particles
                new_game.grid[r][c].owner = game.grid[r][c].owner
        new_game.scores = game.scores.copy()
        new_game.current_player = game.current_player
        new_game.game_over = game.game_over
        return new_game

class Button:
    def __init__(self, x, y, width, height, text, color, text_color, action):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.action = action

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        text_surface = FONT.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.action()

class QuantumSquaresGUI:
    def __init__(self):
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Quantum Squares")
        self.clock = pygame.time.Clock()
        self.game = None
        self.ai_player = None
        self.opponent_type = None
        self.create_menu()

    def create_menu(self):
        self.menu_buttons = [
            Button(WINDOW_SIZE[0] // 4, WINDOW_SIZE[1] // 2, WINDOW_SIZE[0] // 2, 50, 
                  "Play vs Human", (100, 100, 100), (255, 255, 255), 
                  lambda: self.start_game("human")),
            Button(WINDOW_SIZE[0] // 4, WINDOW_SIZE[1] // 2 + 70, WINDOW_SIZE[0] // 2, 50, 
                  "Play vs AI", (100, 100, 100), (255, 255, 255), 
                  lambda: self.start_game("ai"))
        ]

    def start_game(self, opponent):
        self.game = QuantumSquares()
        self.opponent_type = opponent
        if opponent == "ai":
            self.ai_player = AIPlayer(1)

    def run(self):
        while True:
            if self.game is None:
                self.show_menu()
            else:
                self.play_game()

    def show_menu(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            for button in self.menu_buttons:
                button.handle_event(event)

        self.screen.fill(BACKGROUND_COLOR)
        # Draw title
        title = FONT.render("Quantum Squares", True, (255, 255, 255))
        title_rect = title.get_rect(center=(WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 3))
        self.screen.blit(title, title_rect)
        
        for button in self.menu_buttons:
            button.draw(self.screen)
        pygame.display.flip()
        self.clock.tick(60)

    def play_game(self):
        self.handle_events()
        self.update()
        self.draw()
        pygame.display.flip()
        self.clock.tick(60)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and not self.game.game_over:
                self.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.game = None
                self.create_menu()

    def handle_click(self, pos):
        if self.game.current_player == 0 or (self.opponent_type == "human" and self.game.current_player == 1):
            col = pos[0] // (CELL_SIZE + MARGIN)
            row = pos[1] // (CELL_SIZE + MARGIN)
            if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
                self.game.add_particle(row, col)

    def update(self):
        if self.game:
            self.game.update_particles()
            if not self.game.game_over and self.opponent_type == "ai" and self.game.current_player == 1:
                move = self.ai_player.get_move(self.game)
                if move:
                    self.game.add_particle(move[0], move[1])

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        self.draw_grid()
        self.draw_particles()
        self.draw_info()

    def draw_grid(self):
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = col * (CELL_SIZE + MARGIN) + MARGIN
                y = row * (CELL_SIZE + MARGIN) + MARGIN
                square = self.game.grid[row][col]
                color = GRID_COLOR if square.owner is None else PLAYER_COLORS[square.owner]
                pygame.draw.rect(self.screen, color, (x, y, CELL_SIZE, CELL_SIZE))
                if square.particles > 0:
                    text = FONT.render(str(square.particles), True, (255, 255, 255))
                    text_rect = text.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                    self.screen.blit(text, text_rect)

    def draw_particles(self):
        for particle in self.game.particles:
            particle.draw(self.screen)

    def draw_info(self):
        info_y = GRID_SIZE * (CELL_SIZE + MARGIN) + MARGIN
        player_text = f"Player {self.game.current_player + 1}'s Turn" if not self.game.game_over else "Game Over"
        player_color = PLAYER_COLORS[self.game.current_player]
        text = FONT.render(player_text, True, player_color)
        self.screen.blit(text, (MARGIN, info_y + 10))

        score_text = f"Red: {self.game.scores[0]}  Blue: {self.game.scores[1]}"
        text = FONT.render(score_text, True, (255, 255, 255))
        self.screen.blit(text, (MARGIN, info_y + 50))

        if self.game.game_over:
            if self.game.scores[0] > self.game.scores[1]:
                winner = "Red Wins!"
            elif self.game.scores[1] > self.game.scores[0]:
                winner = "Blue Wins!"
            else:
                winner = "It's a Tie!"
            text = FONT.render(winner, True, (255, 255, 0))
            text_rect = text.get_rect(center=(WINDOW_SIZE[0] // 2, info_y + 90))
            self.screen.blit(text, text_rect)

        restart_text = FONT.render("Press 'R' to Restart", True, (200, 200, 200))
        self.screen.blit(restart_text, (MARGIN, WINDOW_SIZE[1] - 40))

def main():
    try:
        # Initialize pygame mixer to avoid audio driver issues
        pygame.mixer.init()
        
        # Create and run the game
        game = QuantumSquaresGUI()
        game.run()
    except Exception as e:
        print(f"An error occurred: {e}")
        pygame.quit()
        sys.exit(1)

if __name__ == "__main__":
    main()