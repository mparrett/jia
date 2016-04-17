#!/usr/bin/env python -u

"""jia - Simple Shell Script Provisioner

Usage:
    jia.py configure (--def=<def>) (--host=<host>) [--port=<port>] [--user=<user>] [--key=<key>] [--pass=<pass>] [--vars=<vars>] [--match=<match>] [-v]
    jia.py -h|--help

Options:
    -h --help                   Show this screen.
    -v --verbose                Be more verbose.
    --port=<port>               SSH Port [default: 22].
    --user=<user>               SSH User [default: root].
    --key=<key>                 SSH Key.
    --host=<host>               Server host.
    --def=<def>                 Server definition.
    --vars=<vars>               YML file containing template variables.
    --match=<match>             Only run scripts that match specified pattern.
"""

import os
import sys
import yaml
import signal
import time
import re

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

args = docopt(__doc__, version='0.9')


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
    cmd = "cd /tmp/jia-py && tar -czf {} {}".format(filename, ' '.join(files))
    return call(cmd, shell=True)


def extract_remote_archive(filename):
    ssh_command("cd /tmp/jia-py && tar xvfm {}".format(filename))


def cleanup_remote():
    ssh_command("rm -rf /tmp/jia-py")


def cleanup_local():
    call("rm -rf /tmp/jia-py", shell=True)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, sigint_handler)

    try:
        if args['--key']:
            key = os.path.expanduser(args['--key'])
            ssh.connect(args['--host'], int(args['--port']), args['--user'], key_filename=key, timeout=5)
        else:
            ssh.connect(args['--host'], int(args['--port']), args['--user'], args['--pass'], timeout=5)
    except Exception as e:
        print "Could not establish a connection to {}:{}".format(args['--host'], args['--port'])
        print e
        sys.exit(1)

    trans = ssh.get_transport()
    chan = trans.open_channel('session')

    try:
        definition = open(os.getcwd() + '/actions/' + args['--def']).read()
    except:
        print "Definition not found: " + args['--def']
        sys.exit(1)

    scp = SCPClient(ssh.get_transport())

    server_def = yaml.load(definition)

    # Let's do some basic checks on the server definition

    if not 'scripts' in server_def:
        print "Server definition missing 'scripts'. Won't do anything!"
        sys.exit(1)

    if 'files' in server_def and server_def['files'] is not None:
        for f in (server_def['files'] + server_def['scripts']):
            if not os.path.isfile(os.getcwd() + '/' + f):
                print "Specified file or script not found: " + os.getcwd() + '/' + f
                sys.exit(1)

    # Now the fun part!
    ret = call('mkdir -p /tmp/jia-py/{files,scripts} >/dev/null 2>&1', shell=True)

    template_vars = {}
    if '--vars' in args:
        try:
            template_vars = yaml.load(open(os.getcwd() + '/vars/' + args['--vars']).read())
        except:
            print 'Specified variables file not found: ' + args['--vars']
            sys.exit(1)

    #pp(template_vars)

    copy_files = []

    # Expand templates
    if 'files' in server_def and server_def['files'] is not None:
        for f in server_def['files']:
            if not f.endswith('.j2'):
                copy_files.append(f)
                continue

            #print "Rendering template {} {} {}".format(f, os.getcwd() + '/' + f, f.replace('.j2', ''))
            print "Rendering template {}".format(f)

            t = Template(open(os.getcwd() + '/' + f).read())
            if not os.path.exists(os.path.dirname('/tmp/jia-py/' + f.replace('.j2', ''))):
                os.makedirs(os.path.dirname('/tmp/jia-py/' + f.replace('.j2', '')))
            open('/tmp/jia-py/' + f.replace('.j2', ''), 'w').write(t.render(template_vars))

            copy_files.append(f.replace('.j2', ''))


    # Copy everything to /tmp for packaging
    call("cp -R {files,scripts} /tmp/jia-py", shell=True)

    # Package it up
    filename = 'jia-py.tar.gz';
    ret = create_local_archive(filename, server_def['scripts'] + copy_files)

    if ret != 0:
        print "Could not create local archive"
        sys.exit(ret)

    ssh_command('mkdir /tmp/jia-py >/dev/null 2>&1')
    scp.put('/tmp/jia-py/' + filename, '/tmp/jia-py/' + filename)
    extract_remote_archive('/tmp/jia-py/' + filename)

    # NOW RUN THE SCRIPTS!

    for script in server_def['scripts']:
        if not args['--match'] or re.search(args['--match'], script) is not None:
            ssh_command('DEBIAN_FRONTEND=noninteractive PYFSSTMP=/tmp/jia-py {}'.format('/tmp/jia-py/' + script))

    cleanup_remote()
    cleanup_local()

    sys.exit(0)
