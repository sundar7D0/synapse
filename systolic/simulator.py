import os
import array
import DRAM

LOAD = 'LD'
STORE = 'ST'
GEMM = 'GEMM'

#flags order: pop prev, push prev, pop next, push next
def pop_prev(flags):  #1XXX
	return ((flags // 1000) == 1)

def pop_next(flags):  #X1XX
	return ((flags // 100) % 10 == 1)

def push_prev(flags):  #XX1X
	return (((flags // 10) % 10) == 1)

def push_next(flags):  #XXX1
	return (flags % 10 == 1)

def pop_timestamp(old_timestamp, pop_timestamp):
	if pop_timestamp > old_timestamp:
		return pop_timestamp
	else:
		return old_timestamp

class Simulator:
	def __init__(self, array):
		self.array = array
		self.load_timestamp = 0
		self.gemm_timestamp = 0
		self.store_timestamp = 0
		self.load_util_cycles = 0
		self.gemm_util_cycles = 0
		self.store_util_cycles = 0
		self.LOAD_GEMM_Q = []
		self.GEMM_LOAD_Q = []
		self.GEMM_STORE_Q = []
		self.STORE_GEMM_Q = []

	def load_cycles(self, params):
		dram_time = self.array.mem.get_current_time()
		if self.load_timestamp < dram_time:
			self.load_timestamp = dram_time
		else:
			self.array.mem.update(self.load_timestamp)
		base = int(params[0])
		d1 = int(params[1])
		d2 = int(params[2])
		d3 = int(params[3])
		s1 = int(params[4])
		s2 = int(params[5])
		d3 = (d3 // 64) + (0 if d3%64==0 else 1)  #!why?
		addr1 = base
		addr2 = base	
		for i in range(d1):
			addr2 = addr1
			for j in range(d2):
				for k in range(d3):
					self.array.mem.request(addr2 + k * 64, False)  #!verify
					rv = self.array.mem.read_response()
				addr2 += s1
			addr1 += s2
		return rv.clock_cycle + 1

	def store_cycles(self, params):
		dram_time = self.array.mem.get_current_time()
		if self.store_timestamp < dram_time:
			self.store_timestamp = dram_time
		else:
			self.array.mem.update(self.store_timestamp)
		base = int(params[0])
		d1 = int(params[1])
		d2 = int(params[2])
		d3 = int(params[3])
		s1 = int(params[4])
		s2 = int(params[5])
		d3 = (d3 // 64) + (0 if d3%64==0 else 1)  #!why?
		addr1 = base
		addr2 = base
		for i in range(d1):
			addr2 = addr1
			for j in range(d2):
				for k in range(d3):
					self.array.mem.request(addr2 + k * 64, True)  #!verify
					rv = self.array.mem.write_response()
				addr2 += s1
			addr1 += s2
		return rv.clock_cycle + 1

	def gemm_cycles(self, params):
		T = params[0]
		H = params[1]
		W = params[2]
		cycles = T + H + W - 2  #!PE utilization (0 muls/just partial output passing) is not taken into account?
		return self.gemm_timestamp + cycles

	def run_load(self, instruction, output_file, log):
		dep_flags = int(instruction.flags)
		if pop_next(dep_flags):
			dep_timestamp = self.GEMM_LOAD_Q.pop(0)
			if log:
				output_file.write("%d : GEMM -> LOAD dependency received" % dep_timestamp + "\n")
			self.load_timestamp = pop_timestamp(self.load_timestamp, dep_timestamp)
			if log:
				output_file.write("%d : GEMM -> LOAD dependency processed" % self.load_timestamp + "\n")
		if instruction.operands != []:
			if log:
				output_file.write(str(self.load_timestamp) + " : begin " + str(instruction.operands[0].coord) + "\n")
			size = instruction.operands[0].size
			params = (instruction.operands[0].dram_base, size[0], size[1], size[2], size[3], size[4])
			new_timestamp = self.load_cycles(params)
			old_timestamp = self.load_timestamp
			self.load_util_cycles += (new_timestamp - old_timestamp)
			self.load_timestamp = new_timestamp
		else:
			if log:
				output_file.write(str(self.store_timestamp) + " : begin " + str(instruction.opcode) + "\n")
			new_timestamp = self.load_timestamp + 1
			old_timestamp = self.load_timestamp
			self.load_timestamp = new_timestamp
		instruction.set_execution_time(old_timestamp, new_timestamp)
		if log:
			output_file.write(str(self.load_timestamp) + " : end" + "\n")
		if push_next(dep_flags):
			self.LOAD_GEMM_Q.append(self.load_timestamp)

	def run_store(self, instruction, output_file, log):
		dep_flags = int(instruction.flags)
		if pop_prev(dep_flags):
			dep_timestamp = self.GEMM_STORE_Q.pop(0)
			if log:
				output_file.write("%d : GEMM -> STORE dependency received" % dep_timestamp + "\n")
			self.store_timestamp = pop_timestamp(self.store_timestamp, dep_timestamp)
			if log:
				output_file.write("%d : GEMM -> STORE dependency processed" % self.store_timestamp + "\n")
		if instruction.operands != []:
			if log:
				output_file.write(str(self.store_timestamp) + " : begin " + str(instruction.operands[0].coord) + "\n")
			size = instruction.operands[0].size
			params = (instruction.operands[0].dram_base, size[0], size[1], size[2], size[3], size[4])
			new_timestamp = self.store_cycles(params)
			old_timestamp = self.store_timestamp
			self.store_util_cycles += (new_timestamp - old_timestamp)
			self.store_timestamp = new_timestamp
		else:
			if log:
				output_file.write(str(self.store_timestamp) + " : begin " + str(instruction.opcode) + "\n")
			new_timestamp = self.store_timestamp + 1
			old_timestamp = self.store_timestamp
			self.store_timestamp = new_timestamp
		instruction.set_execution_time(old_timestamp, new_timestamp)
		if log:
			output_file.write(str(self.store_timestamp) + " : end " + "\n")
		if push_prev(dep_flags):
			self.STORE_GEMM_Q.append(self.store_timestamp)

	def run_gemm(self, instruction, output_file, log):
		dep_flags = int(instruction.flags)
		if pop_prev(dep_flags):
			dep_timestamp = self.LOAD_GEMM_Q.pop(0)
			if log:
				output_file.write("%d : LOAD -> GEMM dependency received" % dep_timestamp + "\n")
			self.gemm_timestamp = pop_timestamp(self.gemm_timestamp, dep_timestamp)
			if log:
				output_file.write("%d : LOAD -> GEMM dependency processed" % self.gemm_timestamp + "\n")
		if pop_next(dep_flags):
			dep_timestamp = self.STORE_GEMM_Q.pop(0)
			if log:
				output_file.write("%d : STORE -> GEMM dependency received" % dep_timestamp + "\n")
			self.gemm_timestamp = pop_timestamp(self.gemm_timestamp, dep_timestamp)
			if log:
				output_file.write("%d : STORE -> GEMM dependency processed" % self.gemm_timestamp + "\n")
		old_timestamp = self.gemm_timestamp
		if instruction.operands != []:
			if log:
				output_file.write(str(self.gemm_timestamp) + " : begin " + str(instruction.opcode) + " " + str(instruction.operands[2].coord) + "\n")
			out_size = instruction.operands[0].size
			T = out_size[0] * out_size[1]
			new_timestamp = self.gemm_cycles((T, self.array.array_height, self.array.array_width))
			self.gemm_util_cycles += (new_timestamp - self.gemm_timestamp)
			self.gemm_timestamp = new_timestamp
		else:
			if log:
				output_file.write(str(self.gemm_timestamp) + " : begin " + str(instruction.opcode) + "[]\n")
			new_timestamp = self.gemm_timestamp + 1
			self.gemm_timestamp = new_timestamp
		instruction.set_execution_time(old_timestamp, self.gemm_timestamp)
		if log:
			output_file.write(str(self.gemm_timestamp) + " : end " + "\n")
		if push_prev(dep_flags):
			self.GEMM_LOAD_Q.append(self.gemm_timestamp)
		if push_next(dep_flags):
			self.GEMM_STORE_Q.append(self.gemm_timestamp)

	def simulate(self, network_mapping, root_dir, overall_stats, log):
		output_file = open(root_dir+"run.log", "w") if log else None 
		for layer in network_mapping.conv_mappings:
			print("Simulating layer %s with %d instructions" % (layer.layer.name,	len(layer.instructions)))
			self.LOAD_QUEUE = []
			self.GEMM_QUEUE = []
			self.STORE_QUEUE = []
			leni=len(layer.instructions)
			l0,l1,l2,l3,g0,g1,g2,g3,s0,s1,s2,s3=0,0,0,0,0,0,0,0,0,0,0,0
			for instruction in layer.instructions:
				opcode = instruction.opcode
				if opcode == LOAD:
					self.LOAD_QUEUE.append(instruction)
					if instruction.flags[0]=='1':
						l0+=1
					if instruction.flags[1]=='1':
						l1+=1
					if instruction.flags[2]=='1':
						l2+=1
					if instruction.flags[3]=='1':
						l3+=1
				elif opcode == STORE:
					self.STORE_QUEUE.append(instruction)
					if instruction.flags[0]=='1':
						s0+=1
					if instruction.flags[1]=='1':
						s1+=1
					if instruction.flags[2]=='1':
						s2+=1
					if instruction.flags[3]=='1':
						s3+=1
				elif opcode == GEMM:
					self.GEMM_QUEUE.append(instruction)
					if instruction.flags[0]=='1':
						g0+=1
					if instruction.flags[1]=='1':
						g1+=1
					if instruction.flags[2]=='1':
						g2+=1
					if instruction.flags[3]=='1':
						g3+=1
			if log:
				print('dep_flags ld: ',l0,l1,l2,l3)
				print('dep_flags gemm: ',g0,g1,g2,g3)
				print('dep_flags st: ',s0,s1,s2,s3)
			count_l,count_g,count_s=len(self.LOAD_QUEUE),len(self.GEMM_QUEUE),len(self.STORE_QUEUE)
			LD,GM,ST=0,1,2
			while (len(self.LOAD_QUEUE) + len(self.STORE_QUEUE) + len(self.GEMM_QUEUE)) != 0:
				timestamps = []
				if len(self.LOAD_QUEUE) != 0:
					timestamps.append([self.load_timestamp,LD])
				if len(self.GEMM_QUEUE) != 0:
					timestamps.append([self.gemm_timestamp,GM])
				if len(self.STORE_QUEUE) != 0:
					timestamps.append([self.store_timestamp,ST])
				timestamps.sort()
#				print('load_left: ',len(self.LOAD_QUEUE),'/',count_l)
#				print('gemm_left: ',len(self.GEMM_QUEUE),'/',count_g)
#				print('store_left: ',len(self.STORE_QUEUE),'/',count_s)
				while timestamps != []:
					stamp = timestamps[0]
					timestamps.pop(0)
					if stamp[0] == self.load_timestamp and stamp[1]==LD:
						ins = self.LOAD_QUEUE[0]
						flags = int(ins.flags)
						pop_nxt = pop_next(flags)
						if not pop_nxt or (pop_nxt and len(self.GEMM_LOAD_Q) != 0):
							self.LOAD_QUEUE.pop(0)
							self.run_load(ins, output_file, log)
							break
						else:
							continue
					if stamp[0] == self.store_timestamp and stamp[1]==ST:
						ins = self.STORE_QUEUE[0]
						flags = int(ins.flags)
						pop_prv = pop_prev(flags)
						if not pop_prv or (pop_prv and len(self.GEMM_STORE_Q) != 0):
							self.STORE_QUEUE.pop(0)
							self.run_store(ins, output_file, log)
							break
						else:
							continue
					if stamp[0] == self.gemm_timestamp and stamp[1]==GM:
						ins = self.GEMM_QUEUE[0]
						flags = int(ins.flags)
						pop_prv = pop_prev(flags)
						pop_nxt = pop_next(flags)
						if ((not pop_prv or (pop_prv and len(self.LOAD_GEMM_Q) != 0)) and \
								 (not pop_nxt or (pop_nxt and len(self.STORE_GEMM_Q) != 0))):
							self.GEMM_QUEUE.pop(0)
							self.run_gemm(ins, output_file, log)
							break
						else:
							continue
		if not os.path.exists(root_dir+overall_stats):
			stats_file = open(root_dir+overall_stats, "a+")
			stats_file.write("Name, H, W, R, S, C, M, Sx, Sy, E_size, F_size, R_size, S_size, C_size, M_size, Start time, Finish time, Total cycles, Load Cycles, GEMM Cycles, Store Cycles, Load Util%, GEMM Util%, Store Util%, Reward, Episode, Step, Overflow_count\n")
		else:
			stats_file = open(root_dir+overall_stats, "a+")
		for layer in network_mapping.conv_mappings:
			stats_file.write("%s, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, " % (layer.layer.name, layer.layer.H, layer.layer.W, \
			layer.layer.R, layer.layer.S, layer.layer.C, layer.layer.M, layer.layer.Sx, layer.layer.Sy, layer.layer.E_size, layer.layer.F_size, layer.layer.R_size, \
			layer.layer.S_size, layer.layer.C_size, layer.layer.M_size))
			if log:
				print("%s: H:%d, W:%d, R:%d, S:%d, C:%d, M:%d, Sx:%d, Sy:%d, E_size:%d, F_size:%d, R_size:%d, S_size:%d, C_size:%d, M_size:%d" % (layer.layer.name,  \
				layer.layer.H, layer.layer.W, layer.layer.R, layer.layer.S, layer.layer.C, layer.layer.M, layer.layer.Sx, layer.layer.Sy, layer.layer.E_size, layer.layer.F_size,\
				layer.layer.R_size, layer.layer.S_size, layer.layer.C_size, layer.layer.M_size))
			layer.print_stats(root_dir, stats_file, log)
		max_timestamp = max(self.load_timestamp, self.store_timestamp, self.gemm_timestamp)
#		stats_file.write("\n");
		stats_file.close()
		print("Total time: %d" %(max_timestamp))
		print("Load module utilization: %f" % (self.load_util_cycles / max_timestamp))
		print("Store module utilization: %f" % (self.store_util_cycles / max_timestamp))
		print("GEMM module utilization: %f" % (self.gemm_util_cycles / max_timestamp))
		return max_timestamp
'''
				stats_file = open(root_dir+"./overall_stats.csv", "r")
		reader_file = csv.reader(stats_file)
		value = len(list(reader_file))	
		print('val:',value)
		stats_file.close()
'''