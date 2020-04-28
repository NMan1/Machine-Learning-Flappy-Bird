import pygame
import os
import random
import neat
import warnings


warnings.filterwarnings("ignore", category=DeprecationWarning)
size = [500, 800]
score = 0
run = True
generations = 0
best_fitness = 0

pygame.font.init()  # init font
window = pygame.display.set_mode((size[0], size[1]))
pygame.display.set_caption("Flappy Bird")
font = pygame.font.SysFont("comicsans", 50)


def load_scaled_img(folder, name):
    return pygame.transform.scale2x(pygame.image.load(os.path.join(folder, name)))


birds_imgs = [load_scaled_img('IMG', 'bird1.png'), load_scaled_img('IMG', 'bird2.png'),
              load_scaled_img('IMG', 'bird3.png')]
base_img = load_scaled_img('IMG', 'base.png').convert_alpha()
pipe_img = load_scaled_img('IMG', 'pipe.png').convert_alpha()
flipped_pipe_img = pygame.transform.flip(pipe_img, False, True)
bg_img = load_scaled_img('IMG', 'bg.png').convert_alpha()


class Bird:
    bird_imgs = birds_imgs
    max_rotation = 25
    rotation_velocity = 20
    animation_time = 5

    def __init__(self):
        self.angle = 0
        self.tick_count = 0
        self.velocity = 0
        self.img_count = 0
        self.img = self.bird_imgs[0]
        self.x = (size[0] - self.img.get_width()) * .5
        self.y = (size[1] - self.img.get_height()) * .5 - 50
        self.height = self.y

    def jump(self):
        self.velocity = -8.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        displacement = self.velocity * self.tick_count + 1.5 * self.tick_count ** 2
        if displacement >= 16:
            displacement = 16
        elif displacement < 0:
            displacement -= 2

        self.y += displacement
        if displacement < 0 or self.y < self.height + 50:
            if self.angle < self.max_rotation:
                self.angle = self.max_rotation
        else:
            if self.angle > -90:
                self.angle -= self.rotation_velocity

    def draw(self):
        self.img_count += 1
        if self.img_count < self.animation_time:
            self.img = self.bird_imgs[0]
        elif self.img_count < self.animation_time * 2:
            self.img = self.bird_imgs[1]
        elif self.img_count < self.animation_time * 3:
            self.img = self.bird_imgs[2]
        elif self.img_count < self.animation_time * 4:
            self.img = self.bird_imgs[1]
        elif self.img_count < self.animation_time * 4 + 1:
            self.img = self.bird_imgs[0]
            self.img_count = 0

        if self.angle <= -80:
            self.img = self.bird_imgs[1]
            self.img_count = self.animation_time * 2

        new_img = pygame.transform.rotate(self.img, self.angle)
        new_rect = new_img.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        window.blit(new_img, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Base:
    velocity = 5
    base_img = base_img

    def __init__(self):
        self.x1 = 0
        self.x2 = self.base_img.get_width()
        self.y = size[1] - 150

    def move(self):
        self.x1 -= self.velocity
        self.x2 -= self.velocity
        if self.x1 + self.base_img.get_width() < 0:
            self.x1 = self.x2 + self.base_img.get_width()

        if self.x2 + self.base_img.get_width() < 0:
            self.x2 = self.x1 + self.base_img.get_width()

    def draw(self):
        window.blit(self.base_img, (self.x1, size[1] - 150))
        window.blit(self.base_img, (self.x2, size[1] - 150))


class Pipe:
    gap = 200
    velocity = 5

    def __init__(self, initial_pos):
        self.x = initial_pos
        self.height = 0
        self.y_top = 0
        self.y_bottom = 0
        self.bottom_img = pipe_img
        self.top_img = flipped_pipe_img
        self.get_height()
        self.passed = False

    def get_height(self):
        self.height = random.randint(50, 400)
        self.y_top = self.height - self.top_img.get_height()
        self.y_bottom = self.height + self.gap

    def draw_pipe(self):
        window.blit(self.top_img, (self.x, self.y_top))
        window.blit(self.bottom_img, (self.x, self.y_bottom))
        self.x -= self.velocity

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.top_img)
        bottom_mask = pygame.mask.from_surface(self.bottom_img)

        # bird to top mask
        top_offset = (self.x - bird.x, self.y_top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.y_bottom - round(bird.y))
        b_point = bird_mask.overlap(bottom_mask, (int(bottom_offset[0]), int(bottom_offset[1])))
        t_point = bird_mask.overlap(top_mask, (int(top_offset[0]), int(top_offset[1])))
        if b_point or t_point:
            return True
        else:
            return False


