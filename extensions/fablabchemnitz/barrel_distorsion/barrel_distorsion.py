import math
import re
import inkex
from inkex import bezier
from inkex.paths import Path, CubicSuperPath

class BarrelDistorsion(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--lambda_coef", type=float, default=-5.0, help="command line help")

    def distort_coordinates(self, x, y):
        """Method applies barrel distorsion to given points with distorsion center in center of image, selected to 
        
        Args:
            x (float): X coordinate of given point
            y (float): Y coordinate of given point
        
        Returns:
            tuple(float, float): Tuple with X,Y distorted coordinates of given point
        """
        x_u = (x - self.x_c) / (self.width + self.height)
        y_u = (y - self.y_c) / (self.width + self.height)
        x_d = x_u / 2 / (self.q * y_u**2 + x_u**2 * self.q) * (1 - math.sqrt(1 - 4 * self.q * y_u**2 - 4 * x_u**2 * self.q))
        y_d = y_u / 2 / (self.q * y_u**2 + x_u**2 * self.q) * (1 - math.sqrt(1 - 4 * self.q * y_u**2 - 4 * x_u**2 * self.q))
        x_d *= self.width + self.height
        y_d *= self.width + self.height
        x_d += self.x_c
        y_d += self.y_c
        return x_d, y_d

    def split_into_nodes(self, nodes_number=1000):
        for id, node in self.svg.selected.items():
            if node.tag == inkex.addNS('path', 'svg'):
                p = CubicSuperPath(node.get('d'))
                new = []
                for sub in p:
                    new.append([sub[0][:]])
                    i = 1
                    while i <= len(sub) - 1:
                        length = bezier.cspseglength(
                            new[-1][-1], sub[i])

                        splits = nodes_number
                        for s in range(int(splits), 1, -1):
                            new[-1][-1], next, sub[
                                i] = bezier.cspbezsplitatlength(
                                    new[-1][-1], sub[i], 1.0 / s)
                            new[-1].append(next[:])
                        new[-1].append(sub[i])
                        i += 1
                node.set('d', str(CubicSuperPath(new)))

    def effect(self):
        if re.match(r'g\d+',
                    list(self.svg.selected.items())[0][0]) is not None:
            raise SystemExit(
                "You are trying to distort group of objects.\n This extension works only with path objects due to Inkscape API restrictions.\n Ungroup your objects and try again."
            )
        self.split_into_nodes()
        self.q = self.options.lambda_coef
        if self.q == 0.0:
            inkex.errormsg("Invalid lambda coefficient. May not be exactly zero.")
            return
        nodes = []
        for id, node in self.svg.selected.items():
            if node.tag == inkex.addNS('path', 'svg'):
                path = Path(node.get('d')).to_arrays()
                nodes += path
        if len(nodes) == 0:
           inkex.utils.debug("Selection is invalid. Please change selection to paths only.")
           exit(1)
        nodes_filtered = [x for x in nodes if x[0] != 'Z']
        x_coordinates = [x[-1][-2] for x in nodes_filtered]
        y_coordinates = [y[-1][-1] for y in nodes_filtered]
        self.width = max(x_coordinates) - min(x_coordinates)
        self.height = max(y_coordinates) - min(y_coordinates)
        self.x_c = sum(x_coordinates) / len(x_coordinates)
        self.y_c = sum(y_coordinates) / len(y_coordinates)
        for id, node in self.svg.selected.items():
            if node.tag == inkex.addNS('path', 'svg'):
                path = Path(node.get('d')).to_arrays()
                distorted = []
                first = True
                for cmd, params in path:
                    if cmd != 'Z':
                        if first == True:
                            x = params[-2]
                            y = params[-1]
                            distorted.append(
                                ['M',
                                 list(self.distort_coordinates(x, y))])
                            first = False
                        else:
                            x = params[-2]
                            y = params[-1]
                            distorted.append(
                                ['L', self.distort_coordinates(x, y)])
                node.set('d', str(Path(distorted)))


if __name__ == '__main__':
    BarrelDistorsion().run()