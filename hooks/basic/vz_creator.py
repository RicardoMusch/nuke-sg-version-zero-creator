"VERSION ZERO CREATOR SCRIPT"

"Params to be extracted on the job:"
"sg_versionZeroZero : Env_Variable : Holds a stringed dictionary of the Shotgun Version Zero we are processing"


#########################################################################################
print "Importing Modules"
#########################################################################################
import ast
import os
import nuke
import sys



#########################################################################################
print "Connecting to Shotgun"
#########################################################################################
try:
    sys.path.append(os.environ["SHOTGUN_API3"])
    import shotgun_api3

    sg = shotgun_api3.Shotgun(os.environ["SHOTGUN_API_SERVER_PATH"], os.environ["SHOTGUN_API_SCRIPT_NAME"], os.environ["SHOTGUN_API_SCRIPT_KEY"])
    print "Connect to Shotgun via API"
except Exception as e:
    print "Error, couldn't connect to Shotgun!"
    print e
    sys.exit(1)


#########################################################################################
print "Loading Environement"
#########################################################################################
sg_versionZero = ast.literal_eval(os.environ["sg_versionZero"])

src = sg_versionZero.get("sg_path_to_frames")
first_frame = str(sg_versionZero.get("sg_first_frame"))
last_frame = str(sg_versionZero.get("sg_last_frame"))
total_frames = int(last_frame)-int(first_frame)+1



#########################################################################################
print "Definitions"
#########################################################################################
count = 0
def printFrame():
    global count
    count = count+1
    print "Frame "+str(nuke.frame())+" ("+str(count)+" of "+str(total_frames)+")"

for s in nuke.allNodes("Write"):
    s["afterFrameRender"].setValue("printFrame()")


def find_version_number(s):
    "Match v(any_digit): v(\d+)"
    s = s.lower()

    ## filter show names
    s = s.replace("av5", "")

    try:
        result = int(re.findall("v(\d+)", s)[0])
    except:
        result = 1
    return result


def apply_fields(path):
    g = nuke.toNode("getShotgunData")
    path = path.replace("<PackageName>", os.environ["playlist"])
    path = path.replace("<EntityType>", g["entity_type"].getValue())
    path = path.replace("<Show>", g["project"].getValue())
    path = path.replace("<Sequence>", g["sequence"].getValue())
    path = path.replace("<EntityName>", g["entity_name"].getValue())
    path = path.replace("<Step>", g["step"].getValue())
    path = path.replace("<VersionName>", g["version_name"].getValue())
    path = path.replace("<VersionNameWithoutVersion>", g["version_name"].getValue().split("_v")[0])
    path = path.replace("<Resolution>", "[value width]x[value height]")

    if "version_zero=True" in os.environ["extra_options"]: 
        version_number = "v000"
    else:
        version_number = g["version_name"].getValue().split("_")[-1]
    path = path.replace("<VersionNumber>", version_number)
    
    return path


#########################################################################################
print "Loading Source frames"
#########################################################################################
src_read = nuke.toNode("src_read")
src_read["file"].setValue(src)
src_read["first"].setValue(int(first_frame))
src_read["last"].setValue(int(last_frame))
src_read["reload"].execute()


#########################################################################################
print "Running getShotgunData"
#########################################################################################
gsd = nuke.toNode("getShotgunData")
gsd["update"].execute()
print "Version: "+gsd["version_name"].getValue()


# ########################################################################################################
# print "Updating Timecode"
# t = nuke.toNode("AddTimeCode")
# t["update"].execute()


#########################################################################################
print "Pathing"
#########################################################################################
path_to_movie_versionZero = ""


#########################################################################################
print "Starting to Render"
#########################################################################################
w = nuke.toNode("write_versionzero")
w["file"].setValue(path_to_movie_versionZero)
nuke.execute(w, int(first_frame)-1, int(last_frame))


try:
    print "Upload to Shotgun for Review/Replace Original Version"
    sg.upload("Version", sg_versionZero.get("id"), path_to_movie_versionZero, field_name="sg_uploaded_movie", display_name="Latest QT")
    print "Uploaded Movie to Shotgun!"
except Exception as e:
    print "Error uploading movie to Shotgun!"
    print e










