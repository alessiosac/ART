#!/bin/bash

sudo apt-get install mate-terminal


tab="--tab"
cmd1="bash -c 'python3.8 DT.py --env net_env:net-v1 --load_trained ./Model_saved_for_sv1';bash"
cmd6="bash -c 'python3.8 DT.py --env net_env:net-v6 --load_trained ./Model_saved_for_sv6';bash"
cmd7="bash -c 'python3.8 DT.py --env net_env:net-v7 --load_trained ./Model_saved_for_sv7';bash"
cmd8="bash -c 'python3.8 DT.py --env net_env:net-v8 --load_trained ./Model_saved_for_sv8';bash"
cmd9="bash -c 'python3.8 DT.py --env net_env:net-v9 --load_trained ./Model_saved_for_sv9';bash"

foo=""

foo+=($tab -t "s1" -e "$cmd1")
foo+=($tab -t "s6" -e "$cmd6")
foo+=($tab -t "s7" -e "$cmd7")
foo+=($tab -t "s8" -e "$cmd8")
foo+=($tab -t "s9" -e "$cmd9")

mate-terminal "${foo[@]}"

exit 0