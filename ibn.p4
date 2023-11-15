/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

//My includes
#include "include/headers.p4"
#include "include/parsers.p4"

#define REGISTER_SIZE 8192
#define TIMESTAMP_WIDTH 48
#define ID_WIDTH 16
#define NUMPACKETS_WIDTH 32

#define DROPPED_MAX 10
#define DROPPING_TIMEOUT 48w200000

#define IPV4_LPM_TABLE_SIZE 1024
#define IPV4_FORWARD_TABLE_SIZE 512
#define IPV6_LPM_TABLE_SIZE 1024
#define SEND_FRAME_TABLE_SIZE 256
#define PACKET_THRESHOLD 700


/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}

/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    counter(MAX_TUNNEL_ID, CounterType.packets_and_bytes) most_used_port_per_switch;
    //counter(MAX_TUNNEL_ID, CounterType.packets_and_bytes) dst_group;

 
    action drop() {
        mark_to_drop(standard_metadata);
    }



    action ecmp_groupA(bit<14> ecmp_group_id, bit<16> num_nhops){
        hash(meta.ecmp_hash,
        HashAlgorithm.crc16,
        (bit<1>)0,
        { hdr.ipv4.srcAddr,
            hdr.ipv4.dstAddr,
            hdr.tcp.srcPort,
            hdr.tcp.dstPort,
            hdr.ipv4.protocol},
        num_nhops);

        meta.ecmp_group_id = ecmp_group_id;
        //dst_group.count((bit<14>) ecmp_group_id);
    }


    action set_nhopA(macAddr_t dstAddr, egressSpec_t port) { //questo cambiera'


        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;

       //set the destination mac address that we got from the match in the table
        hdr.ethernet.dstAddr = dstAddr;

        //set the output port that we also get from the table
        standard_metadata.egress_spec = port;
        
        //decrease ttl by 1
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;

        most_used_port_per_switch.count((bit<32>) port);
    }


    table ecmp_group_to_nhopA {
        key = {
            meta.ecmp_group_id:    exact;
            meta.ecmp_hash: exact;
        }
        actions = {
            drop;
            set_nhopA;
        }
        size = 1024;
    }

    table ipv4_lpmA {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            set_nhopA;
            ecmp_groupA;
            drop;
        }
        size = 1024;
        default_action = drop;
    }

    table drop_table{
        actions = {
            drop;
        }
        size = 1;
        default_action = drop();
    }

    action nhop_dest(egressSpec_t port){
        standard_metadata.egress_spec = port;
    }

    table next_hop_forwarding{
        actions = {
            nhop_dest;
        }
        size = 1024;
    }

    apply {

        if (hdr.ipv4.isValid()){

            //next_hop_forwarding.apply();
         
            switch (ipv4_lpmA.apply().action_run){
                ecmp_groupA:{
                    ecmp_group_to_nhopA.apply();
                }
            }



        digest<to_digest>(1, {hdr.ipv4.dstAddr, standard_metadata.packet_length, standard_metadata.ingress_global_timestamp});


        }
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {

 apply{

 }
}


/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers hdr, inout metadata meta) {
     apply {
	update_checksum(
	    hdr.ipv4.isValid(),
            { hdr.ipv4.version,
	          hdr.ipv4.ihl,
              hdr.ipv4.dscp,
              hdr.ipv4.ecn,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
              hdr.ipv4.hdrChecksum,
              HashAlgorithm.csum16);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

//switch architecture
V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
