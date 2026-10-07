---
name: Python package setup
description: Workspace-specific Python interpreter and package installation behavior.
---

In this workspace, the default Python 3.13 base interpreter has no pip and rejects package installs as externally managed. Install a Python Tools module (Python 3.11 worked) through package management before installing dependencies; then use the managed Python package installer.

**Why:** The base interpreter is immutable, while the Python Tools module provides pip and the project's `.pythonlibs` environment.

**How to apply:** For future Python dependencies, use the managed Python Tools runtime and package installer rather than calling system `pip` directly.
