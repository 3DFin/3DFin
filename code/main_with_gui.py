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
import numpy as np
from pathlib import Path
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from PIL import ImageTk, Image

import gui
import dendromatics as dm


### This function allows to retrieve the path of the data used to generate the images and
### the documentation, so they can be included in the executable ###
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

### This class allows to create the mouse-hover info boxes ###


### -------------------------------- ###
### ------- Creating the GUI ------- ###
### -------------------------------- ###

root = Tk()
root.title("Input parameters")
root.resizable(False, False)
root.geometry('810x632+0+0')
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

### --------------------------------- ###
### ------- Creating the tabs ------- ###
### --------------------------------- ###

note = ttk.Notebook(root)
note.grid(column=0, row=0, sticky="NEWS")

basic_tab = ttk.Frame(note)
advanced_tab = ttk.Frame(note)
expert_tab = ttk.Frame(note)
about_tab = ttk.Frame(note)

### --------------------------------- ###
### -------- Input parameters ------- ###
### --------------------------------- ###


 ### Basic parameters ###
z0_name = StringVar()
upper_limit = StringVar()
lower_limit = StringVar()
number_of_iterations = StringVar()
 
 ### Advanced parameters ###  
maximum_radius = StringVar()
stem_search_radius = StringVar()
minimum_height = StringVar()
maximum_height = StringVar()
section_len = StringVar()
distance_to_axis = StringVar()
axis_upstep = StringVar()
 
 ### Expert parameters ###
 
 # Stem extraction #
res_xy_stripe = StringVar()
res_z_stripe = StringVar()
number_of_points = StringVar()
verticality_scale_stripe = StringVar()
verticality_thresh_stripe = StringVar()
epsilon_stripe = StringVar()
 
 # Tree individualization #
res_xy = StringVar()
res_z = StringVar()
minimum_points = StringVar()
verticality_scale_stems = StringVar()
verticality_thresh_stems = StringVar()
epsilon_stems = StringVar()
height_range = StringVar()
maximum_d = StringVar()
res_heights = StringVar()
maximum_dev = StringVar()
 
 # Extracting sections #
section_wid = StringVar()
number_points_section = StringVar()
radius_proportion = StringVar()
minimum_radius = StringVar()
point_threshold = StringVar()
point_distance = StringVar()
number_sectors = StringVar()
m_number_sectors = StringVar()
circle_width = StringVar()
 
 # Drawing circles and axes #
circa = StringVar()
p_interval = StringVar()
axis_downstep = StringVar()
 
 # Other parameters #
X_column = StringVar()
Y_column = StringVar()
Z_column = StringVar()


### Reading config file only if it is available under name '3DFINconfig.ini' ###

my_file = Path("3DFINconfig.ini")

try:
    my_abs_path = my_file.resolve(strict=True) 

except FileNotFoundError:
    
    ### Basic parameters ###
    z0_name.set("Z0")
    upper_limit.set("2.5")
    lower_limit.set("0.5")
    number_of_iterations.set("2")
    
    ### Advanced parameters ###  
    maximum_radius.set("0.5")
    stem_search_radius.set("0.35")
    minimum_height.set("0.3")
    maximum_height.set("25")
    section_len.set("0.2")
    distance_to_axis.set("1.5")
    axis_upstep.set("10")
    
    ### Expert parameters ###
    
    # Stem extraction #
    res_xy_stripe.set("0.02")
    res_z_stripe.set("0.02")
    number_of_points.set("1000")
    verticality_scale_stripe.set("0.1")
    verticality_thresh_stripe.set("0.7")
    epsilon_stripe.set("0.037")
    
    # Tree individualization #
    res_xy.set("0.035")
    res_z.set("0.035")
    minimum_points.set("20")
    verticality_scale_stems.set("0.1")
    verticality_thresh_stems.set("0.7")
    epsilon_stems.set("0.08")
    height_range.set("1.2")
    maximum_d.set("15")
    res_heights.set("0.3")
    maximum_dev.set("25")
    
    # Extracting sections #
    section_wid.set("0.05")
    number_points_section.set("80")
    radius_proportion.set("0.5")
    minimum_radius.set("0.03")
    point_threshold.set("5")
    point_distance.set("0.02")
    number_sectors.set("16")
    m_number_sectors.set("9")
    circle_width.set("2")
    
    # Drawing circles and axes #
    circa.set("200")
    p_interval.set("0.01")
    axis_downstep.set("0.5")
    
    # Other parameters #
    X_column.set("0")
    Y_column.set("1")
    Z_column.set("2")

else:
    
    print('Configuration file found. Default parameters have been established.')
    
    ### Reading the config file ###
    config = configparser.ConfigParser()
    config.read(my_abs_path)
    
    ### Basic parameters ###
    z0_name.set(config['basic']['z0_name'])
    upper_limit.set(config['basic']['upper_limit'])
    lower_limit.set(config['basic']['lower_limit'])
    number_of_iterations.set(config['basic']['number_of_iterations'])
    
    ### Advanced parameters ###  
    maximum_radius.set(config['advanced']['maximum_radius'])
    stem_search_radius.set(config['advanced']['stem_search_radius'])
    minimum_height.set(config['advanced']['minimum_height'])
    maximum_height.set(config['advanced']['maximum_height'])
    section_len.set(config['advanced']['section_len'])
    distance_to_axis.set(config['advanced']['distance_to_axis'])
    axis_upstep.set(config['advanced']['axis_upstep'])
    
    ### Expert parameters ###
    
    # Stem extraction #
    res_xy_stripe.set(config['expert']['res_xy_stripe'])
    res_z_stripe.set(config['expert']['res_z_stripe'])
    number_of_points.set(config['expert']['number_of_points'])
    verticality_scale_stripe.set(config['expert']['verticality_scale_stripe'])
    verticality_thresh_stripe.set(config['expert']['verticality_thresh_stripe'])
    epsilon_stripe.set(config['expert']['epsilon_stripe'])
    
    # Tree individualization #
    res_xy.set(config['expert']['res_xy'])
    res_z.set(config['expert']['res_z'])
    minimum_points.set(config['expert']['minimum_points'])
    verticality_scale_stems.set(config['expert']['verticality_scale_stems'])
    verticality_thresh_stems.set(config['expert']['verticality_thresh_stems'])
    epsilon_stems.set(config['expert']['epsilon_stems'])
    height_range.set(config['expert']['height_range'])
    maximum_d.set(config['expert']['maximum_d'])
    res_heights.set(config['expert']['res_heights'])
    maximum_dev.set(config['expert']['maximum_dev'])
    
    # Extracting sections #
    section_wid.set(config['expert']['section_wid'])
    number_points_section.set(config['expert']['number_points_section'])
    radius_proportion.set(config['expert']['radius_proportion'])
    minimum_radius.set(config['expert']['minimum_radius'])
    point_threshold.set(config['expert']['point_threshold'])
    point_distance.set(config['expert']['point_distance'])
    number_sectors.set(config['expert']['number_sectors'])
    m_number_sectors.set(config['expert']['m_number_sectors'])
    circle_width.set(config['expert']['circle_width'])
    
    # Drawing circles and axes #
    circa.set(config['expert']['circa'])
    p_interval.set(config['expert']['p_interval'])
    axis_downstep.set(config['expert']['axis_downstep'])
    
    # Other parameters #
    X_column.set(config['expert']['X_column'])
    Y_column.set(config['expert']['Y_column'])
    Z_column.set(config['expert']['Z_column'])


### ----------------------------- ###
### ------- Editing tab 1 ------- ###
### ----------------------------- ###

note.add(basic_tab, text = "Basic")

### This pair of functions allow to enable/disable cloud normalization options

def enable_denoising():
    z0_entry.configure(state="normal")
    z0_entry.update()
    clean_button_1.configure(state="disabled")
    clean_button_1.update()
    clean_button_2.configure(state="disabled")
    clean_button_2.update()

def disable_denoising():
    z0_entry.configure(state="disabled")
    z0_entry.update()
    clean_button_1.configure(state="normal")
    clean_button_1.update()
    clean_button_2.configure(state="normal")
    clean_button_2.update()

  
ttk.Label(basic_tab, text="Is the point cloud height-normalized?").grid(column=2, row=1, columnspan = 2, sticky="EW")


ttk.Label(basic_tab, text="Are there noise points below ground-level?").grid(column=2, row=3, columnspan = 2, sticky="W")


# Z0 field name entry #
z0_entry = ttk.Entry(basic_tab, width=7, textvariable=z0_name)
z0_entry.grid(column=3, row=5, sticky="EW")
z0_entry.configure(state = "disabled")

