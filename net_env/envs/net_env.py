import time

import gymnasium as gym
from gymnasium import spaces
import socket
import struct
import itertools
import collections
import numpy as np
import json
import os

from sklearn.preprocessing import OneHotEncoder

import P4Runtime
import loadtopo as topo
from math import log
import matplotlib.pyplot as plt

# PORT, HOST_IP = 1400, '0.0.0.0'
MAX = 4294967295
AH_LENGTH = 4  # max 5
FD_LENGTH = 4  # max 5
LAMBDA1 = 1
LAMBDA2 = 5  # 0.5
LAMBDA3 = 1
LAMBDA4 = 0.005  # 0.0005
NHOSTS = 10
MAXPORTS = 6
MAXQTIME = 10000
MINQTIME = 0
MINDISTANCE = 1
MAXDISTANCE = 4
PLOT_FREQ = 1000
PLOT_SOIL = 0
MEANSTEP = 250

from collections import defaultdict


dst_dict = {"10.0.1.1": 1, "10.0.1.4": 4, "10.0.6.2": 2, "10.0.6.5": 5, "10.0.7.3": 3, "10.0.7.6": 6,
            "10.0.8.7": 7, "10.0.8.8": 8, "10.0.9.9": 9, "10.0.9.10": 10}


class ValueEncoder:
    def __init__(self):
        self.value_to_id = {}
        self.id_counter = 1  # Start from 1 to avoid conflicts with default value (0)

    def encode_value(self, value):
        if value not in self.value_to_id:
            self.value_to_id[value] = self.id_counter
            self.id_counter += 1
        return self.value_to_id[value]

# Example usage
encoder = ValueEncoder()


def minRw(isBackbone):
    delta1 = 0
    if isBackbone:
        delta3 = 0
        delta4 = 1
    else:
        delta3 = 1
        delta4 = 0
    seconds = MAXQTIME / 1000000
    # seconds = 10
    rw1 = LAMBDA1 * delta1
    rw2 = LAMBDA2 * seconds
    rw3 = LAMBDA3 * delta3
    rw4 = LAMBDA4 * delta4 * MAXDISTANCE
    rw = 0 + rw1 - rw2 - rw3 - rw4
    return rw


def ip2long(ip):
    packedIP = socket.inet_aton(ip)
    return struct.unpack("!L", packedIP)[0]


def maxRw(isBackbone):
    if isBackbone:
        delta1 = 0
        delta4 = 1
    else:
        delta1 = 1
        delta4 = 0
    delta3 = 0
    seconds = MINQTIME / 1000000
    # seconds = 0
    rw1 = LAMBDA1 * delta1
    rw2 = LAMBDA2 * seconds
    rw3 = LAMBDA3 * delta3
    rw4 = LAMBDA4 * delta4 * MINDISTANCE
    rw = 0 + rw1 - rw2 - rw3 - rw4
    return rw


def makeRw(distance, qtime, dropped):
    delta1 = 1
    delta3 = dropped
    if delta3 == 1:
        delta1 = 0
    rw1 = LAMBDA1 * delta1 * (1 / (distance + 1))
    rw2 = LAMBDA2 * (1 / log(qtime + 10, 10))
    rw3 = LAMBDA3 * delta3
    rw = rw1 + rw2 - rw3
    return rw1, rw2, rw3, rw


def makeRw2(distance, qtime):
    if qtime > MAXQTIME:
        qtime = MAXQTIME
    seconds = qtime / 1000000
    rw2 = LAMBDA2 * seconds
    rw4 = LAMBDA4 * distance
    rw = 0 - rw2 - rw4
    return rw2, rw4, rw


def fill(vec, max):
    if (len(vec) < max):
        for i in range(0, max - len(vec)):
            vec.append(0)
        return vec
    else:
        return vec


actionHistory = {}


def addAction(curDst, action):
    if actionHistory.get(curDst) is None:
        actionHistory[curDst] = collections.deque([action], AH_LENGTH)
    else:
        actionHistory[curDst].append(action)


def getActions(curDst):
    if actionHistory.get(curDst) is None:
        return []
    else:
        return actionHistory[curDst]


