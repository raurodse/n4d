import os
import os.path
import threading
import shutil
import pwd
import random
import string
import time

import pyinotify
from pyinotify import WatchManager, Notifier, ThreadedNotifier, EventsCodes, ProcessEvent


class NTicketsManager:
	
	WATCH_DIR="/run/n4d/tickets/"
	ALIVE_TIME=60*30
	#ALIVE_TIME=1
	
	def __init__(self):
		
		if not os.path.exists(NTicketsManager.WATCH_DIR):
			os.makedirs(NTicketsManager.WATCH_DIR)
		
		self.generate_pam()
		self.start_inotify()
		self.tickets={}
		
	#def __init__
	
	def start_inotify(self):

		t=threading.Thread(target=self._inotify)
		t.daemon=True
		t.start()

	#def start_inotify
	

	def _inotify(self):
		
		
		wm=WatchManager()
		mask=pyinotify.IN_CLOSE_WRITE
			
		class Process_handler(ProcessEvent):
				
			def __init__(self,main):
				
				self.main=main
				
			def process_IN_CLOSE_WRITE(self,event):

				for user in pwd.getpwall():
					if user.pw_name == event.name:
						f=open(event.path+"/"+event.name)
						ticket=f.readlines()[0]
						f.close()
						self.main.tickets[user.pw_name]={}
						self.main.tickets[user.pw_name]["password"]=ticket
						self.main.tickets[user.pw_name]["date"]=time.time()
						break
				
				#self.generate_pam()
				
	
		notifier=Notifier(wm,Process_handler(self))
		wdd=wm.add_watch(NTicketsManager.WATCH_DIR,mask,rec=True)
			
		while True:
			try:
					
				notifier.process_events()
				if notifier.check_events():
					notifier.read_events()
				
			except Exception as e:
				print e
				notifier.stop()
					
		return False
	
	#def _inotify
	
	def generate_pam(self):
		
		f=open("/etc/pam.d/common-auth")
		lines=f.readlines()
		f.close()
		
		f=open("/etc/pam.d/n4d","w")
		for line in lines:
			if "n4d" not in line:
				f.write(line)
		f.close()
		
	#def generate_pam

	def set_ticket(self,user,password):


		t=time.time()
		
		f=open(NTicketsManager.WATCH_DIR+user,"w")
		if password==None:
			password ="".join(random.sample(string.letters+string.digits, 50))
		f.write(password)
		f.close()
		self.set_perms(user)
		self.tickets[user]={}
		self.tickets[user]["password"]=password
		self.tickets[user]["date"]=t
		
		return True

	#def set_ticket
	
	def create_ticket(self,user):
		
		t=time.time()
		if user in self.tickets:
			#if self.tickets[user]["date"]+NTicketsManager.ALIVE_TIME > t:
			return True

		f=open(NTicketsManager.WATCH_DIR+user,"w")
		
		password ="".join(random.sample(string.letters+string.digits, 50))
		f.write(password)
		f.close()

		self.set_perms(user)
		self.tickets[user]={}
		self.tickets[user]["password"]=password
		self.tickets[user]["date"]=t

		return True
		
	#def create_ticket
	
	def get_ticket(self,user):
		
		t=time.time()
		if user in self.tickets:
			#if self.tickets[user]["date"]+NTicketsManager.ALIVE_TIME > t:
			return self.tickets[user]["password"]

		self.create_ticket(user)
		return self.get_ticket(user)
		
	#def get_ticket
	
	def validate_user(self,user,password):
		
		if user in self.tickets:
			#t=time.time()
			#if self.tickets[user]["date"]+NTicketsManager.ALIVE_TIME > t:
			if self.tickets[user]["password"]==password:
				return True
		
		return False
		
	#def validate_password
	
	def set_perms(self,user):
		
		prevmask = os.umask(0)
		uid=pwd.getpwnam(user).pw_uid
		path=NTicketsManager.WATCH_DIR+user
		os.chown(path,uid,0)
		os.chmod(path,0460)	
		os.umask(prevmask)
		
	#def set_perms
	
	
#class NTicketsManager


if __name__=="__main__":
	
	ntm=NTicketsManager()
	ntm.create_ticket("cless")
	f=open(ntm.WATCH_DIR+"cless")
	password=f.readlines()[0]
	f.close()
	time.sleep(3)
	print ntm.validate_password("cless",password)
	#ntm.init_watch_monitor()