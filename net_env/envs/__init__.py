from net_env.envs.net_env import NetEnv

from gymnasium.envs.registration import register
register(id = "net-v1", entry_point = "net_env.envs:NetEnv", kwargs = {"switch_id":"s1", "port": 50051})
#register(id = "net-v2", entry_point = "net_env.envs:NetEnv", kwargs = {'nports' : 4, "id":"s2", "port": 50052})
#register(id = "net-v3", entry_point = "net_env.envs:NetEnv", kwargs = {'nports' : 4, "id":"s3", "port": 50053})
#register(id = "net-v4", entry_point = "net_env.envs:NetEnv", kwargs = {'nports' : 4, "id":"s4", "port": 50054})
#register(id = "net-v5", entry_point = "net_env.envs:NetEnv", kwargs = {'nports' : 4, "id":"s5", "port": 50055})
register(id = "net-v6", entry_point = "net_env.envs:NetEnv", kwargs = {"switch_id":"s6", "port": 50056})
register(id = "net-v7", entry_point = "net_env.envs:NetEnv", kwargs = {"switch_id":"s7", "port": 50057})
register(id = "net-v8", entry_point = "net_env.envs:NetEnv", kwargs = {"switch_id":"s8", "port": 50058})
# simple topology env
register(id = "net-v9", entry_point = "net_env.envs:NetEnv", kwargs = {"switch_id":"s9", "port": 50059})
register(id = "net-v0", entry_point = "net_env.envs:NetEnv",)