from PIL import Image, ImageColor
import sys
import math
from decimal import *
import queue

# globals to cut down on arguments, sorry for not as proper coding
colorArray = []
eArray = []
season = ""
slowList = []
pathDist = 0

# This will take an rgb value and turn it into hex code
def rgb2hex(r,g,b):
    l = "#{:02x}{:02x}{:02x}".format(r,g,b)
    return l

# this method should open an image and provide an
# array of the color values
def processImage(mapPic, season,footPathQ):
    cArray = [0] * 395
    for i in range(395):
        cArray[i] = [0] * 500
    # breaks up image into 2d array
    im = Image.open(mapPic)
    pix = im.load()
    for i in range(395):
        for j in range(500):
            p = list(pix[i,j])
            val = rgb2hex(p[0],p[1],p[2])
            if(season == "fall"):
                if(val == "#000000" or val == "#473303"):
                    footPathQ.append([i,j])
            cArray[i][j] = val
    return cArray

# this method will take the elevation file and store that into a
# 2 dimentional array. It will ignore the last 5 pixles
def processElevation(elev):
    eleArray = [0] * 395
    for i in range(395):
        eleArray[i] = [0] * 500
    i = 0
    j = 0
    # breaks of file into 2d array, fuck it being flipped, took forever for me to figure out
    with open(elev) as f:
        for line in f:
            line = line.strip()
            elevationLines = line.split(" ")
            j = 0
            for elevations in elevationLines:
                if(j<395):
                    if(elevations!=""):
                        eleArray[j][i] = float(elevations)
                        j = j+1
            i = i+1
    return eleArray

# This will get all the coordinates for the paths
def processPath(pathFile):
    pathList = []
    with open(pathFile) as f:
        for line in f:
            line = line.strip()
            lineList = line.split(" ")
            for element in lineList:
                pathList.append(int(element))
    return pathList

# this will make a new state array that is useful for keeping track of who
# has what or their calculated distance
def mkState():
    stateArray = [0] * 395
    for i in range(395):
        stateArray[i] = [0] * 500
    # makes a bunch of states for it to help me with tracking stuff
    for i in range(395):
        for j in range(500):
            dict = {
                "parent": None,
                "pixTravel":0,
                "distance": 0,
                "total": 0,
                "diagonal":0,
                "slower":False
            }
            stateArray[i][j] = dict
    return stateArray

# this function assigns some speed to the different terrains
def colorSpeed(color):
    if(color == "#f89412"):
        return 2.4
    elif (color == "#ffc000"):
        return 4.5
    elif (color == "#ffffff"):
        return 2.4
    elif (color == "#02d03c"):
        return 3
    elif (color == "#028828"):
        return 5
    elif (color == "#054918"):
        return 1000000
    elif (color == "#0000ff"):
        return 7
    elif (color == "#473303"):
        return 1
    elif (color == "#000000"):
        return 1
    elif (color == "#cd0065"):
        return 10000000
    elif (color == "#03fcf8"):
        return 3.6
    elif(color == "#8a4f04"):
        return 4

# this function will calucate the degree of the elevations
def gradeCalc(startEl, endEl, dist):
    diff = endEl - startEl
    return math.degrees(math.atan(diff/dist))

# this will assign a speed to the different slopes of the ground
def gradeSpeed(startEl, endEl, dist):
    gradeDeg = gradeCalc(startEl, endEl, dist)
    if(gradeDeg>0):
        if(gradeDeg<=5):
            return 1.3
        elif(gradeDeg<=10):
            return 1.9
        elif(gradeDeg<=15):
            return 2.4
        elif(gradeDeg<=20):
            return 3.1
        elif(gradeDeg<=25):
            return 3.6
        elif(gradeDeg<=30):
            return 4.5
        elif(gradeDeg<=35):
            return 5.3
        elif(gradeDeg<=40):
            return 8.9
        else:
            return 100
    else:
        if(gradeDeg>=-5):
            return 1.3
        elif(gradeDeg>=-10):
            return 1.5
        elif(gradeDeg>=-15):
            return 2
        elif(gradeDeg>=-20):
            return 2.4
        elif(gradeDeg>=-25):
            return 3.9
        elif(gradeDeg>=-30):
            return 4.6
        elif(gradeDeg>=-35):
            return 5.3
        elif(gradeDeg>=-40):
            return 8.7
        else:
            return 100

# predition for shortest possible path
def getStraightLine(x,y ,endx,endy):
    xDif = abs(x-endx)*10.29
    yDif = abs(y - endy)*7.55
    return (1.3*1*math.sqrt(math.pow(xDif, 2) + math.pow(yDif, 2)))

