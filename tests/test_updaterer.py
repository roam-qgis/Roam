import pytest

from roam import updater


def test_check_version_matches_higher_version():
    assert not updater.checkversion(toversion="1", fromversion="1")
    assert not updater.checkversion(toversion="0", fromversion="1")
    assert updater.checkversion(toversion="2", fromversion="1")


def test_can_extract_projectinfo_from_html():
    html = """
    <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN"><html>
    <title>Directory listing for /projects/</title>
    <body>
    <h2>Directory listing for /projects/</h2>
    <hr>
    <ul>
    <li><a href="test-1.zip">test-1.zip</a>
    <li><a href="test-2.zip">test-2.zip</a>
    </ul>
    <hr>
    </body>
    </html>"""
    versions = updater.parse_serverprojects(html)
    print versions
    assert "test" in versions
    assert 1 in versions["test"]
    assert 2 in versions["test"]
    data = versions["test"][1]
    assert data['path'] == 'test-1.zip'
    assert data['name'] == 'test'
    assert data['version'] == 1


def test_get_project_info_returns_max_version_info():
    name = "test"
    v1 = dict(version="1")
    v2 = dict(version="2")
    projects = {name: {}}
    projects[name]['1'] = v1
    projects[name]['2'] = v2
    got = updater.get_project_info(name, projects)
    assert got['version'] == "2"


def test_parse_server_projects_returns_correct_data():
    content = "Test_File-1.zip"
    data = updater.parse_serverprojects(content)
    data = data['Test_File'][1]
    assert data['version'] == 1
    assert data['name'] == 'Test_File'
    assert data['path'] == 'Test_File-1.zip'
    # with dash
    content = "Test-File-1.zip"
    data = updater.parse_serverprojects(content)
    data = data['Test-File'][1]
    assert data['version'] == 1
    assert data['name'] == 'Test-File'
    assert data['path'] == 'Test-File-1.zip'