# Stripe upper limit entry #
upper_limit_entry = ttk.Entry(basic_tab, width=7, textvariable=upper_limit)
upper_limit_entry.grid(column=3, row=6, sticky="EW")

# Stripe lower limit entry #
lower_limit_entry = ttk.Entry(basic_tab, width=7, textvariable=lower_limit)
lower_limit_entry.grid(column=3, row=7, sticky="EW")

# Number of iterations entry #
number_of_iterations_entry = ttk.Entry(basic_tab, width=7, textvariable=number_of_iterations)
number_of_iterations_entry.grid(column=3, row=8, sticky="EW")

ttk.Label(basic_tab, text="Normalized height field name").grid(column=2, row=5, sticky="W")
ttk.Label(basic_tab, text="Stripe upper limit").grid(column=2, row=6, sticky="W")
ttk.Label(basic_tab, text="Stripe lower limit").grid(column=2, row=7, sticky="W")
ttk.Label(basic_tab, text="Pruning intensity").grid(column=2, row=8, sticky="W")

ttk.Label(basic_tab, text="meters").grid(column=4, row=6, sticky="W")
ttk.Label(basic_tab, text="meters").grid(column=4, row=7, sticky="W")
ttk.Label(basic_tab, text="1 - 5").grid(column=4, row=8, sticky="W")

#### Adding logo ####
logo_png = ImageTk.PhotoImage(Image.open(resource_path("3dfin_png.png")))
ttk.Label(basic_tab, image = logo_png).grid(column = 6, row = 1, rowspan = 2, columnspan = 2, sticky = "NS")


#### Text displaying info ###
insert_text1 = """This program implements an algorithm to detect the trees present in a ground-based 
3D point cloud from a forest plot, and compute individual tree parameters: tree height,
tree location, diameters along the stem (including DBH), and stem axis. 

It accepts a .LAS/.LAZ file, which may contain extra fields (.LAS standard or not). Also, 
the input point cloud can come from terrestrial photogrammetry, TLS or mobile (e.g. 
hand-held) LS, a combination of those, and/or a combination of those with UAV-(LS 
or SfM), or ALS. 

The algorithm may be divided in three main steps:
    1. Identification of stems in an user-defined horizontal stripe.
    2. Tree individualization based on point-to-stem-axis distances.
    3. Robust computation of stem diameter at different section heights.

For further details, please refer to the documentation.
"""
ttk.Separator(basic_tab, orient = "vertical").grid(column = 5, row = 1, rowspan = 9, sticky = "NS")

ttk.Label(basic_tab, text = insert_text1).grid(column = 6, row = 3, rowspan = 7, columnspan = 2, sticky = "NW")

#### Adding images ####

img1 = ImageTk.PhotoImage(Image.open(resource_path("stripe.jpg")))

img2 = ImageTk.PhotoImage(Image.open(resource_path("original_cloud.jpg")))
img3 = ImageTk.PhotoImage(Image.open(resource_path("normalized_cloud.jpg")))


ttk.Label(basic_tab, text = "Stripe", font = ("Helvetica", 10, "bold")).grid(column = 1, row = 11, columnspan = 4, sticky = "N")
ttk.Label(basic_tab, image = img1).grid(column = 1, row = 12, columnspan = 4, sticky = "N")

ttk.Label(basic_tab, text = "Region where one should expect mostly stems.").grid(column = 1, row = 13, columnspan = 4, sticky = "N")

ttk.Label(basic_tab, text = "Original cloud", font = ("Helvetica", 10, "bold")).grid(column = 6, row = 11, sticky = "N")
ttk.Label(basic_tab, image = img2).grid(column = 6, row = 12, columnspan = 1, sticky = "N")

ttk.Label(basic_tab, text = "Height-normalized cloud", font = ("Helvetica", 10, "bold")).grid(column = 7, row = 11, sticky = "N")
ttk.Label(basic_tab, image = img3).grid(column = 7, row = 12, columnspan = 1, sticky = "N")

ttk.Label(basic_tab, text = "The algorithm requires a height-normalized point cloud, such as the one above.").grid(column = 6, row = 13, columnspan = 2, sticky = "N")


for child in basic_tab.winfo_children(): 
    child.grid_configure(padx=5, pady=5)

#### Adding radio buttons ####

# Variable to keep track of the option selected in OptionMenu
is_normalized_var = BooleanVar()

normalized_button_1 = ttk.Radiobutton(basic_tab, text="Yes", variable=is_normalized_var, value=True, command = enable_denoising)
normalized_button_1.grid(column=2, row=2, sticky="EW")
normalized_button_2 = ttk.Radiobutton(basic_tab, text="No", variable=is_normalized_var, value=False, command = disable_denoising)
normalized_button_2.grid(column=3, row=2, sticky="EW")

 
# Variable to keep track of the option selected in OptionMenu
is_noisy_var = BooleanVar()

# Create the optionmenu widget and passing the options_list and value_inside to it.
clean_button_1 = ttk.Radiobutton(basic_tab, text="Yes", variable=is_noisy_var, value=True)
clean_button_1.grid(column=2, row=4, sticky="EW")
clean_button_2 = ttk.Radiobutton(basic_tab, text="No", variable=is_noisy_var, value=False)
clean_button_2.grid(column=3, row=4, sticky="EW")

#### Adding info buttons ####

info_icon = ImageTk.PhotoImage(Image.open(resource_path("info_icon.png")))

is_normalized_info = ttk.Label(basic_tab, image = info_icon)
is_normalized_info.grid(column = 1, row = 1)
gui.CreateToolTip(is_normalized_info, text = 'If the point cloud is not height-normalized, a Digital Terrain\n'
                  'Model will be generated to compute normalized heights for all points.')

is_noisy_info = ttk.Label(basic_tab, image = info_icon)
is_noisy_info.grid(column = 1, row = 3)
gui.CreateToolTip(is_noisy_info, text = 'If it is expected to be noise below ground level (or if you know\n'
                  'that there is noise), a denoising step will be added before\n'
                  'generating the Digital Terrain Model.')

z0_info = ttk.Label(basic_tab, image = info_icon)
z0_info .grid(column = 1, row = 5)
gui.CreateToolTip(z0_info, text = 'Name of the Z0 field in the LAS file containing the cloud.\n'
              'If the normalized heights are stored in the Z coordinate\n'
              'of the .LAS file, then: Z0 field name = "z" (lowercase).\n'
              'Default is "Z0".')

upper_limit_info = ttk.Label(basic_tab, image = info_icon)
upper_limit_info.grid(column = 1, row = 6)
gui.CreateToolTip(upper_limit_info, text = 'Upper (vertical) limit of the stripe where it should be reasonable\n'
              'to find stems with minimum presence of shrubs or branches.\n'
              'Reasonable values are 2-5 meters.\n'
              'Default value is 2.5 meters.')

lower_limit_info = ttk.Label(basic_tab, image = info_icon)
lower_limit_info.grid(column = 1, row = 7)
gui.CreateToolTip(lower_limit_info, text = 'Lower (vertical) limit of the stripe where it should be reasonable\n'
              'to find stems with minimum presence of shrubs or branches.\n'
              'Reasonable values are 0.3-1.3 meters.\n'
              'Default value is 0.5 meters.')

number_of_iterations_info = ttk.Label(basic_tab, image = info_icon)
number_of_iterations_info.grid(column = 1, row = 8)
gui.CreateToolTip(number_of_iterations_info, text = 'Number of iterations of "pruning" during stem identification.\n'
              'Values between 1 (slight stem peeling/cleaning)\n'
              'and 5 (extreme branch peeling/cleaning).\n'
              'Default value is 2.')


### ----------------------------- ###
### ------- Editing tab 2 ------- ###
### ----------------------------- ###
note.add(advanced_tab, text = "Advanced")


# Maximum radius entry #
maximum_radius_entry = ttk.Entry(advanced_tab, width=7, textvariable=maximum_radius)
maximum_radius_entry.grid(column=3, row=1, sticky="EW")

# Stem search radius entry #
stem_search_radius_entry = ttk.Entry(advanced_tab, width=7, textvariable=stem_search_radius)
stem_search_radius_entry.grid(column=3, row=2, sticky="EW")

# Lowest section #
minimum_height_entry = ttk.Entry(advanced_tab, width=7, textvariable=minimum_height)
minimum_height_entry.grid(column=3, row=3, sticky="EW")

# Highest section #
maximum_height_entry = ttk.Entry(advanced_tab, width=7, textvariable=maximum_height)
maximum_height_entry.grid(column=3, row=4, sticky="EW")

