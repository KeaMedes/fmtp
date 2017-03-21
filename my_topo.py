from mininet.net import Mininet
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.log import lg
from mininet.cli import CLI

"""
        s1
h1              h2
        s2
"""
class MyTopo(Topo):
	"2-host-2-switch-double-links topo"

	def build(self):
		h1 = self.addHost('h1')
		h2 = self.addHost('h2')
		s1 = self.addSwitch('s1')
		s2 = self.addSwitch('s2')

		# bandwidth(Mbps), delay(ms), loss rate, queue size(packtes)
		link_h1_s1 = [20, 10, 9, 400]
		link_h1_s2 = [10, 10, 1, 400]
		link_h2_s1 = [10, 10, 1, 400]
		link_h2_s2 = [10, 10, 1, 400]

		self.addLink(h1, s1, bw=link_h1_s1[0], delay=str(link_h1_s1[1])+'ms', loss=link_h1_s1[2], max_queue_size=link_h1_s1[3])
		self.addLink(h1, s2, bw=link_h1_s2[0], delay=str(link_h1_s2[1])+'ms', loss=link_h1_s2[2], max_queue_size=link_h1_s2[3])
		self.addLink(h2, s1, bw=link_h2_s1[0], delay=str(link_h2_s1[1])+'ms', loss=link_h2_s1[2], max_queue_size=link_h2_s1[3])
		self.addLink(h2, s2, bw=link_h2_s2[0], delay=str(link_h2_s2[1])+'ms', loss=link_h2_s2[2], max_queue_size=link_h2_s2[3])

topos = {'mytopo': (lambda: MyTopo())}

def set_ip(net):
	h1 = net.getNodeByName('h1')
	h1.setIP(intf='h1-eth0', ip='10.10.0.1')
	h1.setIP(intf='h1-eth1', ip='10.10.0.2')
	h2 = net.getNodeByName('h2')
	h2.setIP(intf='h2-eth0', ip='10.10.0.3')
	h2.setIP(intf='h2-eth1', ip='10.10.0.4')

def set_route(net):
	h1 = net.getNodeByName('h1')
	h2 = net.getNodeByName('h2')

	h1_cmds = [
	'ip rule add from 10.10.0.1 table 1',
	'ip rule add from 10.10.0.2 table 2',
	'ip route add 10.10.0.1 dev h1-eth0 scope link table 1',
	'ip route add 10.10.0.2 dev h1-eth1 scope link table 2']
	h2_cmds = [
	'ip rule add from 10.10.0.3 table 1',
	'ip rule add from 10.10.0.4 table 2',
	'ip route add 10.10.0.3 dev h1-eth0 scope link table 1',
	'ip route add 10.10.0.4 dev h1-eth1 scope link table 2']

	for cmd in h1_cmds:
		h1.cmdPrint(cmd)
	for cmd in h2_cmds:
		h2.cmdPrint(cmd)

def set_all(net):
	lg.info("setIp\n")
	set_ip(net)
	lg.info("setRoute\n")
	set_route(net)

def create_file(f_size):
	import random
	import string
	lg.info("creating file test_data with size of %d KB\n" % (f_size))
	char_list = string.printable
	with open('test_data', 'wb') as fout:
		for i in range(0, f_size * 1024):
			fout.write(random.choice(char_list))

def run_test(net):
	from time import sleep
	h_clinet = net.getNodeByName('h1')
	h_server = net.getNodeByName('h2')

	lg.info("start server process\n")
	tcpdump_p = h_server.popen("sudo tcpdump -i any -w server_trace.pcap")
	lg.info("sleep 1 second before start the server process\n")
	sleep(1)
	h_server.sendCmd("nc -l -p 8080 > test_data_dump")

	lg.info("start client process\n")
	h_clinet.sendCmd("nc 10.10.0.3 8080 < test_data")
	lg.info(h_clinet.waitOutput())
	lg.info("client done\n")

	lg.info(h_server.waitOutput())
	lg.info("sleep 1 second before closing the tcpdump process\n")
	sleep(1)
	tcpdump_p.kill()
	lg.info("server done\n")

def set_ip_wrapper(self, line):
	set_ip(self.mn)

def set_route_wrapper(self, line):
	set_route(self.mn)

def set_all_wrapper(self, line):
	set_all(self.mn)

def create_file_wrapper(self, line):
	f_size = int(line)
	create_file(f_size)

def run_test_wrapper(self, line):
	run_test(self.mn)

CLI.do_setIp = set_ip_wrapper
CLI.do_setRoute = set_route_wrapper
CLI.do_setAll = set_all_wrapper
CLI.do_createFile = create_file_wrapper
CLI.do_runTest = run_test_wrapper

def main():
	print("run the scripts in pure python environment")
	print("create and start net")
	net = Mininet(topo = MyTopo(), link=TCLink)
	net.start()
	print("setup the ip and route table")
	set_all(net)
	print("run tests")
	run_test(net)
	print("stop the net")
	net.stop()

if __name__ == '__main__':
	main()
