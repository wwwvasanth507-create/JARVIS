"""
OS-native application path resolution and discovery mechanisms for Windows, Linux, and macOS.
"""

import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional
from jarvis.applications.state import ApplicationInfo


class ApplicationPlatform:
    """Platform-specific discovery locations and path expansion helper."""

    @staticmethod
    def get_platform_name() -> str:
        return sys.platform

    @classmethod
    def expand_path(cls, path_str: str) -> Path:
        """Expands environment variables and user tildes."""
        expanded = os.path.expandvars(os.path.expanduser(path_str))
        return Path(expanded)

    @classmethod
    def resolve_executable_path(cls, app_info: ApplicationInfo) -> Optional[Path]:
        """Resolves existing executable Path on system for ApplicationInfo."""
        # 1. Check if on system PATH via shutil.which
        which_path = shutil.which(app_info.executable)
        if which_path:
            p = Path(which_path)
            if p.exists():
                return p.resolve(strict=False)

        # 2. Check configured common_paths
        for cp in app_info.common_paths:
            exp_p = cls.expand_path(cp)
            if exp_p.exists() and exp_p.is_file():
                return exp_p.resolve(strict=False)

        return None

    @classmethod
    def get_discovery_locations(cls) -> List[Path]:
        """Returns standard OS installation directories for fast discovery."""
        plat = sys.platform
        locs: List[Path] = []

        if plat == "win32":
            start_user = cls.expand_path("%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs")
            start_common = cls.expand_path("%ALLUSERSPROFILE%\\Microsoft\\Windows\\Start Menu\\Programs")
            pf = cls.expand_path("C:\\Program Files")
            pfx86 = cls.expand_path("C:\\Program Files (x86)")
            local_app = cls.expand_path("%LOCALAPPDATA%\\Programs")

            for p in [start_user, start_common, pf, pfx86, local_app]:
                if p.exists() and p.is_dir():
                    locs.append(p)
        elif plat == "darwin":
            mac_apps = cls.expand_path("/Applications")
            mac_user_apps = cls.expand_path("~/Applications")
            for p in [mac_apps, mac_user_apps]:
                if p.exists() and p.is_dir():
                    locs.append(p)
        else:
            usr_share = cls.expand_path("/usr/share/applications")
            local_share = cls.expand_path("~/.local/share/applications")
            for p in [usr_share, local_share]:
                if p.exists() and p.is_dir():
                    locs.append(p)

        return locs
