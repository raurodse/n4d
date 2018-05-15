import json
import os.path
import os
import time
import xmlrpclib
import socket
import netifaces
import re
import importlib
import sys
import tarfile
import threading
import subprocess
import time
import string

class VariablesManager:

	VARIABLES_FILE="/var/lib/n4d/variables"
	VARIABLES_DIR="/var/lib/n4d/variables-dir/"
	LOCK_FILE="/tmp/.llxvarlock"
	INBOX="/var/lib/n4d/variables-inbox/"
	TRASH="/var/lib/n4d/variables-trash/"
	CUSTOM_INSTALLATION_DIR="/usr/share/n4d/variablesmanager-funcs/"
	LOG="/var/log/n4d/variables-manager"
	
	def __init__(self):
		
		self.instance_id="".join(random.sample(string.letters+string.digits, 50))
		self.server_instance_id=None
		self.variables={}
		self.variables_ok=False
		self.variables_clients={}
		self.variables_triggers={}
		self.failed_servers={}
		t=threading.Thread(target=self.check_clients,args=())
		t.daemon=True
		t.start()
		
		if os.path.exists(VariablesManager.LOCK_FILE):
			os.remove(VariablesManager.LOCK_FILE)
			
			
		if os.path.exists(VariablesManager.VARIABLES_FILE):
			self.variables_ok,ret=self.load_json(VariablesManager.VARIABLES_FILE)
			try:
				os.remove(VariablesManager.VARIABLES_FILE)
			except:
				pass
		else:
			self.variables_ok,ret=self.load_json(None)
			
		if self.variables_ok:
			#print "\nVARIABLES FILE"
			#print "=============================="
			#self.listvars()
			self.read_inbox(False)
			#print "\nAFTER INBOX"
			#print "=============================="
			#print self.listvars(True)
			self.empty_trash(False)
			#print "\nAFTER TRASH"
			#print "=============================="
			#print self.listvars(True)
			self.add_volatile_info()
			self.write_file()
		else:
			print("[VariablesManager] Loading variables failed because: " + str(ret))

		
	#def __init__
	
	
	def startup(self,options):

		if "REMOTE_VARIABLES_SERVER" in self.variables:
			t=threading.Thread(target=self.register_n4d_instance_to_server)
			t.daemon=True
			t.start()
			
	#def startup
	
	
	def is_ip_in_range(self,ip,network):
		
		try:
			return netaddr.ip.IPAddress(ip) in netaddr.IPNetwork(network).iter_hosts()
		except:
			return False
			
	#def is_ip_in_range
	

	def get_net_size(self,netmask):
		
		netmask=netmask.split(".")
		binary_str=""
		for octet in netmask:
			binary_str += bin(int(octet))[2:].zfill(8)
			
		return str(len(binary_str.rstrip('0')))
		
	#def get_net_size


	def get_ip(self):
		
		for item in netifaces.interfaces():
			tmp=netifaces.ifaddresses(item)
			if tmp.has_key(netifaces.AF_INET):
				if tmp[netifaces.AF_INET][0].has_key("broadcast") and tmp[netifaces.AF_INET][0]["broadcast"]=="10.0.2.255":
					return tmp[netifaces.AF_INET][0]["addr"]
		return None
		
	#def get_ip
	

	def route_get_ip(self,ip):
		
		p=subprocess.Popen(["ip route get %s"%ip],shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
		if "dev" in p[0]:
			dev=p[0].split("dev ")[1].split(" ")[0]
		else:
			dev=None
		return dev
		
	#def route_get_ip
		

	def get_mac_from_device(self,dev):

		for item in netifaces.interfaces():
			
			try:
				i=netifaces.ifaddresses(item)
				mac=i[17][0]["addr"]
				broadcast=i[2][0]["broadcast"]
				network=broadcast
				netmask=i[2][0]["netmask"]
				network+="/%s"%self.get_net_size(netmask)
				ip=i[2][0]["addr"]
			except Exception as e:
				continue
			
			if dev=="lo":
				return mac
			
			if item==dev:
				return mac
				
		return None

	#def get_mac_from_device_in_server_network
	
	
	def register_instance(self,autocompleted_secured_ip,mac):

		client={}
		client["last_check"]=int(time.time())
		client["missed_pings"]=0
		client["ip"]=autocompleted_secured_ip
		self.variables_clients[mac]=client
		
		return self.instance_id

	#def register_instance
	

	def register_n4d_instance_to_server(self):
		
		while True:
		
			try:
				server_ip=socket.gethostbyname(self.variables["REMOTE_VARIABLES_SERVER"][u"value"])
				if self.get_ip()!=server_ip:
				
					c=xmlrpclib.ServerProxy("https://%s:9779"%server_ip)
					mac=self.get_mac_from_device(self.route_get_ip(server_ip))
					self.server_instance_id=c.register_instance("","VariablesManager","",mac)
				
			except Exception as e:

				self.server_instance_id=None
				return None
				
			time.sleep(60*3)

	#def register_n4d_instance_to_server
	
	
	def check_clients(self):
		
		while True:
			
			for mac in self.variables_clients:
				
				ip=self.variables_clients[mac]["ip"]
				t=threading.Thread(target=self.check_single_client,args=(mac,ip,))
				t.daemon=True
				t.start()
			
			time.sleep(60*3)
		
		
	#def check_clients

	def manual_client_list_check(self):

		for mac in self.variables_clients:
			ip=self.variables_clients[mac]["ip"]
			t=threading.Thread(target=self.check_single_client,args=(mac,ip,))
			t.daemon=True
			t.start()
			ip=self.variable

	#def manual_client_list_check
	
	
	def check_single_client(self,mac,ip):
		
		max_pings=3
		
		print("[VariablesManager] Checking client { MAC:%s IP:%s } ... "%(mac,ip))
		c=xmlrpclib.ServerProxy("https://%s:9779"%ip)
		try:
			c.get_methods()
			self.variables_clients[mac]["last_check"]=time.time()
			self.variables_clients[mac]["missed_pings"]=0
		except:
			self.variables_clients[mac]["missed_pings"]+=1
			if self.variables_clients[mac]["missed_pings"] >=max_pings:
				print "[VariablesManager] Removing client %s:%s after %s missed pings."%(mac,ip,max_pings)
				self.variables_clients.pop(mac)
		
	#def check_single_client
	
	
	
	def get_client_list(self):
		
		return self.variables_clients
		
	#def get_client_list
	
	def notify_changes(self,variable):
		
		if len(self.variables_clients) > 0:
		
			print "[VariablesManager] Notifying changes... "
			for mac in self.variables_clients:
				
				ip=self.variables_clients[mac]["ip"]
				c=xmlrpclib.ServerProxy("https://%s:9779"%ip)
				try:
					c.server_changed("","VariablesManager","",self.instance_id,variable)
					
				except:
					self.variables_clients[mac]["missed_pings"]+=1
					
				self.variables_clients[mac]["last_check"]=time.time()
		
	#def announce_changes
	
	
	def server_changed(self,autocompleted_server_ip,server_instance_id,variable_name):

		if server_instance_id==self.server_instance_id:

			print "[VariablesManager] Server instance ID validated"
			t=threading.Thread(target=self.execute_trigger,args=(variable_name,))
			t.daemon=True
			t.start()
			
			return True
			
		else:
			
			if autocompleted_server_ip not in self.failed_servers:
				self.failed_servers[autocompleted_server_ip]={}
				self.failed_servers[autocompleted_server_ip]["failed_count"]=0
			
			sleep_time=0.1
			self.failed_servers[autocompleted_server_ip]["failed_count"]+=1
			time.sleep(sleep_time*self.failed_servers[autocompleted_server_ip]["failed_count"])
			return False
		
	#def server_changed
	
	
	def execute_trigger(self,variable_name):
		
		if variable_name in self.variables_triggers:
			for i in self.variables_triggers[variable_name]:
				class_name,function=i
				try:
					print "[VariablesManager] Executing %s.%s trigger..."%(class_name,function.im_func.func_name)
					function(self.get_variable(variable_name))
				except Exception as e:
					print e
		
	#def execute_trigger
	
	
	def register_trigger(self,variable_name,class_name,function):
		
		if variable_name not in self.variables_triggers:
			self.variables_triggers[variable_name]=[]
			
		self.variables_triggers[variable_name].append((class_name,function))
		
	#def register_trigger
	
	
	def backup(self,dir="/backup"):
		
		try:
		
			#file_path=dir+"/"+self.get_time()+"_VariablesManager.tar.gz"
			file_path=dir+"/"+get_backup_name("VariablesManager")
			tar=tarfile.open(file_path,"w:gz")
			tar.add(VariablesManager.VARIABLES_DIR)
			tar.close()
			
			return [True,file_path]
			
		except Exception as e:
			return [False,str(e)]
		
	#def backup

	
	def restore(self,file_path=None):


		if file_path==None:
			for f in sorted(os.listdir("/backup"),reverse=True):
				if "VariablesManager" in f:
					file_path="/backup/"+f
					break

		try:

			if os.path.exists(file_path):
				
				tmp_dir=tempfile.mkdtemp()
				tar=tarfile.open(file_path)
				tar.extractall(tmp_dir)
				tar.close()
				
				if not os.path.exists(VariablesManager.VARIABLES_DIR):
					os.mkdir(VariablesManager.VARIABLES_DIR)
				
				for f in os.listdir(tmp_dir+VariablesManager.VARIABLES_DIR):
					tmp_path=tmp_dir+VariablesManager.VARIABLES_DIR+f
					shutil.copy(tmp_path,VariablesManager.VARIABLES_DIR)
					
				self.load_json(None)
						
				return [True,""]
				
		except Exception as e:
				
			return [False,str(e)]
		
	#def restore
	
	def log(self,txt):
		
		try:
			f=open(VariablesManager.LOG,"a")
			txt=str(txt)
			f.write(txt+"\n")
			f.close()
		except Exception as e:
			pass
		
	#def log
	
	def listvars(self,extra_info=False,custom_dic=None):
		ret=""
		
		try:
		
			if custom_dic==None:
				custom_dic=self.variables
			for variable in custom_dic:
				if type(custom_dic[variable])==type({}) and "root_protected" in custom_dic[variable] and custom_dic[variable]["root_protected"]:
					continue
				value=self.get_variable(variable)
				if value==None:
					continue
				ret+=variable+ "='" + str(value).encode("utf-8") + "';\n"
				if extra_info:
					ret+= "\tDescription: " + self.variables[variable][u"description"] + "\n"
					ret+="\tUsed by:\n"
					for depend in self.variables[variable][u"packages"]:
						ret+= "\t\t" + depend.encode("utf-8") + "\n"
			
			return ret.strip("\n")
		except Exception as e:
			return str(e)
					
	#def listvars
	
	def calculate_variable(self,value):
		
		pattern="_@START@_.*?_@END@_"
		variables=[]
		
		ret=re.findall(pattern,value)
		
		for item in ret:
			tmp=item.replace("_@START@_","")
			tmp=tmp.replace("_@END@_","")
			variables.append(tmp)
		
		for var in variables:
			value=value.replace("_@START@_"+var+"_@END@_",self.get_variable(var))
			
		return value
		
	#def remove_calculated_chars
	
	def add_volatile_info(self):
		
		for item in self.variables:
		
			if not self.variables[item].has_key("volatile"):
				self.variables[item]["volatile"]=False
		
	#def add_volatile_info

	
	def showvars(self,var_list,extra_info=False):
		
		ret=""
		
		for var in var_list:
			ret+=var+"='"
			if self.variables.has_key(var):
				try:
					ret+=self.variables[var][u'value'].encode("utf-8")+"';\n"
				except Exception as e:
					#it's probably something old showvars couldn't have stored anyway
					ret+="';\n"
				if extra_info:
					ret+= "\tDescription: " + self.variables[var][u"description"] + "\n"
					ret+="\tUsed by:\n"
					for depend in self.variables[var][u"packages"]:
						ret+= "\t\t" + depend.encode("utf-8") + "\n"
			else:
				ret+="'\n"
						
		return ret.strip("\n")
		
	#def  showvars

	
	def get_variables(self):

		return self.variables
		
	#def get_variables
		
	
	def load_json(self, file=None):

		self.variables={}
		
		if file!=None:
		
			try:
				
				f=open(file,"r")
				data=json.load(f)
				f.close()
				self.variables=data
				#return [True,""]
				
			except Exception as e:
				print(str(e))
				#return [False,e.message]
				
		for file in os.listdir(VariablesManager.VARIABLES_DIR):
			try:
				sys.stdout.write("\t[VariablesManager] Loading " + file + " ... ")
				f=open(VariablesManager.VARIABLES_DIR+file)	
				data=json.load(f)
				f.close()
				self.variables[file]=data[file]
				print("OK")
			except Exception as e:
				print("FAILED ["+str(e)+"]")
				
		return [True,""]
		
	#def load_json
	
	def read_inbox(self, force_write=False):
		
		
		if self.variables_ok:
		
			if os.path.exists(VariablesManager.INBOX):
				
				for file in os.listdir(VariablesManager.INBOX):
					file_path=VariablesManager.INBOX+file
					print "[VariablesManager] Adding " + file_path + " info..."
					try:
						f=open(file_path,"r")
						data=json.load(f)
						f.close()
						
						for item in data:
							if self.variables.has_key(item):
								for key in data[item].keys():
									if not self.variables[item].has_key(unicode(key)):
										self.variables[item][unicode(key)] = data[item][key]
								if data[item].has_key(unicode('function')):
									self.variables[item][unicode('function')] = data[item][u'function']
								for depend in data[item][u'packages']:
									if depend not in self.variables[item][u'packages']:
										self.variables[item][u'packages'].append(depend)
								
								if "force_update" in data[item] and data[item]["force_update"]:
									self.variables[item][u'value']=data[item][u'value']
							else:
								self.variables[item]=data[item]

					
					except Exception as e:
						print e
						#return [False,e.message]
					os.remove(file_path)
				
				if force_write:
					try:
						self.add_volatile_info()
						self.write_file()
					except Exception as e:
						print(e)
						
		
		return [True,""]
				
	#def read_inbox

	
	def empty_trash(self,force_write=False):
		
		
		if self.variables_ok:
		
			for file in os.listdir(VariablesManager.TRASH):
				file_path=VariablesManager.TRASH+file
				#print "[VariablesManager] Removing " + file_path + " info..."
				try:
					f=open(file_path,"r")
					data=json.load(f)
					f.close()
					
					for item in data:
						if self.variables.has_key(item):
							if data[item][u'packages'][0] in self.variables[item][u'packages']:
								count=0
								for depend in self.variables[item][u'packages']:
									if depend==data[item][u'packages'][0]:
										self.variables[item][u'packages'].pop(count)
										if len(self.variables[item][u'packages'])==0:
											self.variables.pop(item)
										break
									else:
										count+=1
					
				except Exception as e:
					print e
					#return [False,e.message]
					
				os.remove(file_path)
			
			if force_write:
				try:	
					self.write_file()
				except Exception as e:
					print(e)
				
		return [True,'']
			
		
	#def empty_trash
	

	def get_variable_list(self,variable_list,store=False,full_info=False):
		
		ret={}
		if variable_list!=None:
			for item in variable_list:
				try:
					ret[item]=self.get_variable(item,store,full_info)
				except Exception as e:
					print e

		return ret
		
	#def get_variable_list
	

	def get_variable(self,name,store=False,full_info=False,key=None):
	
		global master_password
		
		if name in self.variables and self.variables[name].has_key("root_protected") and self.variables[name]["root_protected"] and key!=master_password:
			return None
			
		if name in self.variables and self.variables[name].has_key("function"):
			try:
				if not full_info:
					if (type(self.variables[name][u"value"])==type("") or  type(self.variables[name][u"value"])==type(u"")) and self.variables[name][u"value"].find("_@START@_")!=-1:
						#print "I have to ask for " + name + " which has value: " + self.variables[name][u'value']
						value=self.calculate_variable(self.variables[name][u"value"])
					else:
						value=self.variables[name][u"value"]

					if type(value)==type(u""):
						try:
							ret=value.encode("utf-8")
							return ret
						except:
							return value
					else:
						return value
				else:
					variable=self.variables[name].copy()
					variable["remote"]=False
					if type(variable[u"value"])==type(""):
						if variable[u"value"].find("_@START@_")!=-1:
							variable["original_value"]=variable[u"value"]
							variable[u"value"]=self.calculate_variable(self.variables[name][u"value"])
							variable["calculated"]=True
					return variable
			except:
				return None
		else:
			if self.variables.has_key("REMOTE_VARIABLES_SERVER") and self.variables["REMOTE_VARIABLES_SERVER"][u"value"]!="" and self.variables["REMOTE_VARIABLES_SERVER"][u"value"]!=None:
				try:
					server_ip=socket.gethostbyname(self.variables["REMOTE_VARIABLES_SERVER"][u"value"])
				except:
					return None
				if self.get_ip()!=server_ip:
					for count in range(0,3):
						try:

							server=xmlrpclib.ServerProxy("https://"+server_ip+":9779",allow_none=True)
							var=server.get_variable("","VariablesManager",name,True,True)
							
							if var==None:
								return None
							if (var!=""  or type(var)!=type("")) and store:

								self.add_variable(name,var[u"value"],var[u"function"],var[u"description"],var[u"packages"],False)
								return self.get_variable(name,store,full_info)
							else:
								if full_info:
									var["remote"]=True
									return var
								else:
									return var["value"]
								
						except Exception as e:
							time.sleep(1)
					
					return None
				else:
					return None
			else:
				
				return None
			
	#def get_variable

	
	def set_variable(self,name,value,depends=[],force_volatile_flag=False):

		if name in self.variables:
			
			if value == self.variables[name][u"value"]:
				return [True,"Variable already contained that value"]
			
			if type(value)==type(""):
				self.variables[name][u"value"]=unicode(value).encode("utf-8")
			else:
				self.variables[name][u"value"]=value

			if len(depends)>0:
				for depend in depends:
					self.variables[unicode(name).encode("utf-8")][u"packages"].append(depend)
			
			if not force_volatile_flag:
				self.write_file()
			else:
				
				self.variables[name]["volatile"]=True
				if "function" not in self.variables["name"]:
					self.variables[name]["function"]=""
				if "description" not in self.variables["name"]:
					self.variables[name]["description"]=""
			
			t=threading.Thread(target=self.notify_changes,args=(name,))
			t.daemon=True
			t.start()
			
			# local trigger call
			self.execute_trigger(name)
			
			return [True,""]
		else:
			return [False,"Variable not found. Use add_variable"]
		
		
	#def set_variable

	
	def add_variable(self,name,value,function,description,depends,volatile=False,root_protected=False):

		if name not in self.variables:
			dic={}
			if type(value)==type(""):
				dic[u"value"]=unicode(value).encode("utf-8")
			else:
				dic[u"value"]=value
			dic[u"function"]=function
			dic[u"description"]=unicode(description).encode("utf-8")
			if type(depends)==type(""):
				dic[u"packages"]=[unicode(depends).encode("utf-8")]
			elif type(depends)==type([]):
				dic[u"packages"]=depends
			else:
				dic[u"packages"]=[]
			dic["volatile"]=volatile
			dic["root_protected"]=root_protected
			self.variables[unicode(name)]=dic
			if not volatile:
				self.write_file()
			return [True,""]
		else:
			return [False,"Variable already exists. Use set_variable"]
			
	#def add_variable


	def write_file(self,fname=None):
		
		try:
			while os.path.exists(VariablesManager.LOCK_FILE):
				time.sleep(2)
				
			f=open(VariablesManager.LOCK_FILE,"w")
			f.close()
			tmp_vars={}
			for item in self.variables:
				if self.variables[item].has_key("volatile") and self.variables[item]["volatile"]==False:
					tmp_vars[item]=self.variables[item]
					
			for item in tmp_vars:
				
				tmp={}
				tmp[item]=tmp_vars[item]
				f=open(VariablesManager.VARIABLES_DIR+item,"w")
				data=unicode(json.dumps(tmp,indent=4,encoding="utf-8",ensure_ascii=False)).encode("utf-8")
				f.write(data)
				f.close()
				
				if "root_protected" in tmp_vars[item]:
					if tmp_vars[item]["root_protected"]:
						self.chmod(VariablesManager.VARIABLES_DIR+item,0600)
						
						
			os.remove(VariablesManager.LOCK_FILE)
			return True
				
			
		except Exception as e:
			os.remove(VariablesManager.LOCK_FILE)
			print (e)
			return False
		
	#def write_file


	def chmod(self,file,mode):
		prevmask = os.umask(0)
		try:
			os.chmod(file,mode)
			os.umask(prevmask)
			return True
		except Exception as e:
			print e
			os.umask(prevmask)
			return False
			
	#def chmod
	
	
	def init_variable(self,variable,args={},force=False,full_info=False):

		try:
			funct=self.variables[variable]["function"]
			mod_name=funct[:funct.rfind(".")]
			funct_name=funct[funct.rfind(".")+1:]
			funct_name=funct_name.replace("(","")
			funct_name=funct_name.replace(")","")
			mod=importlib.import_module(mod_name)
			ret=getattr(mod,funct_name)(args)
			ok,exc=self.set_variable(variable,ret)
			if ok:
				return (True,ret)
			else:
				return (False,ret)
		except Exception as e:
			return (False,e)
		
	#def init_variable
	
	
#class VariablesManager


if __name__=="__main__":
	
	vm=VariablesManager()
	
	
		
		
		
	
	
	