# Section height #
section_len_entry = ttk.Entry(advanced_tab, width=7, textvariable=section_len)
section_len_entry.grid(column=3, row=5, sticky="EW")

# Section height #
distance_to_axis_entry = ttk.Entry(advanced_tab, width=7, textvariable=distance_to_axis)
distance_to_axis_entry.grid(column=3, row=6, sticky="EW")

# Axis highest point #
axis_upstep_entry = ttk.Entry(advanced_tab, width=7, textvariable=axis_upstep)
axis_upstep_entry.grid(column=3, row=7, sticky="EW")

ttk.Label(advanced_tab, text="Maximum radius").grid(column=2, row=1, sticky="W")
ttk.Label(advanced_tab, text="Steam search radius").grid(column=2, row=2, sticky="W")
ttk.Label(advanced_tab, text="Lowest section").grid(column=2, row=3, sticky="W")
ttk.Label(advanced_tab, text="Highest section").grid(column=2, row=4, sticky="W")
ttk.Label(advanced_tab, text="Distance between sections").grid(column=2, row=5, sticky="W")
ttk.Label(advanced_tab, text="Distance from axis").grid(column=2, row=6, sticky="W")
ttk.Label(advanced_tab, text="Axis upstep from stripe center").grid(column=2, row=7, sticky="W")

ttk.Label(advanced_tab, text="meters").grid(column=4, row=1, sticky="W")
ttk.Label(advanced_tab, text="meters").grid(column=4, row=2, sticky="W")
ttk.Label(advanced_tab, text="meters").grid(column=4, row=3, sticky="W")
ttk.Label(advanced_tab, text="meters").grid(column=4, row=4, sticky="W")
ttk.Label(advanced_tab, text="meters").grid(column=4, row=5, sticky="W")
ttk.Label(advanced_tab, text="meters").grid(column=4, row=6, sticky="W")
ttk.Label(advanced_tab, text="meters").grid(column=4, row=7, sticky="W")

#### Text displaying info ###
insert_text2 = """If the results obtained by just tweaking basic parameters do not 
meet your expectations, you might want to modify these. 

You can get a brief description of what they do by hovering the
mouse over the info icon right before each parameter. However, 
keep in mind that a thorough understanding is advisable before
changing these. For that, you can get a better grasp of what does 
the algorithm do in the attached documentation. You can easily 
access it through the Documentation button in the bottom-left 
corner.
"""
ttk.Separator(advanced_tab, orient = "vertical").grid(column = 5, 
                                                      row = 1, 
                                                      rowspan = 7, 
                                                      sticky = "NS",
                                                      )

ttk.Label(advanced_tab, text = "Advanced parameters", font = ("Helvetica", 10, "bold")).grid(column = 6, row = 1)
ttk.Label(advanced_tab, text = insert_text2).grid(column = 6, row = 2, rowspan = 6, sticky = "NW")



for child in advanced_tab.winfo_children(): 
    child.grid_configure(padx=5, pady=5)


#### Adding info buttons ####

maximum_radius_info = ttk.Label(advanced_tab, image = info_icon)
maximum_radius_info.grid(column = 1, row = 1)
gui.CreateToolTip(maximum_radius_info, text = 'Maximum radius expected for any stem.\n'
              'Default value: 0.5 meters.')

stem_search_radius_info = ttk.Label(advanced_tab, image = info_icon)
stem_search_radius_info.grid(column = 1, row = 2)
gui.CreateToolTip(stem_search_radius_info, text = 'Points within this distance from tree axes will be considered\n'
              'as potential stem points. Reasonable values are "Maximum radius"-1 meters \n'
              '(exceptionally greater than 1: very large diameters and/or intricate stems).')

minimum_height_info = ttk.Label(advanced_tab, image = info_icon)
minimum_height_info.grid(column = 1, row = 3)
gui.CreateToolTip(minimum_height_info, text = 'Lowest height at which stem diameter will be computed.\n'
              'Default value: 0.2 meters.')

maximum_height_info = ttk.Label(advanced_tab, image = info_icon)
maximum_height_info.grid(column = 1, row = 4)
gui.CreateToolTip(maximum_height_info, text = 'Highest height at which stem diameter will be computed.\n'
              'Default value: 25 meters.')

section_len_info = ttk.Label(advanced_tab, image = info_icon)
section_len_info.grid(column = 1, row = 5)
gui.CreateToolTip(section_len_info, text = 'Height of the sections (z length). Diameters will then be\n'
              'computed for every section.\n'
              'Default value: 0.2 meters.')

distance_to_axis_info = ttk.Label(advanced_tab, image = info_icon)
distance_to_axis_info.grid(column = 1, row = 6)
gui.CreateToolTip(distance_to_axis_info, text = 'Maximum distance from tree axis at which points will\n'
              'be considered while computing tree height. Points too far away\n'
              'from the tree axis might not be representative of actual tree height.\n'
              'Default value: 1.5 meters.')

axis_upstep_info = ttk.Label(advanced_tab, image = info_icon)
axis_upstep_info.grid(column = 1, row = 7)
gui.CreateToolTip(axis_upstep_info, text = 'From the stripe centroid, how much (upwards direction)\n'
              'will the drawn axes extend. Basically, this parameter controls\n'
              'how long will the drawn axes be.\n'
              'Default value: 10 meters.')


#### Adding images ####

individual_trees_img = ImageTk.PhotoImage(Image.open(resource_path("individual_trees.jpg")))
tree_axes_img = ImageTk.PhotoImage(Image.open(resource_path("tree_axes.jpg")))
sections_img = ImageTk.PhotoImage(Image.open(resource_path("sections.jpg")))


ttk.Label(advanced_tab, text = "Individual trees", font = ("Helvetica", 10, "bold")).grid(column = 1, row = 8, columnspan = 2, sticky = "S")
ttk.Label(advanced_tab, image = individual_trees_img).grid(column = 1, row = 9, columnspan = 2, sticky = "S")

ttk.Label(advanced_tab, text = "Tree axes", font = ("Helvetica", 10, "bold")).grid(column = 3, row = 8, columnspan = 3, sticky = "S")
ttk.Label(advanced_tab, image = tree_axes_img).grid(column = 3, row = 9, columnspan = 3, sticky = "S")

ttk.Label(advanced_tab, text = "Sections", font = ("Helvetica", 10, "bold")).grid(column = 6, row = 8, sticky = "S")
ttk.Label(advanced_tab, image = sections_img).grid(column = 6, row = 9, sticky = "S")

advanced_tab_text = """The algorithm outputs several .LAS files so the user can explore the results and these will be subject to the parameter configuration. 
The quality of the tree identification step will somehow depend on the 'Stem search radius' and the 'Maximum radius'. The length
of the drawn axes can be changed by modifying 'Axis upstep from stripe center'. 'Lowest section', 'Highest section' and 'Distance
between sections' will directly impact diameter computations and how the sections display in the output .LAS file dedicated to them.
"""
ttk.Label(advanced_tab, text = advanced_tab_text).grid(column = 2, row = 10, columnspan = 5, sticky = NW)



### ----------------------------- ###
### ------- Editing tab 3 ------- ###
### ----------------------------- ###

note.add(expert_tab, text = "Expert")


### Stem extraction ###
ttk.Label(expert_tab, text="Stem extraction", font = ("Helvetica", 10, "bold")).grid(column=2, row=1, sticky="E")

# (x, y) voxel resolution 
res_xy_stripe_entry = ttk.Entry(expert_tab, width=7, textvariable=res_xy_stripe)
res_xy_stripe_entry.grid(column=3, row=2, sticky="EW")


# (z) voxel resolution during stem extraction entry #
res_z_stripe_entry = ttk.Entry(expert_tab, width=7, textvariable=res_z_stripe)
res_z_stripe_entry.grid(column=3, row=3, sticky="EW")


# Number of points entry #
number_of_points_entry = ttk.Entry(expert_tab, width=7, textvariable=number_of_points)
number_of_points_entry.grid(column=3, row=4, sticky="EW")


# Vicinity radius for PCA during stem extraction entry #
verticality_scale_stripe_entry = ttk.Entry(expert_tab, width=7, textvariable=verticality_scale_stripe)
verticality_scale_stripe_entry.grid(column=3, row=5, sticky="EW")


# Verticality threshold durig stem extraction entry #
verticality_thresh_stripe_entry = ttk.Entry(expert_tab, width=7, textvariable=verticality_thresh_stripe)
verticality_thresh_stripe_entry.grid(column=3, row=6, sticky="EW")


# epsilon durig stem extraction entry # Should be 0.037 at least
epsilon_stripe_entry = ttk.Entry(expert_tab, width=7, textvariable=epsilon_stripe)
epsilon_stripe_entry.grid(column=3, row=7, sticky="EW")


