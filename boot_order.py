#!/usr/bin/python3

import argparse
import subprocess
import time
import sys
from xml.dom import minidom
import tempfile


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vm', type=str, help='Domain (VM) name or ID', required=True)
    order_group = parser.add_mutually_exclusive_group(required=True)
    order_group.add_argument('--hd', action='store_true', help='Boot from HDD first', default=False)
    order_group.add_argument('--cd', action='store_true', help='Boot from CD first', default=False)
    return parser.parse_args()


def virsh(*varargs):
    cmd = list(varargs)
    cmd.insert(0, 'virsh')
    return subprocess.check_output(cmd, timeout=20).decode('utf-8').strip()


def get_name(vm_id):
    return virsh('domname', vm_id)


def shutdown(vm_name):
    virsh('shutdown', vm_name)

    for _ in range(0, 12):
        if virsh('domstate', vm_name) == 'shut off':
            return
        time.sleep(10)

    raise TimeoutError(f'Shutting down \'{vm_name}\' took too long')


def set_order(vm_name, cd_first=False):

    definition = virsh('dumpxml', '--inactive', '--security-info', vm_name)
    dom = minidom.parseString(definition)
    os_element = dom.getElementsByTagName('os')[0]

    for child in os_element.getElementsByTagName('boot'):
        if child.getAttribute('dev') in ['cdrom', 'hd']:
            os_element.removeChild(child)

    first = dom.createElement('boot')
    first.setAttribute('dev', 'cdrom' if cd_first else 'hd')
    os_element.appendChild(first)

    second = dom.createElement('boot')
    second.setAttribute('dev', 'hd' if cd_first else 'cdrom')
    os_element.appendChild(second)

    return dom.toprettyxml()


def define(content):
    with tempfile.NamedTemporaryFile() as f:
        f.write(content.encode())
        f.seek(0)
        virsh('define', f.name)


def boot(vm_name):
    return virsh('start', vm_name)


if __name__ == '__main__':
    args = get_args()
    try:
        vm = get_name(args.vm) if args.vm.isdigit() else args.vm
        shutdown(vm)
        xml = set_order(vm, args.cd)
        define(xml)
        boot(vm)
    except Exception as e:
        print(e, file=sys.stderr)
        exit(1)
