/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

//Type definitions
typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;
typedef bit<48> time_t;
typedef bit<8> util_t;
typedef bit<80> cpu_type_reg_t;
typedef bit<14> SFW_reg_type;

typedef bit<32> port_id_t;

//Regular constants
const bit<16> TYPE_IPV4 = 0x800;

const port_id_t numm_port = 1;
const time_t FLOWLET_TOUT = 48w1 << 3;

const bit<32> MAX_TUNNEL_ID = 1 << 16;

//Regular headers
header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<6>    dscp;
    bit<2>    ecn;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

header tcp_t{
    bit<16> srcPort;
    bit<16> dstPort;
    bit<32> seqNo;
    bit<32> ackNo;
    bit<4>  dataOffset;
    bit<4>  res;
    bit<1>  cwr;
    bit<1>  ece;
    bit<1>  urg;
    bit<1>  ack;
    bit<1>  psh;
    bit<1>  rst;
    bit<1>  syn;
    bit<1>  fin;
    bit<16> window;
    bit<16> checksum;
    bit<16> urgentPtr;
}

struct to_digest{
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
    bit<32> packet_length;
    bit<48> timestamp;
}


struct metadata {
    bit<14> ecmp_hash;
    bit<14> ecmp_group_id;

    bit<32> register_cell_one;
    bit<32> register_cell_two;

    bit<32> register_position_one;
    bit<32> register_position_two;

    bit<48> flowlet_last_stamp;
    bit<48> flowlet_time_diff;
    bit<32> flowlet_num_packets;
    bit<48> dropped_time_diff;

    bit<32> output_hash_one;
    bit<32> output_hash_two;

    bit<32> counter_one;
    bit<32> counter_two;

    bit<13> flowlet_register_index;
    bit<16> flowlet_id;

    bit<2> router_status;
}

struct headers {
    ethernet_t   ethernet;
    ipv4_t       ipv4;
    tcp_t        tcp;
}
