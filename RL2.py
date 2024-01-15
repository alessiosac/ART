import argparse

import numpy as np
from stable_baselines3 import DQN, A2C, PPO
from net_env2.envs import net_env2
import gymnasium as gym
import mmap
import os
import time
import multiprocessing

parser = argparse.ArgumentParser(description='RL environment')
parser.add_argument('-e', '--env',
                    help='Set the environment',
                    action="store", required=True)
args = parser.parse_args()

env = gym.make(args.env)

switch_id = (args.env).split("-")[1]

#check_env(env, warn=True)

model = DQN("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=4000)
model.save("Model_saved_for_s%s" % switch_id)

'''
obs = env.reset()
for _ in range(1000):
    action, _ = model.predict(obs)
    obs, _, done, _, _ = env.step(action)
    if done:
        obs = env.reset()

class QLearningAgent:
    def __init__(self, num_actions):
        self.num_actions = num_actions
        self.q_values = np.zeros(num_actions)

    def choose_action(self, state):
        return np.argmax(self.q_values)

    def update_q_values(self, state, action, reward, next_state, alpha=0.1, gamma=0.9):
        # Q-learning update rule
        next_action = self.choose_action(next_state)
        td_error = reward + gamma * self.q_values[next_action] - self.q_values[action]
        self.q_values[action] += alpha * td_error


# Training the agent
env = PortForwardingEnvironment()
agent = QLearningAgent(num_actions=env.num_ports)

num_episodes = 1000
for episode in range(num_episodes):
    state = env.reset()

    while True:
        action = agent.choose_action(state)
        reward = env.step(action)
        next_state = env.current_packet
        agent.update_q_values(state, action, reward, next_state)

        state = next_state

        if np.sum(env.port_utilization) >= 100:
            break

# Testing the trained agent
test_episodes = 10
total_rewards = 0
for _ in range(test_episodes):
    state = env.reset()

    while True:
        action = agent.choose_action(state)
        reward = env.step(action)
        total_rewards += reward

        state = env.current_packet

        if np.sum(env.port_utilization) >= 100:
            break

average_reward = total_rewards / test_episodes
print("Average Test Reward:", average_reward)

'''
