#!/bin/bash

# Specify the directory where the files are located
directory="/home/p4/Desktop/ROAR22"

# Remove files starting with "latency"
rm -f "$directory"/latency*

# Remove files starting with "arriving"
rm -f "$directory"/arriving*

echo "Files starting with 'latency' and 'arriving' have been canceled."
