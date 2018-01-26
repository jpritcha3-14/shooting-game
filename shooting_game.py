import os, pygame, random, math, copy
from collections import deque
from pygame.locals import *
from pygame.compat import geterror

main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, 'data')

direction = {None:(0,0), K_w:(0,-2), K_s:(0,2), K_a:(-2,0), K_d:(2,0)}

def load_image(name, colorkey=None):
    fullname = os.path.join(data_dir, name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error:
        print('Cannot load image:', fullname)
        raise SystemExit(str(geterror()))
    image = image.convert()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()
     
class Explosion(pygame.sprite.Sprite):
    pool = pygame.sprite.Group()
    active = pygame.sprite.Group()
    allsprites = None
    
    def __init__(self, linger=30):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('explosion.png', -1)
        self.linger = linger
    
    @classmethod
    def position(cls, loc):
        if len(cls.pool) > 0:
            explosion = cls.pool.sprites()[0]
            explosion.add(cls.active, cls.allsprites)
            explosion.remove(cls.pool)
            explosion.rect.center = loc
            explosion.linger = 30

    def update(self):
        self.linger -= 1
        if self.linger <= 0:
            self.remove(self.allsprites, self.active)
            self.add(self.pool)

class Missile(pygame.sprite.Sprite):
    pool = pygame.sprite.Group()
    active = pygame.sprite.Group()
    allsprites = None

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('missile.png', -1)
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.speed = -4

    @classmethod
    def position(cls, loc):
        if len(cls.pool) > 0:
            missile = cls.pool.sprites()[0]
            missile.add(cls.allsprites, cls.active)
            missile.remove(cls.pool)
            missile.rect.midbottom = loc
        
    def table(self):
        self.add(self.pool)
        self.remove(self.allsprites, self.active)

    def update(self):
        newpos = self.rect.move(0,self.speed)
        self.rect = newpos
        if self.rect.top < self.area.top:
            self.table()

            
class Bomb(pygame.sprite.Sprite):
    def __init__(self, ship):
        pygame.sprite.Sprite.__init__(self)
        self.image = None
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.radius = 20
        self.radiusIncrement = 4
        self.rect = ship.rect 

    def update(self):
        self.radius += self.radiusIncrement 
        pygame.draw.circle(pygame.display.get_surface(), Color(0,0,255,128), self.rect.center, self.radius, 3)
        if (self.rect.center[1] - self.radius <= self.area.top 
            and self.rect.center[1] + self.radius >= self.area.bottom 
            and self.rect.center[0] - self.radius <= self.area.left 
            and self.rect.center[0] + self.radius >= self.area.right):
            self.kill()

class Powerup(pygame.sprite.Sprite):
    def __init__(self, kindof):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image(kindof + '_powerup.png', -1)
        self.original = self.image
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.rect.midtop = (random.randint(
                            self.area.left + self.rect.width//2, 
                            self.area.right - self.rect.width//2), self.area.top)
        self.speed = 2
        self.angle = 0

    def update(self):
        center = self.rect.center
        self.angle = (self.angle + 2) % 360
        rotate = pygame.transform.rotate
        self.image = rotate(self.original, self.angle)
        self.rect = self.image.get_rect(center=(center[0], center[1]+self.speed))

class BombPowerup(Powerup):
    def __init__(self):
        Powerup.__init__(self, 'bomb')
        self.pType = 'bomb'

class ShieldPowerup(Powerup):
    def __init__(self):
        Powerup.__init__(self, 'shield')
        self.pType = 'shield'

class Ship(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('ship.png', -1)
        self.original = self.image
        self.shield, self.rect = load_image('ship_shield.png', -1)
        self.screen = pygame.display.get_surface()
        self.area = self.screen.get_rect()
        self.rect.midbottom = (self.screen.get_width()//2, self.area.bottom)
        self.radius = max(self.rect.width, self.rect.height)
        self.alive = True
        self.shieldUp = False
        self.vert = 0
        self.horiz = 0
        self.checkKeys()

    def checkKeys(self):
        keyState = pygame.key.get_pressed()
        if keyState[K_w]:
            self.vert -= 4
        if keyState[K_s]:
            self.vert += 4
        if keyState[K_a]:
            self.horiz -= 4
        if keyState[K_d]:
            self.horiz += 4

    def update(self):
        newpos = self.rect.move((self.horiz, self.vert))
        newhoriz = self.rect.move((self.horiz, 0))
        newvert = self.rect.move((0, self.vert))

        if not (newpos.left <= self.area.left
            or newpos.top <= self.area.top
            or newpos.right >= self.area.right
            or newpos.bottom >= self.area.bottom):
            self.rect = newpos
        elif not (newhoriz.left <= self.area.left
            or newhoriz.right >= self.area.right):
            self.rect = newhoriz
        elif not (newvert.top <= self.area.top
            or newvert.bottom >= self.area.bottom):
            self.rect = newvert

        if self.shieldUp and self.image != self.shield:
            self.image = self.shield 

        if not self.shieldUp and self.image != self.original:
            self.image = self.original

    def bomb(self):
        return Bomb(self)

class Alien(pygame.sprite.Sprite):
    pool = pygame.sprite.Group()
    active = pygame.sprite.Group()
    allsprites = None

    def __init__(self, color):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('space_invader_'+ color +'.png', -1)
        self.initialRect = self.rect
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.loc = 0
        self.speed = 1
        self.radius = min(self.rect.width//2, self.rect.height//2) 

    @classmethod
    def position(cls):
        if len(cls.pool) > 0 and cls.numOffScreen > 0:
            alien = random.choice(cls.pool.sprites())
            if isinstance(alien, Crawly):
                alien.rect.midbottom = (random.choice((alien.area.left, alien.area.right)),
                                        random.randint((alien.area.bottom*3)//4, alien.area.bottom))
            else:
                alien.rect.midtop = (random.randint(alien.area.left + alien.rect.width//2, 
                                     alien.area.right - alien.rect.width//2), alien.area.top)
            alien.initialRect = alien.rect
            alien.loc = 0
            alien.add(cls.allsprites, cls.active)
            alien.remove(cls.pool)
            Alien.numOffScreen -= 1

    def update(self):
        horiz, vert = self.moveFunc()
        if horiz + self.initialRect.x > 500:
            horiz -= 500 + self.rect.width
        elif horiz + self.initialRect.x < 0 - self.rect.width:
            horiz += 500 + self.rect.width
        self.rect = self.initialRect.move((horiz, self.speed*self.loc + vert))
        self.loc = self.loc + 1
        if self.rect.top > self.area.bottom:
            self.table()
            Alien.numOffScreen += 1

    def table(self):
        self.kill()
        self.add(self.pool)

class Siney(Alien):
    def __init__(self):
        Alien.__init__(self, 'green')
        self.amp = random.randint(self.rect.width, 3*self.rect.width)
        self.freq = 1/20
        self.moveFunc = lambda: (self.amp*math.sin(self.loc*self.freq), 0)

class Roundy(Alien):
    def __init__(self):
        Alien.__init__(self, 'red')
        self.amp = random.randint(self.rect.width, 2*self.rect.width)
        self.freq = 1/20
        self.moveFunc = lambda: (self.amp*math.sin(self.loc*self.freq), self.amp*math.cos(self.loc*self.freq))

class Spikey(Alien):
    def __init__(self):
        Alien.__init__(self, 'blue')
        self.slope = random.choice(list(x for x in range(-3,3) if x != 0))
        self.period = random.choice(list(4*x for x in range(10,41)))
        self.moveFunc = lambda: (self.slope*(self.loc % self.period) if self.loc % self.period < self.period // 2 else self.slope*self.period // 2 - self.slope*((self.loc % self.period) - self.period//2), 0)
                
class Fasty(Alien):
    def __init__(self):
        Alien.__init__(self, 'white')
        self.moveFunc = lambda: (0, 3*self.speed*self.loc)

class Crawly(Alien):
    def __init__(self):
        Alien.__init__(self, 'yellow')
        self.moveFunc = lambda: (self.speed*self.loc, 0)
        
    def update(self):
        horiz, vert = self.moveFunc()
        horiz = -horiz if self.initialRect.center[0] == self.area.right else horiz
        if (horiz + self.initialRect.left > self.area.right
            or horiz + self.initialRect.right < self.area.left):
            self.table()
            Alien.numOffScreen += 1
        self.rect = self.initialRect.move((horiz, vert))
        self.loc = self.loc + 1

def main():
#Initialize everything
    pygame.init()
    screen = pygame.display.set_mode((500,500))
    pygame.display.set_caption('Shooting Game')
    pygame.mouse.set_visible(0)

#Create the background
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))

#Display the background
    screen.blit(background, (0, 0))
    pygame.display.flip()
    
#Prepare game objects
    clock = pygame.time.Clock()
    ship = Ship()
    alienTypes = (Siney, Spikey, Roundy, Fasty, Crawly)
    #alienTypes = (Crawly,)
    powerupTypes = (BombPowerup, ShieldPowerup)
    
    alldrawings = pygame.sprite.Group()
    allsprites = pygame.sprite.RenderPlain((ship,))
    Alien.pool = pygame.sprite.Group([alien() for alien in alienTypes for _ in range(5)])
    Alien.active = pygame.sprite.Group() 
    Alien.allsprites = allsprites
    Missile.pool = pygame.sprite.Group([Missile() for _ in range(10)])
    Missile.active = pygame.sprite.Group()
    Missile.allsprites = allsprites
    Explosion.pool = pygame.sprite.Group([Explosion() for _ in range(10)])
    Explosion.active = pygame.sprite.Group()
    Explosion.allsprites = allsprites
    bombs = pygame.sprite.Group()
    powerups = pygame.sprite.Group()

    clockTime = 120 
    alienPeriod = clockTime//2 
    curTime = 0 
    aliensThisWave, aliensLeftThisWave, Alien.numOffScreen = 10, 10, 10 
    wave = 1
    bombsHeld = 3
    score = 0
    powerupTime = 10*clockTime 
    powerupTimeLeft = powerupTime
    betweenWaveTime = 3*clockTime 
    betweenWaveCount = betweenWaveTime
    font = pygame.font.Font(None, 36)

    def killShip():
        ship.alive = False
        ship.remove(allsprites)
        Explosion.position(ship.rect.center)

    while ship.alive:
        clock.tick(clockTime)

        if aliensLeftThisWave >= 20:
            powerupTimeLeft -= 1
        if powerupTimeLeft <= 0:
            powerupTimeLeft = powerupTime
            random.choice(powerupTypes)().add(powerups, allsprites)

    #Event Handling
        for event in pygame.event.get():
            if (event.type == QUIT
                or event.type == KEYDOWN 
                and event.key == K_ESCAPE):
                return 
            elif (event.type == KEYDOWN 
                and event.key in direction.keys()):
                ship.horiz += direction[event.key][0] 
                ship.vert += direction[event.key][1] 
            elif (event.type == KEYUP 
                and event.key in direction.keys()):
                ship.horiz -= direction[event.key][0] 
                ship.vert -= direction[event.key][1] 
            elif (event.type == KEYDOWN
                and event.key == K_SPACE):
                Missile.position(ship.rect.midtop)
            elif (event.type == KEYDOWN
                and event.key == K_b):
                if bombsHeld > 0:
                    bombsHeld -= 1 
                    newBomb = ship.bomb() 
                    newBomb.add(bombs, alldrawings)
    
    #Collision Detection
        #Aliens
        for alien in Alien.active:
            for bomb in bombs:
                if pygame.sprite.collide_circle(bomb, alien):
                    alien.table()
                    Explosion.position(alien.rect.center)
                    aliensLeftThisWave -= 1
                    score += 1
            for missile in Missile.active:
                if pygame.sprite.collide_rect(missile, alien):
                    alien.table()
                    missile.table()
                    Explosion.position(alien.rect.center)
                    aliensLeftThisWave -= 1
                    score += 1
            if pygame.sprite.collide_rect(alien, ship):
                if ship.shieldUp:
                    alien.table()
                    Explosion.position(alien.rect.center)
                    aliensLeftThisWave -= 1
                    score += 1
                    ship.shieldUp = False
                else:
                    killShip()

        #PowerUps
        for powerup in powerups:
            if pygame.sprite.collide_circle(powerup, ship):
                if powerup.pType == 'bomb':
                    bombsHeld += 1
                elif powerup.pType == 'shield':
                    ship.shieldUp = True
                powerup.kill()
            elif powerup.rect.top > powerup.area.bottom: 
                powerup.kill()

    #Update Aliens
        if curTime <= 0 and aliensLeftThisWave > 0:
            Alien.position()
            curTime = alienPeriod
        elif curTime > 0:
            curTime -= 1
            
    #Update text overlays
        waveText = font.render("Wave: "+str(wave), 1, (0,0,255))
        leftText = font.render("Aliens Left: "+str(aliensLeftThisWave), 1, (0,0,255))
        scoreText = font.render("Score: "+str(score), 1, (0,0,255))
        bombText = font.render("Bombs: "+str(bombsHeld), 1, (0,0,255))
        
        wavePos = waveText.get_rect(topleft=background.get_rect().topleft)
        leftPos = leftText.get_rect(midtop=background.get_rect().midtop)
        scorePos = scoreText.get_rect(topright=background.get_rect().topright)
        bombPos = bombText.get_rect(bottomleft=background.get_rect().bottomleft)

        text = [waveText, leftText, scoreText, bombText]
        textposition = [wavePos, leftPos, scorePos, bombPos]
    
    #Detertmine when to move to next wave
        if aliensLeftThisWave <= 0:
            if betweenWaveCount > 0:
                betweenWaveCount -= 1
                nextWaveText = font.render('Wave ' + str(wave+1) + ' in', 1, (0,0,255))
                nextWaveNum = font.render(str((betweenWaveCount // clockTime) + 1), 1, (0,0,255))
                text.extend([nextWaveText, nextWaveNum])
                nextWavePos = nextWaveText.get_rect(center=background.get_rect().center)
                nextWaveNumPos = nextWaveNum.get_rect(midtop=nextWavePos.midbottom)
                textposition.extend([nextWavePos, nextWaveNumPos])
            elif betweenWaveCount == 0:
                wave += 1
                aliensLeftThisWave, aliensThisWave, Alien.numOffScreen = 3*[2*aliensThisWave]
                betweenWaveCount = betweenWaveTime
                
        textOverlays = zip(text, textposition)

    #Update and draw all sprites and text
        allsprites.update()
        screen.blit(background, (0,0))
        allsprites.draw(screen)
        alldrawings.update()
        for txt, pos in textOverlays:
            screen.blit(txt, pos)
        pygame.display.flip()

    
    while True:
        clock.tick(clockTime)

    #Event Handling
        for event in pygame.event.get():
            if (event.type == QUIT
                or event.type == KEYDOWN 
                and event.key == K_ESCAPE):
                return False
            elif (event.type == KEYDOWN 
                and event.key == K_SPACE):
                
                return True

    #Update and draw all sprites 
        allsprites.update()
        screen.blit(background, (0,0))
        allsprites.draw(screen)
        alldrawings.update()
        pygame.display.flip()

if __name__ == '__main__':
    while(main()):
        pass
