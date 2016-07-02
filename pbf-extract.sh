#!/bin/bash

if [ "$1" == "" ]; then
	echo "Please provide an pbf"
	exit 1
fi

pbf=$1

top=-6.0
left=106.0
bottom=-6.5
right=107.5

osmosis --read-pbf $pbf \
	--bounding-box top=$top left=$left bottom=$bottom right=$right \
	--write-pbf indonesia-jakarta.osm.pbf


