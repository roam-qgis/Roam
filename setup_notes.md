## DEV Enviornment Setup Instruction:

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


### Other notes:
- Install OsGeo4W using express install as admin
- run the OSGeo4W Shell as admin and run the following commands:
    - set PATH=C:\OSGeo4W\apps\Qt5\bin;C:\OSGeo4W\bin;C:\OSGeo4W\apps\qgis-ltr\bin;%PATH%
    - set QT_PLUGIN_PATH=C:\OSGeo4W\apps\Qt5\plugins
    - set PYTHONPATH=C:\OSGeo4W\apps\qgis-ltr
- clone the Roam repository and cd into it: https://github.com/roam-qgis/Roam
- run the setups:
    - scripts\setenv.bat (this have been updated in the fork)
    - scripts\setupdev.bat
- you may need to update the requirements.txt file this is what I had:
        mock==3.0.5
        nose==1.3.7
        pytest==5.0.1
        pywin32
        pyaml==19.4.1
        raven==6.10.0
        markdown==3.3.7
        pytest-cov==2.7.1
        pillow
        sentry-sdk==0.11.2
- the path for gdal is out of date in the repo so you ahve to patch it and change it from:
    - import gdal
    to:
    - from osgeo import gdal
- in the config.py replace `settings = yaml.safe_load(f)` with `settings = yaml.safe_load(f.read())`
- structs.py replace the collection import to this:
    from collections import OrderedDict
    from collections.abc import MutableMapping
- from the Roam dir run:
    - for %f in (src\roam\ui\*.ui) do python -m PyQt5.uic.pyuic "%f" -o "%~dpf%~nf.py"
    - for %f in (src\roam\editorwidgets\uifiles\*.ui) do python -m PyQt5.uic.pyuic "%f" -o "%~dpf%~nf.py"
    - for %f in (src\configmanager\ui\*.ui) do python -m PyQt5.uic.pyuic "%f" -o "%~dpf%~nf.py"
    - for %f in (src\configmanager\ui\nodewidgets\*.ui) do python -m PyQt5.uic.pyuic "%f" -o "%~dpf%~nf.py"
    - for %f in (src\configmanager\editorwidgets\uifiles\*.ui) do python -m PyQt5.uic.pyuic "%f" -o "%~dpf%~nf.py"
- now generate the resources_rc:
    python -m PyQt5.pyrcc_main src\roam\resources.qrc -o src\roam\resources_rc.py
    cd /d D:\Development\Roam\src\configmanager\resources
    python -m PyQt5.pyrcc_main resources.qrc -o resources_rc.py
- there will be references to qgis._core and qgis._gui in the code you need to change them to qgis.core and qgis.gui respectively
    - run this to find all the files with this: findstr /S /N /I "qgis._" src\*.py src\*\*.py
    - the fork will have fixed these already


set PATH=C:\OSGeo4W\apps\Qt5\bin;C:\OSGeo4W\bin;C:\OSGeo4W\apps\qgis-ltr\bin;%PATH%
set QT_PLUGIN_PATH=C:\OSGeo4W\apps\Qt5\plugins
set PYTHONPATH=C:\OSGeo4W\apps\qgis-ltr
