import glob
import os
import shutil
import sys
from distutils.command.build import build
from distutils.command.clean import clean
from sys import platform

from setuptools import find_packages
from ext_libs.cx_Freeze import setup, Executable

from scripts.fabricate import run

curpath = os.path.dirname(os.path.realpath(__file__))

# You are not meant to do this but we don't install using
# setup.py so no big deal.
sys.path.append(os.path.join(curpath, 'src'))

import roam

try:
    osgeopath = os.environ['OSGEO4W_ROOT']
except KeyError:
    osgeopath = r'C:\OSGeo4W'

try:
    qgisname = os.environ['QGISNAME']
except KeyError:
    qgisname = 'qgis'

osgeobin = os.path.join(osgeopath, 'bin')
pythonroot = os.path.join(osgeopath, 'apps', "Python37")
qgisroot = os.path.join(osgeopath, "apps", qgisname)
qgisbin = os.path.join(qgisroot, "bin")
qtbin = os.path.join(osgeopath, "apps", "qt5", "bin")
qtplugins = os.path.join(osgeopath, "apps", "qt5", "plugins")

qtimageforms = os.path.join(osgeopath, r'apps\qt5\plugins\imageformats\*')
qtsqldrivers = os.path.join(osgeopath, r'apps\qt5\plugins\sqldrivers\*')
qgisresources = os.path.join(osgeopath, "apps", qgisname, "resources")
svgs = os.path.join(osgeopath, "apps", qgisname, "svg")
qgispluginpath = os.path.join(osgeopath, "apps", qgisname, "plugins", "*provider.dll")
gdalsharepath = os.path.join(osgeopath, 'share', 'gdal')
projsharepath = os.path.join(osgeopath, 'share', 'proj')

appsrcopyFilesath = os.path.join(curpath, "src", 'roam')
configmangerpath = os.path.join(curpath, "src", 'configmanager')

sys.path.append(osgeobin)
sys.path.append(qgisbin)
sys.path.append(qtbin)

qtplugin_list = [
    # "bearer",
    # "canbus",
    "crypto",
    # "gamepads",
    "generic",
    # "geometryloaders",
    # "geoservices",
    "iconengines",
    "imageformats",
    "mediaservice",
    "platforminputcontexts",
    "platforms",
    # "platformthemes",
    # "playlistformats",
    "position",
    # "printsupport",
    # "qmltooling",
    # "renderplugins",
    # "scenegraph",
    # "sceneparsers",
    # "sensorgestures",
    # "sensors",
    "sqldrivers",
    "styles",
    # "texttospeech",
]


def getfiles(folder, outpath, includebase=True):
    """
    Walks a given folder and converts all paths to outpath root.
    """

    def filecollection(files):
        collection = []
        for f in files:
            filename = os.path.join(path, f)
            collection.append(filename)

        return newpath, collection

    for path, dirs, files in os.walk(folder):
        if not files: continue

        if includebase:
            newpath = r'{}\{}'.format(outpath, os.path.basename(path))
        else:
            newpath = r'{}'.format(outpath)

        newpath, collection = filecollection(files)
        yield newpath, collection

        for dir in dirs:
            for path, collection in getfiles(os.path.join(path, dir), newpath):
                yield (path, collection)


def get_data_files():
    def format_paths(paths, new_folder="lib"):
        newpaths = []
        for path in paths:
            libpath = os.path.join(new_folder, os.path.basename(path))
            newpaths.append((path, libpath))
        return newpaths

    files = [
        (r"src\roam.config", "roam.config")
    ]

    # only copy the proj.db because that is all we need at the moment
    files += format_paths(glob.glob(os.path.join(projsharepath, "proj.db")), new_folder=r"lib\proj")

    files += format_paths(glob.glob(os.path.join(qgisbin, "*.dll")))
    files += format_paths(glob.glob(os.path.join(qgisroot, "plugins", "*.dll")), new_folder=r"lib\qgis\plugins")
    files += format_paths(glob.glob(os.path.join(qgisresources, "*.db")), new_folder=r"lib\qgis\resources")
    files += format_paths(glob.glob(os.path.join(qtbin, "*.dll")))
    files += format_paths(glob.glob(qtsqldrivers), new_folder="sqldrivers")

    utils = ['ogr2ogr.exe', 'ogrinfo.exe', 'gdalinfo.exe', 'NCSEcw.dll', "spatialite.dll",
             os.path.join('gdalplugins', 'gdal_ECW_JP2ECW.dll')]
    extrafiles = [os.path.join(osgeobin, path) for path in utils]
    files += format_paths(extrafiles)
    files += format_paths(glob.glob(os.path.join("lib", "*.dll")), new_folder="lib\qgis")

    files.append((os.path.join(pythonroot, "python3.dll"), "python3.dll"))
    files.append((r"src\plugins", "plugins"))
    files.append((r"src\roam\templates", r"lib\roam\templates"))
    files.append((r"src\configmanager\templates", r"lib\configmanager\templates"))
    files.append((svgs, r"lib\qgis\svg"))

    for qtplugin in qtplugin_list:
        pluginpath = os.path.join(qtplugins, qtplugin)
        files.append((pluginpath, r"lib\qtplugins\{}".format(qtplugin)))

    files.append((gdalsharepath, "lib\gdal"))

    versiontext = os.path.join(r"src\roam", "version.txt")

    with open(versiontext, 'w') as f:
        f.write(roam.__version__)

    files.append((versiontext, r"lib\roam\version.txt"))
    print("Including extra files:")
    for file, finalpath in sorted(files):
        print(f"\t - {file} -> {finalpath}")

    return files


