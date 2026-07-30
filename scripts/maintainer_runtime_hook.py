"""Enable maintainer-only learning tools in the dedicated Windows build."""

from __future__ import annotations

import os

os.environ["PSFS_MAINTAINER_MODE"] = "1"
