
from math import sqrt, isnan
import numpy as np

try:
    from sklearn.cluster import MeanShift, estimate_bandwidth
    from sklearn.utils import shuffle

    cluster_analysis_available = True
    print("Cluster analysis is available")
except ImportError:
    cluster_analysis_available = False
    print("Cluster analysis is not available")

try:
    import Image
    pil_available = True
    print("PIL is available")
except ImportError:
    print("PIL is not available")
    try:
        from PIL import Image
        print("Pillow is available")
        pil_available = True
    except ImportError:
        print("Neither PIL or Pillow are available")
        pil_available = False

from color.colors import *

if pil_available:

    def imread(filename):
        img = Image.open(filename)

class Box(object):
    def __init__(self, arr):
        self._array = arr

    def population(self):
        return self._array.size

    def axis_size(self, idx):
        slice_ = self._array[:, idx]
        M = slice_.max()
        m = slice_.min()
        return M - m

    def biggest_axis(self):
        sizes = [self.axis_size(i) for i in range(3)]
        return max(range(3), key = lambda i: sizes[i])
    
    def mean(self):
        return self._array.mean(axis=0)
    
    def mean_color(self):
        size = self._array.size
        if not size:
            return None
        xs = self._array.mean(axis=0)
        x,y,z = xs[0], xs[1], xs[2]
        if isnan(x) or isnan(y) or isnan(z):
            return None
        return Color(int(x), int(y), int(z))

    def div_pos(self, idx):
        slice_ = self._array[:, idx]
        M = slice_.max()
        m = slice_.min()
        return (m+M)/2.0

    def divide(self):
        axis = self.biggest_axis()
        q = self.div_pos(axis)
        idxs = self._array[:, axis] > q
        smaller = self._array[~idxs]
        bigger  = self._array[idxs]
        self._array = smaller
        return Box(bigger)

if pil_available and cluster_analysis_available:

    # Use Means Shift algorithm for cluster analysis

    def cluster_analyze(filename, N=1000):
        image = imread(filename)
        w,h,d = tuple(image.shape)
        image_array = np.array( np.reshape(image, (w * h, d)), dtype=np.float64 )
        #if image.dtype == 'uint8':
        #    image_array = image_array / 255.0
        image_array_sample = shuffle(image_array, random_state=0)[:N]
        bandwidth = estimate_bandwidth(image_array_sample, quantile=0.01, n_samples=500)
        ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)
        ms.fit(image_array_sample)
        cluster_centers = ms.cluster_centers_
        n_clusters = len(cluster_centers)
        colors = []
        print("Number of clusters: {}".format(n_clusters))
        for x in cluster_centers:
            #print x
            clr = Color()
            clr.setRGB1((x[0], x[1], x[2]))
            colors.append(clr)
        return colors


if pil_available:

# Use very fast algorithm for image analysis, translated from Krita's kis_common_colors_recalculation_runner.cpp
# Do not know exactly why does this algorithm work, but it does.
# Initial (C) Adam Celarek

    def bin_divide_colors(filename, N=1<<16, n_clusters=49):
        img = Image.open(filename)
        if img.mode == 'P':
            img = img.convert('RGB')
        w,h = img.size
        n_pixels = w*h
        if n_pixels > N:
            ratio = sqrt( float(N) / float(n_pixels) )
            w,h = int(w*ratio), int(h*ratio)
            img = img.resize((w,h))

        image = np.array(img)
        w,h,d = tuple(image.shape)
        colors = np.array( np.reshape(image, (w * h, d)), dtype=np.float64 )
        #if image.dtype == 'uint8':
        #    colors = colors / 255.0
        colors = colors[:,0:3]

        boxes = [Box(colors)]

        while (len(boxes) < n_clusters * 3/5) and (len(colors) > n_clusters * 3/5):
            biggest_box = None
            biggest_box_population = None

            for box in boxes:
                population = box.population()
                if population <= 3:
                    continue
                if biggest_box_population is None or (population > biggest_box_population and box.axis_size(box.biggest_axis()) >= 3):
                        biggest_box = box
                        biggest_box_population = population

            if biggest_box is None or biggest_box.population() <= 3:
                break
            
            new_box = biggest_box.divide()
            boxes.append(new_box)

        while (len(boxes) < n_clusters) and (len(colors) > n_clusters):
            biggest_box = None
            biggest_box_axis_size = None

            for box in boxes:
                if box.population() <= 3:
                    continue
                size = box.axis_size(box.biggest_axis())
                if biggest_box_axis_size is None or (size > biggest_box_axis_size and size >= 3):
                    biggest_box = box
                    biggest_box_axis_size = size

            if biggest_box is None or biggest_box.population() <= 3:
                break

            new_box = biggest_box.divide()
            boxes.append(new_box)

        result = [box.mean_color() for box in boxes if box.mean_color() is not None]
        return result

image_loading_supported = pil_available or cluster_analysis_available

if pil_available:
    get_common_colors = bin_divide_colors
    use_sklearn = False
elif cluster_analysis_available :
    get_common_colors = cluster_analyze
    use_sklearn = True

