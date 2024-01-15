import argparse

import numpy as np
from matplotlib import pyplot as plt
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from stable_baselines3 import DQN
import gymnasium as gym
from sklearn.metrics import accuracy_score
from net_env2.envs import net_env
from sklearn import tree
import pickle


def generate_dataset(dqn_model, env, num_samples=100000):
    states = []
    actions = []
    i = 0

    for _ in range(num_samples):
        state, info = env.reset()
        done = False

        while not done:
            action, _ = dqn_model.predict(state, deterministic=True)

            next_state, _, done, _, _ = env.step(action)

            flat_state = np.asarray(state).flatten()
            flat_state = flat_state.astype(np.float64)

            states.append(flat_state[0] + flat_state[0])
            actions.append(action)

            state = next_state

        print("SONO AL SAMPLE NUMERO ", i)
        i = i + 1

    return np.array(states), np.array(actions)


parser = argparse.ArgumentParser(description='DT environment')
parser.add_argument('-e', '--env',
                    help='Set the environment',
                    action="store", required=True)
parser.add_argument('-load', '--load_trained',
                    help='Load the previously trained DQN model',
                    action="store", required=True)
args = parser.parse_args()

env = gym.make(args.env)

switch_id = (args.env).split("-")[1]

dqn_model = DQN.load(args.load_trained)

print("Building the DT")
states, actions = generate_dataset(dqn_model, env)
#states = np.array([np.asarray(state, dtype=np.int64) for state in states])

np.savetxt("/media/sf_Shared/X_s%s" % switch_id, states, fmt="%d")

np.savetxt("/media/sf_Shared/y_s%s" % switch_id, actions, fmt="%d")

feature_labels = np.random.randint(0, 3, size=len(states))

X_train, X_test, y_train, y_test = train_test_split(states, actions, test_size=0.2, random_state=42)
# DT training
decision_tree = DecisionTreeClassifier()
decision_tree.fit(X_train, y_train)

with open("/media/sf_Shared/Trained_DT_s%s" % switch_id, "wb") as file:
    pickle.dump(decision_tree, file)

y_prec = decision_tree.predict(X_test)

accuracy = accuracy_score(y_test, y_prec)

print("Accuracy on the same test %d" % accuracy)

print("Decision tree correctly created for s%s" % switch_id)


fig = plt.figure(figsize=(25,20))
_ = tree.plot_tree(decision_tree,
                   feature_names=["dstAddr", "size", "latency"],
                   class_names=[0, 1, 2, 3, 4, 5],
                   filled=True,
                   max_depth=2)

fig.savefig("/media/sf_Shared/decistion_tree%s.png" % switch_id)
