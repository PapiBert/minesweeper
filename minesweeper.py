import pygame
import sys
import numpy as np
from scipy import signal
import random
"""This is a minesweeper game coded as practice with pygame and OOP in general. Everything is
made by myself, except for the SpriteSheet class."""

class SpriteSheet:
    """Class to turn a sprite sheet into several sprites. Ripped from the internet."""
    def __init__(self, filename):
        """Load the sheet."""
        try:
            self.sheet = pygame.image.load(filename).convert()
        except pygame.error as e:
            print(f"Unable to load spritesheet image: {filename}")
            raise SystemExit(e)

    def image_at(self, rectangle, colorkey=None):
        """Load a specific image from a specific rectangle."""
        # Loads image from x, y, x+offset, y+offset.
        rect = pygame.Rect(rectangle)
        image = pygame.Surface(rect.size).convert()
        image.blit(self.sheet, (0, 0), rect)
        if colorkey is not None:
            if colorkey == -1:
                colorkey = image.get_at((0, 0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)
        return image

    def images_at(self, rects, colorkey=None):
        """Load a whole bunch of images and return them as a list."""
        return [self.image_at(rect, colorkey) for rect in rects]

    def load_strip(self, rect, image_count, colorkey=None):
        """Load a whole strip of images, and return them as a list."""
        tups = [(rect[0]+rect[2]*image_x, rect[1], rect[2], rect[3])
                for image_x in range(image_count)]
        return self.images_at(tups, colorkey)


class Game:
    """Initializes game data and calculates the values of the cells."""
    def __init__(self, n_cells_x, n_cells_y, n_bombs):
        self.n_cells_x = n_cells_x
        self.n_cells_y = n_cells_y
        self.n_bombs = n_bombs
        self.n_cells = n_cells_x * n_cells_y
        self.n_clicked_cells = 0
        self.cells = []
        self.bombs = None
        self.surround_grid = None
        for i in range(self.n_cells_x):
            for j in range(self.n_cells_y):
                self.cells.append(Cell(i, j))
        self.won = False
        self.lost = False

    def set_bombs(self, cell_no):
        # Set bombs and make sure that the clicked cell is no bomb
        self.bombs = random.sample(range(self.n_cells-1), self.n_bombs)
        self.bombs = [bomb + 1 if bomb >= cell_no else bomb for bomb in self.bombs]
        self.surround_grid = self.count_surrounding_bombs()
        for i, c in enumerate(self.cells):
            if i in self.bombs:
                c.is_bomb = True
            else:
                c.surrounding = self.surround_grid[i]

    def count_surrounding_bombs(self):
        """Counts bombs and return a numpy array with the number of bombs surrounding each cell.
        The value will be 0 on the bomb locations"""
        bomb_grid = np.zeros((self.n_cells_x, self.n_cells_y))
        for bomb in self.bombs:
            bomb_grid[bomb // self.n_cells_y, bomb % self.n_cells_y] = 1    # generate 2d bomb grid
        kernel = np.ones((3, 3), dtype=int)
        kernel[1, 1] = 0
        surround_grid = signal.convolve2d(bomb_grid, kernel, mode="same")

        bomb_x, bomb_y = np.where(bomb_grid == 1)           # return 0 at bomb locations
        for i in range(int(sum(sum(bomb_grid)))):
            surround_grid[bomb_x[i], bomb_y[i]] = 0
        return surround_grid.flatten()

    def click_update_cell(self, clicked_cell):
        """Calls the click_update() method if the cell if this cell was not clicked. Calls the update method for
        the surrounding cells recursively if the cell value is 0"""
        cell_no = self.n_cells_y * clicked_cell.x + clicked_cell.y

        if self.n_clicked_cells == 0:                           # generates bombs if no cell is clicked yet.
            self.set_bombs(cell_no)

        if clicked_cell.is_clicked:
            return

        if clicked_cell.is_bomb:
            self.lost = True                                    # game is lost when bomb is clicked
            for bomb_cell in self.cells:                        # clicks all cells with bombs to show solution
                if bomb_cell.is_bomb:
                    bomb_cell.click_update()

        self.n_clicked_cells += clicked_cell.click_update()     # 'clicks' all surrounding cells if value is 0
        if clicked_cell.surrounding == 0:
            if clicked_cell.x != 0:
                self.click_update_cell(self.cells[cell_no - self.n_cells_y])
                if clicked_cell.y != 0:
                    self.click_update_cell(self.cells[cell_no - self.n_cells_y - 1])
                if clicked_cell.y != self.n_cells_y - 1:
                    self.click_update_cell(self.cells[cell_no - self.n_cells_y + 1])

            if clicked_cell.x != self.n_cells_x - 1:
                self.click_update_cell(self.cells[cell_no + self.n_cells_y])
                if clicked_cell.y != 0:
                    self.click_update_cell(self.cells[cell_no + self.n_cells_y - 1])
                if clicked_cell.y != self.n_cells_y - 1:
                    self.click_update_cell(self.cells[cell_no + self.n_cells_y + 1])

            if clicked_cell.y != 0:
                self.click_update_cell(self.cells[cell_no - 1])

            if clicked_cell.y != self.n_cells_y - 1:
                self.click_update_cell(self.cells[cell_no + 1])


class Cell(pygame.sprite.Sprite):
    """Create a cell object that has no bomb or value. These are set by the game instance.
        provide the x and y values of the grid, not of the pixels in the window."""
    def __init__(self, x_cell, y_cell):
        super().__init__()
        self.x = x_cell
        self.y = y_cell

        #Set unclicked sprites at right position
        self.surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image = sprites_dict.get('long')
        self.pos = vec(TILE_SIZE * x_cell, TILE_SIZE * y_cell)
        self.rect = self.surf.get_rect(topleft=(int(self.pos.x), int(self.pos.y)))
        self.is_clicked = False     # will be True after clicking
        self.is_bomb = False        # will be True if set as bomb
        self.surrounding = None     # will contain number of surrounding bombs
        self.is_flagged = False     # will be True if right-clicked

    def click_update(self):
        """Updates sprites if this cell is clicked and was not clicked before."""
        self.is_clicked = True
        if self.is_bomb:
            self.image = sprites_dict.get('bomb')
            return 0
        else:
            self.image = sprites_dict.get(str(int(self.surrounding)))
            return 1                # change sprite to corresponding one with value

    def flag_update(self):
        """Update flag sprite whether a point is flagged or not and change cell sprite."""
        if self.is_clicked:
            return
        elif self.is_flagged:
            self.image = sprites_dict.get('long')
            self.is_flagged = False
        else:
            self.is_flagged = True
            self.image = sprites_dict.get('flag')


def load_sprites(tilesize):
    """Loads the sprite from the spritesheet and puts them in a dict."""
    sprite_sheet = SpriteSheet('sprites\minesweeper_sprite_sheet.png')
    sprite_names = ['long', 'flag', '0', 'bomb', '1', '2', '3', '4', '5', '6', '7', '8']
    sprite_list = sprite_sheet.load_strip([0, 0, 16, 16], 12)
    sprite_list_resized = []
    for image in sprite_list:
        sprite_list_resized.append(pygame.transform.scale(image, (tilesize, tilesize)))
    sprites_dict_out = dict(zip(sprite_names, sprite_list_resized))
    return sprites_dict_out

if __name__ == '__main__':
    # Initialize pygame
    pygame.init()
    vec = pygame.math.Vector2

    # Set game and tile parameters
    N_X = 9
    N_Y = 9
    N_BOMBS = 10
    N_CELLS = N_Y * N_X
    TILE_SIZE = 48
    FPS = 60
    SIZE = (N_X * TILE_SIZE, N_Y * TILE_SIZE)

    # Fix display parameters
    FramePerSec = pygame.time.Clock()
    screen = pygame.display.set_mode(SIZE)
    pygame.display.set_caption("Minesweeper v1")

    # Load images and start game
    sprites_dict = load_sprites(TILE_SIZE)
    game = Game(N_X, N_Y, N_BOMBS)
    all_sprites = pygame.sprite.Group()
    for cell in game.cells:
        all_sprites.add(cell)

    while not(game.won or game.lost):
        if game.n_clicked_cells == N_CELLS - N_BOMBS:        # check if game is won
            game.won = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:               # quit if x on the game gui is clicked
                pygame.quit()                           # close the game window
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:        # quit if "esc" key pressed
                    pygame.quit()                       # close the game window
            if event.type == pygame.MOUSEBUTTONDOWN:    # check clicked cells
                x, y = event.pos                        # obtain clicked pixel
                for cell in game.cells:                 # check collision for every cell
                    if cell.rect.collidepoint(x, y):
                        if event.button == 1:           # click_update if left click
                            game.click_update_cell(cell)
                        if event.button == 3:           # flag_update if right click
                            cell.flag_update()

        all_sprites.draw(screen)
        pygame.display.update()
        FramePerSec.tick(FPS)


    if game.won:
        print('You won the game you dream player')
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

    elif game.lost:
        print('You lost you mediocre player')
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
