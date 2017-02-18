#!/usr/bin/python
# encoding: utf-8
from subprocess import check_output, call, check_call
import os
import glob

MPTCP_BASE = '/home/luoy/mptcp/mptcp_src'

def update_files():
    for f in glob.glob('include/net/*'):
        f = f.replace('\\', '/')
        cmd = ['scp', f, 'mininet@mininet:mptcp/include/net/']
        print cmd
        check_output(cmd)
    for f in glob.glob('net/mptcp/*'):
        f = f.replace('\\', '/')
        cmd = ['scp', f, 'mininet@mininet:mptcp/net/mptcp/']
        print cmd
        check_output(cmd)

   
def build_deb():
    cwd = os.getcwd()
    try:
        os.chdir(MPTCP_BASE)
        env = os.environ.copy()
        env['CONCURRENCY_LEVEL'] = '4'
        call(['fakeroot', 'make-kpkg', '--initrd', 'linux_image'], env=env)
    except:
        raise
    finally:
        os.chdir(cwd)

def copy_and_install_image():
    deb_path = os.path.join(MPTCP_BASE, '..', 'linux-image-3.18.20+_3.18.20+-10.00.Custom_amd64.deb')
    check_call(['cp', deb_path, '.'])
    check_call(['scp', 'linux-image-3.18.20+_3.18.20+-10.00.Custom_amd64.deb', 'mininet@mininet:'])
    # check_call(['ssh', 'mininet@mininet', 'sudo dpkg -i linux-image-3.18.20+_3.18.20+-10.00.Custom_amd64.deb'])
    # check_call(['ssh', 'mininet@mininet', 'sudo reboot'])


if __name__ == '__main__':
    update_files()
    # build_deb()
    # copy_and_install_image()