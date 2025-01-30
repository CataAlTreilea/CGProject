def earcut(data, holeIndices=None, dim=2):
    hasHoles = holeIndices and len(holeIndices)
    outerLen = holeIndices[0] * dim if hasHoles else len(data)
    outerNode = linkedList(data, 0, outerLen, dim, True)
    triangles = []

    if (not outerNode or outerNode.next == outerNode.prev):
        return triangles

    minX = None
    minY = None
    invSize = None

    if (hasHoles):
        outerNode = eliminateHoles(data, holeIndices, outerNode, dim)

    if (len(data) > 80 * dim):
        minX = maxX = data[0]
        minY = maxY = data[1]

        for i in range(dim, outerLen, dim):
            x = data[i]
            y = data[i + 1]
            if (x < minX): 
                minX = x
            if (y < minY): 
                minY = y
            if (x > maxX): 
                maxX = x
            if (y > maxY): 
                maxY = y

        invSize = max(maxX - minX, maxY - minY)
        invSize = 1 / invSize if invSize != 0 else 0

    earcutLinked(outerNode, triangles, dim, minX, minY, invSize)

    return triangles

def linkedList(data, start, end, dim, clockwise):

    last = None

    if (clockwise == (signedArea(data, start, end, dim) > 0)):
        for i in range(start, end, dim):
            last = insertNode(i, data[i], data[i + 1], last)
    else:
        for i in range(end - dim, start - 1, -dim):
            last = insertNode(i, data[i], data[i + 1], last)

    if (last and equals(last, last.next)):
        removeNode(last)
        last = last.next

    return last

def filterPoints(start, end=None):
    if (not start):
        return start
    if (not end):
        end = start

    p = start

    while True:
        again = False

        if (not p.steiner and (equals(p, p.next) or area(p.prev, p, p.next) == 0)):
            removeNode(p)
            p = end = p.prev
            if (p == p.next):
                break
            again = True

        else:
            p = p.next

        if not (again or p != end):
            break

    return end

