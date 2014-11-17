"""
Roam search plugin

Install into roam install\plugins\search_plugin

Add the following config to project.config

plugins:
 - search_pluing

search:
    layer2:
        columns:
            - col1
            - col2
    layer1:
        columns:
            - col1

where layer1 and layer2 are layer names found in the project.

Example:

search:
    Pits:
        columns:
            - assetno
    Pipes:
        columns:
            - assetno

"""
import search


def pages():
    """
    Return the pages exposed for this plugin to Roam
    :return: list of pages for Roam to show
    """
    return [search.SearchPlugin]

