#!/usr/bin/env python3
import argparse
import threading
import time
import struct
from importlib.machinery import SourceFileLoader
import grpc
import sys
import os
import queue

from utils_file_for_P4Runtime.p4runtime_lib import helper, bmv2

# from net_env.envs import net_env

NUMBER_SWITCHES = 9

LOWER_SWITCHES = [1, 6, 7, 8, 9]
UPPER_SWITCHES = [2, 3, 4, 5]

subnet_identification = {"1": ("10.0.1.1", "10.0.1.4"), "6": ("10.0.6.2", "10.0.6.5"), "7": ("10.0.7.3", "10.0.7.6"),
                         "8": ("10.0.8.7", "10.0.8.8"), "9": ("10.0.9.9", "10.0.9.10")}
num_of_host_per_subnet = 2

connected_switches = []

counter_to_pass = []

p4info_value = 'build/ibn.p4.p4info.txt'

p4info_helper = helper.P4InfoHelper(p4info_value)

digest_queue = queue.Queue()

ready = [False for _ in range(0, 9)]


def ipv4_lpm_add(p4info_helper, switch_id, ingress_sw, table_name, action_name, dst_ip_addr, splitted):
    # print("debug:  " + table_name + " " + action_name + " " + dst_ip_addr + " ")
    if action_name == "set_nhopA":
        dst_eth_addr = splitted[5]
        port = int(splitted[6].split("\n")[0])
        # print("%s %d" % (dst_eth_addr, port))
        if switch_id in LOWER_SWITCHES:
            table_entry = p4info_helper.buildTableEntry(
                table_name="MyIngress." + table_name,
                match_fields={
                    "hdr.ipv4.dstAddr": (dst_ip_addr, 32)
                },
                action_name="MyIngress." + action_name,
                action_params={
                    "dstAddr": dst_eth_addr,
                    "port": port,
                })
            ingress_sw.WriteTableEntry(table_entry)
        if switch_id in UPPER_SWITCHES:
            table_entry = p4info_helper.buildTableEntry(
                table_name="MyIngress." + table_name,
                match_fields={
                    "hdr.ipv4.dstAddr": (dst_ip_addr, 24)
                },
                action_name="MyIngress." + action_name,
                action_params={
                    "dstAddr": dst_eth_addr,
                    "port": port,
                })
            ingress_sw.WriteTableEntry(table_entry)
    else:
        subnet = dst_ip_addr.split(".")[2]  # 10.0.6.2 -> 6
        subnet_in_dic = subnet_identification[subnet]  # 6 -> 10.0.6.2 e 10.0.6.5
        ecmp_group_id = int(splitted[5])
        n_nhop = int(splitted[6].split("\n")[0])
        # print("%d %d" % (ecmp_group_id, n_nhop))
        for x in range(0, num_of_host_per_subnet):
            ip_addr = subnet_in_dic[x]
            table_entry = p4info_helper.buildTableEntry(
                table_name="MyIngress." + table_name,
                match_fields={
                    "hdr.ipv4.dstAddr": (ip_addr, 32)
                },
                action_name="MyIngress." + action_name,
                action_params={
                    "ecmp_group_id": ecmp_group_id,
                    "num_nhops": n_nhop,
                })
            ingress_sw.WriteTableEntry(table_entry)


def group_add(p4info_helper, ingress_sw, table_name, action_name, ecmp_group_id, ecmp_hash, dst_eth_addr, port):
    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress." + table_name,
        match_fields={
            "meta.ecmp_group_id": ecmp_group_id,
            "meta.ecmp_hash": ecmp_hash
        },
        action_name="MyIngress." + action_name,
        action_params={
            "dstAddr": dst_eth_addr,
            "port": port,
        })
    ingress_sw.WriteTableEntry(table_entry)


