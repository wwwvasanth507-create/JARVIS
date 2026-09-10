"""
Dangerous command, destructive operation, and privilege escalation detector for JARVIS.
"""

import re
from typing import List, Optional
from jarvis.shell.errors import DangerousCommandBlocked, PrivilegeEscalationBlocked
from jarvis.shell.parser import ParsedCommand


DANGEROUS_PATTERNS = [
    # Disk formatting & partition destruction
    (r"\b(format|mkfs|fdisk|parted|diskpart)\b", "Disk formatting and partition alteration"),
    # Recursive system deletion
    (r"\brm\s+-[rRfF\s]+\s*(/|/\*|\*|[cC]:\\?)", "Recursive root directory deletion"),
    (r"\brd\s+/s\s+/q\s+[cC]:?\\?", "Windows recursive root deletion"),
    # System power actions
    (r"\b(shutdown|reboot|init\s+[06]|stop-computer|restart-computer)\b", "System shutdown or reboot"),
    # Security software & firewall tampering
    (r"\b(netsh\s+advfirewall|ufw\s+disable|set-mppreference\s+-disablerealtimemonitoring)\b", "Security/Firewall software disabling"),
    # Credential & secret harvesting
    (r"\b(mimikatz|samdump|pwdump|lsass|vaultcmd)\b", "Credential harvesting utility"),
    # Download & execute pipelines
    (r"(curl|wget|iwr|invoke-webrequest).*\|.*(sh|bash|powershell|iex|cmd)", "Download and execute pipeline pattern"),
]

PRIVILEGE_ESCALATION_PATTERNS = [
    r"\bsudo\b",
    r"\bsu\b",
    r"\brunas(\.exe)?\b",
    r"\bpsexec(\.exe)?\b",
    r"\bstart-process\s+.*-verb\s+runas\b",
]


class DangerousCommandDetector:
    """Detects destructive actions, privilege escalations, and credential harvesting patterns."""

    @staticmethod
    def inspect(parsed: ParsedCommand) -> None:
        """
        Analyzes a parsed command. Raises DangerousCommandBlocked or PrivilegeEscalationBlocked
        if any malicious or destructive pattern is matched.
        """
        raw = parsed.raw_command.lower()

        # Check privilege escalation
        for p_pat in PRIVILEGE_ESCALATION_PATTERNS:
            if re.search(p_pat, raw, re.IGNORECASE):
                raise PrivilegeEscalationBlocked(
                    f"Autonomous privilege escalation attempt detected ('{parsed.executable}'). "
                    "Administrator/root elevation is blocked."
                )

        # Check dangerous patterns
        for d_pat, description in DANGEROUS_PATTERNS:
            if re.search(d_pat, raw, re.IGNORECASE):
                raise DangerousCommandBlocked(
                    f"Dangerous command pattern detected: {description}. Command execution blocked."
                )
