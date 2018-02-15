A simple alien shooting game built in python3 using pygame
==========================================================

* Aliens have different movement types based on their colors
* Missiles kill single aliens, the ship has an unlimited supply
* Bombs kill all aliens on screen and are scarce, use them wisely
* Powerups drop periodically and give either more bombs or a shield
* The shield powerup allows the ship to collide with 1 alien and survive
* High scores are recorded in an SQLite database

Game Controls
-------------

**MENUS**

* w/s: move cursor
* enter/return: confirm selections or submit a high score

**GAME**

* w/a/s/d: move the ship
* space: shoot a missile
* b: drop a bomb

Instructions
------------

This program requires the [pygame library](http://www.pygame.org/).
You may install it like this:
```
python3 -m pip install pygame --user
```

Clone this repository to your local disk using Git, e.g.
```
git clone https://github.com/jpritcha3-14/shooting-game.git
cd shooting-game
```

Then run the shooting_game program from your terminal using Python, e.g.
```
python3 shooting_game.py
```

How To Contribute
-----------------

Please, run [Flake8](http://flake8.pycqa.org/) and, optionally, [Pylint](
http://pylint.readthedocs.io/) before committing changes and [opening a
pull request](https://github.com/jpritcha3-14/shooting-game/pulls).

Acknowledgements
----------------

Game title made with [textcraft.net](https://textcraft.net/)

Music is by [joshuaempyre](https://freesound.org/people/joshuaempyre/), and was converted to an OGG file from the original WAV.  It is used under a [Creative Commons Attribution 3.0 License](https://creativecommons.org/licenses/by/3.0/legalcode)
