#!/bin/bash
for file in boxes.py/*.inx ; do
	#echo $file
	sed -i 's/"Boxes.py"/"FabLab Chemnitz Boxes.py"/g' $file
done
