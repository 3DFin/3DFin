'''
-----------------------------------------------------------------------------
------------------        General Description          ----------------------
-----------------------------------------------------------------------------

This  Python script implements an algorithm to detect the trees present
in a ground-based 3D point cloud from a forest plot, 
and compute individual tree parameters: tree height, tree location, 
diameters along the stem (including DBH), and stem axis. 

The input point cloud will be in .LAS/.LAZ format and can contain extra fields (.LAS standard or not) 
This algorithm is mainly based on rules, although it uses clusterization in some stages.
Also, the input point cloud can come from terrestrail photogrammetry, TLS or mobile (e.g. hand-held) LS,
a combination of those, and/or a combination of those with UAV-(LS or SfM), or ALS. 

The algorithm may be divided in three main steps:

    1.	Identification of stems in an user-defined horizontal stripe.
    2.	Tree individualization based on point-to-stem-axis distances.
    3.	Robust computation of stem diameter at different section heights.

-----------------------------------------------------------------------------
------------------   Heights in the input .LAS file    ----------------------
-----------------------------------------------------------------------------
    
    This script uses Z and Z0 to describe coordinates referring to 'heights'. 
         - Z refers to the originally captured elevation in the point cloud
         - Z0 refers to a normalized height (elevation from the ground). 
    This script needs normalized heights to work, but also admits elevation 
    coordinates and preserves them in the outputs, as additional information
    Then, the input point cloud might include just just Z0, or both Z and Z0. 
    
    Before running script, it should be checked where the normalized heights are stored in the input file: 'z' or another field. 
    The name of that field is one of the basic input parameters:
        - field_name_z0: Name of the field containing the height normalized data in the .LAS file. 
    If the normalized heights are stored in the z coordinate of the .LAS file, the value of field_name_z0 will be ‘z’ (lowercase).


-----------------------------------------------------------------------------
------------------                Outputs              ----------------------
-----------------------------------------------------------------------------    

After all computations are complete, the following files are output:
Filenames are: [original file name] + [specific suffix] + [.txt or .las]

LAS files (mainly for checking visually the outputs). 
They can be open straightaway in CloudCompare, where 'colour visualization' of fields with additional information is straightforward 

•	[original file name]_tree_ID_dist_axes: LAS file containing the original point cloud and a scalar field that contains tree IDs.
•	[original file name]_axes: LAS file containing stem axes coordinates.
•	[original file name]_circ: LAS file containing circles (sections) coordinates.
•	[original file name]_stripe: LAS file containing the stems obtained from the stripe during step 1.
•	[original file name]_tree_locator: LAS file containing the tree locators coordinates.
•	[original file name]_tree_heights: LAS file containing the highest point from each tree.

Text files with tabular data:
    Files contain TAB-separated information with as many rows as trees detected in the plot and as many columns as stem sections considered
    All units are m or points. 
    _outliers and _check_circle have no units

•	[original file name]_dbh_and_heights: Text file containing tree height, tree location and DBH of every tree as tabular data.
•	[original file name]_X_c: Text file containing the (x) coordinate of the centre of every section of every tree as tabular data.
•	[original file name]_Y_c: Text file containing the (y) coordinate of the centre of every section of every tree as tabular data.
•	[original file name]_R: Text file containing the radius of every section of every tree as tabular data.
•	[original file name]_outliers: Text file containing the ‘outlier probability’ of every section of every tree as tabular data.
•	[original file name]_sector_perct: Text file containing the sector occupancy of every section of every tree as tabular data.
•	[original file name]_check_circle: Text file containing the ‘check’ status of every section of every tree as tabular data.
•	[original file name]_n_points_in: Text file containing the number of points within the inner circle of every section of every tree as tabular data.
•	[original file name]_sections: Text file containing the sections as a vector.
  
'''

###################### -------------------------------------------------------- ######################
###################### --------------------    imports     -------------------- ######################
###################### -------------------------------------------------------- ######################

