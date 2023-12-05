#!/usr/bin/env python3

# We will use the inkex module with the predefined Effect base class.
import inkex
import math
from lxml import etree

objStyle = str(inkex.Style(
    {'stroke': '#000000',
    'stroke-width': 0.1,
    'fill': 'none'
    }))

class inkcape_polar:
    def __init__(self, Offset, group):
        self.offsetX = Offset[0]
        self.offsetY = Offset[1]
        self.Path = ''
        self.group = group
    
    def MoveTo(self, r, angle):
    #Retourne chaine de caractères donnant la position du point avec des coordonnées polaires
        self.Path += ' M ' + str(round(r*math.cos(angle)-self.offsetX, 3)) + ',' + str(round(r*math.sin(angle)-self.offsetY, 3))

    def LineTo(self, r, angle):
    #Retourne chaine de caractères donnant la position du point avec des coordonnées polaires
        self.Path += ' L ' + str(round(r*math.cos(angle)-self.offsetX, 3)) + ',' + str(round(r*math.sin(angle)-self.offsetY, 3))

    def Line(self, r1, angle1, r2, angle2):
    #Retourne chaine de caractères donnant la position du point avec des coordonnées polaires
        self.Path += ' M ' + str(round(r1*math.cos(angle1)-self.offsetX, 3)) + ',' + str(round(r1*math.sin(angle1)-self.offsetY, 3)) + ' L ' + str(round(r2*math.cos(angle2)-self.offsetX, 3)) + ',' + str(round(r2*math.sin(angle2)-self.offsetY, 3))
    
    def GenPath(self):
        line_attribs = {'style': objStyle, 'd': self.Path}
        etree.SubElement(self.group, inkex.addNS('path', 'svg'), line_attribs)

