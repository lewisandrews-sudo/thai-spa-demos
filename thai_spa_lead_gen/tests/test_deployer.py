import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from deployer import build_site_name, deploy_site, DeployResult


def test_build_site_name_starter():
    assert build_site_name("lotus-spa-wellness", is_premium=False) == "lotus-spa-wellness-starter"


def test_build_site_name_premium():
    assert build_site_name("lotus-spa-wellness", is_premium=True) == "lotus-spa-wellness-premium"


def test_deploy_site_returns_url_on_success(mocker, tmp_path):
    # Create a minimal site dir
    site_dir = tmp_path / "starter"
    site_dir.mkdir()
    (site_dir / "index.html").write_text("<html>test</html>")

    mock_run = mocker.patch("deployer.subprocess.run")
    mock_run.return_value = mocker.MagicMock(
        returncode=0,
        stdout='{"deploy_url": "https://lotus-spa-wellness-starter.netlify.app"}\n',
        stderr="",
    )
    mocker.patch("deployer.NETLIFY_TOKEN", "test-token")

    result = deploy_site(str(site_dir), "lotus-spa-wellness", is_premium=False)
    assert isinstance(result, DeployResult)
    assert result.url == "https://lotus-spa-wellness-starter.netlify.app"
    assert result.success is True


def test_deploy_site_returns_failure_on_error(mocker, tmp_path):
    site_dir = tmp_path / "starter"
    site_dir.mkdir()
    (site_dir / "index.html").write_text("<html>test</html>")

    mock_run = mocker.patch("deployer.subprocess.run")
    mock_run.return_value = mocker.MagicMock(returncode=1, stdout="", stderr="Auth error")
    mocker.patch("deployer.NETLIFY_TOKEN", "test-token")

    result = deploy_site(str(site_dir), "lotus-spa-wellness", is_premium=False)
    assert result.success is False
    assert result.url is None
