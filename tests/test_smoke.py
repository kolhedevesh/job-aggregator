def test_app_import():
    # Smoke test: importing app should not execute the server
    import app

    assert hasattr(app, "main")
