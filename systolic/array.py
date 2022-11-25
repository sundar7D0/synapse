import sys
import configparser as cp
import DRAM

class SystolicArray:
	def __init__(self,
						config_file,
						dram_ini_file,
						system_ini_file,
						dramsim_folder,
						dram_output_dir,
						dram_capacity):
		general = 'general'
		arch_sec = 'architecture_presets'
		net_sec  = 'network_presets'
		
		config = cp.ConfigParser()
		config.read(config_file)

		print("Reading array configurations from " + config_file)
		self.array_height = int(config.get(arch_sec, "ArrayHeight"))
		self.array_width = int(config.get(arch_sec, "ArrayWidth"))

		self.ibuf_size = 1024 * int(config.get(arch_sec, "IfmapSramSz"))
		self.wbuf_size = 1024 * int(config.get(arch_sec, "FilterSramSz"))
		self.obuf_size = 1024 * int(config.get(arch_sec, "OfmapSramSz"))

		self.ibuf_entries = self.ibuf_size // self.array_height
		self.wbuf_entries = self.wbuf_size // self.array_width
		self.obuf_entries = self.obuf_size // self.array_width

		self.mem = DRAM.Memifc(dram_ini_file, system_ini_file, dramsim_folder, dram_output_dir, dram_capacity)

if __name__ == '__main__':
	if len(sys.argv) != 5:
		print("insufficient arguments")

	num_arrays = int(sys.argv[1])
	config_dir = sys.argv[2]
	topology_dir = sys.argv[3]
	output_dir = sys.argv[4]

	for i in range(num_arrays):
		array = SystolicArray(i+1, config_dir, topology_dir, output_dir,
				"./ini/DDR3_micron_64M_8B_x4_sg15.ini", "./system.ini.example", "./DRAMSim2", "kulan", 16384)
		array.simulate()
	print('exiting')