ttk.Label(expert_tab, text="(x, y) voxel resolution").grid(column=2, row=2, sticky="w")
ttk.Label(expert_tab, text="(z) voxel resolution").grid(column=2, row=3, sticky="W")
ttk.Label(expert_tab, text="Number of points").grid(column=2, row=4, sticky="W")
ttk.Label(expert_tab, text="Vicinity radius").grid(column=2, row=5, sticky="W")
ttk.Label(expert_tab, text="Verticality threshold").grid(column=2, row=6, sticky="W")
ttk.Label(expert_tab, text="DBSCAN eps").grid(column=2, row=7, sticky="W")

ttk.Label(expert_tab, text="meters").grid(column=4, row=2, sticky="W")
ttk.Label(expert_tab, text="meters").grid(column=4, row=3, sticky="W")
ttk.Label(expert_tab, text="meters").grid(column=4, row=5, sticky="W")
ttk.Label(expert_tab, text="(0, 1)").grid(column=4, row=6, sticky="W")
ttk.Label(expert_tab, text="meters").grid(column=4, row=7, sticky="W")

### Tree individualization ###
ttk.Label(expert_tab, text="Tree individualization", font = ("Helvetica", 10, "bold")).grid(column=2, row=8, sticky="E")

# (x, y) voxel resolution 
res_xy_entry = ttk.Entry(expert_tab, width=7, textvariable=res_xy)
res_xy_entry.grid(column=3, row=9, sticky="EW")


# (z) voxel resolution #
res_z_entry = ttk.Entry(expert_tab, width=7, textvariable=res_z)
res_z_entry.grid(column=3, row=10, sticky="EW")


# Minimum points #
minimum_points_entry = ttk.Entry(expert_tab, width=7, textvariable=minimum_points)
minimum_points_entry.grid(column=3, row=11, sticky="EW")


# Vicinity radius for PCA #
verticality_scale_stems_entry = ttk.Entry(expert_tab, width=7, textvariable=verticality_scale_stems)
verticality_scale_stems_entry.grid(column=3, row=12, sticky="EW")


# Verticality threshold durig tree individualization entry #
verticality_thresh_stems_entry = ttk.Entry(expert_tab, width=7, textvariable=verticality_thresh_stems)
verticality_thresh_stems_entry.grid(column=3, row=13, sticky="EW")


# epsilon durig tree individualization entry #
epsilon_stems_entry = ttk.Entry(expert_tab, width=7, textvariable=epsilon_stems)
epsilon_stems_entry.grid(column=3, row=14, sticky="EW")


# Vertical range #
height_range_entry = ttk.Entry(expert_tab, width=7, textvariable=height_range)
height_range_entry.grid(column=3, row=15, sticky="EW")


# Maximum distance to axis #
maximum_d_entry = ttk.Entry(expert_tab, width=7, textvariable=maximum_d)
maximum_d_entry.grid(column=3, row=16, sticky="EW")


# Voxel resolution during height computation #
res_heights_entry = ttk.Entry(expert_tab, width=7, textvariable=res_heights)
res_heights_entry.grid(column=3, row=17, sticky="EW")


# Maximum degree of vertical deviation from the axis #
maximum_dev_entry = ttk.Entry(expert_tab, width=7, textvariable=maximum_dev)
maximum_dev_entry.grid(column=3, row=18, sticky="EW")


ttk.Label(expert_tab, text="(x, y) voxel resolution").grid(column=2, row=9, sticky="W")
ttk.Label(expert_tab, text="(z) voxel resolution").grid(column=2, row=10, sticky="W")
ttk.Label(expert_tab, text="Minimum points").grid(column=2, row=11, sticky="W")
ttk.Label(expert_tab, text="Vicinity radius").grid(column=2, row=12, sticky="W")
ttk.Label(expert_tab, text="Verticality threshold").grid(column=2, row=13, sticky="W")
ttk.Label(expert_tab, text="DBSCAN eps").grid(column=2, row=14, sticky="W")
ttk.Label(expert_tab, text="Vertical range").grid(column=2, row=15, sticky="W")
ttk.Label(expert_tab, text="Maximum distance to tree axis").grid(column=2, row=16, sticky="W")
ttk.Label(expert_tab, text="Voxel resolution for height computation").grid(column=2, row=17, sticky="W")
ttk.Label(expert_tab, text="Maximum vertical deviation from axis").grid(column=2, row=18, sticky="W")

ttk.Label(expert_tab, text="meters").grid(column=4, row=9, sticky="W")
ttk.Label(expert_tab, text="meters").grid(column=4, row=10, sticky="W")
ttk.Label(expert_tab, text="meters").grid(column=4, row=12, sticky="W")
ttk.Label(expert_tab, text="(0, 1)").grid(column=4, row=13, sticky="W")
ttk.Label(expert_tab, text="meters").grid(column=4, row=14, sticky="W")
ttk.Label(expert_tab, text="meters").grid(column=4, row=15, sticky="W")
ttk.Label(expert_tab, text="meters").grid(column=4, row=16, sticky="W")
ttk.Label(expert_tab, text="meters").grid(column=4, row=17, sticky="W")
ttk.Label(expert_tab, text="degrees").grid(column=4, row=18, sticky="W")

### Extracting sections ###
ttk.Label(expert_tab, text="Extracting sections", font = ("Helvetica", 10, "bold")).grid(column = 7, row=1, sticky="E")

### Vertical separator

ttk.Separator(expert_tab, orient = "vertical").grid(column = 5, row = 1, rowspan = 18, sticky = "NS")

# Section width #
section_wid_entry = ttk.Entry(expert_tab, width=7, textvariable=section_wid)
section_wid_entry.grid(column = 8, row=2, sticky="EW")


# Minimum number of points in a section #
number_points_section_entry = ttk.Entry(expert_tab, width=7, textvariable=number_points_section)
number_points_section_entry.grid(column = 8, row=3, sticky="EW")


# Inner/outer circle proportion #
radius_proportion_entry = ttk.Entry(expert_tab, width=7, textvariable=radius_proportion)
radius_proportion_entry.grid(column = 8, row=4, sticky="EW")

# Minimum radius expected #
minimum_radius_entry = ttk.Entry(expert_tab, width=7, textvariable=minimum_radius)
minimum_radius_entry.grid(column = 8, row=5, sticky="EW")

# Number of points inside the inner circle used as threshold #
point_threshold_entry = ttk.Entry(expert_tab, width=7, textvariable=point_threshold)
point_threshold_entry.grid(column = 8, row=6, sticky="EW")

# Maximum point distance #
point_distance_entry = ttk.Entry(expert_tab, width=7, textvariable=point_distance)
point_distance_entry.grid(column = 8, row=7, sticky="EW")

# Number of sectors #
number_sectors_entry = ttk.Entry(expert_tab, width=7, textvariable=number_sectors)
number_sectors_entry.grid(column = 8, row=8, sticky="EW")

# Mnimum number of occupied sectors #
m_number_sectors_entry = ttk.Entry(expert_tab, width=7, textvariable=m_number_sectors)
m_number_sectors_entry.grid(column = 8, row=9, sticky="EW")

# Width #
circle_width_entry = ttk.Entry(expert_tab, width=7, textvariable=circle_width)
circle_width_entry.grid(column = 8, row=10, sticky="EW")


ttk.Label(expert_tab, text="Section width").grid(column = 7, row=2, sticky="W")
ttk.Label(expert_tab, text="Points within section").grid(column = 7, row=3, sticky="W")
ttk.Label(expert_tab, text="Inner/outer circle proportion").grid(column = 7, row=4, sticky="W")
ttk.Label(expert_tab, text="Minimum expected radius").grid(column = 7, row=5, sticky="W")
ttk.Label(expert_tab, text="Points within inner circle").grid(column = 7, row=6, sticky="W")
ttk.Label(expert_tab, text="Maximum point distance").grid(column = 7, row=7, sticky="W")
ttk.Label(expert_tab, text="Number of sectors").grid(column = 7, row=8, sticky="W")
ttk.Label(expert_tab, text="Number of occupied sectors").grid(column = 7, row=9, sticky="W")
ttk.Label(expert_tab, text="Circle width").grid(column = 7, row=10, sticky="W")

ttk.Label(expert_tab, text="meters").grid(column = 9, row=2, sticky="W")
ttk.Label(expert_tab, text="> 0").grid(column = 9, row=4, sticky="W")
ttk.Label(expert_tab, text="meters").grid(column = 9, row=5, sticky="W")
ttk.Label(expert_tab, text="meters").grid(column = 9, row=7, sticky="W")
ttk.Label(expert_tab, text="centimeters").grid(column = 9, row=10, sticky="W")


