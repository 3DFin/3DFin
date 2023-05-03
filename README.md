
<img width="892" alt="3dfin_logo" src="https://user-images.githubusercontent.com/68945855/233049674-8d2c96a7-8abc-4a7c-8e83-4a329ba6dd0c.png">

Welcome to 3DFin: 3D Forest inventory's official repository!

3DFin is a free software for automatic computation of tree parameters in terrestrial point clouds. It offers the users a quick, ease-of-use interface to load their forest plots and generate tree metrics with just a few clicks.

Be sure to check the [Documentation](https://github.com/3DFin/3DFin/blob/main/src/three_d_fin/assets/documentation.pdf), which features detailed explanations on how the program works and an User manual.


# Download 

3DFin is available in Windows as a standalone program, which can be downloaded from here: [Download](https://github.com/3DFin/3DFin/releases/download/3DFin.exe).

Older versions of 3DFin may also be downloaded from [Releases](https://github.com/3DFin/3DFin/releases/). From there, simply navigate to the desired version and click on __3DFin.exe__.

3DFin may be launched from the command line as well after downloading the repository. To do so, simply change the working directory to `src` folder and use the following command:

```

python -m three_d_fin

```

For this last alternative to work you must install the required dependencies listed in `pyproject.toml` (/3DFin/3DFin/pyproject.toml).


# Further releases

Good news! Soon, 3DFin will also be available as a plugin in [CloudCompare](https://www.danielgm.net/cc/). CloudCompare is the largest, most used, free software for 3D point cloud visualization and manipulation.  It will also be available as a plugin in [QGIS](https://www.qgis.org/en/site/), the most used free software for GIS data.


# Acknowledgement

3DFin has been developed at the Centre of Wildfire Research of Swansea University (UK) in collaboration with the Research Institute of Biodiversity (CSIC, Spain) and the Department of Mining Exploitation of the University of Oviedo (Spain). 

Funding provided by the UK NERC project (NE/T001194/1): 

'_Advancing 3D Fuel Mapping for Wildfire Behaviour and Risk Mitigation Modelling_' 

and by the Spanish Knowledge Generation project (PID2021-126790NB-I00): 

‘_Advancing carbon emission estimations from wildfires applying artificial intelligence to 3D terrestrial point clouds_’.
