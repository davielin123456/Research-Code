import sys
import os
import pprint
import time
import hashlib
import random
import time
from random import shuffle

f_temp = open(sys.argv[2], "w")
f_sectors = open(sys.argv[5], "w")

req_count = 0
max_written_sector = 0

#adjust_ambient_T = 0
#adjust_ambient_C = 0

time_count = 0
one_second = 2*10**5 # 2*10**5  0.01 record
one_second_count = 0
cycle_times = 10
down_scale = 4.5

def parseArgument(argv):
	global cycle_times, down_scale
	parameter = {}
	parameter['traceFile'] = open(argv[1], 'r')
	cycle_times = int(argv[3])
	down_scale = float(argv[4])
	return parameter

def readOneTrace(parameter):
	fd = parameter['traceFile']
	stringFromFile = fd.readline()

	if not stringFromFile:
		return None
	sptStr = stringFromFile.split()

	request = {}
	request['type'] = sptStr[0][0].lower()

	request['LBA'] = int(sptStr[1])
	request['length'] = int(sptStr[2])

	return request

class initStorage():
	def __init__(self):
		self.total_space = 128*1024*1024*2 # based on LBA(sectors)
		self.layer_n = 16 # number of layers
		self.layer_size = self.total_space / self.layer_n # numbers of block in a layer (50GB/layer), 1 block = 512 bytes

		self.layers = [] # Storage System
		for i in range(self.layer_n):
			self.layers.append({})

		
		self.layer_sectors = [] # recorf the actual situations
		self.layer_sectors_map = [] # report the relationships between LBA and sectors
		for i in range(self.layer_n):
			self.layer_sectors.append([0]*self.layer_size)
			self.layer_sectors_map.append({})
		
		self.temperature = [25]*self.layer_n # temperature of each layer
		self.current = 2*10**(-3) # Write Current
		self.EResistance = 10**6 # Electronic resistance of a PCM cell
		self.HResistance = 0.7073*(10**(-6)) # Heat resistance between each layer
		self.write_time = 50*10**(-9) # Write Time
		self.layer_mass = 0.0785664 # 0.49104  Mass of a layer (g)
		self.layer_heatCapacity = 0.202 # Heat Capacity of GST (J/gK)
		self.area = self.total_space/(self.layer_n*1024*2*256) * 79.2*(10**(-6)) # Area of a layer (m^2)
		self.layer_used = [0]*self.layer_n # Used blocks in each layer

	def RiseTemperature(self, layer_index): # Simulate the rising of temperature in each layer
		# Temperature risen from passing current
		length = 1
		layer_risen = (((self.current**2)*self.EResistance*self.write_time)*(length*512*8)/4.184) / self.layer_mass*self.layer_heatCapacity
		self.temperature[layer_index] += layer_risen

		global adjust_ambient_T, adjust_ambient_C

		for i in range(self.layer_n): # Ambient temperature risen because of 3D stack
			ambient_risen = 0
			for j in range(layer_index+1):
				ambient_risen += (self.current**2)*self.EResistance*(length*512*8)*self.write_time
			ambient_risen *= self.HResistance / self.area
			self.temperature[i] += ambient_risen

	def DownTemperature(self):
		global f_temp, temp_record, one_second, one_second_count, down_scale

		down_temp_PerSec = 90.660691 # !!! Reference COMSOL
		down_time = down_scale * 10**(-6) # 0.5M requests per second
		down_temp = down_temp_PerSec * down_time
		self.temperature[:] = [temp - down_temp for temp in self.temperature]
		# Record Temperature
		
		one_second_count += 1
		if one_second_count >= one_second:
			temp_record = ''
			for i in range(self.layer_n):
				temp_record += (str(self.temperature[i]) + ' ')
			temp_record += '\n'
			f_temp.write(temp_record)
			one_second_count = 0
		

	def addLBA(self, layer_index, LBA_in, max_LBA, min_LBA):
		global PageTable, time_count, max_written_sector #, TLB

		try:
			inside = self.layers[layer_index][LBA_in]
		except:
			inside = 0

		try:
			sector_now = self.layer_sectors_map[layer_index][LBA_in]
		except:
			sector_now = None

		if inside == 0: # New LBA
			PageTable.update(LBA_in, layer_index, time_count)
			self.layers[layer_index][LBA_in] = 1

			r = range(self.layer_size)
			sector_now = random.choice(r)
			self.layer_sectors[layer_index][sector_now] += 1
			self.layer_sectors_map[layer_index][LBA_in] = sector_now
		else:
			self.layer_used[layer_index] += 1
			PageTable.update(LBA_in, layer_index, time_count)

			self.layer_sectors[layer_index][sector_now] += 1

		if self.layer_sectors[layer_index][sector_now] > max_written_sector:
			max_written_sector = self.layer_sectors[layer_index][sector_now]


	def OldLBAIn(self, LBA_in, OldAddress, Oldtime, max_LBA, min_LBA): # the current LBA exists in the Storage
		global time_count # Time point
		time_count += 1
		self.addLBA(OldAddress, LBA_in, max_LBA, min_LBA)

		# Update the temperatures of each layer
		self.RiseTemperature(OldAddress)

	def NewLBAIn(self, LBA_in, max_LBA, min_LBA): # the current LBA doesn't exist in the Storage
		global time_count
		time_count += 1

		r = range(self.layer_n)
		layer_index = random.choice(r)
		self.addLBA(layer_index, LBA_in, max_LBA, min_LBA)

		"""
		# Layers with maximum and minimum temperature respectively
		max_layer_index = self.temperature.index(max(self.temperature))
		min_layer_index = self.temperature.index(min(self.temperature))

		if data_type == 2: # Hot data -> Write to the layer with minimum temperature
			layer_index = min_layer_index
			self.addLBA(layer_index, LBA_in, max_LBA, min_LBA)
		elif data_type == 1: # Warm data -> Write to a random layer
			r = range(self.layer_n)
			r.remove(max_layer_index)
			try:
				r.remove(min_layer_index)
			except:
				pass
			layer_index = random.choice(r)
			self.addLBA(layer_index, LBA_in, max_LBA, min_LBA)
		elif data_type == 0: # Cold data -> Write to the layer with maximum temperature
			layer_index = max_layer_index
			self.addLBA(layer_index, LBA_in, max_LBA, min_LBA)
		"""

		# Update Temperature
		self.RiseTemperature(layer_index)


