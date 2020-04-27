import pygame
import os
import random

size = [500, 800]

window = pygame.display.set_mode((size[0], size[1]))
pygame.display.set_caption("Flappy Bird")


def load_scaled_img(folder, name):
    return pygame.transform.scale2x(pygame.image.load(os.path.join(folder, name)))


birds_img = [load_scaled_img('IMG', 'bird1.png'), load_scaled_img('IMG', 'bird2.png'), load_scaled_img('IMG', 'bird3.png')]
base_img = load_scaled_img('IMG', 'base.png')
pipe_img = load_scaled_img('IMG', 'pipe.png').convert_alpha()
bg_img = load_scaled_img('IMG', 'bg.png')


class Pipe:
    gap = 200
    velocity = 5

    def __init__(self, initial_pos):
        self.x = initial_pos
        self.y_top = 0
        self.y_bottom = 0
        self.bottom_img = pipe_img
        self.top_img = pygame.transform.flip(pipe_img, False, True)
        self.get_height()

    def get_height(self):
        height = random.randint(50, 400)
        self.y_top = height - self.top_img.get_height()
        self.y_bottom = height + self.gap

    def draw_pipe(self):
        window.blit(self.top_img, (self.x, self.y_top))
        window.blit(self.bottom_img, (self.x, self.y_bottom))
        self.x -= self.velocity


pipe_list = [Pipe(700)]


def draw_window():
    window.blit(bg_img, (0, -340))

    app_pipe = False
    remove_pipes = []
    for pipe in pipe_list:
        pipe.draw_pipe()
        if pipe.x + pipe.top_img.get_width() < 0:
            remove_pipes.append(pipe)

        if pipe.x < 100:  # change to bird pisotion
            app_pipe = True

    if app_pipe:
        pipe_list.append(Pipe(size[0]))

    for pipe in remove_pipes:
        pipe_list.remove(pipe)

    window.blit(base_img, (0, size[1] - 150))

    pygame.display.update()


run = True
while run:
    draw_window()

    # event handler
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

pygame.quit()
exit()
