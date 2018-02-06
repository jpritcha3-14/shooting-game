import pygame
import random
import math
from load import load_image


class MasterSprite(pygame.sprite.Sprite):
    allsprites = None
    speed = None


class Explosion(MasterSprite):
    pool = pygame.sprite.Group()
    active = pygame.sprite.Group()

    def __init__(self):
        super().__init__()
        self.image, self.rect = load_image('explosion.png', -1)
        self.linger = MasterSprite.speed * 3

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

    def __init__(self):
        super().__init__()
        self.image, self.rect = load_image('missile.png', -1)
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()

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
        newpos = self.rect.move(0, -4 * MasterSprite.speed)
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
        pygame.draw.circle(
            pygame.display.get_surface(),
            pygame.Color(0, 0, 255, 128),
            self.rect.center, self.radius, 3)
        if (self.rect.center[1] - self.radius <= self.area.top
            and self.rect.center[1] + self.radius >= self.area.bottom
            and self.rect.center[0] - self.radius <= self.area.left
                and self.rect.center[0] + self.radius >= self.area.right):
            self.kill()


class Powerup(MasterSprite):
    def __init__(self, kindof):
        super().__init__()
        self.image, self.rect = load_image(kindof + '_powerup.png', -1)
        self.original = self.image
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.rect.midtop = (random.randint(
                            self.area.left + self.rect.width // 2,
                            self.area.right - self.rect.width // 2),
                            self.area.top)
        self.angle = 0

    def update(self):
        center = self.rect.center
        self.angle = (self.angle + 2) % 360
        rotate = pygame.transform.rotate
        self.image = rotate(self.original, self.angle)
        self.rect = self.image.get_rect(
            center=(
                center[0],
                center[1] +
                MasterSprite.speed))


class BombPowerup(Powerup):
    def __init__(self):
        super().__init__('bomb')
        self.pType = 'bomb'


class ShieldPowerup(Powerup):
    def __init__(self):
        super().__init__('shield')
        self.pType = 'shield'


class Ship(MasterSprite):
    def __init__(self):
        super().__init__()
        self.image, self.rect = load_image('ship.png', -1)
        self.original = self.image
        self.shield, self.rect = load_image('ship_shield.png', -1)
        self.screen = pygame.display.get_surface()
        self.area = self.screen.get_rect()
        self.rect.midbottom = (self.screen.get_width() // 2, self.area.bottom)
        self.radius = max(self.rect.width, self.rect.height)
        self.alive = True
        self.shieldUp = False
        self.vert = 0
        self.horiz = 0

    def initializeKeys(self):
        keyState = pygame.key.get_pressed()
        self.vert = 0
        self.horiz = 0
        if keyState[pygame.K_w]:
            self.vert -= 2 * MasterSprite.speed
        if keyState[pygame.K_a]:
            self.horiz -= 2 * MasterSprite.speed
        if keyState[pygame.K_s]:
            self.vert += 2 * MasterSprite.speed
        if keyState[pygame.K_d]:
            self.horiz += 2 * MasterSprite.speed

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

    def __init__(self, color):
        super().__init__()
        self.image, self.rect = load_image(
            'space_invader_' + color + '.png', -1)
        self.initialRect = self.rect
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.loc = 0
        self.radius = min(self.rect.width // 2, self.rect.height // 2)

    @classmethod
    def position(cls):
        if len(cls.pool) > 0 and cls.numOffScreen > 0:
            alien = random.choice(cls.pool.sprites())
            if isinstance(alien, Crawly):
                alien.rect.midbottom = (random.choice(
                    (alien.area.left, alien.area.right)),
                    random.randint(
                    (alien.area.bottom * 3) // 4,
                    alien.area.bottom))
            else:
                alien.rect.midtop = (random.randint(
                    alien.area.left
                    + alien.rect.width // 2,
                    alien.area.right
                    - alien.rect.width // 2),
                    alien.area.top)
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
        self.loc = self.loc + MasterSprite.speed
        if self.rect.top > self.area.bottom:
            self.table()
            Alien.numOffScreen += 1

    def table(self):
        self.kill()
        self.add(self.pool)


class Siney(Alien):
    def __init__(self):
        super().__init__('green')
        self.amp = random.randint(self.rect.width, 3 * self.rect.width)
        self.freq = (1 / 20)
        self.moveFunc = lambda: (self.amp * math.sin(self.loc * self.freq), 0)


class Roundy(Alien):
    def __init__(self):
        super().__init__('red')
        self.amp = random.randint(self.rect.width, 2 * self.rect.width)
        self.freq = 1 / (20)
        self.moveFunc = lambda: (
            self.amp *
            math.sin(
                self.loc *
                self.freq),
            self.amp *
            math.cos(
                self.loc *
                self.freq))


class Spikey(Alien):
    def __init__(self):
        super().__init__('blue')
        self.slope = random.choice(list(x for x in range(-3, 3) if x != 0))
        self.period = random.choice(list(4 * x for x in range(10, 41)))
        self.moveFunc = lambda: (self.slope * (self.loc % self.period)
                                 if self.loc % self.period < self.period // 2
                                 else self.slope * self.period // 2
                                 - self.slope * ((self.loc % self.period)
                                 - self.period // 2), 0)


class Fasty(Alien):
    def __init__(self):
        super().__init__('white')
        self.moveFunc = lambda: (0, 3 * self.loc)


class Crawly(Alien):
    def __init__(self):
        super().__init__('yellow')
        self.moveFunc = lambda: (self.loc, 0)

    def update(self):
        horiz, vert = self.moveFunc()
        horiz = (-horiz if self.initialRect.center[0] == self.area.right
                 else horiz)
        if (horiz + self.initialRect.left > self.area.right
                or horiz + self.initialRect.right < self.area.left):
            self.table()
            Alien.numOffScreen += 1
        self.rect = self.initialRect.move((horiz, vert))
        self.loc = self.loc + MasterSprite.speed