class FutureDestinations:
    def __init__(self):
        self.curDst = 0
        self.size = 2
        self.dsts = collections.deque(maxlen=FD_LENGTH)

    def pushDst(self, dst):
        self.dsts.append(int(dst))

    def setSize(self, size):
        self.size = int(size)

    def setCurDst(self, dst):
        self.curDst = int(dst)

    def getCurDst(self):
        return self.curDst

    def getDsts(self):
        return self.dsts

    def reset(self):
        self.dsts = []
        self.curDst = 0
        self.size = 0

    def show(self):
        print("Number of future destinations:", len(self.dsts))
        print("Current destination:", self.curDst)
        print("List of future destinations:")
        for dst in self.dsts:
            print(dst)


class State:
    def __init__(self, nfeatures, nports):
        self.destinations = FutureDestinations()
        self.prevActions = []
        self.nfeatures = nfeatures
        self.topology = None
        self.nports = nports

    def setDsts(self, destinations):
        self.destinations = destinations
        self.prevActions = getActions(self.destinations.getCurDst())

    def setTopo(self, topology):
        self.topology = topology

    def getCurDst(self):
        return self.destinations.getCurDst()

    def show(self):
        print("Future destinations: ")
        self.destinations.show()
        print("Previous actions: ", self.prevActions)

    def makeArray(self):
        features = np.full(self.nfeatures, 0)
        list_nhop = np.full(5, 0)
        counter = 0
        try:
            targetHost = self.topology.getNodeByIp(self.destinations.getCurDst())
            index = (counter * NHOSTS) + (int(targetHost[1]) - 1)
            features[index % 5] = 1
            futureDestinations = self.destinations.getDsts()
            for fd in futureDestinations:
                counter += 1
                targetHost = self.topology.getNodeByIp(fd)
                index = (counter * NHOSTS) + (int(targetHost[1]) - 1)
                features[index % 5] = 1
            for i in range(0, FD_LENGTH - len(futureDestinations)):
                counter += 1
            start = (counter * NHOSTS) + NHOSTS
            counter = 0
            hosts = self.topology.getHosts()
            for h in hosts:
                hostname = h.getName()
                if actionHistory.get(hostname) is not None:
                    ah = actionHistory[hostname]
                    for action in ah:
                        action -= 1
                        index = start + ((counter * self.nports) + action)
                        features[index % 5] = 1
                        counter += 1
                start += (MAXPORTS * AH_LENGTH)
                counter = 0
            list_possible_nhop = [] # if different nhop are equal because there is not congestion

            for i in range(0, len(features)):
                if features[i] == 1:
                   list_possible_nhop.append(i)
            print("POSSIBLE N_HOP: %d" % x)
            list_nhop[x - 1] = 1
            return list_nhop
        except:
            return list_nhop
        return features

    def getReward(self, size, latency):
        return size/latency


class Packet:
    def __init__(self, destinations, reward):
        self.futureDestinations = destinations
        self.reward = reward

    def getDsts(self):
        return self.futureDestinations

    def getReward(self):
        return self.reward

    def show(self):
        print("***************************")
        print("Packet:")
        print("Future Destinations:")
        self.futureDestinations.show()
        print("Last reward:", self.reward)
        print("***************************")


def parse_req(return_digest):
    destinations = FutureDestinations()

    destinations.setCurDst(ip2long(return_digest[0]))
    for i in range(0, 2):
        destinations.pushDst(ip2long(return_digest[0]))
    # max = 4 + size
    # for i in range(4, max):
    #    destinations.pushDst(parsed[i])
    latency = return_digest[0][2]
    pkt = Packet(destinations, latency)
    return pkt


