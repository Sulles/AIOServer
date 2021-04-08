"""
Created: July 20, 2020
Updated: April 2, 2021
Author: Suleyman Barthe-Sukhera
Description: _pb2.py auto generator for all Proto files in this folder
"""

import subprocess
from os import listdir, name as os_name
from os.path import isfile, join
from pathlib import Path

# initialize path at current working directory
path = Path().cwd()

if os_name == 'nt':
    protoc = 'protoc.exe'
elif os_name == 'posix':
    protoc = './protoc'
else:
    raise (OSError, 'build_pb2 only works on "nt" and "posix" operating systems')
# can be called from source root, or from /bin
if str(path.cwd())[-9:] == 'AIOServer':
    path = path.cwd() / 'CommonLib' / 'proto' / 'bin'
# print(f'path: {path}')

# Get all .proto files
all_files = [f + ' ' for f in listdir(path) if isfile(join(path, f)) and f[-6:] == '.proto']
# Put Base.proto first if it exists
if 'Base.proto' in all_files:
    del all_files[all_files.index(f'Base.proto ')]
    all_files = ''.join(all_files)
    all_files = 'Base.proto ' + all_files
else:
    all_files = ''.join(all_files)
# print(f'all_files: {all_files}')

# Get client directory to output python files
# print(f'client directory: {path.client}')

# Build protoc command
command = f'{protoc} --proto_path={path} --python_out={path.parent} {all_files}'
# print(f'command: {command}')

# Send command
output = subprocess.run(args=command, text=True, capture_output=True, cwd=path, shell=True)
# print(f'command output:\n{output}')
if output.stderr != '':
    print(f'Failed to successfully execute shell command:\n'
          f'{command}\n'
          f'Received error:\n'
          f'{output.stderr}')
    raise RuntimeError
