
from color.colors import *
from color.spaces import *

def find_min(idx, occupied, d):
    best_i = None
    best_y = None
    best_clr = None
    for i, clr in d.iteritems():
        if i in occupied:
            continue
        y = clr[idx]
        if best_y is None or y < best_y:
            best_i = i
            best_y = y
            best_clr = clr
    if best_y is not None:
        return best_i
    for i, clr in d.iteritems():
        y = clr[idx]
        if best_y is None or y < best_y:
            best_i = i
            best_y = y
            best_clr = clr
    assert best_i is not None
    return best_i

def find_max(idx, occupied, d):
    best_i = None
    best_y = None
    best_clr = None
    for i, clr in d.iteritems():
        if i in occupied:
            continue
        y = clr[idx]
        if best_y is None or y > best_y:
            best_i = i
            best_y = y
            best_clr = clr
    if best_y is not None:
        return best_i
    for i, clr in d.iteritems():
        y = clr[idx]
        if best_y is None or y > best_y:
            best_i = i
            best_y = y
            best_clr = clr
    assert best_i is not None
    return best_i

def match_colors(colors1, colors2):
    hsvs1 = dict(enumerate([c.getHCY() for c in colors1 if c is not None]))
    hsvs2 = dict(enumerate([c.getHCY() for c in colors2 if c is not None]))
    occupied = []
    result = {}
    while len(hsvs1.keys()) > 0:
        # Darkest of SVG colors
        darkest1_i = find_min(2, [], hsvs1)
        # Darkest of palette colors
        darkest2_i = find_min(2, occupied, hsvs2)
        hsvs1.pop(darkest1_i)
        occupied.append(darkest2_i)
        result[darkest1_i] = darkest2_i
        if not hsvs1:
            break

        # Lightest of SVG colors
        lightest1_i = find_max(2, [], hsvs1)
        # Lightest of palette colors
        lightest2_i = find_max(2, occupied, hsvs2)
        hsvs1.pop(lightest1_i)
        occupied.append(lightest2_i)
        result[lightest1_i] = lightest2_i
        if not hsvs1:
            break

        # Less saturated of SVG colors
        grayest1_i = find_min(1, [], hsvs1)
        # Less saturated of palette colors
        grayest2_i = find_min(1, occupied, hsvs2)
        hsvs1.pop(grayest1_i)
        occupied.append(grayest2_i)
        result[grayest1_i] = grayest2_i
        if not hsvs1:
            break

        # Most saturated of SVG colors
        saturated1_i = find_max(1, [], hsvs1)
        # Most saturated of palette colors
        saturated2_i = find_max(1, occupied, hsvs2)
        hsvs1.pop(saturated1_i)
        occupied.append(saturated2_i)
        result[saturated1_i] = saturated2_i
        if not hsvs1:
            break

        redest1_i = find_min(0, [], hsvs1)
        redest2_i = find_min(0, occupied, hsvs2)
        hsvs1.pop(redest1_i)
        occupied.append(redest2_i)
        result[redest1_i] = redest2_i
        if not hsvs1:
            break

        bluest1_i = find_max(0, [], hsvs1)
        bluest2_i = find_max(0, occupied, hsvs2)
        hsvs1.pop(bluest1_i)
        occupied.append(bluest2_i)
        result[bluest1_i] = bluest2_i

    clrs = []
    for i in range(len(result.keys())):
        j = result[i]
        clrs.append(colors2[j])
    return clrs