### Drawing circles and axes ###
ttk.Label(expert_tab, text="Drawing circles and axes", font = ("Helvetica", 10, "bold")).grid(column = 7, row=11, sticky="E")

# Circa points #
circa_entry = ttk.Entry(expert_tab, width=7, textvariable=circa)
circa_entry.grid(column = 8, row=12, sticky="EW")


# Point interval #
p_interval_entry = ttk.Entry(expert_tab, width=7, textvariable=p_interval)
p_interval_entry.grid(column = 8, row=13, sticky="EW")


# Axis lowest point #
axis_downstep_entry = ttk.Entry(expert_tab, width=7, textvariable=axis_downstep)
axis_downstep_entry.grid(column = 8, row=14, sticky="EW")


ttk.Label(expert_tab, text="N of points to draw each circle").grid(column = 7, row=12, sticky="W")
ttk.Label(expert_tab, text="Interval at which points are drawn").grid(column = 7, row=13, sticky="W")
ttk.Label(expert_tab, text="Axis upstep from stripe center").grid(column = 7, row=14, sticky="W")

    
### Other parameters ###
ttk.Label(expert_tab, text="Other parameters", font = ("Helvetica", 10, "bold")).grid(column = 7, row=15, sticky="E")

# Which column contains X field #
X_column_entry = ttk.Entry(expert_tab, width=7, textvariable=X_column)
X_column_entry.grid(column = 8, row=16, sticky="EW")


# Which column contains Y field #
Y_column_entry = ttk.Entry(expert_tab, width=7, textvariable=Y_column)
Y_column_entry.grid(column = 8, row=17, sticky="EW")


# Which column contains Z field #
Z_column_entry = ttk.Entry(expert_tab, width=7, textvariable=Z_column)
Z_column_entry.grid(column = 8, row=18, sticky="EW")


ttk.Label(expert_tab, text="X field").grid(column = 7, row=16, sticky="W")
ttk.Label(expert_tab, text="Y field").grid(column = 7, row=17, sticky="W")
ttk.Label(expert_tab, text="Z field").grid(column = 7, row=18, sticky="W")

for child in expert_tab.winfo_children(): 
    child.grid_configure(padx=5, pady=5)
    
#### Adding an info buttons ####

res_xy_stripe_info = ttk.Label(expert_tab, image = info_icon)
res_xy_stripe_info.grid(column = 1, row = 2)
gui.CreateToolTip(res_xy_stripe_info, text = '(x, y) voxel resolution during stem extraction.\n'
              'Default value: 0.035 meters.')

res_z_stripe_info = ttk.Label(expert_tab, image = info_icon)
res_z_stripe_info.grid(column = 1, row = 3)
gui.CreateToolTip(res_z_stripe_info, text = '(z) voxel resolution during stem extraction.\n'
              'Default value: 0.035 meters.')

number_of_points_info = ttk.Label(expert_tab, image = info_icon)
number_of_points_info.grid(column = 1, row = 4)
gui.CreateToolTip(number_of_points_info, text = 'minimum number of points per stem within the stripe\n'
              '(DBSCAN clustering). Reasonable values are between 500 and 3000.\n'
              'Default value: 1000.')

verticality_scale_stripe_info = ttk.Label(expert_tab, image = info_icon)
verticality_scale_stripe_info.grid(column = 1, row = 5)
gui.CreateToolTip(verticality_scale_stripe_info, text = 'Vicinity radius for PCA during stem extraction.\n'
              'Default value: 0.1 meters.')

verticality_thresh_stripe_info = ttk.Label(expert_tab, image = info_icon)
verticality_thresh_stripe_info.grid(column = 1, row = 6)
gui.CreateToolTip(verticality_thresh_stripe_info, text = 'Verticality threshold durig stem extraction.\n'
              'Default value: 0.7.')

epsilon_stripe_info = ttk.Label(expert_tab, image = info_icon)
epsilon_stripe_info.grid(column = 1, row = 7)
gui.CreateToolTip(epsilon_stripe_info, text = 'DBSCAN radius during stem extraction.\n'
              'Default value: 0.037 meters.')

res_xy_info = ttk.Label(expert_tab, image = info_icon)
res_xy_info.grid(column = 1, row = 9)
gui.CreateToolTip(res_xy_info, text = '(x, y) voxel resolution during tree individualization.\n'
              'Default value: 0.035 meters.')

res_z_info = ttk.Label(expert_tab, image = info_icon)
res_z_info.grid(column = 1, row = 10)
gui.CreateToolTip(res_z_info, text = '(z) voxel resolution during tree individualization.\n'
              'Default value: 0.035 meters.')

minimum_points_info = ttk.Label(expert_tab, image = info_icon)
minimum_points_info.grid(column = 1, row = 11)
gui.CreateToolTip(minimum_points_info, text = 'Minimum number of points within a stripe to consider it\n'
              'as a potential tree during tree individualization.\n'
              'Default value: 20.')

verticality_scale_stems_info = ttk.Label(expert_tab, image = info_icon)
verticality_scale_stems_info.grid(column = 1, row = 12)
gui.CreateToolTip(verticality_scale_stems_info, text = 'Vicinity radius for PCA during tree individualization.\n'
              'Default value: 0.1 meters.')

verticality_thresh_stems_info = ttk.Label(expert_tab, image = info_icon)
verticality_thresh_stems_info.grid(column = 1, row = 13)
gui.CreateToolTip(verticality_thresh_stems_info, text = 'Verticality threshold durig tree individualization.\n'
              'Default value: 0.7.')

epsilon_stems_info = ttk.Label(expert_tab, image = info_icon)
epsilon_stems_info.grid(column = 1, row = 14)
gui.CreateToolTip(epsilon_stems_info, text = 'DBSCAN radius during tree individualization.\n'
              'Default value: 0.08 meters.')

height_range_info = ttk.Label(expert_tab, image = info_icon)
height_range_info.grid(column = 1, row = 15)
gui.CreateToolTip(height_range_info, text = 'Only stems where points extend vertically throughout\n'
              'this range are considered.\n'
              'Default value: 1.2 meters.')

maximum_d_info = ttk.Label(expert_tab, image = info_icon)
maximum_d_info.grid(column = 1, row = 16)
gui.CreateToolTip(maximum_d_info, text = 'Points that are closer than this distance to an axis '
              'are assigned to that axis during individualize_trees process.\n'
              'Default value: 15 meters.')

res_heights_info = ttk.Label(expert_tab, image = info_icon)
res_heights_info.grid(column = 1, row = 17)
gui.CreateToolTip(res_heights_info, text = '(x, y, z) voxel resolution during tree height computation.\n'
              'Default value: 0.3 meters.')

maximum_dev_info = ttk.Label(expert_tab, image = info_icon)
maximum_dev_info.grid(column = 1, row = 18)
gui.CreateToolTip(maximum_dev_info, text = 'Maximum degree of vertical deviation from the axis for\n'
              'a tree height to be considered as valid.\n'
              'Default value: 25 degrees.')

section_wid_info = ttk.Label(expert_tab, image = info_icon)
section_wid_info.grid(column = 6, row = 2)
gui.CreateToolTip(section_wid_info, text = 'Sections are this wide. This means that points within this distance\n'
              '(vertical) are considered during circle fitting and diameter computation.\n'
              'Default value: 0.05 meters.')

number_points_section_info = ttk.Label(expert_tab, image = info_icon)
number_points_section_info.grid(column = 6, row = 3)
gui.CreateToolTip(number_points_section_info, text = 'Minimum number of points in a section to be considered\n'
              'as valid.\n'
              'Default value: 80.')

radius_proportion_info = ttk.Label(expert_tab, image = info_icon)
radius_proportion_info.grid(column = 6, row = 4)
gui.CreateToolTip(radius_proportion_info, text = 'Proportion, regarding the circumference fit by fit_circle,\n'
              'that the inner circumference radius will have as length.\n'
              'Default value: 0.5 times.')

minimum_radius_info = ttk.Label(expert_tab, image = info_icon)
minimum_radius_info.grid(column = 6, row = 5)
gui.CreateToolTip(minimum_radius_info, text = 'Minimum radius expected for any section during circle fitting.\n'
              'Default value: 0.03 meters.')

point_threshold_info = ttk.Label(expert_tab, image = info_icon)
point_threshold_info.grid(column = 6, row = 6)
gui.CreateToolTip(point_threshold_info, text = 'Minimum number of points inside the inner circle\n'
              'to consider the fitting as OK.\n'
              'Default value: 5.')

