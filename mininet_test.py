#!/usr/bin/python
import sys
import os
from time import sleep
from math import sqrt
import argparse
from subprocess import Popen, PIPE
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.log import lg
from mininet.cli import CLI


"""
bandwidth: Mbps
delay: ms, 1-way
loss rate: 0-100
queue size: # packets
"""
links = [
		[10, 100, 0.1, 400],
		[10, 100, 0.1, 400]
]

class TwoHostNLink(Topo):
	def __init__(self, **opts):
		super(TwoHostNLink, self).__init__(**opts)

		# add switches
		switches = []
		for i in range(len(links)):
			switches.append('s%i' % (i+1))
			self.addSwitch('s%i' % (i+1))

		# add hosts
		self.addHost('h1')
		self.addHost('h2')

		# add links
		for i in range(len(links)):
			bw = links[i][0]
			delay = links[i][1]/2
			loss = (100-sqrt(100-links[i][2]))/100
			qsize = links[i][3]
			self.addLink('h1', switches[i], bw=bw, delay=str(delay)+'ms', loss=loss, max_queue_size=qsize)
			self.addLink('h2', switches[i], bw=bw, delay=str(delay)+'ms', loss=loss, max_queue_size=qsize)

def progress(t):
	while t > 0:
		print "%3d seconds left" % t
		t -= 1
		sleep(1)
	print "\n"

def parse_args():
	parser = argparse.ArgumentParser(description="MPTCP 2-host n-switch test")
	parser.add_argument('--mptcp',
		action="store_true",
		help="Enable MPTCP (net.mptcp.mptcp_enabled)",
		default=False)
	parser.add_argument('--ndiffports',
		action="store",
		help="Set # subflows (net.mptcp.mptcp_ndiffports)",
		default=1)
	parser.add_argument('-t',
		action="store",
		help="Seconds to run the experiment",
		default=2)
	args = parser.parse_args()
	args.ndiffports = int(args.ndiffports)
	return args

def sysctl_set(key, value):
	"""Issue systcl for given param to given value and check for error."""
	p = Popen("sysctl -w %s=%s" % (key, value), shell=True, stdout=PIPE,
						stderr=PIPE)
	# Output should be empty; otherwise, we have an issue.
	stdout, stderr = p.communicate()
	stdout_expected = "%s = %s\n" % (key, value)
	if stdout != stdout_expected:
		raise Exception("Popen returned unexpected stdout: %s != %s" % (stdout, stdout_expected))
	if stderr:
		raise Exception("Popen returned unexpected stderr: %s" % stderr)

def set_mptcp_enabled(enabled):
	"""Enable MPTCP if true, disable if false"""
	e = 1 if enabled else 0
	lg.info("setting MPTCP enabled to %s\n" % e)
	sysctl_set('net.mptcp.mptcp_enabled', e)

def set_mptcp_ndiffports(ports):
	"""Set ndiffports, the number of subflows to instantiate"""
	lg.info("setting MPTCP ndiffports to %s\n" % ports)
	sysctl_set("net.mptcp.mptcp_ndiffports", ports)


def set_mptcp_debug(enabled):
	e = 1 if enabled else 0
	lg.info("setting MPTCP_DEBUG to %s\n" % e)
	sysctl_set('net.mptcp.mptcp_debug', 1)

def set_mptcp_fullmesh():
	lg.info("setting MPTCP PM to fullmesh\n")
	sysctl_set('net.mptcp.mptcp_path_manager', "fullmesh")

def set_mptcp_rr():
	lg.info("setting MPTCP sched to rr")
	sysctl_set('net.mptcp.mptcp_scheduler', 'roundrobin')

def set_mptcp_simple():
	lg.info("setting MPTCP sched to simple")
	sysctl_set('net.mptcp.mptcp_scheduler', 'simple')

def setup(args):
	set_mptcp_enabled(True)
	set_mptcp_debug(True)
	set_mptcp_fullmesh()
	set_mptcp_simple()
	# set_mptcp_rr()
	# set_mptcp_ndiffports(args.ndiffports)

def end(args):
	set_mptcp_enabled(False)
	# set_mptcp_ndiffports(1)

def mptcp_run(net, args):
	h1 = net.getNodeByName('h1')
	h2 = net.getNodeByName('h2')

	for i in range(len(links)):
		# Setup IPs:
		h1.cmdPrint('ifconfig h1-eth%i 10.0.%i.3 netmask 255.255.255.0' % (i, i))
		h2.cmdPrint('ifconfig h2-eth%i 10.0.%i.4 netmask 255.255.255.0' % (i, i))

		if args.mptcp:
			lg.info("configuring source-specific routing tables for MPTCP\n")
			# This creates two different routing tables, that we use based on the
			# source-address.
			dev = 'h1-eth%i' % i
			table = '%s' % (i + 1)
			h1.cmdPrint('ip rule add from 10.0.%i.3 table %s' % (i, table))
			h1.cmdPrint('ip route add 10.0.%i.0/24 dev %s scope link table %s' % (i, dev, table))
			h1.cmdPrint('ip route add default via 10.0.%i.1 dev %s table %s' % (i, dev, table))


def server_run(server_host, eth1, eth2, client_addr):
	lg.info('start server process, pid: %d\n' % os.getpid())
	tcpdump_p = server_host.popen('sudo tcpdump -i any -w server.pcap')
	server_host.sendCmd('nc -l -p 8080 > data_server')

	def wait_and_clean():
		output = server_host.waitOutput()
		lg.info('server nc output: %s\n' % (output))
		tcpdump_p.kill()

	return wait_and_clean


def client_run(client_host, eth1, eth2, server_addr):
	lg.info('start client process, pid: %d\n' % os.getpid())
	client_host.sendCmd('nc %s 8080 < data' % (server_addr))
	output = client_host.waitOutput()
	lg.info('client output: %s\n' % output)


def run(args, net):
	seconds = int(args.t)
	h1 = net.getNodeByName('h1')
	h2 = net.getNodeByName('h2')

	wait_and_clean = server_run(h2, 'h2-eth0', 'h2-eth1', '10.0.0.3')
	client_run(h1, 'h1-eth0', 'h1-eth1', '10.0.0.4')
	wait_and_clean()
	return None

def genericTest(args, topo, setup, run, end):
	net = Mininet(topo=topo, link=TCLink)
	setup(args)
	net.start()
	print("wait for 5 seconds")
	time.sleep(5)
	mptcp_run(net, args)
	# CLI(net)
	data = run(args, net)
	net.stop()
	end(args)
	return data

def main():
	args = parse_args()
	lg.setLogLevel('info')
	topo = TwoHostNLink()
	genericTest(args, topo, setup, run, end)

if __name__ == '__main__':
	main()
