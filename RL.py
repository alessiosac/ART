import argparse

import gymnasium as gym
import sys
from stable_baselines3 import DQN

from net_env.envs import net_env

parser = argparse.ArgumentParser(description='RL environment')
parser.add_argument('-e', '--env',
                    help='Set the environment',
                    action="store", required=True)
args = parser.parse_args()

env = gym.make(args.env)

model = DQN("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=10000)

vec_env = model.get_env()
obs = vec_env.reset()