import os
import sys
import configparser
import timeit
import laspy
import jakteristics as jak
import numpy as np
from tkinter import filedialog
from copy import deepcopy
from scipy import optimize as opt
from scipy.cluster import hierarchy as sch
from scipy.spatial import distance_matrix
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA

import gui
from functions import *

### Reading the config file ###
config = configparser.ConfigParser()
config.read('config.ini')

tree_id_field = 4 # Which column contains tree ID field  - NON MODIFIABLE
n_digits = 5 # Number of digits for voxel encoding.


#-------------------------------------------------------------------------------------------------
# Input data.
#-------------------------------------------------------------------------------------------------

# --- Import file --- #

filename_las = filedialog.askopenfilename()


#################################################################
#################################################################
#   SCRIPT   ####################################################
#################################################################
#################################################################


t_t = timeit.default_timer()
    
# Number of points and area occuped by the plot. 
print('---------------------------------------------')
print('1.-Analyzing cloud size...')
print('---------------------------------------------')

# Read .LAS file. It must contain a Z0 field (normalized height). 
entr = laspy.read(filename_las)
coords = np.vstack((entr.x, entr.y, entr.z, entr[config['basic']['z0_name']])).transpose()

_, _, voxelated_ground = voxelate(coords[coords[:, 3] < 0.5, 0:3], 1, 2000, n_digits, with_n_points = False)

print('   This cloud has',"{:.2f}".format(coords.shape[0]/1000000),'millions points')
print('   Its area is ',voxelated_ground.shape[0],'m^2')
del voxelated_ground

print('---------------------------------------------')
print('2.-Extracting the stripe and peeling the stems...')
print('---------------------------------------------')

stripe = coords[(coords[:, 3] > float(config['basic']['lower_limit'])) & (coords[:, 3] < float(config['basic']['upper_limit'])), 0:4]
clust_stripe = verticality_clustering_iteration(stripe, float(config['advanced']['verticality_scale_stripe']), float(config['advanced']['verticality_thresh_stripe']), float(config['advanced']['epsilon_stripe']), int(config['advanced']['number_of_points']), int(config['basic']['number_of_iterations']), float(config['advanced']['res_xy_stripe']), float(config['advanced']['res_z_stripe']), n_digits)       
del stripe

print('---------------------------------------------')
print('3.-Computing distances to axes and individualizating trees...')
print('---------------------------------------------')
                                                                                       
assigned_cloud, tree_vector, tree_heights = individualize_trees(coords, clust_stripe, float(config['advanced']['res_xy']), float(config['advanced']['res_z']), float(config['advanced']['maximum_d']), float(config['advanced']['height_range']), int(config['advanced']['minimum_points']), float(config['intermediate']['distance_to_axis']), float(config['advanced']['maximum_dev']), filename_las, float(config['advanced']['res_heights']), tree_id_field = -1)     

print('  ')
print('---------------------------------------------')
print('4.-Exporting .LAS files including complete cloud and stripe...')
print('---------------------------------------------')

# Stripe
t_las = timeit.default_timer()
las_stripe = laspy.create(point_format = 2, file_version='1.2')
las_stripe.x = clust_stripe[:, 0]
las_stripe.y = clust_stripe[:, 1]
las_stripe.z = clust_stripe[:, 2]

las_stripe.add_extra_dim(laspy.ExtraBytesParams(name = "tree_ID", type = np.int32))
las_stripe.tree_ID= clust_stripe[:, -1]
las_stripe.write(filename_las[:-4]+"_stripe.las")
del clust_stripe

# Whole cloud including new fields
entr.add_extra_dim(laspy.ExtraBytesParams(name="dist_axes", type=np.float64))
entr.add_extra_dim(laspy.ExtraBytesParams(name="tree_ID", type=np.int32))
entr.dist_axes = assigned_cloud[:, 5]
entr.tree_ID = assigned_cloud[:, 4]
entr.write(filename_las[:-4]+"_tree_ID_dist_axes.las")
elapsed_las = timeit.default_timer() - t_las
print('Total time:',"   %.2f" % elapsed_las,'s')


