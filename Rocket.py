from direct.showbase.ShowBase import ShowBase
from panda3d.core import TextNode, TransparencyAttrib
from panda3d.core import LPoint3, LVector3
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import Filename, AmbientLight, DirectionalLight
from direct.task.Task import Task
from direct.actor.Actor import Actor
from random import randint, choice, random
from direct.interval.MetaInterval import Sequence
from direct.interval.FunctionInterval import Wait, Func
from direct.gui.OnscreenImage import OnscreenImage
import sys
import math
import random

# Constants:
SPRITE_POS = 55

def loadObject(tex=None, pos=LPoint3(0, 0), depth=SPRITE_POS, scale=1, transparency=True):
    obj = loader.loadModel("models/plane")
    obj.reparentTo(camera)
    # Set initial position and scale.
    obj.setPos(pos.getX(), depth, pos.getY())
    obj.setScale(scale)
    obj.setBin("unsorted", 0)
    obj.setDepthTest(False)

    return obj

class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.timeInitial1 = 0 # helps tracks time
        self.yInitial = 0 # helps track y position of rocket
        
        self.setBackgroundColor((0, 0, 0, 1))
        # Disable the camera trackball controls
        self.disableMouse()
        self.keyMap = {"left": 0, "right": 0, "up": 0, "down":0, "fire": 0}
        self.accept("arrow_left", self.setKey, ["left", True])
        self.accept("arrow_right", self.setKey, ["right", True])
        self.accept("arrow_up", self.setKey, ["up", True])
        self.accept("arrow_down", self.setKey, ["down", True])
        self.accept("space", self.setKey, ["fire", True])
        self.accept("p", self.removeHomeScreen)

        # Creates some lighting
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor((.2, .2, .2, 0.2))
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection((-10, 10, 5))
        directionalLight.setColor((1, 1, 1, 1))
        directionalLight.setSpecularColor((1, 1, 1, 1))
        render.setLight(render.attachNewNode(ambientLight))
        render.setLight(render.attachNewNode(directionalLight))
        
        # Create rocket model
        self.rocket = self.createObjRend("models/rocket16.blend.x", 1, [])
        self.rocket.setPos(0, 10, 0)
        # initialize all variables
        self.rocketSpeed = 0.5
        self.enemySpeed = 0.04 #initial enemy speed
        self.stars, self.coins, self.enemies, self.bullets, self.speedBoosts, self.AIList, self.coinMagnets, self.obstacles, self.lives = ([] for i in range(9))
        self.isSpeeding, self.isAI, self.isMagnetic, self.gameOver, self.hasRocketBuddy, self.hasCoinGun, self.hasObstacleGun, self.readingFeatures, self.readingStore = (False for i in range(9))
        self.endSpeedingTime, self.endAITime, self.endMagneticTime, self.numCoins, self.highScore, self.totalCoins = (0 for i in range(6))
        self.numLives = 3 # player starts out with 3 lives
        self.getLifeObjects()
        self.levelNum = 1 # start on level 1

        ##### READ TEXT FILE #####
        self.inventoryFile = open("RocketInventory.txt","r+")
        self.inventory = self.inventoryFile.readlines()
        self.read_inventory()

        self.totalCoins = int(self.totalCoins)
        self.highScore = float(self.highScore)
        ## Give user appropriate powers
        if self.hasRocketBuddy:
            # if the user has rocket buddy, load model   
            self.buddy = loader.loadModel("models/miniRocket.blend.x")
            self.buddy.setScale(0.4)
            self.buddy.reparentTo(render)
            x, y, z = self.getObjectPos(self.rocket)
            self.buddy.setPos(x + 2, y, z + 2)

        ##### ON-SCREEN TEXT #####
        self.title = OnscreenText(text="SPACE RAIDERS",
                                  parent=base.a2dBottomRight, scale=.1,
                                  align=TextNode.ARight, pos=(-0.1, 0.1),
                                  fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.5))
        self.getOnscreenText("[Space Bar]: Fire", 0.07, -.07 - 0.1, 0.07)
        self.getOnscreenText("Use arrow keys to move", 0.07, -.07 * 2 - 0.1, 0.07)
        self.coinsText =  self.getOnscreenText("Coins:"+ str(self.totalCoins), 0.07, -.07 * 3 - 0.1, 0.07)
        self.levelText =  self.getOnscreenText("Level:"+ str(self.levelNum), 0.07, -.07 * 4 - 0.1, 0.07)
        self.distanceText = self.getOnscreenText("Level:"+ str(0), 0.07, -.07 * 5 - 0.1, 0.07)
        self.powerUpText = self.getOnscreenText("Time left for power up:"+ str(0), 0.07, -.07 * 6 - 0.1, 0.07)

        # DISPLAY IMAGE OF INSTRUCTIONS/DIFFERENT ITEMS IN GAME
        self.imageObject = OnscreenImage(image='models/Summary.png', pos=(0.45, 0, 0.1), scale = (0.75,1,0.9))
        self.displayHomeScreen = True
        taskMgr.add(self.gameLoop, "moveTask")
    
    def getObjectPos(self, object):
        x = object.getX()
        y = object.getY()
        z = object.getZ()
        return x, y, z

    def read_inventory(self):
        for line in self.inventory:
            if ":" in line:
                i = line.index(":")
                s = line[:i]
            if s == "High Score":
                self.highScore = line[i+1:]
                self.highScore = self.highScore[:-1]

            elif s == "Coins":
                self.totalCoins = line[i+1:]
                self.totalCoins = self.totalCoins[:-1]
                
            elif s == "Features":
                self.readingFeatures = True

            if (self.readingFeatures and s == "Rocket buddy"):
                if "No" in line[i:]:
                    self.hasRocketBuddy = False
                else:
                    self.hasRocketBuddy = True

            elif s == "Store":
                self.readingStore = True

    # Records the state of the arrow keys
    def setKey(self, key, value):
        self.keyMap[key] = value
        
    def removeHomeScreen(self):
        self.displayHomeScreen = False
        self.playButton.destroy()
        self.imageObject.destroy()
        taskMgr.add(self.gameLoop, "moveTask")
        
        if self.gameOver == True:
            app.destroy()
            MyApp(True)

    def updateHighScore(self):
        # update high score
        newLine = ""
        for line in self.inventory:
            if "High Score" in line: newLine = "High Score:" + str(self.highScore) + "\n"

        self.inventory[0] = newLine
        self.inventoryFile.truncate(0)
        
        for line in self.inventory:
            self.inventoryFile.write(line)


    def updateCoin(self):
        # update total coins
        self.inventoryFile = open("RocketInventory.txt","r+")
        
        for line in self.inventory:
            if "Coins" in line:
                newLine = "Coins:" + str(self.totalCoins) + "\n"

        self.inventory[1] = newLine
        self.inventoryFile.truncate(0)
        
        for line in self.inventory:
            self.inventoryFile.write(line)

        self.inventoryFile.close()
    
    def getOnscreenText(self, set_text, xpos, ypos, set_scale):
        return OnscreenText(text=set_text, parent=base.a2dTopLeft,
                            pos=(xpos, ypos), fg=(1, 1, 1, 1), align=TextNode.ALeft,
                            shadow=(0, 0, 0, 0.5), scale=set_scale)

    def gameLoop(self, task):
        if self.numLives <= 0:
            self.gameOver = True
            self.displayHomeScreen = True
            self.gameOverText = self. getOnscreenText("Game Over!", 1, -1, 0.1)
            if self.rocket.getY() > float(self.highScore):
                self.highScore = self.rocket.getY()
                self.updateHighScore()
            self.updateCoin()
            return 0
        elif self.displayHomeScreen:
            self.playButton = self.getOnscreenText("Press 'p' to Play!", 0.2, -1, 0.09)
        else:
            dt = globalClock.getDt()
            self.distanceText.destroy() #replace distance text to show new distance
            self.distanceText =  self.getOnscreenText("Distance:"+ str(self.rocket.getY()), 0.07, -.07 * 5 - 0.1, 0.07)
            # Event handling
            self.keyHandling()
            self.moveBullets()
 
            time = round(task.time)
            if time % 2 == 0 and time != self.timeInitial1:         
                for i in range(self.levelNum*2):
                    self.createEnemies()
                self.enemySpeed = self.levelNum / 100 * 4
                self.createObject("models/obstacle.blend.x", self.obstacles) # create two obstacles
                self.createObject("models/obstacle.blend.x", self.obstacles)
                self.createObject("models/coin.blend.x", self.coins)
                if not self.isSpeeding: self.createObject("models/speedBoost1.blend.x", self.speedBoosts)
                if not self.isAI: self.createObject("models/AI.blend.x", self.AIList)
                if not self.isMagnetic: self.createObject("models/CoinMagnet1.blend.x", self.coinMagnets)
                self.timeInitial1 = time

            # move rocket
            rx, ry, rz = self.getObjectPos(self.rocket)
            if self.isSpeeding and not self.isAI: # if rocket is speeding               
                self.display_powerUp_Text(self.endSpeedingTime, 4*self.rocketSpeed, time) 
                if time == self.endSpeedingTime:
                    self.isSpeeding = False
                
            elif self.isAI and not self.isMagnetic and not self.isSpeeding:
                self.display_powerUp_Text(self.endAITime, self.rocketSpeed, time)

                for y in range(int(round(ry)), int(round(ry + 50))):
                    for e in self.enemies:
                        ex, ey, ez = self.getObjectPos(e)
                        if abs(rx-ex) < 3 and abs(y-ey)<3 and abs(rz-ez) < 3:
                            self.fire(self.rocket) # shoot bullet at enemy
                            self.checkBECollision() # remove enemy from screen and list

                # Check if there's an obstacle within 75 units ahead
                for y in range(int(round(ry)), int(round(ry + 75))):
                    for o in self.obstacles:
                        ox, oy, oz = self.getObjectPos(o)
                        if abs(rx-ox) < 3 and abs(y-oy) < 3 and abs(rz-oz) < 3:
                            leftCount, rightCount, lowerCount, upperCount = self.getCount(self.obstacles)
                            if leftCount <= rightCount: self.check_obstacle_helper(lowerCount, upperCount, -0.01, -3.5)
                            elif leftCount > rightCount: self.check_obstacle_helper(lowerCount, upperCount, 0.01, 3.5)
                        
                if time == self.endAITime:
                    self.isAI = False

            elif self.isMagnetic and not self.isAI and not self.isSpeeding:
                self.powerUpText.destroy()
                self.powerUpText = self.getOnscreenText("Time left for power up:"+ str(self.endMagneticTime - time), 0.07, -.07 * 6 - 0.1, 0.07)
                for c in self.coins:
                    self.rocket.setPos(rx, ry + self.rocketSpeed, rz)
                    x, y, z = self.getObjectPos(c)
                    
                    if y - ry <= 50:
                        if rx < x: newX = x - 0.5
                        else: newX = x + 0.5
                        if rz < z: newZ = z - 0.5
                        else: newZ = z + 0.5
                    else:
                        newX = x
                        newZ = z
                    newY = y - 0.5
                    c.setPos(newX, newY, newZ)
                    
                if time == self.endMagneticTime:
                    self.isMagnetic = False
                
            else:
                self.rocket.setPos(rx, ry + self.rocketSpeed, rz)

            self.camera.setPos(0, self.rocket.getY() - 15, 1) # move camera
            self.moveEnemies() # move enemies         
            self.createStars() # create stars
            # remove items once they are off-screen
            self.removeOffScreen([self.stars, self.coins, self.enemies, self.speedBoosts, self.AIList, self.coinMagnets, self.obstacles])
            # remove bullets once they are off-screen
            for b in self.bullets:
                if b.getY() >= self.rocket.getY() + 300:
                    self.bullets.remove(b)
                    b.removeNode()
     
            self.keyMap["fire"] = False
            self.checkCollisions(task) # check for collisions
            self.drawLives()

            # change level number if rocket y pos reaches certain value
            ry = self.rocket.getY()
            if round(ry) % 1000 == 0 and round(ry) != self.yInitial: #increase level by 1 every 1000 units
                self.levelText.destroy()                
                self.levelNum += 1
                self.levelText = self.getOnscreenText("Level:"+ str(self.levelNum), 0.07, -.07 * 4 - 0.1, 0.07)
                self.yInitial = round(ry)

            if self.hasRocketBuddy:
                self.moveBuddy()

            return task.cont

    def display_powerUp_Text(self, endTime, speed, time): #display time and change speed
        rx, ry, rz = self.getObjectPos(self.rocket)
        self.powerUpText.destroy()
        self.powerUpText = self.getOnscreenText("Time left for power up:"+ str(endTime - time), 0.07, -.07 * 6 - 0.1, 0.07)
        self.rocket.setPos(rx, ry + speed, rz)

    def checkCollisions(self, task):
        self.checkBECollision() # check if bullet hits enemy
        self.checkObstaclCollision(self.enemies) # check if rocket hits enemy
        self.checkObstaclCollision(self.obstacles) # check if rocket hits obstacle
        self.checkRCCollision() # check if rocket hits coin
        self.checkRSCollision(task) # rocket hits speed boost
        self.checkRAICollision(task) # rocket hits AI power up
        self.checkRCMCollision(task) # rocket hits coin magnet power up

    def check_obstacle_helper(self, lowerCount, upperCount, num, num2):
        if self.rocket.getX() + num > num2:
            self.rocket.setX(self.rocket.getX() + num)
        else:
            if lowerCount <= upperCount:
                if self.rocket.getZ() - 0.01 > -3.5:
                    self.rocket.setZ(self.rocket.getZ() - 0.01)
                else:
                    self.rocket.setZ(self.rocket.getZ() + num)
                    
            elif upperCount > lowerCount:
                if self.rocket.getZ() + 0.01 < 3.5:
                    self.rocket.setZ(self.rocket.getZ() + 0.01)
                else:
                    self.rocket.setZ(self.rocket.getZ() - 0.01)

    def moveBuddy(self):
        bx, by, bz = self.getObjectPos(self.buddy)
        if self.isSpeeding: self.buddy.setPos(bx, by + 4*self.rocketSpeed, bz)
        else: self.buddy.setPos(bx, by + self.rocketSpeed, bz)

        for y in range(int(round(by)), int(round(by + 50))): # Check if there's an obstacle within 50 units ahead
            for e in self.enemies:
                ex, ey, ez = self.getObjectPos(e)
                if abs(bx-ex) < 2 and abs(y-ey) < 2 and abs(bz-ez) < 2:
                    self.fire(self.buddy) # shoot bullet at enemy
                    self.checkBECollision() # remove enemy from screen and list

                if abs(bx-ex) < 3 and abs(y-ey) < 3 and abs(bz-ez) < 3:
                    leftCount, rightCount, upperCount, lowerCount = self.getCount(self.enemies)
                    buddySpeed = 0.01
                    if leftCount >= rightCount:
                        cond = self.buddy.getX() - buddySpeed > -3
                        self.move_buddy_helper(lowerCount, upperCount, buddySpeed, cond, -1)                        
                    elif leftCount < rightCount:
                        cond = self.buddy.getX() + buddySpeed < 3
                        self.move_buddy_helper(lowerCount, upperCount, buddySpeed, cond, 1)

    def set_x_and_z():
        self.buddy.setX(self.rocket.getX())
        self.buddy.setZ(self.rocket.getZ())

    def move_buddy_helper(self, lowerCount, upperCount, buddySpeed, cond, sign):
        if cond:
            self.buddy.setX(self.buddy.getX() + (sign * buddySpeed))
        else:
            if lowerCount >= upperCount:
                if self.buddy.getZ() - buddySpeed > -3:
                    self.buddy.setZ(self.buddy.getZ() - buddySpeed)
                else:
                    self.set_x_and_z()
            elif upperCount < lowerCount:
                if self.buddy.getZ() + buddySpeed < 3:
                    self.buddy.setZ(self.buddy.getZ() + buddySpeed)
                else:
                    self.set_x_and_z()

    def removeOffScreen(self, list):
        for items in list:
            for x in items:
                if x.getY() <= 0:
                    items.remove(x)
                    x.removeNode()
       
    def getCount(self, items):
        leftCount, rightCount, lowerCount, upperCount = 0, 0, 0, 0
        for i in items:
            x, y, z = self.getObjectPos(i)
            if x < 0: leftCount += 1
            else: rightCount += 1
            if z < 0: lowerCount += 1
            else: upperCount += 1
        return leftCount, rightCount, upperCount, lowerCount
        
    def keyHandling(self): # rocket reacts to arrow keys and shoots bullet if spacebar is hit
        if self.keyMap["left"]:
            self.rocket.setX(self.rocket.getX() - 0.25)
            self.keyMap["left"] = not self.keyMap["left"]
                
        elif self.keyMap["right"]:
            self.rocket.setX(self.rocket.getX() + 0.25)
            self.keyMap["right"] = not self.keyMap["right"]

        elif self.keyMap["up"]:
            self.rocket.setZ(self.rocket.getZ() + 0.25)
            self.keyMap["up"] = not self.keyMap["up"]

        elif self.keyMap["down"]:
            self.rocket.setZ(self.rocket.getZ() - 0.25)
            self.keyMap["down"] = not self.keyMap["down"]
            
        elif self.keyMap["fire"]:
            self.fire(self.rocket)

    def createObjRend(self, model, scale, obj_list):
        object = loader.loadModel(model)
        object.setScale(scale)
        object.reparentTo(render)
        obj_list.append(object)
        return object

    def getLifeObjects(self):
        for count in range(self.numLives):
            self.life = self.createObjRend("models/life.blend.x" , 0.5, self.lives)
            listX = [-12, -10, -8]
            y = self.rocket.getY() + 25
            z = -8
            self.life.setPos(listX[count], y, z)
                                          
    def drawLives(self):
        for l in self.lives:
            x, y, z = self.getObjectPos(l)
            if self.isSpeeding:
                l.setPos(x, y + 4*self.rocketSpeed , z)
            else:
                l.setPos(x, y + self.rocketSpeed , z)                
               
    def createStars(self):
        self.star = self.createObjRend("models/star3.blend.x" , 0.05, self.stars)
        x = random.randint(-20, 20)
        z = random.randint(-20, 20)
        self.star.setPos(x, self.rocket.getY() + 150, z)

    def createObject(self, filename, obj_list):
        object = self.createObjRend(filename , 0.5, obj_list)
        x = random.randint(-7, 7)
        z = random.randint(-7, 7)
        object.setPos(x, self.rocket.getY() + 150, z)        

    def createEnemies(self):
        self.createObject("models/enemy10.blend.x", self.enemies)

    def fire(self, rocket): 
        xPos, yPos, zPos = self.getObjectPos(rocket)
        yPos = rocket.getY() + 5
        self.bullet = self.createObjRend("models/bullet.blend.x", 0.7, self.bullets)
        self.bullet.setPos(xPos, yPos, zPos)

    def moveBullets(self):
        for b in self.bullets:
            x, y, z = self.getObjectPos(b)
            b.setPos(x, y + 5, z)

    def checkBECollision(self):
        for b in self.bullets:
            x, y, z = self.getObjectPos(b)
            for e in self.enemies:
                ex, ey, ez = self.getObjectPos(e)
                if abs(x-ex) < 3 and abs(y-ey)<3 and abs(z-ez) < 3:
                    e.removeNode()
                    self.enemies.remove(e)

    def checkObstaclCollision(self, obj_list):
        x, y, z = self.getObjectPos(self.rocket)
        for o in obj_list:
            ox, oy, oz = self.getObjectPos(o)
            if abs(x-ox) < 2 and abs(y-oy) < 2 and abs(z-oz) < 2:
                o.removeNode()
                obj_list.remove(o)
                if self.numLives != 0 and not self.isSpeeding and not self.isAI:
                    self.numLives -= 1
                    self.lives.pop()
                else:
                    gameOver = True

    def checkRCCollision(self): # check if rocket hits coins
        x, y, z = self.getObjectPos(self.rocket)
        for c in self.coins:
            cx, cy, cz = self.getObjectPos(c)
            if abs(x-cx) < 2 and abs(y-cy) < 2 and abs(z-cz) < 2:
                c.removeNode()
                self.coins.remove(c)
                self.totalCoins += 1
                self.coinsText.destroy()
                self.coinsText = self.getOnscreenText("Coins:"+ str(self.totalCoins), 0.07, -.07 * 3 - 0.1, 0.07)

    def checkPowerUpCollision(self, task, obj_list, cond1, cond2, setcond, setTime, time):
        x, y, z = self.getObjectPos(self.rocket)
        for obj in obj_list:
            ox, oy, oz = self.getObjectPos(obj)
            if abs(x-ox) < 2 and abs(y-oy)< 2 and abs(z-oz) < 2:
                obj.removeNode()
                obj_list.remove(obj)
                if not cond1 and not cond2:
                    setcond = True
                    time = round(task.time) + setTime

        return time, setcond

    def checkRSCollision(self, task): # check if rocket hits speed boost
        self.endSpeedingTime, self.isSpeeding = self.checkPowerUpCollision(task, self.speedBoosts, self.isAI, self.isMagnetic, self.isSpeeding, 5, self.endSpeedingTime)     

    def checkRAICollision(self, task): # check if rocket hits AI power up
        self.endAITime, self.isAI = self.checkPowerUpCollision(task, self.AIList, self.isSpeeding, self.isMagnetic, self.isAI, 7, self.endAITime)  

    def checkRCMCollision(self, task): # check if rocket hits coin magnet
        self.endMagneticTime, self.isMagnetic = self.checkPowerUpCollision(task, self.coinMagnets, self.isSpeeding, self.isAI, self.isMagnetic, 10, self.endMagneticTime) 
    def moveEnemies(self): # after y position of enemy reaches less than 75, it moves towards rocket
        for e in self.enemies:
            rx, ry, rz = self.getObjectPos(self.rocket)
            x, y, z = self.getObjectPos(e)  
            if y - ry <= 75 and y - ry >= 10:
                if rx < x:  newX = x - self.enemySpeed
                else: newX = x + self.enemySpeed
                if rz < z: newZ = z - self.enemySpeed
                else: newZ = z + self.enemySpeed
            else:
                newX = x
                newZ = z

            newY = y - 0.5
            e.setPos(newX, newY, newZ)

    def spinCameraTask(self, task):
        angleDegrees = task.time * 6.0
        angleRadians = angleDegrees * (pi / 180.0)
        self.camera.setPos(20 * sin(angleRadians), -20.0 * cos(angleRadians), 3)
        self.camera.setHpr(angleDegrees, 0, 0)
        return Task.cont

app = MyApp()
app.run()
 