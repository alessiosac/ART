import mmap
import os
import random
import time

import gymnasium
import numpy as np

import P4Runtime

dst_dict = {"10.0.1.1": 1, "10.0.1.4": 4, "10.0.6.2": 2, "10.0.6.5": 5, "10.0.7.3": 3, "10.0.7.6": 6,
            "10.0.8.7": 7, "10.0.8.8": 8, "10.0.9.9": 9, "10.0.9.10": 10}

ts = 0
class CurrentPacket:
    def __init__(self, dst=0, size=0, latency=0.0):
        self.dst = dst
        self.size = size
        self.latency = latency

    def getdst(self):
        return self.dst

    def getsize(self):
        return self.size

    def getlatency(self):
        return self.latency


class PortForwardingEnvironment(gymnasium.Env):
    def __init__(self, switch_id, h1_h2, h2_h1, h1_h3, h1_h7, h1_h9):
        self.num_ports = 4
        self.ts = 0
        self.current_packet = CurrentPacket()
        self.port_capacity = np.full(self.num_ports, 100000) #link hanno capacita' di 100Mbps, quindi 100000Kbps
        self.port_utilization = np.zeros(self.num_ports)
        self.h1_h2 = h1_h2
        self.h2_h1 = h2_h1
        self.h1_h3 = h1_h3
        self.h1_h7 = h1_h7
        self.h1_h9 = h1_h9

        self.id = switch_id  # per esempio s9
        self.id_num = int(self.id.split("s")[1])  # cosi da avere il 9
        self.connection_to_controller = P4Runtime.getP4RuntimeConnection(self.id_num)[self.id_num-1]
        time.sleep(3)
        self.firstRun = True
        self.Time_start = time.time()
        self.switch_turning_on_time = [-1 for _ in range(0, 9)]
        self.action_space = gymnasium.spaces.Discrete(self.num_ports)
        '''
        self.observation_space = gymnasium.spaces.Dict({
            "dst": gymnasium.spaces.Discrete(10),
            "size": gymnasium.spaces.Box(low=0, high=2000, shape=(1,), dtype=np.float64),
            "latency": gymnasium.spaces.Box(low=0, high=float('inf'), shape=(1,), dtype=np.float64)})
        '''
        #self.observation_space = gymnasium.spaces.Box(low = 0, high = 3, shape=(3,))
        self.observation_space = gymnasium.spaces.Box(low=np.zeros(4), high=np.full(4, 15000), dtype=np.float64)

    def reset(self, seed=None, options=None):

        return_digest = P4Runtime.get_from_digest(self.id_num, self.switch_turning_on_time, self.h1_h2, self.h2_h1, self.h1_h3, self.h1_h7, self.h1_h9)

        while return_digest[2] is None or return_digest[2] <= 0:
            return_digest = P4Runtime.get_from_digest(self.id_num, self.switch_turning_on_time, self.h1_h2, self.h2_h1, self.h1_h3, self.h1_h7, self.h1_h9)

        value_from_dict = dst_dict.get(return_digest[0])
        dst = int(value_from_dict)
        size = int(return_digest[1])
        latency = int(return_digest[2])

        self.current_packet = CurrentPacket(dst, size, latency)
        #obs = {"dst": dst, "size": size, "latency": latency}
        if self.firstRun:
            self.switch_turning_on_time = P4Runtime.getSwitchesTurningOnTime()
            self.firstRun = False
            return self.port_utilization, {}
        else:
            return self.port_utilization, {}

    def step(self, action):

        done = False
        return_digest = P4Runtime.get_from_digest(self.id_num, self.switch_turning_on_time, self.h1_h2, self.h2_h1, self.h1_h3, self.h1_h7, self.h1_h9)

        while return_digest[2] is None or return_digest[2] <= 0:
            return_digest = P4Runtime.get_from_digest(self.id_num, self.switch_turning_on_time, self.h1_h2, self.h2_h1, self.h1_h3, self.h1_h7, self.h1_h9)

        value_from_dict = dst_dict.get(return_digest[0])
        dst = int(value_from_dict)
        size = int(return_digest[1])
        latency = float(return_digest[2])

        self.current_packet = CurrentPacket(dst, size, latency)

        self.port_utilization[action] += self.current_packet.getsize()

        #target_latency = 4

        latency_reward = float(float(1.0) / float((1.0 + self.current_packet.getlatency())))
        #latency_reward = float(float(1.0) / float((1.0 + float(lat))))
        #print("Action %d" % action)
        utilization_penalty = float(0.2 * self.port_utilization[action] / self.port_capacity[action])

        print("LR: %f\n" % self.current_packet.getlatency())
        print("UP: %f\n" % utilization_penalty)
        #reward = ret_lat(latency_reward, utilization_penalty)

        reward = latency_reward - utilization_penalty

        if time.time() - self.Time_start >= 1:
            self.port_utilization[action] = 0
            self.Time_start = time.time()

        P4Runtime.NextHop(self.id_num, port=(int(action) + 2))

        print("Reward: %f\n" % reward)
        #print("Port_UT: %f" % self.port_utilization[action])
        #print("Port_PC: %f" % self.port_capacity[action])

        filename = ("s%d_reward.txt" % self.id_num)
        with open(filename, "a") as file:
            file.write(str(reward))
            file.write(", ")
        file.close()

        filename = ("s%d_action.txt" % self.id_num)
        with open(filename, "a") as file:
            file.write(str(action))
            file.write(", ")
        file.close()

        filename = ("s%d_Latency_reward.txt" % self.id_num)
        with open(filename, "a") as file:
            file.write(str(latency_reward))
            file.write(", ")
        file.close()

        filename = ("s%d_UP.txt" % self.id_num)
        with open(filename, "a") as file:
            file.write(str(utilization_penalty))
            file.write(", ")
        file.close()

        #self.port_utilization[action] -= self.current_packet.getsize()

        return self.port_utilization, reward, done, False, {}
