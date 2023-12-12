#!/bin/bash

# List of IP addresses
IP_ADDRESSES=("10.0.1.1" "10.0.1.4" "10.0.6.2" "10.0.6.5" "10.0.7.3" "10.0.7.6" "10.0.8.7" "10.0.8.8" "10.0.9.9" "10.0.9.10")

# Duration for iperf3 in seconds (1 hour = 3600 seconds)
DURATION=3600

# Output file
OUTPUT_FILE="iperf3_test.sh"

# Create the script
echo "#!/bin/bash" > $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

# Loop through each pair of IP addresses
for ((i=0; i<${#IP_ADDRESSES[@]}; i++)); do
  for ((j=$i+1; j<${#IP_ADDRESSES[@]}; j++)); do
    SOURCE_IP="${IP_ADDRESSES[$i]}"
    DESTINATION_IP="${IP_ADDRESSES[$j]}"

    # Append iperf3 command to the script
    echo "iperf3 -c $DESTINATION_IP -t $DURATION -i 1 -P 1 &" >> $OUTPUT_FILE
  done
done

# Make the script executable
chmod +x $OUTPUT_FILE

echo "Script generated successfully. Execute ./$OUTPUT_FILE on each host to start iperf3 tests."