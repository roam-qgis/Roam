import os
import zipfile


def bundle_project(project, outpath):
    root = project.folder
    basefolder = project.basefolder
    filename = "{}-{}.zip".format(basefolder, project.version)
    filename = os.path.join(outpath, filename)
    zipper(root, filename)


def zipper(dir, zip_file):
    with zipfile.ZipFile(zip_file, 'w', compression=zipfile.ZIP_DEFLATED) as zip:
        root_len = len(os.path.abspath(dir))
        for root, dirs, files in os.walk(dir):
            if os.path.basename(root).startswith("_"):
                continue

            archive_root = os.path.abspath(root)[root_len:]
            for f in files:
                fullpath = os.path.join(root, f)
                archive_name = os.path.join(archive_root, f)
                print archive_name
                zip.write(fullpath, archive_name, zipfile.ZIP_DEFLATED)
    return zip_file