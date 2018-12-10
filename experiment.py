import sys
import os
import pprint
import time
import hashlib
import random
import time
from random import shuffle
import collections

f_temp = open(sys.argv[2], "w")
#f_hot_degree = open("Hot_Degree.txt", "w")
f_sectors = open(sys.argv[8], "w")
f_redirect = open(sys.argv[9], "w")

req_count = 0
max_written_sector = 0

#adjust_ambient_T = 0
#adjust_ambient_C = 0

one_second = 2*10**5 # 2*10**5  0.01 record
one_second_count = 0

hot = 0
warm = 0
cold = 0
total = 0
up = 15
down = 20
threshold1 = 200
threshold2 = 20
cycle_times = 10
redirect = 0
hot_redirect = 0
cold_redirect = 0
HD_threshold = 100
down_scale = 4.5

def parseArgument(argv):
	global up, down, cycle_times, threshold1, threshold2, HD_threshold, down_scale
	parameter = {}
	parameter['traceFile'] = open(argv[1], 'r')
	cycle_times = int(argv[3])
	threshold1 = int(argv[4])
	threshold2 = int(argv[5])
	HD_threshold = int(argv[6])
	down_scale = float(argv[7])
	
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

def FindMedian(numbers_in):
	length = len(numbers_in)
	numbers = numbers_in[:]
	numbers.sort()
	if length % 2 == 0:
		return (numbers[length/2] + numbers[length/2-1])/2
	else:
		return numbers[(length-1)/2]

class initStorage():
	def __init__(self):
		self.total_space = 128*1024*1024*2 # based on LBA(sectors)
		self.layer_n = 16 # number of layers
		self.layer_size = self.total_space / self.layer_n # numbers of block in a layer (50GB/layer), 1 block = 512 bytes

		self.layers = [] # Storage System
		for i in range(self.layer_n):
			self.layers.append({})

		
		self.layer_sectors = [] # record the actual situations
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
		

	def addLBA(self, layer_index, LBA_in, data_type):
		global PageTable, max_written_sector #, TLB

		try:
			inside = self.layers[layer_index][LBA_in]
		except:
			inside = 3

		try:
			sector_now = self.layer_sectors_map[layer_index][LBA_in]
		except:
			sector_now = None

		if inside == 3: # new LBA
			PageTable.update(LBA_in, layer_index)
			self.layers[layer_index][LBA_in] = 4

			r = range(self.layer_size)
			sector_now = random.choice(r)
			self.layer_sectors[layer_index][sector_now] += 1
			self.layer_sectors_map[layer_index][LBA_in] = sector_now
		else: # old LBA
			self.layers[layer_index][LBA_in] = data_type
			self.layer_used[layer_index] += 1
			PageTable.update(LBA_in, layer_index)

			self.layer_sectors[layer_index][sector_now] += 1

		if self.layer_sectors[layer_index][sector_now] > max_written_sector:
			max_written_sector = self.layer_sectors[layer_index][sector_now]

	def OldLBAIn(self, LBA_in, data_type, OldAddress, hot_degree): # the current LBA exists in the Storage
		global hot_redirect, cold_redirect, HD_threshold # Time point

		if data_type == 2: # Hot data
			if hot_degree > HD_threshold and OldAddress == self.temperature.index(max(self.temperature)): # too old -> Mode LBA
				layer_index = self.temperature.index(min(self.temperature))
				try:
					del self.layers[OldAddress][LBA_in]
					del self.layer_sectors_map[OldAddress][LBA_in]
				except:
					pass
				self.addLBA(layer_index, LBA_in, data_type)
				hot_redirect += 1
			else: # Not too old -> write to the same layer
				layer_index = OldAddress
				self.addLBA(OldAddress, LBA_in, data_type)

		elif data_type == 1: # Warm data -> Write to the same layer
			layer_index = OldAddress
			self.addLBA(OldAddress, LBA_in, data_type)
		elif data_type == 0: # Cold data -> Write to the layer with maximum temperature
			"""
			layer_index = self.temperature.index(max(self.temperature))
			if layer_index != OldAddress:
				try:
					del self.layers[OldAddress][LBA_in]
					del self.layer_sectors_map[OldAddress][LBA_in]
				except:
					pass
				cold_redirect += 1
			self.addLBA(layer_index, LBA_in, data_type)
			"""
			layer_index = OldAddress
			self.addLBA(OldAddress, LBA_in, data_type)

		# Update the temperatures of each layer
		self.RiseTemperature(layer_index)

	def NewLBAIn(self, LBA_in): # the current LBA doesn't exist in the Storage

		# Layers with maximum and minimum temperature respectively
		max_layer_index = self.temperature.index(max(self.temperature))

		r = range(self.layer_n)
		r.remove(max_layer_index)
		layer_index = random.choice(r)

		self.addLBA(layer_index, LBA_in, 3)

		# Update Temperature
		self.RiseTemperature(layer_index)
		

