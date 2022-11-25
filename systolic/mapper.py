import math
import array

LOAD = 'LD'
STORE = 'ST'
GEMM = 'GEMM'

OUT = 0
INP = 1
WGT = 2
NOP = 3

POP_PREV = 0
POP_NEXT = 1
PUSH_PREV = 2
PUSH_NEXT = 3

class Instruction:
	def __init__(self, opcode, flags, operands, idx=0):
		self.opcode = opcode
		self.flags = flags
		self.operands = operands
		self.idx=idx

	def set_flags(self, flags):
		self.flags = flags

	def set_execution_time(self, start, end):
		self.start_time = start
		self.end_time = end
		self.elapsed_time = end - start

	def print_stats(self, layerwise_stats):
		if self.opcode == LOAD or self.opcode == STORE:
			if len(self.operands) != 0:
				entry = self.operands[0]
				if entry.typ == OUT:  #nefm
					layerwise_stats.write("\t"+self.opcode+"(o),")
					e, f, m = entry.coord					
					layerwise_stats.write("\t%d,\t,\t%d,\t%d,\t,\t," % (m, e, f))
					es, fs, ms, s1, s2 = entry.size
					layerwise_stats.write("\t%d,\t,\t%d,\t%d,\t,\t," % (ms, es, fs))
				elif entry.typ == INP:  #nhwc
					layerwise_stats.write("\t"+self.opcode+"(i),")
					e, f, c = entry.coord
					layerwise_stats.write("\t,\t%d,\t%d,\t%d,\t,\t," % (c, e, f))
					es, fs, cs, s1, s2 = entry.size
					layerwise_stats.write("\t,\t%d,\t%d,\t%d,\t,\t," % (cs, es, fs))
				elif entry.typ == WGT:  #rscm
					layerwise_stats.write("\t"+self.opcode+"(w),")
					r, s, c, m = entry.coord
					layerwise_stats.write("\t%d,\t%d,\t,\t,\t%d,\t%d," % (m, c, r, s))
					_, cs, ms, s1, s2 = entry.size
					layerwise_stats.write("\t%d,\t%d,\t,\t,\t1,\t1," % (ms, cs))
			else:
				layerwise_stats.write("\t"+self.opcode+",")
				layerwise_stats.write("\t,\t,\t,\t,\t,\t,\t,\t,\t,\t,\t,\t,")
		else:
			layerwise_stats.write("\t"+self.opcode+",")
			if len(self.operands) != 0:
				out = self.operands[0]
				e, f, m = out.coord
				es, fs, ms, s1, s2 = out.size
				wgt = self.operands[2]
				r, s, c, m = wgt.coord
				_, cs, ms, s1, s2 = wgt.size
				layerwise_stats.write("\t%d,\t%d,\t%d,\t%d,\t%d,\t%d," % (m, c, e, f, r, s))
				layerwise_stats.write("\t%d,\t%d,\t%d,\t%d,\t%d,\t%d," % (ms, cs, es, fs, 1, 1))
			else:
				layerwise_stats.write("\t,\t,\t,\t,\t,\t,\t,\t,\t,\t,\t,\t,")
		if self.opcode == LOAD:
			layerwise_stats.write("\t%d,\t%d,\t%d,\t,\t,\t,\t\n" % (self.elapsed_time, self.start_time,	self.end_time))
		elif self.opcode == STORE:
			layerwise_stats.write("\t%d,\t,\t,\t,\t,\t%d,\t%d\n" % (self.elapsed_time, self.start_time,	self.end_time))
		else:
			layerwise_stats.write("\t%d,\t,\t,\t%d,\t%d,\t,\t\n" % (self.elapsed_time, self.start_time,	self.end_time))

class BufferEntry:
	def __init__(self, dram_base, sram_base, typ, coord, size):
		self.dram_base = dram_base
		self.sram_base = sram_base
		self.typ = typ
		self.coord = coord
		self.size = size
#		'{0:08b}'.format(dram_base),'{0:08b}'.format(dram_base),'{0:08b}'.format(dram_base)

class NetworkMapping:
	def __init__(self, network, array, sizes):
		self.network = network
		self.array = array
		self.start_instruction = Instruction(STORE, "0100", [])
		self.conv_mappings = []
		for layer in self.network.layers:
			conv_mapping = Conv2DMapping(self.array, layer, sizes)
			self.conv_mappings.append(conv_mapping)

class Conv2DMapping:
	def __init__(self, array, layer, sizes):
		self.array = array
		self.layer = layer
		for key, value in sizes.items():
			if key=='E_size':
				self.layer.E_size=int(value)
			elif key=='F_size':
				self.layer.F_size=int(value)
			elif key=='M_size':
				self.layer.M_size=int(value)
			elif key=='C_size':
				self.layer.C_size=int(value)