def readTableRules(p4info_helper, sw):
    """
    Reads the table entries from all tables on the switch.

    :param p4info_helper: the P4Info helper
    :param sw: the switch connection
    """
    print('\n----- Reading tables rules for %s -----' % sw.name)
    for response in sw.ReadTableEntries():
        for entity in response.entities:
            entry = entity.table_entry
            table_name = p4info_helper.get_tables_name(entry.table_id)
            print('%s: ' % table_name, end=' ')
            for m in entry.match:
                print(p4info_helper.get_match_field_name(table_name, m.field_id), end=' ')
                print('%r' % (p4info_helper.get_match_field_value(m),), end=' ')
            action = entry.action.action
            action_name = p4info_helper.get_actions_name(action.action_id)
            print('->', action_name, end=' ')
            for p in action.params:
                print(p4info_helper.get_action_param_name(action_name, p.param_id), end=' ')
                print('%r' % p.value, end=' ')
            print()


def printGrpcError(e):
    print("gRPC Error:", e.details(), end=' ')
    status_code = e.code()
    print("(%s)" % status_code.name, end=' ')
    traceback = sys.exc_info()[2]
    print("[%s:%d]" % (traceback.tb_frame.f_code.co_filename, traceback.tb_lineno))


def printCounter(p4info_helper, switch_number, counter_name):
    connected_switch = connected_switches[switch_number]
    for index in range(1, 7):
        for response in connected_switch.ReadCounters(p4info_helper.get_counters_id(counter_name), index):
            for entity in response.entities:
                counter = entity.counter_entry
                print("s%d %s %d: %d packets (%d bytes)" % (
                    switch_number, counter_name, index,
                    counter.data.packet_count, counter.data.byte_count
                ))
                counter_to_pass.append(
                    [switch_number, counter_name, index, counter.data.packet_count, counter.data.byte_count])
    return counter_to_pass
    # net_env.variable_to_get(counter_to_pass)
    # next_hop = net_env.next_destination()


def printDst(p4info_helper, switch_number, counter_name):
    connected_switch = connected_switches[switch_number]
    for index in range(1, 6):  # dal primo dst switch al quinto
        for response in connected_switch.ReadCounters(p4info_helper.get_counters_id(counter_name), index):
            for entity in response.entities:
                counter = entity.counter_entry
                print("s%d %s %d: %d packets (%d bytes)" % (
                    switch_number, counter_name, index,
                    counter.data.packet_count, counter.data.byte_count
                ))


def getCounterValue():
    return counter_to_pass


def define_connection(bmv2_file_path, switch_id):
    # p4info_helper = helper.P4InfoHelper(p4info_file_path)
    print("Connected to s" + str(switch_id))
    try:
        # Create a switch connection object for s1 and s2;
        # this is backed by a P4Runtime gRPC connection.
        # Also, dump all P4Runtime messages sent to switch to given txt files.
        switch = bmv2.Bmv2SwitchConnection(
            name='s' + str(switch_id),
            address='127.0.0.1:5005' + str(switch_id),
            device_id=int(switch_id) - 1,
            proto_dump_file='logs/s' + str(switch_id) + '-p4runtime-requests.txt')

        # Send master arbitration update message to establish this controller as
        # master (required by P4Runtime before performing any other write operation)
        switch.MasterArbitrationUpdate()

        # Install the P4 program on the switches
        # p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file)

        switch.SetForwardingPipelineConfig(p4info=p4info_helper.p4info, bmv2_json_file_path=bmv2_file_path)

        ## Write the rules that tunnel traffic from h1 to h2
        with open("s" + str(switch_id) + "-commands.txt") as file:
            lines = file.readlines()
            for line in lines:
                splitted = line.split(" ")
                command = splitted[0]
                if command == "\n" or command == "//":
                    continue
                table_name = splitted[1]
                if command == "table_add":
                    if table_name == "ipv4_lpmA":
                        action_name = splitted[2]
                        dst_ip_addr = splitted[3]
                        dst_ip_addr = dst_ip_addr.split("/")[0]
                        ipv4_lpm_add(p4info_helper, switch_id, switch, table_name, action_name, dst_ip_addr, splitted)
                    elif table_name == "ecmp_group_to_nhopA":
                        action_name = splitted[2]
                        ecmp_group_id = int(splitted[3])
                        ecmp_hash = int(splitted[4])
                        dst_eth_addr = splitted[6]
                        port = int(splitted[7].split("\n")[0])
                        # print("debug: %s %s %d %d %s %d  " % (table_name, action_name, ecmp_group_id, ecmp_hash, dst_eth_addr, port))
                        group_add(p4info_helper, switch, table_name, action_name, ecmp_group_id, ecmp_hash,
                                  dst_eth_addr, port)

        connected_switches.append(switch)

    except KeyboardInterrupt:
        print(" Shutting down.")
    except grpc.RpcError as e:
        printGrpcError(e)


