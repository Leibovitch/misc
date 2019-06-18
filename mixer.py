import re
import os
import sys
from pathlib import Path
import logging
import subprocess


logging.getLogger().setLevel(logging.INFO)
valid_line_matcher = re.compile(r'^[-\w]+={2}(\d+\.)+\d+(\.\w+)?$')
version_matcher = re.compile(r'(?<===)(\d+\.)+\d+(\.\w+)?$')
package_matcher = re.compile(r'^[-\w]+')


packages = []
irregular_lines = []
versions = {}

def create_reqs():
    path = sys.argv[1]
    file_path = path + '/requirements.txt'
    
    if Path(file_path).exists():    
        with open(file_path):
            os.system('mv ' + file_path + ' ' + path + '/old_reqs.txt')
            os.system('pipreqs ' + path)
            os.system('mv ' + file_path + ' ' + path + '/pip_reqs.txt')
            mixer(path + '/old_reqs.txt', path + '/pip_reqs.txt')
    else:
        os.system('pipreqs ' + path)
        fill_lists(file_path)
    
    update_setup(path)

        # os.system('rm ' + path + '/pip_reqs.txt')
        # os.system('rm ' +   path + '/old_reqs.txt')

def update_setup(path):
    #assumes the file exists
    setup_path = path + '/setup.py'
    os.system('mv ' + setup_path + ' ' + path + '/old_setup.py')
    with open(path + '/old_setup.py', 'r') as sp, open(setup_path, 'w+') as ns:
        line = sp.readline()
        while not re.compile(r'install_requires').search(line):
            ns.write(line)
            line = sp.readline()

        ns.write(line)
        for package in packages[0:-1]:
            ns.write(package + ',\n')
            
        ns.write(package + '\n')
        line = sp.readline()
        while line:
            ns.write(line)
            line = sp.readline()

def mixer(path1, path2):
    print('mixer running')
    fill_lists(path1)
    fill_lists(path2)
    write_packages_to_files('/'.join(path1.split('/')[0:-1]))


def fill_lists(path):
    with open(path) as fp:
        line = fp.readline()[0:-1]
        while line:
            add_to_lists(line)
            line = fp.readline()[0:-1]


def write_packages_to_files(path):
    with open(path + '/requirements.txt', 'w+') as req:
        for irreg in irregular_lines:
            req.write(irreg + '\n')

        for package in packages:
            req.write('{}=={}'.format(package, versions[package]) + '\n')


def return_newer_version(competitor_version, holding_version):
    competitior_fragments = competitor_version.split('.')
    holding_fragments = holding_version.split('.')
    if len(competitior_fragments) >= len(holding_fragments):
        shorter_fragments = competitior_fragments
        longer_fragments = holding_fragments
    else:
        shorter_fragments = holding_fragments
        longer_fragments = competitior_fragments

    for i, fragment in enumerate(shorter_fragments):
        if is_num(fragment) and is_num(longer_fragments[i]):
            if int(fragment) > int(longer_fragments[i]):
                return '.'.join(shorter_fragments)
            elif int(fragment) < int(longer_fragments[i]):
                return '.'.join(longer_fragments)
        else:
            return False

    return '.'.join(longer_fragments)


def add_to_lists(line):
    package, version = get_version_and_package(line)
    if package:
        if package not in packages:
            packages.append(package)
            versions[package] = version
        else:
            new_version = return_newer_version(
                versions[package], version)
            if new_version:
                versions[package] = new_version
            else:
                logging.info(
                    'version for package {} is unclear, add this package manually'.format(package))

    else:
        irregular_lines.append(line)


def is_num(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def get_version_and_package(line):
    is_valid_line = valid_line_matcher.match(line)
    if is_valid_line:
        package = package_matcher.search(line).group()
        version = version_matcher.search(line).group()

    else:
        package = False
        version = False

    return package, version

create_reqs()