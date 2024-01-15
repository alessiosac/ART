from net_env2.envs.net_env2 import PortForwardingEnvironment

from gymnasium.envs.registration import register
register(id = "net-v1", entry_point = "net_env2.envs:PortForwardingEnvironment")
#register(id = "net-v2", entry_point = "net_env.envs:NetEnv", kwargs = {'nports' : 4, "id":"s2", "port": 50052})
#register(id = "net-v3", entry_point = "net_env.envs:NetEnv", kwargs = {'nports' : 4, "id":"s3", "port": 50053})
#register(id = "net-v4", entry_point = "net_env.envs:NetEnv", kwargs = {'nports' : 4, "id":"s4", "port": 50054})
#register(id = "net-v5", entry_point = "net_env.envs:NetEnv", kwargs = {'nports' : 4, "id":"s5", "port": 50055})
register(id = "net-v6", entry_point = "net_env2.envs:PortForwardingEnvironment")
register(id = "net-v7", entry_point = "net_env2.envs:PortForwardingEnvironment")
register(id = "net-v8", entry_point = "net_env2.envs:PortForwardingEnvironment")
# simple topology env
register(id = "net-v9", entry_point = "net_env2.envs:PortForwardingEnvironment")