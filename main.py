from multiprocessing import Process, Manager
import argparse

import numpy as np
from stable_baselines3 import DQN, A2C, PPO
from net_env2.envs.net_env2 import PortForwardingEnvironment
import gymnasium as gym
import mmap
from ctypes import c_float
import os
import time
from multiprocessing import Process, Manager

def s1(h1_h2, h2_h1, h1_h3, h1_h7, h1_h9):

    #env = gym.make("net_env2:net-v1", "switch_id:" "s9", src_dst_dict)
    env = PortForwardingEnvironment("s1", h1_h2, h2_h1, h1_h3, h1_h7, h1_h9)

    model = DQN("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=3000)
    model.save("Model_saved_for_s1")

def s6(h1_h2, h2_h1, h1_h3, h1_h7, h1_h9):
    env = PortForwardingEnvironment("s6", h1_h2, h2_h1, h1_h3, h1_h7, h1_h9)

    model = DQN("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=3000)
    model.save("Model_saved_for_s6")

def s7(h1_h2, h2_h1, h1_h3, h1_h7, h1_h9):

    #env = gym.make("net_env2:net-v1", "switch_id:" "s9", src_dst_dict)
    env = PortForwardingEnvironment("s7", h1_h2, h2_h1, h1_h3, h1_h7, h1_h9)

    model = DQN("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=3000)
    model.save("Model_saved_for_s7")

def s8(h1_h2, h2_h1, h1_h3, h1_h7, h1_h9):
    env = PortForwardingEnvironment("s8", h1_h2, h2_h1, h1_h3, h1_h7, h1_h9)

    model = DQN("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=3000)
    model.save("Model_saved_for_s8")

def s9(h1_h2, h2_h1, h1_h3, h1_h7, h1_h9):
    env = PortForwardingEnvironment("s9", h1_h2, h2_h1, h1_h3, h1_h7, h1_h9)

    model = DQN("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=3000)
    model.save("Model_saved_for_s9")

if __name__ == '__main__':
    manager = Manager()
    #src_dst_dict = manager.dict()
    h1_h2 = manager.Value(c_float, 0.0)
    h2_h1 = manager.Value(c_float, 0.0)
    h1_h3 = manager.Value(c_float, 0.0)
    h1_h7 = manager.Value(c_float, 0.0)
    h1_h9 = manager.Value(c_float, 0.0)
    p1 = Process(target=s1, args=(h1_h2, h2_h1, h1_h3, h1_h7, h1_h9, ))
    p6 = Process(target=s6, args=(h1_h2, h2_h1, h1_h3, h1_h7, h1_h9, ))
    p7 = Process(target=s7, args=(h1_h2, h2_h1, h1_h3, h1_h7, h1_h9, ))
    p8 = Process(target=s8, args=(h1_h2, h2_h1, h1_h3, h1_h7, h1_h9, ))
    p9 = Process(target=s9, args=(h1_h2, h2_h1, h1_h3, h1_h7, h1_h9, ))

    p1.start()
    p6.start()
    p7.start()
    p8.start()
    p9.start()

    p1.join()
    p6.join()
    p7.join()
    p8.join()
    p9.join()