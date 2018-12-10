import matplotlib.pyplot as plt
import math
import sys

fe = open(sys.argv[1], "r")
fc = open(sys.argv[2], "r")
fm = open(sys.argv[3], "r")

e = []
c = []
m = []

counter = 0
MAX = 0


count = 0
x = []
line = fm.readline() # Description Line
line = fm.readline() # 0 write time

for line in fm.readlines():
	write_time = int(line.strip())
	count += 1
	x.append(count)
	m.append(write_time)
line_m, = plt.plot(x, m, color='m', label="Random") #, marker="*", c="m"


count = 0
x = []
line = fe.readline() # Description Line
line = fe.readline() # 0 write time

for line in fe.readlines():
	write_time = int(line.strip())
	count += 1
	x.append(count)
	e.append(write_time)
line_e, = plt.plot(x, e, color='g', label="OARS") #, marker="o", c="g"


count = 0
x = []
line = fc.readline() # Description Line
line = fc.readline() # 0 write time

for line in fc.readlines():
	write_time = int(line.strip())
	count += 1
	x.append(count)
	c.append(write_time)
line_c, = plt.plot(x, c, color='b', label="Nothing") #, marker="x", c="b"


plt.xlabel("# of IO Requests(x10^7)")
plt.ylabel("Most written times for one block")
plt.legend(handles=[line_e, line_c, line_m], loc=5)

plt.gcf().subplots_adjust(left=0.15)

plt.hlines(1000000, 0, count, colors="r", linestyles="dashed")
plt.savefig("/home/yuchenlin/pcm_dac2019/figures/" + str(sys.argv[4]))
plt.show()