#! /usr/bin/env python3

# this module is under licence MIT  @ Tiemen DUVILLARD 2020
# for all questions, comments, bugs: duvillard.tiemen@gmail.com

from random import choice, randrange

# Representation of maze :
# A labyrinth is a set of 2 door panels.
# For a maze 5*5 :
# Theory :                                   ## Example :
# L = [[[a, b, c, d],  # vertical doors      ## L = [[[1, 1, 1, 1],  # vertical doors
#       [e, f, g, h],                        ##       [1, 0, 1, 0],
#       [i, j, k, l],                        ##       [0, 1, 0, 1],
#       [m, n, o, p],                        ##       [0, 0, 0, 0],
#       [q, r, s, t]],                       ##       [0, 1, 0, 0]],
#      [[A, B, C, D, E], # horizontal doors  ##      [[0, 0, 0, 0, 0], # horizontal doors
#       [F, G, H, I, J],                     ##       [0, 0, 0, 0, 1],
#       [K, L, M, N, O],                     ##       [0, 1, 1, 1, 0],
#       [P, Q, R, S, T]]]                    ##       [0, 1, 0, 1, 1]]]
#                                            ##
# ==>>                                       ## ==>>
#   X 0   1   2   3   4                      ##   X 0   1   2   3   4
# Y ┌───┬───┬───┬───┬───┐                    ## Y ┌───┬───┬───┬───┬───┐
# 0 │ ∙ a ∙ b ∙ c ∙ d ∙ │                    ## 0 │ ∙ │ ∙ │ ∙ │ ∙ │ ∙ │
#   ├─A─┼─B─┼─C─┼─D─┼─E─┤                    ##   │   │   │   │   │   │
# 1 │ ∙ e ∙ f ∙ g ∙ h ∙ │                    ## 1 │ ∙ │ ∙   ∙ │ ∙   ∙ │
#   ├─F─┼─G─┼─H─┼─I─┼─J─┤                    ##   │   │   │   │   ┌───┤
# 2 │ ∙ i ∙ j ∙ k ∙ l ∙ │                    ## 2 │ ∙   ∙ │ ∙   ∙ │ ∙ │
#   ├─K─┼─L─┼─M─┼─N─┼─O─┤                    ##   │   ╶───┴───────┘   │
# 3 │ ∙ m ∙ n ∙ o ∙ p ∙ │                    ## 3 │ ∙   ∙   ∙   ∙   ∙ │
#   ├─P─┼─Q─┼─R─┼─S─┼─T─┤                    ##   │   ╶───┐   ╶───────│
# 4 │ ∙ q ∙ r ∙ s ∙ t ∙ │                    ## 4 │ ∙   ∙ │ ∙   ∙   ∙ │
#   └───┴───┴───┴───┴───┘                    ##   └───────┴───────────┘

def kruskal(x, y):
    global ID
    ID = 0

    class case:
        """Little class for union-find"""
        def __init__(self,x,y):
            self.x = x
            self.y = y
            self.is_repr = True
            self.repr = None
            global ID
            self.ID = ID
            ID += 1

        def represent(self):
            if self.is_repr:
                return self
            else:
                L = [self.repr]
                while not L[0].is_repr:
                    L[0] = L[0].repr
                return L[0]

        def __eq__(self,other):
            return self.represent().ID == other.represent().ID

        def union(self,other):
            a = self.represent()
            b = other.represent()
            if not (a == b):
                b.is_repr = False
                b.repr = a

    # set of doors
    doors = []
    # verticals doors result
    verti = []
    # horizontals doors result
    horiz = []
    # set of cases
    cases = []
    ## initialize vertical doors
    for j in range(y):
        l = []
        for i in range(x-1):
            l.append(1)
            doors.append([i,j,'v'])
        verti.append(l)
    ## initialize horizontal doors
    for j in range(y-1):
        l = []
        for i in range(x):
            l.append(1)
            doors.append([i,j,'h'])
        horiz.append(l)

    ## initialize cases
    for i in range(y):
        l = []
        for j in range(x):
            l.append(case(x,y))
        cases.append(l)

    cpt = x*y -1 # nb of openings in perfect maze
    while cpt > 0:
        # I choose a door
        idoor = randrange(len(doors))
        dx, dy, dd = doors[idoor]
        cx1, cy1 = dx, dy
        if dd == 'h' : cx2, cy2 = cx1, cy1+1
        else :         cx2, cy2 = cx1+1, cy1

        C1 = cases[cy1][cx1]
        C2 = cases[cy2][cx2]
        # if the 2 cases separate by my door are not in same set
        if not C1 == C2:
            C1.union(C2)
            cpt -= 1
            # i modify my result
            if dd == "v": verti[dy][dx] = 0
            else:         horiz[dy][dx] = 0
        # i delete the door
        del doors[idoor]

    return verti,horiz

