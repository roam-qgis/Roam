from setuptools import find_packages
from distutils.core import setup
from distutils.command.build import build
from scripts.fabricate import run

import os

if os.name is 'nt':
    try:
        import py2exe
    except ImportError:
        print "Can't import py2exe. Do you have it installed."

import glob

import sys
import shutil
import sys
from sys import platform

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
qtimageforms = os.path.join(osgeopath, r'apps\qt4\plugins\imageformats\*')
qtsqldrivers = os.path.join(osgeopath, r'apps\qt4\plugins\sqldrivers\*')
qgisresources = os.path.join(osgeopath, "apps", qgisname, "resources")
svgs = os.path.join(osgeopath, "apps", qgisname, "svg")
qgispluginpath = os.path.join(osgeopath, "apps", qgisname, "plugins", "*provider.dll")
gdalsharepath = os.path.join(osgeopath, 'share', 'gdal')

sdkpath = os.path.join(curpath, "sdk")
appsrcopyFilesath = os.path.join(curpath, "src", 'roam')
srceditorwidgets = os.path.join(curpath, "src", 'roam', 'editorwidgets')
projectinstallerpath = os.path.join(curpath, "src", 'project_installer')
configmangerpath = os.path.join(curpath, "src", 'configmanager')


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
    utils = ['ogr2ogr.exe', 'ogrinfo.exe', 'gdalinfo.exe', 'NCSEcw.dll',
             os.path.join('gdalplugins', 'gdal_ECW_JP2ECW.dll')]

    extrafiles = [os.path.join(osgeobin, path) for path in utils]

    i18nfiles = os.path.join(appsrcopyFilesath, 'i18n\*.qm')

    datafiles = [(".", [r'src\roam.config']),
                 # We have to copy the imageformat drivers to the root folder.
                 (r'imageformats', glob.glob(qtimageforms)),
                 (r'libs\qgis\plugins', glob.glob(qgispluginpath)),
                 (r'libs\qgis\resources', [os.path.join(qgisresources, 'qgis.db'),
                                           os.path.join(qgisresources, 'srs.db')]),
                 (r'libs', extrafiles),
                 (r'sqldrivers', glob.glob(qtsqldrivers)),
                 (r'libs\roam\i18n', glob.glob(i18nfiles)),
                 (r'libs\roam\editorwidgets', glob.glob(os.path.join(srceditorwidgets, "*.pil"))),
                 (r'libs\roam\editorwidgets', glob.glob(os.path.join(srceditorwidgets, "*.pyd"))),
                 (r'libs\roam\editorwidgets', glob.glob(os.path.join(srceditorwidgets, "*.png")))]

    extapaths = [
        (r"src\roam\templates", r"libs\roam"),
        (svgs, r'libs\qgis\svg'),
        (r'src\configmanager\templates', r'libs\configmanager\templates'),
        (r'src\plugins', r'plugins'),
        (gdalsharepath, r'libs')
    ]

    for source, dest in extapaths:
        files = getfiles(source, dest)
        datafiles.append(files)

    versiontext = os.path.join(appsrcopyFilesath, "version.txt")

    with open(versiontext, 'w') as f:
        f.write(roam.__version__)

    datafiles.append((r'libs\roam', [versiontext]))

    return datafiles


icon = r'src\roam\resources\branding\icon.ico'
configicon = r'src\roam\resources\branding\config.ico'

roam_target = dict(
    script=r'src\roam\__main__.py',
    dest_base='Roam',
    icon_resources=[(1, icon)])

tests_target = dict(
    script=r'tests\__main__.py',
    dest_base='Roam_tests',
    icon_resources=[(1, icon)])

projectupdater_target = dict(
    script=r'src\project_installer\__main__.py',
    dest_base='Roam Project Updater',
    icon_resources=[(1, icon)])

configmanager_target = dict(
    script=r'src\configmanager\__main__.py',
    dest_base='Roam Config Manager',
    icon_resources=[(1, configicon)])


def buildqtfiles():
    pyuic4 = 'pyuic4'
    if platform == 'win32':
        pyuic4 += '.bat'
    for folder in [appsrcopyFilesath, projectinstallerpath, configmangerpath]:
        for root, dirs, files in os.walk(folder):
            for file in files:
                filepath = os.path.join(root, file)
                file, ext = os.path.splitext(filepath)
                if ext == '.ui':
                    newfile = file + ".py"
                    run(pyuic4, '-o', newfile, filepath, shell=True)
                elif ext == '.qrc':
                    newfile = file + "_rc.py"
                    run('pyrcc4', '-o', newfile, filepath)
                elif ext == '.ts':
                    newfile = file + '.qm'
                    try:
                        if os.name is 'nt':
                            run('lrelease', filepath, '-qm', newfile)
                        else:
                            run('lrelease-qt4', filepath, '-qm', newfile)
                    except:
                        print "Missing lrelease - skipping"
                        continue


class qtbuild(build):
    def run(self):
        buildqtfiles()
        build.run(self)


package_details = dict(
    name='roam',
    version=roam.__version__,
    packages=find_packages('./src'),
    package_dir={'': 'src', 'tests': 'tests'},
    url='',
    license='GPL',
    author='Digital Mapping Solutions',
    author_email='nathan.woodrow@mapsolutions.com.au',
    description='',
    data_files=get_data_files(),
    cmdclass={'build': qtbuild},
)

if os.name is 'nt':
    origIsSystemDLL = py2exe.build_exe.isSystemDLL

    def isSystemDLL(pathname):
        if os.path.basename(pathname).lower() in ("msvcp100.dll", "msvcr100.dll"):
            return 0
        return origIsSystemDLL(pathname)

    py2exe.build_exe.isSystemDLL = isSystemDLL
    package_details.update(
        options={'py2exe': {
            'dll_excludes': ['msvcr80.dll', 'msvcp80.dll',
                             'msvcr80d.dll', 'msvcp80d.dll',
                             'powrprof.dll', 'mswsock.dll',
                             'w9xpopen.exe', 'MSVCP90.dll'],
            'excludes': ['PyQt4.uic.port_v3'],
            'includes': ['PyQt4.QtNetwork', 'sip', 'PyQt4.QtSql', 'sqlite3', "Queue", 'PyQt4.Qsci'],
            'skip_archive': True,
        }},
        windows=[roam_target, configmanager_target],
        zipfile="libs\\"
    )

setup(**package_details)

