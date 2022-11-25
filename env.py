import random
import model

class envi:
	def __init__(self):
		super(envi,self).__init__()
		f = open(model.network_topo, "r")
		layers = f.readlines()
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
			break
		self.name=name
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
		self.state_shape=[2]  #['E_size','F_size']
		self.action_shape=[3]*2  #['+1','-1','+0']*states
		self.max_dims={'E_size':self.E,'F_size':self.F}
		self.min_dims={'E_size':1,'F_size':1}
		self.acts=[-1,0,+1]
		self.base_reward=model.cost_model({})
		self.overflow_count=0
		self.stats_dir=model.root_dir+model.overall_stats
		stats_file = open(self.stats_dir, "a+")
		stats_file.write('%d,%d,%d,%d,\n' %(0,0,0,self.overflow_count))
		stats_file.close()
		self.R_size,self.S_size,self.C_size,self.M_size=1,1,model.array_.array_height,model.array_.array_width

	def reset(self):
		self.state={'E_size':random.randint(1,self.E),'F_size':random.randint(1,self.F)}
		temp_state={'E_size':(self.state['E_size']-(self.E/2))/(self.E/2),'F_size':(self.state['F_size']-(self.F/2))/(self.F/2)}
		return temp_state

	def step(self,action,episode=0,step=0,prop_neg=True,constant_p=100,constant_n=50):
		i=0
		for key, value in self.state.items():
			self.state[key]=max(self.min_dims[key],min(self.max_dims[key],value+self.acts[action[i]]))
			i+=1
		temp_state={'E_size':(self.state['E_size']-(self.E/2))/(self.E/2),'F_size':(self.state['F_size']-(self.F/2))/(self.F/2)}		
		allow, reward=self._is_allowed(self.state)
		if not prop_neg:
			reward=-constant_n
		else:
			reward*=constant_n
		stats_file = open(self.stats_dir, "a+")
		if allow:
			reward=model.cost_model(self.state)
			reward=(self.base_reward-reward)/self.base_reward
			if reward>0:
				reward*=constant_p
			stats_file.write('%0.6f,%d,%d,%d,\n' %(reward,episode,step,self.overflow_count))
		else:
			self.overflow_count+=1
			stats_file.write("%s, %d, %d, %d, %d, %d, %d, %d, %d, %.3f, %.3f, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %.3f, %.3f, %.3f, %0.6f, %d, %d, %d,\n " % (self.name,\
			self.H,self.W,self.R,self.S,self.C,self.M,self.Sx,self.Sy,self.state['E_size'],self.state['F_size'],self.R_size,self.S_size,self.C_size,self.M_size,\
			0,0,0,0,0,0,0.,0.,0.,reward,episode,step,self.overflow_count))
		stats_file.close()
		return temp_state, reward, False, allow 

	def _is_allowed(self,state):
		ef=self.state['E_size']*self.state['F_size']
		obuf_overflow=ef-model.array_.obuf_entries  #!*C_size, scaling factor based on var_size
		ibuf_overflow=ef*self.Sx*self.Sy-model.array_.ibuf_entries  #!*C_size, scaling factor based on var_size
		wbuf_overflow=self.M_size*self.R_size*self.S_size*self.C_size-model.array_.wbuf_size
		if obuf_overflow > 0:
			print('GEMM\'s output is more than output buffer size! (per column)')
			return False, -obuf_overflow/model.array_.obuf_entries  #float(-math.inf)
		if ibuf_overflow > 0:     
			print('Input buffer is small!')
			return False, -ibuf_overflow/model.array_.ibuf_entries
		if wbuf_overflow>0:  #scaling factor based on variable size!
			print('Weight buffer is small!')
			return False, -wgt_overflow/model.array_.wbuf_entries  #float(-math.inf)
		return True, 0
'''
		if self.state['M_size']*self.state['R_size']*self.state['S_size']*self.state['C_size']>model.array_.wbuf_size:  #scaling factor based on variable size!
			print('Weight buffer is small!')
			return False, -wgt_overflow  #float(-math.inf)
'''
'''
env=envi()
for e in range(2):
    avg_reward=0
    observation = env.reset()  #initialize OpenAI Gym environment
    for t in range(2):
        # Query the agent for its action decision
        act, value  = [1,2,0],0
        #print(action, value)
        # Execute the decision and retrieve the current performance
        observation, reward, done, info = env.step(act)
        print('reward:',reward,observation,done)
        avg_reward+=reward
        # Modify reward so that negative reward is given when it finishes too early
        # Pass feedback about performance (and termination) to the agent
'''