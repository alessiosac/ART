import argparse

import gymnasium as gym
import sys
from stable_baselines3 import DQN
from net_env.envs import net_env
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.env_util import make_vec_env


from net_env.envs import net_env

parser = argparse.ArgumentParser(description='RL environment')
parser.add_argument('-e', '--env',
                    help='Set the environment',
                    action="store", required=True)
args = parser.parse_args()

env = gym.make(args.env)

switch_id = (args.env).split("-")[1]

#check_env(env, warn=True)

model = DQN("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=10000)
model.save("Model_saved_for_s%s" % switch_id)
#vec_env = model.get_env()
#obs, info = env.reset()


