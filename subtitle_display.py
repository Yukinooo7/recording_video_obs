import obspython
import time

html_path = ""
video_path = ""
scene_name = "Recording Scene"
is_stopped = True


def script_load(setting):
    global s_dic
    obspython.script_log(obspython.LOG_INFO, "Script Load successfully")


def script_description():
    return "Show subtitle"


def script_properties():
    props = obspython.obs_properties_create()

    obspython.obs_properties_add_path(
        props, "html_path", "Subtitle File (HTML)", obspython.OBS_PATH_FILE, "HTML (*.html)", 'null')
    obspython.obs_properties_add_path(
        props, "video_path", "Video File", obspython.OBS_PATH_FILE, "VIDEO (*.mp4)", "null")

    obspython.obs_properties_add_button(
        props, "start", "Start Recording", start_record)
    obspython.obs_properties_add_button(
        props, "stop", "Stop Recording", stop_record)
    obspython.obs_properties_add_button(
        props, "refresh", "Refresh Sources", refresh_source)

    return props


def start_record(props, prop):
    global video_path

    scenes_names = obspython.obs_frontend_get_scene_names()

    if scene_name not in scenes_names:
        new_scene = obspython.obs_scene_create(scene_name)

    scenes = obspython.obs_frontend_get_scenes()
    for scene in scenes:
        name = obspython.obs_source_get_name(scene)
        if name == scene_name:
            obspython.obs_frontend_set_current_scene(scene)
            new_scene = obspython.obs_scene_from_source(obspython.obs_frontend_get_current_scene())
    obspython.source_list_release(scenes)

    if scene_name not in scenes_names:
        video_data = obspython.obs_data_create()
        obspython.obs_data_set_string(video_data, 'local_file', video_path)
        video_source = obspython.obs_source_create(
            "ffmpeg_source", "Record Video", video_data, None)

        html_data = obspython.obs_data_create()
        obspython.obs_data_set_string(html_data, 'local_file', html_path)
        obspython.obs_data_set_bool(html_data, 'is_local_file', True)
        html_source = obspython.obs_source_create("browser_source", "Math Subtitle", html_data, None)
        source_item = obspython.obs_scene_add(new_scene, video_source)
        fit_to_screen(source_item)
        source_item = obspython.obs_scene_add(new_scene, html_source)
        fit_to_screen(source_item)
        duration = obspython.obs_source_media_get_duration(video_source)
        print(duration)

        obspython.obs_frontend_recording_start()

        obspython.timer_add(stop_only, duration)
    else:
        if obspython.obs_frontend_recording_active():
            refresh_source(props, prop)
        else:
            refresh_source(props, prop)

            obspython.obs_frontend_recording_start()

    obspython.obs_scene_release(new_scene)


def refresh_source(props, prop):
    obspython.timer_remove(stop_only)
    obspython.obs_frontend_recording_stop()

    video_source = obspython.obs_get_source_by_name("Record Video")
    duration = obspython.obs_source_media_get_duration(video_source)
    html_source = obspython.obs_get_source_by_name("Math Subtitle")
    video_data = obspython.obs_source_get_settings(video_source)

    obspython.obs_source_set_enabled(html_source, False)
    obspython.obs_data_set_string(video_data, 'local_file', None)
    obspython.obs_source_update(video_source, video_data)
    html_data = obspython.obs_source_get_settings(html_source)
    fps = obspython.obs_data_get_int(html_data, "fps")

    if fps % 2 == 0:
        obspython.obs_data_set_int(html_data, "fps", fps + 1)
    else:
        obspython.obs_data_set_int(html_data, "fps", fps - 1)

    time.sleep(1)
    obspython.obs_data_set_string(video_data, 'local_file', video_path)
    obspython.obs_source_update(video_source, video_data)

    obspython.obs_data_set_string(html_data, 'local_file', html_path)
    obspython.obs_source_update(html_source, html_data)
    obspython.obs_source_set_enabled(html_source, True)

    obspython.obs_data_release(video_data)
    obspython.obs_data_release(html_data)

    obspython.timer_add(stop_only, duration)

is_stopped = True


def start_recording():
    global is_stopped
    if is_stopped:
        if not obspython.obs_frontend_recording_active():
            obspython.obs_frontend_recording_start()
            print("Start recording...")
        else:
            obspython.timer_remove(start_recording)


def stop_recording():
    global is_stopped

    if obspython.obs_frontend_recording_active():
        obspython.obs_frontend_recording_stop()
        print("Stop recording...")
        is_stopped = False
    else:
        obspython.timer_remove(stop_recording)
        is_stopped = True


def stop_only():
    print("Time to stop!")
    if obspython.obs_frontend_recording_active():
        obspython.obs_frontend_recording_stop()
        obspython.timer_remove(stop_only)


def stop_record(props, prop):
    global html_path

    obspython.timer_remove(stop_only)
    obspython.obs_frontend_recording_stop()


def script_defaults(settings):
    obspython.obs_data_set_default_string(settings, "source name", "None")


def script_update(setting):
    global html_path
    global video_path
    # global interval_txt

    html_path = obspython.obs_data_get_string(setting, "html_path")
    video_path = obspython.obs_data_get_string(setting, "video_path")


def script_description():
    return "<b>Recording videos with math subtitles</b>" + \
           "<hr>" + \
           "Allow users to record videos with its math subtitles (Html file)<br/>" + \
           "Please Refresh Source before restart recording" + \
           "<hr>"


def fit_to_screen(scene_item):
    # see ~/Library/Application Support/obs-studio/basic/profiles/Untitled/basic.ini
    # which contains
    # BaseCX=1680
    # BaseCY=1050
    # OutputCX=1120
    # OutputCY=700
    # 1680 x 1050 appear to be the dimensions we want, to completely fill the scren.
    video_info = obspython.obs_video_info()
    obspython.obs_get_video_info(video_info)

    bounds = obspython.vec2()
    bounds.x = video_info.base_width  # output_width # 1680 # source_width
    bounds.y = video_info.base_height  # output_height # 1050 # source_height
    obspython.obs_sceneitem_set_bounds(scene_item, bounds)

    # fit video to screen
    # https://obsproject.com/docs/reference-scenes.html?highlight=bounds#c.obs_transform_info.bounds
    obspython.obs_sceneitem_set_bounds_type(scene_item, obspython.OBS_BOUNDS_SCALE_INNER)

    scale = obspython.vec2()
    scale.x = 1
    scale.y = 1
    obspython.obs_sceneitem_set_scale(scene_item, scale)