point_distance_info = ttk.Label(expert_tab, image = info_icon)
point_distance_info.grid(column = 6, row = 7)
gui.CreateToolTip(point_distance_info, text = 'Maximum distance among points to be considered within the\n'
              'same cluster during circle fitting.\n'
              'Default value: 0.02 meters.')

number_sectors_info = ttk.Label(expert_tab, image = info_icon)
number_sectors_info.grid(column = 6, row = 8)
gui.CreateToolTip(number_sectors_info, text = 'Number of sectors in which the circumference will be divided\n'
              'Default value: 16.')

m_number_sectors_info = ttk.Label(expert_tab, image = info_icon)
m_number_sectors_info.grid(column = 6, row = 9)
gui.CreateToolTip(m_number_sectors_info, text = 'Minimum number of sectors that must be occupied.\n'
              'Default value: 9.')

circle_width_info = ttk.Label(expert_tab, image = info_icon)
circle_width_info.grid(column = 6, row = 10)
gui.CreateToolTip(circle_width_info, text = 'Width, in centimeters, around the circumference to look\n'
              'for points.\n'
              'Defaul value: 2 centimeters.')

circa_info = ttk.Label(expert_tab, image = info_icon)
circa_info.grid(column = 6, row = 12)
gui.CreateToolTip(circa_info, text = 'Number of points that will be used to draw the circles\n '
              'in the LAS files.\n'
              'Default value: 200.')

p_interval_info = ttk.Label(expert_tab, image = info_icon)
p_interval_info.grid(column = 6, row = 13)
gui.CreateToolTip(p_interval_info, text = 'Distance at which points will be placed from one to another\n'
              'while drawing the axes in the LAS files.\n'
              'Default value: 0.01 meters.')

axis_downstep_info = ttk.Label(expert_tab, image = info_icon)
axis_downstep_info.grid(column = 6, row = 14)
gui.CreateToolTip(axis_downstep_info, text = 'From the stripe centroid, how much (downwards direction)\n'
              'will the drawn axes extend. Basically, this parameter controls\n'
              'from where will the axes be drawn.\n'
              'Default value: 0.5 meters.')

X_column_info = ttk.Label(expert_tab, image = info_icon)
X_column_info.grid(column = 6, row = 16)
gui.CreateToolTip(X_column_info, text = 'Which column contains X field.\n'
              'Default value: 0.')

Y_column_info = ttk.Label(expert_tab, image = info_icon)
Y_column_info.grid(column = 6, row = 17)
gui.CreateToolTip(Y_column_info, text = 'Which column contains Y field.\n'
              'Default value: 1.')

Z_column_info = ttk.Label(expert_tab, image = info_icon)
Z_column_info.grid(column = 6, row = 18)
gui.CreateToolTip(Z_column_info, text = 'Which column contains Z field.\n'
              'Default value: 2.')

warning_img = ImageTk.PhotoImage(Image.open(resource_path("warning_img_1.png")))

#### Warning button ####
def open_warning():
   new = Toplevel(root)
   new.geometry("670x335")
   new.title("WARNING")
   ttk.Label(new, image = warning_img).grid(column = 2, row = 1, rowspan = 3, sticky = "E")
   ttk.Label(new, text = "This is the expert parameters tab.", font=("Helvetica", 10)).grid(column = 1, row = 1, sticky = "W")
   ttk.Label(new, text = "Are you sure you know what these do?", font = ("Helvetica", 10, "bold")).grid(column = 1, row = 2, sticky = "W")
   ttk.Label(new, text = "Before modifying these, you should read the documentation and the\n"
             "references listed below for a deep understading of what the algorithm does.", font = ("Helvetica", 10)).grid(column = 1, row = 3, sticky = "W")
   
   ttk.Label(new, text = "References:", font = ("Helvetica", 11)).grid(column = 1, row = 4, sticky = "W")
   ttk.Label(new, text = "Cabo, C., Ordonez, C., Lopez-Sanchez, C. A., & Armesto, J. (2018). Automatic dendrometry:\n"
             "Tree detection, tree height and diameter estimation using terrestrial laser scanning.\n"
             "International Journal of Applied Earth Observation and Geoinformation, 69, 164–174.\n"
             "https://doi.org/10.1016/j.jag.2018.01.011", font = ("Helvetica", 10)).grid(column = 1, row = 5, sticky = "W")
   
   ttk.Label(new, text = "Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996). A Density-Based Algorithm for\n"
             "Discovering Clusters in Large Spatial Databases with Noise. www.aaai.org", font = ("Helvetica", 10)).grid(column = 1, row = 6, sticky = "W")
   
   ttk.Label(new, text = "Prendes, C., Cabo, C., Ordoñez, C., Majada, J., & Canga, E. (2021). An algorithm for\n"
             "the automatic parametrization of wood volume equations from Terrestrial Laser Scanning\n"
             "point clouds: application in Pinus pinaster. GIScience and Remote Sensing, 58(7), 1130–1150.\n"
             "https://doi.org/10.1080/15481603.2021.1972712 ", font = ("Helvetica", 10)).grid(column = 1, row = 7, sticky = "W")
   
   for child in new.winfo_children(): 
       child.grid_configure(padx=3, pady=3)


Button(expert_tab, text='What is this?', bg = "IndianRed1", width = 12, font = ("Helvetica", 10, "bold"), cursor="hand2", command=open_warning).grid(column = 9, row = 1, columnspan = 2, sticky = "E")


### ----------------------------- ###
### ------- Editing tab 4 ------- ###
### ----------------------------- ###

note.add(about_tab, text = "About")

### SCROLLBAR ###

# Create a frame for the canvas with non-zero row&column weights
frame_canvas = ttk.Frame(about_tab)
frame_canvas.grid(row=0, column=0, pady=(5, 0), sticky='nw')
frame_canvas.grid_rowconfigure(0, weight=1)
frame_canvas.grid_columnconfigure(0, weight=1)
# Set grid_propagate to False to allow 5-by-5 buttons resizing later
frame_canvas.grid_propagate(False)

# Add a canvas in that frame
canvas = Canvas(frame_canvas)
canvas.grid(row=0, column=0, sticky="news")

# Link a scrollbar to the canvas
vsb = ttk.Scrollbar(frame_canvas, orient="vertical", command=canvas.yview)
vsb.grid(row=0, column=1, sticky='ns')
canvas.configure(yscrollcommand=vsb.set)

# Create a frame to contain the info
scrollable = ttk.Frame(canvas)

### COPYRIGHT ###
copyright_info_1 = """ 3DFIN: Forest Inventory Copyright (C) 2023 Carlos Cabo & Diego Laino."""

copyright_info_2 = """This program comes with ABSOLUTELY NO WARRANTY. This is a free software, and you are welcome to redistribute it under certain conditions."""

copyright_info_3 = """See LICENSE at the botton of this tab for further details."""

### ABOUT THE PROJECT ###

about = """This software has been developed by the Centre of Wildfire Research at the Faculty of Science & Engineering, Swansea University in collaboration 
with the Department of Mining Exploitation of University of Oviedo, under the UK NERC funded project (NERC reference: NE/T001194/1):"""

nerc_project = """'Advancing 3D Fuel Mapping for Wildfire Behaviour and Risk Mitigation Modelling'."""

### TEAM MEMBERS ###

carloscabo = """Carlos Cabo (carloscabo.uniovi@gmail.com). PhD in Geomatics. 'Maria Zambrano' Research Fellow at Department of 
Mining Exploitation, University of Oviedo and Honorary Appointment at Science and Engineering Faculty, Swansea 
University. Research fields: Spatial analysis, cartography, geomatics."""

diegolaino = """Diego Laino (diegolainor@gmail.com). PhD student in Natural Resources Engineering at Department of Mining Exploit-
ation, University of Oviedo. Assist. Researcher at Centre for Wildfire Research, Geography Department, Swansea Univer-
sity. Research fields: deep learning, remote sensing, forestry."""

crissantin = """Cristina Santin (c.santin@csic.es). Research fellow at the Research Institute of Biodiversity (CSIC-University of Oviedo 
- Principality of Asturias, Spain) and Honorary Assoc. Professor at the Biosciences Department of Swansea University. 
Research fields: environmental impacts of wildfires."""

stefandoerr = """Stefan Doerr (s.doerr@swansea.ac.uk). PhD in Geography. Full Professor at the Geography Department, Swansea Univer-
sity and Director of its Centre for Wildfire Research. Editor-in-Chief: International Journal of Wildland Fire. Research fields:
wildfires, landscape carbon dynamics, soils, water quality, ecosystem services."""

