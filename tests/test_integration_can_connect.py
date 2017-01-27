import warnings


def test_get_version(ui):
    with warnings.catch_warnings(record=True) as w:
        assert 'version' in ui.get("/api/v1/version").json()
    ui._requestsession.close()


def test_get_version_without_credentials(ui):
    assert 'Credentials' in str(ui)
    ui._authprovider = None
    assert 'Credentials' not in str(ui)

    with warnings.catch_warnings(record=True) as w:
        assert 'version' in ui.get("/api/v1/version").json()
    ui._requestsession.close()
