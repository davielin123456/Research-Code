import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import math
import sys

x = list(range(1, 17))
TPC_c = "261.662876041 269.579840046 204.661439969 320.327544073 248.301142996 302.84347249 227.716633859 311.174734286 229.588776617 229.195118203 265.685541479 276.726099409 267.951342648 246.264388601 303.342844798 233.855087417".strip().split(' ') # TPC_c 13
TPC_c = [float(i) for i in TPC_c]
TPC_e = "262.438246373 262.443783767 262.44076337 262.443280368 262.444287167 262.44076337 262.442273569 262.443280368 262.44126677 262.443783767 262.442776968 262.443280368 262.442273569 262.443280368 262.443783767 262.443280368".strip().split(' ') # TPC_e 13
TPC_e = [float(i) for i in TPC_e]
TPC_r = "262.900331441 263.451553899 262.834386106 262.436197099 261.954947172 262.578155759 262.294238438 262.60735293 261.049331464 262.030457098 261.992198736 262.726658612 262.88170566 261.35841876 264.100939259 261.810471515".strip().split(' ') # TPC_r 13
TPC_r = [float(i) for i in TPC_r]

CAMUSP_c = "166.339599843 370.953375937 119.161501713 268.374148757 127.194247599 152.334018838 244.594059573 303.827065641 165.315181852 406.349408681 232.979626206 201.994379923 461.086050379 414.97264219 367.117975114 -27.1450199653".strip().split(' ') # CAMUSP_c 27
CAMUSP_c = [float(i) for i in CAMUSP_c]
CAMUSP_e = "247.714629464 247.712615866 247.713622665 247.713119265 247.714629464 247.715132864 247.713622665 247.712615866 247.714126065 247.715132864 247.715132864 247.712615866 247.715132864 247.714629464 247.713622665 247.71261586".strip().split(' ') # CAMUSP_e 27
CAMUSP_e = [float(i) for i in CAMUSP_e]
CAMUSP_r = "247.090501013 248.268455853 249.17457496 249.180112355 245.753975329 248.696345431 248.848372081 247.196214909 248.384741138 247.933191783 244.953570118 247.652294859 247.040161063 246.21055868 246.989821112 249.930681015".strip().split(' ') # CAMUSP_r 27
CAMUSP_r = [float(i) for i in CAMUSP_r]

CAMRES_c = "474.192903585 249.051502509 230.151871522 237.534728651 347.164569286 236.887356888 158.220109562 235.765279394 188.903819542 166.989832325 296.498415982 315.797746177 83.1184409309 255.848906014 246.33817918 212.362739839".strip().split(' ') # CAMRES c 17
CAMRES_c = [float(i) for i in CAMRES_c]
CAMRES_e = "247.065985205 247.064475006 247.065985205 247.064475006 247.064978406 247.065481805 247.063468207 247.063468207 247.066488604 247.063971607 247.064475006 247.065481805 247.063468207 247.063468207 247.066488604 247.063468207".strip().split(' ') # CAMRES_e 17
CAMRES_e = [float(i) for i in CAMRES_e]
CAMRES_r = "246.348505775 247.305468233 245.827487288 246.8312659 246.045459274 247.490215851 247.406651533 246.19144513 247.780677365 247.19673394 246.756259374 247.783194362 247.342216397 248.400865554 247.652813891 246.875565056".strip().split(' ') # CAMRES_r 17
CAMRES_r = [float(i) for i in CAMRES_r]

plt.scatter(x, TPC_c, s=100, marker="x", c="b")
plt.scatter(x, TPC_r, s=100, marker="*", c="m")
plt.scatter(x, TPC_e, s=100, marker="o", c="g")
blue_line = mlines.Line2D([], [], color='blue', marker='x', linestyle='None', markersize=6, label='Nothing')
m_line = mlines.Line2D([], [], color='m', marker='*', linestyle='None', markersize=6, label='Random')
e_line = mlines.Line2D([], [], color='g', marker='o', linestyle='None', markersize=6, label='OARS')
line = plt.hlines(300, 1, 16, colors="r", linestyles="dashed", label="crystallization point")

plt.legend(handles=[blue_line, m_line, e_line, line])
plt.xlabel("Layer")
plt.ylabel("Temperature($^\circ$C)")
plt.savefig("/home/yuchenlin/pcm_dac2019/figures/TPC_PCMLayers_temperatures.eps")
plt.show()

plt.scatter(x, CAMUSP_c, s=100, marker="x", c="b")
plt.scatter(x, CAMUSP_r, s=100, marker="*", c="m")
plt.scatter(x, CAMUSP_e, s=100, marker="o", c="g")
blue_line = mlines.Line2D([], [], color='blue', marker='x', linestyle='None', markersize=6, label='Nothing')
m_line = mlines.Line2D([], [], color='m', marker='*', linestyle='None', markersize=6, label='Random')
e_line = mlines.Line2D([], [], color='g', marker='o', linestyle='None', markersize=6, label='OARS')
line = plt.hlines(300, 1, 16, colors="r", linestyles="dashed", label="crystallization point") 
plt.legend(handles=[blue_line, m_line, e_line, line], loc=3)
plt.xlabel("Layer")
plt.ylabel("Temperature($^\circ$C)")
plt.savefig("/home/yuchenlin/pcm_dac2019/figures/CAMUSP_PCMLayers_temperatures.eps")
plt.show()

plt.scatter(x, CAMRES_c, s=100, marker="x", c="b")
plt.scatter(x, CAMRES_r, s=100, marker="*", c="m")
plt.scatter(x, CAMRES_e, s=100, marker="o", c="g")
blue_line = mlines.Line2D([], [], color='blue', marker='x', linestyle='None', markersize=6, label='Nothing')
m_line = mlines.Line2D([], [], color='m', marker='*', linestyle='None', markersize=6, label='Random')
e_line = mlines.Line2D([], [], color='g', marker='o', linestyle='None', markersize=6, label='OARS')
plt.hlines(300, 1, 16, colors="r", linestyles="dashed", label="crystallization point")
plt.legend(handles=[blue_line, m_line, e_line, line], loc=3)
plt.xlabel("Layer")
plt.ylabel("Temperature($^\circ$C)")
plt.savefig("/home/yuchenlin/pcm_dac2019/figures/CAMRES_PCMLayers_temperatures.eps")
plt.show()