class CurvedSurface:
    def __init__(self, L1, L2, nombre_pas, angle_par_pas, taille_exacte_pas, nb_parts, epaisseur, parent, xOffset, yOffset):
        self.L1 = L1
        self.L2 = L2
        self.nombre_pas = nombre_pas
        self.angle_par_pas = angle_par_pas
        self.taille_exacte_pas = taille_exacte_pas
        self.epaisseur = epaisseur
        self.parent = parent
        self.OffsetX = xOffset
        self.OffsetY = yOffset
        self.nb_parts = nb_parts

    def genere_element_1(self, angle):
        path = inkcape_polar(self.Offset, self.group)
        # Commence par le pas de liaison avec le suivant. Va de (L1, angle+angle_par_pas) vers (L1, angle+angle_par_pas/2)
        path.Line(self.L1, angle+self.angle_par_pas, self.L1, angle+self.angle_par_pas/2)
        # Puis trait court de (L1+TraiteTraitCourt, angle+angle_par_pas/2) vers (L1-epaisseur, angle+angle_par_pas/2)
        path.Line(self.L1+self.TailleTraitCourt, angle+self.angle_par_pas/2, self.L1-self.epaisseur, angle+self.angle_par_pas/2)
        # Puis fait la dent inétrieur et va en (L1-epaisseur, angle)
        path.LineTo(self.L1-self.epaisseur, angle)
        # Puis trait court, va en (L1+TailleTraitCourt, angle) 
        path.LineTo(self.L1+self.TailleTraitCourt, angle)
        path.GenPath()

    def genere_element_1_debut(self, angle):
        path = inkcape_polar(self.Offset, self.group)
        # Commence par le pas de liaison avec le suivant
        # Commence en (L1,0) et finit en (L1, angle/2)
        path.Line(self.L1, 0, self.L1, angle/2)
        #Se déplace pour se positionner à (self.L1+TailleTraitCourt, angle/2)  et termine en (L1-epaisseur, angle /2)
        path.Line(self.L1+self.TailleTraitCourt, angle/2, self.L1-self.epaisseur, angle/2)
        #Puis trace la dent. Se déplace en (L1-epaisseur, angle*0.75)
        path.LineTo(self.L1-self.epaisseur, angle*0.75)
        # Puis bord complet : se déplace en (L2+epaisseur,angle*0.75)
        path.LineTo(self.L2+self.epaisseur, angle*0.75)
        # Puis dent externe, revient en (L2+epaisseur, angle/2)
        path.LineTo(self.L2+self.epaisseur, angle*0.5)
        # Puis trait de taille TailleTraitcourt --> va en (L2-TailleTraitCourt) avec angle/2
        path.LineTo(self.L2-self.TailleTraitCourt, angle*0.5)
        # Puis liaison vers suivant. Se déplace en (L2, taille_exacte_pas*0.5) avec angle/2 et va en (L2,0) avec angle 0 
        path.Line(self.L2, angle*0.5, self.L2, 0)
        path.GenPath()

    def genere_element_1_fin(self, angle):
        path = inkcape_polar(self.Offset, self.group)
        #   Génère le dernier path, pour le dernier pas. Proche du cas normal, mais path plus complet, prend en compte la découpe du bord
        #   Par rapport au premier, pas de liaison avec le suivant !
        # Commence par le trait court intérieur : Va de (L1+TailleTraitCourt, angle) vers (L1-epaisseur, angle)
        path.Line(self.L1+self.TailleTraitCourt, angle, self.L1-self.epaisseur, angle)
        # Puis la dent coté intérieur : Va en (L1-epaisseur, angle+angle_par_pas/4)
        path.LineTo(self.L1-self.epaisseur, angle+self.angle_par_pas/4)
        # Puis découpe complète du bord. Va en (L2+epaisseur, angle+angle_par_pas/4)
        path.LineTo(self.L2+self.epaisseur, angle+self.angle_par_pas/4)
        # Puis dent coté extérieur, va en (L2+epaisseur, angle)
        path.LineTo(self.L2+self.epaisseur, angle)
        # et enfin traitcourt, va en (L2-TailleTraitCOurt, angle)
        path.LineTo(self.L2-self.TailleTraitCourt, angle) 
        path.GenPath()

    def genere_element_2(self, angle):
        path = inkcape_polar(self.Offset, self.group)
        #   Génère 2nd path, 2 traits entre bords des dents de l'interieur vers l'exterieur
        # Se positionne en (L1 + TailleTraitCourt+2, angle) et va en ((L2+L1)/2-1, angle)
        path.Line(self.L1+self.TailleTraitCourt+2, angle, (self.L2+self.L1)/2-1, angle)
        # Se positionne en ((L2+L1)/2+1, angle) et va en (L2-TailleTraitCourt-2, angle)
        path.Line((self.L2+self.L1)/2+1, angle, self.L2-self.TailleTraitCourt-2, angle)
        path.GenPath()

    def genere_element_3(self, angle):
        path = inkcape_polar(self.Offset, self.group)
        #   Génère la dent, la liaison avec le suivant coté extérieur
        # Commence en (L2-TailleTraitCourt, angle) et va en (L2+epaisseur, angle)
        path.Line(self.L2-self.TailleTraitCourt, angle, self.L2+self.epaisseur, angle)
        # Trace la dent, va en (L2+epaisseur, angle+angle_par_pas/2)
        # Ajoute angle_par_pas / 2 à l'angle car ce sera la nouvelle origine
        angle += self.angle_par_pas/2
        path.LineTo(self.L2+self.epaisseur, angle)
        # Revient vers l'intérieur en (L2-TailleTraitCourt, angle+angle_par_pas/2) mais c'est le nouvel angle
        path.LineTo(self.L2-self.TailleTraitCourt, angle)
        # Trace liaison avec le suivant. Début en (L2, nouvel_angle) fin en (L2, nouvel_angle+angle_par_pas/2)
        path.Line(self.L2, angle, self.L2, angle+self.angle_par_pas/2) 
        path.GenPath()

    def genere_element_4(self, angle):
        path = inkcape_polar(self.Offset, self.group)
        #   Génère 2nd path, 2 traits entre bords des dents de l'extérieur vers l'intérieur
        # Se positionne en (L2-TailleTraitCourt-2, angle+angle_par_pas/2) et va en ((L2+L1)/2+1, angle+angle_par_pas/2) 
        path.Line(self.L2-self.TailleTraitCourt-2, angle+self.angle_par_pas/2, (self.L2+self.L1)/2+1, angle+self.angle_par_pas/2)
        # Se positionne en ((L2+L1)/2-1, angle+angle_par_pas/2) et va en (L1 + TailleTraitCourt+2, angle+angle_par_pas/2) 
        path.Line((self.L2+self.L1)/2-1, angle+self.angle_par_pas/2, self.L1+self.TailleTraitCourt+2, angle+self.angle_par_pas/2)
        path.GenPath()

    def genere_element_5(self, angle):
        path = inkcape_polar(self.Offset, self.group)
        #   Génère path avec 3 traits longueur TailleTraitLong entre les dents externes
        #Tous les angles de ce motifs sont incrénetés de angle_par_pas/4
        angle += self.angle_par_pas/4
        # Se positionne en (L1-epaisseur+1, angle) et va en (L1+TailleTraitLong-1)
        path.Line(self.L1-self.epaisseur+1, angle, self.L1+self.TailleTraitLong-1, angle)
        # Se positionne en (L1+TailleTraitLong+1, angle) et va en (L1+2*TailleTraitLong+1)
        path.Line(self.L1+self.TailleTraitLong+1, angle, self.L1+2*self.TailleTraitLong+1, angle)
        # Se positionne en (L2 - TailleTraitLong + 1 et va en L2+epaisseur-1)
        path.Line(self.L2-self.TailleTraitLong+1, angle, self.L2+self.epaisseur-1, angle)
        path.GenPath()

    def genere_element_6(self, angle):
        path = inkcape_polar(self.Offset, self.group)
        #Tous les angles de ce motifs sont incrénetés de angle_par_pas*0.75
        angle += self.angle_par_pas*0.75
        # Se positionne en (L2-1, angle) et va en (L2-TailleTraitLong+1)
        path.Line(self.L2-1, angle, self.L2-self.TailleTraitLong+1, angle)
        # Se positionne en (L2 - TailleTraitLong-1, angle) et va en (L1+TailleTraitLong+1)
        path.Line(self.L2-self.TailleTraitLong - 1, angle, self.L1+self.TailleTraitLong+1, angle)
        # Se positionne en (L1+TailleTraitLong-1) et va en (L1+1,angle)
        path.Line(self.L1+self.TailleTraitLong - 1, angle, self.L1+1, angle)
        path.GenPath()

    def genere_pas_debut(self):
        # Génère les paths du premier pas, le bord est complètement coupé et son épaisseur est divisée par 2 (élement_1 début)
        angle = -1*self.angle_par_pas
        #Taille traits court et long premiere partie
        self.genere_element_1_debut(angle)
        self.genere_element_4(angle)
        self.genere_element_6(angle)

    def genere_pas_fin(self, index_pas_fin):
        # Génère les paths du dernier pas, le bord est complètement coupé et son épaisseur est divisée par 2 (élement_1 fin)
        angle = index_pas_fin*self.angle_par_pas
        # Génère les deux traits courts entre les dents
        self.genere_element_2(angle)
        # Génère la dent et ferme le contour
        self.genere_element_1_fin(angle)


    def genere_pas(self, index_pas):
        # Génère les paths d'un des pas du milieu. 6 paths sont créés
        angle = self.angle_par_pas * index_pas
        # Premier élément : dent intérieure
        self.genere_element_1(angle)
        # Second élément : 2 trait courts entre dents proche précédent
        self.genere_element_2(angle)
        # 3ème élément : dent extérieure
        self.genere_element_3(angle)
        # 4ème élément : 2 traits courts entre dents vers milieu
        self.genere_element_4(angle)
        # 5ème élément : 3 traits longs proche du précédent
        self.genere_element_5(angle)
        # 6ème élément : 3 traits longs vers suivant
        self.genere_element_6(angle)


    def GeneratePaths(self):
        #Taille traits courts et longs entre les dents
        self.TailleTraitCourt = (self.L2 - self.L1) / 6 - 1
        self.TailleTraitLong = (self.L2 - self.L1- 2) / 3
        pas_par_bloc = int(self.nombre_pas/self.nb_parts)
        #genere les pas du "flex"
        for i in range(self.nb_parts):
            group = etree.SubElement(self.parent, 'g')
            self.group = group
            current_pas = 0
            pas_pour_ce_bloc = pas_par_bloc
            self.Offset = (self.OffsetX, self.OffsetY)
            self.OffsetX += self.L2*2+ 5
            if i == self.nb_parts - 1:
                pas_pour_ce_bloc = self.nombre_pas - i * pas_par_bloc
            self.genere_pas_debut()
            while current_pas < pas_pour_ce_bloc:
                self.genere_pas(current_pas)
                current_pas += 1
            self.genere_pas_fin(pas_pour_ce_bloc)

