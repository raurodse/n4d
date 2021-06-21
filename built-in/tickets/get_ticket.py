import n4d.responses
import os

def get_ticket(self,user,password):

	UNKNOWN_USER_ERROR=-10

	ret=self.validate_user(user,password)
	if ret["status"]!=0:
		return n4d.responses.build_authentication_failed_response()
		
	ticket=self.tickets_manager.get_ticket(user)
	if ticket!=None:
		return n4d.responses.build_successful_call_response(ticket)
	else:
		return n4d.responses.build_failed_call_response(UNKNOWN_USER_ERROR,"Unknown user error.")

#def set_variable

