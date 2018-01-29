import os, pygame, random, math, sqlite3
from collections import deque
from pygame.locals import *
from pygame.compat import geterror

if not pygame.mixer: print ('Warning, sound disabled')
if not pygame.font: print ('Warning, fonts disabled')

BLUE = (0, 0, 255)
RED = (255, 0, 0)

direction = {None:(0,0), K_w:(0,-2), K_s:(0,2), K_a:(-2,0), K_d:(2,0)}

main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, 'data')

def load_sound(name):
    class NoneSound:
        def play(self): pass
    if not pygame.mixer or not pygame.mixer.get_init():
        return NoneSound()
    fullname = os.path.join(data_dir, name)
    try:
        sound = pygame.mixer.Sound(fullname)
    except pygame.error:
        print ('Cannot load sound: %s' % fullname)
        raise SystemExit(str(geterror()))
    return sound

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

class MasterSprite(pygame.sprite.Sprite):
    allsprites = None
     
class Explosion(MasterSprite):
    pool = pygame.sprite.Group()
    active = pygame.sprite.Group()
    
    def __init__(self, speed):
        super().__init__()
        self.image, self.rect = load_image('explosion.png', -1)
        self.linger = speed*3 
    
    @classmethod
    def position(cls, loc):
        if len(cls.pool) > 0:
            explosion = cls.pool.sprites()[0]
            explosion.add(cls.active, cls.allsprites)
            explosion.remove(cls.pool)
            explosion.rect.center = loc
            explosion.linger = 12 

    def update(self):
        self.linger -= 1
        if self.linger <= 0:
            self.remove(self.allsprites, self.active)
            self.add(self.pool)

class Missile(MasterSprite):
    pool = pygame.sprite.Group()
    active = pygame.sprite.Group()

    def __init__(self, speed):
        super().__init__()
        self.image, self.rect = load_image('missile.png', -1)
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.speed = -4*speed

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
        super().__init__()
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
        super().__init__()
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
        super().__init__('bomb')
        self.pType = 'bomb'

class ShieldPowerup(Powerup):
    def __init__(self):
        super().__init__('shield')
        self.pType = 'shield'

class Ship(pygame.sprite.Sprite):
    def __init__(self, speed):
        super().__init__()
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
        self.speed = speed

    def initializeKeys(self):
        keyState = pygame.key.get_pressed()
        if keyState[K_w]:
            self.vert -= 2*speed
        if keyState[K_s]:
            self.vert += 2*speed
        if keyState[K_a]:
            self.horiz -= 2*speed
        if keyState[K_d]:
            self.horiz += 2*speed

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

class Alien(MasterSprite):
    pool = pygame.sprite.Group()
    active = pygame.sprite.Group()

    def __init__(self, color, speed):
        super().__init__()
        self.image, self.rect = load_image('space_invader_'+ color +'.png', -1)
        self.initialRect = self.rect
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.loc = 0
        self.speed = speed 
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
        self.rect = self.initialRect.move((horiz, self.loc + vert))
        self.loc = self.loc + self.speed 
        if self.rect.top > self.area.bottom:
            self.table()
            Alien.numOffScreen += 1

    def table(self):
        self.kill()
        self.add(self.pool)

class Siney(Alien):
    def __init__(self, speed):
        super().__init__('green', speed)
        self.amp = random.randint(self.rect.width, 3*self.rect.width)
        self.freq = (1/20)
        self.moveFunc = lambda: (self.amp*math.sin(self.loc*self.freq), 0)

class Roundy(Alien):
    def __init__(self, speed):
        super().__init__('red', speed)
        self.amp = random.randint(self.rect.width, 2*self.rect.width)
        self.freq = 1/(20)
        self.moveFunc = lambda: (self.amp*math.sin(self.loc*self.freq), self.amp*math.cos(self.loc*self.freq))

