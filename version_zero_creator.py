def run():

    import nuke
    import os
    import time
    import subprocess


    #########################################################################################
    "APP VARS"
    #########################################################################################
    app_name = "Version Zero Creator"
    app_version = "v1.0"
    app_root = os.path.dirname(__file__)


    #########################################################################################
    "Preflight Check"
    #########################################################################################
    if not os.path.exists(os.path.join(os.environ["DEADLINE_PATH"],"deadlinecommand.exe")):
        nuke.message("Could not find a deadline installation.\n\nPlease contact your system admin.")
        return


    #########################################################################################
    "Get Data from Shotgun"
    #########################################################################################
    "Get a sg instance"
    try:
        import sgtk
    except:
        nuke.message("Could not find a running Shotgun engine for tk-nuke.\n\nPlease ask your pipeline engineer for help.")
        return
    # get the engine we are currently running in
    current_engine = sgtk.platform.current_engine()
    # get hold of the shotgun api instance used by the engine, (or we could have created a new one)
    shotgun = current_engine.shotgun
    current_context = current_engine.context
    print("Project:",current_context.project["name"])


    "Get Playlists"
    fields = ["code"]
    filters = [['project', 'name_is', current_context.project["name"]]]
    playlists = shotgun.find('Playlist', filters, fields)
    print playlists
    playlist_names = []
    for p in playlists:
        if not " " in p:
            playlist_names.append(p.get("code"))


    #########################################################################################
    "Main Panel"
    #########################################################################################
    mainPanel = nuke.Panel(app_name+" "+app_version)

    "Show Project Name"
    env = current_context.project["name"].replace(" ","_")
    mainPanel.addEnumerationPulldown('Project:', env)

    "Choose Playlist"
    mainPanel.addEnumerationPulldown("Playlist to generate versions zero's from:", " ".join(playlist_names))

    "New Playlist to Generate"
    #mainPanel.addSingleLineInput('Name of new playlist:', '')

    mainPanel.show()


    #########################################################################################
    "Catch Data"
    #########################################################################################
    selectedPlaylist = mainPanel.value("Playlist to generate versions zero's from:")
    try:
        newPlaylistName = mainPanel.value('Name of new playlist:').replace(" ", "_")
    except:
        pass


    # #########################################################################################
    # "Try to Create New Playlist on Shotgun"
    # #########################################################################################
    # data = {
    #     'project': current_context.project,
    #     'code': newPlaylistName,
    # }
    # try:
    #     "Try to create new playlist"
    #     sg_newPlaylist = shotgun.create('Playlist', data)
    # except:
    #     print "Playlist probbaly exists already"
    #     filters = [
    #     ['project', 'name_is', current_context.project["name"]],
    #     ['code', 'name_is', newPlaylistName]
    #     ]
    #     sg_newPlaylist = shotgun.find_one('Playlist', filters, fields)


    #########################################################################################
    "Get all Versions in selected Playlist"
    #########################################################################################
    fields = ["code", "entity", "sg_path_to_frames", "sg_first_frame", "sg_last_frame"]
    filters = [
    ['project', 'name_is', current_context.project["name"]],
    ['playlists', 'name_contains', selectedPlaylist]
    ]
    versions = shotgun.find('Version', filters, fields)
    #print versions


    #########################################################################################
    "Create new version Version Zero Shotgun Version for each Version in the Playlist"
    #########################################################################################
    for version in versions:
        data = {
            'project': current_context.project,
            "entity": version.get("entity"),
            'code': "Version_Zero_"+version.get("code"),
            'description': "Version Zero",
            #"playlists": sg_newPlaylist,
            "sg_first_frame": version.get("sg_first_frame"),
            "sg_last_frame": version.get("sg_last_frame"),
            "frame_range": str(version.get("sg_first_frame"))+"-"+str(version.get("sg_last_frame")),
        }
        versionZero = shotgun.create('Version', data)
        
        #########################################################################################
        "Send Farm Job for New Version Zero Creation"
        #########################################################################################
        
        ## WRITE JOB INFO FILE
        jif = os.path.join(os.environ["TEMP"], str(time.time()).split(".")[0]+"_deadlineJobInfo.txt")
        print "Path to JobInfo File:", jif
        file = open(jif,"w")
        file.write("Plugin=Nuke") 
        file.write("\nLimitGroups=nuke")
        file.write("\nFrames="+str(version.get("sg_first_frame"))+"-"+str(version.get("sg_last_frame")))
        file.write("\nChunkSize=999999")
        file.write("\nPriority=30")
        file.write("\nPool=pipeline")
        file.write("\nName="+versionZero.get("code"))
        file.write("\nBatchName="+selectedPlaylist)
        file.write("\nDepartment="+app_name+" "+app_version)
        #file.write("\nOutputFilename0=")

        env_count = 0
        "Required variables"
        try:
            file.write("\nEnvironmentKeyValue"+str(env_count)+"=NUKE_PATH="+str(os.environ["NUKE_PATH"]))
            env_count = env_count+1
        except:
            pass
        try:
            file.write("\nEnvironmentKeyValue"+str(env_count)+"=OFX_PLUGIN_PATH="+str(os.environ["OFX_PLUGIN_PATH"]))
            env_count = env_count+1
        except:
            pass
        file.close() 

        ## WRITE PLUGIN INFO FILE
        pif = os.path.join(os.environ["TEMP"], str(time.time()).split(".")[0]+"deadlinePluginInfo.txt")
        print "Path to PluginInfo file:", pif
        file = open(pif,"w")
        file.write("Plugin=Nuke") 
        file.write("\nVersion=11.3")
        
        ## Nuke Hook
        "Load Nuke Project Hook, else load normal file"
        try:
            nukeHook = os.environ["VZ_NUKE_SCRIPT"]
            print "Found hook, loading:", nukeHook
            file.write("\nSceneFile="+nukeHook)
        except Exception as e:
            print e
            file.write("\nSceneFile="+os.path.join(app_root,"hooks", "basic","vz_creator.nk"))
        file.write("\nFrames=1")
        file.write("\nScriptJob=True")
        
        ## Python Hook
        "Load Python Hook if exists for project, else just load standard config"
        try:
            pyHook = os.environ["VZ_PYTHON_SCRIPT"]
            print "Found hook, loading:", pyHook
            file.write("\nScriptFilename="+pyHook)
        except Exception as e:
            print e       
            script_path = os.path.join(app_root, "hooks", "basic", "vz_creator.py")
            script_path = script_path.replace("\\","/")
            file.write("\nScriptFilename="+script_path)        

        file.close()

        ## SEND TO DEADLINE
        proc = subprocess.Popen([os.path.join(os.environ["DEADLINE_PATH"],"deadlinecommand.exe"), jif, pif], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        print "\n\nSending Version Zero to Deadline!\n", out

    nuke.message("Done!\n\nCheck the Renderfarm for progress of the Version Zero Creation.")