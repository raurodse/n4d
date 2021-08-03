
def set_remote_server(self,auth,variable_name,server):

	ret=self.builtin_validation(auth)
	
	if ret["status"]==0:	
		#internal core funciton
		return self.set_remote_server(variable_name,value,attr_dic)

	else:
		return ret

#def set_variable

