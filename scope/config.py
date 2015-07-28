import json
import os

'''
A few general assumptions:
-Camera is changed rarely.  Therefore only one camera per config file
-Objectives are changed reasonably often
    They cannot changed during a scan
    They can be changed in the GUI
'''

# FIXME: look into support multilevel default dictionary
class Config:
    defaults = {
        "live_video": True,
        "objective_json": "objective.json",
        "scan_json": "scan.json",
        "multithreaded": True,
        "imager": {
            "engine":'mock',
            "snapshot_dir":"snapshot",
            "width": 3264,
            "height": 2448,
            "scalar": 0.5,
       },
        "cnc": {
            # Good for testing and makes usable to systems without CNC
            "engine": "mock",
            "startup_run": False,
            "startup_run_exit": False,
            "out_dir":"out",
            "overwrite":False,
            # Default to no action, make movement explicit
            # Note that GUI can override this
            "dry":True,
        }
    }
    
    def __init__(self, fn):
        self.j = json.loads(open('microscope.json').read())
    
    def __getitem__(self, name):
        if name in self.j:
            return self.j[name]
        else:
            return Config.defaults[name]
    
    def __setitem__(self, name, value):
        self.j[name] = value
    
    def __delete__(self, name):
        del self.j[name]

class UScopeConfig(Config):
    pass

def get_config(fn='microscope.json'):
    return UScopeConfig(fn)
