"""
Unit tests for SkillManifestParser and SkillValidator.
"""

from pathlib import Path
import pytest
from jarvis.skills.errors import SkillValidationError
from jarvis.skills.manifest import SkillManifestParser
from jarvis.skills.models import SkillCategory
from jarvis.skills.validator import SkillValidator


def test_manifest_parser_valid():
    parser = SkillManifestParser()
    manifest_data = {
        "skill": {
            "id": "test_skill",
            "name": "Test Skill",
            "category": "builtin",
            "aliases": ["run test"],
            "tools": ["application.open"],
            "risk_level": "LOW",
        },
        "workflow": [
            {"id": "step1", "action": "application.open"}
        ],
    }
    skill = parser.parse_dict(manifest_data)
    assert skill.skill_id == "test_skill"
    assert skill.name == "Test Skill"
    assert skill.category == SkillCategory.BUILTIN
    assert len(skill.workflow) == 1


def test_validator_rejects_unregistered_tool():
    validator = SkillValidator()
    parser = SkillManifestParser()
    manifest_data = {
        "skill": {
            "id": "invalid_skill",
            "name": "Invalid Skill",
            "tools": ["nonexistent.tool"],
        },
        "workflow": [{"id": "s1", "action": "nonexistent.tool"}],
    }
    skill = parser.parse_dict(manifest_data)
    with pytest.raises(SkillValidationError) as excinfo:
        validator.validate(skill, registered_tools={"application.open": None})
    assert "nonexistent.tool" in str(excinfo.value)
