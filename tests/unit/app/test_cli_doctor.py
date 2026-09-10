"""
Unit tests for CLI Entry Point and Diagnostic Doctor.
"""

from jarvis.core.diagnostics import JarvisDoctor, JarvisSelfTest, DiagnosticStatus


def test_jarvis_doctor_diagnostics():
    results = JarvisDoctor.run_diagnostics()
    assert len(results) >= 5
    
    config_result = next(r for r in results if r.component == "Configuration")
    assert config_result.status == DiagnosticStatus.PASS

    db_result = next(r for r in results if r.component == "Database (SQLite)")
    assert db_result.status == DiagnosticStatus.PASS


def test_jarvis_self_test():
    report = JarvisSelfTest.run_self_test()
    assert "overall_status" in report
    assert report["overall_status"] == "PASS"
    assert report["tests"]["config_load"] == "PASS"
    assert report["tests"]["database_init"] == "PASS"
    assert report["tests"]["fast_path_command"] == "PASS"
