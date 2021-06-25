import n4d.responses

def create_ticket(self,user):
	
	ret=self.tickets_manager.create_ticket(user)

	if ret:
		return n4d.responses.build_successful_call_response(True,"Ticket created for user %s"%user)
	else:
		CREATE_TICKET_ERROR=-5
		return n4d.responses.build_failed_call_response(CREATE_TICKET_ERROR,"Failed to create ticket")

#def test
