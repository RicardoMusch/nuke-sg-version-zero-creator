"""
--- Shotgun Settings ---

Template Paths:
    path_to_versionzero_dir
    path_to_versionzero_movie
    path_to_versionzero_frames

Custom Keys:
    Day:
        type: str
    Month:
        type: str
    Year:
        type: str
    Playlist:
        type: str
    original_file_basename:
        type: str


--- ENV Variables ---



"""


def run():

    import nuke
    import os
    import time
    import subprocess
    from datetime import datetime


    #########################################################################################
    "APP VARS"
    #########################################################################################
    app_name = "Shotgun Version Zero Creator"
    app_version = "v2.0"
    app_root = os.path.dirname(__file__)


    #########################################################################################
    "Preflight Check"
    #########################################################################################
    if not os.path.exists(os.path.join(os.environ["DEADLINE_PATH"],"deadlinecommand.exe")):
        nuke.message("Could not find a deadline installation.\n\nPlease contact your system admin.")
        return


    #########################################################################################
    "Check for Setup"
    #########################################################################################
    if not "VZC_NUKE_SCRIPT" in os.environ:
        nuke.message("This tool has not been set up for the current show.\n\nPlease ask your pipeline person to configure it.")
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
    sg = current_engine.shotgun
    current_context = current_engine.context


    "Get Playlists"
    fields = ["code"]
    filters = [
        ['project', 'name_is', current_context.project["name"]],
        ['sg_playlist_status', 'is', "Ready to Export"]
    ]
    playlists = sg.find('Playlist', filters, fields)
    #print playlists
    playlist_names = []
    "Make sure to ignore playlists with spaces in the name"
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
    mainPanel.addSingleLineInput('Note:', 'Version Zero from Lola')
    try:
        output_options = (os.environ["VZC_OUTPUT_OPTIONS"]).split(";")
        mainPanel.addEnumerationPulldown("Output:", " ".join(output_options))
    except:
        mainPanel.addEnumerationPulldown("Output:", "movies_only frames_only movies_and_frames")
    mainPanel.addBooleanCheckBox('Submit as Suspended?', False)

    "New Playlist to Generate"
    #mainPanel.addSingleLineInput('Name of new playlist:', '')

    result = mainPanel.show()

    if result == 1:
        #########################################################################################
        "Catch Data"
        #########################################################################################

        selectedPlaylist = mainPanel.value("Playlist to generate versions zero's from:")
        # try:
        #     newPlaylistName = mainPanel.value('Name of new playlist:').replace(" ", "_")
        # except:
        #     pass


        # #########################################################################################
        # "Try to Create New Playlist on Shotgun"
        # #########################################################################################
        # data = {
        #     'project': current_context.project,
        #     'code': "VZ_"+selectedPlaylist,
        # }
        # try:
        #     "Try to create new playlist"
        #     sg_newPlaylist = sg.create('Playlist', data)
        # except:
        #     print "Playlist probbaly exists already"
        #     filters = [
        #     ['project', 'name_is', current_context.project["name"]],
        #     ['code', 'name_is', newPlaylistName]
        #     ]
        #     sg_newPlaylist = sg.find_one('Playlist', filters, fields)
        #     print sg_newPlaylist


        #########################################################################################
        "Get all Versions in selected Playlist"
        #########################################################################################
        fields = ["code", "entity", "sg_path_to_frames", "sg_first_frame", "sg_last_frame"]
        filters = [
        ['project', 'name_is', current_context.project["name"]],
        ['playlists', 'name_contains', selectedPlaylist]
        ]
        playlist_versions = sg.find('Version', filters, fields)


        #########################################################################################
        "Create new Version Zero Shotgun Version for each Version in the Playlist"
        #########################################################################################       
        t = nuke.ProgressTask("Creating Shotgun Versions and Sending Versions to the Farm!")
        tasks = len(playlist_versions)
        count = 0
        percent = tasks/100

        for version in playlist_versions:
            count = count+1
            t.setProgress(percent)
            t.setMessage("Step %s of %d" % (count, tasks))

            os.environ["VZC_ORIGINAL_SG_VERSION"] = str(version)

            # #########################################################################################
            # "Check Shotgun if Version Zero already exists"
            # #########################################################################################
            # fields = ["code", "entity", "sg_path_to_frames", "sg_first_frame", "sg_last_frame"]
            # filters = [ 
            # ['project', 'name_is', current_context.project["name"]],
            # ['code', 'contains', version_zero_name]
            # ]
            # sg_versionZero = sg.find_one('Version', filters, fields)


            #########################################################################################
            "Find the parent entity info"
            #########################################################################################
            fields = ["code", "sg_sequence", "sg_episode"]
            filters = [
            ['code', 'is', version.get("entity").get("name")],
            ]
            version_entity = sg.find_one(version.get("entity").get("type"), filters, fields)


            #################################
            "Get Shotgun template paths"
            #################################
            #Grab the sgtk API instance.
            tk = current_engine.sgtk

            #Create Context from Version Zero
            ctx = tk.context_from_entity(version_entity["type"], version_entity["id"])
            
            #Create the folders just in case they haven't already been created.
            tk.create_filesystem_structure(version_entity["type"], version_entity["id"])

            # Get a template instance for for the template we want to resolve into a path.
            path_to_versionzero_dir = tk.templates["path_to_versionzero_dir"]
            path_to_versionzero_movie = tk.templates["path_to_versionzero_movie"]
            path_to_versionzero_frames = tk.templates["path_to_versionzero_frames"]

            # Use the context to resolve as many of the template fields as possible.
            dir_fields = ctx.as_template_fields(path_to_versionzero_dir)
            movie_fields = ctx.as_template_fields(path_to_versionzero_movie)
            frames_fields = ctx.as_template_fields(path_to_versionzero_frames)

            # Manually fill in the remaining fields that can't be figured out automatically from context.
            dir_fields["original_file_basename"] = os.path.basename(version.get("sg_path_to_frames")).split(".")[0]
            movie_fields["original_file_basename"] = os.path.basename(version.get("sg_path_to_frames")).split(".")[0]
            frames_fields["original_file_basename"] = os.path.basename(version.get("sg_path_to_frames")).split(".")[0]
            dir_fields["Shot"] = ctx.entity.get("name")
            movie_fields["Shot"] = ctx.entity.get("name")
            frames_fields["Shot"] = ctx.entity.get("name")
            dir_fields["Episode"] = version_entity.get("sg_episode")
            movie_fields["Episode"] = version_entity.get("sg_episode")
            frames_fields["Episode"] = version_entity.get("sg_episode")
            dir_fields["Sequence"] = version_entity.get("sg_sequence")
            movie_fields["Sequence"] = version_entity.get("sg_sequence")
            frames_fields["Sequence"] = version_entity.get("sg_sequence")
            dir_fields["Day"] = datetime.today().strftime('%d')
            movie_fields["Day"] = datetime.today().strftime('%d')
            frames_fields["Day"] = datetime.today().strftime('%d')
            dir_fields["Month"] = datetime.today().strftime('%m')
            movie_fields["Month"] = datetime.today().strftime('%m')
            frames_fields["Month"] = datetime.today().strftime('%m')
            dir_fields["Year"] = datetime.today().strftime('%Y')
            movie_fields["Year"] = datetime.today().strftime('%Y')
            frames_fields["Year"] = datetime.today().strftime('%Y')
            dir_fields["Playlist"] = selectedPlaylist
            movie_fields["Playlist"] = selectedPlaylist
            frames_fields["Playlist"] = selectedPlaylist
            #fields["version"] = 2

            # Resolve the template path using the field values.
            os.environ["VZC_PATH_TO_VERSIONZERO_DIR"] = (path_to_versionzero_dir.apply_fields(dir_fields)).replace("\\", "/")
            try:
                os.environ["VZC_PATH_TO_VERSIONZERO_MOVIE"] = (path_to_versionzero_movie.apply_fields(movie_fields)).replace("\\", "/")
            except Exception as e:
                print "    Could not find a path_to_versionzero_movie template in the templates file, skipping..."
                print e
            try:
                os.environ["VZC_PATH_TO_VERSIONZERO_FRAMES"] = (path_to_versionzero_frames.apply_fields(frames_fields)).replace("\\", "/")
            except Exception as e:
                print "    Could not find a path_to_versionzero_frames template in the templates file, skipping..."
                print e

            
            # #########################################################################################
            # "If No Version Zero Exists on Shotgun, Create a new Version Zero record on Shotgun"
            # #########################################################################################
            # if sg_versionZero == None:
            data = {
                'project': current_context.project,
                "entity": version.get("entity"),
                'code': (os.path.basename(os.environ["VZC_PATH_TO_VERSIONZERO_MOVIE"])).split(".")[0],
                'description': mainPanel.value("Note:"),
                'sg_path_to_frames': version.get("sg_path_to_frames"),
                #"playlists": [ sg_newPlaylist ],
                "sg_first_frame": version.get("sg_first_frame"),
                "sg_last_frame": version.get("sg_last_frame"),
                "frame_range": str(version.get("sg_first_frame"))+"-"+str(version.get("sg_last_frame")),
                "sg_version_type": "version_zero",
                "sg_status_list": "ren"
            }
            sg_versionZero = sg.create('Version', data)

            
            def send_to_farm(output_format):
                #########################################################################################
                "Send Farm Job for New Version Zero Creation"
                #########################################################################################
                
                ## WRITE JOB INFO FILE
                jif = os.path.join(os.environ["TEMP"], str(time.time()).replace(".", "")+"_deadlineJobInfo.txt")
                print "Path to JobInfo File:", jif
                file = open(jif,"w")
                file.write("Plugin=Nuke") 
                file.write("\nLimitGroups=nuke")
                file.write("\nFrames="+str(version.get("sg_first_frame"))+"-"+str(version.get("sg_last_frame")))
                #file.write("\nChunkSize=999999")
                if "frames" in output_format:
                    file.write("\nChunkSize=100")
                else:
                    file.write("\nChunkSize=999999")
                file.write("\nPriority=30")
                file.write("\nPool=pipeline")
                file.write("\nName="+sg_versionZero.get("code")+" / "+output_format)
                file.write("\nBatchName="+selectedPlaylist)
                file.write("\nDepartment="+app_name+" "+app_version)
                if mainPanel.value("Submit as Suspended?") == True:
                    file.write("\nInitialStatus=Suspended")
                file.write("\nOutputFilename0="+os.environ["VZC_PATH_TO_VERSIONZERO_DIR"]+"/")

                env_count = 0
                "Required variables"
                try:
                    file.write("\nEnvironmentKeyValue"+str(env_count)+"=SG_VERSION="+str(sg_versionZero))
                    env_count = env_count+1
                except:
                    pass
                try:
                    file.write("\nEnvironmentKeyValue"+str(env_count)+"=SG_PLAYLIST_NAME="+str(selectedPlaylist))
                    env_count = env_count+1
                except:
                    pass

                "ADD ALL VZC VARS"
                for e in os.environ:
                    if "VZC_" in e:
                        file.write("\nEnvironmentKeyValue"+str(env_count)+"="+e+"="+str(os.environ[e]))
                        env_count = env_count+1

                try:
                    file.write("\nEnvironmentKeyValue"+str(env_count)+"=OUTPUT_FORMAT="+output_format)
                    env_count = env_count+1
                except:
                    pass
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
                pif = os.path.join(os.environ["TEMP"], str(time.time()).replace(".", "")+"deadlinePluginInfo.txt")
                print "Path to PluginInfo file:", pif
                file = open(pif,"w")
                file.write("Plugin=Nuke") 
                file.write("\nVersion="+str(nuke.NUKE_VERSION_MAJOR)+"."+str(nuke.NUKE_VERSION_MINOR))
                
                ## Nuke Hook
                "Load Nuke Project Hook, else load normal file"
                file.write("\nSceneFile="+os.environ["VZC_NUKE_SCRIPT"])
                file.write("\nFrames="+str(version.get("sg_first_frame"))+"-"+str(version.get("sg_last_frame")))
                file.write("\nScriptJob=True")
                
                ## Python Hook
                "Load Python Hook if exists for project, else just load standard config"
                try:
                    pyHook = os.environ["VZC_PYTHON_SCRIPT"]
                    print "Found hook, loading:", pyHook
                    file.write("\nScriptFilename="+pyHook)
                except Exception as e:
                    print e       
                    script_path = os.path.join(app_root, "hooks", "basic", "vzc_render_version.py")
                    script_path = script_path.replace("\\","/")
                    file.write("\nScriptFilename="+script_path)        

                file.close()

                ## SEND TO DEADLINE
                subprocess.Popen([os.path.join(os.environ["DEADLINE_PATH"],"deadlinecommand.exe"), jif, pif], stdout=None, shell=True)
                return


            if mainPanel.value("Output:") == "movies_and_frames":
                send_to_farm("movies")
                time.sleep(2)
                send_to_farm("frames")
            
            if mainPanel.value("Output:") == "frames_only":
                send_to_farm("frames_only")

            if mainPanel.value("Output:") == "movies_only":
                send_to_farm("movies_only")


        nuke.message("Done!\n\nCheck the Renderfarm for progress of the Version Zero Creation.")