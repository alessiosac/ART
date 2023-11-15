#ifndef _HEADERS_BPP_P4_
#define _HEADERS_BPP_P4_

/*
 *  BPP HEADER
 */

typedef bit<8> bppNextHeader_t;

const bppNextHeader_t BPP_ICMP = 0x01;
const bppNextHeader_t BPP_COMMAND = 0xf0;
const bppNextHeader_t BPP_METADATA = 0xff;

const bit<16> BPP_PARAMETER_CATEGORY_METADATA = 0x0001;
const bit<16> BPP_PARAMETER_CATEGORY_STATELET = 0x0002;
const bit<16> BPP_PARAMETER_CATEGORY_BUILTIN = 0x0003;

const bit<8> BPP_ACTION_SUM = 0x01;
const bit<8> BPP_ACTION_PUT = 0x02;
const bit<8> BPP_ACTION_DROP = 0xff;

const bit<16> BPP_CONDITION_AND = 0x0001;
const bit<16> BPP_CONDITION_OR = 0x0002;
const bit<8> BPP_CONDITION_NOT = 0x01;
const bit<8> BPP_CONDITION_EQUAL = 0x01;
const bit<8> BPP_CONDITION_INFERIOR = 0x02;
const bit<8> BPP_CONDITION_SUPERIOR = 0x03;

header bppMetadata_t {
    bit<64>          id;
    bit<64>         data1;
    bit<64>         data2;
    bit<64>         data3;
    bit<64>         data4;
    bit<64>         data5;
    bit<64>         data6;
    bit<64>         data7;
    bit<64>         data8;
    bit<64>         data9;
    bit<64>         data10;
    bit<24>         empty;
    bit<8>          next;
}

header bppHeader_t {
    bit<4>          version;
    bit<16>         length;
    bit<4>          errorAction;
    bit<2>          priorErrors;
    bit<2>          v;
    bit<2>          tFlag;
    bit<2>          rsrvd;
    bit<8>          metadataOffset;
    bit<16>         checksum;
    bit<8>          next;
}

header bppCommand_t {
    // Command header
    bit<16>         length;
    bit<8>          serialized;

    // Condition set
    bit<16>         conditionLength;
    bit<16>         conditionType;

    // Condition 1
    bit<8>          c1Length;
    bit<8>          c1Negation;
    bit<8>          c1Flags;
    bit<8>          c1Type;

    // Condition 1 Param 1
    bit<16>         c1p1Category;
    bit<16>         c1p1Length;
    bit<32>         c1p1Value;

    // Condition 1 Param 2
    bit<16>         c1p2Category;
    bit<16>         c1p2Length;
    bit<32>         c1p2Value;

    // Condition 2
    bit<8>          c2Length;
    bit<8>          c2Negation;
    bit<8>          c2Flags;
    bit<8>          c2Type;

    // Condition 2 Param 1
    bit<16>         c2p1Category;
    bit<16>         c2p1Length;
    bit<32>         c2p1Value;

    // Condition 2 Param 2
    bit<16>         c2p2Category;
    bit<16>         c2p2Length;
    bit<32>         c2p2Value;

    // Action set
    bit<32>         actionLength;

    // Action 1
    bit<8>          a1Length;
    bit<8>          a1Serialized;
    bit<8>          a1Flags;
    bit<8>          a1Type;

    // Action 1 Param 1
    bit<16>         a1p1Category;
    bit<16>         a1p1Length;
    bit<32>         a1p1Value;

    // Action 1 Param 2
    bit<16>         a1p2Category;
    bit<16>         a1p2Length;
    bit<32>         a1p2Value;

    // Action 2
    bit<8>          a2Length;
    bit<8>          a2Serialized;
    bit<8>          a2Flags;
    bit<8>          a2Type;

    // Action 2 Param 1
    bit<16>         a2p1Category;
    bit<16>         a2p1Length;
    bit<32>         a2p1Value;

    // Action 2 Param 2
    bit<16>         a2p2Category;
    bit<16>         a2p2Length;
    bit<32>         a2p2Value;

    // Next header
    bit<8>          next;
}

struct bppBlock_t {
    bppHeader_t             hdr;
    bppCommand_t[8]         cmd;
}

#endif