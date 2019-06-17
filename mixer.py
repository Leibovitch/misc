import re
import os
import sys
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
    try:
        with open(file_path):
            os.system('mv ' + file_path + ' ' + path + '/old_reqs.txt')
            os.system('pipreqs ' + path)
            os.system('mv ' + file_path + ' ' + path + '/pip_reqs.txt')
            mixer(path + '/old_reqs.txt', path + '/pip_reqs.txt')
            os.system('rm ' + path + '/pip_reqs.txt')
            # os.system('rm ' +   path + '/old_reqs.txt')
    except Exception as e:
        print(e)
        os.system('pipreqs ' + path)
    

def mixer(path1, path2):
    print('mixer running')
    with open(path1) as fp1, open(path2) as fp2:
        line1 = fp1.readline()[0:-1]
        while line1:
            add_to_lists(line1)
            line1 = fp1.readline()[0:-1]
        
        line2 = fp2.readline()[0:-1]
        while line2:
            add_to_lists(line2)
            line2 = fp2.readline()[0:-1]

    write_packages_to_files('/'.join(path1.split('/')[0:-1]))


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