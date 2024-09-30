import os

script_to_run:str = "full_test.py"
# path below in UNIX format, with slashes
script_dir:str = "/Users/gilles_recital/source/repos/rag-package/tests/"


commands:dict[str,dict] = {
    "linux": {"command": 'wsl -e bash -li -c "python3 {}"', "prefix_path": "/mnt/c"},
    "windows": {"command": "python {}", "prefix_path": "C:", "replace_slash_with_bs":True},
}

for os_name, params in commands.items():
    print('*'*15 + f' Start for OS "{os_name}"')
    command:str = params['command'].format(f'{params["prefix_path"]}{script_dir}{script_to_run}')
    if "replace_slash_with_bs" in params: command = command.replace('/', '\\')
    os.system(command)
    print('*'*15 + f' End for OS "{os_name}"')

