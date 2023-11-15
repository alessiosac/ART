#!/usr/bin/env python3
import argparse
import os
import sys
from time import sleep

import grpc

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../utils/'))

import p4runtime_lib.bmv2
import p4runtime_lib.helper
from p4runtime_lib.switch import ShutdownAllSwitchConnections

subnet_identification = {"1": ("10.0.1.1", "10.0.1.4"), "6": ("10.0.6.2", "10.0.6.5"), "7": ("10.0.7.3", "10.0.7.6"),
                         "8": ("10.0.8.7", "10.0.8.8"), "9": ("10.0.9.9", "10.0.9.10")}
num_of_host_per_subnet = 2


def ipv4_lpm_add(p4info_helper, ingress_sw, table_name, action_name, dst_ip_addr, splitted):
    print("debug:  " + table_name + " " + action_name + " " + dst_ip_addr + " ")
    if action_name == "set_nhop" or action_name == "set_nhopA":
        dst_eth_addr = splitted[5]
        port = int(splitted[6].split("\n")[0])
        # print("%s %d" % (dst_eth_addr, port))
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


def SFW_id_group(p4info_helper, ingress_sw, table_name, action_name, src_ip_addr, ecmp_group_id):
    subnet = src_ip_addr.split(".")[2]  # 10.0.6.2 -> 6
    subnet_in_dic = subnet_identification[subnet]  # 6 -> 10.0.6.2 e 10.0.6.5
    for x in range(0, num_of_host_per_subnet):
        ip_addr = subnet_in_dic[x]
        table_entry = p4info_helper.buildTableEntry(
            table_name="MyIngress." + table_name,
            match_fields={
                "hdr.ipv4.srcAddr": (ip_addr, 32)
            },
            action_name="MyIngress." + action_name,
            action_params={
                "ecmp_group_id": ecmp_group_id,
            })
        ingress_sw.WriteTableEntry(table_entry)


