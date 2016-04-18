#!/usr/bin/env python -u 
"""jia - Simple Shell Script Provisioner

Usage:
    jia.py configure <def-dir> [options] 
    jia.py -h|--help

Options:
    -h --help                   Show this screen.
    -v --verbose                Be more verbose.
    --host=<host>               Remote host to run commands on.
    --def-file=<def-file>       Definition file [default: main.yaml].
    -p --port=<port>            SSH Port [default: 22].
    -u --user=<user>            SSH User [default: vagrant].
    --pass=<pass>               SSH Password.
    -k --key=<key>              SSH Key [default: ~/.vagrant.d/insecure_private_key].
    --vars=<vars>               YAML file containing template variables.
    --match=<match>             Only run scripts matching specified pattern.
"""

import os
import stat
import sys
import yaml
import signal
import time
import re

from jia import __version__

from paramiko import SSHClient, AutoAddPolicy, Channel, Transport
from textcolor import textcolor, RED, GREEN, YELLOW
from pprint import pprint as pp

from scp import SCPClient
from docopt import docopt
from subprocess import call
from jinja2 import Template

ssh = SSHClient()
ssh.set_missing_host_key_policy(AutoAddPolicy())
trans = None
chan = None

args = docopt(__doc__, version=__version__)


def sigint_handler(signum, frame):
    print "\n"
    print "Bye-bye"
    sys.exit(1)


def ssh_command(cmd):
    if args['--verbose']:
        print 'SSH> ' + cmd

    stdin, stdout, stderr = ssh.exec_command(cmd)

    if args['--verbose']:

        #read_data = stdout.read()
        #print read_data

        #read_data = stderr.read()
        #print read_data

        outlines = stdout.readlines()

        if len(outlines) > 0:
            print textcolor("SSH<\n" + "".join(outlines), GREEN)

        errlines = stderr.readlines()

        if len(errlines) > 0:
            print textcolor("SSH<\n" + "".join(errlines), RED)

    return [stdin, stdout, stderr]


def create_local_archive(filename, files):
    if args['--verbose']:
        tar_opts = '-czvf'
    else:
        tar_opts = '-cvf'

    cmd = "cd /tmp/jia-py && tar {} {} {}".format(tar_opts, filename, ' '.join(files))
    return call(cmd, shell=True)


def extract_remote_archive(filename):
    ssh_command("cd /tmp/jia-py && tar xvfm {}".format(filename))


def cleanup_remote():
    ssh_command("rm -rf /tmp/jia-py")


def cleanup_local():
    call("rm -rf /tmp/jia-py", shell=True)


def ssh_connect():
    # Priority: CLI, environment, Vagrant
    key_file = args['--key'] or os.getenv('SSH_PRIVATE_KEY')

    if args['--verbose']:
        print "Using key file: {}".format(key_file)
        print "Connecting to {}:{}".format(args['--host'], args['--port'])

    key_file = os.path.expanduser(key_file)
    if not os.path.isfile(key_file):
        print "Error: Private key file does not exist: {}".format(key_file)
        sys.exit(1)

    ssh.connect(args['--host'], int(args['--port']), args['--user'], key_filename=key_file, timeout=5)