class initBF():
	def __init__(self):
		global threshold1, threshold2
		self.counter_n = 1000 #193449 The number of counters inside the Bloom Filter
		self.counter_size = 8 #!!! The size of each counter inside the Bloom Filter 
		self.counters = [] # content of each counters, each element is a integer
		for i in range(self.counter_n):
			self.counters.append([0]*self.counter_size)
		self.index_now = 0 # which column now
		self.index_times = 0 # record the number of coming requests to the current column
		self.index_max = 100 # maximum times in a single column !!!
		self.index_clean = 0 # which column to clean
		self.index_weight = [128, 64, 32, 16, 8, 4, 2, 1]
		self.clean_times = 0
		self.clean_max = self.counter_size * self.index_max #!
		self.threshold_max = self.counter_size * self.index_max
		self.T1 = threshold1 # !!! initial value of threshold between Hot and Warm
		self.T2 = threshold2 # !!! initial value of threshold between Warm and Cold
		self.lowest = 5
		self.HW_record = [] # Record the Hot Degree of requests into Hot and Warm
		self.WC_record = [] # Record the Hot Degree of requests into Warm and Cold

	def FindBFCounter(self, request): # Use SHA to find the counters of the request

		LBA = str(request['LBA'])
		t1 = hashlib.sha1()
		t2 = hashlib.sha256()
		t3 = hashlib.sha224()

		t1.update(LBA)
		t2.update(LBA)
		t3.update(LBA)

		h1 = int(t1.hexdigest(), 16)
		h2 = int(t2.hexdigest(), 16)
		h3 = int(t3.hexdigest(), 16)

		selected_counters = []
		selected_counters.append(h1%self.counter_n)
		selected_counters.append(h2%self.counter_n)
		selected_counters.append(h3%self.counter_n)

		return selected_counters

	def update_BF(self, request): # update the content of BF
		selected_counters = self.FindBFCounter(request) # selected counters that are going to be recorded
		Hot_degree = 0
		for i in selected_counters: # Update the content of the counters
			self.counters[i][self.index_now] = 1
			for j in range(self.counter_size):
				Hot_degree += self.counters[i][j] * self.index_weight[j] # To determine Hot or Cold

		self.index_times += 1 # the column has one more requests on it
		self.clean_times += 1

		if self.index_times >= self.index_max: # the requests on the column exceed the limit, turn to the next column
			# Change Col
			if self.index_now >= self.counter_size-1:
				self.index_now = 0
			else:
				self.index_now += 1
			self.index_times = 0
			for weight in self.index_weight:
				if weight == 128:
					weight = 1
				else:
					weight *= 2

		# Clean one Column
		if self.clean_times >= self.clean_max:
			if self.clean_max == self.counter_size * self.index_max:
				self.clean_max = self.index_max
			for i in range(self.counter_n):
				self.counters[i][self.index_clean] = 0
			self.index_clean += 1
			if self.index_clean == self.counter_size:
				self.index_clean = 0
			self.clean_times = 0

		#f_hot_degree.write(str(Hot_degree) + '\n')
		return Hot_degree

	def HotOrCold(self, request): # 2:Hot / 1:Warm / 0:Cold
		global hot, warm, cold, total, up, down, threshold1, threshold2
		total += 1

		Hot_degree = self.update_BF(request) # get the hot degree of the request(LBA)

		data_type = 3
		#print(Hot_degree, self.T1, self.T2)]
		if Hot_degree >= self.T1: # Hot Data
			self.HW_record.append(Hot_degree)
			data_type = 2
			hot += 1
		elif Hot_degree < self.T1 and Hot_degree > self.T2: # Warm Data
			self.HW_record.append(Hot_degree)
			self.WC_record.append(Hot_degree)
			data_type = 1
			warm += 1
		elif Hot_degree <= self.T2: # Cold Data
			self.WC_record.append(Hot_degree)
			data_type = 0
			cold += 1

		return data_type, Hot_degree

class initPageTable():
	
	def __init__(self):
		self.relationships = {} # Record Relations between LBA and the stored layer, stored time point
	
	def update(self, LBA_in, Address_in): # update the content of Page Table
		global redirect
		try:
			if self.relationships[LBA_in] != Address_in:
				redirect += 1
		except:
			pass
		self.relationships[LBA_in] = Address_in

	def check(self, LBA): # Check whether if a request(LBA) is inside Page Table or not. Yes: return the Hardware Address(Layer) and write time point. No: return None
		try:
			return self.relationships[LBA]
		except:
			return None

#TLB = initTLB()
PageTable = initPageTable()

if __name__ == '__main__':
	parm = parseArgument(sys.argv) # python experiment.py [trace file] [output file]

	global hot, warm, cold, total, cycle_times, redirect, hot_redirect, cold_redirect, max_written_sector, req_count

	global PageTable #, TLB
	BF = initBF()	# declare Bloom Filters
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
				data_type, hot_degree = BF.HotOrCold(request) # Determine Hot or Warm or Cold

				for i in range(request['length']):
					LBA_now = request['LBA']+i
					Address = PageTable.check(LBA_now)
					if Address == None:
						Storage.NewLBAIn(LBA_now)
					else:
						Storage.OldLBAIn(LBA_now, data_type, Address, hot_degree)

			req_count += 1

			if req_count > 100000:
				if max_written_sector > 0:
					f_sectors.write(str(max_written_sector) + '\n')
				req_count = 0


			Storage.DownTemperature()
			request = readOneTrace(parm) # Read a Request from trace
		parm['traceFile'].seek(0)

	max_layer_index = Storage.temperature.index(max(Storage.temperature))
	max_hot = 0
	max_warm = 0
	max_cold = 0
	total = len(Storage.layers[max_layer_index])
	for LBA in Storage.layers[max_layer_index]:
		if Storage.layers[max_layer_index][LBA] == 2:
			max_hot += 1
		elif Storage.layers[max_layer_index][LBA] == 1:
			max_warm += 1
		elif Storage.layers[max_layer_index][LBA] == 0:
			max_cold += 1
	"""
	sector_write_times = {}
	for i in range(Storage.layer_n):
		for write_times in Storage.layer_sectors[i]:
			if write_times not in sector_write_times:
				sector_write_times[write_times] = 1
			else:
				sector_write_times[write_times] += 1

	f_sectors.write("Write_Times Sector_numbers\n")
	for key in sorted(sector_write_times.iterkeys()):
		f_sectors.write(str(key) + ' ' + str(sector_write_times[key]) + '\n')
	"""
	f_redirect.write("Page Table Redirect Times: " + str(redirect))
