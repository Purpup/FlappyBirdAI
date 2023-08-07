import pygame
import neat
import os
import random
pygame.font.init()

# define window width for the game
WIDTH = 500
HEIGHT = 800

# load in the necessary assets for the game, bird, pipe, base (ground), background
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

# define the type of font to use
STAT_FONT = pygame.font.SysFont("comicsans", 50)

# Bird class for each bird in the game
class Bird:
    IMGS = BIRD_IMGS
    
    # define the tilt behavior of the bird
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5
    
    def __init__(self, x, y):
        
        # initialize starting position, tilt, velocity, height
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        
        # initialize index of current bird image as well as the image itself
        self.img_count = 0
        self.img = self.IMGS[0]
        
    def jump(self):
        
        # change velocity when bird jumps (negative since top left is (0, 0))
        self.vel = -10.5
        
        # reset tick count to 0, since tick = frames since jump
        self.tick_count = 0
        self.height = self.y
        
    def move(self):
        
        # update tick count, number of frames since last jump
        self.tick_count += 1
        
        # calculate bird displacement (up or down) based on simple formulas
        d = self.vel * self.tick_count + 1.5 * self.tick_count ** 2
        
        # update displacement if we reach "terminal" velocity
        if d >= 16:
            d = 16
            
        # fine tunes jump behavior
        if d < 0:
            d -= 2
        
        # update bird's vertical position
        self.y += d
        
        # ensure bird does not rotate past max rotation angle
        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        # start tilting the bird downwards while bird is falling
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL
                
    def draw(self, win):
        
        # update count of bird image
        self.img_count += 1
        
        # rotate image between wing being up, down, and neutral based on frame
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0
            
        # keep wings neutral if bird is nose diving
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count  = self.ANIMATION_TIME * 2
            
        # rotate image around its center and height to get correct rotation behavior
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)
        
    # use masks for collision detection
    def get_mask(self):
        return pygame.mask.from_surface(self.img)
    
class Pipe:
    GAP = 200
    VEL = 5
    
    def __init__(self, x):
        self.x = x
        self.height = 0
        
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG
        
        self.passed = False
        self.set_height()
        
    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP
        
    def move(self):
        self.x -= self.VEL
        
    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))
        
    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x -bird.x, self.bottom - round(bird.y))
        
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)
        
        if t_point or b_point:
            return True
        return False

class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG
    
    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH
        
    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
            
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH
            
    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))

def draw_window(win, birds, pipes, base, score):
    
    # draw background image
    win.blit(BG_IMG, (0, 0))
    
    # draw each pipe in pipes
    for pipe in pipes:
        pipe.draw(win)
        
    # display the score, score += 1 for each pipe passed
    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIDTH - 10 - text.get_width(), 10))
    
    base.draw(win)
    
    # draw our bird popluation into the window
    for bird in birds:
        bird.draw(win)
    pygame.display.update()
    
def main(genomes, config):
    nets = []
    ge = []
    birds = []
    
    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        ge.append(g)
    
    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIDTH, HEIGHT)) 
    clock = pygame.time.Clock()
    
    score = 0
    
    # main game loop
    run = True
    while run:
        
        # set fps = 30
        clock.tick(30)
        
        # quits the game if window is closed
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            break
                
        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += .1
            
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), 
                                       abs(bird.y - pipes[pipe_ind].bottom)))
            if output[0] > .5:
                bird.jump()
        
        rem = []
        add_pipe = False
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)
                
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True
            
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
                
            pipe.move()
            
        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(600))
            
        for r in rem:
            pipes.remove(r)
            
        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)
        base.move()
        draw_window(win, birds, pipes, base, score)
    
def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    
    p = neat.Population(config)
    
    p.add_reporter(neat.StdOutReporter(True))
    p.add_reporter(neat.StatisticsReporter())
    
    winner = p.run(main, 50)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config.txt")
    run(config_path)
