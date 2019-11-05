# nuke-sg-version-zero-creator
 Nuke Tool to create version zero's from a playlist in Shotgun, hookable via ENV Vars.


## Custom Shotgun Template Keys
    # Shotgun Version Zero Custom keys
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


## Custom Template Paths
    #
    # Shotgun Version Zero Creator
    #
    path_to_versionzero_dir:
        definition: 'editorial/out/{Year}-{Month}-{Day}/{Playlist}/versionZero/{Shot}_v000'
    path_to_versionzero_movie:
        definition: 'editorial/out/{Year}-{Month}-{Day}/{Playlist}/versionZero/{Shot}_v000/{Shot}_v000.mov'
    path_to_versionzero_frames:
        definition: 'editorial/out/{Year}-{Month}-{Day}/{Playlist}/versionZero/{Shot}_v000/frames/{original_file_basename}_v000.{SEQ}.exr'



## Environement Variables to Hook
- VZ_NUKE_SCRIPT
To load a different nuke script for version creation. 
If not defined, the basic file will be loaded.




## Changelog:
v2.0
- Recoded base code
- Now searches Standard Shotgun Template fields for info
- Added Progress Task