# this checks to see if a state has a parent (i.e. they have been visited by someone else)
def hasParent(x,y,state):
    if(state[x][y]["parent"]==None):
        return False
    else:
        return True

# this function just gets the elevation at an x y coordinate
def getElevation(x,y):
    global eArray
    return eArray[x][y]

# this gets the color of some pixel
def getColor(x,y):
    global colorArray
    col = colorArray[x][y]
    return col

# this function will determine if the current distance for the node is greater than or
# less than the distance it could have from the goal node. If the distance is less then
# this function will determine that the parents should be replaced and return true.
# false otherwise
def canReplace(startX, startY, useX, useY, stateArray):
    global colorArray
    global eArray
    state1 = stateArray[startX][startY]
    state2 = stateArray[useX][useY]
    traveledD = getNodeDistance(startX, startY, useX, useY, stateArray)
    SL = state2["diagonal"]
    if(traveledD+SL <state2["total"]):
        return True
    else:
        return False


# This will get the sum of the current traveled distance so far and the distance it took to
# travel through the current node into the next node.
def getNodeDistance(startX, startY, nextX, nextY, stateArray):
    global colorArray
    global eArray
    # gets the  states
    state1 = stateArray[startX][startY]

    # sets up initial travel distance
    movementDist = state1["distance"]
    travelDistance = 0
    mD = 0

    if(startX==nextX):
        mD = 7.55
    elif(startY==nextY):
        mD = 10.29

    # math calculations for distance traveled
    elevStart = getElevation(startX, startY)
    elevFinish = getElevation(nextX, nextY)
    gSpeed = gradeSpeed(elevStart,elevFinish,mD)
    cSpeed = colorSpeed(getColor(startX,startY))
    travelDistance = (mD+ abs(elevFinish - elevStart)) * gSpeed * cSpeed
    if (state1["slower"] == True):
        travelDistance = travelDistance*2.2
    return travelDistance+movementDist

# this function will run a calculation for a pixel and the one it wants to travel to
# checks if it has been seen before and will replace the pixel info with new info
# if it can reach that pixel faster. If it hasnt been seen then it does the normal
# calculations
def doCal(stateArray,pq,xCord,yCord,useX,useY,goalX,goalY):
    if (hasParent(useX, useY, stateArray)):
        if (canReplace(xCord, yCord, useX, useY, stateArray)):
            traveledD = getNodeDistance(xCord, yCord, useX, useY, stateArray)
            SL = getStraightLine(useX, useY, goalX, goalY)
            total = traveledD + SL
            st = stateArray[useX][useY]
            st["parent"] = [xCord, yCord]
            st["distance"] = traveledD
            st["total"] = total
            st["diagonal"] = SL
            elevStart = getElevation(xCord, yCord)
            elevFinish = getElevation(useX, useY)
            mD=4
            if(abs(xCord-useX)==0):
               mD= 7.55
            else:
                mD=10.29

            st["pixTravel"] = mD + abs(elevFinish - elevStart)
            pq.append((total, [useX, useY]))

    # put on queue and update stuff
    else:
        traveledD = getNodeDistance(xCord, yCord, useX, useY, stateArray)
        SL = getStraightLine(useX, useY, goalX, goalY)
        total = traveledD + SL
        st = stateArray[useX][useY]
        st["parent"] = [xCord, yCord]
        st["distance"] = traveledD
        st["total"] = total
        st["diagonal"] = SL
        elevStart = getElevation(xCord, yCord)
        elevFinish = getElevation(useX, useY)
        mD = 4
        if (abs(xCord - useX) == 0):
            mD = 7.55
        else:
            mD = 10.29

        st["pixTravel"] = mD + abs(elevFinish - elevStart)

        pq.append((total, [useX, useY]))

# does the backtracking for the path so then it can properly get the path and the distance
# before everything is reset
def doBackTrack(goalX, goalY, stateArray,outArr):
    s1 = stateArray[goalX][goalY]
    global pathDist
    pathDist = s1["pixTravel"]+pathDist
    if(goalX == s1["parent"][0] and goalY == s1["parent"][1]):
        outArr[goalX][goalY] = "#d442f5"
        return outArr
    else:
        outArr[goalX][goalY] = "#d442f5"
        nextX = s1["parent"][0]
        nextY = s1["parent"][1]
        return doBackTrack(nextX,nextY,stateArray,outArr)

