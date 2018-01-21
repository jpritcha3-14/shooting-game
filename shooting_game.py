import os, pygame, random, math
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
    def __init__(self, explodedThing, linger=30):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('explosion.png', -1)
        self.rect.center = explodedThing.rect.center 
        self.linger = linger
    
    def update(self):
        self.linger -= 1
        if self.linger <= 0:
            self.kill()

class Missile(pygame.sprite.Sprite):
    def __init__(self, ship):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('missile.png', -1)
        self.rect.midbottom = ship.rect.midtop
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.speed = -4

    def update(self):
        newpos = self.rect.move(0,self.speed)
        if newpos.bottom > self.area.top:
            self.rect = newpos
        else:
            self.kill()
            
class Bomb(pygame.sprite.Sprite):
    def __init__(self, ship):
        pygame.sprite.Sprite.__init__(self)
        self.image = None
        self.rect = ship.rect
        self.radius = 20

    def update(self):
        self.radius += 4
        pygame.draw.circle(pygame.display.get_surface(), Color(0,0,255,128), self.rect.center, self.radius, 3)
        if self.rect.center[1] - self.radius <= 0:
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
    def __init__(self, MisType=Missile, ExplosionType=Explosion):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('ship.png', -1)
        self.original = self.image
        self.shield, self.rect = load_image('ship_shield.png', -1)
        self.screen = pygame.display.get_surface()
        self.area = self.screen.get_rect()
        self.rect.midbottom = (self.screen.get_width()//2, self.area.bottom)
        self.vert = 0
        self.horiz = 0
        self.MisType = MisType
        self.ExplosionType = ExplosionType
        self.radius = max(self.rect.width, self.rect.height)
        self.alive = True
        self.shieldUp = False

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

    def fire(self):
        return self.MisType(self) 

    def bomb(self):
        return Bomb(self)

    def explode(self):
        self.kill()
        self.alive = False
        return self.ExplosionType(self)

class Alien(pygame.sprite.Sprite):
    def __init__(self, color):
        pygame.sprite.Sprite.__init__(self)
        self.loc = 0
        self.image, self.rect = load_image('space_invader_'+ color +'.png', -1)
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.rect.midtop = (random.randint(
                            self.area.left + self.rect.width//2, 
                            self.area.right - self.rect.width//2), self.area.top)
        self.initialRect = self.rect
        self.speed = 1
        self.radius = min(self.rect.width//2, self.rect.height//2) 

    def update(self):
        horiz, vert = self.moveFunc()
        if horiz + self.initialRect.x > 500:
            horiz -= 500 + self.rect.width
        elif horiz + self.initialRect.x < 0 - self.rect.width:
            horiz += 500 + self.rect.width
        self.rect = self.initialRect.move((horiz, self.speed*self.loc + vert))
        self.loc = self.loc + 1

    def explode(self):
        self.kill()
        return Explosion(self)

class Siney(Alien):
    def __init__(self):
        Alien.__init__(self, 'green')
        self.amp = random.randint(self.rect.width, 3*self.rect.width)
        self.freq = 1/20
        self.moveFunc = lambda: (self.amp*math.sin(self.loc*self.freq), 0)

class Roundy(Alien):
    def __init__(self):
        Alien.__init__(self, 'red')
        self.amp = random.randint(self.rect.width, 3*self.rect.width)
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
    ship = Ship(Missile)
    alienTypes = (Siney, Spikey, Roundy, Fasty)
    powerupTypes = (BombPowerup, ShieldPowerup)
    
    aliens = pygame.sprite.Group()
    missiles = pygame.sprite.Group() 
    bombs = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    explosions = pygame.sprite.Group()
    alldrawings = pygame.sprite.Group()
    allsprites = pygame.sprite.RenderPlain((ship,))

    clockTime = 120
    alienPeriod = 50
    curTime = 0 
    aliensThisWave, aliensLeft, aliensOffScreen = 10, 10, 10 
    wave = 1
    bombsHeld = 3
    score = 0
    powerupTime = 10*clockTime 
    powerupTimeLeft = powerupTime
    betweenWaveTime = 5*clockTime 
    betweenWaveCount = betweenWaveTime
    font = pygame.font.Font(None, 36)

    while ship.alive:
        clock.tick(clockTime)

        if aliensLeft >= 20:
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
                newMissile = ship.fire() 
                newMissile.add(missiles, allsprites)
            elif (event.type == KEYDOWN
                and event.key == K_b):
                if bombsHeld > 0:
                    bombsHeld -= 1 
                    newBomb = ship.bomb() 
                    newBomb.add(bombs, alldrawings)

    #Collision Detection
        #Aliens
        for alien in aliens:
            if alien.rect.top > alien.area.bottom:
                alien.kill()
                aliensOffScreen += 1
            for bomb in bombs:
                if pygame.sprite.collide_circle(bomb, alien):
                    alien.explode().add(allsprites, explosions)
                    aliensLeft -= 1
                    score += 1
            for missile in missiles:
                if pygame.sprite.collide_rect(missile, alien):
                    alien.explode().add(allsprites, explosions)
                    missile.kill()
                    aliensLeft -= 1
                    score += 1
            if pygame.sprite.collide_rect(alien, ship):
                if ship.shieldUp:
                    ship.shieldUp = False
                    alien.explode().add(allsprites, explosions)
                    aliensLeft -= 1
                    score += 1
                else:
                    ship.explode().add(allsprites, explosions)

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
        if curTime <= 0 and aliensOffScreen > 0:
            random.choice(alienTypes)().add(aliens, allsprites)
            aliensOffScreen -= 1
            curTime = alienPeriod
        elif curTime > 0:
            curTime -= 1
            
    #Update text overlays
        waveText = font.render("Wave: "+str(wave), 1, (0,0,255))
        leftText = font.render("Aliens Left: "+str(aliensLeft), 1, (0,0,255))
        scoreText = font.render("Score: "+str(score), 1, (0,0,255))
        bombText = font.render("Bombs: "+str(bombsHeld), 1, (0,0,255))
        
        wavePos = waveText.get_rect(topleft=background.get_rect().topleft)
        leftPos = leftText.get_rect(midtop=background.get_rect().midtop)
        scorePos = scoreText.get_rect(topright=background.get_rect().topright)
        bombPos = bombText.get_rect(bottomleft=background.get_rect().bottomleft)

        text = [waveText, leftText, scoreText, bombText]
        position = [wavePos, leftPos, scorePos, bombPos]
    
    #Detertmine when to move to next wave
        if aliensLeft <= 0:
            if betweenWaveCount > 0:
                betweenWaveCount -= 1
                nextWaveText = font.render('Wave ' + str(wave+1), 1, (0,0,255))
                nextWaveNum = font.render(str((betweenWaveCount // clockTime) + 1), 1, (0,0,255))
                text.extend([nextWaveText, nextWaveNum])
                nextWavePos = nextWaveText.get_rect(center=background.get_rect().center)
                nextWaveNumPos = nextWaveNum.get_rect(midtop=nextWavePos.midbottom)
                position.extend([nextWavePos, nextWaveNumPos])

            else:
                wave += 1
                aliensLeft, aliensOffScreen, aliensThisWave = 3*[2*aliensThisWave]
                betweenWaveCount = betweenWaveTime
                
        textOverlays = zip(text, position)

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