# stem extraction and curation 
print('---------------------------------------------')
print('5.-Extracting and curating stems...')
print('---------------------------------------------')

xyz0_coords = assigned_cloud[(assigned_cloud[:, 5] < float(config['intermediate']['stem_search_radius'])) & (assigned_cloud[:, 3] > float(config['intermediate']['minimum_height'])) & (assigned_cloud[:,3] < float(config['intermediate']['maximum_height']) + float(config['intermediate']['section_len'])),:]
stems = verticality_clustering_iteration(xyz0_coords, float(config['advanced']['verticality_scale_stems']), float(config['advanced']['verticality_thresh_stems']), float(config['advanced']['epsilon_stems']), int(config['advanced']['minimum_points']), int(config['basic']['number_of_iterations']), float(config['advanced']['res_xy_stripe']), float(config['advanced']['res_y_stripe']), n_digits)[:, 0:6]
del xyz0_coords

# Computing circles 
print('---------------------------------------------')
print('6.-Computing diameters along stems...')
print('---------------------------------------------')
print('   Nº of trees to compute sections:')
trees = np.unique(stems[:, tree_id_field]) # Select the column that contains tree ID
sections = np.arange(float(config['intermediate']['minimum_height']), float(config['intermediate']['maximum_height']), float(config['intermediate']['section_len'])) # Range of uniformly spaced values within the specified interval 

n_trees = trees.size # Number of trees
n_sections = sections.size  # Number of sections
    
zeros_template = np.zeros((n_trees, n_sections), dtype = float) # Empty array to be reused.
    
X_c = deepcopy(zeros_template) # Empty array to store X data 
Y_c = deepcopy(zeros_template) # Empty array to store Y data
R = deepcopy(zeros_template)# Empty array to store radius data
check_circle = deepcopy(zeros_template) # Empty array to store 'check' data
second_time = deepcopy(zeros_template) # Empty array to store 'second_time' data
sector_perct = deepcopy(zeros_template) # Empty array to store percentage of occuped sectors data
n_points_in = deepcopy(zeros_template) # Empty array to store inner points data


# Filling previous empty arrays

# Auxiliar index for first loop
tree = -1 # Loop will start at -1

# First loop: iterates over each tree
for tr in trees: 
    
    # Tree ID is used to iterate over trees
    tree_i = stems[stems[:, tree_id_field] == tr, :]
    tree = tree + 1 
    
    sys.stdout.write("\r%d%%" % np.float64((trees.shape[0] - tree) * 100 / trees.shape[0]))
    sys.stdout.flush()
    
    # Auxiliar index for second loop
    section = 0 
    
    # Second loop: iterates over each section
    for b in sections: 
        
        # Selecting (x, y) coordinates of points within the section
        X = tree_i[(tree_i[:, 3] >= b) & (tree_i[:, 3] < b + float(config['advanced']['section_wid'])), 0]
        Y = tree_i[(tree_i[:, 3] >= b) & (tree_i[:, 3] < b + float(config['advanced']['section_wid'])), 1]
        # fit_circle_check call. It provides data to fill the empty arrays  
        (X_c_fill, Y_c_fill, R_fill, check_circle_fill, second_time_fill, sector_perct_fill, n_points_in_fill) = fit_circle_check(X, Y, 0, 0, float(config['advanced']['radius_proportion']), int(config['advanced']['point_threshold']), float(config['advanced']['minimum_radius']), float(config['intermediate']['maximum_radius']), float(config['advanced']['point_distance']), int(config['advanced']['number_points_section']), int(config['advanced']['number_sectors']), int(config['advanced']['m_number_sectors']), float(config['advanced']['circle_width']))

        # Filling the empty arrays
        X_c[tree, section] = X_c_fill
        Y_c[tree, section] = Y_c_fill
        R[tree, section] = R_fill
        check_circle[tree, section] = check_circle_fill
        second_time[tree, section] = second_time_fill
        sector_perct[tree, section] = sector_perct_fill
        n_points_in[tree, section] = n_points_in_fill
        
        # Freeing memory
        del X_c_fill, Y_c_fill, R_fill, check_circle_fill, second_time_fill
        
        section = section + 1


