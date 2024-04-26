import subprocess
import time
import questionary
import os

result = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'])
base_directory = result.decode('utf-8').strip()

def run_script(script_path, args):
    try:
        subprocess.run(["python3", script_path, *args],  check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running script: {e}")

def main():
    # controller = "/home/vmadm/demo/RapidServe/southbound/new_controller.py"
    tenant_name = questionary.text("Enter your org name:").ask()
    

    # playbook_path = os.path.join(base_directory, 'southbound', 'deploy_vpc.yaml')
    # print(playbook_path)
    controller = os.path.join(base_directory, 'southbound', 'new_controller.py')


    time.sleep(5)
    run_script(controller, [tenant_name])

if __name__ == "__main__":
    main()