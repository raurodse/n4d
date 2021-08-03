
def set_remote_server(self,auth,variable_name):

	ret=self.builtin_validation(auth)
	
	if ret["status"]==0:	
		#internal core funciton
		return self.remove_remote_server(variable_name,value)

	else:
		return ret

#def set_variable