class NetEnv(gym.Env):

    def __init__(self, switch_id, port):
        self.nports = 6
        self.id = switch_id  # per esempio s9
        self.id_num = int(self.id.split("s")[1])  # cosi da avere il 9
        # print("initialized with nports =", nports, ", id =", id, ", id_num =", self.id_num)
        # self.P4Runtime_connection = P4Runtime.getP4RuntimeConnection(self.id_num)
        self.action_space = spaces.Discrete(self.nports)
        # self.observation_space = spaces.Box(low = 0, high = MAX, shape=(3, 5))
        self.nfeatures = (AH_LENGTH * MAXPORTS * NHOSTS) + (FD_LENGTH * NHOSTS) + NHOSTS
        # self.nfeatures = 5
        # self.observation_space = spaces.Box(low=np.full(self.nfeatures, 0), high=np.full(self.nfeatures, 1))
        self.observation_space = spaces.Box(low = 0, high = 3, shape=(3,))

        # self.observation_space = spaces.Discrete(self.nports)
        self.state = State(self.nfeatures, self.nports)
        self.pkt = Packet(0, 0)
        self.port = port
        self.firstRun = True
        self.node = None
        self.topology = None
        self.rw1 = []
        self.rw2 = []
        self.rw3 = []
        self.rw4 = []
        self.rw = []
        self.sumrw = 0
        self.meanrw = []
        self.meanrw2 = []
        self.tmpmean = []
        self.tmpmean2 = []
        self.counter = 0
        self.resetvar = False
        # filelog = open(self.id + "_rl_log.txt", "w")
        # filelog.close()
        if self.firstRun:
            self.topology = topo.loadtopology()
            self.state.setTopo(self.topology)
            self.node = self.topology.getNode(id)
            self.firstRun = False
        self.firstTime_Digest = True

        self.connection_to_controller = P4Runtime.getP4RuntimeConnection(self.id_num)
        time.sleep(3)
        self.switch_turning_on_time = P4Runtime.getSwitchesTurningOnTime()

        '''
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            self.s = s
            self.s.bind((HOST_IP, self.port))
            self.s.listen()
            while True:
                print("listening on address " + HOST_IP + ", port " + str(self.port) + "...")
                self.conn, self.addr = self.s.accept()
                #self.conn.settimeout(20)
                print("connected by", self.addr)
                if self.firstRun:
                    self.topology = topo.loadtopology()
                    self.state.setTopo(self.topology)
                    self.node = self.topology.getNode(id)
                    self.firstRun = False
                return
        '''

    def step(self, action):
        global return_digest
        action = action + 1  # because action goes from 0 to N-1, while ports are counted from 1 to N
        info = {}
        # action contains the # of the port the packet must be forwarded to

        # send action back on socket
        # store action in action history
        # ret = action
        addAction(self.state.getCurDst(), action)
        # sendBack = struct.pack('I', ret)
        # self.conn.sendall(sendBack)
        ifname = self.id + "-eth" + str(action)
        interface = self.node.getPort(ifname)
        targetNode = self.topology.getNodeByIp(self.state.getCurDst())
        neighbor = interface.getNeighbor()
        truncated = False
        if neighbor is None:
            nhop = 1  # dst to the host
            return nhop, 1, True, truncated, info
        if "h" in neighbor.getName():
            distance = 0
            if targetNode != neighbor.getName():
                dropped = 1
            else:
                delivered = 1
        else:
            distance = neighbor.getDistance(targetNode)

        # listen on socket
        # as msg arrives store fields in state(t + 1) and reward(t)

        # list_counter = P4Runtime.getCounterValue()
        # self.state.makeNPArray()
        # return_digest = None
        # while return_digest is None:
        # if self.firstTime_Digest:
        #    return_digest = P4Runtime.get_from_digest(self.P4Runtime_connection, self.firstTime_Digest,
        #                                                   int(self.id_num) - 1)
        # self.firstTime_Digest = False
        #i = 0
        return_digest = P4Runtime.get_from_digest(self.id_num, self.switch_turning_on_time)
        self.pkt = parse_req(return_digest)

        if return_digest[2] <= 0 or return_digest[2] is None:
            print("No more data")
            nhop = self.state.makeArray()
            try:
                P4Runtime.NextHop(self.connection_to_controller, nhop)
            except:
                print("P4runtime error")
                pass

            return_array = np.array(return_digest, dtype=np.int64)

            value_from_dict = dst_dict.get(return_array[0])

            return_array[0] = int(value_from_dict)
            return_array[1] = int(return_array[1])
            return_array[2] = int(return_array[2])

            return return_array, self.pkt.getReward(), True, truncated, info

        # check for the "if not data"

        '''
        try:
            data = self.conn.recv(512)
            if not data:
                print("no data")
                return self.state.makeNPArray(), self.pkt.getReward(), True, info
            self.pkt = parse_req(data)
            self.state.setDsts(self.pkt.getDsts())
        except Exception as e:
            print("Exception occured:", e)
            self.conn.close()
            self.s.close()
        '''

        self.state.setDsts(self.pkt.getDsts())
        done = False
        qtime = self.pkt.getReward()
        rw2, rw4, rw = makeRw2(distance, qtime)
        self.rw2.append(rw2)
        self.rw4.append(rw4)
        self.rw.append(rw)
        self.sumrw += rw
        self.counter += 1
        if (self.counter % MEANSTEP) == 0:
            self.tmpmean = []
            self.tmpmean2 = []
        self.tmpmean.append(rw)
        self.tmpmean2.append(rw2)
        self.meanrw.append(sum(self.tmpmean) / len(self.tmpmean))
        self.meanrw2.append(sum(self.tmpmean2) / len(self.tmpmean2))
        '''
        if (self.counter % PLOT_FREQ) == 0 and self.counter >= PLOT_SOIL:
            fig, axs = plt.subplot_mosaic([
                ["upL", "upR"],
                ["midL", "midR"],
                ["low", "low"]
            ], constrained_layout = True)
            plrw1 = axs["upL"]
            plrw2 = axs["upR"]
            plrw3 = axs["midL"]
            plrw4 = axs["midR"]
            plrw = axs["low"]
            plrw1.plot(range(len(self.rw1)), self.rw1)
            plrw1.set_title("rw1 = LAMBDA1 * delta1")
            plrw2.axis(ymin=0, ymax=(MAXQTIME*LAMBDA2 / 1000000))
            plrw2.plot(range(len(self.rw2)), self.rw2)
            plrw2.plot(range(len(self.meanrw2)), self.meanrw2)
            plrw2.set_title("rw2 = LAMBDA2 * seconds")
            plrw3.plot(range(len(self.rw3)), self.rw3)
            plrw3.set_title("rw3 = LAMBDA3 * delta3")
            plrw4.axis(ymin=LAMBDA4*MINDISTANCE, ymax=LAMBDA4*MAXDISTANCE)
            plrw4.plot(range(len(self.rw4)), self.rw4)
            plrw4.set_title("rw4 = LAMBDA4 * delta4 * distance")
            plrw.axis(ymin=minRw(isBackbone), ymax=maxRw(isBackbone))
            plrw.plot(range(len(self.rw)), self.rw)
            plrw.plot(range(len(self.rw)), self.meanrw)
            plrw.set_title("rw = rw1 - rw2 - rw3 - rw4")
            plt.rcParams["figure.figsize"] = (20,10)
            plt.savefig(self.id + "_rw.png", dpi = 300)
            plt.clf()
        '''
        return_array = np.array(return_digest, dtype=np.int64)

        value_from_dict = dst_dict.get(return_array[0])

        return_array[0] = int(value_from_dict)
        return_array[1] = int(return_array[1])
        return_array[2] = int(return_array[2])

        print(self.sumrw / len(self.rw))
        return return_array, rw, True, truncated, info

    def render(self, mode="human", close=False):
        print("render called")

    def reset(self, seed=None, options=None):
        # listen on socket
        # as msg arrives store fields in state, drop reward

        # self.firstTime_Digest = True
        # return_digest = None
        # while return_digest is None:
        '''
            if not self.resetvar:
                if self.firstTime_Digest:
                    return_digest = P4Runtime.get_from_digest(self.P4Runtime_connection, self.firstTime_Digest,
                                                                int(self.id_num) - 1)
                    self.firstTime_Digest = False

                return_digest = P4Runtime.get_from_digest(self.P4Runtime_connection, self.firstTime_Digest,
                                                            int(self.id_num) - 1)

        print(return_digest)
        '''

        global return_digest
        try:
            return_digest = P4Runtime.get_from_digest(self.id_num, self.switch_turning_on_time)
            while return_digest[2] is None or return_digest[2] <= 0:
                return_digest = P4Runtime.get_from_digest(self.id_num, self.switch_turning_on_time)
            pkt = parse_req(return_digest)
            self.state.setDsts(pkt.getDsts())
        except:
            print("Some error. Need to debug")

        # self.resetvar = True

        # x = self.state.makeNPArray()

        # print(x)

        # x = self.state.makeArray()
        # print(x)

        #encoder_id = encoder.encode_value(return_digest[0])

        #return_digest[0] = encoder_id


        value_from_dict = dst_dict.get(return_digest[0])

        #return_array = np.array(return_digest, dtype=np.int64)

        return_array = np.array([0,0,0], dtype=np.int64)

        return_array[0] = int(value_from_dict)
        return_array[1] = int(return_digest[1])
        return_array[2] = int(return_digest[2])

        return return_array, {}

# def variable_to_get(counter):

# def next_destination():
