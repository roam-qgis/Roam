import pytest

from roam import updater


def test_check_version_matches_higher_version():
    assert not updater.checkversion(toversion="1", fromversion="1")
    assert not updater.checkversion(toversion="0", fromversion="1")
    assert updater.checkversion(toversion="2", fromversion="1")


def test_can_extract_projectinfo_from_config():
    html = """
    projects:
      Test_Project:
        version: 1
        title: Test title
        name: Test_Project
        description: Example dataset
      Test_Project 2:
        version: 1
        title: Test title
        name: Test_Project_2
        description: Example dataset
    """
    versions = updater.parse_serverprojects(html)
    assert "Test_Project" in versions
    assert 1 in versions["Test_Project"]
    data = versions["Test_Project"][1]
    assert data['path'] == 'Test_Project.zip'
    assert data['title'] == 'Test title'
    assert data['name'] == 'Test_Project'
    assert data['version'] == 1
    assert "Test_Project 2" in versions


def test_get_project_info_returns_max_version_info():
    name = "test"
    v1 = dict(version="1")
    v2 = dict(version="2")
    projects = {name: {}}
    projects[name]['1'] = v1
    projects[name]['2'] = v2
    got = updater.get_project_info(name, projects)
    assert got['version'] == "2"

