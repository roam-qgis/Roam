import pytest

from roam import updater

def test_check_version_matches_higher_version():
    assert not updater.checkversion(toversion="1.0.0", fromversion="1.0.0")
    assert not updater.checkversion(toversion="0.1.0", fromversion="1.0.0")
    assert updater.checkversion(toversion="2.0.0", fromversion="1.0.0")


def test_can_extract_projectinfo_from_html():
    html = """
    <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN"><html>
    <title>Directory listing for /projects/</title>
    <body>
    <h2>Directory listing for /projects/</h2>
    <hr>
    <ul>
    <li><a href="test-1.1.0.zip">test-1.1.0.zip</a>
    <li><a href="test-2.2.6.zip">test-2.2.6.zip</a>
    </ul>
    <hr>
    </body>
    </html>"""
    versions = updater.parse_serverprojects(html)
    assert "test" in versions
    assert "1.1.0" in versions["test"]
    assert "2.2.6" in versions["test"]
    data = versions["test"]['1.1.0']
    assert data['path'] == 'test-1.1.0.zip'
    assert data['name'] == 'test'
    assert data['version'] == '1.1.0'

def test_get_project_info_returns_max_version_info():
    name = "test"
    v1 = dict(version="1.1.0")
    v2 = dict(version="2.0.0")
    projects = {name:{}}
    projects[name]['1.1.0'] = v1
    projects[name]['2.0.0'] = v2
    got = updater.get_project_info(name, projects)
    assert got['version'] == "2.0.0"
