
<img width="892" alt="3dfin_logo" src="https://user-images.githubusercontent.com/68945855/233049674-8d2c96a7-8abc-4a7c-8e83-4a329ba6dd0c.png">

Welcome to 3DFin: 3D Forest inventory's official repository!

3DFin is a free software for automatic computation of tree parameters in terrestrial point clouds. It offers the users a quick, ease-of-use interface to load their forest plots and generate tree metrics with just a few clicks.


# Getting Started 

Be sure to check the [Documentation](https://github.com/3DFin/3DFin/blob/main/src/three_d_fin/documentation/documentation.pdf), which features detailed explanations on how the program works and an User Manual.

Also, the [Tutorial](https://github.com/3DFin/3DFin_Tutorial) covers the basics of 3DFin and is a great tool to get started.


# Download 

3DFin is freely available in 4 ways:
1. As a CloudCompare plugin (**Windows and Linux**)
2. As a QGIS plugin
3. As a standalone program (**Only in Windows**)
4. As a Python package (**In Windows, Linux and macOS**)

## 1. CloudCompare plugin 

3DFin is available in Windows as a **plugin in CloudCompare (2.13)** thanks to CloudCompare PythonRuntime (see [References](#references)). You can download the latest version CloudCompare (Windows installer version) including the 3DFin plugin here:

[CloudCompare](https://www.danielgm.net/cc/release/)

Simply install the latest version of CloudCompare and tick Python and 3DFin's checkbox during the installation:

**To install 3DFin plugin, tick the 'Python plugin support' checkbox during CloudCompare installation.** 
![image](https://github.com/3DFin/3DFin/assets/68945855/f34b4cd9-58ce-41fc-a8bd-262dd11ff8e7)

For Linux, the plugin is embedded into the CloudCompare [flatpak](https://flathub.org/fr/apps/org.cloudcompare.CloudCompare). 

**3DFin plugin in CloudCompare.**
![Fig_01](https://github.com/3DFin/3DFin/assets/68945855/2c874f53-39fd-4eff-b29c-15f3ca80013d)

Running the plugin will open 3DFin's graphical user interface (GUI). 
**3DFin GUI. It is common to any version of 3DFin.**
![basic_tab](https://github.com/3DFin/3DFin/assets/68945855/d6d21e45-5934-4762-88ec-782c03f4700d)


## 2. QGIS plugin 

3DFin is also available as a plugin in [QGIS](https://www.qgis.org/en/site/). Please follow the instructions available [here](https://github.com/3DFin/3DFin-QGIS) in order to test it. 
Note that for now this does not provide much added value in comparison with CloudCompare and Standalone version of 3DFin.

## 3. Standalone program

3DFin is also available in Windows and macOS as a standalone program, which can be downloaded from here: 

[Standalone](https://github.com/3DFin/3DFin/releases). 

`3DFin.exe` file is the Windows version while `3DFin` is the macOS version.
These binaries are built into Github servers and are thus unsigned and unverified. As consequences, while executing theses binaries your system may warn from security issues and should ask you to grant some permissions. 
If you have a complete Python environment on your system, please consider installing 3DFin standalone via [`pip` package manager](#4-python-package-3dfin).

Older versions of 3DFin standalone may also be downloaded from [Releases](https://github.com/3DFin/3DFin/releases/). From there, simply navigate to the desired version and click on __3DFin[.exe]__.


## 4. Python package (3DFin)

3DFin and its dependencies may be installed and launched **in any OS (Windows, Linux and macOS)** as a Python package: 

```console
pip install 3DFin
python -m three_d_fin
```

*If you are a macOS or Linux user and you may want to try 3DFin, this is the way you should proceed.*

`pip` will also install a script entry point in your Python installation's bin|script directory, so alternatively you can launch 3DFin from the command line with:  

```console
3DFin[.exe]
```

# Usage

CloudCompare plugin is the reccomended way of using 3DFin, as it provides enhanced features for visualisation of the results and exporting of the outputs (it allows to export the results as a CloudCompare native BIN file). 

By default, running 3DFin (either the CloudCompare plugin or any version of 3DFin) will open a GUI window.

For batch processing you can use the CLI capabilities of 3DFin and running the following command:
```console
3DFin[.exe] cli --help
```
will give you an overview of the available parameters. 


# Citing 3DFin

As of now, the best way to cite 3DFin is by referring to the original paper describing the algorithm behind:

Cabo, C., Ordóñez, C., López-Sánchez, C. A., & Armesto, J. (2018). Automatic dendrometry: Tree detection, tree height and diameter estimation using terrestrial laser scanning. International Journal of Applied Earth Observation and Geoinformation, 69, 164–174. https://doi.org/10.1016/j.jag.2018.01.011

Or directly citing the repository itself:

3DFin: 3D Forest Inventory. 3DFin https://github.com/3DFin/3DFin.

We are currently working on a scientific article about 3DFin, which may be published in 2023.

# References 

CloudCompare-PythonRuntime, by Thomas Montaigu: [CloudCompare-PythonRuntime](https://github.com/tmontaigu/CloudCompare-PythonRuntime)

# Acknowledgement

3DFin has been developed at the Centre of Wildfire Research of Swansea University (UK) in collaboration with the Research Institute of Biodiversity (CSIC, Spain) and the Department of Mining Exploitation of the University of Oviedo (Spain). 

Funding provided by the UK NERC project (NE/T001194/1): 

'_Advancing 3D Fuel Mapping for Wildfire Behaviour and Risk Mitigation Modelling_' 

and by the Spanish Knowledge Generation project (PID2021-126790NB-I00): 

‘_Advancing carbon emission estimations from wildfires applying artificial intelligence to 3D terrestrial point clouds_’.
