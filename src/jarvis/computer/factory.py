"""
ComputerController Factory for JARVIS.
Detects running host OS and returns appropriate native ComputerController implementation.
"""

import platform
import logging
from jarvis.computer.base import ComputerController
from jarvis.computer.windows import WindowsComputerController

logger = logging.getLogger("jarvis.computer.factory")


class ComputerControllerFactory:
    """Factory creating OS-specific ComputerController instances."""

    @staticmethod
    def get_controller() -> ComputerController:
        os_name = platform.system().lower()
        if os_name == "windows":
            logger.info("Instantiating WindowsComputerController")
            return WindowsComputerController()
        else:
            logger.warning(f"Platform '{platform.system()}' defaults to WindowsComputerController abstraction fallback.")
            return WindowsComputerController()