#this function will start my a* search
# it will constantly run through the priority queue until
# it has found all of the goal states
def search(stateArray, pathList, pq, goalX, goalY, outArr):
    while(len(pq)>0):
        nodeCords = pq.pop()
        xCord = nodeCords[1][0]
        yCord = nodeCords[1][1]
        # if we found a goals state, time to reset
        if(xCord== goalX and yCord == goalY):
            # plots path onto aray
            outArr = doBackTrack(goalX,goalY,stateArray,outArr)
            # if theres more points then it must reset states and pq
            if(len(pathList)>0):
                stateArray = mkState()
                global season
                if(season == "fall"):
                    global slowList
                    for e in slowList:
                        stateArray[e[0]][e[1]]["slower"] = True
                startX = goalX
                startY = goalY
                goalX = pathList.pop()
                goalY = pathList.pop()

                pq = []
                stateInitial = stateArray[startX][startY]
                stateInitial["diagonal"] = getStraightLine(startX, startY, goalX, goalY)
                stateInitial["total"] = getStraightLine(startX, startY, goalX, goalY)
                stateInitial["parent"] = [startX, startY]
                pq.append((stateArray[startX][startY]["diagonal"], [startX, startY]))
            # we are done
            else:
                return outArr

        # this is checking the adjacent pixels
        else:
            if(xCord>0):
                useX = xCord-1
                useY = yCord
                doCal(stateArray,pq,xCord,yCord,useX,useY,goalX,goalY)

            if(xCord<394):
                useX = xCord + 1
                useY = yCord
                doCal(stateArray,pq,xCord,yCord,useX,useY,goalX,goalY)

            if(yCord>0):
                useX = xCord
                useY = yCord-1
                doCal(stateArray,pq,xCord,yCord,useX,useY,goalX,goalY)

            if(yCord<499):
                useX = xCord
                useY = yCord+1
                doCal(stateArray,pq,xCord,yCord,useX,useY,goalX,goalY)
            pq.sort()
            pq.reverse()
    return outArr

# this will be used to update the image at the end of the search
def colorImage(outArr,outPut):
    im = Image.open(outPut)
    im.convert("RGB")
    pix = im.load()
    for i in range(395):
        for j in range(500):
            input = outArr[i][j]
            image = ImageColor.getrgb(input)
            pix[i,j] = image
    im.save(outPut)

# this will set the boolean value for all pixels when they are being processed so that it will
# be easier to determine their value at runtime on if the path should be slowed down
def fallTime(footList,stateArray):
    global colorArray
    for e in footList:
        x = e[0]
        y = e[1]
        if(x>0):
            if(colorArray[x-1][y] == "#ffffff"):
                stateArray[x][y]["slower"]=True
        if(x<394):
            if (colorArray[x + 1][y] == "#ffffff"):
                stateArray[x][y]["slower"] = True
        if(y>0):
            if (colorArray[x][y-1] == "#ffffff"):
                stateArray[x][y]["slower"] = True
        if(y<499):
            if (colorArray[x][y+1] == "#ffffff"):
                stateArray[x][y]["slower"] = True
        if(stateArray[x][y]["slower"]==True):
            global slowList
            slowList.append([x,y])
    return stateArray

# This will find the water's edge and return a queue with them
def findEdge(waterList):
    global colorArray
    for i in range(395):
        for j in range(500):
            color = colorArray[i][j]
            b = False
            if(color == "#0000ff"):
                if (i > 0):
                    if (colorArray[i - 1][j] != "#0000ff"):
                        b = True
                if (i < 394):
                    if (colorArray[i + 1][j] != "#0000ff"):
                        b = True
                if (j > 0):
                    if (colorArray[i][j - 1] != "#0000ff"):
                        b = True
                if (j < 499):
                    if (colorArray[i][j + 1] != "#0000ff"):
                        b = True
                if (b == True):
                    global season
                    if(season == "spring"):
                        waterList.put([i, j,16])
                    else:
                        waterList.put([i,j,7])
    return waterList

# this is the water bfs which will go through the queue
# and constantly lay down ice as it is getting searched
def waterBfs(seen,waterList):
    global colorArray
    while(not waterList.empty()):
        e = waterList.get()
        x = e[0]
        y=e[1]
        depth = e[2]
        if(depth>0):
            colorArray[x][y] = "#03fcf8"
            if (x > 0):
                if (colorArray[x - 1][y] == "#0000ff" and seen[x-1][y]==False):
                    seen[x-1][y]=True
                    waterList.put([x-1,y,depth-1])
            if (x < 394):
                if (colorArray[x + 1][y] == "#0000ff" and seen[x+1][y]==False):
                    seen[x + 1][y] = True
                    waterList.put([x + 1, y, depth - 1])
            if (y > 0):
                if (colorArray[x][y - 1] == "#0000ff" and seen[x][y-1]==False):
                    seen[x][y-1] = True
                    waterList.put([x, y-1, depth - 1])
            if (y < 499):
                if (colorArray[x][y + 1] == "#0000ff" and seen[x][y+1]==False):
                    seen[x][y+1] = True
                    waterList.put([x, y+1, depth - 1])

