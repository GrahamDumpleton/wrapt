import sys
import threading
from importlib.metadata import EntryPoint
from unittest.mock import MagicMock, Mock, patch

import pytest

import wrapt
from wrapt.importer import _post_import_hooks, discover_post_import_hooks


class TestEntryPoints:

    def setup_method(self):
        """Clean up modules and hooks before each test"""
        # Clean up test modules
        for module_name in ["this", "test_target", "dummy_package"]:
            sys.modules.pop(module_name, None)
            _post_import_hooks.pop(module_name, None)

    def test_discover_post_import_hooks_python310_style(self):
        """Test entry point discovery using Python 3.10+ style entry_points()"""

        invoked = []

        def mock_hook(module):
            invoked.append(module.__name__)

        # Create mock entry point
        mock_entrypoint = Mock(spec=EntryPoint)
        mock_entrypoint.name = "this"
        mock_entrypoint.load.return_value = mock_hook

        # Mock the entry_points function for Python 3.10+ style
        with patch("importlib.metadata.entry_points") as mock_entry_points:
            mock_entry_points.return_value = [mock_entrypoint]

            # Test the discovery
            discover_post_import_hooks("wrapt_hooks")

            # Verify entry_points was called correctly
            mock_entry_points.assert_called_once_with(group="wrapt_hooks")
            mock_entrypoint.load.assert_called_once()

            # Test that the hook is registered and works
            import this

            assert len(invoked) == 1
            assert invoked[0] == "this"

    def test_discover_post_import_hooks_python38_style(self):
        """Test entry point discovery using Python 3.8-3.9 style entry_points()"""

        invoked = []

        def mock_hook(module):
            invoked.append(f"old_style:{module.__name__}")

        # Create mock entry point
        mock_entrypoint = Mock(spec=EntryPoint)
        mock_entrypoint.name = "this"
        mock_entrypoint.load.return_value = mock_hook

        # Mock the entry_points function to raise TypeError first (3.8-3.9 style)
        with patch("importlib.metadata.entry_points") as mock_entry_points:
            # First call raises TypeError, second call returns dict
            mock_entry_points.side_effect = [
                TypeError("group parameter not supported"),
                {"wrapt_hooks": [mock_entrypoint]},
            ]

            # Test the discovery
            discover_post_import_hooks("wrapt_hooks")

            # Verify entry_points was called twice due to fallback
            assert mock_entry_points.call_count == 2
            mock_entrypoint.load.assert_called_once()

            # Test that the hook works
            import this

            assert len(invoked) == 1
            assert invoked[0] == "old_style:this"

    def test_multiple_entry_points_same_group(self):
        """Test multiple entry points in the same group"""

        invoked = []

        def hook1(module):
            invoked.append(f"hook1:{module.__name__}")

        def hook2(module):
            invoked.append(f"hook2:{module.__name__}")

        # Create multiple mock entry points
        mock_entrypoint1 = Mock(spec=EntryPoint)
        mock_entrypoint1.name = "this"
        mock_entrypoint1.load.return_value = hook1

        mock_entrypoint2 = Mock(spec=EntryPoint)
        mock_entrypoint2.name = "this"  # Same target module
        mock_entrypoint2.load.return_value = hook2

        with patch("importlib.metadata.entry_points") as mock_entry_points:
            mock_entry_points.return_value = [mock_entrypoint1, mock_entrypoint2]

            discover_post_import_hooks("multi_hooks")

            # Import target module
            import this

            # Both hooks should be called
            assert len(invoked) == 2
            assert "hook1:this" in invoked
            assert "hook2:this" in invoked

    def test_entry_point_for_already_imported_module(self):
        """Test entry point registration when target module is already imported"""

        invoked = []

        def hook_for_imported(module):
            invoked.append(f"already_imported:{module.__name__}")

        # Import module first
        import this

        # Now register hook via entry point
        mock_entrypoint = Mock(spec=EntryPoint)
        mock_entrypoint.name = "this"
        mock_entrypoint.load.return_value = hook_for_imported

        with patch("importlib.metadata.entry_points") as mock_entry_points:
            mock_entry_points.return_value = [mock_entrypoint]

            discover_post_import_hooks("post_import_hooks")

            # Hook should be called immediately since module already imported
            assert len(invoked) == 1
            assert invoked[0] == "already_imported:this"

    def test_entry_point_hook_exception_handling(self):
        """Test that exceptions in entry point hooks are properly propagated"""

        def failing_hook(module):
            raise ValueError("Test exception from hook")

        mock_entrypoint = Mock(spec=EntryPoint)
        mock_entrypoint.name = "this"
        mock_entrypoint.load.return_value = failing_hook

        with patch("importlib.metadata.entry_points") as mock_entry_points:
            mock_entry_points.return_value = [mock_entrypoint]

            discover_post_import_hooks("failing_hooks")

            # Importing should raise the exception from the hook
            with pytest.raises(ValueError, match="Test exception from hook"):
                import this

    def test_entry_point_with_different_target_modules(self):
        """Test entry points targeting different modules"""

        invoked = []

        def hook_for_this(module):
            invoked.append(f"this_hook:{module.__name__}")

        def hook_for_sys(module):
            invoked.append(f"sys_hook:{module.__name__}")

        mock_entrypoint1 = Mock(spec=EntryPoint)
        mock_entrypoint1.name = "this"
        mock_entrypoint1.load.return_value = hook_for_this

        mock_entrypoint2 = Mock(spec=EntryPoint)
        mock_entrypoint2.name = "sys"  # sys is already imported
        mock_entrypoint2.load.return_value = hook_for_sys

        with patch("importlib.metadata.entry_points") as mock_entry_points:
            mock_entry_points.return_value = [mock_entrypoint1, mock_entrypoint2]

            discover_post_import_hooks("multi_target_hooks")

            # sys hook should fire immediately (already imported)
            # this hook should fire when we import this
            import this

            assert len(invoked) == 2
            assert "sys_hook:sys" in invoked
            assert "this_hook:this" in invoked

    def test_empty_entry_points_group(self):
        """Test discovery when no entry points exist for the group"""

        with patch("importlib.metadata.entry_points") as mock_entry_points:
            mock_entry_points.return_value = []

            # Should not raise any exceptions
            discover_post_import_hooks("nonexistent_group")

            mock_entry_points.assert_called_once_with(group="nonexistent_group")

    def test_entry_point_load_failure(self):
        """Test handling of entry point load failures"""

        mock_entrypoint = Mock(spec=EntryPoint)
        mock_entrypoint.name = "this"
        mock_entrypoint.load.side_effect = ImportError("Cannot load entry point")

        with patch("importlib.metadata.entry_points") as mock_entry_points:
            mock_entry_points.return_value = [mock_entrypoint]

            # Should propagate the ImportError
            with pytest.raises(ImportError, match="Cannot load entry point"):
                discover_post_import_hooks("failing_load_hooks")

    def test_threading_safety_with_entry_points(self):
        """Test that entry point discovery is thread-safe"""

        invoked = []

        def thread_safe_hook(module):
            invoked.append(f"thread_safe:{module.__name__}")

        mock_entrypoint = Mock(spec=EntryPoint)
        mock_entrypoint.name = "this"
        mock_entrypoint.load.return_value = thread_safe_hook

        def worker():
            with patch("importlib.metadata.entry_points") as mock_entry_points:
                mock_entry_points.return_value = [mock_entrypoint]
                discover_post_import_hooks("thread_hooks")

        # Run discovery in multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(timeout=10)
            assert not thread.is_alive()

        # Import target module
        import this

        # Should have multiple hook registrations
        assert len(invoked) >= 1  # At least one should succeed
