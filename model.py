from systolic.array import SystolicArray
from systolic.simulator import Simulator
from systolic.layer import Conv2DLayer, Network
from systolic.mapper import Conv2DMapping, NetworkMapping
#import argparse
import os

log=False  #whether to layer_wise_stats & run.log
#if __name__ == '__main__':
#parser = argparse.ArgumentParser()
#parser.add_argument('--dram_ini_file', default="./ini/DDR3_micron_64M_8B_x4_sg15.ini", help="Path for DRAM config file")
#parser.add_argument('--system_ini_file', default="./system.ini.example",	help="Path for system config file, required for DRAMSim2")
#parser.add_argument('--dram_capacity', default=16384, help="DRAM Capacity in MB")
#parser.add_argument('--array_config', default="./configs/1.cfg", help="Path for systolic array config file")  #systolic_array_config
#parser.add_argument('--network', default="./topologies/1.csv",	help="Path for configuration of layers of the network")  #network_config
#parser.add_argument('--run_name', default="out1")  # required=True)
#args = parser.parse_args()
#array = SystolicArray(args.array_config, args.dram_ini_file, args.system_ini_file, DRAMSim_dir, args.run_name, args.dram_capacity)
#network = Network(args.network)
dram_ini_file="./ini/DDR3_micron_64M_8B_x4_sg15.ini"
system_ini_file="./system.ini.example"
dram_capacity=16384
array_config='./configs/1.cfg'
network_topo='./topologies/1.csv'
run_name='out1'
root_dir = "./outputs/" + run_name + "/"  #args.run_name
DRAMSim_dir = "./DRAMSim2"
DRAM_capacity = 16384
network = Network(network_topo)
array_ = SystolicArray(array_config, dram_ini_file, system_ini_file, DRAMSim_dir, run_name, dram_capacity)
overall_stats="./overall_stats.csv"
def cost_model(sizes):
	array = SystolicArray(array_config, dram_ini_file, system_ini_file, DRAMSim_dir, run_name, dram_capacity)
	simulator = Simulator(array)
	mapping = NetworkMapping(network, array, sizes)
	if not os.path.exists("./outputs"):
		os.makedirs("./outputs")
	if not os.path.exists("./outputs/" + run_name):  #args.run_name
		os.makedirs("./outputs/" + run_name)  #args.run_name
	if log:
		if not os.path.exists("./outputs/" + run_name + "/layerwise_stats"):  #args.run_name
			os.makedirs("./outputs/" + run_name + "/layerwise_stats")  #args.run_name
	reward=simulator.simulate(mapping, root_dir, overall_stats, log)  #total_cycle_time
	return reward
#cost_model({'E_size':89, 'F_size':10})
#cost_model({'E_size':58, 'F_size':2})
#cost_model({})