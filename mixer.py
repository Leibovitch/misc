import re
import os
import sys
from pathlib import Path
import logging
import subprocess
from pandas import DataFrame as df
from shutil import move
from termcolor import colored
import geoplot


logging.getLogger().setLevel(logging.INFO)
valid_line_matcher = re.compile(r'^[-\w]+={2}(\d+\.)+\d+(\.\w+)?$')
version_matcher = re.compile(r'(?<===)(\d+\.)+\d+(\.\w+)?$')
package_matcher = re.compile(r'^[-\w]+')


def update_setup(path, packages):
    #assumes the file exists
    setup_path = path + '/setup.py'
    move(setup_path , path + '/old_setup.py')
    with open(path + '/old_setup.py', 'r') as sp, open(setup_path, 'w+') as ns:
        line = sp.readline()
        while not re.compile(r'install_requires').search(line):
            ns.write(line)
            line = sp.readline()

        ns.write("install_requires = [\'" + "\',\'".join(packages) + "\'])")
        # ns.write(line)
        # for package in packages[0:-1]:
        #     ns.write(package + ',\n')
            
        # ns.write(packages[-1] + '\n')
        # line = sp.readline()
        # while line:
        #     ns.write(line)
        #     line = sp.readline()


def write_packages_to_files(path, packages: dict, irregs: set):
    with open(path + '/requirements.txt', 'w+') as req:
        for irreg_line in irregs:
            req.write(irreg_line + '\n')

        for package, version in packages.items():
            req.write('{}=={}'.format(package, version) + '\n')


def return_newer_version(competitor_version: str, holding_version: str) -> (str, str):
    if competitor_version == holding_version:
        return (competitor_version, holding_version)
        
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
                winner = '.'.join(shorter_fragments)
                loser = '.'.join(longer_fragments)
                return (winner, loser)

            elif int(fragment) < int(longer_fragments[i]):
                winner = '.'.join(longer_fragments)
                loser = '.'.join(shorter_fragments)
                return (winner, loser)
        else:
            print('there\'s an error with version comprehention. versions are {}, {}'.format(competitor_version, holding_version))
            return ('', '')

    # if i got here the versions are the same
    winner = '.'.join(longer_fragments)
    loser = '.'.join(shorter_fragments)
    return (winner, loser)


def is_num(s) -> bool:
    try:
        int(s)
        return True
    except ValueError:
        return False


def get_version_and_package(line: str) -> (str, str):
    is_valid_line = valid_line_matcher.match(line)
    if is_valid_line:
        package = package_matcher.search(line).group()
        version = version_matcher.search(line).group()

    else:
        package = line
        version = 'irreg'

    return package, version


def dict_fill_lists(path: str) -> dict:
    packages_in_path = {}
    with open(path) as fp:
        line = fp.readline()[0:-1]
        while line:
            package, version = get_version_and_package(line)
            if version != 'irreg':
                packages_in_path[package] = version
            line = fp.readline()[0:-1]

    return packages_in_path

# print(df_fill_lists('./misc/requirements.txt'))

def mixer(path):
    mixed_dict = {}

    existing_dict = dict_fill_lists(path + '/old_reqs.txt')
    existing_irreg_set = {key for (key, value) in existing_dict.items() if value == 'irreg'}
    existing_package_set = {key for (key, value) in existing_dict.items() if value != 'irreg'}

    competitor_dict = dict_fill_lists(path + '/pip_reqs.txt')
    competitor_irreg_set = {key for (key, value) in competitor_dict.items() if value == 'irreg'}
    competitor_package_set = {key for (key, value) in competitor_dict.items() if value != 'irreg'}

    shared_packages = existing_package_set.intersection(competitor_package_set)
    competitor_exclusives = competitor_package_set.difference(existing_package_set)
    existing_exclusives = existing_package_set.difference(competitor_package_set)
    irreg = existing_irreg_set.union(competitor_irreg_set)

    print('The following packages were added: ')
    for new_pack in competitor_exclusives:
        mixed_dict[new_pack] = competitor_dict[new_pack]
        print(colored(new_pack + '\n', 'green'))

    print('The following packages seem to have been removed: ')
    for removed_pack in existing_exclusives:
        yn = input(colored('Do you wan\'t to remove {}? [y/n]'.format(removed_pack), 'red'))
        while yn != 'y' and yn != 'n':
            yn = input('[y/n]')
        
        if yn == 'y':
            existing_exclusives.remove(removed_pack)

    for shared_pack in shared_packages:
        existing_version = existing_dict[shared_pack]
        competitor_version = competitor_dict[shared_pack]
        (newer_version, older_version) = return_newer_version(competitor_version, existing_version)
        if newer_version != older_version:
            yn = input('Package version seems to have changed. would you like to update from {} to {}?'.format(newer_version, older_version))
            
            while yn != 'y' and yn != 'n':
                yn = input('Listen here... you can answer only y or n. i\'ll keep annoying you if you enter something else')

            if yn == 'y':
                mixed_dict[shared_pack] = newer_version

            elif yn == 'n':
                mixed_dict[shared_pack] = older_version

    return mixed_dict, irreg


def create_reqs():
    path = sys.argv[1]
    file_path = path + '/requirements.txt'
    
    if Path(file_path).exists():
        move(file_path, path + '/old_reqs.txt')
        os.system('pipreqs ' + path)
        move(file_path, path + '/pip_reqs.txt')
        (mixed, irreg) = mixer(path)
        write_packages_to_files(path, mixed, irreg)
    else:
        os.system('pipreqs ' + path)
        packeges = dict_fill_lists(path + '/requirements.txt')
        mixed = {key: value for (key, value) in packeges.items() if value != 'irreg'}

    

    res = input("Do you want to amend setup.py? [y/n] \n")
    while res != 'y' and res != 'n':
        res = input("[y/n]")

    if res == 'y':
        update_setup(path, list(mixed.keys()))

create_reqs()