def draw_window(birds, pipe_list, base, ge, nets):
    global score, run, best_fitness
    window.blit(bg_img, (0, -340))

    pipe_ind = 0
    if len(birds) > 0:
        if len(pipe_list) > 1 and birds[0].x > pipe_list[0].x + pipe_list[0].top_img.get_width():  # determine whether to use the first or second
            pipe_ind = 1

    for x, bird in enumerate(birds):
        bird.move()
        ge[x].fitness += 0.1
        output = nets[birds.index(bird)].activate((bird.y, abs(bird.y - pipe_list[pipe_ind].height), abs(bird.y - pipe_list[pipe_ind].y_bottom)))

        if output[0] > .5:
            bird.jump()

        if bird.y >= base.y:  # floor
            birds.pop(x)
            nets.pop(x)
            ge.pop(x)
        elif bird.y < 0:  # roof
            birds.pop(x)
            nets.pop(x)
            ge.pop(x)

    rem = []
    add = False
    for pipe in pipe_list:
        pipe.draw_pipe()
        for x, bird in enumerate(birds):
            if pipe.x < bird.x and not pipe.passed:
                pipe.passed = True
                add = True

            if pipe.collide(bird):
                ge[x].fitness -= 1
                nets.pop(x)
                ge.pop(x)
                birds.pop(x)

        if pipe.x + pipe.top_img.get_width() < 0:
            rem.append(pipe)

    # have to do this outside of for loop to prevent flickering
    if add:
        score += 1
        for g in ge:
            g.fitness += 5
        pipe_list.append(Pipe(size[0] + 50))

    for pipe in rem:
        pipe_list.remove(pipe)

    if len(pipe_list) == 1:
        pipe_ind = 0

    for x, bird in enumerate(birds):
        if pipe_list[pipe_ind] and not pipe_list[pipe_ind].passed:
            pygame.draw.line(window, (255, 0, 0), (bird.x+bird.img.get_width()/2, bird.y+bird.img.get_height()/2), (pipe_list[pipe_ind].x, pipe_list[pipe_ind].height), 2)
            pygame.draw.line(window, (255, 0, 0), (bird.x+bird.img.get_width()/2, bird.y+bird.img.get_height()/2), (pipe_list[pipe_ind].x, pipe_list[pipe_ind].y_bottom), 2)
        bird.draw()

    base.move()
    base.draw()

    score_label = font.render("Score: " + str(score), 1, (255, 255, 255))
    window.blit(score_label, (size[0] - score_label.get_width() - 15, 10))

    gen_label = font.render("Gen: " + str(generations), 1, (255, 0, 0))
    window.blit(gen_label, (15, 10))

    alive_label = font.render("Alive: " + str(len(birds)), 1, (255, 0, 0))
    window.blit(alive_label, (15, 45))

    fitnesses = []
    if ge:
        for g in ge:
            fitnesses.append(g.fitness)
        if max(fitnesses) > best_fitness:
            best_fitness = max(fitnesses)

    alive_label = font.render("Best Fitness: " + str(best_fitness)[0:3], 1, (255, 0, 0))
    window.blit(alive_label, (15, 80))

    pygame.display.flip()


def main(genomes, config):
    global generations, score
    generations += 1

    pipe_list = [Pipe(650)]
    base = Base()
    nets = []
    ge = []
    birds = []
    score = 0

    for _, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird())
        genome.fitness = 0
        ge.append(genome)

    clock = pygame.time.Clock()
    while run and len(birds) > 0:
        clock.tick(30)

        # event handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        draw_window(birds, pipe_list, base, ge, nets)



def setup_neat(path):
    # setup neat
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, path)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    p.add_reporter(neat.StatisticsReporter())
    winner = p.run(main, 50)
    print('\nBest genome:\n{!s}'.format(winner))

if __name__ == '__main__':
    # get path to config file
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")

    setup_neat(config_path)