#		ins = Instruction(GEMM, "0110", []);  Instruction(LOAD, "0010", [])  #!
		self.mapping()

	def print_stats(self, root_dir, stats_file, log):
		start_time = self.instructions[0].start_time
		end_time = self.instructions[-1].end_time
		total_cycles = end_time - start_time		
		load_cycles = 0
		gemm_cycles = 0
		store_cycles = 0
		if log:
			layerwise_stats = open(root_dir+"layerwise_stats/"+self.layer.name+".csv","w")
			layerwise_stats.write("\tInstruction,\tm,\tc,\te,\tf,\tr,\ts,\tm_s,\tc_s,\te_s,\tf_s,\tr_s,\ts_s,\tExec Time,\tLoad Start,\t Load End,\t GEMM Start,\tGEMM End,\tStore Start,\tStore End\n")
		for ins in self.instructions:
			if log:
				ins.print_stats(layerwise_stats)
			exec_time = ins.elapsed_time
			if ins.opcode == LOAD:
				load_cycles += exec_time
			elif ins.opcode == GEMM:
				gemm_cycles += exec_time
			elif ins.opcode == STORE:
				store_cycles += exec_time
		if log:
			layerwise_stats.close()
		stats_file.write("%d, %d, %d, %d, %d, %d, %.3f, %.3f, %.3f," % (start_time, \
		end_time, total_cycles, load_cycles, gemm_cycles, store_cycles, \
		100 * load_cycles / total_cycles, 100 * gemm_cycles / total_cycles, 100 * store_cycles / total_cycles))

	def mapping(self):
		try:
			self.layer.M_size 
		except Exception:  #NameError
			self.layer.M_size=self.array.array_width
		self.M_folds = math.ceil(self.layer.M / self.layer.M_size)
		try:
			self.layer.C_size
		except Exception:
			self.layer.C_size=self.array.array_height
		self.C_folds = math.ceil(self.layer.C / self.layer.C_size)
		ibuf_limit = self.array.ibuf_size // (self.array.array_height * self.layer.Sx * self.layer.Sy)
		obuf_limit = self.array.obuf_size // (self.array.array_width)
		T_size_2 = min(ibuf_limit, obuf_limit, self.layer.N * self.layer.E * self.layer.F);T_size = math.floor(math.sqrt(T_size_2))	
		try:
			self.layer.E_size
		except Exception:
			self.layer.E_size=min(self.layer.E,T_size)
		try:
			self.layer.F_size
		except Exception:
			self.layer.F_size=min(self.layer.F,T_size)
		try:
			self.layer.R_size
#			print('Warning: Using a non-unity R_size!')
#			exit(0)
		except Exception:
			self.layer.R_size=1
		try:
			self.layer.S_size