def gen_cercle(diametre, nombre_pas, epaisseur, xOffset, yOffset, parent):
    group = etree.SubElement(parent, 'g')
    angle_par_pas = 2 * math.pi / nombre_pas
    #Rayons des cercle, avec et sans picots
    r1 = diametre / 2
    r2 = r1 + epaisseur
    path = inkcape_polar((xOffset, yOffset), group)
    path.MoveTo(r1, 0)
    index_pas = 0
    while index_pas < nombre_pas:
        angle = index_pas * angle_par_pas
        path.LineTo(r2, angle)
        path.LineTo(r2, angle+angle_par_pas/2)
        path.LineTo(r1, angle+angle_par_pas/2)
        path.LineTo(r1, angle+angle_par_pas)
        index_pas += 1
    path.GenPath()

class BoxMakerConical(inkex.EffectExtension):
    """
    Creates a new layer with the drawings for a parametrically generaded box.
    """
    def __init__(self):
        inkex.Effect.__init__(self)
        self.knownUnits = ['in', 'pt', 'px', 'mm', 'cm', 'm', 'km', 'pc', 'yd', 'ft']
        self.arg_parser.add_argument('--unit', default = 'mm', help = 'Unit, should be one of ')
        self.arg_parser.add_argument('--thickness', type = float, default = 3.0, help = 'Material thickness')
        self.arg_parser.add_argument('--d1', type = float, default = 50.0,  help = 'Small circle diameter')
        self.arg_parser.add_argument('--d2', type = float, default = 100.0, help = 'Large circle diameter')
        self.arg_parser.add_argument('--zc', type = float, default = 50.0, help = 'Cone height')
        self.arg_parser.add_argument('--nb_pieces', type = int, default = 1, help = '# pieces for cone')
        self.arg_parser.add_argument('--inner_size', type = inkex.Boolean, default = True,  help = 'Dimensions are internal')

    try:
        inkex.Effect.unittouu   # unitouu has moved since Inkscape 0.91
    except AttributeError:
        try:
            def unittouu(self, unit):
                return inkex.unittouu(unit)
        except AttributeError:
            pass

    def effect(self):
        """
        Draws a conic box, based on provided parameters
        """

        # input sanity check
        error = False
        if self.options.zc < 15:
            inkex.errormsg('Error: Height should be at least 15mm')
            error = True

        if self.options.d1 < 30:
            inkex.errormsg('Error: d1 should be at least 30mm')
            error = True

        if self.options.d2 < self.options.d1 + 0.009999:
            inkex.errormsg('Error: d2 should be at d1 + 0.01mm')
            error = True

        if self.options.thickness <  1 or self.options.thickness >  10:
            inkex.errormsg('Error: thickness should be at least 1mm and less than 10mm')
            error = True

        if error:
            exit()


        # convert units
        unit = self.options.unit
        d1 = self.svg.unittouu(str(self.options.d1) + unit)
        d2 = self.svg.unittouu(str(self.options.d2) + unit)
        zc = self.svg.unittouu(str(self.options.zc) + unit)
        
        nb_parts = self.options.nb_pieces
        
        thickness = self.svg.unittouu(str(self.options.thickness) + unit)
        #Si prend dimensions externes, corrige les tailles
        if self.options.inner_size == False:
            d1 -= 2*thickness
            d2 -= 2*thickness
            zc -= 2*thickness
            
        svg = self.document.getroot()
        docWidth = self.svg.unittouu(svg.get('width'))
        docHeigh = self.svg.unittouu(svg.attrib['height'])

        layer = etree.SubElement(svg, 'g')
        layer.set(inkex.addNS('label', 'inkscape'), 'Conical Box')
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')

        #Compute size of projection
        h1 = math.sqrt(zc*zc + (d2-d1)*(d2-d1)/4)
        L1 = d1 * h1 / (d2 - d1)
        L2 = d2 * h1 / (d2 - d1)

        alpha = math.pi*d2/L2
        #calcul nombre de pas (sauf premeirs et derniers) pour D1, avec 2*2 mm par pas
        nombre_pas = round((d1 * math.pi - 6) / 4)
        #calcul angle par pas, ajoute 1.5 pour tenir compte des premiers et derniers pas qui font 3/4 de pas.
        angle_par_pas = alpha / (nombre_pas+1.5*nb_parts)
        taille_exacte_pas = math.pi * d1 / (nombre_pas+1.5*nb_parts)

        # do not put elements right at the edge of the page.
        # Drawing will max left will be L2*cos(alpha) - thickness
        if alpha > math.pi:
            xOffset = -L2 - thickness - 10
            xmin = -L2 - thickness
            xmax = L2 + thickness
        else:
            xOffset = L2 * math.cos(alpha) - thickness - 10
            xmin = (L2+thickness) * math.cos(alpha)
            xmax = L2 + thickness
        if alpha > math.pi*1.5:
            yOffset = -L2 - thickness - 10
            ymin = -L2 - thickness
            ymax = L2 + thickness
        elif alpha > math.pi:
            yOffset = (L2+thickness)*math.sin(alpha) - 10
            ymin = (L2+thickness)*math.sin(alpha) - thickness
            ymax = L2 + thickness
        elif alpha > math.pi/2:
            yOffset = 0
            ymin = 0
            ymax = L2 + thickness
        else:
            yOffset = 0
            ymin = 0
            ymax = (L2+thickness)*math.sin(alpha)

        #dessine la partie "souple"        
        PartieSouple = CurvedSurface(L1, L2, nombre_pas, angle_par_pas, taille_exacte_pas, nb_parts, thickness, layer, xOffset, yOffset)
        PartieSouple.GeneratePaths()
        #génère maintenant le path du grand cercle
        #Un pas de plus pour les cercles, pour tenir compte du début et de la fin
        nombre_pas += 1
        #Positionne Offset
        gen_cercle(d2, nombre_pas, thickness, -xmax - d2/2 + xOffset + 10, yOffset - ymax - d2/2 - 10 , layer) 
        #puis pour le petit cercle
        gen_cercle(d1, nombre_pas, thickness, -xmax - d1/2 + xOffset + 10,  d1/2 + yOffset - ymin + 10, layer)                                  

if __name__ == '__main__':
    BoxMakerConical().run()