import os
import zipfile


def bundle_project(project, outpath):
    root = project.folder
    basefolder = project.basefolder
    filename = "{}-{}.zip".format(basefolder, project.version)
    filename = os.path.join(outpath, filename)
    with zipfile.ZipFile(filename, "w") as zip:
        for root, dir, files in os.walk(root):
            name = os.path.basename(root)
            for file in files:
                newpath = os.path.join(basefolder, name, file)
                print newpath
                zip.write(file, newpath)
    print project, outpath
