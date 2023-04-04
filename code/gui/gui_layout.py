import configparser
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from .tooltip import ToolTip
from PIL import Image, ImageTk


class Application(tk.Tk):
    def __init__(self, processing_callback: callable):
        tk.Tk.__init__(self)
        self.processing_callback = processing_callback
        self._bootstrap()

    def _get_resource_path(self, relative_path: str) -> str:
        """
        This method allows to retrieve the path of the data used to generate the images and
        the documentation, so they can be included in the executable

            Parameters:
                relatvie_path (str): the current relative path to the ressource

            Returns:
                str: the full path to the ressource
        """
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = Path(__file__).absolute().parents[2] / "files"
        return str(base_path / Path(relative_path))

    def _preload_images(self):
        """
        Centralise image loading
        TODO(RJ): Add license loading too
        """
        self.warning_img = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("warning_img_1.png"))
        )
        self.nerc_logo_img = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("nerc_logo_1.png"))
        )
        self.swansea_logo_img = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("swansea_logo_1.png"))
        )
        self.spain_logo_img = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("spain_logo_1.png"))
        )
        self.csic_logo_img = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("csic_logo_1.png"))
        )
        self.uniovi_logo_img = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("uniovi_logo_1.png"))
        )
        self.carlos_img = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("carlos_pic_1.jpg"))
        )
        self.diego_img = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("diego_pic_1.jpg"))
        )
        self.cris_img = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("cris_pic_1.jpg"))
        )
        self.stefan_img = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("stefan_pic_1.jpg"))
        )
        self.celestino_img = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("celestino_pic_1.jpg"))
        )
        self.tadas_img = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("tadas_pic_1.jpg"))
        )
        self.covadonga_img = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("covadonga_pic_1.jpg"))
        )
        self.info_icon = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("info_icon.png"))
        )
        self.img_stripe = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("stripe.png"))
        )
        self.img_cloud = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("original_cloud.png"))
        )
        self.img_normalized_cloud = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("normalized_cloud.png"))
        )

    def _generate_parameters(self):
        """
        Generate dendromatics mandatory parameters
        The methods tries to load a config file in the root of the source code and if it fails,
        it fallback to default parameters hardcoded here.
        """
        ### Basic parameters
        self.z0_name = tk.StringVar()
        self.upper_limit = tk.StringVar()
        self.lower_limit = tk.StringVar()
        self.number_of_iterations = tk.StringVar()

        ### Advanced parameters
        self.maximum_diameter = tk.StringVar()
        self.stem_search_diameter = tk.StringVar()
        self.minimum_height = tk.StringVar()
        self.maximum_height = tk.StringVar()
        self.section_len = tk.StringVar()
        self.section_wid = tk.StringVar()

        ### Expert parameters
        # Stem identification 
        self.res_xy_stripe = tk.StringVar()
        self.res_z_stripe = tk.StringVar()
        self.number_of_points = tk.StringVar()
        self.verticality_scale_stripe = tk.StringVar()
        self.verticality_thresh_stripe = tk.StringVar()
        self.height_range = tk.StringVar()

        # Stem extraction and Tree individualization
        self.res_xy = tk.StringVar()
        self.res_z = tk.StringVar()
        self.minimum_points = tk.StringVar()
        self.verticality_scale_stems = tk.StringVar()
        self.verticality_thresh_stems = tk.StringVar()
        self.maximum_d = tk.StringVar()
        self.distance_to_axis = tk.StringVar()
        self.res_heights = tk.StringVar()
        self.maximum_dev = tk.StringVar()

        # Extracting sections
        self.number_points_section = tk.StringVar()
        self.diameter_proportion = tk.StringVar()
        self.minimum_diameter = tk.StringVar()
        self.point_threshold = tk.StringVar()
        self.point_distance = tk.StringVar()
        self.number_sectors = tk.StringVar()
        self.m_number_sectors = tk.StringVar()
        self.circle_width = tk.StringVar()

        # Drawing circles and axes
        self.circa = tk.StringVar()
        self.p_interval = tk.StringVar()
        self.axis_downstep = tk.StringVar()
        self.axis_upstep = tk.StringVar()

        # Other parameters
        self.res_ground = tk.StringVar()
        self.min_points_ground = tk.StringVar()
        self.res_cloth = tk.StringVar()

        # TODO: misc parameters. These parameters have no entry in the option file
        # but they are needed for processing and exposed in the GUI
        # Variable to keep track of the option selected in normalized_button_1
        self.is_normalized_var = tk.BooleanVar()
        # Variable to keep track of the option selected in clean_button_1
        self.is_noisy_var = tk.BooleanVar()
        # Variable to keep track of the option selected in excel_button_1
        self.txt_var = tk.BooleanVar()

        ### Reading config file only if it is available under name '3DFINconfig.ini'
        my_file = Path("3DFINconfig.ini")

        try:
            my_abs_path = my_file.resolve(strict=True)

        except FileNotFoundError:
            ### Basic parameters
            self.z0_name.set("Z0")
            self.upper_limit.set("3.5")
            self.lower_limit.set("0.7")
            self.number_of_iterations.set("2")

            ### Advanced parameters
            self.maximum_diameter.set("1.0")
            self.stem_search_diameter.set("2.0")
            self.minimum_height.set("0.3")
            self.maximum_height.set("25")
            self.section_len.set("0.2")
            self.section_wid.set("0.05")

            ### Expert parameters

            # Stem identification
            self.res_xy_stripe.set("0.02")
            self.res_z_stripe.set("0.02")
            self.number_of_points.set("1000")
            self.verticality_scale_stripe.set("0.1")
            self.verticality_thresh_stripe.set("0.7")
            self.height_range.set("0.7")

            # Stem extraction and Tree individualization
            self.res_xy.set("0.035")
            self.res_z.set("0.035")
            self.minimum_points.set("20")
            self.verticality_scale_stems.set("0.1")
            self.verticality_thresh_stems.set("0.7")
            self.maximum_d.set("15")
            self.distance_to_axis.set("1.5")
            self.res_heights.set("0.3")
            self.maximum_dev.set("25")

            # Extracting sections
            self.number_points_section.set("80")
            self.diameter_proportion.set("0.5")
            self.minimum_diameter.set("0.06")
            self.point_threshold.set("5")
            self.point_distance.set("0.02")
            self.number_sectors.set("16")
            self.m_number_sectors.set("9")
            self.circle_width.set("0.02")

            # Drawing circles and axes
            self.circa.set("200")
            self.p_interval.set("0.01")
            self.axis_downstep.set("0.5")
            self.axis_upstep.set("10")

            # Other parameters
            self.res_ground.set("0.15")
            self.min_points_ground.set("2")
            self.res_cloth.set("2")

        else:
            print("Configuration file found. Default parameters have been established.")

            ### Reading the config file
            config = configparser.ConfigParser()
            config.read(my_abs_path)

            ### Basic parameters
            self.z0_name.set(config["basic"]["z0_name"])
            self.upper_limit.set(config["basic"]["upper_limit"])
            self.lower_limit.set(config["basic"]["lower_limit"])
            self.number_of_iterations.set(config["basic"]["number_of_iterations"])

            ### Advanced parameters
            self.maximum_diameter.set(config["advanced"]["maximum_diameter"])
            self.stem_search_diameter.set(config["advanced"]["stem_search_diameter"])
            self.minimum_height.set(config["advanced"]["minimum_height"])
            self.maximum_height.set(config["advanced"]["maximum_height"])
            self.section_len.set(config["advanced"]["section_len"])
            self.section_wid.set(config["advanced"]["section_wid"])

            ### Expert parameters

            # Stem identification whithin the stripe
            self.res_xy_stripe.set(config["expert"]["res_xy_stripe"])
            self.res_z_stripe.set(config["expert"]["res_z_stripe"])
            self.number_of_points.set(config["expert"]["number_of_points"])
            self.verticality_scale_stripe.set(
                config["expert"]["verticality_scale_stripe"]
            )
            self.verticality_thresh_stripe.set(
                config["expert"]["verticality_thresh_stripe"]
            )
            self.height_range.set(config["expert"]["height_range"])

            # Stem extraction and tree individualization
            self.res_xy.set(config["expert"]["res_xy"])
            self.res_z.set(config["expert"]["res_z"])
            self.minimum_points.set(config["expert"]["minimum_points"])
            self.verticality_scale_stems.set(
                config["expert"]["verticality_scale_stems"]
            )
            self.verticality_thresh_stems.set(
                config["expert"]["verticality_thresh_stems"]
            )
            self.maximum_d.set(config["expert"]["maximum_d"])
            self.distance_to_axis.set(config["expert"]["distance_to_axis"])
            self.res_heights.set(config["expert"]["res_heights"])
            self.maximum_dev.set(config["expert"]["maximum_dev"])

            # Extracting sections
            self.number_points_section.set(config["expert"]["number_points_section"])
            self.diameter_proportion.set(config["expert"]["diameter_proportion"])
            self.minimum_diameter.set(config["expert"]["minimum_diameter"])
            self.point_threshold.set(config["expert"]["point_threshold"])
            self.point_distance.set(config["expert"]["point_distance"])
            self.number_sectors.set(config["expert"]["number_sectors"])
            self.m_number_sectors.set(config["expert"]["m_number_sectors"])
            self.circle_width.set(config["expert"]["circle_width"])

            # Drawing circles and axes
            self.circa.set(config["expert"]["circa"])
            self.p_interval.set(config["expert"]["p_interval"])
            self.axis_downstep.set(config["expert"]["axis_downstep"])
            self.axis_upstep.set(config["expert"]["axis_upstep"])

            # Other parameters
            self.res_ground.set(config["expert"]["res_ground"])
            self.min_points_ground.set(config["expert"]["min_points_ground"])
            self.res_cloth.set(config["expert"]["res_cloth"])

    def get_parameters(self) -> dict:
        """Returns parameters as a dictionary"""
        params = {}
        params["misc"] = {}
        params["basic"] = {}
        params["expert"] = {}
        params["advanced"] = {}

        # misc parameters see TODO section in the _generate_parameters method
        params["misc"]["is_normalized"] = self.is_normalized_var.get()
        params["misc"]["is_noisy"] = self.is_noisy_var.get()
        params["misc"]["txt"] = self.txt_var.get()

        # -------------------------------------------------------------------------------------------------
        # BASIC PARAMETERS. These are the parameters to be checked (and changed if needed) for each dataset/plot
        # All parameters are in m or points
        # -------------------------------------------------------------------------------------------------

        params["basic"]["z0_name"] = (
            self.z0_name.get()
        )  # Name of the Z0 field in the LAS file containing the cloud.
        # If the normalized heights are stored in the Z coordinate of the .LAS file: field_name_z0 = "z" (lowercase)

        # Upper and lower limits (vertical) of the stripe where it should be reasonable to find stems with minimum presence of shrubs or branches.
        params["basic"]["upper_limit"] = float(
            self.upper_limit.get()
        )  # Values, normally between 2 and 5
        params["basic"]["lower_limit"] = float(
            self.lower_limit.get()
        )  # Values, normally between 0.3 and 1.3

        params["basic"]["number_of_iterations"] = int(
            self.number_of_iterations.get()
        )  # Number of iterations of 'peeling off branches'.
        # Values between 0 (no branch peeling/cleaning) and 5 (very extreme branch peeling/cleaning)

        # -------------------------------------------------------------------------------------------------
        # Advanced PARAMETERS. They should only be modified when no good results are obtained tweaking basic parameters.
        # They require a deeper knowledge of how the algorithm and the implementation work
        # -------------------------------------------------------------------------------------------------

        params["advanced"]["stem_search_diameter"] = (
            float(self.stem_search_diameter.get()) / 2
        )  # Points within this distance from tree axes will be considered as potential stem points.
        # Values between maximum diameter and 1 (exceptionally greater than 1: very large diameters and/or intricate stems)

        params["advanced"]["maximum_diameter"] = (
            float(self.maximum_diameter.get()) / 2
        )  # Maximum radius expected for any section during circle fitting.

        params["advanced"]["minimum_height"] = float(
            self.minimum_height.get()
        )  # Lowest height
        params["advanced"]["maximum_height"] = float(
            self.maximum_height.get()
        )  # highest height

        params["advanced"]["section_len"] = float(
            self.section_len.get()
        )  # sections are this long (z length)
        params["advanced"]["section_wid"] = float(
            self.section_wid.get()
        )  # sections are this wide

        # -------------------------------------------------------------------------------------------------
        # EXPERT PARAMETERS. They should only be modified when no good results are obtained peaking basic parameters.
        # They require a deeper knowledge of how the algorithm and the implementation work
        # *Stored in the main script in this version.
        # -------------------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------------------
        # Stem identification within the stripe
        # -------------------------------------------------------------------------------------------------
        params["expert"]["res_xy_stripe"] = float(
            self.res_xy_stripe.get()
        )  # (x, y)voxel resolution during stem identification
        params["expert"]["res_z_stripe"] = float(
            self.res_z_stripe.get()
        )  # (z) voxel resolution during stem identification

        params["expert"]["number_of_points"] = int(
            self.number_of_points.get()
        )  # minimum number of points per stem within the stripe (DBSCAN clustering).
        # Values, normally between 500 and 3000

        params["expert"]["verticality_scale_stripe"] = float(
            self.verticality_scale_stripe.get()
        )  # Vicinity radius for PCA during stem extraction
        params["expert"]["verticality_thresh_stripe"] = float(
            self.verticality_thresh_stripe.get()
        )  # Verticality threshold durig stem extraction

        # -------------------------------------------------------------------------------------------------
        # Tree individualization.
        # -------------------------------------------------------------------------------------------------
        params["expert"]["res_xy"] = float(
            self.res_xy.get()
        )  # (x, y) voxel resolution during tree individualization
        params["expert"]["res_z"] = float(
            self.res_z.get()
        )  # (z) voxel resolution during tree individualization

        params["expert"]["minimum_points"] = int(
            self.minimum_points.get()
        )  # Minimum number of points within a stripe to consider it as a potential tree during tree individualization

        params["expert"]["verticality_scale_stems"] = float(
            self.verticality_scale_stems.get()
        )   # DBSCAN minimum number of points during stem identification
        params["expert"]["verticality_thresh_stems"] = float(
            self.verticality_thresh_stems.get()
        )  # Verticality threshold durig stem identification

        params["expert"]["height_range"] = float(
            self.height_range.get()
        )  # only stems where points extend vertically throughout this range are considered.
        params["expert"]["maximum_d"] = float(
            self.maximum_d.get()
        )  # Points that are closer than d_max to an axis are assigned to that axis during individualize_trees process.

        params["expert"]["distance_to_axis"] = float(
            self.distance_to_axis.get()
        )  # Points within this distance from tree axes will be used to find tree height
        params["expert"]["res_heights"] = float(
            self.res_heights.get()
        )  # Resolution for the voxelization while computing tree heights
        params["expert"]["maximum_dev"] = float(
            self.maximum_dev.get()
        )  # Maximum degree of vertical deviation from the axis

        # -------------------------------------------------------------------------------------------------
        # Extracting sections.
        # -------------------------------------------------------------------------------------------------
        params["expert"]["number_points_section"] = int(
            self.number_points_section.get()
        )  # Minimum number of points in a section to be considered
        params["expert"]["diameter_proportion"] = float(
            self.diameter_proportion.get()
        )  # Proportion, regarding the circumference fit by fit_circle, that the inner circumference radius will have as length
        params["expert"]["minimum_diameter"] = (
            float(self.minimum_diameter.get()) / 2
        )  # Minimum radius expected for any section circle fitting.
        params["expert"]["point_threshold"] = int(
            self.point_threshold.get()
        )  # Number of points inside the inner circle
        params["expert"]["point_distance"] = float(
            self.point_distance.get()
        )  # Maximum distance among points to be considered within the same cluster.
        params["expert"]["number_sectors"] = int(
            self.number_sectors.get()
        )  # Number of sectors in which the circumference will be divided
        params["expert"]["m_number_sectors"] = int(
            self.m_number_sectors.get()
        )  # Minimum number of sectors that must be occupied.
        params["expert"]["circle_width"] = float(
            self.circle_width.get()
        )  # Width, in centimeters, around the circumference to look for points

        # -------------------------------------------------------------------------------------------------
        # Drawing circles.
        # -------------------------------------------------------------------------------------------------
        params["expert"]["circa_points"] = int(self.circa.get())

        # -------------------------------------------------------------------------------------------------
        # Drawing axes.
        # -------------------------------------------------------------------------------------------------
        params["expert"]["p_interval"] = float(self.p_interval.get())
        params["expert"]["axis_downstep"] = float(self.axis_downstep.get())
        params["expert"]["axis_upstep"] = float(
            self.axis_upstep.get()
        )  # From the stripe centroid, how much (upwards direction) will the drawn axes extend.

        # -------------------------------------------------------------------------------------------------
        # Height normalization
        # -------------------------------------------------------------------------------------------------
        params["expert"]["res_ground"] = float(self.res_ground.get())
        params["expert"]["min_points_ground"] = int(self.min_points_ground.get())
        params["expert"]["res_cloth"] = float(self.res_cloth.get())

        return params

    def _create_basic_tab(self):
        """Create the basic parameters tab (1)"""
        self.basic_tab = ttk.Frame(self.note)
        self.note.add(self.basic_tab, text="Basic")

        ttk.Label(self.basic_tab, text="Is the point cloud height-normalized?").grid(
            column=2, row=1, columnspan=3, sticky="EW"
        )

        ttk.Label(
            self.basic_tab, text="Do you expect noise points below ground-level?"
        ).grid(column=2, row=3, columnspan=3, sticky="W")

        ttk.Label(self.basic_tab, text="Format of output tabular data").grid(
            column=2, row=5, columnspan=3, sticky="W"
        )

        # Z0 field name entry
        z0_entry = ttk.Entry(self.basic_tab, width=7, textvariable=self.z0_name)
        z0_entry.grid(column=3, row=7, sticky="EW")
        z0_entry.configure(state="disabled")

        # Stripe upper limit entry
        upper_limit_entry = ttk.Entry(
            self.basic_tab, width=7, textvariable=self.upper_limit
        )
        upper_limit_entry.grid(column=3, row=8, sticky="EW")

        # Stripe lower limit entry
        lower_limit_entry = ttk.Entry(
            self.basic_tab, width=7, textvariable=self.lower_limit
        )
        lower_limit_entry.grid(column=3, row=9, sticky="EW")

        # Number of iterations entry
        number_of_iterations_entry = ttk.Entry(
            self.basic_tab, width=7, textvariable=self.number_of_iterations
        )
        number_of_iterations_entry.grid(column=3, row=10, sticky="EW")

        ttk.Label(self.basic_tab, text="Normalized height field name").grid(
            column=2, row=7, sticky="W"
        )
        ttk.Label(self.basic_tab, text="Stripe upper limit").grid(
            column=2, row=8, sticky="W"
        )
        ttk.Label(self.basic_tab, text="Stripe lower limit").grid(
            column=2, row=9, sticky="W"
        )
        ttk.Label(self.basic_tab, text="Pruning intensity").grid(
            column=2, row=10, sticky="W"
        )

        ttk.Label(self.basic_tab, text="meters").grid(column=4, row=8, sticky="W")
        ttk.Label(self.basic_tab, text="meters").grid(column=4, row=9, sticky="W")
        ttk.Label(self.basic_tab, text="0 - 5").grid(column=4, row=10, sticky="W")

        #### Adding logo
        logo_png = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("3dfin_logo.png"))
        )
        ttk.Label(self.basic_tab, image=logo_png).grid(
            column=6, row=1, rowspan=2, columnspan=2, sticky="NS"
        )

        #### Text displaying info
        insert_text1 = """This program implements an algorithm to detect the trees present in a ground-based 
        3D point cloud from a forest plot, and compute individual tree parameters: tree height,
        tree location, diameters along the stem (including DBH), and stem axis. 

        It takes a .LAS/.LAZ file as input, which may contain extra fields (.LAS standard
        or not). Also, the input point cloud can come from terrestrial photogrammetry, 
        TLS or mobile (e.g. hand-held) LS, a combination of those, and/or a combination 
        of those with UAV-(LS or SfM), or ALS. 

        After all computations are done, it outputs several .LAS files containing resulting
        point clouds and a XLSX file storing tabular data. Optionally, tabular data may be 
        output as text files instead of the Excel spreadsheet if preferred. 


        Further details may be found in next tabs and in the documentation.
        """

        ttk.Separator(self.basic_tab, orient="vertical").grid(
            column=5, row=1, rowspan=10, sticky="NS"
        )

        ttk.Label(self.basic_tab, text=insert_text1).grid(
            column=6, row=3, rowspan=8, columnspan=2, sticky="NW"
        )

        #### Adding images
        ttk.Label(self.basic_tab, text="Stripe", font=("Helvetica", 10, "bold")).grid(
            column=1, row=11, columnspan=4, sticky="N"
        )
        ttk.Label(self.basic_tab, image=self.img_stripe).grid(
            column=1, row=12, columnspan=4, sticky="N"
        )

        ttk.Label(
            self.basic_tab, text="Region where one should expect mostly stems."
        ).grid(column=1, row=13, columnspan=4, sticky="N")

        ttk.Label(
            self.basic_tab, text="Original cloud", font=("Helvetica", 10, "bold")
        ).grid(column=6, row=11, sticky="N")
        ttk.Label(self.basic_tab, image=self.img_cloud).grid(
            column=6, row=12, columnspan=1, sticky="N"
        )

        ttk.Label(
            self.basic_tab,
            text="Height-normalized cloud",
            font=("Helvetica", 10, "bold"),
        ).grid(column=7, row=11, sticky="N")
        ttk.Label(self.basic_tab, image=self.img_normalized_cloud).grid(
            column=7, row=12, columnspan=1, sticky="N"
        )

        ttk.Label(
            self.basic_tab,
            text="The algorithm requires a height-normalized point cloud, such as the one above.",
        ).grid(column=6, row=13, columnspan=2, sticky="N")

        for child in self.basic_tab.winfo_children():
            child.grid_configure(padx=5, pady=5)

        #### Adding radio buttons
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

        normalized_button_1 = ttk.Radiobutton(
            self.basic_tab,
            text="Yes",
            variable=self.is_normalized_var,
            value=True,
            command=enable_denoising,
        )
        normalized_button_1.grid(column=2, row=2, sticky="EW")
        normalized_button_2 = ttk.Radiobutton(
            self.basic_tab,
            text="No",
            variable=self.is_normalized_var,
            value=False,
            command=disable_denoising,
        )
        normalized_button_2.grid(column=3, row=2, sticky="EW")

        # Create the optionmenu widget and passing the options_list and value_inside to it.
        clean_button_1 = ttk.Radiobutton(
            self.basic_tab, text="Yes", variable=self.is_noisy_var, value=True
        )
        clean_button_1.grid(column=2, row=4, sticky="EW")
        clean_button_2 = ttk.Radiobutton(
            self.basic_tab, text="No", variable=self.is_noisy_var, value=False
        )
        clean_button_2.grid(column=3, row=4, sticky="EW")

        # Create the optionmenu widget and passing the options_list and value_inside to it.
        txt_button_1 = ttk.Radiobutton(
            self.basic_tab, text="TXT files", variable=self.txt_var, value=True
        )
        txt_button_1.grid(column=2, row=6, sticky="EW")
        txt_button_1 = ttk.Radiobutton(
            self.basic_tab, text="XLSX files", variable=self.txt_var, value=False
        )
        txt_button_1.grid(column=3, row=6, sticky="EW")

        #### Adding info buttons ####

        is_normalized_info = ttk.Label(self.basic_tab, image=self.info_icon)
        is_normalized_info.grid(column=1, row=1)
        ToolTip.create(
            is_normalized_info,
            text="If the point cloud is not height-normalized, a Digital Terrain\n"
            "Model will be generated to compute normalized heights for all points.",
        )

        is_noisy_info = ttk.Label(self.basic_tab, image=self.info_icon)
        is_noisy_info.grid(column=1, row=3)
        ToolTip.create(
            is_noisy_info,
            text="If it is expected to be noise below ground level (or if you know\n"
            "that there is noise), a denoising step will be added before\n"
            "generating the Digital Terrain Model.",
        )

        txt_info = ttk.Label(self.basic_tab, image=self.info_icon)
        txt_info.grid(column=1, row=5)
        ToolTip.create(
            txt_info,
            text="Outputs are gathered in a xlsx (Excel) file by default.\n"
            'Selecting "TXT files" will make the program output several txt files\n'
            "with the raw data, which may be more convenient for processing\n"
            "the data via scripting.",
        )

        z0_info = ttk.Label(self.basic_tab, image=self.info_icon)
        z0_info.grid(column=1, row=7)
        ToolTip.create(
            z0_info,
            text="Name of the Z0 field in the LAS file containing the cloud.\n"
            "If the normalized heights are stored in the Z coordinate\n"
            'of the .LAS file, then: Z0 field name = "z" (lowercase).\n'
            'Default is "Z0".',
        )

        upper_limit_info = ttk.Label(self.basic_tab, image=self.info_icon)
        upper_limit_info.grid(column=1, row=8)
        ToolTip.create(
            upper_limit_info,
            text="Upper (vertical) limit of the stripe where it should be reasonable\n"
            "to find stems with minimum presence of shrubs or branches.\n"
            "Reasonable values are 2-5 meters.\n"
            "Default value is 2.5 meters.",
        )

        lower_limit_info = ttk.Label(self.basic_tab, image=self.info_icon)
        lower_limit_info.grid(column=1, row=9)
        ToolTip.create(
            lower_limit_info,
            text="Lower (vertical) limit of the stripe where it should be reasonable\n"
            "to find stems with minimum presence of shrubs or branches.\n"
            "Reasonable values are 0.3-1.3 meters.\n"
            "Default value is 0.5 meters.",
        )

        number_of_iterations_info = ttk.Label(self.basic_tab, image=self.info_icon)
        number_of_iterations_info.grid(column=1, row=10)
        ToolTip.create(
            number_of_iterations_info,
            text='Number of iterations of "pruning" during stem identification.\n'
            "Values between 1 (slight stem peeling/cleaning)\n"
            "and 5 (extreme branch peeling/cleaning).\n"
            "Default value is 2.",
        )

    def _create_advanced_tab(self):
        """Create the advanced parameters tab (2)"""
        self.advanced_tab = ttk.Frame(self.note)
        self.note.add(self.advanced_tab, text="Advanced")

        # Maximum diameter entry #
        maximum_diameter_entry = ttk.Entry(
            self.advanced_tab, width=7, textvariable=self.maximum_diameter
        )
        maximum_diameter_entry.grid(column=3, row=1, sticky="EW")

        # Stem search radius entry #
        stem_search_diameter_entry = ttk.Entry(
            self.advanced_tab, width=7, textvariable=self.stem_search_diameter
        )
        stem_search_diameter_entry.grid(column=3, row=2, sticky="EW")

        # Lowest section #
        minimum_height_entry = ttk.Entry(
            self.advanced_tab, width=7, textvariable=self.minimum_height
        )
        minimum_height_entry.grid(column=3, row=3, sticky="EW")

        # Highest section #
        maximum_height_entry = ttk.Entry(
            self.advanced_tab, width=7, textvariable=self.maximum_height
        )
        maximum_height_entry.grid(column=3, row=4, sticky="EW")

        # Section height #
        section_len_entry = ttk.Entry(
            self.advanced_tab, width=7, textvariable=self.section_len
        )
        section_len_entry.grid(column=3, row=5, sticky="EW")

        # Section width #
        section_wid_entry = ttk.Entry(
            self.advanced_tab, width=7, textvariable=self.section_wid
        )
        section_wid_entry.grid(column=3, row=6, sticky="EW")

        ttk.Label(self.advanced_tab, text="Expected maximum diameter").grid(
            column=2, row=1, sticky="W"
        )
        ttk.Label(self.advanced_tab, text="Stem search diameter").grid(
            column=2, row=2, sticky="W"
        )
        ttk.Label(self.advanced_tab, text="Lowest section").grid(
            column=2, row=3, sticky="W"
        )
        ttk.Label(self.advanced_tab, text="Highest section").grid(
            column=2, row=4, sticky="W"
        )
        ttk.Label(self.advanced_tab, text="Distance between sections").grid(
            column=2, row=5, sticky="W"
        )
        ttk.Label(self.advanced_tab, text="Section width").grid(
            column=2, row=6, sticky="W"
        )

        ttk.Label(self.advanced_tab, text="meters").grid(column=4, row=1, sticky="W")
        ttk.Label(self.advanced_tab, text="meters").grid(column=4, row=2, sticky="W")
        ttk.Label(self.advanced_tab, text="meters").grid(column=4, row=3, sticky="W")
        ttk.Label(self.advanced_tab, text="meters").grid(column=4, row=4, sticky="W")
        ttk.Label(self.advanced_tab, text="meters").grid(column=4, row=5, sticky="W")
        ttk.Label(self.advanced_tab, text="meters").grid(column=4, row=6, sticky="W")

        #### Text displaying info ###
        insert_text2 = """If the results obtained by just tweaking basic parameters do not meet your expectations,
        you might want to modify these. 

        You can get a brief description of what they do by hovering the mouse over the info icon
        right before each parameter. However, keep in mind that a thorough understanding is
        advisable before changing these. For that, you can get a better grasp of what the algo-
        rithm does in the attached documentation. You can easily access it through the 
        Documentation button in the bottom-left corner.
        """

        ttk.Separator(self.advanced_tab, orient="vertical").grid(
            column=5,
            row=1,
            rowspan=6,
            sticky="NS",
        )

        ttk.Label(
            self.advanced_tab,
            text="Advanced parameters",
            font=("Helvetica", 10, "bold"),
        ).grid(column=6, row=1, rowspan=8, sticky="N")
        ttk.Label(self.advanced_tab, text=insert_text2).grid(
            column=6, row=2, rowspan=8, sticky="NW"
        )

        for child in self.advanced_tab.winfo_children():
            child.grid_configure(padx=5, pady=5)

        #### Adding images
        sections_img = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("section_details.png"))
        )
        ttk.Label(self.advanced_tab, image=sections_img).grid(
            column=1, row=9, columnspan=15, sticky="W", padx=20, pady=5
        )

        sections_text = """A) Sections along the stem B) Detail of computed sections showing the distance 
        between them and their width C) Circle fitting to the points of a section.
        """
        ttk.Label(self.advanced_tab, text=sections_text).grid(
            column=1, row=10, columnspan=15, sticky="NW", padx=20, pady=5
        )

        sectors_img = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("sectors.png"))
        )
        ttk.Label(self.advanced_tab, image=sectors_img).grid(
            column=1, row=9, columnspan=15, sticky="E", padx=20, pady=5
        )

        sectors_text = """Several quality controls are implemented to
        validate the fitted circles, such as measuring
        the point distribution along the sections."""

        ttk.Label(self.advanced_tab, text=sectors_text).grid(
            column=1, row=10, columnspan=15, sticky="NE", padx=20, pady=5
        )

        #### Adding info buttons
        maximum_diameter_info = ttk.Label(self.advanced_tab, image=self.info_icon)
        maximum_diameter_info.grid(column=1, row=1)
        ToolTip.create(
            maximum_diameter_info,
            text="Maximum diameter expected for any stem.\n"
            "Default value: 0.5 meters.",
        )

        stem_search_diameter_info = ttk.Label(self.advanced_tab, image=self.info_icon)
        stem_search_diameter_info.grid(column=1, row=2)
        ToolTip.create(
            stem_search_diameter_info,
            text="Points within this distance from tree axes will be considered\n"
            'as potential stem points. Reasonable values are "Maximum diameter"-2 meters \n'
            "(exceptionally greater than 2: very large diameters and/or intricate stems).",
        )

        minimum_height_info = ttk.Label(self.advanced_tab, image=self.info_icon)
        minimum_height_info.grid(column=1, row=3)
        ToolTip.create(
            minimum_height_info,
            text="Lowest height at which stem diameter will be computed.\n"
            "Default value: 0.2 meters.",
        )

        maximum_height_info = ttk.Label(self.advanced_tab, image=self.info_icon)
        maximum_height_info.grid(column=1, row=4)
        ToolTip.create(
            maximum_height_info,
            text="Highest height at which stem diameter will be computed.\n"
            "Default value: 25 meters.",
        )

        section_len_info = ttk.Label(self.advanced_tab, image=self.info_icon)
        section_len_info.grid(column=1, row=5)
        ToolTip.create(
            section_len_info,
            text="Height of the sections (z length). Diameters will then be\n"
            "computed for every section.\n"
            "Default value: 0.2 meters.",
        )

        section_wid_info = ttk.Label(self.advanced_tab, image=self.info_icon)
        section_wid_info.grid(column=1, row=6)
        ToolTip.create(
            section_wid_info,
            text="Sections are this wide. This means that points within this distance\n"
            "(vertical) are considered during circle fitting and diameter computation.\n"
            "Default value: 0.05 meters.",
        )

    def _create_expert_tab(self):
        """Create the expert parameters tab (3)"""
        self.expert_tab = ttk.Frame(self.note)

        self.note.add(self.expert_tab, text="Expert")

        ### Stem identification from stripe ###
        ttk.Label(
            self.expert_tab,
            text="Stem identification whithin the stripe",
            font=("Helvetica", 10, "bold"),
        ).grid(column=1, row=1, columnspan=4, sticky="N")

        # (x, y) voxel resolution
        res_xy_stripe_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.res_xy_stripe
        )
        res_xy_stripe_entry.grid(column=3, row=2, sticky="EW")

        # (z) voxel resolution during stem identification entry #
        res_z_stripe_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.res_z_stripe
        )
        res_z_stripe_entry.grid(column=3, row=3, sticky="EW")

        # Number of points entry #
        number_of_points_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.number_of_points
        )
        number_of_points_entry.grid(column=3, row=4, sticky="EW")

        # Vicinity radius for PCA during stem identification entry #
        verticality_scale_stripe_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.verticality_scale_stripe
        )
        verticality_scale_stripe_entry.grid(column=3, row=5, sticky="EW")

        # Verticality threshold durig stem identification entry #
        verticality_thresh_stripe_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.verticality_thresh_stripe
        )
        verticality_thresh_stripe_entry.grid(column=3, row=6, sticky="EW")

        # Vertical range #
        height_range_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.height_range
        )
        height_range_entry.grid(column=3, row=7, sticky="EW")

        ttk.Label(self.expert_tab, text="(x, y) voxel resolution").grid(
            column=2, row=2, sticky="w"
        )
        ttk.Label(self.expert_tab, text="(z) voxel resolution").grid(
            column=2, row=3, sticky="W"
        )
        ttk.Label(self.expert_tab, text="Number of points").grid(
            column=2, row=4, sticky="W"
        )
        ttk.Label(
            self.expert_tab, text="Vicinity radius (verticality computation)"
        ).grid(column=2, row=5, sticky="W")
        ttk.Label(self.expert_tab, text="Verticality threshold").grid(
            column=2, row=6, sticky="W"
        )
        ttk.Label(self.expert_tab, text="Vertical range").grid(
            column=2, row=7, sticky="W"
        )

        ttk.Label(self.expert_tab, text="meters").grid(column=4, row=2, sticky="W")
        ttk.Label(self.expert_tab, text="meters").grid(column=4, row=3, sticky="W")
        ttk.Label(self.expert_tab, text="meters").grid(column=4, row=5, sticky="W")
        ttk.Label(self.expert_tab, text="(0, 1)").grid(column=4, row=6, sticky="W")

        ### Stem extraction and tree individualization ###
        ttk.Label(
            self.expert_tab,
            text="Stem extraction and tree individualization",
            font=("Helvetica", 10, "bold"),
        ).grid(column=1, row=9, columnspan=4, sticky="N")

        # (x, y) voxel resolution
        res_xy_entry = ttk.Entry(self.expert_tab, width=7, textvariable=self.res_xy)
        res_xy_entry.grid(column=3, row=10, sticky="EW")

        # (z) voxel resolution #
        res_z_entry = ttk.Entry(self.expert_tab, width=7, textvariable=self.res_z)
        res_z_entry.grid(column=3, row=11, sticky="EW")

        # Minimum points #
        minimum_points_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.minimum_points
        )
        minimum_points_entry.grid(column=3, row=12, sticky="EW")

        # Vicinity radius for PCA #
        verticality_scale_stems_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.verticality_scale_stems
        )
        verticality_scale_stems_entry.grid(column=3, row=13, sticky="EW")

        # Verticality threshold durig tree individualization entry #
        verticality_thresh_stems_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.verticality_thresh_stems
        )
        verticality_thresh_stems_entry.grid(column=3, row=14, sticky="EW")

        # Maximum distance to axis #
        maximum_d_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.maximum_d
        )
        maximum_d_entry.grid(column=3, row=15, sticky="EW")

        # Distance to axis during height computation #
        distance_to_axis_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.distance_to_axis
        )
        distance_to_axis_entry.grid(column=3, row=16, sticky="EW")

        # Voxel resolution during height computation #
        res_heights_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.res_heights
        )
        res_heights_entry.grid(column=3, row=17, sticky="EW")

        # Maximum degree of vertical deviation from the axis #
        maximum_dev_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.maximum_dev
        )
        maximum_dev_entry.grid(column=3, row=18, sticky="EW")

        ttk.Label(self.expert_tab, text="(x, y) voxel resolution").grid(
            column=2, row=10, sticky="W"
        )
        ttk.Label(self.expert_tab, text="(z) voxel resolution").grid(
            column=2, row=11, sticky="W"
        )
        ttk.Label(self.expert_tab, text="Minimum points").grid(
            column=2, row=12, sticky="W"
        )
        ttk.Label(
            self.expert_tab, text="Vicinity radius (verticality computation)"
        ).grid(column=2, row=13, sticky="W")
        ttk.Label(self.expert_tab, text="Verticality threshold").grid(
            column=2, row=14, sticky="W"
        )
        ttk.Label(self.expert_tab, text="Maximum distance to tree axis").grid(
            column=2, row=15, sticky="W"
        )
        ttk.Label(self.expert_tab, text="Distance from axis").grid(
            column=2, row=16, sticky="W"
        )
        ttk.Label(self.expert_tab, text="Voxel resolution for height computation").grid(
            column=2, row=17, sticky="W"
        )
        ttk.Label(self.expert_tab, text="Maximum vertical deviation from axis").grid(
            column=2, row=18, sticky="W"
        )

        ttk.Label(self.expert_tab, text="meters").grid(column=4, row=10, sticky="W")
        ttk.Label(self.expert_tab, text="meters").grid(column=4, row=11, sticky="W")
        ttk.Label(self.expert_tab, text="meters").grid(column=4, row=12, sticky="W")
        ttk.Label(self.expert_tab, text="(0, 1)").grid(column=4, row=13, sticky="W")
        ttk.Label(self.expert_tab, text="meters").grid(column=4, row=14, sticky="W")
        ttk.Label(self.expert_tab, text="meters").grid(column=4, row=15, sticky="W")
        ttk.Label(self.expert_tab, text="meters").grid(column=4, row=16, sticky="W")
        ttk.Label(self.expert_tab, text="meters").grid(column=4, row=17, sticky="W")
        ttk.Label(self.expert_tab, text="degrees").grid(column=4, row=18, sticky="W")

        ### Computing sections ###
        ttk.Label(
            self.expert_tab, text="Computing sections", font=("Helvetica", 10, "bold")
        ).grid(column=7, row=1, sticky="E")

        ### Vertical separator

        ttk.Separator(self.expert_tab, orient="vertical").grid(
            column=5, row=1, rowspan=18, sticky="NS"
        )

        # Minimum number of points in a section #
        number_points_section_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.number_points_section
        )
        number_points_section_entry.grid(column=8, row=2, sticky="EW")

        # Inner/outer circle proportion #
        diameter_proportion_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.diameter_proportion
        )
        diameter_proportion_entry.grid(column=8, row=3, sticky="EW")

        # Minimum radius expected #
        minimum_diameter_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.minimum_diameter
        )
        minimum_diameter_entry.grid(column=8, row=4, sticky="EW")

        # Number of points inside the inner circle used as threshold #
        point_threshold_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.point_threshold
        )
        point_threshold_entry.grid(column=8, row=5, sticky="EW")

        # Maximum point distance #
        point_distance_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.point_distance
        )
        point_distance_entry.grid(column=8, row=6, sticky="EW")

        # Number of sectors #
        number_sectors_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.number_sectors
        )
        number_sectors_entry.grid(column=8, row=7, sticky="EW")

        # Mnimum number of occupied sectors #
        m_number_sectors_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.m_number_sectors
        )
        m_number_sectors_entry.grid(column=8, row=8, sticky="EW")

        # Width #
        circle_width_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.circle_width
        )
        circle_width_entry.grid(column=8, row=9, sticky="EW")

        ttk.Label(self.expert_tab, text="Points within section").grid(
            column=7, row=2, sticky="W"
        )
        ttk.Label(self.expert_tab, text="Inner/outer circle proportion").grid(
            column=7, row=3, sticky="W"
        )
        ttk.Label(self.expert_tab, text="Minimum expected diameter").grid(
            column=7, row=4, sticky="W"
        )
        ttk.Label(self.expert_tab, text="Points within inner circle").grid(
            column=7, row=5, sticky="W"
        )
        ttk.Label(self.expert_tab, text="Maximum point distance").grid(
            column=7, row=6, sticky="W"
        )
        ttk.Label(self.expert_tab, text="Number of sectors").grid(
            column=7, row=7, sticky="W"
        )
        ttk.Label(self.expert_tab, text="Number of occupied sectors").grid(
            column=7, row=8, sticky="W"
        )
        ttk.Label(self.expert_tab, text="Circle width").grid(
            column=7, row=9, sticky="W"
        )

        ttk.Label(self.expert_tab, text="[0, 1]").grid(column=9, row=3, sticky="W")
        ttk.Label(self.expert_tab, text="meters").grid(column=9, row=4, sticky="W")
        ttk.Label(self.expert_tab, text="meters").grid(column=9, row=6, sticky="W")
        ttk.Label(self.expert_tab, text="centimeters").grid(column=9, row=9, sticky="W")

        ### Drawing circles and axes ###
        ttk.Label(
            self.expert_tab,
            text="Drawing circles and axes",
            font=("Helvetica", 10, "bold"),
        ).grid(column=7, row=10, sticky="E")

        # Circa points #
        circa_entry = ttk.Entry(self.expert_tab, width=7, textvariable=self.circa)
        circa_entry.grid(column=8, row=11, sticky="EW")

        # Point interval #
        p_interval_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.p_interval
        )
        p_interval_entry.grid(column=8, row=12, sticky="EW")

        # Axis lowest point #
        axis_downstep_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.axis_downstep
        )
        axis_downstep_entry.grid(column=8, row=13, sticky="EW")

        # Axis highest point #
        axis_upstep_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.axis_upstep
        )
        axis_upstep_entry.grid(column=8, row=14, sticky="EW")

        ttk.Label(self.expert_tab, text="N of points to draw each circle").grid(
            column=7, row=11, sticky="W"
        )
        ttk.Label(self.expert_tab, text="Interval at which points are drawn").grid(
            column=7, row=12, sticky="W"
        )
        ttk.Label(self.expert_tab, text="Axis downstep from stripe center").grid(
            column=7, row=13, sticky="W"
        )
        ttk.Label(self.expert_tab, text="Axis upstep from stripe center").grid(
            column=7, row=14, sticky="W"
        )

        ttk.Label(self.expert_tab, text="meters").grid(column=9, row=12, sticky="W")
        ttk.Label(self.expert_tab, text="meters").grid(column=9, row=13, sticky="W")
        ttk.Label(self.expert_tab, text="meters").grid(column=9, row=14, sticky="W")

        ### Height normalization ###
        ttk.Label(
            self.expert_tab, text="Height normalization", font=("Helvetica", 10, "bold")
        ).grid(column=7, row=15, sticky="E")

        # (x, y) voxel resolution during denoising
        res_ground_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.res_ground
        )
        res_ground_entry.grid(column=8, row=16, sticky="EW")

        min_points_ground_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.min_points_ground
        )
        min_points_ground_entry.grid(column=8, row=17, sticky="EW")

        res_cloth_entry = ttk.Entry(
            self.expert_tab, width=7, textvariable=self.res_cloth
        )
        res_cloth_entry.grid(column=8, row=18, sticky="EW")

        ttk.Label(self.expert_tab, text="(x, y) voxel resolution").grid(
            column=7, row=16, sticky="W"
        )
        ttk.Label(self.expert_tab, text="Minimum number of points").grid(
            column=7, row=17, sticky="W"
        )
        ttk.Label(self.expert_tab, text="Cloth resolution").grid(
            column=7, row=18, sticky="W"
        )

        ttk.Label(self.expert_tab, text="meters").grid(column=9, row=16, sticky="W")
        ttk.Label(self.expert_tab, text="meters").grid(column=9, row=18, sticky="W")

        for child in self.expert_tab.winfo_children():
            child.grid_configure(padx=5, pady=5)

        #### Adding info buttons ####

        res_xy_stripe_info = ttk.Label(self.expert_tab, image=self.info_icon)
        res_xy_stripe_info.grid(column=1, row=2)
        ToolTip.create(
            res_xy_stripe_info,
            text="(x, y) voxel resolution during stem extraction.\n"
            "Default value: 0.035 meters.",
        )

        res_z_stripe_info = ttk.Label(self.expert_tab, image=self.info_icon)
        res_z_stripe_info.grid(column=1, row=3)
        ToolTip.create(
            res_z_stripe_info,
            text="(z) voxel resolution during stem extraction.\n"
            "Default value: 0.035 meters.",
        )

        number_of_points_info = ttk.Label(self.expert_tab, image=self.info_icon)
        number_of_points_info.grid(column=1, row=4)
        ToolTip.create(
            number_of_points_info,
            text="minimum number of points (voxels) per stem within the stripe\n"
            "(DBSCAN clustering). Reasonable values are between 500 and 3000.\n"
            "Default value: 1000.",
        )

        verticality_scale_stripe_info = ttk.Label(self.expert_tab, image=self.info_icon)
        verticality_scale_stripe_info.grid(column=1, row=5)
        ToolTip.create(
            verticality_scale_stripe_info,
            text="Vicinity radius for PCA during stem identification.\n"
            "Default value: 0.1 meters.",
        )

        verticality_thresh_stripe_info = ttk.Label(
            self.expert_tab, image=self.info_icon
        )
        verticality_thresh_stripe_info.grid(column=1, row=6)
        ToolTip.create(
            verticality_thresh_stripe_info,
            text="Verticality threshold durig stem identification\n"
            "Verticality is defined as (1 - sin(V)), being V the vertical angle of the normal\n"
            "vector, measured from the horizontal. Note that it does not grow linearly.\n"
            "Default value: 0.7.",
        )

        height_range_info = ttk.Label(self.expert_tab, image=self.info_icon)
        height_range_info.grid(column=1, row=7)
        ToolTip.create(
            height_range_info,
            text="Proportion (0: none - 1: all) of the vertical range of the stripe\n"
            "that points need to extend through to be valid stems.\n"
            "Default value: 0.7.",
        )

        res_xy_info = ttk.Label(self.expert_tab, image=self.info_icon)
        res_xy_info.grid(column=1, row=10)
        ToolTip.create(
            res_xy_info,
            text="(x, y) voxel resolution during tree individualization.\n"
            "Default value: 0.035 meters.",
        )

        res_z_info = ttk.Label(self.expert_tab, image=self.info_icon)
        res_z_info.grid(column=1, row=11)
        ToolTip.create(
            res_z_info,
            text="(z) voxel resolution during tree individualization.\n"
            "Default value: 0.035 meters.",
        )

        minimum_points_info = ttk.Label(self.expert_tab, image=self.info_icon)
        minimum_points_info.grid(column=1, row=12)
        ToolTip.create(
            minimum_points_info,
            text="Minimum number of points (voxels) within a stripe to consider it\n"
            "as a potential tree during tree individualization.\n"
            "Default value: 20.",
        )

        verticality_scale_stems_info = ttk.Label(self.expert_tab, image=self.info_icon)
        verticality_scale_stems_info.grid(column=1, row=13)
        ToolTip.create(
            verticality_scale_stems_info,
            text="Vicinity radius for PCA during tree individualization.\n"
            "Default value: 0.1 meters.",
        )

        verticality_thresh_stems_info = ttk.Label(self.expert_tab, image=self.info_icon)
        verticality_thresh_stems_info.grid(column=1, row=14)
        ToolTip.create(
            verticality_thresh_stems_info,
            text="Verticality threshold durig stem extraction.\n"
            "Verticality is defined as (1 - sin(V)), being V the vertical angle of the normal\n"
            "vector, measured from the horizontal. Note that it does not grow linearly.\n"
            "Default value: 0.7.",
        )

        maximum_d_info = ttk.Label(self.expert_tab, image=self.info_icon)
        maximum_d_info.grid(column=1, row=15)
        ToolTip.create(
            maximum_d_info,
            text="Points that are closer than this distance to an axis "
            "are assigned to that axis during tree individualization process.\n"
            "Default value: 15 meters.",
        )

        distance_to_axis_info = ttk.Label(self.expert_tab, image=self.info_icon)
        distance_to_axis_info.grid(column=1, row=16)
        ToolTip.create(
            distance_to_axis_info,
            text="Maximum distance from tree axis at which points will\n"
            "be considered while computing tree height. Points too far away\n"
            "from the tree axis might not be representative of actual tree height.\n"
            "Default value: 1.5 meters.",
        )

        res_heights_info = ttk.Label(self.expert_tab, image=self.info_icon)
        res_heights_info.grid(column=1, row=17)
        ToolTip.create(
            res_heights_info,
            text="(x, y, z) voxel resolution during tree height computation.\n"
            "Default value: 0.3 meters.",
        )

        maximum_dev_info = ttk.Label(self.expert_tab, image=self.info_icon)
        maximum_dev_info.grid(column=1, row=18)
        ToolTip.create(
            maximum_dev_info,
            text="Maximum degree of vertical deviation from the axis for\n"
            "a tree height to be considered as valid.\n"
            "Default value: 25 degrees.",
        )

        number_points_section_info = ttk.Label(self.expert_tab, image=self.info_icon)
        number_points_section_info.grid(column=6, row=2)
        ToolTip.create(
            number_points_section_info,
            text="Minimum number of points in a section to be considered\n"
            "as valid.\n"
            "Default value: 80.",
        )

        diameter_proportion_info = ttk.Label(self.expert_tab, image=self.info_icon)
        diameter_proportion_info.grid(column=6, row=3)
        ToolTip.create(
            diameter_proportion_info,
            text="Proportion, regarding the circumference fit by fit_circle,\n"
            "that the inner circumference diameter will have as length.\n"
            "Default value: 0.5 times.",
        )

        minimum_diameter_info = ttk.Label(self.expert_tab, image=self.info_icon)
        minimum_diameter_info.grid(column=6, row=4)
        ToolTip.create(
            minimum_diameter_info,
            text="Minimum diameter expected for any section during circle fitting.\n"
            "Default value: 0.03 meters.",
        )

        point_threshold_info = ttk.Label(self.expert_tab, image=self.info_icon)
        point_threshold_info.grid(column=6, row=5)
        ToolTip.create(
            point_threshold_info,
            text="Maximum number of points inside the inner circle\n"
            "to consider the fitting as OK.\n"
            "Default value: 5.",
        )

        point_distance_info = ttk.Label(self.expert_tab, image=self.info_icon)
        point_distance_info.grid(column=6, row=6)
        ToolTip.create(
            point_distance_info,
            text="Maximum distance among points to be considered within the\n"
            "same cluster during circle fitting.\n"
            "Default value: 0.02 meters.",
        )

        number_sectors_info = ttk.Label(self.expert_tab, image=self.info_icon)
        number_sectors_info.grid(column=6, row=7)
        ToolTip.create(
            number_sectors_info,
            text="Number of sectors in which the circumference will be divided\n"
            "Default value: 16.",
        )

        m_number_sectors_info = ttk.Label(self.expert_tab, image=self.info_icon)
        m_number_sectors_info.grid(column=6, row=8)
        ToolTip.create(
            m_number_sectors_info,
            text="Minimum number of sectors that must be occupied.\n"
            "Default value: 9.",
        )

        circle_width_info = ttk.Label(self.expert_tab, image=self.info_icon)
        circle_width_info.grid(column=6, row=9)
        ToolTip.create(
            circle_width_info,
            text="Width, in meters, around the circumference to look\n"
            "for points.\n"
            "Defaul value: 0.02 meters.",
        )

        circa_info = ttk.Label(self.expert_tab, image=self.info_icon)
        circa_info.grid(column=6, row=11)
        ToolTip.create(
            circa_info,
            text="Number of points that will be used to draw the circles\n "
            "in the LAS files.\n"
            "Default value: 200.",
        )

        p_interval_info = ttk.Label(self.expert_tab, image=self.info_icon)
        p_interval_info.grid(column=6, row=12)
        ToolTip.create(
            p_interval_info,
            text="Distance at which points will be placed from one to another\n"
            "while drawing the axes in the LAS files.\n"
            "Default value: 0.01 meters.",
        )

        axis_downstep_info = ttk.Label(self.expert_tab, image=self.info_icon)
        axis_downstep_info.grid(column=6, row=13)
        ToolTip.create(
            axis_downstep_info,
            text="From the stripe centroid, how much (downwards direction)\n"
            "will the drawn axes extend. Basically, this parameter controls\n"
            "from where will the axes be drawn.\n"
            "Default value: 0.5 meters.",
        )

        axis_upstep_info = ttk.Label(self.expert_tab, image=self.info_icon)
        axis_upstep_info.grid(column=6, row=14)
        ToolTip.create(
            axis_upstep_info,
            text="From the stripe centroid, how much (upwards direction)\n"
            "will the drawn axes extend. Basically, this parameter controls\n"
            "how long will the drawn axes be.\n"
            "Default value: 10 meters.",
        )

        res_ground_info = ttk.Label(self.expert_tab, image=self.info_icon)
        res_ground_info.grid(column=6, row=16)
        ToolTip.create(
            res_ground_info,
            text="(x, y, z) voxel resolution during denoising.|n"
            " Note that the whole point cloud is voxelated.\n"
            "Default value: 0.15.",
        )

        min_points_ground_info = ttk.Label(self.expert_tab, image=self.info_icon)
        min_points_ground_info.grid(column=6, row=17)
        ToolTip.create(
            min_points_ground_info,
            text="Clusters with size smaller than this value will be\n"
            "regarded as noise and thus eliminated.\n"
            "Default value: 2.",
        )

        res_cloth_info = ttk.Label(self.expert_tab, image=self.info_icon)
        res_cloth_info.grid(column=6, row=18)
        ToolTip.create(
            res_cloth_info,
            text="Initial cloth grid resolution to generate the DTM that\n"
            "be used to compute normalized heights.\n"
            "Default value: 0.5.",
        )

        def open_warning():
            """
            logic triggered by the warning button
            """
            new = tk.Toplevel(self)
            new.geometry("700x380")
            new.title("WARNING")
            ttk.Label(new, image=self.warning_img).grid(
                column=2, row=1, rowspan=3, sticky="E"
            )
            ttk.Label(
                new, text="This is the expert parameters tab.", font=("Helvetica", 10)
            ).grid(column=1, row=1, sticky="W")
            ttk.Label(
                new,
                text="Are you sure you know what these do?",
                font=("Helvetica", 10, "bold"),
            ).grid(column=1, row=2, sticky="W")
            ttk.Label(
                new,
                text="Before modifying these, you should read the documentation and the\n"
                "references listed below for a deep understading of what the algorithm does.",
                font=("Helvetica", 10),
            ).grid(column=1, row=3, sticky="W")

            ttk.Label(new, text="References:", font=("Helvetica", 11)).grid(
                column=1, row=4, sticky="W"
            )
            ttk.Label(
                new,
                text="Cabo, C., Ordonez, C., Lopez-Sanchez, C. A., & Armesto, J. (2018). Automatic dendrometry:\n"
                "Tree detection, tree height and diameter estimation using terrestrial laser scanning.\n"
                "International Journal of Applied Earth Observation and Geoinformation, 69, 164–174.\n"
                "https://doi.org/10.1016/j.jag.2018.01.011",
                font=("Helvetica", 10),
            ).grid(column=1, row=5, sticky="W")

            ttk.Label(
                new,
                text="Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996). A Density-Based Algorithm for\n"
                "Discovering Clusters in Large Spatial Databases with Noise. www.aaai.org",
                font=("Helvetica", 10),
            ).grid(column=1, row=6, sticky="W")

            ttk.Label(
                new,
                text="Prendes, C., Cabo, C., Ordoñez, C., Majada, J., & Canga, E. (2021). An algorithm for\n"
                "the automatic parametrization of wood volume equations from Terrestrial Laser Scanning\n"
                "point clouds: application in Pinus pinaster. GIScience and Remote Sensing, 58(7), 1130–1150.\n"
                "https://doi.org/10.1080/15481603.2021.1972712 ",
                font=("Helvetica", 10),
            ).grid(column=1, row=7, sticky="W")

            ttk.Label(
                new,
                text="Zhang, W., Qi, J., Wan, P., Wang, H., Xie, D., Wang, X., & Yan, G. (2016). An\n"
                "easy-to-use airborne LiDAR data filtering method based on cloth simulation. Remote Sensing, 8(6).\n"
                "https://doi.org/10.3390/rs8060501",
                font=("Helvetica", 10),
            ).grid(column=1, row=8, sticky="W")

            for child in new.winfo_children():
                child.grid_configure(padx=3, pady=3)

        tk.Button(
            self.expert_tab,
            text="What is this?",
            bg="IndianRed1",
            width=12,
            font=("Helvetica", 10, "bold"),
            cursor="hand2",
            command=open_warning,
        ).grid(column=9, row=1, columnspan=2, sticky="E")

    def _create_about_tab(self):
        """Create the about tab (4)"""
        self.about_tab = ttk.Frame(self.note)
        self.note.add(self.about_tab, text="About")

        nerc_project = """'Advancing 3D Fuel Mapping for Wildfire Behaviour and Risk Mitigation Modelling' """

        csic_project = """‘Advancing carbon emission estimations from wildfires applying artificial intelligence to 3D terrestrial point clouds’"""

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

        ### SCROLLBAR ###

        # Create a frame for the canvas with non-zero row&column weights
        frame_canvas = ttk.Frame(self.about_tab)
        frame_canvas.grid(row=0, column=0, pady=(5, 0), sticky="nw")
        frame_canvas.grid_rowconfigure(0, weight=1)
        frame_canvas.grid_columnconfigure(0, weight=1)
        # Set grid_propagate to False to allow 5-by-5 buttons resizing later
        frame_canvas.grid_propagate(False)

        # Add a canvas in that frame
        canvas = tk.Canvas(frame_canvas)
        canvas.grid(row=0, column=0, sticky="news")

        # Link a scrollbar to the canvas
        vsb = ttk.Scrollbar(frame_canvas, orient="vertical", command=canvas.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=vsb.set)

        # Create a frame to contain the info
        self.scrollable_info = ttk.Frame(canvas)

        # Copyright notice #
        copyright_1_lab = ttk.Label(
            self.scrollable_info, text=self.copyright_info_1, font=("Helvetica", 10, "bold")
        )
        copyright_1_lab.grid(row=1, column=1, columnspan=3)

        copyright_2_lab = ttk.Label(self.scrollable_info, text=self.copyright_info_2)
        copyright_2_lab.grid(row=2, column=1, columnspan=3)

        copyright_3_lab = ttk.Label(self.scrollable_info, text=self.copyright_info_3)
        copyright_3_lab.grid(row=3, column=1, columnspan=3)

        # About the project #
        about_1_lab = ttk.Label(self.scrollable_info, text=self.about_1)
        about_1_lab.grid(row=4, column=1, columnspan=3, sticky="W")

        nerc_project_lab = ttk.Label(
            self.scrollable_info, text=nerc_project, font=("Helvetica", 10, "italic")
        )
        nerc_project_lab.grid(row=5, column=1, columnspan=3)

        about_2_lab = ttk.Label(self.scrollable_info, text=self.about_2)
        about_2_lab.grid(row=6, column=1, columnspan=3, sticky="W")

        csic_project_lab = ttk.Label(
            self.scrollable_info, text=csic_project, font=("Helvetica", 10, "italic")
        )
        csic_project_lab.grid(row=7, column=1, columnspan=3)

        ttk.Label(self.scrollable_info, image=self.nerc_logo_img).grid(
            row=8, column=1, columnspan=3, sticky="W"
        )

        ttk.Label(self.scrollable_info, image=self.swansea_logo_img).grid(
            row=8, column=1, columnspan=3, sticky="E"
        )

        ttk.Label(self.scrollable_info, image=self.spain_logo_img).grid(
            row=9, column=1, columnspan=3, sticky="W"
        )

        ttk.Label(self.scrollable_info, image=self.csic_logo_img).grid(
            row=9, column=1, columnspan=3
        )

        ttk.Label(self.scrollable_info, image=self.uniovi_logo_img).grid(
            row=9, column=1, columnspan=3, sticky="E"
        )

        ttk.Separator(self.scrollable_info, orient="horizontal").grid(
            row=10, column=1, columnspan=3, sticky="EW"
        )

        team_lab = ttk.Label(
            self.scrollable_info, text="Team", font=("Helvetica", 12, "bold")
        )
        team_lab.grid(row=11, column=1, columnspan=3)

        carloscabo_lab = ttk.Label(self.scrollable_info, text=carloscabo)
        carloscabo_lab.grid(row=11, column=2, columnspan=2, sticky="W")

        diegolaino_lab = ttk.Label(self.scrollable_info, text=diegolaino)
        diegolaino_lab.grid(row=12, column=2, columnspan=2, sticky="W")

        crissantin_lab = ttk.Label(self.scrollable_info, text=crissantin)
        crissantin_lab.grid(row=13, column=2, columnspan=2, sticky="W")

        stefandoerr_lab = ttk.Label(self.scrollable_info, text=stefandoerr)
        stefandoerr_lab.grid(row=14, column=2, columnspan=2, sticky="W")

        celestinoordonez_lab = ttk.Label(self.scrollable_info, text=celestinoordonez)
        celestinoordonez_lab.grid(row=15, column=2, columnspan=2, sticky="W")

        tadasnikonovas_lab = ttk.Label(self.scrollable_info, text=tadasnikonovas)
        tadasnikonovas_lab.grid(row=16, column=2, columnspan=2, sticky="W")

        covadongaprendes_lab = ttk.Label(self.scrollable_info, text=covadongaprendes)
        covadongaprendes_lab.grid(row=17, column=2, columnspan=2, sticky="W")

        ttk.Label(self.scrollable_info, image=self.carlos_img).grid(row=11, column=1)

        ttk.Label(self.scrollable_info, image=self.diego_img).grid(row=12, column=1)

        ttk.Label(self.scrollable_info, image=self.cris_img).grid(row=13, column=1)

        ttk.Label(self.scrollable_info, image=self.stefan_img).grid(row=14, column=1)

        ttk.Label(self.scrollable_info, image=self.celestino_img).grid(row=15, column=1)

        ttk.Label(self.scrollable_info, image=self.tadas_img).grid(row=16, column=1)

        ttk.Label(self.scrollable_info, image=self.covadonga_img).grid(row=17, column=1)

        f = open(self._get_resource_path("License.txt"), "r")
        gnu_license = f.read()

        #### license button ####
        def open_license():
            new = tk.Toplevel(self.scrollable_info)

            # Create a frame for the canvas with non-zero row&column weights
            license_frame_canvas = ttk.Frame(new)
            license_frame_canvas.grid(row=0, column=0, pady=(0, 0), sticky="nw")
            license_frame_canvas.grid_rowconfigure(0, weight=1)
            license_frame_canvas.grid_columnconfigure(0, weight=1)

            # Set grid_propagate to False to allow 5-by-5 buttons resizing later
            license_frame_canvas.grid_propagate(False)

            # Add a canvas in that frame
            license_canvas = tk.Canvas(license_frame_canvas)
            license_canvas.grid(row=0, column=0, sticky="news")

            # Link a scrollbar to the canvas
            license_vsb = ttk.Scrollbar(
                license_frame_canvas, orient="vertical", command=license_canvas.yview
            )
            license_vsb.grid(row=0, column=1, sticky="ns")
            license_canvas.configure(yscrollcommand=license_vsb.set)

            # Create a frame to contain the info
            license_scrollable = ttk.Frame(license_canvas)

            new.geometry("620x400")
            new.title("LICENSE")
            ttk.Label(
                license_scrollable.scrollable_info,
                text="GNU GENERAL PUBLIC LICENSE",
                font=("Helvetica", 10, "bold"),
            ).grid(row=1, column=1)

            ttk.Label(
                license_scrollable.scrollable_info,
                text=gnu_license,
                font=("Helvetica", 10),
            ).grid(row=2, column=1, sticky="W")

            # Create canvas window to hold the buttons_frame.
            license_canvas.create_window(
                (0, 0), window=license_scrollable.scrollable_info, anchor="nw"
            )

            # Update buttons frames idle tasks to let tkinter calculate buttons sizes
            license_scrollable.scrollable_info.update_idletasks()

            license_frame_canvas.config(width=620, height=400)

            # Set the canvas scrolling region
            license_canvas.config(scrollregion=license_canvas.bbox("all"))

            for child in license_scrollable.scrollable_info.winfo_children():
                child.grid_configure(padx=5, pady=5)

        ttk.Separator(self.scrollable_info, orient="horizontal").grid(
            row=18, column=1, columnspan=3, sticky="EW"
        )

        tk.Button(
            self.scrollable_info,
            text="License",
            width=8,
            font=("Helvetica", 10, "bold"),
            cursor="hand2",
            command=open_license,
        ).grid(row=19, column=1, columnspan=3)

        for child in self.scrollable_info.winfo_children():
            child.grid_configure(padx=5, pady=5)

        # Create canvas window to hold the buttons_frame.
        canvas.create_window((0, 0), window=self.scrollable_info, anchor="nw")

        # Update buttons frames idle tasks to let tkinter calculate buttons sizes
        self.scrollable_info.update_idletasks()

        frame_canvas.config(width=810, height=540)

        # Set the canvas scrolling region
        canvas.config(scrollregion=canvas.bbox("all"))

    def run(self):
        """
        TODO: This is a temporary method. One of the last milestone before the final design
        it runs the GUI and return the options dictionary when the user quit the GUI in order
        to match the current behavior (the processing button quit the GUI)
        """
        self.mainloop()
        return self.get_parameters()
    
    def run_callback_and_destroy(self):
        """
        This method runs the processing callback and eventually destroys the GUI application
        """
        self.processing_callback(self, self.get_parameters())
        self.destroy()

    def _bootstrap(self):
        """Create the GUI"""
        self._preload_images()
        self._generate_parameters()

        self.iconbitmap(default=self._get_resource_path("icon_window.ico"))
        self.title("3DFIN")
        self.option_add("Helvetica", "12")
        self.resizable(False, False)
        self.geometry("810x632+0+0")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        ### Define here some infos and copyrights
        # Copyrights
        self.copyright_info_1 = (
            """ 3DFIN: Forest Inventory Copyright (C) 2023 Carlos Cabo & Diego Laino."""
        )
        self.copyright_info_2 = """This program comes with ABSOLUTELY NO WARRANTY. This is a free software, and you are welcome to redistribute it under certain conditions."""
        self.copyright_info_3 = (
            """See LICENSE at the botton of this tab for further details."""
        )

        # about the project
        self.about_1 = """This software has been developed at the Centre of Wildfire Research of Swansea University (UK) in collaboration with the Research Institute of 
        Biodiversity (CSIC, Spain) and the Department of Mining Exploitation of the University of Oviedo (Spain). Funding provided by the UK NERC 
        project (NE/T001194/1):"""
        self.about_2 = """and by the Spanish Knowledge Generation project (PID2021-126790NB-I00):"""

        ### Creating the tabs
        self.note = tk.ttk.Notebook(self)
        self.note.grid(column=0, row=0, sticky="NEWS")
        self._create_basic_tab()
        self._create_advanced_tab()
        self._create_expert_tab()
        self._create_about_tab()

        tk.Button(
            self,
            text="Select file & compute",
            bg="light green",
            width=30,
            font=("Helvetica", 10, "bold"),
            cursor="hand2",
            command=self.run_callback_and_destroy,
        ).grid(sticky="S")

        ### Adding a hyperlink to the documentation
        link1 = ttk.Label(
            self,
            text=" Documentation",
            font=("Helvetica", 11),
            foreground="blue",
            cursor="hand2",
        )
        link1.grid(sticky="NW")
        link1.bind(
            "<Button-1>",
            lambda e: subprocess.Popen(
                self._get_resource_path("documentation.pdf"), shell=True
            ),
        )
