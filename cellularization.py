#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 22 18:04:16 2018

@author: yuchiunwang
"""

from skimage import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import scipy.optimize as opt

def fitted_func(t, a, b, tau):
	return (a - b * np.exp(-t / tau))

def derivative_fitted_func(t, b, tau):
	return ( (b / tau) * np.exp(-t/ tau))

Folder = '20150601_01_sqhGFP'

path = '/Users/cib/Documents/CF formation imaging/Exp27/E3TL/' + Folder
tif_filename = path + '/cellu_front_y_t.tif'
txt_filename = path + '/time_pixel_scales.txt'
DF_txt = pd.read_csv(txt_filename, sep=' ')
type(DF_txt)
t_step_size = '%.1f'%(DF_txt.iloc[0,0])
pixel_size = '%.3f'%(DF_txt.iloc[0,1])

tif = io.imread(tif_filename)
type(tif)

[rows, cols] = np.shape(tif)
# plt.figure()
# plt.imshow(tif[:,:], cmap="gray")
        
DF = pd.DataFrame(tif)
print(DF.columns)
Y = len(DF)
X = len(DF.columns)
cdn = []

""" Same as below
for i, y in enumerate(np.arange(0, Y, 1)):
   for j, x in enumerate(np.arange(0, X, 1)):
       if DF.iloc[i, j] == 255:
           edge = (i, j)
           cdn.append(edge)
DF_edge = pd.DataFrame(cdn)       
"""   

for y in np.arange(0, Y, 1):
    for x in np.arange(0, X, 1):
        if DF.iloc[y, x] == 255:
            edge = (y, x)
            cdn.append(edge)
            break;
DF_edge = pd.DataFrame(cdn)    

DF_edge = DF_edge.rename(columns = {0:'time', 1: 'position'})
DF_edge['position'] = DF_edge['position'] - DF_edge['position'].min(axis = 0)
pos_max = DF_edge['position'].max(axis = 0)
time_pos_max = DF_edge[DF_edge['position'] == pos_max]
time_end = time_pos_max['time'].max(axis = 0)
DF_edge_max = DF_edge[DF_edge['time'] <= time_end]

plt.figure()
plt.subplot(321)
ax1 = plt.plot(DF_edge['time'],DF_edge['position'], 'x')
ax2 = plt.plot(DF_edge_max['time'],DF_edge_max['position'], '.')
plt.title("No fit")

plt.subplot(322)
z = np.polyfit(DF_edge_max['time'], DF_edge_max['position'], 1)
#print(z)
p = np.poly1d(z)
#print(p(10))
xp = np.linspace(0, time_end, 1000)
ax = plt.plot(DF_edge_max['time'],DF_edge_max['position'], '.', xp, p(xp), '-')
plt.title("Linear fit")

plt.subplot(323)
z = np.polyfit(DF_edge_max['time'], DF_edge_max['position'], 2)
#print(z)
p = np.poly1d(z)
#print(p(10))
xp = np.linspace(0, time_end, 1000)
ax = plt.plot(DF_edge_max['time'],DF_edge_max['position'], '.', xp, p(xp), '-')
plt.title("Second-order polynomial fit")

plt.subplot(324)
z = np.polyfit(DF_edge_max['time'], DF_edge_max['position'], 3)
#print(z)
p = np.poly1d(z)
#print(p(10))
xp = np.linspace(0, time_end, 1000)
ax = plt.plot(DF_edge_max['time'],DF_edge_max['position'], '.', xp, p(xp), '-')
plt.title("Third-order polynomial fit")

plt.subplot(325)
z = np.polyfit(DF_edge_max['time'], DF_edge_max['position'], 4)
#print(z)
p = np.poly1d(z)
#print(p(10))
xp = np.linspace(0, time_end, 1000)
ax = plt.plot(DF_edge_max['time'],DF_edge_max['position'], '.', xp, p(xp), '-')
plt.title("Fourth-order polynomial fit")

plt.subplot(326)
opt_parameters, pcov = opt.curve_fit(fitted_func, 
                                     DF_edge_max['time'].astype('float'), 
                                     DF_edge_max['position'].astype('float'))
tp = np.linspace(0, time_end, 1000)
ax = plt.plot(DF_edge_max['time'],DF_edge_max['position'], '.', 
              tp, fitted_func(tp, *opt_parameters), '-')
plt.title("Exponential fit")

plt.tight_layout()

print(opt_parameters)
print("tau = %.3f" % opt_parameters[2])

DF_edge_max['time_scaled'] = DF_edge_max['time'] * float(t_step_size) 
DF_edge_max['position_scaled'] = DF_edge_max['position'] * float(pixel_size) 
time_end_scaled = time_end * float(t_step_size) 

#plt.figure()
#plt.subplot(121)
#z = np.polyfit(DF_edge_max['time_scaled'], DF_edge_max['position_scaled'], 3)
#print(z)
#p = np.poly1d(z)
#xp = np.linspace(0, time_end_scaled, 1000)
#ax = plt.plot(DF_edge_max['time_scaled'],DF_edge_max['position_scaled'], '.', xp, p(xp), '-')
#
#plt.subplot(122)
#p2 = np.polyder(p)
#print(p2)
#xpxp = np.linspace(0, time_end_scaled, 1000)
#ax = plt.plot(xpxp, p2(xpxp), '-')
#Derivative = p2(xpxp)
#print(Derivative)
#
#
#DF_edge_max['velocity'] = p2(DF_edge_max['time_scaled'])
#DF_v_t = pd.DataFrame({'timeframe': np.arange(1, time_end + 1 , 1),
#                      'actual_time': np.arange(float(t_step_size), time_end_scaled + float(t_step_size), float(t_step_size)),
#                      'velocity': p2(np.arange(float(t_step_size), time_end_scaled + float(t_step_size), float(t_step_size)))})
#
#os.chdir(path) 
#DF_v_t.to_excel('time_velocity.xlsx')   

plt.figure()
plt.subplot(121)
real_opt_parameters, pcov = opt.curve_fit(fitted_func, 
                                          DF_edge_max['time_scaled'], 
                                          DF_edge_max['position_scaled'])
tp = np.linspace(0, time_end_scaled, 1000);
ax = plt.plot(DF_edge_max['time_scaled'],DF_edge_max['position_scaled'], '.',
              tp, fitted_func(tp, *real_opt_parameters), '-')

plt.subplot(122)
ax = plt.plot(tp, derivative_fitted_func(tp, real_opt_parameters[1], 
                                         real_opt_parameters[2]), '-')

DF_edge_max.loc[:,'velocity'] = derivative_fitted_func(DF_edge_max['time_scaled'], 
                                                 real_opt_parameters[1], 
                                                 real_opt_parameters[2])

DF_v_t = pd.DataFrame({'timeframe': np.arange(1, time_end + 1 , 1),
                      'actual_time': np.arange(float(t_step_size), time_end_scaled + float(t_step_size), float(t_step_size)),
                      'velocity': derivative_fitted_func(np.arange(float(t_step_size), 
                                                                   time_end_scaled + float(t_step_size), 
                                                                   float(t_step_size)), 
                                                         real_opt_parameters[1], real_opt_parameters[2])})


DF_v_t.to_excel(os.path.join(path, 'time_velocity_expo.xlsx'))
plt.show()