class Spikey(Alien):
    def __init__(self, speed):
        super().__init__('blue', speed)
        self.slope = random.choice(list(x for x in range(-3,3) if x != 0))
        self.period = random.choice(list(4*x for x in range(10,41)))
        self.moveFunc = lambda: (self.slope*(self.loc % self.period) if self.loc % self.period < self.period // 2 else self.slope*self.period // 2 - self.slope*((self.loc % self.period) - self.period//2), 0)
                
class Fasty(Alien):
    def __init__(self, speed):
        super().__init__('white', speed)
        self.moveFunc = lambda: (0, 3*self.loc)

class Crawly(Alien):
    def __init__(self, speed):
        super().__init__('yellow', speed)
        self.moveFunc = lambda: (self.loc, 0)
        
    def update(self):
        horiz, vert = self.moveFunc()
        horiz = -horiz if self.initialRect.center[0] == self.area.right else horiz
        if (horiz + self.initialRect.left > self.area.right
            or horiz + self.initialRect.right < self.area.left):
            self.table()
            Alien.numOffScreen += 1
        self.rect = self.initialRect.move((horiz, vert))
        self.loc = self.loc + self.speed 

class Database(object):
    path = os.path.join(data_dir, 'hiScores.db')
    numScores = 15

    @staticmethod
    def getSound(music=False):
        conn = sqlite3.connect(Database.path)
        c = conn.cursor()
        if music:
            c.execute("CREATE TABLE if not exists music (setting integer)")
            c.execute("SELECT * FROM music")
        else:
            c.execute("CREATE TABLE if not exists sound (setting integer)")
            c.execute("SELECT * FROM sound")
        setting = c.fetchall()
        conn.close()
        return bool(setting[0][0]) if len(setting) > 0 else False 

    @staticmethod
    def setSound(setting, music=False):
        conn = sqlite3.connect(Database.path)
        c = conn.cursor()
        table = 'music' if music else 'sound'
        if music:
            c.execute("DELETE FROM music")
            c.execute("INSERT INTO music VALUES (?)", (setting,))
        else:
            c.execute("DELETE FROM sound")
            c.execute("INSERT INTO sound VALUES (?)", (setting,))
        conn.commit()
        conn.close()

    @staticmethod
    def getScores():
        conn = sqlite3.connect(Database.path)
        c = conn.cursor()
        c.execute('''CREATE TABLE if not exists scores
                     (name text, score integer, accuracy real)''')
        c.execute("SELECT * FROM scores ORDER BY score DESC")
        hiScores = c.fetchall()
        conn.close()
        return hiScores

    @staticmethod
    def setScore(hiScores, entry):
        conn = sqlite3.connect(Database.path)
        c = conn.cursor()
        if len(hiScores) == Database.numScores:
            lowScoreName = hiScores[-1][0]
            lowScore = hiScores[-1][1]
            c.execute("DELETE FROM scores WHERE (name = ? AND score = ?)", (lowScoreName, lowScore))
        c.execute("INSERT INTO scores VALUES (?,?,?)", entry)
        conn.commit()
        conn.close()

class Keyboard(object):
    keys = {K_a:'A', K_b:'B', K_c:'C', K_d:'D',
            K_e:'E', K_f:'F', K_g:'G', K_h:'H',
            K_i:'I', K_j:'J', K_k:'K', K_l:'L',
            K_m:'M', K_n:'N', K_o:'O', K_p:'P',
            K_q:'Q', K_r:'R', K_s:'S', K_t:'T',
            K_u:'U', K_v:'V', K_w:'W', K_x:'X',
            K_y:'Y', K_z:'Z'}
            
def main():
#Initialize everything
    pygame.mixer.pre_init(11025, -16, 2, 512)
    pygame.init()
    screen = pygame.display.set_mode((500,500))
    pygame.display.set_caption('Shooting Game')
    pygame.mouse.set_visible(0)

#Create the background which will scroll and loop over a set of different size stars
    background = pygame.Surface((500, 2000))
    background = background.convert()
    background.fill((0, 0, 0))
    backgroundLoc = 1500 
    finalStars = deque()
    for y in range(0,1500,30):
        size = random.randint(2,5)
        x = random.randint(0,500-size)
        if y <= 500:
            finalStars.appendleft((x, y+1500, size))
        pygame.draw.rect(background, (255, 255, 0), pygame.Rect(x,y,size,size))
    while finalStars:
        x, y, size = finalStars.pop()
        pygame.draw.rect(background, (255, 255, 0), pygame.Rect(x,y,size,size))

#Display the background
    screen.blit(background, (0, 0))
    pygame.display.flip()
    
#Prepare game objects
    speed = 2 
    clockTime = 60  #maximum FPS 
    clock = pygame.time.Clock()
    ship = Ship(speed)
    alienTypes = (Siney, Spikey, Roundy, Fasty, Crawly)
    powerupTypes = (BombPowerup, ShieldPowerup)
    
    #Sprite groups 
    alldrawings = pygame.sprite.Group()
    allsprites = pygame.sprite.RenderPlain((ship,))
    MasterSprite.allsprites = allsprites
    Alien.pool = pygame.sprite.Group([alien(speed) for alien in alienTypes for _ in range(5)])
    Alien.active = pygame.sprite.Group() 
    Missile.pool = pygame.sprite.Group([Missile(speed) for _ in range(10)])
    Missile.active = pygame.sprite.Group()
    Explosion.pool = pygame.sprite.Group([Explosion(speed) for _ in range(10)])
    Explosion.active = pygame.sprite.Group()
    bombs = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    
    #Sounds
    missile_sound = load_sound('missile.ogg')
    bomb_sound = load_sound('bomb.ogg')
    alien_explode_sound = load_sound('alien_explode.ogg')
    ship_explode_sound = load_sound('ship_explode.ogg')
    pygame.mixer.music.load(os.path.join(data_dir, 'music_loop.ogg'))
    
    alienPeriod = clockTime//2 
    curTime = 0 
    aliensThisWave, aliensLeftThisWave, Alien.numOffScreen = 10, 10, 10 
    wave = 1
    bombsHeld = 3
    score = 0
    missilesFired = 0
    powerupTime = 10*clockTime 
    powerupTimeLeft = powerupTime
    betweenWaveTime = 3*clockTime 
    betweenWaveCount = betweenWaveTime
    font = pygame.font.Font(None, 36)

    inMenu = True
    hiScores = Database.getScores()
    highScoreTexts = [font.render("NAME", 1, RED), 
                      font.render("SCORE", 1, RED),
                      font.render("ACCURACY", 1, RED)]
    highScorePos = [highScoreTexts[0].get_rect(topleft=screen.get_rect().inflate(-100,-100).topleft),
                    highScoreTexts[1].get_rect(midtop=screen.get_rect().inflate(-100,-100).midtop),
                    highScoreTexts[2].get_rect(topright=screen.get_rect().inflate(-100,-100).topright)] 
    for hs in hiScores:
        highScoreTexts.extend([font.render(str(hs[x]), 1, BLUE) for x in range(3)])
        highScorePos.extend([highScoreTexts[x].get_rect(topleft=highScorePos[x].bottomleft) for x in range(-3,0)])

    title, titleRect = load_image('title.png')
    titleRect.midtop = screen.get_rect().inflate(0 ,-200).midtop

    startText = font.render('START GAME', 1, BLUE)
    startPos = startText.get_rect(midtop=titleRect.inflate(0, 100).midbottom)
    hiScoreText = font.render('HIGH SCORES', 1, BLUE)
    hiScorePos = hiScoreText.get_rect(topleft=startPos.bottomleft)
    fxText = font.render('SOUND FX ', 1, BLUE)
    fxPos = fxText.get_rect(topleft=hiScorePos.bottomleft)
    fxOnText = font.render('ON', 1, RED)
    fxOffText = font.render('OFF', 1, RED)
    fxOnPos = fxOnText.get_rect(topleft=fxPos.topright)
    fxOffPos = fxOffText.get_rect(topleft=fxPos.topright)
    musicText = font.render('MUSIC', 1, BLUE)
    musicPos = fxText.get_rect(topleft=fxPos.bottomleft)
    musicOnText = font.render('ON', 1, RED)
    musicOffText = font.render('OFF', 1, RED)
    musicOnPos = musicOnText.get_rect(topleft=musicPos.topright)
    musicOffPos = musicOffText.get_rect(topleft=musicPos.topright)
    quitText = font.render('QUIT', 1, BLUE)
    quitPos = quitText.get_rect(topleft=musicPos.bottomleft)
    selectText = font.render('*', 1, BLUE)
    selectPos = selectText.get_rect(topright=startPos.topleft)
    menuDict = {1:startPos, 2:hiScorePos, 3:fxPos, 4:musicPos, 5:quitPos}
    selection = 1
    showHiScores = False
    soundFX = Database.getSound()
    music = Database.getSound(music=True)
    if music:
        pygame.mixer.music.play(loops=-1)

    while inMenu:
        clock.tick(clockTime)

        screen.blit(background, (0,0), area=pygame.Rect(0,backgroundLoc,500,500))
        backgroundLoc -= speed
        if backgroundLoc == 0:
            backgroundLoc = 1500

        for event in pygame.event.get():
            if (event.type == QUIT):
                return
            elif (event.type == KEYDOWN and event.key == K_RETURN):
                if showHiScores:
                    showHiScores = False
                elif selection == 1:
                    inMenu = False
                    ship.initializeKeys()
                elif selection == 2:
                    showHiScores = True
                elif selection == 3:
                    soundFX = not soundFX
                    if soundFX:
                        missile_sound.play()
                    Database.setSound(int(soundFX))
                elif selection == 4:
                    music = not music
                    if music:
                        pygame.mixer.music.play(loops=-1)
                    else:
                        pygame.mixer.music.stop()
                    Database.setSound(int(music), music=True)
                elif selection == 5:
                    return
            elif (event.type == KEYDOWN and event.key == K_w and selection > 1 and not showHiScores):
                selection -= 1
            elif (event.type == KEYDOWN and event.key == K_s and selection < len(menuDict) and not showHiScores):
                selection += 1

        selectPos = selectText.get_rect(topright=menuDict[selection].topleft)

        if showHiScores:
            textOverlays = zip(highScoreTexts, highScorePos) 
        else:
            textOverlays = zip([startText, hiScoreText, fxText, musicText, quitText, selectText, 
                                fxOnText if soundFX else fxOffText, musicOnText if music else musicOffText],
                               [startPos, hiScorePos, fxPos, musicPos, quitPos, selectPos,
                                fxOnPos if soundFX else fxOffPos, musicOnPos if music else musicOffPos])
            screen.blit(title, titleRect)
        for txt, pos in textOverlays:
            screen.blit(txt, pos)
        pygame.display.flip()


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
                ship.horiz += direction[event.key][0]*speed
                ship.vert += direction[event.key][1]*speed
            elif (event.type == KEYUP 
                and event.key in direction.keys()):
                ship.horiz -= direction[event.key][0]*speed
                ship.vert -= direction[event.key][1]*speed
            elif (event.type == KEYDOWN
                and event.key == K_SPACE):
                Missile.position(ship.rect.midtop)
                missilesFired += 1
                if soundFX:
                    missile_sound.play()
            elif (event.type == KEYDOWN
                and event.key == K_b):
                if bombsHeld > 0:
                    bombsHeld -= 1 
                    newBomb = ship.bomb() 
                    newBomb.add(bombs, alldrawings)
                    if soundFX:
                        bomb_sound.play()
    
    #Collision Detection
        #Aliens
        for alien in Alien.active:
            for bomb in bombs:
                if pygame.sprite.collide_circle(bomb, alien):
                    alien.table()
                    Explosion.position(alien.rect.center)
                    missilesFired += 1
                    aliensLeftThisWave -= 1
                    score += 1
                    if soundFX:
                        alien_explode_sound.play()
            for missile in Missile.active:
                if pygame.sprite.collide_rect(missile, alien):
                    alien.table()
                    missile.table()
                    Explosion.position(alien.rect.center)
                    aliensLeftThisWave -= 1
                    score += 1
                    if soundFX:
                        alien_explode_sound.play()
            if pygame.sprite.collide_rect(alien, ship):
                if ship.shieldUp:
                    alien.table()
                    Explosion.position(alien.rect.center)
                    aliensLeftThisWave -= 1
                    score += 1
                    missilesFired += 1
                    ship.shieldUp = False
                else:
                    ship.alive = False
                    ship.remove(allsprites)
                    Explosion.position(ship.rect.center)
                    if soundFX:
                        ship_explode_sound.play()

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
        waveText = font.render("Wave: "+str(wave), 1, BLUE)
        leftText = font.render("Aliens Left: "+str(aliensLeftThisWave), 1, BLUE)
        scoreText = font.render("Score: "+str(score), 1, BLUE)
        bombText = font.render("Bombs: "+str(bombsHeld), 1, BLUE)
        
        wavePos = waveText.get_rect(topleft=screen.get_rect().topleft)
        leftPos = leftText.get_rect(midtop=screen.get_rect().midtop)
        scorePos = scoreText.get_rect(topright=screen.get_rect().topright)
        bombPos = bombText.get_rect(bottomleft=screen.get_rect().bottomleft)

        text = [waveText, leftText, scoreText, bombText]
        textposition = [wavePos, leftPos, scorePos, bombPos]
    
    #Detertmine when to move to next wave
        if aliensLeftThisWave <= 0:
            if betweenWaveCount > 0:
                betweenWaveCount -= 1
                nextWaveText = font.render('Wave ' + str(wave+1) + ' in', 1, (0,0,255))
                nextWaveNum = font.render(str((betweenWaveCount // clockTime) + 1), 1, (0,0,255))
                text.extend([nextWaveText, nextWaveNum])
                nextWavePos = nextWaveText.get_rect(center=screen.get_rect().center)
                nextWaveNumPos = nextWaveNum.get_rect(midtop=nextWavePos.midbottom)
                textposition.extend([nextWavePos, nextWaveNumPos])
            elif betweenWaveCount == 0:
                wave += 1
                aliensLeftThisWave, aliensThisWave, Alien.numOffScreen = 3*[2*aliensThisWave]
                betweenWaveCount = betweenWaveTime
                
        textOverlays = zip(text, textposition)

    #Update and draw all sprites and text
        screen.blit(background, (0,0), area=pygame.Rect(0,backgroundLoc,500,500))
        backgroundLoc -= speed 
        if backgroundLoc == 0:
            backgroundLoc = 1500
        allsprites.update()
        allsprites.draw(screen)
        alldrawings.update()
        for txt, pos in textOverlays:
            screen.blit(txt, pos)
        pygame.display.flip()

    accuracy = round(score/missilesFired,4) if missilesFired > 0 else 0.0
    isHiScore = len(hiScores) < Database.numScores or score > hiScores[-1][1] 
    name = ''
    nameBuffer = []
    
    while True:
        clock.tick(clockTime)

    #Event Handling
        for event in pygame.event.get():
            if (event.type == QUIT
                or not isHiScore
                and event.type == KEYDOWN 
                and event.key == K_ESCAPE):
                return False
            elif (event.type == KEYDOWN 
                and event.key == K_RETURN
                and not isHiScore):
                return True
            elif (event.type == KEYDOWN
                and event.key in Keyboard.keys.keys()
                and len(nameBuffer) < 8):
                nameBuffer.append(Keyboard.keys[event.key])
                name = ''.join(nameBuffer)
            elif (event.type == KEYDOWN
                and event.key == K_BACKSPACE 
                and len(nameBuffer) > 0):
                nameBuffer.pop()
                name = ''.join(nameBuffer)
            elif (event.type == KEYDOWN
                and event.key == K_RETURN 
                and len(name) > 0):
                Database.setScore(hiScores, (name, score, accuracy))
                return True

        if isHiScore:
            hiScoreText = font.render('HIGH SCORE!', 1, RED)
            hiScorePos = hiScoreText.get_rect(midbottom=screen.get_rect().center)
            scoreText = font.render(str(score), 1, BLUE)
            scorePos = scoreText.get_rect(midtop=hiScorePos.midbottom)
            enterNameText = font.render('ENTER YOUR NAME:', 1, RED)
            enterNamePos = enterNameText.get_rect(midtop=scorePos.midbottom)
            nameText = font.render(name, 1, BLUE)
            namePos = nameText.get_rect(midtop=enterNamePos.midbottom)
            textOverlay = zip([hiScoreText, scoreText, enterNameText, nameText], 
                              [hiScorePos, scorePos, enterNamePos, namePos])
        else:
            gameOverText = font.render('GAME OVER', 1, BLUE)
            gameOverPos = gameOverText.get_rect(center=screen.get_rect().center)
            scoreText = font.render('Score: {}'.format(score), 1, BLUE)
            scorePos = scoreText.get_rect(midtop=gameOverPos.midbottom)
            textOverlay = zip([gameOverText, scoreText], [gameOverPos, scorePos])
                
    #Update and draw all sprites 
        screen.blit(background, (0,0), area=pygame.Rect(0,backgroundLoc,500,500))
        backgroundLoc -= speed
        if backgroundLoc == 0:
            backgroundLoc = 1500
        allsprites.update()
        allsprites.draw(screen)
        alldrawings.update()
        for txt, pos in textOverlay:
            screen.blit(txt, pos)
        pygame.display.flip()

if __name__ == '__main__':
    while(main()):
        pass
