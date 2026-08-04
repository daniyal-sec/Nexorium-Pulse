import json
import os
from datetime import datetime
import ipaddress
import socket
import time
from concurrent.futures import ThreadPoolExecutor


# ==========================================
# NEXORIUM PULSE CONFIGURATION
# ==========================================

VERSION = "1.0"
TIMEOUT = 0.5
MAX_WORKERS = 100


# ==========================================
# CLI
# ==========================================

def print_banner():
    print(f"""
========================================================
                    NEXORIUM PULSE
                      Version {VERSION}
                    TCP Port Scanner
========================================================
""")


def print_scan_info(target, start_port, end_port):
    print("\n[ TARGET CONFIGURATION ]\n")

    print("Target IP     :", target)
    print("Port Range    :", f"{start_port} - {end_port}")
    print("Timeout       :", TIMEOUT, "seconds")
    print("Workers       :", MAX_WORKERS)

    print("\n[*] Starting TCP scan...\n")


# ==========================================
# INPUT VALIDATION
# ==========================================

def get_target_ip():
    while True:
        target_ip = input("Enter IP of the Target : ")

        try:
            ipaddress.ip_address(target_ip)
            return target_ip

        except ValueError:
            print("[!] Please enter a valid IP address.")


def get_port_range():
    while True:
        try:
            start_port = int(input("Enter start port : "))
            end_port = int(input("Enter end port   : "))

            if 1 <= start_port <= end_port <= 65535:
                return start_port, end_port

            print("[!] Ports must be between 1 and 65535.")

        except ValueError:
            print("[!] Port numbers must be integers.")


# ==========================================
# PORT SCANNING
# ==========================================

def scan_port(target_ip, port):
    sock = socket.socket()
    sock.settimeout(TIMEOUT)

    try:
        result = sock.connect_ex((target_ip, port))

        if result == 0:
            return port

        return None

    except OSError:
        return None

    finally:
        sock.close()


def get_service_name(port):
    try:
        return socket.getservbyport(port, "tcp")

    except OSError:
        return "unknown"


def scan_ports(target_ip, start_port, end_port):
    start_time = time.time()

    # Run port checks concurrently
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        results = executor.map(
            lambda port: scan_port(target_ip, port),
            range(start_port, end_port + 1)
        )

    # Store discovered open ports
    open_ports = []

    for result in results:
        if result is not None:
            open_ports.append(result)

    end_time = time.time()

    duration = end_time - start_time

    total_ports = end_port - start_port + 1
    open_count = len(open_ports)
    closed_ports = total_ports - open_count

    # ==========================================
    # SCAN SUMMARY
    # ==========================================

    print("\n========================================================")
    print("                     SCAN COMPLETE")
    print("========================================================\n")

    print("Target        :", target_ip)
    print("Port Range    :", f"{start_port} - {end_port}")
    print("Ports Scanned :", total_ports)
    print("Open Ports    :", open_count)
    print("Closed Ports  :", closed_ports)
    print("Duration      :", round(duration, 2), "seconds")

    # ==========================================
    # OPEN PORT TABLE
    # ==========================================

    if open_ports:

        print()
        print(f"{'PORT':<12}{'STATE':<12}{'SERVICE':<20}")
        print("-" * 44)

        for port in open_ports:
            service = get_service_name(port)
            port_display = f"{port}/tcp"

            print(
                f"{port_display:<12}"
                f"{'OPEN':<12}"
                f"{service:<20}"
            )

    else:
        print("\n[!] No open ports found.")

    print("\n========================================================")
    print("             Nexorium Pulse - Scan Finished")
    print("========================================================")

    export_results(
    target_ip,
    start_port,
    end_port,
    open_ports,
    duration
)



def export_results(
    target_ip,
    start_port,
    end_port,
    open_ports,
    duration
):
    os.makedirs("results", exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    txt_filename = f"results/pulse_scan_{timestamp}.txt"
    json_filename = f"results/pulse_scan_{timestamp}.json"

    total_ports = end_port - start_port + 1
    closed_ports = total_ports - len(open_ports)

    scan_data = {
        "tool": "Nexorium Pulse",
        "version": VERSION,
        "target": target_ip,
        "start_port": start_port,
        "end_port": end_port,
        "ports_scanned": total_ports,
        "open_ports": open_ports,
        "closed_ports": closed_ports,
        "duration_seconds": round(duration, 2)
    }

    # JSON report
    with open(json_filename, "w") as file:
        json.dump(scan_data, file, indent=4)

    # TXT report
    with open(txt_filename, "w") as file:
        file.write("NEXORIUM PULSE SCAN REPORT\n")
        file.write("=" * 40 + "\n")
        file.write(f"Target        : {target_ip}\n")
        file.write(f"Port Range    : {start_port} - {end_port}\n")
        file.write(f"Ports Scanned : {total_ports}\n")
        file.write(f"Open Ports    : {len(open_ports)}\n")
        file.write(f"Closed Ports  : {closed_ports}\n")
        file.write(f"Duration      : {round(duration, 2)} seconds\n")

        file.write("\nOPEN PORTS\n")
        file.write("-" * 40 + "\n")

        if open_ports:
            for port in open_ports:
                service = get_service_name(port)
                file.write(f"{port}/tcp - OPEN - {service}\n")
        else:
            file.write("No open ports found.\n")

    print("\n[+] Reports saved:")
    print("    ", txt_filename)
    print("    ", json_filename)


# ==========================================
# MAIN
# ==========================================


def main():

    print_banner()

    target = get_target_ip()

    start_port, end_port = get_port_range()

    print_scan_info(
        target,
        start_port,
        end_port
    )

    scan_ports(
        target,
        start_port,
        end_port
    )


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("\n\n[!] Scan cancelled by user.")
        print("[*] Nexorium Pulse shutting down.")