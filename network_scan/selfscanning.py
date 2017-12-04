import datetime
import pymysql
from time import sleep
import socket
from uuid import getnode as get_mac
import platform
import subprocess
import os
from collections import defaultdict
import ctypes

HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

conn = pymysql.connect(host = , port = , user = , password = ,
					   db = , charset = 'utf8')

def isroot():
	try:
		is_admin = os.getuid() == 0
	except AttributeError:
		is_admin = ctypes.windll.shell32.IsUserAnAdmin()

	return is_admin

def getIPaddr():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	ipaddr = s.getsockname()[0]

	return ipaddr

def shell(code):
	output = subprocess.check_output(code,shell=True)
	return output

def getMACaddr():
	MAC = get_mac()
	MAC = ':'.join(("%012X" % MAC)[i:i + 2] for i in range(0, 12, 2))

	return MAC

def getVersionInfoW(process):
	try:
		Path = shell("wmic process where name='" + process + "' get ExecutablePath")
	except:
		return None
	path=""
	for data in Path.replace('\r', '').split('\n')[1:]:
		if data:
			if len(data.replace(' ', '')) > 0:
				path = data
				break
#### ------ Version ------ ####
	if path:
		path = path.replace('\\', '\\\\')
		try:
			version = shell("wmic datafile where name='" + path + "' get version")
			return version.split()[1]
		except:
			return None
	return None

def getVersionInfoL(pid):
	try:
		path = shell("ps aux | grep "+pid)
		path = path.split()[10]
		package = shell("dpkg-query --search "+path)
		package = package.split(':')[0]
		version = shell("dpkg -s "+package+" | grep Version")
		version = version.split(": ")[1].replace('\n','')
		return version
	except:
		return None

def windows_Scanner(ipaddr,MAC):

	all = defaultdict(lambda:{'target':[],'state':[],'port':[],'protocol':[],'service':None,'version':None})

	### netstat ###
	packet = shell("netstat -ano")
	lines = packet.split('\n')
	allpid=set()
	for line in lines:
		if line[4:5]=='P':
			data = line.split()
			ipport = data[1].split(':')
			if ipport[0] == '0.0.0.0':
				target = 'all'
			elif ipport[0] == '127.0.0.1' or ipport[0]=='127.0.1.1':
				target = 'localhost'
			else:
				target = 'else'
			port = int(ipport[-1])
			if data[0]=='TCP':
				pid = data[4]
				all[pid]['target'].append(target)
				all[pid]['state'].append(data[3])
				all[pid]['port'].append(port)
				all[pid]['protocol'].append('TCP')
			else:
				#UDP
				pid = data[3]
				all[pid]['target'].append(target)
				all[pid]['port'].append(port)
				all[pid]['state'].append(None)
				all[pid]['protocol'].append('UDP')
			allpid.add(pid)
	#### ----- netstat done ----- ####

	###tasklist /SVC ----- process name from pid###
	process = defaultdict(lambda:{'process':None, 'version':None})
	tasklist = shell("tasklist /SVC")
	lines = tasklist.split('\n')
	port_proc = set()
	for line in lines:
		data = line.split()
		try:
			pid = data[1]
			process[pid]['process']=data[0]
		except:
			continue
	for pid in process.keys():
		version = getVersionInfoW(process[pid]['process'])
		process[pid]['version']=version

	db = conn.cursor()
	db.execute("DELETE FROM NW_SCAN_SVC WHERE MACaddr='"+MAC+"'")
	db.close()
	conn.commit()
	for pid in all.keys():
		proc = process[pid]['process']
		if proc:
			all[pid]['service'] = proc.split('.')[0]
			all[pid]['version'] = process[pid]['version']
		now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		for idx, protocol in enumerate(all[pid]['protocol']):
			datas = [MAC, ipaddr, now, protocol, all[pid]['port'][idx], all[pid]['state'][idx], all[pid]['target'][idx], all[pid]['service'],all[pid]['version']]
			sql_t = ""
			for d in datas:
				if not d:
					sql_t += 'Null,'
				else:
					sql_t += "\"" + str(d) + "\","

			sql = "INSERT INTO NW_SCAN_SVC VALUES(" + sql_t[:-1] + ")"
			db = conn.cursor()
			db.execute(sql)
			db.close()
		conn.commit()

	### Except port based pid ###
	procset=set()
	for pid in process.keys():
		proc = process[pid]['process']
		version = process[pid]['version']
		if pid not in allpid:
			if proc in procset:
				continue
			else:
				if version:

					print MAC, ipaddr, 'JUST_PROCESS', proc.split('.')[0], process[pid]['version']
			procset.add(proc)

def linux_Scanner(ipaddr,MAC):

	# all = defaultdict(lambda: {'target':[], 'state': [], 'port': [], 'protocol': [],'service':None,'version':None})
	netstat = shell("sudo netstat -atulvnp")
	lines = netstat.split('\n')


	db = conn.cursor()
	db.execute("DELETE FROM NW_SCAN_SVC WHERE MACaddr='"+MAC+"'")
	db.close()
	conn.commit()

	for line in lines:
		data = line.split()
		try:
			check = data[0][2]
		except:
			continue
		if check=='p':
			protocol=data[0]
			state = None
			ipport = data[3].split(':')
			if ipport[0]=='127.0.1.1' or ipport[0]=='127.0.0.1':
				target='localhost'
			elif ipport[0]=='0.0.0.0':
				target='all'
			else:
				target='else'
			port = ipport[-1]
			if data[0][0]=='t':
				#TCP
				state = data[5]
				t = data[-1].split('/')
			else:
				t = data[5].split('/')
			try:
				pid = t[0]
				proc = t[1]
				version = getVersionInfoL(pid)
			except:
				pid = -1
				proc = None
				version = None

			now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			datas = [MAC, ipaddr, now, protocol, port, state, target, proc, version]
			sql_t = ""
			for d in datas:
				if not d:
					sql_t += 'Null,'
				else:
					sql_t += "\"" + str(d) + "\","

			sql = "INSERT INTO NW_SCAN_SVC VALUES(" + sql_t[:-1] + ")"
			db = conn.cursor()
			db.execute(sql)
			db.close()
		conn.commit()

	return

if __name__ == "__main__":

	if not isroot():
		print FAIL + "No root!!" + ENDC
		exit()

	OS = platform.uname()
	MAC = getMACaddr()
	ipaddr = getIPaddr()

	if OS[0].lower()=='windows':
		OS_ver = shell("ver")
		OS_ver = OS_ver.split('Version ')[-1].replace(']','')
		db = conn.cursor()
		now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

		db.execute("DELETE FROM NW_SCAN_OS WHERE MACaddr='" + MAC + "'")
		db.execute("INSERT INTO NW_SCAN_OS VALUES('"+MAC+"','"+ipaddr+"','"+now+"','Windows "+OS_ver+"')")
		db.close()
		conn.commit()
		windows_Scanner(ipaddr, MAC)
	else:
		print MAC,ipaddr, platform.platform()
		db = conn.cursor()
		now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		db.execute("DELETE FROM NW_SCAN_OS WHERE MACaddr='" + MAC + "'")
		db.execute("INSERT INTO NW_SCAN_OS VALUES('" + MAC + "','" + ipaddr + "','" + now + "','"+ platform.platform() + "')")
		db.close()
		conn.commit()
		linux_Scanner(ipaddr, MAC)

	conn.close()


