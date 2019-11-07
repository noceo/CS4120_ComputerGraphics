from tkinter import *
import sys

WIDTH = 700  # width of canvas
HEIGHT = 700  # height of canvas

HPSIZE = 3  # half of point size (must be integer)
CLSIZE = 4  # clip line size
FCOLOR = "#000000"  # black (fill color)
BCOLOR = "#000000"  # blue (boundary color)

clipRegion = []  # clipping rectangle

pointList = []  # list of points
elementList = []  # list of elements (used by Canvas.delete(...))


class Point:
    """ Point consists of coordinates and region code """

    def __init__(self, co, cr):
        self.coords = co
        # region code
        self.reCode = 8 * (co[1] < cr[1][1]) + 4 * (co[1] > cr[0][1]) + 2 * (co[0] > cr[1][0]) + (co[0] < cr[0][0])


def normalizeClipRegion(clipRegion):
    """ normalize clip region to point list [lower left, upper right] """
    ll = list(map(min, zip(*clipRegion)))  # lower left corner
    ur = list(map(max, zip(*clipRegion)))  # upper right corner
    return [[ll[0], ur[1]], [ur[0], ll[1]]]


def drawPoints():
    """ draw oints """
    for p in pointList:
        element = can.create_oval(p.coords[0] - HPSIZE, p.coords[1] - HPSIZE,
                                  p.coords[0] + HPSIZE, p.coords[1] + HPSIZE,
                                  fill=FCOLOR, outline=BCOLOR)
        elementList.append(element)


def drawBox():
    """ use first and second point in pointlist to draw a box"""
    if len(pointList) > 1:
        element = can.create_rectangle(pointList[0].coords, pointList[1].coords, width=3)
        elementList.append(element)


def drawLines():
    """ use third and next points in pointlist to draw lines"""
    for line in zip(pointList[2::2], pointList[3::2]):
        lc = lineCase(line)
        if lc == 0:
            print("line complete inside rectangle!")
            element = can.create_line(line[0].coords, line[1].coords, width=CLSIZE)
            elementList.append(element)
        elif lc == -1:
            print("line not visible!")
            element = can.create_line(line[0].coords, line[1].coords, width=1)
            elementList.append(element)
        else:
            print("need further tests... linecode: ", lc)
            element = can.create_line(line[0].coords, line[1].coords, width=1)
            elementList.append(element)
            newLine = calcNewLine(line, lc, clipRegion)
            if newLine:
                element = can.create_line(newLine, width=CLSIZE)
                elementList.append(element)


def lineCase(line):
    """ Cohen-Sutherland Algorithm. Use region codes of line points to determine wether
        1. both points -> line lies completly inside the clipping region
        2. both points -> line lies complety on one side of the clipping region
        3. Otherwise
    """
    union = line[0].reCode | line[1].reCode
    sect = line[0].reCode & line[1].reCode
    # 2. case
    if sect != 0:
        # line is completely unvisible
        return -1
    # 1. and 3. case
    else:
        # if union == 0 line is completely visible
        # otherwise further tests are necessary
        return union


def calcNewLine(line, line_case, clip_region):
    """ Calculate clipped line """
    # TODO: calculate new line (clipped at clipRegion)

    p1 = Point([line[0].coords[0], line[0].coords[1]], clip_region)
    p2 = Point([line[1].coords[0], line[1].coords[1]], clip_region)

    line_clipping = False

    x1 = line[0].coords[0]
    y1 = line[0].coords[1]

    x2 = line[1].coords[0]
    y2 = line[1].coords[1]

    x_min = clip_region[0][0]
    y_min = clip_region[0][1]

    x_max = clip_region[1][0]
    y_max = clip_region[1][1]

    while True:
        # trivial cases
        if p1.reCode | p2.reCode == 0:
            line_clipping = True
            break
        if (p1.reCode & p2.reCode) != 0:
            break

        # cases, that need further checks
        else:
            if p1.reCode != 0:
                p_out = p1
            else:
                p_out = p2

            if p_out.reCode & 1:
                y = y1 + (y2 - y1) * (x_min - x1) / (x2 - x1)
                x = x_min

            elif p_out.reCode >> 1 & 1:
                y = y1 + (y2 - y1) * (x_max - x1) / (x2 - x1)
                x = x_max

            elif p_out.reCode >> 2 & 1:
                x = x1 + (x2 - x1) * (y_min - y1) / (y2 - y1)
                y = y_min

            elif p_out.reCode >> 3 & 1:
                x = x1 + (x2 - x1) * (y_max - y1) / (y2 - y1)
                y = y_max

            new_code = 8 * (y < y_max) + 4 * (y > y_min) + 2 * (x > x_max) + (x < x_min)
            if p_out.reCode == p1.reCode:
                p1.coords = [x, y]
                p1.reCode = new_code
            else:
                p2.coords = [x, y]
                p2.reCode = new_code

    if line_clipping:
        return [p1.coords, p2.coords]
    return []


def quit(root=None):
    """ quit programm """
    if root == None:
        sys.exit(0)
    root._root().quit()
    root._root().destroy()


def draw():
    """ draw elements """
    can.delete(*elementList)
    drawPoints()
    drawBox()
    drawLines()


def clearAll():
    """ clear all (point list and canvas) """
    can.delete(*elementList)
    del pointList[:]


def mouseEvent(event):
    """ process mouse events """
    # print "left mouse button clicked at ", event.x, event.y
    global clipRegion
    p = [event.x, event.y]
    if len(pointList) < 2:
        point = Point(p, [[0, 0], [WIDTH, HEIGHT]])
    elif len(pointList) == 2:
        clipRegion = normalizeClipRegion([pointList[0].coords, pointList[1].coords])
        point = Point(p, clipRegion)
    else:
        point = Point(p, clipRegion)

    pointList.append(point)
    draw()


if __name__ == "__main__":
    # check parameters
    if len(sys.argv) != 1:
        print("LineClipping")
        sys.exit(-1)

    # create main window
    mw = Tk()
    mw._root().wm_title("Line clipping (Cohen-Sutherland Algorithm)")

    # create and position canvas and buttons
    cFr = Frame(mw, width=WIDTH, height=HEIGHT, relief="sunken", bd=1)
    cFr.pack(side="top")
    can = Canvas(cFr, width=WIDTH, height=HEIGHT)
    can.bind("<Button-1>", mouseEvent)
    can.pack()
    cFr = Frame(mw)
    cFr.pack(side="left")
    bClear = Button(cFr, text="Clear", command=clearAll)
    bClear.pack(side="left")
    eFr = Frame(mw)
    eFr.pack(side="right")
    bExit = Button(eFr, text="Quit", command=(lambda root=mw: quit(root)))
    bExit.pack()

    # start
    mw.mainloop()