if __name__ == '__main__':

    signal.signal(signal.SIGINT, sigint_handler)

    server_def_dir = args['<def-dir>']

    if not os.path.isdir(server_def_dir):
        print 'Error: Def dir needs to be a directory'
        sys.exit(1)

    def_file_path = server_def_dir + '/' + args['--def-file']
    if not os.path.isfile(def_file_path):
        print 'Error: Definition file ' + def_file_path + ' does not exist'
        sys.exit(1)

    try:
        definition = open(def_file_path).read()
    except:
        print "Couldn't read def file: {}".format(def_file_path)
        sys.exit(1)

    if args['--host']:
        try:
            ssh_connect()
        except Exception as e:
            print "Error: Couldn't establish connection to {}:{}\n{}".format(args['--host'], args['--port'], e)
            sys.exit(1)

        trans = ssh.get_transport()
        chan = trans.open_channel('session')

        scp = SCPClient(ssh.get_transport())

    server_def = yaml.load(definition)

    # Do some basic checks on the server definition

    if not 'scripts' in server_def:
        print "WARNING: Server definition missing 'scripts'. Won't run anything!"

    all_files_and_scripts = (
            ['files/' + f for f in server_def['files']] + 
            ['scripts/' + f for f in server_def['scripts']]
    )

    if 'files' in server_def and server_def['files'] is not None:
        for f in all_files_and_scripts:
            if not os.path.isfile(server_def_dir + '/' + f):
                print "Error: File or script not found: " + os.getcwd() + '/' + f
                sys.exit(1)

    # Now the fun part: Build the package!

    ret = call('mkdir -p /tmp/jia-py/{files,scripts} >/dev/null 2>&1', shell=True)

    template_vars = {}

    if server_def['vars']:
        template_vars = server_def['vars']
    pp(template_vars)

    # possibly override
    if '--vars' in args and args['--vars']:
        yaml_file = os.getcwd() + '/vars/' + args['--vars']
        if not os.path.isfile(yaml_file):
            print 'Error: Variables file not found: {}'.format(args['--vars'])
            sys.exit(1)

        try:
            template_vars_override = yaml.load(open(yaml_file).read())
            template_vars.update(template_vars_override)
        except:
            print 'Error: Failed parsing YAML: {}'.format(args['--vars'])
            sys.exit(1)

    pp(template_vars)

    copy_files = []


    # Expand templates
    if 'files' in server_def and server_def['files'] is not None:
        for f in server_def['files']:
            if not f.endswith('.j2'):
                copy_files.append('files/' + f)
                continue

            if args['--verbose']:
                #print "Rendering template {} {} {}".format(f, os.getcwd() + '/' + f, f.replace('.j2', ''))
                print "Rendering template {}".format(f)

            t = Template(open(server_def_dir + '/files/' + f).read())

            template_file_dir = os.path.dirname('/tmp/jia-py/' + f.replace('.j2', ''))

            if not os.path.exists(template_file_dir):
                os.makedirs(template_file_dir)

            open('/tmp/jia-py/files/' + f.replace('.j2', ''), 'w').write(t.render(template_vars))

            copy_files.append('files/' + f.replace('.j2', ''))


    # Copy everything to /tmp for packaging
    call("cp -Rv " + server_def_dir + "/ /tmp/jia-py/", shell=True)

    cmds = []
    for script in server_def['scripts']:
        if not args['--match'] or re.search(args['--match'], script) is not None:
            cmd = ''
            if args['--host']:
                cmd = 'DEBIAN_FRONTEND=noninteractive PYFSSTMP=/tmp/jia-py '
            cmd = cmd + '{}'.format('/tmp/jia-py/' + script)
            cmds.append(cmd)

    with open('/tmp/jia-py/configure.sh', 'w') as f:
        f.write("#!/bin/bash\n")
        f.write("DEBIAN_FRONTEND=noninteractive\n")
        f.write("PYFSSTMP=/tmp/jia-py\n")
        f.write("\n# commands:\n")
        f.write("".join(cmds) + "\n")

    os.chmod('/tmp/jia-py/configure.sh', 0744)

    # Package everything up
    filename = 'jia-py.tar.gz';
    all_files = ['scripts/' + f for f in server_def['scripts']] + copy_files
    ret = create_local_archive(filename, all_files)

    if ret != 0:
        print "Error: Could not create local archive"
        sys.exit(ret)

    if args['--host']:
        ssh_command('mkdir /tmp/jia-py >/dev/null 2>&1')
        scp.put('/tmp/jia-py/' + filename, '/tmp/jia-py/' + filename)
        extract_remote_archive('/tmp/jia-py/' + filename)
        # Now run the scripts
        for cmd in cmds:
                ssh_command(cmd)

        cleanup_remote()
        cleanup_local()
    else:
        if args['--verbose']:
            print "Creating local archive only"

    sys.exit(0)
