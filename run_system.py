import os
import sys
import subprocess
import signal

DEFAULT_NUMBER_OF_RELAYS = 10
DEFAULT_NUMBER_OF_FAKE_RELAYS = 10
DEFAULT_NUMBER_OF_CLIENTS = 5

# checks if the arguments are valid
if len(sys.argv) == 4:
    if str.isdigit(sys.argv[1]) and str.isdigit(sys.argv[2]) and str.isdigit(sys.argv[3]):
        if int(sys.argv[1]) > 0 and int(sys.argv[2]) > 0 and int(sys.argv[3]) > 0:
            DEFAULT_NUMBER_OF_RELAYS = int(sys.argv[1])
            DEFAULT_NUMBER_OF_FAKE_RELAYS = int(sys.argv[2])
            DEFAULT_NUMBER_OF_CLIENTS = int(sys.argv[3])


def main():
    # data for the status
    processes_running = {
        "relay.py": 0,
        "fake_relay.py": 0,
        "client.py": 0
    }

    # get current path
    path = os.getcwd()
    # processes to run
    tasks = [
        ('server.py', 1),
        ('onion_server.py', 1),
        ('hacker_server.py', 1),
        ('relay.py', DEFAULT_NUMBER_OF_RELAYS),
        ('fake_relay.py', DEFAULT_NUMBER_OF_FAKE_RELAYS),
        ('client.py', DEFAULT_NUMBER_OF_CLIENTS)
    ]

    task_processes = []

    for task in tasks:
        # runs the task n times
        for i in range(task[1]):
            try:
                proc = subprocess.Popen(r'python %s\%s' % (path, task[0]), shell=True)
                if task[0] in processes_running:
                    processes_running[task[0]] += 1
                    task_processes.append(proc)
            except:
                print("----------------------------------error running the process")
                if task[0] not in processes_running:
                    for p in task_processes:
                        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                    return False

    print("----------------------------------status:")
    for p in processes_running:
        print("----------------------------------number of " + p + " running:" + str(processes_running[p]))

    for task in task_processes:
        task.wait()


result = main()
