#!/usr/bin/env python3

import subprocess
import os

def generate_final_file(isvector, hide_inside_marks, colormode, width, height, space, strokewidth, bleedsize, marksize, temp_dir):
    if not isvector:

        if "nt" in os.name:
            shell = True
        else:
             shell = False

        command = []
        final_command = ['convert']

        for color in colormode:
            command.append('convert')
            command.append('-size')
            command.append(str(sum(width) + (marksize*2) + (space * (len(width) -1))) + 'x' + str(sum(height) + (marksize*2) + (space * (len(height) -1))))
            command.append('xc:white')
            command.append('-stroke')
            command.append('black')
            command.append('-strokewidth')
            command.append(str(strokewidth))

            width_value = 0
            number_of_column = 1

            for column in width:
                height_value = 0
                number_of_line = 1

                for line in height:
                    with open(os.path.join(temp_dir, 'str.txt'), 'a') as f:
                        f.write(str(width.index(column)))

                    if not hide_inside_marks or (hide_inside_marks and number_of_column == 1):
                        command.append('-draw')
                        command.append('line ' + str(width_value + marksize) + ',' + str(height_value + marksize + bleedsize) + ', ' + str(width_value) + ',' + str(height_value + marksize + bleedsize))
                        command.append('-draw')
                        command.append('line ' + str(width_value + marksize) + ',' + str(height_value + line + marksize - bleedsize) + ', ' + str(width_value) + ',' + str(height_value + line + marksize - bleedsize))

                    if not hide_inside_marks or (hide_inside_marks and number_of_line == 1):
                        command.append('-draw')
                        command.append('line ' + str(width_value + marksize + bleedsize) + ',' + str(height_value + marksize) + ', ' + str(width_value + marksize + bleedsize) + ',' + str(height_value))
                        command.append('-draw')
                        command.append('line ' + str(width_value + column + marksize - bleedsize) + ',' + str(height_value + marksize) + ', ' + str(width_value + column + marksize - bleedsize) + ',' + str(height_value))

                    if not hide_inside_marks or (hide_inside_marks and number_of_column == len(width)):
                        command.append('-draw')
                        command.append('line ' + str(width_value + marksize + column) + ',' + str(height_value + marksize + bleedsize) + ', ' + str(width_value + (marksize*2) + column) + ',' + str(height_value + marksize + bleedsize))
                        command.append('-draw')
                        command.append('line ' + str(width_value + marksize + column) + ',' + str(height_value + line + marksize - bleedsize) + ', ' + str(width_value + (marksize*2) + column) + ',' + str(height_value + marksize + line - bleedsize))

                    if not hide_inside_marks or (hide_inside_marks and number_of_line == len(height)):
                        command.append('-draw')
                        command.append('line ' + str(width_value + marksize + bleedsize) + ',' + str(height_value + line + marksize) + ', ' + str(width_value + marksize + bleedsize) + ',' + str(height_value + line + (marksize*2)))
                        command.append('-draw')
                        command.append('line ' + str(width_value + column + marksize - bleedsize) + ',' + str(height_value + line + marksize) + ', ' + str(width_value + marksize + column - bleedsize) + ',' + str(height_value + line + (marksize*2)))

                    height_value += line + space
                    number_of_line += 1
                width_value += column + space
                number_of_column += 1
            command.append(os.path.join(temp_dir, 'cut_mark_' + color + '.png'))
            subprocess.Popen(command, shell=shell).wait()
            del command[:]

            command.append('convert')
            command.append(os.path.join(temp_dir, 'cut_mark_' + color + '.png'))
            command.append('-colorspace')
            command.append(str(colormode).lower())
            command.append('-channel')
            command.append('K')
            command.append('-separate')
            command.append(os.path.join(temp_dir, 'cut_mark_' + color + '.png'))
            subprocess.Popen(command, shell=shell).wait()
            del command[:]

            final_command.append(os.path.join(temp_dir, 'cut_mark_' + color + '.png'))

        final_command.extend(['-set', 'colorspace', colormode, '-combine', os.path.join(temp_dir, 'cut_mark.tiff')])
        subprocess.Popen(final_command, shell=shell).wait()