# Once every circle on every tree is fitted, outliers are detected.
outliers = tilt_detection(X_c, Y_c, R, sections, w_1 = 3, w_2 = 1)


print('  ')
print('---------------------------------------------')
print('7.-Drawing circles and axes...')
print('---------------------------------------------')

t_las2 = timeit.default_timer()

draw_circles(X_c, Y_c, R, sections, check_circle, sector_perct, n_points_in, tree_vector, outliers, float(config['advanced']['minimum_radius']), float(config['intermediate']['maximum_radius']), int(config['advanced']['point_threshold']), int(config['advanced']['number_sectors']), int(config['advanced']['m_number_sectors']), filename_las, int(config['advanced']['circa']))

draw_axes(tree_vector, float(config['advanced']['axis_downstep']), float(config['intermediate']['axis_upstep']), float(config['basic']['lower_limit']), float(config['basic']['upper_limit']), float(config['advanced']['p_interval']), filename_las)

dbh_values, tree_locations = tree_locator(sections, X_c, Y_c, tree_vector, sector_perct, R, n_points_in, int(config['advanced']['point_threshold']), outliers, filename_las, X_field = 0, Y_field = 1, Z_field = 2)

# matrix with tree height, DBH and (x,y) coordinates of each tree
dbh_and_heights = np.zeros((dbh_values.shape[0], 4))
if tree_heights.shape[0] != dbh_values.shape[0]:
    tree_heights = tree_heights[0:dbh_values.shape[0], :]
dbh_and_heights[:, 0] = tree_heights[:, 3]
dbh_and_heights[:, 1] = dbh_values[:, 0]
dbh_and_heights[:, 2] = tree_locations[:, 0]
dbh_and_heights[:, 3] = tree_locations[:, 1]


# -------------------------------------------------------------------------------------------------------------
# Exporting results in .txt file 
# -------------------------------------------------------------------------------------------------------------

np.savetxt(filename_las[:-4]+'_R.txt', R, fmt = ('%.3f'))
np.savetxt(filename_las[:-4]+'_X_c.txt', X_c, fmt = ('%.3f'))
np.savetxt(filename_las[:-4]+'_Y_c.txt', Y_c, fmt = ('%.3f'))
np.savetxt(filename_las[:-4]+'_check_circle.txt', check_circle, fmt = ('%.3f'))

np.savetxt(filename_las[:-4]+'_n_points_in.txt', n_points_in, fmt = ('%.3f'))
np.savetxt(filename_las[:-4]+'_sector_perct.txt', sector_perct, fmt = ('%.3f'))
np.savetxt(filename_las[:-4]+'_outliers.txt', outliers, fmt = ('%.3f'))
np.savetxt(filename_las[:-4]+'_dbh_and_heights.txt', dbh_and_heights, fmt = ('%.3f'))
np.savetxt(filename_las[:-4]+'_sections.txt', np.column_stack(sections), fmt = ('%.3f'))

elapsed_las2 = timeit.default_timer() - t_las2
print('Total time:',"   %.2f" % elapsed_las2,'s')

elapsed_t = timeit.default_timer() - t_t
# -------------------------------------------------------------------------------------------------------------
print('---------------------------------------------') 
print('8.-End of process!')
print('---------------------------------------------')
print('Total time:',"   %.2f" % elapsed_t,'s')
print('nº of trees:',X_c.shape[0])

input("Press enter to close the program...")