class initPageTable():
	def __init__(self):
		self.relationships = {} # Record Relations between LBA and the stored layer, stored time point
	
	def update(self, LBA_in, Address_in, time): # update the content of Page Table
		self.relationships[LBA_in] = [Address_in, time]

	def check(self, LBA): # Check whether if a request(LBA) is inside Page Table or not. Yes: return the Hardware Address(Layer) and write time point. No: return None
		try:
			return self.relationships[LBA][0], self.relationships[LBA][1]
		except:
			return None, None

#TLB = initTLB()
PageTable = initPageTable()

if __name__ == '__main__':
	parm = parseArgument(sys.argv) # python experiment.py [trace file] [output file]

	global PageTable, cycle_times, max_written_sector, req_count #, TLB
	#BF = initBF()	# declare Bloom Filters
	Storage = initStorage() # declare Storage System

	trace_cycle = 0
	while True:
		trace_cycle += 1
		if trace_cycle > cycle_times:
			break

		request = readOneTrace(parm) # Read a Request from trace
		while request != None: # Keep reading requests

			if request['type'] == 'r': # Read Request
				pass
				#hardAddress = TLB.check(request)
			elif request['type'] == 'w': # Write Request
				#data_type = BF.HotOrCold(request) # Determine Hot or Warm or Cold
				#print(data_type)

				#Address, W_time = TLB.check(request) # Check if the TLB has LBA of the request

				for i in range(request['length']):
					LBA_now = request['LBA']+i
					Address, W_time = PageTable.check(LBA_now)
					if Address == None:
						Storage.NewLBAIn(LBA_now, request['LBA']+request['length']-1, request['LBA'])
					else:
						Storage.OldLBAIn(LBA_now, Address, W_time, request['LBA']+request['length']-1, request['LBA'])
				
			req_count += 1

			if req_count > 100000:
				if max_written_sector > 0:
					f_sectors.write(str(max_written_sector) + '\n')
				req_count = 0
			
			Storage.DownTemperature()
			request = readOneTrace(parm) # Read a Request from trace
		parm['traceFile'].seek(0)

	"""
	sector_times = []
	for i in range(Storage.layer_n):
		sector_times += Storage.layer_sectors[i]
	sector_write_times = {}
	for write_times in sector_times:
		if write_times not in sector_write_times:
			sector_write_times[write_times] = 1
		else:
			sector_write_times[write_times] += 1

	f_sectors.write("Write_Times Sector_numbers\n")
	for key in sorted(sector_write_times.iterkeys()):
		f_sectors.write(str(key) + ' ' + str(sector_write_times[key]) + '\n')
	"""