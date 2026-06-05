"""Configuration module tests."""

from __future__ import annotations

from pathlib import Path

from src.config import AppEnvironment, Settings, get_settings, reset_settings_cache


def test_settings_defaults() -> None:
    reset_settings_cache()
    settings = Settings()
    assert settings.app_env == AppEnvironment.DEVELOPMENT
    assert settings.chunk_size == 500
    assert settings.chunk_overlap == 100
    assert settings.retrieval_top_k == 8


def test_settings_paths_are_path_objects() -> None:
    settings = Settings(data_dir="./data/custom")
    assert isinstance(settings.data_dir, Path)


def test_get_settings_is_cached() -> None:
    reset_settings_cache()
    assert get_settings() is get_settings()