def earcutLinked(ear, triangles, dim, minX, minY, invSize, passs=None):
    if (not ear):
        return

    if (not passs and invSize):
        indexCurve(ear, minX, minY, invSize)

    stop = ear

    while (ear.prev != ear.next):
        prev = ear.prev
        next = ear.next

        if (isEarHashed(ear, minX, minY, invSize) if invSize else isEar(ear)):

            triangles.append(prev.i // dim)
            triangles.append(ear.i // dim)
            triangles.append(next.i // dim)

            removeNode(ear)

            ear = next.next
            stop = next.next

            continue

        ear = next

        if (ear == stop):

            if (not passs):
                earcutLinked(filterPoints(ear), triangles, dim, minX, minY, invSize, 1)

            elif (passs == 1):
                ear = cureLocalIntersections(filterPoints(ear), triangles, dim)
                earcutLinked(ear, triangles, dim, minX, minY, invSize, 2)

            elif (passs == 2):
                splitEarcut(ear, triangles, dim, minX, minY, invSize)

            break

def isEar(ear):
    a = ear.prev
    b = ear
    c = ear.next

    if (area(a, b, c) >= 0):
        return False 

    p = ear.next.next

    while (p != ear.prev):
        if (pointInTriangle(a.x, a.y, b.x, b.y, c.x, c.y, p.x, p.y) and
                area(p.prev, p, p.next) >= 0):
            return False
        p = p.next

    return True

def isEarHashed(ear, minX, minY, invSize):
    a = ear.prev
    b = ear
    c = ear.next

    if (area(a, b, c) >= 0):
        return False 

    minTX = (a.x if a.x < c.x else c.x) if a.x < b.x else (b.x if b.x < c.x else c.x)
    minTY = (a.y if a.y < c.y else c.y) if a.y < b.y else (b.y if b.y < c.y else c.y)
    maxTX = (a.x if a.x > c.x else c.x) if a.x > b.x else (b.x if b.x > c.x else c.x)
    maxTY = (a.y if a.y > c.y else c.y) if a.y > b.y else (b.y if b.y > c.y else c.y)

    minZ = zOrder(minTX, minTY, minX, minY, invSize)
    maxZ = zOrder(maxTX, maxTY, minX, minY, invSize)

    p = ear.prevZ
    n = ear.nextZ

    while (p and p.z >= minZ and n and n.z <= maxZ):
        if (p != ear.prev and p != ear.next and
                pointInTriangle(a.x, a.y, b.x, b.y, c.x, c.y, p.x, p.y) and
                area(p.prev, p, p.next) >= 0):
            return False
        p = p.prevZ

        if (n != ear.prev and n != ear.next and
                pointInTriangle(a.x, a.y, b.x, b.y, c.x, c.y, n.x, n.y) and
                area(n.prev, n, n.next) >= 0):
            return False;
        n = n.nextZ

    while (p and p.z >= minZ):
        if (p != ear.prev and p != ear.next and
                pointInTriangle(a.x, a.y, b.x, b.y, c.x, c.y, p.x, p.y) and
                area(p.prev, p, p.next) >= 0):
            return False
        p = p.prevZ

    while (n and n.z <= maxZ):
        if (n != ear.prev and n != ear.next and
                pointInTriangle(a.x, a.y, b.x, b.y, c.x, c.y, n.x, n.y) and
                area(n.prev, n, n.next) >= 0):
            return False
        n = n.nextZ

    return True

def cureLocalIntersections(start, triangles, dim):
    p = start

    while True:
        a = p.prev
        b = p.next.next

        if (not equals(a, b) and intersects(a, p, p.next, b) and locallyInside(a, b) and locallyInside(b, a)):

            triangles.append(a.i // dim)
            triangles.append(p.i // dim)
            triangles.append(b.i // dim)

            removeNode(p)
            removeNode(p.next)

            p = start = b

        p = p.next

        if not (p != start):
            break

    return filterPoints(p)

def splitEarcut(start, triangles, dim, minX, minY, invSize):

    a = start

    while True:
        b = a.next.next

        while (b != a.prev):
            if (a.i != b.i and isValidDiagonal(a, b)):

                c = splitPolygon(a, b)

                a = filterPoints(a, a.next)
                c = filterPoints(c, c.next)

                earcutLinked(a, triangles, dim, minX, minY, invSize)
                earcutLinked(c, triangles, dim, minX, minY, invSize)
                return

            b = b.next

        a = a.next
        if not (a != start):
            break

def eliminateHoles(data, holeIndices, outerNode, dim):
    queue = []

    length = len(holeIndices)
    for i in range(length):
        start = holeIndices[i] * dim
        end = holeIndices[i + 1] * dim if i < length - 1 else len(data)
        list = linkedList(data, start, end, dim, False)
        if (list == list.next):
            list.steiner = True
        queue.append(getLeftmost(list))

    queue = sorted(queue, key=lambda k: k.x, reverse=True)

    for i in range(len(queue)):
        eliminateHole(queue[i], outerNode)
        outerNode = filterPoints(outerNode, outerNode.next)

    return outerNode

def eliminateHole(hole, outerNode):
    outerNode = findHoleBridge(hole, outerNode)
    if (outerNode):
        b = splitPolygon(outerNode, hole)

        filterPoints(outerNode, outerNode.next)
        filterPoints(b, b.next)

def findHoleBridge(hole, outerNode):
    p = outerNode
    hx = hole.x
    hy = hole.y
    qx = float("-inf")
    m = None

    while True:
        if (hy <= p.y and hy >= p.next.y and p.next.y != p.y):
            x = p.x + (hy - p.y) * (p.next.x - p.x) / (p.next.y - p.y)

            if (x <= hx and x > qx):
                qx = x
                if (x == hx):
                    if (hy == p.y):
                        return p
                    if (hy == p.next.y):
                        return p.next

                m = p if p.x < p.next.x else p.next

        p = p.next
        if not (p != outerNode):
            break

    if (not m):
        return None

    if (hx == qx):
        return m 

    stop = m
    mx = m.x
    my = m.y
    tanMin = float("inf")

    p = m

    while True:
        if (hx >= p.x and p.x >= mx and hx != p.x and
                pointInTriangle(hx if hy < my else qx, hy, mx, my, qx if hy < my else hx, hy, p.x, p.y)):

            tan = abs(hy - p.y) / (hx - p.x) 

            if (locallyInside(p, hole) and
                    (tan < tanMin or (tan == tanMin and (p.x > m.x or (p.x == m.x and sectorContainsSector(m, p)))))):
                m = p
                tanMin = tan

        p = p.next
        if not (p != stop):
            break

    return m

def sectorContainsSector(m, p):
    return area(m.prev, m, p.prev) < 0 and area(p.next, m, m.next) < 0

def indexCurve(start, minX, minY, invSize):
    p = start

    while True:
        if (p.z == None):
            p.z = zOrder(p.x, p.y, minX, minY, invSize)
        p.prevZ = p.prev
        p.nextZ = p.next
        p = p.next
        if not (p != start):
            break

    p.prevZ.nextZ = None
    p.prevZ = None

    sortLinked(p)

def sortLinked(list):
    inSize = 1
    e = None

    while True:
        p = list
        list = None
        tail = None
        numMerges = 0

        while (p):
            numMerges += 1
            q = p
            pSize = 0
            for i in range(inSize):
                pSize += 1
                q = q.nextZ
                if (not q):
                    break

            qSize = inSize

            while (pSize > 0 or (qSize > 0 and q)):

                if (pSize != 0 and (qSize == 0 or not q or p.z <= q.z)):
                    e = p
                    p = p.nextZ
                    pSize -= 1
                else:
                    e = q
                    q = q.nextZ
                    qSize -= 1

                if (tail):
                    tail.nextZ = e
                else:
                    list = e

                e.prevZ = tail
                tail = e

            p = q

        tail.nextZ = None
        inSize *= 2

        if not (numMerges > 1):
            break

    return list

def zOrder(x, y, minX, minY, invSize):

    x = int(32767 * (x - minX) * invSize)
    y = int(32767 * (y - minY) * invSize)

    x = (x | (x << 8)) & 0x00FF00FF
    x = (x | (x << 4)) & 0x0F0F0F0F
    x = (x | (x << 2)) & 0x33333333
    x = (x | (x << 1)) & 0x55555555

    y = (y | (y << 8)) & 0x00FF00FF
    y = (y | (y << 4)) & 0x0F0F0F0F
    y = (y | (y << 2)) & 0x33333333
    y = (y | (y << 1)) & 0x55555555

    return x | (y << 1)

def getLeftmost(start):
    p = start
    leftmost = start
    while True:
        if (p.x < leftmost.x or (p.x == leftmost.x and p.y < leftmost.y)):
            leftmost = p
        p = p.next
        if not (p != start):
            break

    return leftmost

def pointInTriangle(ax, ay, bx, by, cx, cy, px, py):
    return (cx - px) * (ay - py) - (ax - px) * (cy - py) >= 0 and \
           (ax - px) * (by - py) - (bx - px) * (ay - py) >= 0 and \
           (bx - px) * (cy - py) - (cx - px) * (by - py) >= 0

def isValidDiagonal(a, b):

    return a.next.i != b.i and a.prev.i != b.i and not intersectsPolygon(a, b) and \
           (locallyInside(a, b) and locallyInside(b, a) and middleInside(a, b) and
            (area(a.prev, a, b.prev) or area(a, b.prev, b)) or
            equals(a, b) and area(a.prev, a, a.next) > 0 and area(b.prev, b, b.next) > 0)

def area(p, q, r):
    return (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y);

def equals(p1, p2):
    return p1.x == p2.x and p1.y == p2.y;

def intersects(p1, q1, p2, q2):
    o1 = sign(area(p1, q1, p2))
    o2 = sign(area(p1, q1, q2))
    o3 = sign(area(p2, q2, p1))
    o4 = sign(area(p2, q2, q1))

    if (o1 != o2 and o3 != o4):
        return True 

    if (o1 == 0 and onSegment(p1, p2, q1)):
        return True 
    if (o2 == 0 and onSegment(p1, q2, q1)):
        return True 
    if (o3 == 0 and onSegment(p2, p1, q2)):
        return True 
    if (o4 == 0 and onSegment(p2, q1, q2)):
        return True 

    return False

def onSegment(p, q, r):
    return q.x <= max(p.x, r.x) and q.x >= min(p.x, r.x) and q.y <= max(p.y, r.y) and q.y >= min(p.y, r.y)

def sign(num):
    return 1 if num > 0 else -1 if num < 0 else 0

def intersectsPolygon(a, b):
    p = a

    while True:
        if (p.i != a.i and p.next.i != a.i and p.i != b.i and p.next.i != b.i and
                intersects(p, p.next, a, b)):
            return True
        p = p.next
        if not (p != a):
            break

    return False

def locallyInside(a, b):
    return area(a, b, a.next) >= 0 and area(a, a.prev, b) >= 0 if \
        area(a.prev, a, a.next) < 0 else \
        area(a, b, a.prev) < 0 or area(a, a.next, b) < 0

def middleInside(a, b):
    p = a
    inside = False
    px = (a.x + b.x) / 2
    py = (a.y + b.y) / 2

    while True:
        if (((p.y > py) != (p.next.y > py)) and p.next.y != p.y and
                (px < (p.next.x - p.x) * (py - p.y) / (p.next.y - p.y) + p.x)):
            inside = not inside
        p = p.next

        if not (p != a):
            break

    return inside

def splitPolygon(a, b):
    a2 = Node(a.i, a.x, a.y)
    b2 = Node(b.i, b.x, b.y)
    an = a.next
    bp = b.prev

    a.next = b
    b.prev = a

    a2.next = an
    an.prev = a2

    b2.next = a2
    a2.prev = b2

    bp.next = b2
    b2.prev = bp

    return b2

def insertNode(i, x, y, last):
    p = Node(i, x, y)

    if (not last):
        p.prev = p
        p.next = p

    else:
        p.next = last.next
        p.prev = last
        last.next.prev = p
        last.next = p

    return p

def removeNode(p):
    p.next.prev = p.prev
    p.prev.next = p.next

    if (p.prevZ):
        p.prevZ.nextZ = p.nextZ
    if (p.nextZ):
        p.nextZ.prevZ = p.prevZ

class Node:
    def __init__(self, i, x, y):

        self.i = i

        self.x = x
        self.y = y

        self.prev = None
        self.next = None

        self.z = None

        self.prevZ = None
        self.nextZ = None

        self.steiner = False

def deviation(data, holeIndices, dim, triangles):
    hasHoles = holeIndices and holeIndices.length
    outerLen = holeIndices[0] * dim if hasHoles else len(data)

    polygonArea = abs(signedArea(data, 0, outerLen, dim))

    if (hasHoles):
        length = len(holeIndices)
        for i in range(length):
            start = holeIndices[i] * dim
            end = holeIndices[i + 1] * dim if i < length - 1 else len(data)
            polygonArea -= abs(signedArea(data, start, end, dim))

    trianglesArea = 0

    for i in range(0, len(triangles), 3):
        a = triangles[i] * dim
        b = triangles[i + 1] * dim
        c = triangles[i + 2] * dim
        trianglesArea += abs((data[a] - data[c]) * (data[b + 1] - data[a + 1]) -
                             (data[a] - data[b]) * (data[c + 1] - data[a + 1]))

    return 0 if polygonArea == 0 and trianglesArea == 0 else \
        abs((trianglesArea - polygonArea) / polygonArea)

def signedArea(data, start, end, dim):
    sum = 0

    j = end - dim
    for i in range(start, end, dim):
        sum += (data[j] - data[i]) * (data[i + 1] + data[j + 1])
        j = i

    return sum

def flatten(data):
    dim = len(data[0][0])
    result = {"vertices": [], "holes": [], "dimensions": dim}
    holeIndex = 0

    for i in range(len(data)):
        for j in range(len(data[i])):
            for d in range(dim):
                result["vertices"].append(data[i][j][d])

        if (i > 0):
            holeIndex += len(data[i - 1])
            result["holes"].append(holeIndex)

    return result

if __name__ == '__main__':
    pass