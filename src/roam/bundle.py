import yaml
import os
import zipfile


def bundle_project(project, outpath, options):
    root = project.folder
    basefolder = project.basefolder
    filename = "{}.zip".format(basefolder)
    filename = os.path.join(outpath, filename)
    zipper(root, basefolder, filename, options)
    update_project_details(project, outpath)


def zipper(dir, projectname, zip_file, options):
    with zipfile.ZipFile(zip_file, 'w', compression=zipfile.ZIP_DEFLATED) as zip:
        root_len = len(os.path.abspath(dir))
        skipfolders = options.get("skip", [])
        for root, dirs, files in os.walk(dir):
            if os.path.basename(root) in skipfolders:
                continue

            archive_root = os.path.abspath(root)[root_len + 1:]
            for f in files:
                fullpath = os.path.join(root, f)
                archive_name = os.path.join(projectname, archive_root, f)
                zip.write(fullpath, archive_name, zipfile.ZIP_DEFLATED)
    return zip_file


def update_project_details(project, outpath):
    configpath = os.path.join(outpath, "roam.txt")
    if not os.path.exists(configpath):
        open(configpath, "a").close()

    with open(configpath, 'r+') as f:
        config = yaml.load(f)
        if not config:
            config = {}
        projectsnode = config.setdefault("projects", {})
        projectsnode[project.basefolder] = {"version": project.version,
                                            "name": project.basefolder,
                                            "title": project.name,
                                            "description": project.description}

        config['projects'] = projectsnode
        f.seek(0)
        yaml.dump(data=config, stream=f, default_flow_style=False)
        f.truncate()


