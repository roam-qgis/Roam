## Development Setup (Windows + OSGeo4W QGIS LTR 3.44)
- install OSGeo4W (network installer) - choose express install and tick `QGIS LTR`:
    `https://download.osgeo.org/osgeo4w/v2/osgeo4w-setup.exe`
- clone the repo down to your machine:
    `git clone https://github.com/Nixxs/roam_site_avoidance`
- Open the Osgeo4W Shell and from that shell cd into the project
    `cd D:\Development\roam_site_avoidance`
- run the below command to set environment up:
    `scripts\setenv.bat`
    `scripts\setupdev.bat`
- then set your local environment up for your QGIS install should be:
    ```
    set PATH=C:\OSGeo4W\apps\Qt5\bin;C:\OSGeo4W\bin;C:\OSGeo4W\apps\qgis-ltr\bin;%PATH%
    set QT_PLUGIN_PATH=C:\OSGeo4W\apps\Qt5\plugins
    set PYTHONPATH=C:\OSGeo4W\apps\qgis-ltr
    ```
- next from the directory run the below to install dependancies:
    `python -m pip install -r requirements.txt`
- now run roam with either of the below:
    `python .\src\roam`
    `python .\src\configmanager`

## Building
- from the project root run:
    ```
    scripts\setenv.bat
    .\build.bat clean
    .\build.bat build
    .\build.bat exe
    ```