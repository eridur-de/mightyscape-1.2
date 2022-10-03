#!/usr/bin/env python3

import re
import os
import inkex
from inkex.command import inkscape

def calculateCMYK(red, green, blue):
    C = float()
    M = float()
    Y = float()
    K = float()

    if 1.00 - red < 1.00 - green:
        K = 1.00 - red
    else:
        K = 1.00 - green

    if 1.00 - blue < K:
        K = 1.00 - blue

    if K != 1.00:
        C = ( 1.00 - red   - K ) / ( 1.00 - K )
        M = ( 1.00 - green - K ) / ( 1.00 - K )
        Y = ( 1.00 - blue  - K ) / ( 1.00 - K )

    return [C, M, Y, K]

def clean_svg_color_definitions(svg):
    def change_colors(origin, color_type):
        for i in range(len(str(origin).split(color_type + ':'))):
            if str(str(origin).split(color_type + ':')[i].split(';')[0]) in inkex.colors.SVG_COLOR.keys():
                color_numbers = str(inkex.Color(inkex.Color(str(str(origin).split(color_type + ':')[i].split(';')[0])).to_rgb()))
                origin = str(origin).replace(':' + str(str(origin).split(color_type + ':')[i].split(';')[0]) + ';', ':' + color_numbers + ';')
        return origin

    colortypes = ['fill', 'stop-color', 'flood-color', 'lighting-color', 'stroke']
    for i in range(len(colortypes)):
        svg = change_colors(svg, colortypes[i])

    return svg

def removeK(origin):
    def reset_opacity(value):
        return str(value.group()).split('opacity:')[0] + "opacity:0;"
    #return re.sub("#000000;fill-opacity:[0-9.]+;", reset_opacity, re.sub("#000000;stop-opacity:[0-9.]+;", reset_opacity, re.sub("#000000;stroke-opacity:[0-9.]+;", reset_opacity, re.sub("#000000;flood-opacity:[0-9.]+;", reset_opacity, re.sub("#000000;lighting-opacity:[0-9.]+;", reset_opacity, origin)))))
    return re.sub("#000000;fill-opacity:[0-9.?]+", reset_opacity, re.sub("#000000;stop-opacity:[0-9.?]+", reset_opacity, re.sub("#000000;stroke-opacity:[0-9.?]+", reset_opacity, re.sub("#000000;flood-opacity:[0-9.?]+", reset_opacity, re.sub("#000000;lighting-opacity:[0-9.?]+", reset_opacity, origin)))))

def representC(value):
    # returns CMS color if available
    if (re.search("icc-color", value.group())):
        return str(inkex.Color((float(1.00 - float(re.split(r'[,\)\s]+',value.group())[2])), float(1.00), float(1.00))))
    else:
        red =   float(inkex.Color(str(value.group())).to_rgb()[0]/255.00)
        green = float(inkex.Color(str(value.group())).to_rgb()[1]/255.00)
        blue =  float(inkex.Color(str(value.group())).to_rgb()[2]/255.00)
        return str(inkex.Color((float(1.00 - calculateCMYK(red, green, blue)[0]), float(1.00), float(1.00))))

def representM(value):
    # returns CMS color if available
    if ( re.search("icc-color", value.group()) ):
        return str(inkex.Color((float(1.00), float(1.00 - float(re.split(r'[,\)\s]+',value.group())[3])), float(1.00))))
    else:
        red =   float(inkex.Color(str(value.group())).to_rgb()[0]/255.00)
        green = float(inkex.Color(str(value.group())).to_rgb()[1]/255.00)
        blue =  float(inkex.Color(str(value.group())).to_rgb()[2]/255.00)
        return str(inkex.Color((float(1.00), float(1.00 - calculateCMYK(red, green, blue)[1]), float(1.00))))

def representY(value):
    # returns CMS color if available
    if (re.search("icc-color", value.group()) ):
        return str(inkex.Color((float(1.00), float(1.00), float(1.00 - float(re.split(r'[,\)\s]+',value.group())[4])))))
    else:
        red =   float(inkex.Color(str(value.group())).to_rgb()[0]/255.00)
        green = float(inkex.Color(str(value.group())).to_rgb()[1]/255.00)
        blue =  float(inkex.Color(str(value.group())).to_rgb()[2]/255.00)
        return str(inkex.Color((float(1.00), float(1.00), float(1.00 - calculateCMYK(red, green, blue)[2]))))

def representK(value):
    # returns CMS color if available
    if (re.search("icc-color", value.group()) ):
        return str(inkex.Color((float(1.00 - float(re.split(r'[,\)\s]+',value.group())[5])), float(1.00 - float(re.split(r'[,\)\s]+',value.group())[5])), float(1.00 - float(re.split(r'[,\)\s]+',value.group())[5])))))
    else:
        red =   float(inkex.Color(str(value.group())).to_rgb()[0]/255.00)
        green = float(inkex.Color(str(value.group())).to_rgb()[1]/255.00)
        blue =  float(inkex.Color(str(value.group())).to_rgb()[2]/255.00)
        return str(inkex.Color((float(1.00 - calculateCMYK(red, green, blue)[3]), float(1.00 - calculateCMYK(red, green, blue)[3]), float(1.00 - calculateCMYK(red, green, blue)[3]))))


def generate_svg_separations(temp_dir, original_source, overblack):
    svg_ready = clean_svg_color_definitions(original_source)

    with open(os.path.join(temp_dir, "separationK.svg"), "w") as f:
        f.write(re.sub(r"#[a-fA-F0-9]{6}( icc-color\(.*?\))?", representK, svg_ready))

    if overblack:
        svg_ready = removeK(svg_ready)

    with open(os.path.join(temp_dir, "separationC.svg"), "w") as f:
        f.write(re.sub(r"#[a-fA-F0-9]{6}( icc-color\(.*?\))?", representC, svg_ready))
    with open(os.path.join(temp_dir, "separationM.svg"), "w") as f:
        f.write(re.sub(r"#[a-fA-F0-9]{6}( icc-color\(.*?\))?", representM, svg_ready))
    with open(os.path.join(temp_dir, "separationY.svg"), "w") as f:
        f.write(re.sub(r"#[a-fA-F0-9]{6}( icc-color\(.*?\))?", representY, svg_ready))
            
def generate_png_separations(temp_dir, area_to_export, resolution, alpha):
    if alpha:
        alpha_command = ""
    else:
        alpha_command = ";export-background:white"
    for color in ['C', 'M', 'Y', 'K']:
        cmd = area_to_export + alpha_command + ';export-dpi:' + str(resolution) + ';export-background-opacity:1;export-filename:' + os.path.join(temp_dir, "separated" + area_to_export.replace(' ', '') + color + ".png") + ';export-do'
        #inkex.utils.debug(cmd)
        cli_output = inkscape(os.path.join(temp_dir, "separation" + color + ".svg"), actions=cmd)
        if len(cli_output) > 0:
            inkex.utils.debug(cli_output)
    #inkex.utils.debug(os.listdir(temp_dir))
            