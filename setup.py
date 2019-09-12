import glob
import os
import shutil
import sys
from distutils.command.build import build
from distutils.command.clean import clean
from sys import platform

from setuptools import find_packages
from cx_Freeze import setup, Executable

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

qtimageforms = os.path.join(osgeopath, r'apps\qt5\plugins\imageformats\*')
qtsqldrivers = os.path.join(osgeopath, r'apps\qt5\plugins\sqldrivers\*')
qgisresources = os.path.join(osgeopath, "apps", qgisname, "resources")
svgs = os.path.join(osgeopath, "apps", qgisname, "svg")
qgispluginpath = os.path.join(osgeopath, "apps", qgisname, "plugins", "*provider.dll")
gdalsharepath = os.path.join(osgeopath, 'share', 'gdal')

appsrcopyFilesath = os.path.join(curpath, "src", 'roam')
configmangerpath = os.path.join(curpath, "src", 'configmanager')

sys.path.append(osgeobin)
sys.path.append(qgisbin)
sys.path.append(qtbin)


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

    files += format_paths(glob.glob(os.path.join(qgisbin, "*.dll")))
    files += format_paths(glob.glob(os.path.join(qgisroot, "plugins", "*.dll")), new_folder=r"lib\qgis\plugins")
    files += format_paths(glob.glob(os.path.join(qgisresources, "*.db")), new_folder=r"lib\qgis\resources")
    files += format_paths(glob.glob(os.path.join(qtbin, "*.dll")))
    files += format_paths(glob.glob(os.path.join(qtbin, "*.dll")))
    files += format_paths(glob.glob(qtsqldrivers), new_folder="sqldrivers")

    utils = ['ogr2ogr.exe', 'ogrinfo.exe', 'gdalinfo.exe', 'NCSEcw.dll', "spatialite.dll",
             os.path.join('gdalplugins', 'gdal_ECW_JP2ECW.dll')]
    extrafiles = [os.path.join(osgeobin, path) for path in utils]
    files += format_paths(extrafiles)

    files.append((os.path.join(pythonroot, "python3.dll"), "python3.dll"))
    files.append((r"src\plugins", "plugins"))
    files.append((r"src\roam\templates", r"lib\roam\templates"))
    files.append((r"src\configmanager\templates", r"lib\configmanager\templates"))
    files.append((svgs, r"lib\qgis\svg"))
    files.append((gdalsharepath, "lib\gdal"))

    versiontext = os.path.join(appsrcopyFilesath, "version.txt")

    with open(versiontext, 'w') as f:
        f.write(roam.__version__)

    files.append((versiontext, r"lib\roam\version.txt"))

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

    HASHFILES = [".ui", ".qrc", ".ts"]
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


class qtbuild(build):
    def run(self):
        buildqtfiles()
        build.run(self)


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
# initScript=r"C:\Users\Nathan\dev\Roam\freeze_init.py")

configmanager_exe = Executable(script=r'src\configmanager\__main__.py',
                               icon=configicon,
                               targetName="Config Manager",
                               base="Win32GUI")

excludes = ["mpl-data", "PyQt5.uic.widget-plugins"]
packages = find_packages("./src")
print(sys.path)

# for file in get_data_files():
#     print(file)
include_files = get_data_files()
# include_files = [file for path, file in get_data_files()]
# for file in include_files:
#     print(file)

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
    cmdclass={'build_qt': qtbuild,
              'clean': roamclean},
    options={
        "build_exe": {
            'packages': packages,
            'includes': ["qgis", "PyQt5", "sip"],
            'include_files': include_files,
            'excludes': excludes,
            'include_msvcr': True,
        }},
    executables=[roam_exe, configmanager_exe]
)

dll_excludes = ["MSVFW32.dll",
                "AVIFIL32.dll",
                "AVICAP32.dll",
                "ADVAPI32.dll",
                "CRYPT32.dll",
                "WLDAP32.dll",
                "SECUR32.dll",
                'msvcr80.dll', 'msvcp80.dll',
                'msvcr80d.dll', 'msvcp80d.dll',
                'powrprof.dll', 'mswsock.dll',
                'w9xpopen.exe', 'MSVCP90.dll',
                'libiomp5md.dll']

# if os.name is 'nt':
#     origIsSystemDLL = py2exe.build_exe.isSystemDLL
#
#     def isSystemDLL(pathname):
#         if "api-ms-win-" in pathname:
#             print(" -> Skip: {0}".format(pathname))
#             return True
#
#         if os.path.basename(pathname).lower() in ("msvcp100.dll", "msvcr100.dll"):
#             return False
#
#         return origIsSystemDLL(pathname)
#
#     py2exe.build_exe.isSystemDLL = isSystemDLL
#     package_details.update(
#         options={'py2exe': {
#             'dll_excludes': dll_excludes,
#             'excludes': ['qgis.PyQt.uic.port_v3'],
#             'includes': ['qgis.PyQt.QtNetwork', 'sip', 'qgis.PyQt.QtSql', 'sqlite3', "Queue", 'qgis.PyQt.Qsci'],
#             'skip_archive': True,
#         }},
#         windows=[roam_target, configmanager_target],
#         zipfile="libs\\"
#     )

setup(**package_details)