def recursive_backtrack(x, y):
    # Initialisation of my variables
    labyrinthe = []
    for i in range(y): labyrinthe.append([0] * x)
    horiz = []
    for i in range(y-1): horiz.append([1] * x)
    verti = []
    for i in range(y): verti.append([1] * (x-1))

    # I choose a random start
    X_pos = randrange(x)
    Y_pos = randrange(y)
    labyrinthe[Y_pos][X_pos] = 1
    historique = [[X_pos,Y_pos]]

    # I explore a tree with deep parcours
    while len(historique) != 0:
        X = historique[-1][0]
        Y = historique[-1][1]

        possibilite = []
        if (Y-1 >= 0) and (labyrinthe[Y-1][X] == 0): possibilite.append(0)
        if (X+1 < x)  and (labyrinthe[Y][X+1] == 0): possibilite.append(1)
        if (Y+1 < y)  and (labyrinthe[Y+1][X] == 0): possibilite.append(2)
        if (X-1 >= 0) and (labyrinthe[Y][X-1] == 0): possibilite.append(3)

        if len(possibilite) == 0:
            del historique[-1]
        else:
            d = choice(possibilite)
            if d == 0:
                X1,Y1 = X, Y-1
                horiz[Y-1][X] = 0
            if d == 1:
                X1,Y1 = X+1, Y
                verti[Y][X] = 0
            if d == 2:
                X1,Y1 = X, Y+1
                horiz[Y][X] = 0
            if d == 3:
                X1,Y1 = X-1, Y
                verti[Y][X-1] = 0
            labyrinthe[Y1][X1] = 1
            historique.append([X1,Y1])

    return verti, horiz


def recursive_chamber(x, y):
    # Initialisation of my variables
    def recursive_chamber_recu(VERTI,HORIZ,xA,yA,xB,yB):
        if (xB - xA <= 1):
            return
        elif (yB - yA <= 1):
            return
        else :
            dx = xB-xA
            dy = yB-yA
            v = randrange(0,dx+dy)
            if v < dx :
                x = randrange(xA,xB-1)
                y = randrange(yA,yB)
                for i in range(yA,yB):
                    if i != y:
                        VERTI[i][x] = 1
                recursive_chamber_recu(VERTI,HORIZ,xA,yA,x+1,yB)
                recursive_chamber_recu(VERTI,HORIZ,x+1,yA,xB,yB)
            else:
                x = randrange(xA,xB)
                y = randrange(yA,yB-1)
                for i in range(xA,xB):
                    if i != x:
                        HORIZ[y][i] = 1
                recursive_chamber_recu(VERTI,HORIZ,xA,yA,xB,y+1)
                recursive_chamber_recu(VERTI,HORIZ,xA,y+1,xB,yB)


    horiz = []
    for i in range(y-1): horiz.append([0] * x)
    verti = []
    for i in range(y): verti.append([0] * (x-1))

    # appel recursif
    recursive_chamber_recu(verti,horiz,0,0,x,y)

    return verti, horiz

