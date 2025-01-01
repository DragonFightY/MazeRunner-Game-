import pygame
import random
import math
import json
import os

# Initialize Pygame and constants
WIDTH, HEIGHT = 800, 600
CELL_SIZE = 40
BLACK = (0, 0, 0)
WALL_COLOR = (41, 50, 65)
PATH_COLOR = (152, 193, 217)
PLAYER_COLOR = (255, 89, 94)
COIN_COLOR = (255, 222, 89)
BORDER_COLOR = (90, 111, 140)

pygame.init()
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Maze Runner")
FONT = pygame.font.Font(None, 36)
LARGE_FONT = pygame.font.Font(None, 48)

def generate_maze(difficulty=1.0):
    cols = WIDTH // CELL_SIZE
    rows = HEIGHT // CELL_SIZE
    maze = [[1 for _ in range(cols)] for _ in range(rows)]
    
    def carve_path(x, y):
        maze[y][x] = 0
        directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
        random.shuffle(directions)
        
        for dx, dy in directions:
            new_x, new_y = x + dx, y + dy
            if (0 <= new_x < cols and 0 <= new_y < rows and 
                maze[new_y][new_x] == 1 and
                random.random() > (difficulty * 0.1)):
                maze[y + dy//2][x + dx//2] = 0
                maze[new_y][new_x] = 0
                carve_path(new_x, new_y)

    carve_path(1, 1)
    maze[1][1] = maze[1][0] = 0
    maze[rows-2][cols-2] = maze[rows-2][cols-1] = 0
    return maze

class GameState:
    def __init__(self):
        self.state = 'menu'
        self.load_save()
        
    def load_save(self):
        self.data = {
            'coins': 0,
            'visibility_radius': 3,
            'maze_difficulty': 1.0
        }
        if os.path.exists('save.json'):
            try:
                with open('save.json', 'r') as f:
                    self.data = json.load(f)
            except:
                pass
                
    def save_game(self):
        with open('save.json', 'w') as f:
            json.dump(self.data, f)

class Menu:
    def __init__(self):
        self.buttons = {
            'play': pygame.Rect(WIDTH//2 - 100, 200, 200, 50),
            'upgrades': pygame.Rect(WIDTH//2 - 100, 300, 200, 50)
        }
        
    def draw(self, screen):
        screen.fill(BLACK)
        title = LARGE_FONT.render("Neon Maze Explorer", True, COIN_COLOR)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
        
        for text, rect in self.buttons.items():
            pygame.draw.rect(screen, WALL_COLOR, rect, border_radius=10)
            text_surf = FONT.render(text.title(), True, COIN_COLOR)
            screen.blit(text_surf, (rect.centerx - text_surf.get_width()//2, 
                                  rect.centery - text_surf.get_height()//2))

class UpgradeMenu:
    def __init__(self):
        self.buttons = {
            'visibility': pygame.Rect(WIDTH//2 - 150, 200, 300, 50),
            'difficulty': pygame.Rect(WIDTH//2 - 150, 300, 300, 50),
            'back': pygame.Rect(WIDTH//2 - 100, 500, 200, 50)
        }
        
    def draw(self, screen, game_state):
        screen.fill(BLACK)
        coins = FONT.render(f"Coins: {game_state.data['coins']}", True, COIN_COLOR)
        screen.blit(coins, (20, 20))
        
        costs = {
            'visibility': 10,
            'difficulty': 15
        }
        
        for upgrade, rect in self.buttons.items():
            if upgrade == 'back':
                pygame.draw.rect(screen, WALL_COLOR, rect, border_radius=10)
                text = FONT.render("Back", True, COIN_COLOR)
            else:
                cost = costs.get(upgrade, 0)
                pygame.draw.rect(screen, WALL_COLOR, rect, border_radius=10)
                if upgrade == 'visibility':
                    text = FONT.render(f"Visibility +1 (Cost: {cost})", True, COIN_COLOR)
                else:
                    text = FONT.render(f"Reduce Difficulty (Cost: {cost})", True, COIN_COLOR)
            
            screen.blit(text, (rect.centerx - text.get_width()//2, 
                              rect.centery - text.get_height()//2))
            
    def handle_click(self, pos, game_state):
        for upgrade, rect in self.buttons.items():
            if rect.collidepoint(pos):
                if upgrade == 'back':
                    return 'menu'
                elif upgrade == 'visibility' and game_state.data['coins'] >= 10:
                    game_state.data['coins'] -= 10
                    game_state.data['visibility_radius'] += 1
                elif upgrade == 'difficulty' and game_state.data['coins'] >= 15:
                    game_state.data['coins'] -= 15
                    game_state.data['maze_difficulty'] = max(0.1, 
                                                           game_state.data['maze_difficulty'] - 0.1)
                game_state.save_game()
        return 'upgrades'

class Coin:
    def __init__(self, maze):
        self.place_coin(maze)
        self.size = CELL_SIZE // 4
        self.angle = 0
        
    def place_coin(self, maze):
        """Places the coin in a random walkable cell of the maze."""
        while True:
            y = random.randrange(len(maze))
            x = random.randrange(len(maze[0]))
            if maze[y][x] == 0:
                self.x = x * CELL_SIZE + CELL_SIZE // 2
                self.y = y * CELL_SIZE + CELL_SIZE // 2
                self.grid_x = x
                self.grid_y = y
                break

    def draw(self, player, visibility_radius):
        """Draws the glowing, pulsating coin if within the player's visibility radius."""
        if not self.is_visible(player, visibility_radius):
            return
        
        # Pulsating and glowing effect
        self.angle += 0.1
        oscillation = math.sin(self.angle) * 4
        glow_size = self.size + oscillation
        
        for layer in range(3):  # Create a multi-layer glow effect
            alpha = 100 - (layer * 30)
            glow_surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(
                glow_surface,
                (*COIN_COLOR, alpha),
                (CELL_SIZE // 2, CELL_SIZE // 2),
                int(glow_size + layer * 2)
            )
            SCREEN.blit(glow_surface, (self.x - CELL_SIZE // 2, self.y - CELL_SIZE // 2))
        
        # Core coin
        pygame.draw.circle(SCREEN, COIN_COLOR, (self.x, self.y), int(self.size + oscillation))

    def is_visible(self, player, visibility_radius):
        """Checks if the coin is within the player's visibility radius."""
        distance = math.sqrt((self.grid_x - player.grid_x) ** 2 + (self.grid_y - player.grid_y) ** 2)
        return distance <= visibility_radius

class Player:
    def __init__(self):
        self.reset_position()
        self.color = PLAYER_COLOR
        self.size = CELL_SIZE - 8
        self.rect = pygame.Rect(self.x + 4, self.y + 4, self.size, self.size)
        self.glow_angle = 0
        
    def reset_position(self):
        self.x = CELL_SIZE
        self.y = CELL_SIZE
        self.grid_x = 1
        self.grid_y = 1
        
    def move(self, dx, dy, maze):
        new_x = self.x + dx * CELL_SIZE
        new_y = self.y + dy * CELL_SIZE
        
        grid_x = new_x // CELL_SIZE
        grid_y = new_y // CELL_SIZE
        
        if (0 <= grid_x < len(maze[0]) and 
            0 <= grid_y < len(maze) and 
            maze[grid_y][grid_x] == 0):
            self.x = new_x
            self.y = new_y
            self.grid_x = grid_x
            self.grid_y = grid_y
            self.rect.topleft = (self.x + 4, self.y + 4)
            
    def draw(self):
        self.glow_angle += 0.1
        glow_size = math.sin(self.glow_angle) * 2
        
        for i in range(3):
            alpha = 100 - i * 30
            glow_surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*PLAYER_COLOR, alpha),
                           (4, 4, self.size + glow_size + i*2, self.size + glow_size + i*2),
                           border_radius=8)
            SCREEN.blit(glow_surface, (self.x, self.y))
            
        pygame.draw.rect(SCREEN, self.color, self.rect, border_radius=8)

def draw_maze(maze, player, visibility_radius):
    for row in range(len(maze)):
        for col in range(len(maze[0])):
            distance = math.sqrt((col - player.grid_x)**2 + (row - player.grid_y)**2)
            if distance <= visibility_radius:
                if maze[row][col] == 1:
                    rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    pygame.draw.rect(SCREEN, WALL_COLOR, rect)
                    pygame.draw.rect(SCREEN, BORDER_COLOR, rect, 1)
                else:
                    rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    pygame.draw.rect(SCREEN, PATH_COLOR, rect, 1)
            else:
                rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(SCREEN, BLACK, rect)

def main():
    clock = pygame.time.Clock()
    game_state = GameState()
    menu = Menu()
    upgrade_menu = UpgradeMenu()
    maze = None
    player = None
    coin = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if game_state.state == 'menu':
                    pos = pygame.mouse.get_pos()
                    for button, rect in menu.buttons.items():
                        if rect.collidepoint(pos):
                            if button == 'play':
                                game_state.state = 'game'
                                maze = generate_maze(game_state.data['maze_difficulty'])
                                player = Player()
                                coin = Coin(maze)
                            elif button == 'upgrades':
                                game_state.state = 'upgrades'
                
                elif game_state.state == 'upgrades':
                    game_state.state = upgrade_menu.handle_click(pygame.mouse.get_pos(), 
                                                               game_state)
        
        if game_state.state == 'menu':
            menu.draw(SCREEN)
            
        elif game_state.state == 'upgrades':
            upgrade_menu.draw(SCREEN, game_state)
            
        elif game_state.state == 'game':
            SCREEN.fill(BLACK)
            draw_maze(maze, player, game_state.data['visibility_radius'])
            coin.draw(player, game_state.data['visibility_radius'])
            player.draw()
            
            coins_text = FONT.render(f"Coins: {game_state.data['coins']}", True, COIN_COLOR)
            SCREEN.blit(coins_text, (20, 20))
            
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                player.move(-1, 0, maze)
            if keys[pygame.K_RIGHT]:
                player.move(1, 0, maze)
            if keys[pygame.K_UP]:
                player.move(0, -1, maze)
            if keys[pygame.K_DOWN]:
                player.move(0, 1, maze)
            if keys[pygame.K_ESCAPE]:
                game_state.state = 'menu'
                
            if player.rect.colliderect(pygame.Rect(coin.x, coin.y, coin.size, coin.size)):
                game_state.data['coins'] += 1
                game_state.save_game()
                maze = generate_maze(game_state.data['maze_difficulty'])
                player.reset_position()
                coin = Coin(maze)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()