celestinoordonez = """Celestino Ordonez (ordonezcelestino@uniovi.es). PhD in Mine Engineering. Full professor at Department of Mining Ex-
ploitation, University of Oviedo. Main researcher at GEOGRAPH research group. Research fields: Spatial analysis, laser 
scanning, photogrammetry."""

tadasnikonovas = """Tadas Nikonovas (tadas.nikonovas@swansea.ac.uk). PhD in Geography. Office Researcher at Centre for Wildfire Research, 
Geography Department, Swansea University. Research fields: Global fire activity, atmospheric emissions, fire occurrence 
modelling."""

covadongaprendes = """Covadonga Prendes (cprendes@cetemas.es). PhD in Geomatics. Forest engineer and researcher at CETEMAS (Forest and 
Wood Technology Research Centre Foundation). Geomatics research group. Research fields: LiDAR, sustainable forestry 
development, spatial analysis. """



# Copyright notice #
copyright_1_lab = ttk.Label(scrollable, text = copyright_info_1, font = ("Helvetica", 10, "bold"))
copyright_1_lab.grid(row = 1, column = 1, columnspan = 3)

copyright_2_lab = ttk.Label(scrollable, text = copyright_info_2)
copyright_2_lab.grid(row = 2, column = 1, columnspan = 3)

copyright_3_lab = ttk.Label(scrollable, text = copyright_info_3)
copyright_3_lab.grid(row = 3, column = 1, columnspan = 3)

# About the project #
about_lab = ttk.Label(scrollable, text = about)
about_lab.grid(row = 4, column = 1, columnspan = 3)

nerc_project_lab = ttk.Label(scrollable, text = nerc_project, font = ("Helvetica", 10, "italic"))
nerc_project_lab.grid(row = 5, column = 1, columnspan = 3)

nerc_logo_img = ImageTk.PhotoImage(Image.open(resource_path("nerc_logo_1.png")))
ttk.Label(scrollable, image = nerc_logo_img).grid(row = 6, column = 1, columnspan = 3, sticky = "W")

swansea_logo_img = ImageTk.PhotoImage(Image.open(resource_path("swansea_logo_1.png")))
ttk.Label(scrollable, image = swansea_logo_img).grid(row = 6, column = 1, columnspan = 3, sticky = "E")

uniovi_logo_img = ImageTk.PhotoImage(Image.open(resource_path("uniovi_logo_1.png")))
ttk.Label(scrollable, image = uniovi_logo_img).grid(row = 6, column = 1, columnspan = 3)

ttk.Separator(scrollable, orient = "horizontal").grid(row = 7, column = 1, columnspan = 3, sticky = "EW")

team_lab = ttk.Label(scrollable, text = 'Team', font = ("Helvetica", 12, "bold"))
team_lab.grid(row = 8, column = 1, columnspan = 3)

carloscabo_lab = ttk.Label(scrollable, text = carloscabo)
carloscabo_lab.grid(row = 9, column = 2, columnspan = 2, sticky="W")

diegolaino_lab = ttk.Label(scrollable, text = diegolaino)
diegolaino_lab.grid(row = 10, column = 2, columnspan = 2, sticky="W")

crissantin_lab = ttk.Label(scrollable, text = crissantin)
crissantin_lab.grid(row = 11, column = 2, columnspan = 2, sticky="W")

stefandoerr_lab = ttk.Label(scrollable, text = stefandoerr)
stefandoerr_lab.grid(row = 12, column = 2, columnspan = 2, sticky="W")

celestinoordonez_lab = ttk.Label(scrollable, text = celestinoordonez)
celestinoordonez_lab.grid(row = 13, column = 2, columnspan = 2, sticky="W")

tadasnikonovas_lab = ttk.Label(scrollable, text = tadasnikonovas)
tadasnikonovas_lab.grid(row = 14, column = 2, columnspan = 2, sticky="W")

covadongaprendes_lab = ttk.Label(scrollable, text = covadongaprendes)
covadongaprendes_lab.grid(row = 15, column = 2, columnspan = 2, sticky = "W")

carlos_img = ImageTk.PhotoImage(Image.open(resource_path("carlos_pic_1.jpg")))
ttk.Label(scrollable, image = carlos_img).grid(row = 9, column = 1)

diego_img = ImageTk.PhotoImage(Image.open(resource_path("diego_pic_1.jpg")))
ttk.Label(scrollable, image = diego_img).grid(row = 10, column = 1)

cris_img = ImageTk.PhotoImage(Image.open(resource_path("cris_pic_1.jpg")))
ttk.Label(scrollable, image = cris_img).grid(row = 11, column = 1)

stefan_img = ImageTk.PhotoImage(Image.open(resource_path("stefan_pic_1.jpg")))
ttk.Label(scrollable, image = stefan_img).grid(row = 12, column = 1)

celestino_img = ImageTk.PhotoImage(Image.open(resource_path("celestino_pic_1.jpg")))
ttk.Label(scrollable, image = celestino_img).grid(row = 13, column = 1)

tadas_img = ImageTk.PhotoImage(Image.open(resource_path("tadas_pic_1.jpg")))
ttk.Label(scrollable, image = tadas_img).grid(row = 14, column = 1)

covadonga_img = ImageTk.PhotoImage(Image.open(resource_path("covadonga_pic_1.jpg")))
ttk.Label(scrollable, image = covadonga_img).grid(row = 15, column = 1)

f = open(resource_path("License.txt"),"r")
gnu_license = f.read()

#### license button ####
def open_license():
   new = Toplevel(scrollable)
   
   # Create a frame for the canvas with non-zero row&column weights
   license_frame_canvas = ttk.Frame(new)
   license_frame_canvas.grid(row=0, column=0, pady=(0, 0), sticky='nw')
   license_frame_canvas.grid_rowconfigure(0, weight=1)
   license_frame_canvas.grid_columnconfigure(0, weight=1)
   
   # Set grid_propagate to False to allow 5-by-5 buttons resizing later
   license_frame_canvas.grid_propagate(False)
   
   # Add a canvas in that frame
   license_canvas = Canvas(license_frame_canvas)
   license_canvas.grid(row=0, column=0, sticky="news")

   # Link a scrollbar to the canvas
   license_vsb = ttk.Scrollbar(license_frame_canvas, orient="vertical", command=license_canvas.yview)
   license_vsb.grid(row=0, column=1, sticky='ns')
   license_canvas.configure(yscrollcommand=license_vsb.set)
   
   # Create a frame to contain the info
   license_scrollable = ttk.Frame(license_canvas)
   
   new.geometry("620x400")
   new.title("LICENSE")
   ttk.Label(license_scrollable, text = "GNU GENERAL PUBLIC LICENSE", font = ("Helvetica", 10, "bold"), anchor = "E", justify="LEFT").grid(row = 1, column = 1)
   
   ttk.Label(license_scrollable, text = gnu_license, font = ("Helvetica", 10)).grid(row = 2, column = 1)
   
   # Create canvas window to hold the buttons_frame.
   license_canvas.create_window((0, 0), window=license_scrollable, anchor='nw')

   # Update buttons frames idle tasks to let tkinter calculate buttons sizes
   license_scrollable.update_idletasks()

   license_frame_canvas.config(width=620,
                               height=400)

   # Set the canvas scrolling region
   license_canvas.config(scrollregion=license_canvas.bbox("all"))
   
   for child in license_scrollable.winfo_children(): 
       child.grid_configure(padx=5, pady=5)

ttk.Separator(scrollable, orient = "horizontal").grid(row = 16, column = 1, columnspan = 3, sticky = "EW")

Button(scrollable, text='License', width = 8, font = ("Helvetica", 10, "bold"), cursor="hand2", command=open_license).grid(row = 17, column = 1, columnspan = 3)


for child in scrollable.winfo_children(): 
    child.grid_configure(padx=5, pady=5)

# Create canvas window to hold the buttons_frame.
canvas.create_window((0, 0), window=scrollable, anchor='nw')

# Update buttons frames idle tasks to let tkinter calculate buttons sizes
scrollable.update_idletasks()

frame_canvas.config(width=810,
                    height=540)

# Set the canvas scrolling region
canvas.config(scrollregion=canvas.bbox("all"))


### -------------------------------------- ###
### ------- Button to close the GUI------- ###
### -------------------------------------- ###    
Button(root, text='Select file & compute', bg = "light green", width = 30, font = ("Helvetica", 10, "bold"), cursor="hand2", command=root.destroy).grid(sticky = "S")

#### Adding a hyperlink to the documentation ####

