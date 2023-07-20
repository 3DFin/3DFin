
<img width="892" alt="3dfin_logo" src="https://user-images.githubusercontent.com/68945855/233049674-8d2c96a7-8abc-4a7c-8e83-4a329ba6dd0c.png">

Welcome to 3DFin: 3D Forest inventory's official repository!

3DFin is a free software for automatic computation of tree parameters in terrestrial point clouds. It offers the users a quick, ease-of-use interface to load their forest plots and generate tree metrics with just a few clicks.

Be sure to check the [Documentation](https://github.com/3DFin/3DFin/blob/main/src/three_d_fin/documentation/documentation.pdf), which features detailed explanations on how the program works and an User manual.


# Download 

3DFin is available in Windows as a standalone program, which can be downloaded from here: [Download](https://github.com/3DFin/3DFin/releases/download/3DFin.exe).

Older versions of 3DFin may also be downloaded from [Releases](https://github.com/3DFin/3DFin/releases/download/v0.2.0rc5/3DFin.exe). From there, simply navigate to the desired version and click on __3DFin.exe__.

For all OSes, 3DFin is also available as a Python package in PyPI.

```console
pip install 3DFin
```

pip will install a script entry point in your Python installation's bin|script directory, so you should be able to launch 3DFin from the command line with:  

```console
3DFin[.exe]
```

macOS user may need to install and use an openMP capable compiler, such as GCC from [Homebrew](https://brew.sh/) in order to install the dependencies. 

3DFin is also available as a plugin for [CloudCompare](https://www.danielgm.net/cc/) thanks to [CloudCompare-PythonPlugin](https://github.com/tmontaigu/CloudCompare-PythonPlugin). It is included in latest cloudcompare beta (2.13 beta).

# Usage

By default running 3DFin will open a GUI window. The [documentation](https://github.com/3DFin/3DFin/blob/main/src/three_d_fin/documentation/documentation.pdf) contains a detailed explanation of the GUI and its functionalities.

For batch processing you can use the CLI capabilities of 3DFin and running the following command:
```console
3DFin[.exe] cli --help
```
will give you an overview of the available parameters. 

# Further releases

Good news! Soon, 3DFin will also be available as a plugin in [QGIS](https://www.qgis.org/en/site/), the most used free software for GIS data.

# Citing 3DFin

As of now, the best way to cite 3DFin is by referring to the original paper describing the algorithm behind:

Cabo, C., Ordóñez, C., López-Sánchez, C. A., & Armesto, J. (2018). Automatic dendrometry: Tree detection, tree height and diameter estimation using terrestrial laser scanning. International Journal of Applied Earth Observation and Geoinformation, 69, 164–174. https://doi.org/10.1016/j.jag.2018.01.011

Or directly citing the repository itself:

3DFin: 3D Forest Inventory. 3DFin https://github.com/3DFin/3DFin.

We are currently working on a scientific article about 3DFin, which may be published in 2023.


# Acknowledgement

3DFin has been developed at the Centre of Wildfire Research of Swansea University (UK) in collaboration with the Research Institute of Biodiversity (CSIC, Spain) and the Department of Mining Exploitation of the University of Oviedo (Spain). 

Funding provided by the UK NERC project (NE/T001194/1): 

'_Advancing 3D Fuel Mapping for Wildfire Behaviour and Risk Mitigation Modelling_' 

and by the Spanish Knowledge Generation project (PID2021-126790NB-I00): 

‘_Advancing carbon emission estimations from wildfires applying artificial intelligence to 3D terrestrial point clouds_’.
