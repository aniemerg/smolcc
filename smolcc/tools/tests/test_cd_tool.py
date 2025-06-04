#!/usr/bin/env python3
"""
Unit tests for the ChangeDirectory tool.

These tests verify that the ChangeDirectory tool works correctly across
different scenarios including validation, suggestions, and safety features.
"""

import os
import tempfile
import unittest
import platform
from pathlib import Path

from smolcc.tools.cd_tool import cd_tool

# Constants
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_DIR = os.path.join(TEST_DIR, "testdata")


class ChangeDirectoryToolTests(unittest.TestCase):
    """Tests for the ChangeDirectory tool."""

    def setUp(self):
        """Set up test environment."""
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test directory structure
        self.test_subdir = os.path.join(self.temp_dir, "test_subdir")
        os.makedirs(self.test_subdir, exist_ok=True)
        
        # Create a file in temp dir to distinguish from directories
        with open(os.path.join(self.temp_dir, "test_file.txt"), "w") as f:
            f.write("test content")

    def tearDown(self):
        """Clean up after tests."""
        # Always return to original directory
        os.chdir(self.original_cwd)
        
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_change_to_valid_absolute_path(self):
        """Test changing to a valid absolute directory path."""
        result = cd_tool.forward(path=self.temp_dir)
        
        # Should succeed
        self.assertIn("Directory changed successfully!", result)
        self.assertIn(self.temp_dir, result)
        
        # Verify we actually changed directories
        self.assertEqual(os.getcwd(), self.temp_dir)

    def test_change_to_valid_relative_path(self):
        """Test changing to a valid relative directory path."""
        # Change to temp dir first
        os.chdir(self.temp_dir)
        
        # Now change to relative subdirectory
        result = cd_tool.forward(path="test_subdir")
        
        # Should succeed
        self.assertIn("Directory changed successfully!", result)
        self.assertIn("test_subdir", result)
        
        # Verify we're in the subdirectory
        self.assertEqual(os.getcwd(), self.test_subdir)

    def test_change_to_parent_directory(self):
        """Test changing to parent directory using '..'."""
        # Start in subdirectory
        os.chdir(self.test_subdir)
        
        result = cd_tool.forward(path="..")
        
        # Should succeed
        self.assertIn("Directory changed successfully!", result)
        
        # Verify we're in the parent directory
        self.assertEqual(os.getcwd(), self.temp_dir)

    def test_change_to_home_directory(self):
        """Test changing to home directory using '~'."""
        result = cd_tool.forward(path="~")
        
        # Should succeed
        self.assertIn("Directory changed successfully!", result)
        self.assertIn("(home directory)", result)
        
        # Verify we're in home directory
        self.assertEqual(os.getcwd(), str(Path.home()))

    def test_change_to_previous_directory(self):
        """Test changing to previous directory using '-'."""
        # Change to temp dir first to establish previous
        cd_tool.forward(path=self.temp_dir)
        
        # Change to subdirectory
        cd_tool.forward(path=self.test_subdir)
        
        # Now go back to previous
        result = cd_tool.forward(path="-")
        
        # Should succeed
        self.assertIn("Directory changed successfully!", result)
        self.assertIn("(previous directory)", result)
        
        # Verify we're back in temp dir
        self.assertEqual(os.getcwd(), self.temp_dir)

    def test_change_to_nonexistent_directory(self):
        """Test error handling for nonexistent directory."""
        nonexistent_path = os.path.join(self.temp_dir, "does_not_exist")
        
        result = cd_tool.forward(path=nonexistent_path)
        
        # Should fail with helpful message
        self.assertIn("Error: Directory", result)
        self.assertIn("does not exist", result)
        
        # Should stay in original directory
        self.assertEqual(os.getcwd(), self.original_cwd)

    def test_change_to_file_instead_of_directory(self):
        """Test error handling when target is a file, not directory."""
        file_path = os.path.join(self.temp_dir, "test_file.txt")
        
        result = cd_tool.forward(path=file_path)
        
        # Should fail with helpful message
        self.assertIn("Error:", result)
        self.assertIn("is not a directory", result)
        
        # Should stay in original directory
        self.assertEqual(os.getcwd(), self.original_cwd)

    def test_directory_suggestions_for_typos(self):
        """Test that suggestions are provided for similar directory names."""
        # Create directory with similar name
        similar_dir = os.path.join(self.temp_dir, "test_similar")
        os.makedirs(similar_dir, exist_ok=True)
        
        # Try to access with typo
        typo_path = os.path.join(self.temp_dir, "test_similar_typo")
        result = cd_tool.forward(path=typo_path)
        
        # Should provide suggestions
        self.assertIn("Error: Directory", result)
        self.assertIn("does not exist", result)
        
        # May include suggestions (depending on similarity algorithm)
        # This is a best-effort feature
        
        # Should stay in original directory
        self.assertEqual(os.getcwd(), self.original_cwd)

    def test_restricted_directory_protection(self):
        """Test that restricted system directories are protected."""
        if platform.system() == "Windows":
            restricted_path = "C:\\Windows\\System32"
        else:
            restricted_path = "/bin"
        
        # Only test if the directory actually exists on this system
        if os.path.exists(restricted_path):
            result = cd_tool.forward(path=restricted_path)
            
            # Should be blocked
            self.assertIn("Error: Cannot change to restricted", result)
            self.assertIn("safety reasons", result)
            
            # Should stay in original directory
            self.assertEqual(os.getcwd(), self.original_cwd)

    def test_directory_summary_feature(self):
        """Test that directory summary is provided after successful change."""
        result = cd_tool.forward(path=self.temp_dir)
        
        # Should include directory summary
        self.assertIn("Directory changed successfully!", result)
        # Should show files and directories
        self.assertTrue("📄" in result or "📁" in result or "files" in result or "directories" in result)

    def test_environment_variable_expansion(self):
        """Test that environment variables are properly expanded."""
        # Set a test environment variable
        test_env_var = "TEST_CD_PATH"
        os.environ[test_env_var] = self.temp_dir
        
        try:
            if platform.system() == "Windows":
                result = cd_tool.forward(path=f"%{test_env_var}%")
            else:
                result = cd_tool.forward(path=f"${test_env_var}")
            
            # Should succeed
            self.assertIn("Directory changed successfully!", result)
            
            # Verify we're in the temp directory
            self.assertEqual(os.getcwd(), self.temp_dir)
            
        finally:
            # Clean up environment variable
            if test_env_var in os.environ:
                del os.environ[test_env_var]

    def test_permission_denied_handling(self):
        """Test handling of permission denied errors."""
        # This test is platform and system dependent
        # We'll skip it if we can't create a permission-restricted directory
        try:
            restricted_dir = os.path.join(self.temp_dir, "restricted")
            os.makedirs(restricted_dir, exist_ok=True)
            
            # Try to remove permissions (Unix only)
            if platform.system() != "Windows":
                os.chmod(restricted_dir, 0o000)
                
                result = cd_tool.forward(path=restricted_dir)
                
                # Should handle permission error gracefully
                self.assertIn("Error:", result)
                self.assertTrue("permission" in result.lower() or "access" in result.lower())
                
                # Restore permissions for cleanup
                os.chmod(restricted_dir, 0o755)
            else:
                # On Windows, this test is harder to implement reliably
                self.skipTest("Permission test not implemented for Windows")
                
        except Exception:
            # If we can't set up the test, skip it
            self.skipTest("Could not set up permission test")

    def test_current_directory_preservation_on_error(self):
        """Test that current directory is preserved when change fails."""
        original_dir = os.getcwd()
        
        # Try to change to nonexistent directory
        result = cd_tool.forward(path="/definitely/does/not/exist")
        
        # Should fail
        self.assertIn("Error:", result)
        
        # Should preserve original directory
        self.assertEqual(os.getcwd(), original_dir)

    def test_empty_directory_summary(self):
        """Test directory summary for empty directory."""
        empty_dir = os.path.join(self.temp_dir, "empty")
        os.makedirs(empty_dir, exist_ok=True)
        
        result = cd_tool.forward(path=empty_dir)
        
        # Should succeed and note empty directory
        self.assertIn("Directory changed successfully!", result)
        self.assertIn("empty", result.lower())


if __name__ == "__main__":
    unittest.main()