def portIdentifier(p4info_helper, ingress_sw, table_name, action_name, dst_ip_addr, port):
    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress." + table_name,
        match_fields={
            "hdr.ipv4.dstAddr": (dst_ip_addr, 32)
        },
        action_name="MyIngress." + action_name,
        action_params={
            "port": port,
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


def printCounter(p4info_helper, sw, counter_name, index):
    """
    Reads the specified counter at the specified index from the switch. If the index is 0, it will return all
    values from the counter.

    :param p4info_helper: the P4Info helper
    :param sw:  the switch connection
    :param counter_name: the name of the counter from the P4 program
    :param index: the interested index you want to read of the counter
    """
    counter_id = p4info_helper.get_counters_id(counter_name)

    for response in sw.ReadCounters(counter_id, index):
        for entity in response.entities:
            counter = entity.counter_entry
            print("%s %s %d: %d packets (%d bytes)" % (
                sw.name, counter_name, index,
                counter.data.packet_count, counter.data.byte_count
            ))


def printGrpcError(e):
    print("gRPC Error:", e.details(), end=' ')
    status_code = e.code()
    print("(%s)" % status_code.name, end=' ')
    traceback = sys.exc_info()[2]
    print("[%s:%d]" % (traceback.tb_frame.f_code.co_filename, traceback.tb_lineno))


def getCounterValue(p4info_helper, switch, counter_name):
    counter_id = p4info_helper.get_counters_id(counter_name)
    index = 0 #gets at index 0
    for response in switch.ReadCounters(counter_id, index):
        for entity in response.entities:
            counter = entity.counter_entry
            print("%s %s %d: %d packets (%d bytes)" % (
                switch.name, counter_name, index,
                counter.data.packet_count, counter.data.byte_count
            ))


def connection(p4info_file_path, bmv2_file_path, switch_id):
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)

    try:
        # Create a switch connection object for s1 and s2;
        # this is backed by a P4Runtime gRPC connection.
        # Also, dump all P4Runtime messages sent to switch to given txt files.
        switch = p4runtime_lib.bmv2.Bmv2SwitchConnection(
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

        counter_name = "MyIngress.accettati"
        counter_value = getCounterValue(p4info_helper, switch, counter_name)

        print("Installed P4 Program using SetForwardingPipelineConfig on interested switch")

        ## Write the rules that tunnel traffic from h1 to h2
        with open("s" + str(switch_id) + "-commands.txt") as file:
            lines = file.readlines()
            for line in lines:
                splitted = line.split(" ")
                command = splitted[0]
                if command == "\n":
                    continue
                table_name = splitted[1]
                if command == "table_add":
                    if table_name == "ipv4_lpm" or table_name == "ipv4_lpmA":
                        action_name = splitted[2]
                        dst_ip_addr = splitted[3]
                        dst_ip_addr = dst_ip_addr.split("/")[0]
                        ipv4_lpm_add(p4info_helper, switch, table_name, action_name, dst_ip_addr, splitted)
                    elif table_name == "SFW_identification_group":
                        action_name = splitted[2]
                        src_ip_addr = splitted[3].split("/")[0]
                        ecmp_group_id = int(splitted[5].split("\n")[0])
                        # print("debug: %s %s %s %d" % (table_name, action_name, src_ip_addr, ecmp_group_id))
                        SFW_id_group(p4info_helper, switch, table_name, action_name, src_ip_addr, ecmp_group_id)
                    elif table_name == "portIdentifier":
                        action_name = splitted[2]
                        dst_ip_addr = splitted[3].split("/")[0]
                        port = int(splitted[5].split("\n")[0])
                        # print("debug: %s %s %s %d" % (table_name, action_name, dst_ip_addr, port))
                        portIdentifier(p4info_helper, switch, table_name, action_name, dst_ip_addr, port)
                    elif table_name == "ecmp_group_to_nhop" or table_name == "ecmp_group_to_nhopA":
                        action_name = splitted[2]
                        ecmp_group_id = int(splitted[3])
                        ecmp_hash = int(splitted[4])
                        dst_eth_addr = splitted[6]
                        port = int(splitted[7].split("\n")[0])
                        # print("debug: %s %s %d %d %s %d  " % (table_name, action_name, ecmp_group_id, ecmp_hash, dst_eth_addr, port))
                        group_add(p4info_helper, switch, table_name, action_name, ecmp_group_id, ecmp_hash,
                                  dst_eth_addr, port)

        # readTableRules(p4info_helper, switch)
        # readTableRules(p4info_helper, s2)

        # Print the tunnel counters every 2 seconds
        while True:
            sleep(2)
            print('\n----- Reading tunnel counters -----')
            # TODO
            printCounter(p4info_helper, switch, "MyIngress.accettati", 0)
            # printCounter(p4info_helper, s2, "MyIngress.egressTunnelCounter", 100)
            # printCounter(p4info_helper, s2, "MyIngress.ingressTunnelCounter", 200)
            # printCounter(p4info_helper, s1, "MyIngress.egressTunnelCounter", 200)

    except KeyboardInterrupt:
        print(" Shutting down.")
    except grpc.RpcError as e:
        printGrpcError(e)

    ShutdownAllSwitchConnections()


def conf_connection(switch_id):
    parser = argparse.ArgumentParser(description='P4Runtime Controller')
    parser.add_argument('--p4info', help='p4info proto in text format from p4c',
                        type=str, action="store", required=False,
                        default='build/ibn.p4.p4info.txt')
    parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c',
                        type=str, action="store", required=False,
                        default='build/ibn.json')
    args = parser.parse_args()

    if not os.path.exists(args.p4info):
        parser.print_help()
        print("\np4info file not found: %s\nHave you run 'make'?" % args.p4info)
        parser.exit(1)
    if not os.path.exists(args.bmv2_json):
        parser.print_help()
        print("\nBMv2 JSON file not found: %s\nHave you run 'make'?" % args.bmv2_json)
        parser.exit(1)

    connection(args.p4info, args.bmv2_json, switch_id)


def read_stat(switch_id=0):
    conf_connection(switch_id)

    return


if __name__ == '__main__':
    stat()
