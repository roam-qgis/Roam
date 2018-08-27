import yaml
import os
import zipfile

from configmanager.config import Config


def get_config(outpath):
    configpath = os.path.join(outpath, "roam.txt")
    defaults = {}
    config = Config.from_file(configpath, defaults)
    return config


def bundle_project(project, outpath, options, as_install=False):
    _startoptions = options
    root = project.folder
    basefolder = project.basefolder
    if as_install:
        dataoptions = {"skip": ["index.db"]}
        options = _startoptions.copy()
        options.update(dataoptions)
        filename = "{}-Install.zip".format(basefolder)
    else:
        dataoptions = {"skip": ["_data", "index.db"]}
        options = _startoptions.copy()
        options.update(dataoptions)
        filename = "{}.zip".format(basefolder)

    print filename
    filename = os.path.join(outpath, filename)
    zipper(root, basefolder, filename, options)
    update_project_details(project, outpath)

    # We also create the update package at the same time as the install package
    if as_install:
        bundle_project(project, outpath, _startoptions, as_install=False)


def zipper(dir, projectname, zip_file, options):
    with zipfile.ZipFile(zip_file, 'w', compression=zipfile.ZIP_DEFLATED) as zip:
        root_len = len(os.path.abspath(dir))
        skipfolders = options.get("skip", [])
        for root, dirs, files in os.walk(dir):
            if os.path.basename(root) in skipfolders:
                continue

            archive_root = os.path.abspath(root)[root_len + 1:]
            for f in files:
                if f in skipfolders:
                    continue
                fullpath = os.path.join(root, f)
                archive_name = os.path.join(projectname, archive_root, f)
                zip.write(fullpath, archive_name, zipfile.ZIP_DEFLATED)
    return zip_file


def update_project_details(project, outpath):
    config = get_config(outpath)
    projectsnode = config.get("projects", {})
    projectsnode[project.id] = {"version": project.version,
                                "name": project.basefolder,
                                "title": project.name,
                                "description": project.description}

    config['projects'] = projectsnode
    config.save()
