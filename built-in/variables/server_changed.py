import n4d.responses
import time
import threading

def server_changed(self,n4d_id,variable_name,value):

	UNKNOWN_N4D_ID=-5
	
	if n4d_id == self.clients_manager.server_id:
		self.n4d_id_validation_errors_count=0
		self.dprint("Server variable '%s' change notified."%variable_name)
		if variable_name in self.variables_manager.triggers:
			self.variables_manager.execute_triggers(variable_name,value)
			
		
		return n4d.responses.build_successful_call_response(True)
	
	self.n4d_id_validation_errors_count+=1
	time.sleep(Core.ERROR_SLEEP_TIME*self.n4d_id_validation_errors_count)
	return n4d.responses.build_failed_call_response(UNKNOWN_N4D_ID,"Unknown N4D id")

#def set_variable

