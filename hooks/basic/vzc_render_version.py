########################################################
print " "
print " "
print "############################################################"
print "Creating Logger"
########################################################
def log(msg):
    print " "
    print " "
    print "############################################################"
    print msg
    #print "############################################################"
    print " "


########################################################
log("Starting Shotgun Ingest Publisher Script")
########################################################


########################################################
log("Importing Python Libraries")
########################################################
import nuke
import shutil
import re
import ast
import os
import time


########################################################
log("Reading Version Data")
########################################################
sg_version = ast.literal_eval(os.environ["sg_version"])
sg_original_version = ast.literal_eval(os.environ["VZC_ORIGINAL_SG_VERSION"])


########################################################
log("Setting printFrame Function")
########################################################
count = 0
total_frames = sg_version.get("sg_last_frame")-sg_version.get("sg_first_frame")+1

def printFrame():
    global count
    count = count+1
    print "Frame "+str(nuke.frame())+" ("+str(count)+" of "+str(total_frames)+")"

for s in nuke.allNodes("Write"):
    s["afterFrameRender"].setValue("printFrame()")


########################################################
log("Finding src_read node")
########################################################
src_read = nuke.toNode("src_read")
src_read["file"].setValue(sg_original_version["sg_path_to_frames"])
src_read["first"].setValue(sg_original_version["sg_first_frame"])
src_read["last"].setValue(sg_original_version["sg_last_frame"])
try:
    if sg_original_version["colorspace"] == "raw":
        src_read["raw"].setValue(True)
    else:
        src_read["colorspace"].setValue(sg_original_version["colorspace"])
except Exception as e:
    print "    Couldn't find KEYs for Colorspace, using the default set in the template..."
src_read["reload"].execute()


########################################################
log("Running VZC node...")
########################################################
try:
    vzcNode = nuke.toNode("VZC")
    vzcNode["run"].execute()
except Exception as e:
    print "ERROR running VZC node:"
    print e
