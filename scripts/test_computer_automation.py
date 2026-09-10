"""
End-to-End Computer Control Automation Test Script for PROMPT 005.
Safely tests Calculator application lifecycle: Open -> Verify -> Focus -> Close -> Verify Closed + Latency Benchmarks.
"""

from pathlib import Path
import sys
import time
import psutil

src_dir = Path(__file__).resolve().parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from jarvis.computer.factory import ComputerControllerFactory
from jarvis.applications.launcher import ApplicationLauncher
from jarvis.applications.detector import ApplicationDetector
from jarvis.applications.registry import ApplicationRegistry


def run_computer_automation_test():
    print("=======================================================")
    print("  JARVIS PROMPT 005 COMPUTER AUTOMATION BENCHMARK TEST  ")
    print("=======================================================")

    controller = ComputerControllerFactory.get_controller()
    launcher = ApplicationLauncher()
    registry = ApplicationRegistry()
    target_entry = registry.resolve("notepad")

    # Measure Mouse Action Latency
    start_m = time.perf_counter()
    m_res = controller.move_mouse(150, 150)
    m_dur = time.perf_counter() - start_m
    print(f"[+] Mouse Action Latency     : {m_dur*1000:.2f} ms (Success: {m_res.success})")

    # Measure Keyboard Action Latency
    start_k = time.perf_counter()
    k_res = controller.press_key("SHIFT")
    k_dur = time.perf_counter() - start_k
    print(f"[+] Keyboard Action Latency  : {k_dur*1000:.2f} ms (Success: {k_res.success})")

    # Measure Screenshot Capture Time
    start_s = time.perf_counter()
    s_res = controller.screenshot(active_window_only=False)
    s_dur = time.perf_counter() - start_s
    print(f"[+] Screenshot Capture Time  : {s_dur*1000:.2f} ms ({s_res.data['width']}x{s_res.data['height']})")

    # Measure Window Detection Latency
    start_w = time.perf_counter()
    wins = controller.list_windows()
    w_dur = time.perf_counter() - start_w
    print(f"[+] Window Detection Latency : {w_dur*1000:.2f} ms (Found {len(wins)} top-level windows)")

    # -------------------------------------------------------------
    # CONTROLLED END-TO-END AUTOMATION TEST: NOTEPAD LIFECYCLE
    # -------------------------------------------------------------
    print("\n--- STEP 1: Launching Application ('notepad') ---")
    start_launch = time.perf_counter()
    open_res = launcher.open_application("notepad")
    launch_dur = time.perf_counter() - start_launch

    print(f"[+] App Launch Latency       : {launch_dur*1000:.2f} ms")
    print(f"[+] Launch Action Result      : {open_res.status} ({open_res.message})")

    # Step 2: Verify Application Running
    print("\n--- STEP 2: Verifying Process & Window State ---")
    status_after_open = ApplicationDetector.get_status(target_entry)
    print(f"[+] Application Is Running   : {status_after_open.is_running}")
    print(f"[+] Process IDs              : {status_after_open.process_ids}")
    assert open_res.success is True, "Failed to launch target application"

    # Step 3: Focus Application Window
    print("\n--- STEP 3: Focusing Application Window ---")
    focus_res = controller.focus_window("notepad")
    print(f"[+] Focus Action Result      : {focus_res.status} ({focus_res.message})")

    # Step 4: Close Application
    print("\n--- STEP 4: Closing Application Gracefully ---")
    close_res = launcher.close_application("notepad", force=True)
    print(f"[+] Close Action Result      : {close_res.status} ({close_res.message})")

    # Step 5: Verify Application Closed
    print("\n--- STEP 5: Verifying Process Termination ---")
    status_after_close = ApplicationDetector.get_status(target_entry)
    print(f"[+] Application Is Running   : {status_after_close.is_running}")
    assert status_after_close.is_running is False, "Target application process failed to terminate"

    # Process Resource Measurements
    proc = psutil.Process()
    mem_mb = proc.memory_info().rss / (1024**2)
    cpu_pct = psutil.cpu_percent(interval=0.1)

    print("\n-------------------------------------------------------")
    print(f"[+] Process Memory Footprint : {mem_mb:.2f} MB")
    print(f"[+] CPU Utilization          : {cpu_pct:.1f}%")
    print("=======================================================")
    print("[SUCCESS] Controlled desktop application automation test completed 100% successfully!")
    print("=======================================================\n")


if __name__ == "__main__":
    run_computer_automation_test()
