#!/bin/bash
clear

for folder in */ ; do 
	if [[ -f "${folder}/meta.json" ]]; then
		sed -i 's/github.com\/vmario89/github.com\/eridur-de/g' ${folder}/meta.json
		sed -i 's/mightyscape-1.X/mightyscape-1.2/g' ${folder}/meta.json
		
	fi
done