# This is the water search function which will set up the ice map
def waterSearch(waterList):
    seen = [0] * 395
    for i in range(395):
        seen[i] = [0] * 500
    for i in range(395):
        for j in range(500):
            seen[i][j] = False
    waterBfs(seen,waterList)

# this will run for all elements in the waterList queue so that it will put down the
# appropriate amount of mdu
def mudBfs(seen, waterList):
    global colorArray
    global eArray
    while(not waterList.empty()):
        e = waterList.get()
        x = e[0]
        y = e[1]
        depth = e[2]
        if(depth!=0):
            sElev=eArray[x][y]
            if(colorArray[x][y]!="#0000ff"):
                colorArray[x][y] = "#8a4f04"
            if (x > 0):
                endElev = eArray[x-1][y]
                nextHeight = endElev-sElev
                if(nextHeight<=1):
                    if (colorArray[x - 1][y] != "#0000ff" and seen[x-1][y]==False and colorArray[x - 1][y] != "#cd0065"):
                        seen[x-1][y]=True
                        waterList.put([x-1,y,depth-1])
            if (x < 394):
                endElev = eArray[x + 1][y]
                nextHeight = endElev-sElev
                if (nextHeight<=1):
                    if (colorArray[x + 1][y] != "#0000ff"and seen[x+1][y]==False and colorArray[x + 1][y] != "#cd0065"):
                        seen[x+1][y] = True
                        waterList.put([x+1,y,depth-1])
            if (y > 0):
                endElev = eArray[x][y-1]
                nextHeight = endElev-sElev
                if (nextHeight <=1):
                    if (colorArray[x][y - 1] != "#0000ff"and seen[x][y-1]==False and colorArray[x][y-1] != "#cd0065"):
                        seen[x][y-1]=True
                        waterList.put([x,y-1,depth-1])
            if (y < 499):
                endElev = eArray[x][y+1]
                nextHeight = endElev-sElev
                if (nextHeight<=1):
                    if (colorArray[x][y + 1] != "#0000ff" and seen[x][y+1]==False and colorArray[x][y+1] != "#cd0065"):
                        seen[x][y+1]=True
                        waterList.put([x,y+1,depth-1])

# does the mud search
def mudSearch(waterList):
    seen = [0]*395
    for i in range(395):
        seen[i] = [0] *500
    for i in range(395):
        for j in range(500):
            seen[i][j] = False
    mudBfs(seen,waterList)

def main():
    if len(sys.argv)<6:
        sys.stderr("Usage: Terrain.png mmp.txt path-file season outputImage-flie")
        sys.exit(1)
    else:
        # break up inputs
        mapPic = sys.argv[1]
        elevation = sys.argv[2]
        pathFile = sys.argv[3]
        global season
        season = sys.argv[4].lower()
        outPut = sys.argv[5]

        # gets arguments into usable forms
        footList = []
        global colorArray
        colorArray = processImage(mapPic,season,footList)
        outArr = processImage(mapPic, None, None)
        global eArray
        eArray = processElevation(elevation)
        pathList = processPath(pathFile)
        pathList.reverse()
        stateArray = mkState()
        sys.setrecursionlimit(10**7)

        # checking for seasons
        if(season == "fall"):
            stateArray = fallTime(footList,stateArray)
        elif(season == "winter" or season == "spring"):
            waterList = queue.Queue()
            waterList = findEdge(waterList)
            if(season == "winter"):
                waterSearch(waterList)
            else:
                mudSearch(waterList)
            for i in range(395):
                for j in range(500):
                    outArr[i][j]= str(colorArray[i][j])

        # set up for right before the search
        startX = pathList.pop()
        startY = pathList.pop()
        goalX = pathList.pop()
        goalY = pathList.pop()

        # setting up the "priority queue" for its first element
        pq = []
        stateInitial = stateArray[startX][startY]
        stateInitial["diagonal"]= getStraightLine(startX,startY,goalX,goalY)
        stateInitial["total"]= getStraightLine(startX,startY,goalX,goalY)
        stateInitial["parent"] = [startX,startY]
        pq.append((stateArray[startX][startY]["diagonal"], [startX,startY]))

        # search, saving the finished path and then pringing out the traveled distance
        search( stateArray, pathList, pq, goalX, goalY, outArr)

        colorImage(outArr,outPut)
        global pathDist
        print(pathDist)
        
if __name__ == "__main__":
    main()