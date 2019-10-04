import os
import sys


"Add ourselves to the NUKE_PATH"
try:
    "NUKE_PATH is defined"
    nuke_path = os.environ["NUKE_PATH"]
    new_nuke_path = []
    for s in nuke_path.split(";"):
        if "tk-nuke" in s:
            new_nuke_path.append(s)
    new_nuke_path.prepend(os.path.dirname(__file__))
    os.environ["NUKE_PATH"] = ";".join(new_nuke_path)
except:
    os.environ["NUKE_PATH"] = os.path.dirname(__file__)

print "NUKE_PATH: "+os.environ["NUKE_PATH"]

"Unset OFX_PLUGIN_PATH"
os.environ["OFX_PLUGIN_PATH"] = ""




## Find a Valid Nuke 11 Install, recent first
## Needs to be any Nuke 11 version because Nuke 10.5 and below cannot connect with Shotgun anymore due to incompatibility with python TLS 1.2 libraries... :(
nuke_versions = ["C:/Program Files/Nuke11.3v4/Nuke11.3.exe","C:/Program Files/Nuke11.2v4/Nuke11.2.exe","C:/Program Files/Nuke11.1v4/Nuke11.1.exe","C:/Program Files/Nuke11.1v2/Nuke11.1.exe","F:/Archive/common_2d/Nuke/bin/Nuke11.3v4/Nuke11.3.exe"]
for nuke in nuke_versions:
    if os.path.exists(nuke):
        os.system('start "" "'+nuke+'"'+" --nuke")
        sys.exit()