#			print('Warning: Using a non-unity S_size!')
#			exit(0)
		except Exception:
			self.layer.S_size=1
		self.E_folds = math.ceil(self.layer.E / self.layer.E_size)
		self.F_folds = math.ceil(self.layer.F / self.layer.F_size)
		self.instructions = []
		self.weight_buffer = []
		self.input_buffer = []
		self.output_buffer = []
		self.output_folds = set()
		self.wbuf_empty = self.array.wbuf_entries
		self.ibuf_empty = self.array.ibuf_entries
		self.obuf_empty = self.array.obuf_entries
		self.wbuf_addr = 0
		self.ibuf_addr = 0
		self.obuf_addr = 0
		print("(tile_size/total) E:%d/%d, F:%d/%d, R:%d/%d, S:%d/%d, C:%d/%d, M:%d/%d, Sx:%d, Sy:%d " % (self.layer.E_size,self.layer.E,self.layer.F_size,self.layer.F,\
			self.layer.R_size,self.layer.R,self.layer.S_size,self.layer.S,self.layer.C_size,self.layer.C,self.layer.M_size,self.layer.M,self.layer.Sx,self.layer.Sy))
		for m in range(self.M_folds):
			for c in range(self.C_folds):
				for e in range(self.E_folds):
					for f in range(self.F_folds):
						for r in range(self.layer.R):
							for s in range(self.layer.S):
								wgt_ld, wgt_entry = self.load_weight(r,s,c,m)
								inp_ld, inp_entry = self.load_input(e,f,c)
								out_ld, out_entry, evict_out = self.store_output(e,f,m)
								self.generate_gemm(wgt_ld, inp_ld, out_ld, evict_out, wgt_entry, inp_entry, out_entry)
		
	def update_flag(self, target, operand, coord, flag_idx, dont_update):
		it = len(self.instructions) - 1
		while it >= 0:
			ins = self.instructions[it]
			if target == ins.opcode:
				if target == LOAD or target == STORE:
					ref = ins.operands[0]
				else:
					if ins.operands==[]:
						break
					ref = ins.operands[operand]
				if ref.coord == coord and ref.typ == operand:
					flags = list(ins.flags)
					if dont_update:
						if flags[flag_idx]=="1":
							return True, ins.idx, False  #!(found?, instr_index, already_not_set?)
						else:
							return True, ins.idx, True
					if flags[flag_idx]=="1":
						return True, ins.idx, False
					flags[flag_idx] = "1"
					flags = "".join(flags)
					ins.set_flags(flags)
					return True, ins.idx, True
			it -= 1
		return False, -1, None

	def search_weight(self, coord):
		for entry in self.weight_buffer:
			if entry.coord == coord:
				return (True, entry)
		return (False, 0)
	
	def load_weight(self, r, s, c, m):  
		search, entry = self.search_weight((r,s,c,m))
		if search:
			return (False, entry)
		else:
			halo_c = self.layer.C % self.layer.C_size != 0 and c == (self.C_folds-1)
			halo_m = self.layer.M % self.layer.M_size != 0 and m == (self.M_folds-1)
			wgt_c = (self.layer.C % self.layer.C_size) if halo_c else self.layer.C_size
			wgt_m = (self.layer.M % self.layer.M_size) if halo_m else self.layer.M_size
			wgt_size = wgt_c  #!*wgt_m
			next_dep, update_gemm_idx, update_gemm_coord = False, -1, (-1,-1,-1,-1)
			while self.wbuf_empty < wgt_size:
				entry = self.weight_buffer[0]  #!eviction based on gemm completion on a stale data address! (or can be made as action space of rl)
				gemm_dep, gemm_idx, _=self.update_flag(GEMM, WGT, entry.coord, PUSH_PREV, dont_update=1)
				if gemm_dep and gemm_idx>update_gemm_idx:
					update_gemm_idx=gemm_idx
					update_gemm_coord=entry.coord
				next_dep = next_dep or gemm_dep  
				self.wbuf_empty += entry.size[0] * entry.size[1]  #!entry.size[2]
				self.weight_buffer.pop(0)
			if next_dep:
				gemm_dep, gemm_idx, gemm_set=self.update_flag(GEMM,WGT,update_gemm_coord,PUSH_PREV,dont_update=0)
				assert gemm_dep==True and gemm_idx>-1
				if not gemm_set:
					next_dep=False
			base = self.layer.weight_base
			base += ((r * self.layer.S + s) * self.layer.C + c) * self.layer.M + m * self.layer.M_size
			entry = BufferEntry(base, self.wbuf_addr, WGT, (r, s, c, m), (1, wgt_c, wgt_m, self.layer.M, self.layer.C * self.layer.M))
			self.weight_buffer.append(entry)
			self.wbuf_empty -= wgt_size
			self.wbuf_addr = (self.wbuf_addr + wgt_size) % (self.array.wbuf_entries)  #!How? What abt diff columns?
			ins = Instruction(LOAD, "0100" if next_dep else "0000", [entry])
			self.instructions.append(ins);self.instructions[-1].idx=len(self.instructions)
			return (True, entry)

	def search_input(self, coord):
		for entry in self.input_buffer:
			if entry.coord == coord:
				return (True, entry)
		return (False, 0)

	def load_input(self, e, f, c):
		search, entry = self.search_input((e,f,c))
		if search:
			return (False, entry)
		else:
			halo_e = self.layer.E % self.layer.E_size != 0 and e == self.E_folds-1
			halo_f = self.layer.F % self.layer.F_size != 0 and f == self.F_folds-1
			inp_e = self.layer.Sx * (self.layer.E % self.layer.E_size if halo_e else self.layer.E_size)
			inp_f = self.layer.Sy * (self.layer.F % self.layer.F_size if halo_f else self.layer.F_size)
			inp_size = inp_e * inp_f  #!
			halo_c = self.layer.C % self.layer.C_size != 0 and c == (self.C_folds-1)
			inp_c = self.layer.C % self.layer.C_size if halo_c else self.layer.C_size
			next_dep, update_gemm_idx, update_gemm_coord = False, -1, (-1,-1,-1,-1)
			while self.ibuf_empty < inp_size:
				entry = self.input_buffer[0]
				gemm_dep, gemm_idx, _=self.update_flag(GEMM, INP, entry.coord, PUSH_PREV, dont_update=1)
				if gemm_dep and gemm_idx>update_gemm_idx:
					update_gemm_idx=gemm_idx
					update_gemm_coord=entry.coord
				next_dep = next_dep or gemm_dep
				self.ibuf_empty += entry.size[0] * entry.size[1]  #!*entry.size[2]
				self.input_buffer.pop(0)
			if next_dep:
				gemm_dep, gemm_idx, gemm_set=self.update_flag(GEMM,INP,update_gemm_coord,PUSH_PREV,dont_update=0)
				assert gemm_dep==True and gemm_idx>-1
				if not gemm_set:
					next_dep=False
			base = self.layer.input_base
			base += (e * self.layer.E_size * self.layer.Sx * self.layer.W + f * self.layer.Sy * self.layer.F_size) * self.layer.C + c * self.layer.C_size
			entry = BufferEntry(base, self.ibuf_addr, INP, (e, f, c), (inp_e, inp_f, inp_c, self.layer.C, self.layer.W * self.layer.C))
			self.input_buffer.append(entry)
			self.ibuf_empty -= inp_size
			self.ibuf_addr = (self.ibuf_addr + inp_size) % (self.array.ibuf_entries)
			ins = Instruction(LOAD, "0100" if next_dep else "0000", [entry])
			self.instructions.append(ins);self.instructions[-1].idx=len(self.instructions)
			return (True, entry)
	
	def search_output(self, coord):
		for entry in self.output_buffer:
			if entry.coord == coord:
				return (True, entry)
		return (False, 0)

	def store_output(self, e, f, m):
		search, entry = self.search_output((e,f,m))
		if search:
			return (False, entry, False)
		else:
			halo_e = self.layer.E % self.layer.E_size != 0 and e == self.E_folds-1
			halo_f = self.layer.F % self.layer.F_size != 0 and f == self.F_folds-1
			out_e = self.layer.E % self.layer.E_size if halo_e else self.layer.E_size
			out_f = self.layer.F % self.layer.F_size if halo_f else self.layer.F_size
			out_size = out_e * out_f
			halo_m = self.layer.M % self.layer.M_size != 0 and m == (self.M_folds-1)
			out_m = self.layer.M % self.layer.M_size if halo_m else self.layer.M_size 
			evict_data = False
			while self.obuf_empty < out_size:
				entry = self.output_buffer[0]
				evict_data = True
				gemm_dep, gemm_idx, _=self.update_flag(GEMM, OUT, entry.coord, PUSH_NEXT, dont_update=0)
				ins = Instruction(STORE, "1000" if _ else "0000", [entry])
				self.instructions.append(ins);self.instructions[-1].idx=len(self.instructions)
				self.obuf_empty += entry.size[0] * entry.size[1]  #!*entry.size[2]
				self.output_buffer.pop(0)
			if evict_data:
				t_ins=self.instructions[-1]
				assert t_ins.opcode==STORE
				flags = list(t_ins.flags)
				assert flags[PUSH_PREV]=="0"
				flags[PUSH_PREV] = "1"
				flags = "".join(flags)
				t_ins.set_flags(flags)			
			output_load = False			
			base = (e * self.layer.E_size * self.layer.F + f * self.layer.F_size) * self.layer.M + m * self.layer.M_size
			out_entry = BufferEntry(base, self.obuf_addr, OUT, (e, f, m), (out_e, out_f, out_m, self.layer.M, self.layer.F * self.layer.M))
			self.output_buffer.append(out_entry)
			self.obuf_empty -= out_size
			self.obuf_addr = (self.obuf_addr + out_size) % (self.array.obuf_entries)
			if (e, f, m) in self.output_folds:
				self.instructions.append(Instruction(GEMM, "0110" if evict_data else "0010", []));self.instructions[-1].idx=len(self.instructions)
				ins = Instruction(LOAD, "0100", [out_entry])
				self.instructions.append(ins);self.instructions[-1].idx=len(self.instructions)
				output_load = True
			return (output_load, out_entry, evict_data)

	def generate_gemm(self, wgt_ld, inp_ld, out_ld, evict_data, wgt_entry, inp_entry, out_entry):
		if out_ld:
			loado_dep,_,loado_set=self.update_flag(LOAD, OUT, out_entry.coord, PUSH_NEXT, dont_update=0)
			assert loado_dep and _>-1 and loado_set
		elif inp_ld:
			loadi_dep,_,loadi_set=self.update_flag(LOAD, INP, inp_entry.coord, PUSH_NEXT, dont_update=0)
			assert loadi_dep and _>-1 and loadi_set
		elif wgt_ld:
			loadw_dep,_,loadw_set=self.update_flag(LOAD, WGT, wgt_entry.coord, PUSH_NEXT, dont_update=0)
			assert loadw_dep and _>-1 and loadw_set
		dep_flags = ("1" if (out_ld or inp_ld or wgt_ld) else "0") + ("1" if (evict_data and not out_ld) else "0") + "0" + "0"
		ins = Instruction(GEMM, dep_flags, [out_entry, inp_entry, wgt_entry])
		self.instructions.append(ins);self.instructions[-1].idx=len(self.instructions)
		self.output_folds.add(out_entry.coord)
