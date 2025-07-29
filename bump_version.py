#!/usr/bin/env python3
"""
Simple version bump script for pyobjict package.

Usage:
    python bump_version.py patch   # 1.0.0 -> 1.0.1
    python bump_version.py minor   # 1.0.0 -> 1.1.0
    python bump_version.py major   # 1.0.0 -> 2.0.0
    python bump_version.py --show  # Show current version
"""

import re
import sys
import subprocess
from pathlib import Path
from typing import Tuple


def get_current_version() -> str:
    """Get current version from pyproject.toml"""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found")

    content = pyproject_path.read_text()
    match = re.search(r'version = "([^"]+)"', content)
    if not match:
        raise ValueError("Version not found in pyproject.toml")

    return match.group(1)


def parse_version(version: str) -> Tuple[int, int, int]:
    """Parse version string into major, minor, patch tuple"""
    try:
        parts = version.split(".")
        if len(parts) != 3:
            raise ValueError("Version must be in format MAJOR.MINOR.PATCH")
        return tuple(int(p) for p in parts)
    except ValueError as e:
        raise ValueError(f"Invalid version format: {version}") from e


def bump_version(version: str, bump_type: str) -> str:
    """Bump version based on type"""
    major, minor, patch = parse_version(version)

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}. Use 'major', 'minor', or 'patch'")


def update_pyproject_toml(new_version: str) -> None:
    """Update version in pyproject.toml"""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()

    # Update version in [tool.poetry] section
    content = re.sub(
        r'(version = ")[^"]+(")',
        rf'\g<1>{new_version}\g<2>',
        content
    )

    pyproject_path.write_text(content)
    print(f"✓ Updated pyproject.toml")


def update_init_py(new_version: str) -> None:
    """Update version in objict/__init__.py"""
    init_path = Path("objict/__init__.py")
    if not init_path.exists():
        print("⚠ objict/__init__.py not found, skipping")
        return

    content = init_path.read_text()
    major, minor, patch = parse_version(new_version)

    # Update __version_info__
    content = re.sub(
        r'__version_info__ = \([^)]+\)',
        f'__version_info__ = ({major}, {minor}, {patch})',
        content
    )

    # Update __version__
    content = re.sub(
        r'__version__ = "[^"]+"',
        f'__version__ = "{new_version}"',
        content
    )

    init_path.write_text(content)
    print(f"✓ Updated objict/__init__.py")


def create_git_tag(version: str) -> None:
    """Create git tag for the new version"""
    try:
        # Check if git is available and we're in a git repo
        subprocess.run(["git", "rev-parse", "--git-dir"],
                      check=True, capture_output=True)

        # Create tag
        tag_name = f"v{version}"
        subprocess.run(["git", "tag", tag_name], check=True)
        print(f"✓ Created git tag: {tag_name}")

        # Ask if user wants to push the tag
        response = input(f"Push tag {tag_name} to remote? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            subprocess.run(["git", "push", "origin", tag_name], check=True)
            print(f"✓ Pushed tag {tag_name} to remote")

    except subprocess.CalledProcessError:
        print("⚠ Git not available or not in a git repository, skipping tag creation")
    except KeyboardInterrupt:
        print("\n⚠ Tag creation cancelled")


def commit_changes(version: str) -> None:
    """Commit version bump changes"""
    try:
        # Check if git is available
        subprocess.run(["git", "rev-parse", "--git-dir"],
                      check=True, capture_output=True)

        # Add files
        subprocess.run(["git", "add", "pyproject.toml", "objict/__init__.py"],
                      check=True)

        # Commit
        commit_msg = f"bump version to {version}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        print(f"✓ Committed changes: {commit_msg}")

    except subprocess.CalledProcessError:
        print("⚠ Could not commit changes (git not available or no changes)")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    arg = sys.argv[1]

    try:
        current_version = get_current_version()

        if arg == "--show":
            print(f"Current version: {current_version}")
            return

        if arg not in ["major", "minor", "patch"]:
            print(f"Error: Invalid argument '{arg}'. Use 'major', 'minor', 'patch', or '--show'")
            print(__doc__)
            sys.exit(1)

        new_version = bump_version(current_version, arg)

        print(f"Bumping version: {current_version} -> {new_version}")
        print()

        # Update files
        update_pyproject_toml(new_version)
        update_init_py(new_version)

        print()
        print(f"✅ Version bumped successfully!")
        print(f"   Old version: {current_version}")
        print(f"   New version: {new_version}")
        print()

        # Ask about git operations
        response = input("Commit changes and create git tag? (Y/n): ").strip().lower()
        if response in ['', 'y', 'yes']:
            commit_changes(new_version)
            create_git_tag(new_version)

        print()
        print("Next steps:")
        print("1. Review the changes")
        print("2. Run: poetry build")
        print("3. Run: poetry publish (if ready to release)")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
