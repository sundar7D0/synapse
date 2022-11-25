class Conv2DLayer:
	def __init__(self, name, layer_dimensions, base_addrs):
		self.name = name
		N, H, W, R, S, C, M, Sx, Sy = layer_dimensions
		self.N = N
		self.H = H
		self.W = W
		self.R = R
		self.S = S
		self.C = C
		self.M = M
		self.Sx = Sx
		self.Sy = Sy
	
		self.E = (H - R) // Sx + 1
		self.F = (W - S) // Sy + 1

		self.input_base, self.weight_base, self.output_base = base_addrs

class Network:
	def __init__(self, topology_file):

		self.layers = []

		f = open(topology_file, "r")

		layers = f.readlines()

		weight_addr = 0x10000000
		input_addr = 0x20000000
		output_addr = 0x30000000

		f.close()
		for layer in layers[2:]:
			values = layer.split(",")
			name = values[0]
			N = int(values[1])
			H = int(values[2])
			W = int(values[3])
			R = int(values[4])
			S = int(values[5])
			C = int(values[6])
			M = int(values[7])
			Sx = int(values[8])
			Sy = int(values[9])
			conv = Conv2DLayer(name, (N, H, W, R, S, C, M, Sx, Sy), (input_addr, weight_addr, output_addr))
			self.layers.append(conv)
			input_addr += N * H * W * C
			weight_addr += R * S * C * M
			output_addr += N * conv.E * conv.F * M
