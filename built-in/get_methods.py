import n4d.responses
import n4d.server.core

def get_methods(self,class_filter=None):
	
	#internal core function
	return self.core.get_methods(class_filter)
	
#def get_methods
