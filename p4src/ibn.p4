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
#define BLOOM_FILTER_BIT_WIDTH 32
#define BLOOM_FILTER_ENTRIES 4096
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

    register <util_t>((bit<32>)1) HH_reg;     //register for heavy hitter
    util_t HH_reg_tmp;
    register <util_t>((bit<32>)1) LP_reg;     //register for load profiling
    util_t LP_reg_tmp;
    register <util_t>((bit<32>)1) SFW_reg;    //register for stateful firewall
    util_t SFW_reg_tmp;
    register <util_t>((bit<32>)1) TT_reg;     //register for top talkers
    util_t TT_reg_tmp;


    util_t flag = 0; // for LP purposes, check down
    register <util_t>((bit<32>)1) SFW_block_reg; //register to save what traffic to block
    util_t SFW_block_reg_tmp;
    register<bit<80>>(1) cpu_SFW_dropped;
    SFW_reg_type identif_group;


    register<bit<BLOOM_FILTER_BIT_WIDTH>>(BLOOM_FILTER_ENTRIES) bloom_filter;


    //LP registers
    register <port_id_t>((bit<32>)1) num_port;
    port_id_t num_port_tmp;
    register <port_id_t>((bit<32>)7) reg_weight;
    register <egressSpec_t>((bit<32>)1) porta12;
    register<port_id_t>((bit<32>) 512) best_hop;
    // Last time a packet from a flowlet was observed.
    register<time_t>((bit<32>) 1024) flowlet_time;
    // The next hop a flow should take.
    register<port_id_t>((bit<32>) 1024) flowlet_hop;

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
        }

        action set_allowed(){

           //Get register position
           hash(meta.register_position_one, HashAlgorithm.crc16, (bit<32>)0, {hdr.ipv4.srcAddr,
                                                              hdr.ipv4.dstAddr,
                                                              hdr.ipv4.protocol},
                                                              (bit<32>)BLOOM_FILTER_ENTRIES);

           hash(meta.register_position_two, HashAlgorithm.crc32, (bit<32>)0, {hdr.ipv4.srcAddr,
                                                              hdr.ipv4.dstAddr,
                                                              hdr.ipv4.protocol},
                                                              (bit<32>)BLOOM_FILTER_ENTRIES);


            //set bloom filter fields
            bloom_filter.write(meta.register_position_one, 1);
            bloom_filter.write(meta.register_position_two, 1);
        }

        action check_if_allowed(){

          hash(meta.register_position_one, HashAlgorithm.crc16, (bit<32>)0, {hdr.ipv4.dstAddr,
                                                            hdr.ipv4.srcAddr,
                                                            hdr.ipv4.protocol},
                                                            (bit<32>)BLOOM_FILTER_ENTRIES);

          hash(meta.register_position_two, HashAlgorithm.crc32, (bit<32>)0, {hdr.ipv4.dstAddr,
                                                            hdr.ipv4.srcAddr,
                                                            hdr.ipv4.protocol},
                                                            (bit<32>)BLOOM_FILTER_ENTRIES);


          /*


            //Get register position
            hash(meta.register_position_one, HashAlgorithm.crc16, (bit<32>)0, {hdr.ipv4.dstAddr,
                                                              hdr.ipv4.srcAddr,
                                                              hdr.tcp.dstPort,
                                                              hdr.tcp.srcPort,
                                                              hdr.ipv4.protocol},
                                                              (bit<32>)BLOOM_FILTER_ENTRIES);

            hash(meta.register_position_two, HashAlgorithm.crc32, (bit<32>)0, {hdr.ipv4.dstAddr,
                                                              hdr.ipv4.srcAddr,
                                                              hdr.tcp.dstPort,
                                                              hdr.tcp.srcPort,
                                                              hdr.ipv4.protocol},
                                                              (bit<32>)BLOOM_FILTER_ENTRIES);

            //Read bloom filter cells to check if there are 1's
            bloom_filter.read(meta.register_cell_one, meta.register_position_one);
            bloom_filter.read(meta.register_cell_two, meta.register_position_two);

            */
        }

        action ecmp_group(bit<14> ecmp_group_id, bit<16> num_nhops){
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
        }


        action _update_bloom_filter(){


           //Get register position

           hash(meta.output_hash_one, HashAlgorithm.crc16, (bit<16>)0, {hdr.ipv4.srcAddr,
                                                              hdr.ipv4.dstAddr,
                                                              hdr.tcp.srcPort,
                                                              hdr.tcp.dstPort,
                                                              hdr.ipv4.protocol},
                                                              (bit<32>)BLOOM_FILTER_ENTRIES);

           hash(meta.output_hash_two, HashAlgorithm.crc32, (bit<16>)0, {hdr.ipv4.srcAddr,
                                                              hdr.ipv4.dstAddr,
                                                              hdr.tcp.srcPort,
                                                              hdr.tcp.dstPort,
                                                              hdr.ipv4.protocol},
                                                              (bit<32>)BLOOM_FILTER_ENTRIES);

           hash(meta.output_hash_two, HashAlgorithm.crc32, (bit<16>)0, {hdr.ipv4.srcAddr,
                                                              hdr.ipv4.dstAddr,
                                                              hdr.tcp.srcPort,
                                                              hdr.tcp.dstPort,
                                                              hdr.ipv4.protocol},
                                                              (bit<32>)BLOOM_FILTER_ENTRIES);

           hash(meta.output_hash_two, HashAlgorithm.crc32, (bit<16>)0, {hdr.ipv4.srcAddr,
                                                              hdr.ipv4.dstAddr,
                                                              hdr.tcp.srcPort,
                                                              hdr.tcp.dstPort,
                                                              hdr.ipv4.protocol},
                                                              (bit<32>)BLOOM_FILTER_ENTRIES);



            //Read counters
            bloom_filter.read(meta.counter_one, meta.output_hash_one);
            bloom_filter.read(meta.counter_two, meta.output_hash_two);

            meta.counter_one = meta.counter_one + 1;
            meta.counter_two = meta.counter_two + 1;

            //write counters

            bloom_filter.write(meta.output_hash_one, meta.counter_one);
            bloom_filter.write(meta.output_hash_two, meta.counter_two);


      }


    action set_nhop(macAddr_t dstAddr, egressSpec_t port) { //questo cambiera'

        //CALCOLO DI WEIGHTED RANDOM CHOICE
        bit<32> sum_of_weight = 0;

        num_port.read(num_port_tmp, 0);

        port_id_t sum_tmp;
        reg_weight.read(sum_tmp, 1);
        sum_of_weight = sum_of_weight + sum_tmp;
        reg_weight.read(sum_tmp, 2);
        sum_of_weight = sum_of_weight + sum_tmp;
        reg_weight.read(sum_tmp, 3);
        sum_of_weight = sum_of_weight + sum_tmp;
        reg_weight.read(sum_tmp, 4);
        sum_of_weight = sum_of_weight + sum_tmp;
        reg_weight.read(sum_tmp, 5);
        sum_of_weight = sum_of_weight + sum_tmp;
        reg_weight.read(sum_tmp, 6);
        sum_of_weight = sum_of_weight + sum_tmp;

        port_id_t rand_val;
        random(rand_val, 1, sum_of_weight); //forse sum_of_weight+1

        port_id_t weight_tmp_1;
        port_id_t weight_tmp_2;
        port_id_t weight_tmp_3;
        port_id_t weight_tmp_4;
        port_id_t weight_tmp_5;
        port_id_t weight_tmp_6;
        egressSpec_t chosen_port = 0;

        reg_weight.read(weight_tmp_1, 1);
        reg_weight.read(weight_tmp_2, 2);
        reg_weight.read(weight_tmp_3, 3);
        reg_weight.read(weight_tmp_4, 4);
        reg_weight.read(weight_tmp_5, 5);
        reg_weight.read(weight_tmp_6, 6);

        /*

        time_t curr_time = standard_metadata.ingress_global_timestamp;

        bit<32> flow_hash;
        time_t flow_t;
        port_id_t flow_h;
        port_id_t best_h;

        hash(flow_hash, HashAlgorithm.csum16, 32w0, {
            hdr.ipv4.srcAddr,
            hdr.ipv4.dstAddr,
            hdr.ipv4.protocol,
            hdr.tcp.srcPort,
            hdr.tcp.dstPort
        }, 32w1 << 10 - 1);

        flowlet_time.read(flow_t, flow_hash);

        best_hop.read(best_h, meta.dst);
        port_id_t tmp;
        flowlet_hop.read(tmp, flow_hash);
        tmp = (curr_time - flow_t > FLOWLET_TOUT) ? best_h : tmp;
        flowlet_hop.write(flow_hash, tmp);

        flowlet_hop.read(flow_h, flow_hash);
        standard_metadata.egress_spec = flow_h;
        flowlet_time.write(flow_hash, curr_time);
        */
        if (num_port_tmp > 4){ //higher switches
/*
        if (rand_val < weight_tmp_1){
            chosen_port = 1;
        }else{
            rand_val = rand_val - 1;
            if (rand_val < weight_tmp_2){
                chosen_port = 2;
            }else{
                rand_val = rand_val - 2;
                if (rand_val < weight_tmp_3){
                    chosen_port = 3;
                }else{
                    rand_val = rand_val - 3;
                    if (rand_val < weight_tmp_4){
                        chosen_port = 4;
                    }else{
                        rand_val = rand_val - 4;
                        if (rand_val < weight_tmp_5){
                            chosen_port = 5;
                        }
                    }
                }
            }
        }*/
    }else{ //lower switches
        if(port != 1 || port != 2){
            if (rand_val < weight_tmp_3){
                chosen_port = 3;
            }else{
                rand_val = rand_val - weight_tmp_3;
                if (rand_val < weight_tmp_4){
                    chosen_port = 4;
                }else{
                    rand_val = rand_val - weight_tmp_4;
                    if (rand_val < weight_tmp_5){
                        chosen_port = 5;
                    }else{
                        rand_val = rand_val - weight_tmp_5;
                        if (rand_val <= weight_tmp_6){
                            chosen_port = 6;
                        }
                    }
                }
            }
        }
    }


        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;

       //set the destination mac address that we got from the match in the table
        hdr.ethernet.dstAddr = dstAddr;

        //set the output port that we also get from the table
        if (num_port_tmp > 4 || port == 1 || port == 2){
            standard_metadata.egress_spec = port;
        }else{
            standard_metadata.egress_spec = chosen_port;
        }
        //decrease ttl by 1
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    action set_nhopA(macAddr_t dstAddr, egressSpec_t port) { //questo cambiera'


        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;

       //set the destination mac address that we got from the match in the table
        hdr.ethernet.dstAddr = dstAddr;

        //set the output port that we also get from the table
        standard_metadata.egress_spec = port;
        //decrease ttl by 1
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    action SFW_group_find(bit<14> ecmp_group_id){
        identif_group = ecmp_group_id;
    }

    table SFW_identification_group {
        key = {
            hdr.ipv4.srcAddr: lpm;
        }
        actions = {
            SFW_group_find;
        }
        size = 1024;
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

        table ecmp_group_to_nhop {
            key = {
                meta.ecmp_group_id:    exact;
                meta.ecmp_hash: exact;
            }
            actions = {
                drop;
                set_nhop;
            }
            size = 1024;
        }

        table update_bloom_filter{

            actions = {
                _update_bloom_filter;
            }
            size = 1;
            default_action = _update_bloom_filter;
        }


    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            set_nhop;
            ecmp_group;
            drop;
        }
        size = 1024;
        default_action = drop;
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

        action portId_func(egressSpec_t port){

            porta12.write(0, port);

        }

        table drop_table{
            actions = {
                drop;
            }
            size = 1;
            default_action = drop();
        }


        table portIdentifier{
            key = {
                hdr.ipv4.dstAddr: lpm;
            }
            actions = {
                portId_func;
            }
        }

register<bit<14>>(1)prova;
    apply {


        num_port.read(num_port_tmp, 0);

        portIdentifier.apply();

        egressSpec_t port;
        porta12.read(port,0);


        LP_reg.read(LP_reg_tmp, 0);

        TT_reg.read(TT_reg_tmp, 0);

        HH_reg.read(HH_reg_tmp, 0);

        SFW_reg.read(SFW_reg_tmp, 0);
        SFW_block_reg.read(SFW_block_reg_tmp, 0); //to identify the group ID




        if (hdr.ipv4.isValid()){

          if (HH_reg_tmp != 0){
            if (hdr.tcp.isValid()){
                update_bloom_filter.apply();
                if ((meta.counter_one > PACKET_THRESHOLD && meta.counter_two > PACKET_THRESHOLD)){
                    drop_table.apply();
                    return;
                }
            }
          }

//          if (TT_reg_tmp != 0){

  //        }

          if (SFW_reg_tmp != 0){
              SFW_identification_group.apply();
              prova.write(0, meta.ecmp_group_id);
            if ((bit<14>)SFW_block_reg_tmp == identif_group){ //if the traffic coming from this group ID is the one to be stopped

              cpu_SFW_dropped.read(hdr.cpu.dropped,0);
              hdr.cpu.dropped = hdr.cpu.dropped + 1;
              cpu_SFW_dropped.write(0, hdr.cpu.dropped);

              drop();
              return;
            }

          }

        if (LP_reg_tmp != 0){
          // load profiling stuff
          porta12.write(0,0);
            if (num_port_tmp <= 4 && port != 1 && port != 2){ //sotto
                flag = 1;
                switch (ipv4_lpm.apply().action_run){
                    ecmp_group: {
                        ecmp_group_to_nhop.apply();
                    }
                }

            }
            //end of load profiling stuff
          }
          if ((flag == 0 && LP_reg_tmp == 0) || port == 1 || port == 2){
              switch (ipv4_lpmA.apply().action_run){
                  ecmp_groupA:{
                      ecmp_group_to_nhopA.apply();
                  }
              }
      }

        }
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {

register<bit<80>>(1) cpu_counter;

 apply{
   // Non-cloned packets have an instance_type of 0, so then we clone them
   // using the mirror ID = 100. That, in combination with the control plane, will
   // select to which port the packet has to be cloned to.
   //if (standard_metadata.instance_type == 0 && hdr.ipv4.tos == ){ //ipv4.tos might need to be modified in the send python version
   if (standard_metadata.instance_type == 0){
       clone(CloneType.E2E,100);
   }
   else if (standard_metadata.instance_type != 0){
       hdr.cpu.setValid();
       hdr.cpu.device_id = 1;
       hdr.cpu.reason = 200;
       cpu_counter.read(hdr.cpu.counter, (bit<32>)0);
       hdr.cpu.counter = hdr.cpu.counter + 1;
       cpu_counter.write((bit<32>)0, hdr.cpu.counter);
       // Disable other headers
       hdr.ethernet.setInvalid();
       hdr.ipv4.setInvalid();
   }
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