def connect_switches_to_controller():
    parser = argparse.ArgumentParser(description='P4Runtime Controller')
    parser.add_argument('--p4info', help='p4info proto in text format from p4c',
                        type=str, action="store", required=False,
                        default='build/ibn.p4.p4info.txt')
    parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c',
                        type=str, action="store", required=False,
                        default='build/ibn.json')
    parser.add_argument('-e', '--env',
                        help='Set the environment',
                        action="store", required=False)
    args = parser.parse_args()

    # p4info_value = args.p4info

    if not os.path.exists(args.p4info):
        parser.print_help()
        print("\np4info file not found: %s\nHave you run 'make'?" % args.p4info)
        parser.exit(1)
    if not os.path.exists(args.bmv2_json):
        parser.print_help()
        print("\nBMv2 JSON file not found: %s\nHave you run 'make'?" % args.bmv2_json)
        parser.exit(1)

    for switch_id in range(1, NUMBER_SWITCHES + 1):
        define_connection(args.bmv2_json, switch_id)
        # readTableRules(p4info_helper, connected_switches[switch_id-1])

    # = helper.P4InfoHelper(args.p4info)


def bitstring_to_ip(bitstring):
    ip_address = struct.unpack("!BBBB", bitstring)
    ip_address_str = ".".join(map(str, ip_address))
    return ip_address_str


def bitstring_to_decimal(bitstring):
    decimal_value = 0
    for digit in bitstring:
        decimal_value = decimal_value * 256 + digit
    return decimal_value


def printDigests(sw, idx, lock):
    lock.acquire()
    print("Start checking digests for s%d" % (sw.device_id + 1))
    ready[idx] = True
    lock.release()

    # TODO this is hardcoded and retrieved from the build/file.txt folder
    DIGEST_ID = 391276020

    digest_entry = p4info_helper.BuildDigestEntry(digest_id=DIGEST_ID)
    sw.SendDigestEntry(digest_entry)
    srcAddr, size, arrivalTime = None, None, None
    while True:
        for msgs in sw.StreamDigestMessages(digest_id=DIGEST_ID):
            for members in msgs.data:
                if members.WhichOneof('data') == 'struct':
                    if members.struct.members[0].WhichOneof('data') == 'bitstring':
                        x = members.struct.members[0].bitstring
                        srcAddr = bitstring_to_ip(x)
                        print(srcAddr)
                    if members.struct.members[1].WhichOneof('data') == 'bitstring':
                        size = int.from_bytes(members.struct.members[1].bitstring, byteorder='big')
                        print(size)
                    if members.struct.members[2].WhichOneof('data') == 'bitstring':
                        arrivalTime = bitstring_to_decimal(members.struct.members[2].bitstring)
                        print(arrivalTime)
                    digest_queue.put([srcAddr, size, arrivalTime])
                    return


def getP4RuntimeConnection(switch_id):
    return connected_switches[switch_id]


def get_from_digest(switch_id):
    ready[switch_id] = False
    lock = threading.Lock()
    sw = connected_switches[switch_id]
    t = threading.Thread(target=printDigests, args=(sw, switch_id, lock))
    t.start()

    #CHECK
    while True:
        lock.acquire()
        result = True
        for state in ready:
            result = result and state
        if result:
            lock.release()
            break
        else:
            lock.release()
    
    return_digest = digest_queue.get()
    return return_digest


connect_switches_to_controller()

# p4info_helper = connect_switches_to_controller()
'''
while 1:
    time.sleep(5)
    printCounter(p4info_helper,1, "most_used_port_per_switch")
'''