def buildqtfiles():
    def _hashcheck(file):
        import hashlib
        hasher = hashlib.md5()
        with open(file, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        hash = hasher.hexdigest()
        filehash = hashes.get(file, "")
        hashes[file] = hash
        if hash != filehash:
            print("Hash changed for: {0}, Got {2} wanted {1}".format(file, hash, filehash))
            return False
        else:
            return True

    pyuic5 = 'pyuic5'
    pyrcc5 = 'pyrcc5'
    if platform == 'win32':
        pyuic5 += '.bat'
        pyrcc5 += '.bat'

    import json
    hashes = {}
    try:
        with open(".roambuild") as f:
            hashes = json.load(f)
    except Exception:
        hashes = {}

    HASHFILES = [".ui", ".ts"]
    for folder in [appsrcopyFilesath, configmangerpath]:
        for root, dirs, files in os.walk(folder):
            for file in files:
                filepath = os.path.join(root, file)
                file, ext = os.path.splitext(filepath)

                if ext in HASHFILES and _hashcheck(filepath):
                    print(f"Skipping {file} - Hash match")
                    continue

                if ext == '.ui':
                    newfile = file + ".py"
                    run(pyuic5, '-o', newfile, filepath, shell=True)
                elif ext == '.qrc':
                    newfile = file + "_rc.py"
                    run(pyrcc5, '-o', newfile, filepath)
                elif ext == '.ts':
                    newfile = file + '.qm'
                    try:
                        if os.name is 'nt':
                            run('lrelease', filepath, '-qm', newfile)
                        else:
                            run('lrelease-qt5', filepath, '-qm', newfile)
                    except:
                        print("Missing lrelease - skipping")
                        continue

    with open(".roambuild", "w") as f:
        json.dump(hashes, f)


class roam_build(build):
    def get_sub_commands(self):
        return [
            "clean",
            "build_qt",
            "build",
            "build_package_cleanup"
        ]


class qtbuild(build):
    def run(self):
        buildqtfiles()
        build.run(self)


class package_final(build):
    def run(self):
        buildfolder = r".\build\exe.win-amd64-3.7"
        libfolder = os.path.join(buildfolder, "lib")
        print("Moving python37.dll")
        shutil.move(os.path.join(libfolder, "python37.dll"), os.path.join(buildfolder, "python37.dll"))
        print("Removing imageformats")
        shutil.rmtree(os.path.join(buildfolder, "imageformats"))
        print("Removing sqldrivers")
        shutil.rmtree(os.path.join(buildfolder, "sqldrivers"))
        print("Removing platforms")
        shutil.rmtree(os.path.join(buildfolder, "platforms"))
        print("Removing pyqt5.uic extras")
        shutil.rmtree(os.path.join(buildfolder, "PyQt5.uic.widget-plugins"))
        print("Removing mediaservice")
        shutil.rmtree(os.path.join(buildfolder, "mediaservice"))
        print("Create projects folder")
        os.mkdir(os.path.join(buildfolder, "projects"))


class roamclean(clean):
    def run(self):
        if os.environ.get("CLEAN", "YES").lower() == "no":
            print("Skipping clean due to CLEAN == NO")
            return
        print("Removing .dist")
        if os.path.exists("dist"):
            shutil.rmtree("dist")
        if os.path.exists("build"):
            shutil.rmtree("build")
        clean.run(self)


icon = r'src\roam\resources\branding\icon.ico'
configicon = r'src\roam\resources\branding\config.ico'

roam_exe = Executable(script=r'src\roam\__main__.py',
                      icon=icon,
                      targetName="Roam",
                      base="Win32GUI")

configmanager_exe = Executable(script=r'src\configmanager\__main__.py',
                               icon=configicon,
                               targetName="Config Manager",
                               base="Win32GUI")

excludes = ["matplotlib", "scipy", "numpy", "disutils", "PIL"]
packages = find_packages("./src")

include_files = get_data_files()

package_details = dict(
    name='roam',
    version=roam.__version__,
    packages=find_packages('./src'),
    package_dir={'': 'src'},
    url='',
    license='GPL',
    author='Nathan Woodrow',
    author_email='',
    description='',
    # data_files=get_data_files(),
    cmdclass={
        'build_qt': qtbuild,
        'clean': roamclean,
        'build_roam': roam_build,
        'build_package_cleanup': package_final
    },
    options={
        "build_exe": {
            'packages': packages,
            'includes': ["qgis", "PyQt5", "sip",
                         "sentry_sdk.integrations.logging",
                         "sentry_sdk.integrations.stdlib",
                         "sentry_sdk.integrations.excepthook",
                         "sentry_sdk.integrations.dedupe",
                         "sentry_sdk.integrations.atexit",
                         "sentry_sdk.integrations.modules",
                         "sentry_sdk.integrations.argv",
                         "sentry_sdk.integrations.threading",
                         ],
            'include_files': include_files,
            'excludes': excludes,
            'include_msvcr': True,
        }},
    executables=[roam_exe, configmanager_exe]
)

setup(**package_details)
