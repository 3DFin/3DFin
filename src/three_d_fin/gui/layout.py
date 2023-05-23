import subprocess
import sys
import tkinter as tk
from inspect import cleandoc
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Optional

import laspy
from PIL import Image, ImageTk
from pydantic import ValidationError
from pydantic.fields import ModelField

from three_d_fin import __about__
from three_d_fin.gui.tooltip import ToolTip
from three_d_fin.processing.abstract_processing import FinProcessing
from three_d_fin.processing.configuration import (
    FinConfiguration,
)


class Application(tk.Tk):
    """Encapsulate GUI creation and interactions for 3DFin application."""

    def __init__(
        self,
        processing_object: FinProcessing,
        file_externally_defined: bool = False,
        cloud_fields: Optional[set[str]] = None,
    ):
        """Construct the 3DFin GUI Application.

        Parameters
        ----------
        processing_object : FinProcessing
            An implementation of the abstract FinProcessing class.
            it is responsible for the computing logic.
            Its process() method is triggered by the "compute" button of the GUI.
        file_externally_defined : bool
            Whether or not the file/filename was already defined by a third party.
            if True, input_las input and buttons will be disabled.
        cloud_fields : Optional[list[str]]
            List of candidates fields for the Z0 field. If present (not None),
            the z0_entry will be turned into a dropdown menu. If present but void,
            height normalization radio buttons will be disabled.
            TODO: we can imagine, no z0 fields and z == z0
        """
        tk.Tk.__init__(self)
        self.processing_object = processing_object
        self.file_externally_defined = file_externally_defined
        self.cloud_fields = cloud_fields
        self._bootstrap()

    def _get_resource_path(self, relative_path: str) -> str:
        """Retrieve the path of the assets.

        Assets path is different if run in a standalone fashion or run as a "script"

        Parameters
        ----------
        relative_path : str
            Current relative path to the ressource.

        Returns
        -------
        return_path : str
            Full path to the ressource.
        """
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = Path(__file__).absolute().parents[1] / "assets"
        return str(base_path / Path(relative_path))

    def _preload_images(self) -> None:
        """Centralise assets loading and expose them to class members.

        TODO: Add license loading too.
        """
        self.logo_png = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("3dfin_logo.png"))
        )
        self.sections_img = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("section_details.png"))
        )
        self.sectors_img = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("sectors.png"))
        )
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
        self.cetemas_logo_img = ImageTk.PhotoImage(
            Image.open(self._get_resource_path("cetemas_logo_1.png"))
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

    def _generate_parameters(self) -> None:
        """Generate dendromatics mandatory parameters.

        Try to load a config file in the root of CWD and, if it fails,
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

        # Variable to keep track of the option selected in normalized_button_1
        self.is_normalized = tk.BooleanVar()
        # Variable to keep track of the option selected in clean_button_1
        self.is_noisy = tk.BooleanVar()
        # Variable to keep track of the option selected in excel_button_1
        self.export_txt = tk.BooleanVar()
        # I/O related parameters
        self.output_dir = tk.StringVar()
        self.input_file = tk.StringVar()

        try:
            ### Reading config file only if it is available under name '3DFinconfig.ini'
            config_file_path = Path("3DFinconfig.ini")
            config = FinConfiguration.From_config_file(
                config_file_path.resolve(strict=True), init_misc=True
            )
            print("Configuration file found. Setting default parameters from the file")
        except ValidationError:
            print("Configuration file error")
            config = FinConfiguration()
        except FileNotFoundError:
            # no error message in this case, fallback to default parameters
            config = FinConfiguration()

        # params and tk.Variable instances have the same name, we take advantage of that
        config_dict = config.dict()
        for config_section in config_dict:
            for key_param, value_param in config_dict[config_section].items():
                # Default z0_name should match one of the supplied list if present.
                if (key_param == "z0_name") and self.cloud_fields is not None:
                    if value_param in self.cloud_fields:
                        getattr(self, key_param).set(value_param)
                # Fix a minor presentation issue when no file is defined
                elif key_param == "input_file" and value_param is None:
                    getattr(self, key_param).set("")
                else:
                    getattr(self, key_param).set(value_param)

    def get_parameters(self) -> dict[str, dict[str, str]]:
        """Get parameters from widgets and return them organized in a dictionary.

        Returns
        -------
        options : dict[str, dict[str, str]]
            Dictionary of parameters. It is organized following the
            3DFinconfig.ini file: Each parameters are sorted in sub-dict
            ("basic", "expert", "advanced", "misc").
        """
        config_dict: dict[str, dict[str, str]] = dict()
        for category_name, category_field in FinConfiguration.__fields__.items():
            category_dict: dict[str, str] = dict()
            for category_param in category_field.type_().__fields__:
                category_dict[category_param] = getattr(self, category_param).get()
            config_dict[category_name] = category_dict
        # if the file is defined elsewhere, no need to define it
        if self.file_externally_defined:
            config_dict["misc"]["input_file"] = None
        return config_dict

    def _create_basic_tab(self) -> None:
        """Create the "basic" parameters tab (1)."""
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

        # Z0 field name
        # It can be and entry or a dropdown (optionmenu)
        if self.cloud_fields is None:
            z0_entry = ttk.Entry(self.basic_tab, width=7, textvariable=self.z0_name)
            z0_entry.grid(column=3, row=7, sticky="EW")
        else:
            z0_entry = ttk.OptionMenu(
                self.basic_tab, self.z0_name, self.z0_name.get(), *self.cloud_fields
            )
            z0_entry.grid(column=3, row=7, columnspan=2, sticky="EW")

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
        ttk.Label(self.basic_tab, image=self.logo_png).grid(
            column=6, row=1, rowspan=2, columnspan=2, sticky="NS"
        )

        #### Text displaying info
        insert_text1 = (
            "This program implements an algorithm to detect the trees "
            "present in a ground-based\n 3D point cloud from a forest plot, and compute"
            " individual tree parameters: tree height,\ntree location, diameters along"
            " the stem (including DBH), and stem axis.\n\n"
            "It takes a .LAS/.LAZ file as input, which may contain extra fields "
            "(.LAS standard \nor not). Also, the input point cloud can come from "
            "terrestrial photogrammetry,\nTLS or mobile (e.g. hand-held) LS, a "
            "combination of those, and/or a combination\nof those with UAV-(LS or SfM),"
            " or ALS.\n\nAfter all computations are done, it outputs several .LAS files"
            " containing resulting\npoint clouds and a XLSX file storing tabular data. "
            "Optionally, tabular data may be\noutput as text files instead of the Excel"
            " spreadsheet if preferred.\n\n"
            "Further details may be found in next tabs and in the documentation."
        )

        ttk.Separator(self.basic_tab, orient="vertical").grid(
            column=5, row=1, rowspan=10, sticky="NS"
        )

        ttk.Label(self.basic_tab, text=cleandoc(insert_text1)).grid(
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

        for child in self.basic_tab.winfo_children():
            child.grid_configure(padx=5, pady=5)

        ttk.Label(
            self.basic_tab, text="Region where one should expect mostly stems."
        ).grid(column=1, row=13, columnspan=4, sticky="N")

        ttk.Label(
            self.basic_tab,
            text="3DFin is able to normalize heights automatically, but also\n"
            "allows using already height-normalized point clouds.",
        ).grid(column=6, row=13, columnspan=2, sticky="N")

        #### Adding radio buttons
        def _enable_denoising() -> None:
            z0_entry.configure(state="normal")
            z0_entry.update()
            clean_button_1.configure(state="disabled")
            clean_button_1.update()
            clean_button_2.configure(state="disabled")
            clean_button_2.update()

        def _disable_denoising() -> None:
            z0_entry.configure(state="disabled")
            z0_entry.update()
            clean_button_1.configure(state="normal")
            clean_button_1.update()
            clean_button_2.configure(state="normal")
            clean_button_2.update()

        normalized_button_1 = ttk.Radiobutton(
            self.basic_tab,
            text="Yes",
            variable=self.is_normalized,
            value=True,
            command=_enable_denoising,
        )
        normalized_button_1.grid(column=2, row=2, sticky="EW")
        normalized_button_2 = ttk.Radiobutton(
            self.basic_tab,
            text="No",
            variable=self.is_normalized,
            value=False,
            command=_disable_denoising,
        )
        normalized_button_2.grid(column=3, row=2, sticky="EW")

        if self.cloud_fields is not None and not self.cloud_fields:
            normalized_button_1.configure(state=tk.DISABLED)
            normalized_button_2.configure(state=tk.DISABLED)

        # Create the optionmenu widget and passing the options_list and value_inside to it.
        clean_button_1 = ttk.Radiobutton(
            self.basic_tab, text="Yes", variable=self.is_noisy, value=True
        )
        clean_button_1.grid(column=2, row=4, sticky="EW")
        clean_button_2 = ttk.Radiobutton(
            self.basic_tab, text="No", variable=self.is_noisy, value=False
        )
        clean_button_2.grid(column=3, row=4, sticky="EW")

        # Create the optionmenu widget and passing the options_list and value_inside to it.
        txt_button_1 = ttk.Radiobutton(
            self.basic_tab, text="TXT files", variable=self.export_txt, value=True
        )
        txt_button_1.grid(column=2, row=6, sticky="EW")
        txt_button_1 = ttk.Radiobutton(
            self.basic_tab, text="XLSX files", variable=self.export_txt, value=False
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

    def _create_advanced_tab(self) -> None:
        """Create the advanced parameters tab (2)."""
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
        insert_text2 = (
            "If the results obtained by just tweaking basic parameters do "
            "not meet your expectations,\nyou might want to modify these.\n\n"
            "You can get a brief description of what they do by hovering the mouse over"
            " the info icon\nright before each parameter. However, keep in mind that a "
            "thorough understanding is\nadvisable before changing these. For that, you "
            "can get a better grasp of what the algo-\nrithm does in the attached "
            "documentation. You can easily access it through the\nDocumentation button "
            "in the bottom-right corner."
        )

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
        ttk.Label(self.advanced_tab, text=cleandoc(insert_text2)).grid(
            column=6, row=2, rowspan=8, sticky="NW"
        )

        for child in self.advanced_tab.winfo_children():
            child.grid_configure(padx=5, pady=5)

        #### Adding images

        ttk.Label(self.advanced_tab, image=self.sections_img).grid(
            column=1, row=9, columnspan=15, sticky="W", padx=20, pady=5
        )

        sections_text = (
            "A) Sections along the stem B) Detail of computed sections \n"
            "showing the distance between them and their width \n"
            "C) Circle fitting to the points of a section."
        )

        ttk.Label(self.advanced_tab, text=cleandoc(sections_text)).grid(
            column=1, row=10, columnspan=15, sticky="NW", padx=20, pady=5
        )

        ttk.Label(self.advanced_tab, image=self.sectors_img).grid(
            column=1, row=9, columnspan=15, sticky="E", padx=20, pady=5
        )

        sectors_text = """Several quality controls are implemented to
        validate the fitted circles, such as measuring
        the point distribution along the sections."""

        ttk.Label(self.advanced_tab, text=cleandoc(sectors_text)).grid(
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
            "as potential stem points. Reasonable values are 'Maximum diameter'-2 "
            "meters \n(exceptionally greater than 2: very large diameters and/or "
            "intricate stems).",
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
            "(vertical) are considered during circle fitting and diameter "
            "computation.\nDefault value: 0.05 meters.",
        )

    def _create_expert_tab(self) -> None:
        """Create the expert parameters tab (3)."""
        self.expert_tab = ttk.Frame(self.note)

        self.note.add(self.expert_tab, text="Expert")

        ### Stem identification from stripe ###
        ttk.Label(
            self.expert_tab,
            text="Stem identification within the stripe",
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
            "Verticality is defined as (1 - sin(V)), being V the vertical angle of the "
            "normal\nvector, measured from the horizontal. Note that it does not grow "
            "linearly.\nDefault value: 0.7.",
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
            "Verticality is defined as (1 - sin(V)), being V the vertical angle of the "
            "normal\nvector, measured from the horizontal. Note that it does not grow "
            "linearly.\nDefault value: 0.7.",
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
            "Default value: 0.02 meters.",
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
            "Default value: 0.7.",
        )

        def _open_warning() -> None:
            """Logic triggered by the warning button."""
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
                text="Before modifying these, you should read the documentation and "
                "the\nreferences listed below for a deep understading of what the "
                "algorithm does.",
                font=("Helvetica", 10),
            ).grid(column=1, row=3, sticky="W")

            ttk.Label(new, text="References:", font=("Helvetica", 11)).grid(
                column=1, row=4, sticky="W"
            )
            ttk.Label(
                new,
                text="Cabo, C., Ordonez, C., Lopez-Sanchez, C. A., & Armesto, J. (2018)"
                ". Automatic dendrometry:\nTree detection, tree height and diameter "
                "estimation using terrestrial laser scanning.\nInternational Journal "
                "of Applied Earth Observation and Geoinformation, 69, 164–174.\n"
                "https://doi.org/10.1016/j.jag.2018.01.011",
                font=("Helvetica", 10),
            ).grid(column=1, row=5, sticky="W")

            ttk.Label(
                new,
                text="Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996). A "
                "Density-Based Algorithm for\nDiscovering Clusters in Large Spatial "
                "Databases with Noise. www.aaai.org",
                font=("Helvetica", 10),
            ).grid(column=1, row=6, sticky="W")

            ttk.Label(
                new,
                text="Prendes, C., Cabo, C., Ordoñez, C., Majada, J., & Canga, E. "
                "(2021). An algorithm for\nthe automatic parametrization of wood "
                "volume equations from Terrestrial Laser Scanning\npoint clouds: "
                "application in Pinus pinaster. GIScience and Remote Sensing, 58(7), "
                "1130–1150.\nhttps://doi.org/10.1080/15481603.2021.1972712",
                font=("Helvetica", 10),
            ).grid(column=1, row=7, sticky="W")

            ttk.Label(
                new,
                text="Zhang, W., Qi, J., Wan, P., Wang, H., Xie, D., Wang, X., & Yan, "
                "G. (2016). An\neasy-to-use airborne LiDAR data filtering method based "
                "on cloth simulation. Remote Sensing, 8(6).\n"
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
            command=_open_warning,
        ).grid(column=9, row=1, columnspan=2, sticky="E")

    def _create_about_tab(self) -> None:
        """Create the about tab (4)."""
        self.about_tab = ttk.Frame(self.note)
        self.note.add(self.about_tab, text="About")

        ### TEAM MEMBERS ###
        carloscabo = (
            "Carlos Cabo (carloscabo.uniovi@gmail.com). PhD in Geomatics. "
            "'Maria Zambrano' Research Fellow at Department of\nMining Exploitation, "
            "University of Oviedo and Honorary Appointment at Science and Engineering "
            "Faculty, Swansea\nUniversity. Research fields: Spatial analysis, "
            "cartography, geomatics."
        )

        diegolaino = (
            "Diego Laino (diegolainor@gmail.com). PhD student in Natural "
            "Resources Engineering at Department of Mining Exploit-\nation, University "
            "Oviedo. Assist. Researcher at Centre for Wildfire Research, Geography of "
            "Department, Swansea Univer-\nsity. Research fields: deep learning, remote "
            "sensing, forestry."
        )

        covadongaprendes = (
            "Covadonga Prendes (cprendes@cetemas.es). PhD in Geomatics. "
            "Forest engineer and researcher at CETEMAS (Forest and\nWood Technology "
            "Research Centre Foundation). Geomatics research group. Research fields: "
            "LiDAR, sustainable forestry\ndevelopment, spatial analysis."
        )

        crissantin = (
            "Cristina Santin (c.santin@csic.es). Research fellow at the "
            "Research Institute of Biodiversity (CSIC-University of Oviedo\n- "
            "Principality of Asturias, Spain) and Honorary Assoc. Professor at the "
            "Biosciences Department of Swansea University.\nResearch fields: "
            "environmental impacts of wildfires."
        )

        stefandoerr = (
            "Stefan Doerr (s.doerr@swansea.ac.uk). PhD in Geography. Full \n"
            "Professor at the Geography Department, Swansea Univer-\nsity and Director "
            "of its Centre for Wildfire Research. Editor-in-Chief: International "
            "Journal of Wildland Fire. Research fields:\nwildfires, landscape carbon "
            "dynamics, soils, water quality, ecosystem services."
        )

        celestinoordonez = (
            "Celestino Ordonez (ordonezcelestino@uniovi.es). PhD in "
            "Mine Engineering. Full professor at Department of Mining Ex-\nploitation, "
            "University of Oviedo. Main researcher at GEOGRAPH research group. Research"
            " fields: Spatial analysis, laser\nscanning, photogrammetry."
        )

        tadasnikonovas = (
            "Tadas Nikonovas (tadas.nikonovas@swansea.ac.uk). PhD in "
            "Geography. Office Researcher at Centre for Wildfire Research,\nGeography "
            "Department, Swansea University. Research fields: Global fire activity, "
            "atmospheric emissions, fire occurrence\nmodelling."
        )

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
            self.scrollable_info,
            text=__about__.__copyright_info_1__,
            font=("Helvetica", 10, "bold"),
        )
        copyright_1_lab.grid(row=1, column=1, columnspan=3)

        copyright_2_lab = ttk.Label(
            self.scrollable_info, text=__about__.__copyright_info_2__
        )
        copyright_2_lab.grid(row=2, column=1, columnspan=3)

        copyright_3_lab = ttk.Label(
            self.scrollable_info, text=__about__.__copyright_info_3__
        )
        copyright_3_lab.grid(row=3, column=1, columnspan=3)

        # About the project #
        about_1_lab = ttk.Label(
            self.scrollable_info, text=cleandoc(__about__.__about_1__)
        )
        about_1_lab.grid(row=4, column=1, columnspan=3, sticky="W")

        nerc_project_lab = ttk.Label(
            self.scrollable_info,
            text=__about__.__nerc_project__,
            font=("Helvetica", 10, "italic"),
        )
        nerc_project_lab.grid(row=5, column=1, columnspan=3)

        about_2_lab = ttk.Label(self.scrollable_info, text=__about__.__about_2__)
        about_2_lab.grid(row=6, column=1, columnspan=3, sticky="W")

        csic_project_lab = ttk.Label(
            self.scrollable_info,
            text=__about__.__csic_project__,
            font=("Helvetica", 10, "italic"),
        )
        csic_project_lab.grid(row=7, column=1, columnspan=3)

        ttk.Label(self.scrollable_info, image=self.csic_logo_img).grid(
            row=8, column=1, columnspan=3, sticky="W"
        )
        ttk.Label(self.scrollable_info, image=self.spain_logo_img).grid(
            row=8, column=1, columnspan=3
        )
        ttk.Label(self.scrollable_info, image=self.nerc_logo_img).grid(
            row=8, column=1, columnspan=3, sticky="E"
        )
        ttk.Label(self.scrollable_info, image=self.cetemas_logo_img).grid(
            row=9, column=1, columnspan=3, sticky="W"
        )
        ttk.Label(self.scrollable_info, image=self.uniovi_logo_img).grid(
            row=9, column=1, columnspan=3
        )
        ttk.Label(self.scrollable_info, image=self.swansea_logo_img).grid(
            row=9, column=1, columnspan=3, sticky="E"
        )

        ttk.Separator(self.scrollable_info, orient="horizontal").grid(
            row=10, column=1, columnspan=3, sticky="EW"
        )

        team_lab = ttk.Label(
            self.scrollable_info, text="Team", font=("Helvetica", 12, "bold")
        )
        team_lab.grid(row=11, column=1, columnspan=3)

        carloscabo_lab = ttk.Label(self.scrollable_info, text=cleandoc(carloscabo))
        carloscabo_lab.grid(row=11, column=2, columnspan=2, sticky="W")

        diegolaino_lab = ttk.Label(self.scrollable_info, text=cleandoc(diegolaino))
        diegolaino_lab.grid(row=12, column=2, columnspan=2, sticky="W")

        covadongaprendes_lab = ttk.Label(
            self.scrollable_info, text=cleandoc(covadongaprendes)
        )
        covadongaprendes_lab.grid(row=13, column=2, columnspan=2, sticky="W")

        crissantin_lab = ttk.Label(self.scrollable_info, text=cleandoc(crissantin))
        crissantin_lab.grid(row=14, column=2, columnspan=2, sticky="W")

        stefandoerr_lab = ttk.Label(self.scrollable_info, text=cleandoc(stefandoerr))
        stefandoerr_lab.grid(row=15, column=2, columnspan=2, sticky="W")

        celestinoordonez_lab = ttk.Label(
            self.scrollable_info, text=cleandoc(celestinoordonez)
        )
        celestinoordonez_lab.grid(row=16, column=2, columnspan=2, sticky="W")

        tadasnikonovas_lab = ttk.Label(
            self.scrollable_info, text=cleandoc(tadasnikonovas)
        )
        tadasnikonovas_lab.grid(row=17, column=2, columnspan=2, sticky="W")

        ttk.Label(self.scrollable_info, image=self.carlos_img).grid(row=11, column=1)

        ttk.Label(self.scrollable_info, image=self.diego_img).grid(row=12, column=1)

        ttk.Label(self.scrollable_info, image=self.covadonga_img).grid(row=13, column=1)

        ttk.Label(self.scrollable_info, image=self.cris_img).grid(row=14, column=1)

        ttk.Label(self.scrollable_info, image=self.stefan_img).grid(row=15, column=1)

        ttk.Label(self.scrollable_info, image=self.celestino_img).grid(row=16, column=1)

        ttk.Label(self.scrollable_info, image=self.tadas_img).grid(row=17, column=1)

        def _open_license() -> None:
            """Load the licence and display it in a frame."""
            with Path(self._get_resource_path("License.txt")).open("r") as f:
                gnu_license = f.read()
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
                    license_frame_canvas,
                    orient="vertical",
                    command=license_canvas.yview,
                )
                license_vsb.grid(row=0, column=1, sticky="ns")
                license_canvas.configure(yscrollcommand=license_vsb.set)

                # Create a frame to contain the info
                license_scrollable = ttk.Frame(license_canvas)

                new.geometry("620x400")
                new.title("LICENSE")
                ttk.Label(
                    license_scrollable,
                    text="GNU GENERAL PUBLIC LICENSE",
                    font=("Helvetica", 10, "bold"),
                ).grid(row=1, column=1)

                ttk.Label(
                    license_scrollable,
                    text=gnu_license,
                    font=("Helvetica", 10),
                ).grid(row=2, column=1, sticky="W")

                # Create canvas window to hold the buttons_frame.
                license_canvas.create_window(
                    (0, 0), window=license_scrollable, anchor="nw"
                )

                # Update buttons frames idle tasks to let tkinter calculate button sizes
                license_scrollable.update_idletasks()

                license_frame_canvas.config(width=620, height=400)

                # Set the canvas scrolling region
                license_canvas.config(scrollregion=license_canvas.bbox("all"))

                for child in license_scrollable.winfo_children():
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
            command=_open_license,
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

    def _create_bottom_part(self) -> None:
        """Create the bottom part of the window."""
        bottom_frame = tk.Frame(self)

        def _ask_output_dir() -> None:
            """Ask for a proper output directory."""
            output_dir = filedialog.askdirectory(
                parent=self,
                title="3DFin output directory",
                initialdir=self.output_dir.get(),
            )
            # If the dialog was not closed/cancel
            if output_dir != "" and not None:
                self.output_dir.set(str(Path(output_dir).resolve()))

        def _ask_input_file() -> None:
            """Ask for a proper input las file.

            Current selected file is checked for validity (existence and type)
            in order to setup the initial dir and the initial file in
            the dialog. If a file is selected then it is checked to be a valid
            Las file before adding its path to the related input field.
            the output directory is changed accordingly (default to input las file
            parent directory)
            """
            initial_path = Path(self.input_file.get())
            is_initial_file = (
                True if initial_path.exists() and initial_path.is_file() else False
            )
            initial_dir = (
                initial_path.parent.resolve() if is_initial_file else Path.home()
            )
            initial_file = str(initial_path.resolve()) if is_initial_file else ""
            las_file = filedialog.askopenfilename(
                parent=self,
                title="3DFin input file",
                filetypes=[("las files", ".las .Las .Laz .laz")],
                initialdir=initial_dir,
                initialfile=initial_file,
            )
            # If the dialog was not closed/cancel
            if las_file != "" and not None:
                try:
                    laspy.open(las_file, read_evlrs=False)
                except laspy.LaspyException:
                    messagebox.showerror(
                        parent=self, title="3DFin Error", message="Invalid las file"
                    )
                    return
                self.input_file.set(str(Path(las_file).resolve()))
                self.output_dir.set(str(Path(las_file).parent.resolve()))

        self.label_file = ttk.Label(
            bottom_frame,
            text="Input file",
        )
        self.label_file.grid(row=0, column=0, sticky="W", padx=(5, 0))

        self.label_directory = ttk.Label(bottom_frame, text="Output directory")
        self.label_directory.grid(row=0, column=2, sticky="W")

        self.input_file_entry = ttk.Entry(
            bottom_frame, width=30, textvariable=self.input_file
        )
        self.input_file_entry.grid(row=1, column=0, sticky="W", padx=5)

        self.input_file_button = ttk.Button(
            bottom_frame, text="Select file", command=_ask_input_file
        )
        self.input_file_button.grid(row=1, column=1, sticky="W", padx=(5, 15))

        # If the file is defined by a third party and will be provided in the callback
        # by another mean than input from the GUI, we do not want to show field related
        # to Las input.
        if self.file_externally_defined:
            self.label_file.config(state=tk.DISABLED)
            self.label_file.config(text="File already set by the application")
            self.input_file_button.config(state=tk.DISABLED)
            self.input_file_entry.config(state=tk.DISABLED)

        self.output_dir_entry = ttk.Entry(
            bottom_frame, width=30, textvariable=self.output_dir
        )
        self.output_dir_entry.grid(row=1, column=2, sticky="W")

        self.output_dir_button = ttk.Button(
            bottom_frame, text="Select directory", command=_ask_output_dir
        )
        self.output_dir_button.grid(row=1, column=3, sticky="W", padx=(5, 20))

        self.compute_button = tk.Button(
            bottom_frame,
            text="Compute",
            bg="light green",
            width=25,
            font=("Helvetica", 10, "bold"),
            cursor="hand2",
            command=self.validate_and_run_processing_callback,
        )
        self.compute_button.grid(column=5, row=1, sticky="N")

        ### Adding a hyperlink to the documentation
        link1 = ttk.Label(
            bottom_frame,
            text=" Documentation",
            font=("Helvetica", 11),
            foreground="blue",
            cursor="hand2",
        )
        link1.grid(row=3, column=5, sticky="SE", columnspan=5)
        link1.bind(
            "<Button-1>",
            lambda _: subprocess.Popen(
                self._get_resource_path("documentation.pdf"), shell=True
            ),
        )
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def run(self) -> dict[str, dict[str, Any]]:
        """Run the GUI main loop and return the parameters when it quits.

        Returns
        -------
        options : dict[str, dict[str, Any]]
            parameters from the GUI
        """
        self.mainloop()
        return self.get_parameters()

    def validate_and_run_processing_callback(self) -> None:
        """Validate I/O entries and run the processing callback."""
        params = self.get_parameters()

        # define a lambda to popup error for convenience
        def _show_error(error_msg: str) -> str:
            return messagebox.showerror(
                parent=self, title="3DFin Error", message=error_msg
            )

        # Pydantic checks, we check the validity of the data
        try:
            fin_config = FinConfiguration.parse_obj(params)
        except ValidationError as validation_errors:
            final_msg: str = "Invalid Parameters:\n\n"
            for error in validation_errors.errors():
                error_loc: list[str] = error["loc"]
                # Get the human readable value for the field by introspection
                # (stored in "title "attribute)
                field: ModelField = (
                    FinConfiguration.__fields__[error_loc[0]]
                    .type_()
                    .__fields__[error_loc[1]]
                )
                title = field.field_info.title
                # formatting
                final_msg = final_msg + f"{title} \n"
                final_msg = final_msg + f"""\t -> {error["msg"]} \n"""
            _show_error(final_msg)
            return

        self.processing_object.set_config(fin_config)
        # Here we will check in an astract way if the output could collides
        # with previous computation. and ask if we want to overwrite them.
        if self.processing_object.check_already_computed_data():
            overwrite = messagebox.askokcancel(
                title="3DFin",
                message="The output target already contains results from a previous 3DFin computation, do you want to overwrite them?",
            )
            if not overwrite:
                return

        # Now we do the processing in itself
        # TODO: handle exception in processing here
        self.processing_object.process()

    def _bootstrap(self) -> None:
        """Create the GUI."""
        self._preload_images()
        self._generate_parameters()

        self.iconbitmap(default=self._get_resource_path("icon_window.ico"))

        self.title(f"3DFin v{__about__.__version__}")
        self.option_add("Helvetica", "12")
        self.resizable(False, False)
        self.geometry("810x654+0+0")

        ### Creating the tabs
        self.note = ttk.Notebook(self)
        self._create_basic_tab()
        self._create_advanced_tab()
        self._create_expert_tab()
        self._create_about_tab()
        self.note.pack(side=tk.TOP)

        ### Creating a frame at the bottom with I/O interactions
        self._create_bottom_part()