link1 = ttk.Label(root, text=" Documentation", font = ("Helvetica", 11), foreground = "blue", cursor="hand2")
link1.grid(sticky = "NW")
link1.bind("<Button-1>", lambda e: os.system(resource_path("documentation.pdf")))


root.mainloop()

# ---------------------- #

#-------------------------------------------------------------------------------------------------
# BASIC PARAMETERS. These are the parameters to be checked (and changed if needed) for each dataset/plot
# All parameters are in m or points
#-------------------------------------------------------------------------------------------------

is_normalized = is_normalized_var.get()
is_noisy = is_noisy_var.get()

field_name_z0 = z0_name.get() # Name of the Z0 field in the LAS file containing the cloud. 
# If the normalized heights are stored in the Z coordinate of the .LAS file: field_name_z0 = "z" (lowercase)

# Upper and lower limits (vertical) of the stripe where it should be reasonable to find stems with minimum presence of shrubs or branches.
stripe_upper_limit = float(upper_limit.get()) # Values, normally between 2 and 5
stripe_lower_limit = float(lower_limit.get()) # Values, normally between 0.3 and 1.3

n_iter = int(number_of_iterations.get()) # Number of iterations of 'peeling off branches'. 
# Values between 0 (no branch peeling/cleaning) and 5 (very extreme branch peeling/cleaning)

#-------------------------------------------------------------------------------------------------
# INTERMEDIATE PARAMETERS. They should only be modified when no good results are obtained tweaking basic parameters.
# They require a deeper knowledge of how the algorithm and the implementation work
#-------------------------------------------------------------------------------------------------

expected_R = float(stem_search_radius.get()) # Points within this distance from tree axes will be considered as potential stem points. 
# Values between R_max and 1 (exceptionally greater than 1: very large diameters and/or intricate stems)

R_max = float(maximum_radius.get()) # Maximum radius expected for any section during circle fitting.

min_h = float(minimum_height.get()) # Lowest height
max_h = float(maximum_height.get()) # highest height

section_length = float(section_len.get()) # sections are this long (z length)

d_heights = float(distance_to_axis.get()) # Points within this distance from tree axes will be used to find tree height

line_upstep = float(axis_upstep.get()) # From the stripe centroid, how much (upwards direction) will the drawn axes extend.


#-------------------------------------------------------------------------------------------------
# EXPERT PARAMETERS. They should only be modified when no good results are obtained peaking basic parameters.
# They require a deeper knowledge of how the algorithm and the implementation work
# *Stored in the main script in this version.
#-------------------------------------------------------------------------------------------------


#-------------------------------------------------------------------------------------------------
# Stem extraction
#-------------------------------------------------------------------------------------------------
resolution_xy_stripe = float(res_xy_stripe.get())  # (x, y) voxel resolution during stem extraction
resolution_z_stripe = float(res_z_stripe.get())  # (z) voxel resolution during stem extraction

n_points = int(number_of_points.get()) # minimum number of points per stem within the stripe (DBSCAN clustering). 
# Values, normally between 500 and 3000 

n_points_stripe = int(number_of_points.get())  # DBSCAN minimum number of points during stem extraction
eps_stripe = float(epsilon_stripe.get()) # DBSCAN radius during stem extraction

vert_scale_stripe = float(verticality_scale_stripe.get()) # Vicinity radius for PCA during stem extraction
vert_threshold_stripe = float(verticality_thresh_stripe.get())  # Verticality threshold durig stem extraction

n_iter_stripe = n_iter  # Number of iterations of 'peeling off branchs' during stem extraction

#-------------------------------------------------------------------------------------------------
# Tree individualization.
#-------------------------------------------------------------------------------------------------
resolution_xy = float(res_xy.get())  # (x, y) voxel resolution during tree individualization
resolution_z = float(res_z.get())  # (z) voxel resolution during tree individualization

min_points = int(minimum_points.get()) # Minimum number of points within a stripe to consider it as a potential tree during tree individualization
eps_stems = float(epsilon_stems.get()) # DBSCAN radius during tree individualization

vert_scale_stems = float(verticality_scale_stems.get()) # Vicinity radius for PCA  during tree individualization
vert_threshold_stems = float(verticality_thresh_stems.get()) # Verticality threshold  during tree individualization

h_range = float(height_range.get())  # only stems where points extend vertically throughout this range are considered. 

d_max = float(maximum_d.get()) # Points that are closer than d_max to an axis are assigned to that axis during individualize_trees process.

resolution_heights = float(res_heights.get()) # Resolution for the voxelization while computing tree heights 
max_dev = float(maximum_dev.get()) # Maximum degree of vertical deviation from the axis

n_iter_stems = n_iter # Number of iterations of 'peeling off branchs' during tree individualization

n_points_stems = n_points # DBSCAN minimum number of points during tree individualization 

#-------------------------------------------------------------------------------------------------
# Extracting sections.
#-------------------------------------------------------------------------------------------------

section_width = float(section_wid.get()) # sections are this wide
n_points_section = int(number_points_section.get()) # Minimum number of points in a section to be considered
times_R = float(radius_proportion.get()) # Proportion, regarding the circumference fit by fit_circle, that the inner circumference radius will have as length
R_min = float(minimum_radius.get()) # Minimum radius expected for any section circle fitting.
threshold = int(point_threshold.get()) # Number of points inside the inner circle
max_dist = float(point_distance.get()) # Maximum distance among points to be considered within the same cluster.
n_sectors = int(number_sectors.get()) # Number of sectors in which the circumference will be divided
min_n_sectors = int(m_number_sectors.get()) # Minimum number of sectors that must be occupied.
width = float(circle_width.get()) # Width, in centimeters, around the circumference to look for points

#-------------------------------------------------------------------------------------------------
# Drawing circles.
#-------------------------------------------------------------------------------------------------
circa_points = int(circa.get())

#-------------------------------------------------------------------------------------------------
# Drawing axes.
#-------------------------------------------------------------------------------------------------
point_interval = float(p_interval.get())
line_downstep = float(axis_downstep.get())

#-------------------------------------------------------------------------------------------------
# NON MODIFIABLE. These parameters should never be modified by the user.
#-------------------------------------------------------------------------------------------------

X_field = int(X_column.get()) # Which column contains X field  - NON MODIFIABLE
Y_field = int(Y_column.get()) # Which column contains Y field  - NON MODIFIABLE
Z_field = int(Z_column.get()) # Which column contains Z field  - NON MODIFIABLE

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

print(copyright_info_1)
print(copyright_info_2)
print("See License at the bottom of 'About' tab for more details or visit <https://www.gnu.org/licenses/>")

t_t = timeit.default_timer()


if is_normalized:
    
    # Read .LAS file. It must contain a Z0 field (normalized height). 
    entr = laspy.read(filename_las)
    coords = np.vstack((entr.x, entr.y, entr.z, entr[field_name_z0])).transpose()
    
    # Number of points and area occuped by the plot. 
    print('---------------------------------------------')
    print('Analyzing cloud size...')
    print('---------------------------------------------')

    _, _, voxelated_ground = dm.voxelate(coords[coords[:, 3] < 0.5, 0:3], 1, 2000, n_digits, with_n_points = False, silent = False)

    print('   This cloud has',"{:.2f}".format(coords.shape[0]/1000000),'millions points')
    print('   Its area is ',voxelated_ground.shape[0],'m^2')
    
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

    print('   This cloud has',"{:.2f}".format(coords.shape[0]/1000000),'millions points')
    print('   Its area is ',voxelated_ground.shape[0],'m^2')
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
        clean_points = dm.clean_ground(coords)
        
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
        cloth_nodes = dm.generate_dtm(coords)
        
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
clust_stripe = dm.verticality_clustering(stripe, vert_scale_stripe, vert_threshold_stripe, eps_stripe, n_points_stripe, n_iter_stripe, resolution_xy_stripe, resolution_z_stripe, n_digits)

print('---------------------------------------------')
print('2.-Computing distances to axes and individualizating trees...')
print('---------------------------------------------')
                                                                                       
assigned_cloud, tree_vector, tree_heights = dm.individualize_trees(coords, clust_stripe, resolution_z, resolution_xy, h_range, d_max, min_points, d_heights, max_dev, resolution_heights, n_digits, X_field, Y_field, Z_field, tree_id_field = -1)     

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
stems = dm.verticality_clustering(xyz0_coords, vert_scale_stems, vert_threshold_stems, eps_stems, n_points_stems, n_iter_stems, resolution_xy_stripe, resolution_z_stripe, n_digits)[:, 0:6]


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
print('End of process!')
print('---------------------------------------------')
print('Total time:',"   %.2f" % elapsed_t,'s')
print('nº of trees:',X_c.shape[0])

input("Press enter to close the program...")
