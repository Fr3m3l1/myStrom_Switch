import os
import requests
import sys
import time
import signal
import subprocess
import threading
import platform
from dotenv import load_dotenv

# Global variables for managing the shutdown timer
shutdown_timer = None
shutdown_scheduled = False

def is_computer_online(computer_ip):
    """Check if the computer is reachable by sending a ping."""
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', computer_ip]
    return subprocess.call(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ) == 0

def turn_off_switch(system_ip):
    """Send an HTTP request to turn off the switch."""
    state_off = 0
    off_url = f"http://{system_ip}/elay?state={state_off}"
    try:
        response = requests.get(off_url, timeout=10)
        response.raise_for_status()
        print("Switch turned off successfully")
    except requests.exceptions.RequestException as e:
        print(f"Error turning off switch: {e}", file=sys.stderr)

def main():
    global shutdown_timer, shutdown_scheduled

    # Read environment variables
    system_ip = os.getenv('SYSTEM_IP')    # IP of the switch
    computer_ip = os.getenv('COMPUTER_IP') # IP of the computer to monitor

    # Validate environment variables
    required_env_vars = {'SYSTEM_IP': system_ip, 'COMPUTER_IP': computer_ip}
    for var, value in required_env_vars.items():
        if not value:
            print(f"Error: {var} environment variable not set", file=sys.stderr)
            sys.exit(1)

    # Signal handling for graceful exit
    def signal_handler(sig, frame):
        print("\nExiting gracefully...")
        if shutdown_scheduled:
            shutdown_timer.cancel()
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print(f"Monitoring computer at {computer_ip}. Switch control at {system_ip}")

    while True:
        computer_online = is_computer_online(computer_ip)
        
        if computer_online:
            print("Computer is online")
            if shutdown_scheduled:
                shutdown_timer.cancel()
                shutdown_scheduled = False
                print("Cancelled pending shutdown")
        else:
            print("Computer is offline")
            if not shutdown_scheduled:
                shutdown_timer = threading.Timer(
                    20.0, 
                    turn_off_switch, 
                    args=[system_ip]
                )
                shutdown_timer.start()
                shutdown_scheduled = True
                print("Scheduled switch shutdown in 20 seconds")
        
        time.sleep(10)  # Check every 10 seconds

if __name__ == "__main__":
    load_dotenv()
    main()