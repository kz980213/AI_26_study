from app.config import get_settings


def test_get_settings_with_env(monkeypatch):
    monkeypatch.setenv("APP_NAME", "week1_app")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = get_settings()

    assert settings.app_name == "ai_app"
    assert settings.app_env == "dev"
    assert settings.log_level == "INFO"