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
    
    Before running script, it should be checked where are the normalized heights stored in the input file: 'z' or another field. 
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
•	[original file name]_diameters: Text file containing the diameter of every section of every tree as tabular data.
•	[original file name]_outliers: Text file containing the ‘outlier probability’ of every section of every tree as tabular data.
•	[original file name]_sector_perct: Text file containing the sector occupancy of every section of every tree as tabular data.
•	[original file name]_check_circle: Text file containing the ‘check’ status of every section of every tree as tabular data.
•	[original file name]_n_points_in: Text file containing the number of points within the inner circle of every section of every tree as tabular data.
•	[original file name]_sections: Text file containing the sections as a vector.
  
'''

import timeit
from tkinter import filedialog
from gui_layout import Application

import dendromatics as dm
import laspy
import numpy as np
import pandas as pd


finApp = Application()
finApp.mainloop()


#-------------------------------------------------------------------------------------------------
# BASIC PARAMETERS. These are the parameters to be checked (and changed if needed) for each dataset/plot
# All parameters are in m or points
#-------------------------------------------------------------------------------------------------

is_normalized = finApp.is_normalized_var.get()
is_noisy = finApp.is_noisy_var.get()
txt = finApp.txt_var.get()

field_name_z0 = finApp.z0_name.get() # Name of the Z0 field in the LAS file containing the cloud. 
# If the normalized heights are stored in the Z coordinate of the .LAS file: field_name_z0 = "z" (lowercase)

# Upper and lower limits (vertical) of the stripe where it should be reasonable to find stems with minimum presence of shrubs or branches.
stripe_upper_limit = float(finApp.upper_limit.get()) # Values, normally between 2 and 5
stripe_lower_limit = float(finApp.lower_limit.get()) # Values, normally between 0.3 and 1.3

n_iter = int(finApp.number_of_iterations.get()) # Number of iterations of 'peeling off branches'. 
# Values between 0 (no branch peeling/cleaning) and 5 (very extreme branch peeling/cleaning)

#-------------------------------------------------------------------------------------------------
# INTERMEDIATE PARAMETERS. They should only be modified when no good results are obtained tweaking basic parameters.
# They require a deeper knowledge of how the algorithm and the implementation work
#-------------------------------------------------------------------------------------------------

expected_R = float(finApp.stem_search_diameter.get()) / 2# Points within this distance from tree axes will be considered as potential stem points. 
# Values between R_max and 1 (exceptionally greater than 1: very large diameters and/or intricate stems)

R_max = float(finApp.maximum_diameter.get()) / 2 # Maximum radius expected for any section during circle fitting.

min_h = float(finApp.minimum_height.get()) # Lowest height
max_h = float(finApp.maximum_height.get()) # highest height

section_length = float(finApp.section_len.get()) # sections are this long (z length)


#-------------------------------------------------------------------------------------------------
# EXPERT PARAMETERS. They should only be modified when no good results are obtained peaking basic parameters.
# They require a deeper knowledge of how the algorithm and the implementation work
# *Stored in the main script in this version.
#-------------------------------------------------------------------------------------------------


#-------------------------------------------------------------------------------------------------
# Stem extraction
#-------------------------------------------------------------------------------------------------
resolution_xy_stripe = float(finApp.res_xy_stripe.get())  # (x, y) voxel resolution during stem extraction
resolution_z_stripe = float(finApp.res_z_stripe.get())  # (z) voxel resolution during stem extraction

n_points = int(finApp.number_of_points.get()) # minimum number of points per stem within the stripe (DBSCAN clustering). 
# Values, normally between 500 and 3000 

n_points_stripe = int(finApp.number_of_points.get())  # DBSCAN minimum number of points during stem extraction

vert_scale_stripe = float(finApp.verticality_scale_stripe.get()) # Vicinity radius for PCA during stem extraction
vert_threshold_stripe = float(finApp.verticality_thresh_stripe.get())  # Verticality threshold durig stem extraction

n_iter_stripe = n_iter  # Number of iterations of 'peeling off branchs' during stem extraction

#-------------------------------------------------------------------------------------------------
# Tree individualization.
#-------------------------------------------------------------------------------------------------
resolution_xy = float(finApp.res_xy.get())  # (x, y) voxel resolution during tree individualization
resolution_z = float(finApp.res_z.get())  # (z) voxel resolution during tree individualization

min_points = int(finApp.minimum_points.get()) # Minimum number of points within a stripe to consider it as a potential tree during tree individualization

vert_scale_stems = float(finApp.verticality_scale_stems.get()) # Vicinity radius for PCA  during tree individualization
vert_threshold_stems = float(finApp.verticality_thresh_stems.get()) # Verticality threshold  during tree individualization

h_range = float(finApp.height_range.get())  # only stems where points extend vertically throughout this range are considered. 
d_max = float(finApp.maximum_d.get()) # Points that are closer than d_max to an axis are assigned to that axis during individualize_trees process.

d_heights = float(finApp.distance_to_axis.get()) # Points within this distance from tree axes will be used to find tree height
resolution_heights = float(finApp.res_heights.get()) # Resolution for the voxelization while computing tree heights 
max_dev = float(finApp.maximum_dev.get()) # Maximum degree of vertical deviation from the axis

n_iter_stems = n_iter # Number of iterations of 'peeling off branchs' during tree individualization

n_points_stems = n_points # DBSCAN minimum number of points during tree individualization 

#-------------------------------------------------------------------------------------------------
# Extracting sections.
#-------------------------------------------------------------------------------------------------

section_width = float(finApp.section_wid.get()) # sections are this wide
n_points_section = int(finApp.number_points_section.get()) # Minimum number of points in a section to be considered
times_R = float(finApp.diameter_proportion.get()) # Proportion, regarding the circumference fit by fit_circle, that the inner circumference radius will have as length
R_min = float(finApp.minimum_diameter.get()) / 2 # Minimum radius expected for any section circle fitting.
threshold = int(finApp.point_threshold.get()) # Number of points inside the inner circle
max_dist = float(finApp.point_distance.get()) # Maximum distance among points to be considered within the same cluster.
n_sectors = int(finApp.number_sectors.get()) # Number of sectors in which the circumference will be divided
min_n_sectors = int(finApp.m_number_sectors.get()) # Minimum number of sectors that must be occupied.
width = float(finApp.circle_width.get()) # Width, in centimeters, around the circumference to look for points

#-------------------------------------------------------------------------------------------------
# Drawing circles.
#-------------------------------------------------------------------------------------------------
circa_points = int(finApp.circa.get())

#-------------------------------------------------------------------------------------------------
# Drawing axes.
#-------------------------------------------------------------------------------------------------
point_interval = float(finApp.p_interval.get())
line_downstep = float(finApp.axis_downstep.get())
line_upstep = float(finApp.axis_upstep.get()) # From the stripe centroid, how much (upwards direction) will the drawn axes extend.

#-------------------------------------------------------------------------------------------------
# Height normalization
#-------------------------------------------------------------------------------------------------

ground_res = float(finApp.res_ground.get())
points_ground = int(finApp.min_points_ground.get())
cloth_res = float(finApp.res_cloth.get())

#-------------------------------------------------------------------------------------------------
# NON MODIFIABLE. These parameters should never be modified by the user.
#-------------------------------------------------------------------------------------------------

X_field = 0 # Which column contains X field  - NON MODIFIABLE
Y_field = 1 # Which column contains Y field  - NON MODIFIABLE
Z_field = 2 # Which column contains Z field  - NON MODIFIABLE

Z0_field = 3 # Which column contains Z0 field  - NON MODIFIABLE
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

print(finApp.copyright_info_1)
print(finApp.copyright_info_2)
print("See License at the bottom of 'About' tab for more details or visit <https://www.gnu.org/licenses/>")

t_t = timeit.default_timer()


if is_normalized:
    
    # Read .LAS file. 
    entr = laspy.read(filename_las)
    coords = np.vstack((entr.x, entr.y, entr.z, entr[field_name_z0])).transpose()
    
    # Number of points and area occuped by the plot. 
    print('---------------------------------------------')
    print('Analyzing cloud size...')
    print('---------------------------------------------')

    _, _, voxelated_ground = dm.voxelate(coords[coords[:, 3] < 0.5, 0:3], 1, 2000, n_digits, with_n_points = False, silent = False)
    cloud_size = coords.shape[0]/1000000
    cloud_shape = voxelated_ground.shape[0]
    print('   This cloud has',"{:.2f}".format(cloud_size),'millions points')
    print('   Its area is ',cloud_shape,'m^2')
    
    print('---------------------------------------------')
    print('Cloud is already normalized...')
    print('---------------------------------------------')
    
else:

    # Read .LAS file.
    entr = laspy.read(filename_las)
    coords = np.vstack((entr.x, entr.y, entr.z)).transpose()
    
    # Number of points and area occuped by the plot. 
    print('---------------------------------------------')
    print('Analyzing cloud size...')
    print('---------------------------------------------')

    _, _, voxelated_ground = dm.voxelate(coords, 1, 2000, n_digits, with_n_points = False, silent = False)
    cloud_size = coords.shape[0]/1000000
    cloud_shape = voxelated_ground.shape[0]
    print('   This cloud has',"{:.2f}".format(cloud_size),'millions points')
    print('   Its area is ',cloud_shape,'m^2')
    del voxelated_ground
    
    print('---------------------------------------------')
    print('Cloud is not normalized...')
    print('---------------------------------------------')
    
    if is_noisy:
        
        print('---------------------------------------------')
        print('And there is noise. Reducing it...')
        print('---------------------------------------------')
        t = timeit.default_timer()
        # Noise elimination
        clean_points = dm.clean_ground(coords, ground_res, points_ground)
        
        elapsed = timeit.default_timer() - t
        print('        ',"%.2f" % elapsed,'s: denoising')
        
        print('---------------------------------------------')
        print('Generating a Digital Terrain Model...')
        print('---------------------------------------------')
        t = timeit.default_timer()
        # Extracting ground points and DTM ## MAYBE ADD VOXELIZATION HERE
        cloth_nodes = dm.generate_dtm(clean_points)
        
        elapsed = timeit.default_timer() - t
        print('        ',"%.2f" % elapsed,'s: generating the DTM')
        
    else:
        
        print('---------------------------------------------')
        print('Generating a Digital Terrain Model...')
        print('---------------------------------------------')
        t = timeit.default_timer()
        # Extracting ground points and DTM
        cloth_nodes = dm.generate_dtm(coords, cloth_resolution=cloth_res)
        
        elapsed = timeit.default_timer() - t
        print('        ',"%.2f" % elapsed,'s: generating the DTM')
  
    print('---------------------------------------------')
    print('Cleaning and exporting the Digital Terrain Model...')
    print('---------------------------------------------')
    t = timeit.default_timer()
    # Cleaning the DTM
    dtm = dm.clean_cloth(cloth_nodes)
    
    # Exporting the DTM

    las_dtm_points = laspy.create(point_format = 2, file_version='1.2')
    las_dtm_points.x = dtm[:, 0]
    las_dtm_points.y = dtm[:, 1]
    las_dtm_points.z = dtm[:, 2]

    las_dtm_points.write(filename_las + "_dtm_points.las")
    
    elapsed = timeit.default_timer() - t
    print('        ',"%.2f" % elapsed,'s: exporting the DTM')
    
    # Normalizing the point cloud
    print('---------------------------------------------')
    print('Normalizing the point cloud and running the algorithm...')
    print('---------------------------------------------')
    t = timeit.default_timer()
    z0_values = dm.normalize_heights(coords, dtm)
    coords = np.append(coords, np.expand_dims(z0_values, axis = 1), 1)
    
    elapsed = timeit.default_timer() - t
    print('        ',"%.2f" % elapsed,'s: Normalizing the point cloud')
    
    elapsed = timeit.default_timer() - t_t
    print('        ',"%.2f" % elapsed,'s: Total preprocessing time')

print('---------------------------------------------')
print('1.-Extracting the stripe and peeling the stems...')
print('---------------------------------------------')

stripe = coords[(coords[:, 3] > stripe_lower_limit) & (coords[:, 3] < stripe_upper_limit), 0:4]
clust_stripe = dm.verticality_clustering(stripe, vert_scale_stripe, vert_threshold_stripe, n_points_stripe, n_iter_stripe, resolution_xy_stripe, resolution_z_stripe, n_digits)

print('---------------------------------------------')
print('2.-Computing distances to axes and individualizating trees...')
print('---------------------------------------------')
                                                                                       
assigned_cloud, tree_vector, tree_heights = dm.individualize_trees(coords, clust_stripe, resolution_z, resolution_xy, stripe_lower_limit, stripe_upper_limit, h_range, d_max, min_points, d_heights, max_dev, resolution_heights, n_digits, X_field, Y_field, Z_field, tree_id_field = -1)     

print('  ')
print('---------------------------------------------')
print('3.-Exporting .LAS files including complete cloud and stripe...')
print('---------------------------------------------')

# Stripe
t_las = timeit.default_timer()
las_stripe = laspy.create(point_format = 2, file_version='1.2')
las_stripe.x = clust_stripe[:, X_field]
las_stripe.y = clust_stripe[:, Y_field]
las_stripe.z = clust_stripe[:, Z_field]

las_stripe.add_extra_dim(laspy.ExtraBytesParams(name = "tree_ID", type = np.int32))
las_stripe.tree_ID= clust_stripe[:, -1]
las_stripe.write(filename_las[:-4]+"_stripe.las")

# Whole cloud including new fields
entr.add_extra_dim(laspy.ExtraBytesParams(name="dist_axes", type=np.float64))
entr.add_extra_dim(laspy.ExtraBytesParams(name="tree_ID", type=np.int32))
entr.dist_axes = assigned_cloud[:, 5]
entr.tree_ID = assigned_cloud[:, 4]

if is_noisy:
    entr.add_extra_dim(laspy.ExtraBytesParams(name="Z0", type=np.float64))
    entr.Z0 = z0_values
entr.write(filename_las[:-4]+"_tree_ID_dist_axes.las")
elapsed_las = timeit.default_timer() - t_las
print('Total time:',"   %.2f" % elapsed_las,'s')

# Tree heights
las_tree_heights = laspy.create(point_format = 2, file_version='1.2')
las_tree_heights.x = tree_heights[:, 0] # x
las_tree_heights.y = tree_heights[:, 1] # y
las_tree_heights.z = tree_heights[:, 2] # z
las_tree_heights.add_extra_dim(laspy.ExtraBytesParams(name = "z0", type = np.int32))
las_tree_heights.z0 = tree_heights[:, 3] # z0
las_tree_heights.add_extra_dim(laspy.ExtraBytesParams(name = "deviated", type = np.int32))
las_tree_heights.deviated = tree_heights[:, 4] # vertical deviation binary indicator
las_tree_heights.write(filename_las[: -4] + "_tree_heights.las")


# stem extraction and curation 
print('---------------------------------------------')
print('4.-Extracting and curating stems...')
print('---------------------------------------------')

xyz0_coords = assigned_cloud[(assigned_cloud[:, 5] < expected_R) & (assigned_cloud[:, 3] > min_h) & (assigned_cloud[:,3] < max_h + section_width),:]
stems = dm.verticality_clustering(xyz0_coords, vert_scale_stems, vert_threshold_stems, n_points_stems, n_iter_stems, resolution_xy_stripe, resolution_z_stripe, n_digits)[:, 0:6]


# Computing circles 
print('---------------------------------------------')
print('5.-Computing diameters along stems...')
print('---------------------------------------------')

sections = np.arange(min_h, max_h, section_length) # Range of uniformly spaced values within the specified interval 

X_c, Y_c, R, check_circle, second_time, sector_perct, n_points_in = dm.compute_sections(stems, sections, section_width, times_R, threshold, R_min, R_max, max_dist, n_points_section, n_sectors, min_n_sectors, width)


# Once every circle on every tree is fitted, outliers are detected.
np.seterr(divide='ignore', invalid='ignore')
outliers = dm.tilt_detection(X_c, Y_c, R, sections, w_1 = 3, w_2 = 1)
np.seterr(divide='warn', invalid='warn')

print('  ')
print('---------------------------------------------')
print('6.-Drawing circles and axes...')
print('---------------------------------------------')

t_las2 = timeit.default_timer()

dm.draw_circles(X_c, Y_c, R, sections, check_circle, sector_perct, n_points_in, tree_vector, outliers, filename_las, R_min, R_max, threshold, n_sectors, min_n_sectors, circa_points)

dm.draw_axes(tree_vector, filename_las, line_downstep, line_upstep, stripe_lower_limit, stripe_upper_limit, point_interval, X_field, Y_field, Z_field)

dbh_values, tree_locations = dm.tree_locator(sections, X_c, Y_c, tree_vector, sector_perct, R, outliers, n_points_in, threshold, X_field, Y_field, Z_field)

las_tree_locations = laspy.create(point_format = 2, file_version = '1.2')
las_tree_locations.x = tree_locations[:, 0]
las_tree_locations.y = tree_locations[:, 1]
las_tree_locations.z = tree_locations[:, 2]

las_tree_locations.write(filename_las[:-4] + "_tree_locator.las")


# -------------------------------------------------------------------------------------------------------------
# Exporting results 
# -------------------------------------------------------------------------------------------------------------

    # matrix with tree height, DBH and (x,y) coordinates of each tree
dbh_and_heights = np.zeros((dbh_values.shape[0], 4))

if tree_heights.shape[0] != dbh_values.shape[0]:
    tree_heights = tree_heights[0:dbh_values.shape[0], :]
    
dbh_and_heights[:, 0] = tree_heights[:, 3]
dbh_and_heights[:, 1] = dbh_values[:, 0]
dbh_and_heights[:, 2] = tree_locations[:, 0]
dbh_and_heights[:, 3] = tree_locations[:, 1]

if not txt:
    
    # Generating aggregated quality value for each section
    quality = np.zeros(sector_perct.shape)
    # Section does not pass quality check if:
    mask = (
        (sector_perct < min_n_sectors / n_sectors * 100) # Percentange of occupied sectors less than minimum
        | (n_points_in > threshold) | (outliers > 0.3) # Outlier probability larger than 30 %
        | (R < R_min) # Radius smaller than the minimum radius
        | (R > R_max) # Radius larger than the maximum radius
        )       
    # 0: does not pass quality check - 1: passes quality checks
    quality = np.where(mask, quality, 1)
    
    # Function to convert data to pandas DataFrames
    def to_pandas(data):
        # Covers np.arrays of shape == 2 (almost every case)
        if len(data.shape) == 2:
            df = pd.DataFrame(data=data,
                              index=['T'+str(i + 1) for i in range(data.shape[0])],
                              columns=['S'+str(i + 1) for i in range(data.shape[1])])
        
        # Covers np.arrays of shape == 1 (basically, data regarding the normalized height of every section).
        if len(data.shape) == 1:
            df = pd.DataFrame(data=data).transpose()
            df.index = ['Z0']
            df.columns = ['S'+str(i + 1) for i in range(data.shape[0])]
            
        return(df)
    
    # Converting data to pandas DataFrames for ease to output them as excel files.    
    df_diameters = to_pandas(R) * 2
    df_X_c = to_pandas(X_c)
    df_Y_c = to_pandas(Y_c)
    df_sections = to_pandas(sections)   
    df_quality = to_pandas(quality)
    df_outliers = to_pandas(outliers)
    df_sector_perct = to_pandas(sector_perct)
    df_n_points_in = to_pandas(n_points_in)
    
    df_dbh_and_heights = pd.DataFrame(data=dbh_and_heights, 
                                      index=['T'+str(i + 1) for i in range(dbh_values.shape[0])],
                                      columns = ['TH', 'DBH', 'X', 'Y'])
    
    # Description to be added to each excel sheet.
    info_diameters = """Diameter of every section (S) of every tree (T). 
        Units are meters.
        """
    info_X_c = """(x) coordinate of the centre of every section (S) of every tree (T)."""
    info_Y_c = """(y) coordinate of the centre of every section (S) of every tree (T)."""
    info_sections = """Normalized height (Z0) of every section (S).
    Units are meters."""
    info_quality = """Overal quality of every section (S) of every tree (T).
    0: Section does not pass quality checks - 1: Section passes quality checks.
    """
    info_outliers = """'Outlier probability' of every section (S) of every tree (T).
    It takes values between 0 and 1.
    """
    info_sector_perct = """Percentage of occupied sectors of every section (S) of every tree (T).
    It takes values between 0 and 100.
    """
    info_n_points_in = """Number of points in the inner circle of every section (S) of every tree (T).
    The lowest, the better.
    """
    info_dbh_and_heights = """Total height (TH) of each tree (T).
    Diameter at breast height (DBH) of each tree (T).
    (x, y) coordinates (X and Y) of each tree (T).
    """
    info_cloud_size = f"This cloud has {cloud_size} millions points and its area is {cloud_shape} km2"
    
    # Converting descriptions to pandas DataFrames for ease to include them in the excel file.
    df_info_diameters = pd.Series(info_diameters)
    df_info_X_c = pd.Series(info_X_c)
    df_info_Y_c = pd.Series(info_Y_c)
    df_info_sections = pd.Series(info_sections)
    df_info_quality = pd.Series(info_quality)
    df_info_outliers = pd.Series(info_outliers)
    df_info_sector_perct = pd.Series(info_sector_perct)
    df_info_n_points_in = pd.Series(info_n_points_in)
    df_info_dbh_and_heights = pd.Series(info_dbh_and_heights)
    df_info_cloud_size = pd.Series(info_cloud_size)

    
    # Creating an instance of a excel writer
    writer = pd.ExcelWriter(filename_las[:-4] + ".xlsx", engine='xlsxwriter')
    
    # Writing the descriptions
       
    df_info_dbh_and_heights.to_excel(writer,
                         sheet_name = "Plot Metrics", 
                         header = False, 
                         index = False, 
                         merge_cells = False)
    
    df_info_cloud_size.to_excel(writer, 
                                sheet_name="Plot Metrics",
                                startrow=1,
                                header = False, 
                                index = False, 
                                merge_cells = False)
    
    df_info_diameters.to_excel(writer, 
                               sheet_name = "Diameters", 
                               header = False,
                               index = False,
                               merge_cells = False)
    
    df_info_X_c.to_excel(writer, 
                         sheet_name = "X", 
                         header = False, 
                         index = False, 
                         merge_cells = False)
    
    df_info_Y_c.to_excel(writer,
                         sheet_name = "Y", 
                         header = False, 
                         index = False, 
                         merge_cells = False)
    
    df_info_sections.to_excel(writer,
                              sheet_name = "Sections", 
                              header = False, 
                              index = False, 
                              merge_cells = False)
    
    df_info_quality.to_excel(writer,
                             sheet_name = "Q(Overall Quality 0-1)", 
                             header = False, 
                             index = False, 
                             merge_cells = False)
    
    df_info_outliers.to_excel(writer,
                              sheet_name = "Q1(Outlier Probability)", 
                              header = False, 
                              index = False, 
                              merge_cells = False)
    
    df_info_sector_perct.to_excel(writer,
                                  sheet_name = "Q2(Sector Occupancy)", 
                                  header = False, 
                                  index = False, 
                                  merge_cells = False)
    
    df_info_n_points_in.to_excel(writer,
                                 sheet_name = "Q3(Points Inner Circle)", 
                                 header = False, 
                                 index = False, 
                                 merge_cells = False)
    

    # Writing the data
    df_dbh_and_heights.to_excel(writer, sheet_name="Plot Metrics", startrow=2, startcol= 1)
    df_diameters.to_excel(writer, sheet_name="Diameters", startrow=2, startcol= 1)  
    df_X_c.to_excel(writer, sheet_name="X", startrow=2, startcol= 1)
    df_Y_c.to_excel(writer, sheet_name="Y", startrow=2, startcol= 1)
    df_sections.to_excel(writer, sheet_name="Sections", startrow=2, startcol= 1)
    df_quality.to_excel(writer, sheet_name="Q(Overall Quality 0-1)", startrow=2, startcol= 1)
    df_outliers.to_excel(writer, sheet_name="Q1(Outlier Probability)", startrow=2, startcol= 1)
    df_sector_perct.to_excel(writer, sheet_name="Q2(Sector Occupancy)", startrow=2, startcol= 1)
    df_n_points_in.to_excel(writer, sheet_name="Q3(Points Inner Circle)", startrow=2, startcol= 1)
    
    writer.close()

else:
    
    np.savetxt(filename_las[:-4]+'_diameters.txt', R * 2, fmt = ('%.3f'))
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
print('End of process!')
print('---------------------------------------------')
print('Total time:',"   %.2f" % elapsed_t,'s')
print('nº of trees:',X_c.shape[0])

input("Press enter to close the program...")