import platform
import subprocess
import getpass
import os

def _get_command_output(cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "Unknown"

def get_system_info() -> dict:
    """Safely fetch system information for both Linux and Windows."""
    sys_name = platform.system()
    info = {
        "os": sys_name,
        "user": getpass.getuser(),
        "hostname": platform.node(),
    }

    if sys_name == "Linux":
        info["kernel"] = _get_command_output("uname -r")
        
        # Uptime
        uptime = _get_command_output("uptime -p")
        if uptime.startswith("up "):
            uptime = uptime[3:]
        info["uptime"] = uptime

        # Shell
        shell = os.environ.get("SHELL", "Unknown")
        info["shell"] = os.path.basename(shell) if shell != "Unknown" else "Unknown"

        # Memory
        mem = _get_command_output("free -h | awk '/^Mem:/ {print $3 \" / \" $2}'")
        info["mem"] = mem

        # Distro
        distro = "Linux"
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        distro = line.split("=")[1].strip().strip('"')
                        break
        except Exception:
            pass
        info["distro"] = distro

    elif sys_name == "Windows":
        info["kernel"] = platform.version()
        info["distro"] = f"Windows {platform.release()}"
        
        # Memory
        # Using wmic to get memory in bytes and converting to GB roughly
        try:
            total_mem = _get_command_output("wmic ComputerSystem get TotalPhysicalMemory | findstr /R \"[0-9]\"")
            free_mem = _get_command_output("wmic OS get FreePhysicalMemory | findstr /R \"[0-9]\"")
            if total_mem != "Unknown" and free_mem != "Unknown":
                total_gb = float(total_mem.strip()) / (1024**3)
                free_gb = float(free_mem.strip()) / (1024**2) # FreePhysicalMemory is in KB
                used_gb = total_gb - free_gb
                info["mem"] = f"{used_gb:.1f} GiB / {total_gb:.1f} GiB"
            else:
                info["mem"] = "Unknown"
        except Exception:
            info["mem"] = "Unknown"

        info["uptime"] = "Unknown (Windows)"
        info["shell"] = os.environ.get("COMSPEC", "cmd.exe").split("\\")[-1]

    else:
        # Mac / other
        info["kernel"] = platform.release()
        info["distro"] = sys_name
        info["uptime"] = "Unknown"
        info["shell"] = os.environ.get("SHELL", "Unknown")
        info["mem"] = "Unknown"

    return info
