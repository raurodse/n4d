def is_user_valid(self,user,password,group_list=[]):
	
	#internal core function
	ret=self.validate_auth((user,password))
	
	if ret["status"]==0:
		
		if type(group_list)==list and len(group_list)>0:
			user_group_list=ret["return"][1]
			for group in user_group_list:
				if group in group_list:
					return n4d.responses.build_successful_call_response(True)
		else:
			return n4d.responses.build_successful_call_response(msg="User doesn't belong to requested group list")
	
	return n4d.responses.build_successful_call_response(False,msg="User and/or password error")

#def is_user_valid
