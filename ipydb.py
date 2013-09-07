'''Start an IPython shell (for debugging) with current environment.                    
Runs Call db() to start a shell, e.g.                                                  


def foo(bar):                                                                          
    for x in bar:                                                                      
        if baz(x):                                                                     
            import ipydb; ipydb.db() # <-- start IPython here, with current value of x (ipydb is the name of this module).
.                                                                                      
'''
import inspect,IPython

def debug_trace():
  '''Set a tracepoint in the Python debugger that works with Qt'''
  from PyQt4.QtCore import pyqtRemoveInputHook
  from pdb import set_trace
  pyqtRemoveInputHook()
  # set_trace()

def db():
    '''Start IPython shell with callers environment.'''
    debug_trace()
    # find callers                                                                     
    __up_frame = inspect.currentframe().f_back
    eval('IPython.embed()', # Empty list arg is                       
         # ipythons argv later args to dict take precedence, so                        
         # f_globals() shadows globals().  Need globals() for IPython                  
         # module.                                                                     
         dict(globals().items() + __up_frame.f_globals.items()),
         __up_frame.f_locals)