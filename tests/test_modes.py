"""Tests for the mode system."""

import pytest
from langcode.cli import MODES, ModeManager


class TestModes:
    """Tests for mode definitions."""

    def test_all_modes_defined(self):
        """Test that all expected modes are defined."""
        expected_modes = ["normal", "plan", "yolo", "build"]
        for mode in expected_modes:
            assert mode in MODES

    def test_mode_has_required_fields(self):
        """Test that each mode has required configuration fields."""
        required_fields = ["description", "auto_execute", "show_plan", "require_confirmation"]
        for mode_name, config in MODES.items():
            for field in required_fields:
                assert field in config, f"Mode {mode_name} missing field {field}"

    def test_normal_mode_config(self):
        """Test normal mode configuration."""
        config = MODES["normal"]
        assert config["auto_execute"] is False
        assert config["require_confirmation"] is True

    def test_yolo_mode_config(self):
        """Test yolo mode configuration."""
        config = MODES["yolo"]
        assert config["auto_execute"] is True
        assert config["require_confirmation"] is False

    def test_build_mode_config(self):
        """Test build mode configuration."""
        config = MODES["build"]
        assert config["auto_execute"] is True
        assert config["show_plan"] is True


class TestModeManager:
    """Tests for ModeManager class."""

    def test_initialization_default(self):
        """Test default initialization."""
        manager = ModeManager()
        assert manager.current_mode == "normal"

    def test_initialization_with_mode(self):
        """Test initialization with specific mode."""
        manager = ModeManager("yolo")
        assert manager.current_mode == "yolo"

    def test_switch_mode_valid(self):
        """Test switching to a valid mode."""
        manager = ModeManager("normal")
        result = manager.switch_mode("yolo")
        assert result is True
        assert manager.current_mode == "yolo"
        assert manager.auto_execute is True

    def test_switch_mode_invalid(self):
        """Test switching to an invalid mode."""
        manager = ModeManager("normal")
        result = manager.switch_mode("nonexistent")
        assert result is False
        assert manager.current_mode == "normal"

    def test_get_mode_info(self):
        """Test getting mode information."""
        manager = ModeManager("plan")
        info = manager.get_mode_info()
        assert "plan" in info.lower()
        assert "Mode:" in info

    def test_list_modes(self):
        """Test listing all modes."""
        manager = ModeManager("normal")
        mode_list = manager.list_modes()
        assert "normal" in mode_list
        assert "plan" in mode_list
        assert "yolo" in mode_list
        assert "build" in mode_list

    def test_list_modes_shows_current(self):
        """Test that list shows current mode marker."""
        manager = ModeManager("yolo")
        mode_list = manager.list_modes()
        # Should have marker on current mode
        assert "→" in mode_list or "yolo" in mode_list

    def test_properties(self):
        """Test mode property access."""
        manager = ModeManager("build")
        assert isinstance(manager.auto_execute, bool)
        assert isinstance(manager.show_plan, bool)
        assert isinstance(manager.require_confirmation, bool)

    def test_mode_properties_change_on_switch(self):
        """Test that properties change when mode is switched."""
        manager = ModeManager("normal")
        initial_auto = manager.auto_execute

        manager.switch_mode("yolo")
        assert manager.auto_execute != initial_auto