# a empty maze
def empty(x, y):
    verti = []
    for i in range(y):
        verti.append([0] * (x-1))

    horiz = []
    for i in range(y-1):
        horiz.append([0] * x)
    return verti, horiz

# a full maze
def full(x, y):
    verti = []
    for i in range(y):
        verti.append([1] * (x-1))

    horiz = []
    for i in range(y-1):
        horiz.append([1] * x)
    return verti, horiz



class MazeLib:
    """This Class define a Maze object"""
    def __init__(self, X=5, Y=5, algorithm="empty"):
        """Use : m = Maze(X:int,Y:int, algorithm:string)"""
        self.X      = X # width
        self.Y      = Y # height
        self.verti = [] # table of vertical doors
        self.horiz = [] # table of horizontal doors
        algorithm = algorithm.lower()
        
        if algorithm in ("kruskal","k") :
            self.verti, self.horiz = kruskal(self.X,self.Y)
            self.doors     = self.nbDoors()
            self.algorithm = "kruskal"
            self.perfect   = True
        
        elif algorithm in ("recursive_backtrack","rb") :
            self.verti, self.horiz = recursive_backtrack(self.X,self.Y)
            self.doors     = self.nbDoors()
            self.algorithm = "recursive_backtrack"
            self.perfect   = True

        elif algorithm in ("empty","e") :
            self.verti, self.horiz = empty(self.X,self.Y)
            self.doors      = self.nbDoors() 
            self.algorithm  = "empty"
            self.perfect    = False

        elif algorithm in ("full","f") :
            self.verti, self.horiz = full(self.X,self.Y)
            self.doors      = self.nbDoors() 
            self.algorithm  = "full"
            self.perfect    = False

        elif algorithm in ("recursive_chamber","rc") :
            self.verti, self.horiz = recursive_chamber(self.X,self.Y)
            self.doors      = self.nbDoors() 
            self.algorithm  = "recursive_chamber"
            self.perfect    = False

        else :
            raise("Algorithm not recognized. Algorithm must be in ['kruskal','recursive_backtrack','empty','full']")

    def __str__(self):
        """Return information about maze"""
        s = "Size of maze : {}*{}\nGenerate by  : {}\nNb of doors  : {}\nPerfect      : {}"
        s = s.format(self.X,self.Y,self.algorithm,self.doors,self.perfect)
        return s

    def nbDoors(self):
        """Return number of doors in my maze. If maze is perfect, it equals to (self.X-1)*(self.Y-1)"""
        S = 0
        for k in self.verti: S += sum(k)
        for k in self.horiz: S += sum(k)
        return S

    def verticalDoors(self):
        """Iterate on vertical doors"""
        for i in range(len(self.verti)):
            for j in range(len(self.verti[i])):
                yield i,j, bool(self.verti[i][j])

    def horizontalDoors(self):
        """Iterate on horizontal doors"""
        for i in range(len(self.horiz)):
            for j in range(len(self.horiz[i])):
                yield i,j, bool(self.horiz[i][j])

    def canMove(self, x, y, direction) :
        """return if i can move in a direction since (x,y) """
        if direction in ["down","d",0] : # down
            if y == self.Y-1 :return False
            return not self.horiz[y][x]
        if direction in ["up","u",2] : # up
            if y == 0 : return False
            return not self.horiz[y-1][x]
        if direction in ["left","l",3] : # left
            if x == 0 : return False
            return not self.verti[y][x-1]
        if direction in ["right","r",1] : # right
            if x == self.X-1 : return False
            return not self.verti[y][x]
        return False

    def move(self, x, y, direction) :
        """return new cord after one move in direction"""
        if direction in ["down","d",0] : # down
            return x,y+1
        if direction in ["up","u",2] : # up
            return x,y-1
        if direction in ["left","l",3] : # left
            return x-1,y
        if direction in ["right","r",1] : # right
            return x+1,y
        return x,y

    def liberty(self, x, y):
        """return all cases accessible from (x,y)"""
        r = []
        for d in ["down","up","left","right"]:
            if self.canMove(x,y,d):
                r.append(d)
        return d

    def toSquare(self):
        """return another representation of maze, a List of List of case in {0,1} """
        RET = []
        for i in range(self.Y*2+1):
            l = []
            for j in range(self.X*2+1):
                if i == 0 or i == self.Y*2 or j == 0 or j == self.X*2 :
                    l.append(1)
                else :
                    if (i%2==0 and j%2==0) :
                        l.append(1)
                    elif (i%2==1 and j%2==1):
                        l.append(0)
                    elif (i%2==0 and j%2==1):
                        l.append(self.horiz[(i-1)//2][(j-1)//2])
                    elif (i%2==1 and j%2==0):
                        l.append(self.verti[(i-1)//2][(j-1)//2])
            RET.append(l)
        return RET

    def solve(self, xa, ya, xb, yb):
        """return a list of direction for link (xa,ya) -> (xb,yb). Null"""
        Sol = []
        Pile = [(xa,ya)]
        laby = []
        for i in range(self.Y):
            laby.append(['new'] * self.X)

        while len(Pile) != 0  and Pile[-1] != (xb,yb):
            pos = Pile[-1]
            x,y = pos[0],pos[1]
            if laby[y][x] == 'new':
                possibilite = []
                for d in ['down',"left","up","right"]:
                    if self.canMove(pos[0],pos[1],d) :
                        nx,ny = self.move(pos[0],pos[1],d)
                        if laby[ny][nx] == 'new' :
                            possibilite.append(d)
            
                laby[y][x] = possibilite
            elif laby[y][x] == "old":
                del Pile[-1]
                if len(Sol) != 0:
                    del Sol[-1]
            elif type(laby[y][x]) == list:
                if len(laby[y][x]) == 0:
                    laby[y][x] = "old"
                else:
                    ichoix = -1#randrange(len(laby[y][x]))
                    choix = laby[y][x][ichoix]
                    Pile.append(self.move(x,y,choix))
                    Sol.append(choix)
                    del laby[y][x][ichoix]

        return Sol

    def furthestBox(self, xa, ya):
        """return the case furtest of the case (xa,ya)"""
        Sol = []
        dmax = len(Sol)
        pmax = Sol.copy()
        cmax = (xa,ya)

        Pile = [(xa,ya)]
        laby = []
        for i in range(self.Y):
            laby.append(['new'] * self.X)

        while len(Pile) != 0:
            pos = Pile[-1]
            x,y = pos[0],pos[1]
            if laby[y][x] == 'new':
                possibilite = []
                for d in ['down',"left","up","right"]:
                    if self.canMove(pos[0],pos[1],d) :
                        nx,ny = self.move(pos[0],pos[1],d)
                        if laby[ny][nx] == 'new' :
                            possibilite.append(d)
            
                laby[y][x] = possibilite
            elif laby[y][x] == "old":
                if len(Sol) > dmax:
                    dmax = len(Sol)
                    pmax = Sol.copy()
                    cmax = (x,y)
                del Pile[-1]
                if len(Sol) != 0:
                    del Sol[-1]
            elif type(laby[y][x]) == list:
                if len(laby[y][x]) == 0:
                    laby[y][x] = "old"
                else:
                    ichoix = -1#randrange(len(laby[y][x]))
                    choix = laby[y][x][ichoix]
                    Pile.append(self.move(x,y,choix))
                    Sol.append(choix)
                    del laby[y][x][ichoix]

        return pmax, cmax

    def longestWay(self):
        Xa = randrange(self.X)
        Ya = randrange(self.Y)
        p,B = self.furthestBox(Xa,Ya)
        path,C = self.furthestBox(B[0],B[1])
        return B,path,C




    def save(self):
        """Return a string contain's all information. it can be save in file, print, etc.."""
        s = "{};{};{};{};{};{};{}".format(self.X, self.Y, self.doors, self.algorithm, self.perfect, self.verti, self.horiz)
        return s

    def load(self, st):
        """Load a Maze since a string of format save"""
        cont = st.split(";")
        self.X         = int(cont[0])
        self.Y         = int(cont[1])
        self.doors     = int(cont[2])
        self.algorithm = cont[3]
        self.perfect   = bool(cont[4])
        self.verti     = cont[5].split("], [")
        for i in range(len(self.verti)):
            self.verti[i] = self.verti[i].split(',')
            for j in range(len(self.verti[i])):
                self.verti[i][j] = self.verti[i][j].replace("[","")
                self.verti[i][j] = self.verti[i][j].replace("]","")
                self.verti[i][j] = self.verti[i][j].replace(" ","")
                self.verti[i][j] = int(self.verti[i][j])

        self.horiz     = cont[6].split("], [")
        for i in range(len(self.horiz)):
            self.horiz[i] = self.horiz[i].split(',')
            for j in range(len(self.horiz[i])):
                self.horiz[i][j] = self.horiz[i][j].replace("[","")
                self.horiz[i][j] = self.horiz[i][j].replace("]","")
                self.horiz[i][j] = self.horiz[i][j].replace(" ","")
                self.horiz[i][j] = int(self.horiz[i][j])

    def toTxt(self, centre=False, coord=False, basic= False):
        """return a txt representation of maze in ASCII art"""
        if type(centre) == bool:
            if centre : centre = "*"
            else :      centre = " "
        else:
            centre = centre[0]

        if basic :
            if coord:
                R = "  X"
                for i in range(self.X):
                    R += " {}  ".format(i%10)
                R += "\n"
                R += "Y +"
                r = "0 |"
            else:
                R = "+"
                r = "|"
            for j in range(self.X-1):
                if self.verti[0][j]:
                    R += "---+"
                    r += " {} |".format(centre)
                else:
                    R += "----"
                    r += " {}  ".format(centre)
            R += "---+\n"
            r += " {} |\n".format(centre)
            R += r
            for i in range(self.Y-1):
                if coord:
                    if self.horiz[i][0]:
                        l1 = "  +"
                    else:
                        l1 = "  |"
                    l2 = "{} |".format((i+1)%10)
                else:
                    if self.horiz[i][0]:
                        l1 = "+"
                    else:
                        l1 = "|"
                    l2 = "|"
                for j in range(self.X-1):
                    inter = "+"
                    if     self.horiz[i][j] and     self.horiz[i][j+1] and not self.verti[i][j] and not self.verti[i+1][j] : inter = "-"
                    if not self.horiz[i][j] and not self.horiz[i][j+1] and     self.verti[i][j] and     self.verti[i+1][j] : inter = "|"
                    if not self.horiz[i][j] and not self.horiz[i][j+1] and not self.verti[i][j] and not self.verti[i+1][j] : inter = " "
                    
                    if self.horiz[i][j]:
                        l1 += "---"+inter
                    else:
                        l1 += "   "+inter
    
                    if self.verti[i+1][j]:
                        l2 += " {} |".format(centre)
                    else:
                        l2 += " {}  ".format(centre)
                if self.horiz[i][-1]:
                    l1 += "---+"
                else:
                    l1 += "   |"
                l2 += " {} |".format(centre)
    
                R += l1 + "\n"
                R += l2 + "\n"
            if coord:
                r = "  +"
            else:
                r = "+"
            for j in range(self.X-1):
                if self.verti[-1][j]:
                    r += "---+"
                else:
                    r += "----"
            r += "---+"
            R += r
            return R

        else :
            if coord:
                R = "  X"
                for i in range(self.X):
                    R += " {}  ".format(i%10)
                R += "\n"
                R += "Y ┌"
                r = "0 │"
            else:
                R = "┌"
                r = "│"
            for j in range(self.X-1):
                if self.verti[0][j]:
                    R += "───┬"
                    r += " {} │".format(centre)
                else:
                    R += "────"
                    r += " {}  ".format(centre)
            R += "───┐\n"
            r += " {} │\n".format(centre)
            R += r
            for i in range(self.Y-1):
                if coord:
                    if self.horiz[i][0]:
                        l1 = "  ├"
                    else:
                        l1 = "  │"
                    l2 = "{} │".format((i+1)%10)
                else:
                    if self.horiz[i][0]:
                        l1 = "├"
                    else:
                        l1 = "│"
                    l2 = "│"
                for j in range(self.X-1):
                    # 4 door
                    if     self.horiz[i][j] and     self.horiz[i][j+1] and     self.verti[i][j] and     self.verti[i+1][j] : inter = "┼"
                    # 3 door
                    if     self.horiz[i][j] and     self.horiz[i][j+1] and     self.verti[i][j] and not self.verti[i+1][j] : inter = "┴"
                    if     self.horiz[i][j] and     self.horiz[i][j+1] and not self.verti[i][j] and     self.verti[i+1][j] : inter = "┬"
                    if     self.horiz[i][j] and not self.horiz[i][j+1] and     self.verti[i][j] and     self.verti[i+1][j] : inter = "┤"
                    if not self.horiz[i][j] and     self.horiz[i][j+1] and     self.verti[i][j] and     self.verti[i+1][j] : inter = "├"
                    # 2 door
                    if     self.horiz[i][j] and     self.horiz[i][j+1] and not self.verti[i][j] and not self.verti[i+1][j] : inter = "─"
                    if     self.horiz[i][j] and not self.horiz[i][j+1] and     self.verti[i][j] and not self.verti[i+1][j] : inter = "┘"
                    if not self.horiz[i][j] and     self.horiz[i][j+1] and     self.verti[i][j] and not self.verti[i+1][j] : inter = "└"
                    if     self.horiz[i][j] and not self.horiz[i][j+1] and not self.verti[i][j] and     self.verti[i+1][j] : inter = "┐"
                    if not self.horiz[i][j] and     self.horiz[i][j+1] and not self.verti[i][j] and     self.verti[i+1][j] : inter = "┌"
                    if not self.horiz[i][j] and not self.horiz[i][j+1] and     self.verti[i][j] and     self.verti[i+1][j] : inter = "│"
                    # 1 door
                    if not self.horiz[i][j] and not self.horiz[i][j+1] and not self.verti[i][j] and     self.verti[i+1][j] : inter = "╷"
                    if not self.horiz[i][j] and not self.horiz[i][j+1] and     self.verti[i][j] and not self.verti[i+1][j] : inter = "╵"
                    if not self.horiz[i][j] and     self.horiz[i][j+1] and not self.verti[i][j] and not self.verti[i+1][j] : inter = "╶"
                    if     self.horiz[i][j] and not self.horiz[i][j+1] and not self.verti[i][j] and not self.verti[i+1][j] : inter = "╴"
                    # 0 door
                    if not self.horiz[i][j] and not self.horiz[i][j+1] and not self.verti[i][j] and not self.verti[i+1][j] : inter = " "
                    if self.horiz[i][j]:
                        l1 += "───"+inter
                    else:
                        l1 += "   "+inter
    
                    if self.verti[i+1][j]:
                        l2 += " {} │".format(centre)
                    else:
                        l2 += " {}  ".format(centre)
                if self.horiz[i][-1]:
                    l1 += "───┤"
                else:
                    l1 += "   │"
                l2 += " {} │".format(centre)
    
                R += l1 + "\n"
                R += l2 + "\n"
            if coord:
                r = "  └"
            else:
                r = "└"
            for j in range(self.X-1):
                if self.verti[-1][j]:
                    r += "───┴"
                else:
                    r += "────"
            r += "───┘"
            R += r
            return R