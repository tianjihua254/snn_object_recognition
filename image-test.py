#!/bin/ipython
import numpy as np
import cv2
import sys
import pyNN.nest as sim
import pathlib as plb
import time

import common as cm
import network as nw
import visualization as vis
import time

args = cm.parse_args()

t1 = time.clock()
weights_dict, feature_imgs_dict = nw.train_weights(args.feature_dir)
t2 = time.clock()
print('Training weights took {} s'.format(t2 - t1))

if args.plot_weights:
    vis.plot_weights(weights_dict)
    sys.exit(0)

# The training part is done. Go on with the "actual" simulation
sim.setup(threads=4)

target_img = cm.read_and_prepare_img(args.target_name, args.filter)
cv2.imwrite('{}_{}_edges.png'.format(plb.Path(args.target_name).stem,
                                     args.filter), target_img)

layer_collection = {} # layer name -> list of S1 layers
# TODO make an extra entry here with the spike source layer. This is needed to
#      set new firing rates when processing a video
t1 = time.clock()
layer_collection['S1'] = nw.create_S1_layers(target_img, weights_dict, args)
t2 = time.clock()
print('S1 creation took {} s'.format(t2 - t1))
if not args.no_c1:
    print('Create C1 layers')
    layer_collection['C1'] = nw.create_C1_layers(layer_collection['S1'],
                                                 args.refrac_c1)
    print('C1 creation took {} s'.format(time.clock() - t2))

for layer_dict in layer_collection.values():
    for layers in layer_dict.values():
        for layer in layers:
            layer.population.record('spikes')

print('========= Start simulation =========')
start_time = time.clock()
sim.run(args.sim_time)
end_time = time.clock()
print('========= Stop  simulation =========')
print('Simulation took', end_time - start_time, 's')

t1 = time.clock()
if args.reconstruct_s1_img:
    vis.reconstruct_S1_features(target_img, layer_collection, feature_imgs_dict,
                                args)
    print('S1 visualization took {} s'.format(time.clock() - t1))

t1 = time.clock()
if args.reconstruct_c1_img:
    vis.reconstruct_C1_features(target_img, layer_collection, feature_imgs_dict,
                                args)
    print('C1 visualization took {} s'.format(time.clock() - t1))


t1 = time.clock()
if args.plot_spikes:
    vis.plot_spikes(layer_collection, args)
    print('Plotting spiketrains took {} s'.format(time.clock() - t1))

sim.end()
