#!/usr/bin/env python3
# ver 0.03.2

import configparser
import datetime
import glob
import os
import psutil
import re
import subprocess
import sys
import time
import urwid

# MAIN SCREEN

def main_screen(button=None):
    init_config()
    body = main_body()
    return urwid.ListBox(urwid.SimpleFocusListWalker(body))


def main_screen_2(button):
    body = main_body()
    main.original_widget = urwid.ListBox(urwid.SimpleFocusListWalker(body))


def main_body():
    body = program_header()

    create_backup_button = urwid.Button('Backup')
    urwid.connect_signal(create_backup_button, 'click', show_lvm)
    body.append(urwid.AttrMap(create_backup_button, None, focus_map='reversed'))

    restore_backup_button = urwid.Button("Restore")
    urwid.connect_signal(restore_backup_button, 'click', restore_screen)
    body.append(urwid.AttrMap(restore_backup_button, None, focus_map='reversed'))

    merge_button = urwid.Button('Merge')
    urwid.connect_signal(merge_button, 'click', files_screen)
    body.append(urwid.AttrMap(merge_button, None, focus_map='reversed'))

    exit = urwid.Button('Exit')
    urwid.connect_signal(exit, 'click', exit_program)
    body.append(urwid.AttrMap(exit, None, focus_map='reversed'))

    body.append(urwid.AttrMap(urwid.Divider(), None, focus_map='reversed'))
    body.append(urwid.AttrMap(urwid.Divider(), None, focus_map='reversed'))

    configSectionHeader = urwid.Text('===Config Section ===')
    body.append(urwid.AttrMap(configSectionHeader, None, focus_map='reversed'))

    body.append(urwid.AttrMap(urwid.Divider(), None, focus_map='reversed'))
    current_dir, working_dir = get_directories()
    working_dir_text = urwid.Text('Working directory is: "' + working_dir + '"')
    body.append(urwid.AttrMap(working_dir_text, None, focus_map='reversed'))
    if current_dir != working_dir:
        save_dir_button = urwid.Button(
            'Save "' + current_dir + '" as working directory')
        urwid.connect_signal(save_dir_button, 'click',
                             save_working_dir, current_dir)
        body.append(urwid.AttrMap(save_dir_button, None, focus_map='reversed'))

    body.append(urwid.AttrMap(urwid.Divider(), None, focus_map='reversed'))
    exclude = get_config_param('exclude_list').replace('|', '\n')
    excludes_header = 'Exclude List (instant save to config):\n'
    exclude_listArea = urwid.Edit(excludes_header, exclude, True)
    urwid.connect_signal(exclude_listArea, 'change', save_excludes)
    body.append(urwid.AttrMap(exclude_listArea, None, focus_map='reversed'))

    body.append(urwid.AttrMap(urwid.Divider(), None, focus_map='reversed'))
    body.append(urwid.AttrMap(urwid.Divider(), None, focus_map='reversed'))
    config_file_path_text = urwid.Text('Config File: "' + init_config() + '"')
    body.append(urwid.AttrMap(config_file_path_text, None, focus_map='reversed'))

    return body


#  RESTORE SCREENS
def restore_screen(button):
    body = program_header()
    dirs = get_directories()
    working_dir = dirs[1]
    file_list = get_file_list(working_dir)
    working_directory_header = urwid.Text('Working directory is: "' + working_dir + '"')
    body.append(urwid.AttrMap(working_directory_header,
                                 None, focus_map='reversed'))
    body.append(urwid.AttrMap(urwid.Divider(), None, focus_map='reversed'))

    back = urwid.Button('Back')
    urwid.connect_signal(back, 'click', main_screen_2)
    body.append(urwid.AttrMap(back, None, focus_map='reversed'))
    exit = urwid.Button('Exit')
    urwid.connect_signal(exit, 'click', exit_program)
    body.append(urwid.AttrMap(exit, None, focus_map='reversed'))
    body.append(urwid.AttrMap(urwid.Divider(), None, focus_map='reversed'))

    files_header = urwid.Text('(step 1 of 2) Select file to restore:')
    body.append(urwid.AttrMap(files_header, None, focus_map='reversed'))
    for c in file_list:
        selected_and_all_files = [c, file_list]
        button = urwid.Button(selected_and_all_files[0])
        urwid.connect_signal(button, 'click', restore_location_screen,
                                selected_and_all_files)
        body.append(urwid.AttrMap(button, None, focus_map='reversed'))
    main.original_widget = urwid.ListBox(urwid.SimpleFocusListWalker(body))


def restore_location_screen(button, selected_and_all_files):
    body = program_header()
    body.append(urwid.AttrMap(urwid.Divider(), None, focus_map='reversed'))
    back = urwid.Button('Back')
    urwid.connect_signal(back, 'click', restore_screen)
    body.append(urwid.AttrMap(back, None, focus_map='reversed'))
    exit = urwid.Button('Exit')
    urwid.connect_signal(exit, 'click', exit_program)
    body.append(urwid.AttrMap(exit, None, focus_map='reversed'))
    body.append(urwid.AttrMap(urwid.Divider(), None, focus_map='reversed'))

    selected_file = selected_and_all_files[0]
    all_files = selected_and_all_files[1]
    # filter files to restore: by name and from first one to selected
    files_to_restore = [x for x in all_files if x.startswith(selected_file[:-26])]
    files_to_restore = files_to_restore[:files_to_restore.index(selected_file)+1]


    files_to_restore_text = '\n  '.join(str(f) for f in files_to_restore)
    text = urwid.Text(['This archives will be extracted one by one:\n  ' + files_to_restore_text])
    body.append(urwid.AttrMap(text, None, focus_map='reversed'))
    body.append(urwid.AttrMap(urwid.Divider(), None, focus_map='reversed'))
    
    text2 = urwid.Text(['(step 2 of 2) Select extract point:'])
    body.append(urwid.AttrMap(text2, None, focus_map='reversed'))
    mountpoints = []
    for p in psutil.disk_partitions():
        button = urwid.Button(p.mountpoint)
        params = [p.mountpoint,files_to_restore]
        urwid.connect_signal(button, 'click', restore_start, params)
        body.append(urwid.AttrMap(button, None, focus_map='reversed'))

    body.append(urwid.AttrMap(urwid.Divider(), None, focus_map='reversed'))
    checkbox = urwid.CheckBox('Clear (rm -rf) extract point', False, False,set_clear_mountpoint_flag)
    checkbox.set_state(True)
    checkbox.set_state(False)
    body.append(checkbox)
    main.original_widget = urwid.ListBox(urwid.SimpleFocusListWalker(body))


def restore_start(button, params):
    global clear_mountpoint_flag
    mountpoint = params[0]
    files_to_extract = params[1]
    clear_mountpoint = clear_mountpoint_flag

    body = program_header()
    back = urwid.Button('Back to main screen')
    urwid.connect_signal(back, 'click', main_screen_2)
    body.append(back)

    subprocess.call(bin_clear)
    if clear_mountpoint:
        run_and_log([bin_rm, '-vrf', mountpoint], log_file)

    for f in files_to_extract:
        run_and_log([bin_dar, '-x', f[:-6],'-w', '-v', '-R ', mountpoint], log_file)


    main.original_widget = urwid.ListBox(urwid.SimpleFocusListWalker(body))


#  MERGE SCREENS

def files_screen(button):
    body = program_header()
    dirs = get_directories()
    working_dir = dirs[1]
    file_list = get_file_list(working_dir)
    working_directory_header = urwid.Text('Working directory is: "' + working_dir + '"')
    body.append(urwid.AttrMap(working_directory_header,
                              None, focus_map='reversed'))
    body.append(urwid.AttrMap(urwid.Divider(), None, focus_map='reversed'))

    back = urwid.Button('Back')
    urwid.connect_signal(back, 'click', main_screen_2)
    body.append(urwid.AttrMap(back, None, focus_map='reversed'))
    exit = urwid.Button('Exit')
    urwid.connect_signal(exit, 'click', exit_program)
    body.append(urwid.AttrMap(exit, None, focus_map='reversed'))
    body.append(urwid.AttrMap(urwid.Divider(), None, focus_map='reversed'))

    files_header = urwid.Text('Selected file will be merged with previous one:')
    body.append(urwid.AttrMap(files_header, None, focus_map='reversed'))
    for c in file_list:
        current_and_previous_files = [c, file_list[file_list.index(c)-1]]
        button = urwid.Button(current_and_previous_files[0])
        urwid.connect_signal(button, 'click', item_screen,
                             current_and_previous_files)
        body.append(urwid.AttrMap(button, None, focus_map='reversed'))
    main.original_widget = urwid.ListBox(urwid.SimpleFocusListWalker(body))


def item_screen(button, current_and_previous_files):
    body = program_header()
    current_file = current_and_previous_files[0]
    previous_file = current_and_previous_files[1]
    response = urwid.Text(["You chose                      : ", current_file,"\nit will be merged with this one: ", previous_file, "\n"])
    go = urwid.Button('Go!')
    urwid.connect_signal(go, 'click', run_merge, [current_file, previous_file])
    back = urwid.Button('Back')
    urwid.connect_signal(back, 'click', files_screen)
    exit = urwid.Button('Exit')
    urwid.connect_signal(exit, 'click', exit_program)
    main.original_widget = urwid.Filler(urwid.Pile([
        body[0], body[1],
        response,
        urwid.AttrMap(back, None, focus_map='reversed'),
        urwid.AttrMap(go, None, focus_map='reversed'),
        urwid.AttrMap(exit, None, focus_map='reversed')])
    )


def run_merge(button, files):
    body = program_header()
    back = urwid.Button('Back to file list')
    urwid.connect_signal(back, 'click', files_screen)
    current_file = files[0][:-6]
    previous_file = files[1][:-6]
    previous_fileFull = files[1]
    subprocess.call([bin_clear])
    cmd_merge = [bin_dar,'-ak','-+',current_file,'-A',previous_file,'-@',current_file]
    run_and_log(cmd_merge,log_file)
    cmd_remove_previous_file = [bin_rm, '-f',previous_fileFull]
    run_and_log(cmd_remove_previous_file, log_file)
    main.original_widget = urwid.Filler(urwid.Pile([
        body[0], body[1],
        urwid.AttrMap(back, None, focus_map='reversed')])
    )


# BACKUP SCREENS

def show_lvm(button):
    show_loader()
    backup_volumes_list = []
    current_dir, working_dir = get_directories()
    volumes = os.popen(bin_lvdisplay + " |" + bin_grep + " 'LV Path' | " + bin_awk + " '{print $3}'").read().strip().split('\n')

    body = program_header()
    working_dir_text = urwid.Text('Working directory is: "' + working_dir + '"')
    body.append(urwid.AttrMap(working_dir_text, None, focus_map='reversed'))
    body.append(urwid.AttrMap(urwid.Divider(), None, focus_map='reversed'))

    back = urwid.Button('Back')
    urwid.connect_signal(back, 'click', main_screen_2)
    body.append(urwid.AttrMap(back, None, focus_map='reversed'))
    backupBtn = urwid.Button('Backup')
    urwid.connect_signal(backupBtn, 'click', start_backup, backup_volumes_list)
    body.append(urwid.AttrMap(backupBtn, None, focus_map='reversed'))
    exit = urwid.Button('Exit')
    urwid.connect_signal(exit, 'click', exit_program)
    body.append(urwid.AttrMap(exit, None, focus_map='reversed'))
    body.append(urwid.AttrMap(urwid.Divider(), None, focus_map='reversed'))

    mounted_volumes_list = urwid.Text('Mounted volumes for backup:')
    body.append(urwid.AttrMap(mounted_volumes_list, None, focus_map='reversed'))
    ignored_volumes = get_config_param('ignored_volumes').split('|')
    for volume in volumes:
        for p in psutil.disk_partitions():
            if os.path.realpath(volume) == os.path.realpath(p.device):
                real_volume_path = os.path.realpath(volume)
                v_g_name = os.popen(bin_lvdisplay + " " + volume + " | grep 'VG Name' | awk '{print $3}'").read().strip()
                l_v_name = os.popen(bin_lvdisplay + " " + volume + " | grep 'LV Name' | awk '{print $3}'").read().strip()
                l_v_path = volume
                mount_point = p.mountpoint
                checkbox = urwid.CheckBox(
                    [v_g_name, '|', l_v_name, '|', l_v_path], False, False, 
                    set_volumes_list, backup_volumes_list)
                if l_v_name not in ignored_volumes:
                    checkbox.set_state(True)
                body.append(checkbox)
                body.append(urwid.AttrMap(urwid.Text('   ' + 'Volume Group: "' + v_g_name + '", mount point: "' +
                                                     mount_point + '", device name: "' + real_volume_path + '"'), None, focus_map='reversed'))
    body.append(urwid.AttrMap(urwid.Divider(), None, focus_map='reversed'))
    main.original_widget = urwid.ListBox(urwid.SimpleFocusListWalker(body))


def set_clear_mountpoint_flag(checkbox, state):
    global clear_mountpoint_flag
    if state is True:
        clear_mountpoint_flag = True
    else:
        clear_mountpoint_flag = False


def set_volumes_list(checkbox, state, backup_volumes_list):
    l_v_name = checkbox.get_label().split('|')[1]
    if state is True:
        ignored_volumes = get_config_param('ignored_volumes').split('|')
        if l_v_name in ignored_volumes:
            ignored_volumes.remove(l_v_name)
            set_config_param('ignored_volumes', '|'.join(ignored_volumes))
        if checkbox.get_label() not in backup_volumes_list:
            backup_volumes_list.append(checkbox.get_label())
    else:
        ignored_volumes = get_config_param('ignored_volumes').split('|')
        if l_v_name not in ignored_volumes:
            ignored_volumes.append(l_v_name)
            set_config_param('ignored_volumes', '|'.join(ignored_volumes))
        if checkbox.get_label() in backup_volumes_list:
            backup_volumes_list.remove(checkbox.get_label())


def start_backup(button, backup_volumes_list):
    pipe_to_log = [' | ', bin_tee, ' -a ', log_file]
    subprocess.call([bin_clear])
    print('Logging to: ' + log_file)
    for n in backup_volumes_list:
        v_g_name, l_v_name, l_v_path = n.split("|")
        timestamp = '{0:%Y-%m-%d_%H-%M-%S}'.format(datetime.datetime.now())
        backup_filename = v_g_name + '_' + l_v_name + '_' + timestamp
        backup_full_filename = backup_filename + '.1.dar'
        backup_vol_name = 'backupvol'
        backup_vol_path = l_v_path.replace(l_v_name, backup_vol_name)
        backup_tmp_mountpoint = '/tmp/darlvmbak_' + backup_filename

        nocompress_ext  = list(filter(None, get_config_param('nocompress_ext').split('|')))
        nocompress_params = []
        for i in nocompress_ext:
            nocompress_params.append('-Z')
            nocompress_params.append('\'*.' + i + '\'')

        exclude_list =  list(filter(None, get_config_param('exclude_list').split('|')))
        exclude_params = []
        for i in exclude_list:
            exclude_params.append('-P')
            exclude_params.append('\'' + i + '\'')

        file_mask = v_g_name + '_' + l_v_name + '_' + '*dar'
        files = glob.glob(file_mask)
        files.sort()
        filelist = []
        for file in files:
            filelist.append(file)

        run_and_log([bin_echo,'\n\n======\n',timestamp,v_g_name,l_v_name, '\nMaking dir:\n', backup_tmp_mountpoint, '\n'], log_file)
        os.makedirs(backup_tmp_mountpoint)
        run_and_log([bin_lvcreate,'-L2G','-s','-n', backup_vol_name, l_v_path], log_file)
        run_and_log([bin_mount, backup_vol_path, backup_tmp_mountpoint], log_file)
        cmd_backup = [bin_dar, '-zbzip2:9','-D','-R',backup_tmp_mountpoint,'-c', backup_filename] + exclude_params + nocompress_params
        if len(filelist) > 0:
            previous_backup_filename = filelist[len(filelist)-1].split('.')[0]
            cmd_backup +=  ['-A',previous_backup_filename]

        log = open(log_file,'a')
        print('[Exec] ' + subprocess.list2cmdline(cmd_backup))
        log.write(subprocess.list2cmdline(cmd_backup)+'\n')
        print('\nThis operation may takes a long time. Press CTRL-C once to abort\n')
        p = subprocess.Popen(cmd_backup, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        try:
            while p.poll() is None:
                print(p.stdout.readline())
                log.write(p.stdout.readline() + '\n')
        except KeyboardInterrupt:
            run_and_log([bin_echo, '\nAborting backup...\n'], log_file)
            cmd_rm_backup = [bin_rm,backup_full_filename]
            run_and_log([bin_echo, 'Removing dirty backup file...\n'], log_file)
            run_and_log(cmd_rm_backup, log_file)
        finally:
            log.close()

        run_and_log([bin_umount,backup_tmp_mountpoint], log_file)
        time.sleep(1)
        run_and_log([bin_lvremove,'-f',l_v_path], log_file)
        if os.path.ismount(backup_tmp_mountpoint) is not True:
            os.rmdir(backup_tmp_mountpoint)
    time.sleep(2)
    subprocess.call([bin_clear])
    main_screen_2(True)


# CONFIG

def init_config():
    config = configparser.ConfigParser()
    conf_file = os.path.expanduser("~") + '/.lvmdarbak.conf'
    if os.path.isfile(conf_file):
        return conf_file
    else:
        config.read(conf_file)
        config['DEFAULT'] = {}
        config['DEFAULT']['working_dir'] = os.getcwd()
        config['DEFAULT']['exclude_list'] = 'dev/pts|proc|floppy|cdrom'
        config['DEFAULT']['ignored_volumes'] = ''
        config['DEFAULT']['nocompress_ext'] = 'bz2|zip|rar|7z|deb|rpm'
        config['DEFAULT']['log_file'] = '/tmp/lvmdarbak.log'
        with open(conf_file, 'w') as configfile:
            config.write(configfile)
        return conf_file


def get_config_param(param, section='DEFAULT'):
    config = configparser.ConfigParser()
    conf_file = init_config()
    config.read(conf_file)
    return config[section][param]


def set_config_param(param, value, section='DEFAULT'):
    config = configparser.ConfigParser()
    conf_file = init_config()
    config.read(conf_file)
    config[section][param] = value
    with open(conf_file, 'w') as configfile:
        config.write(configfile)


# COMMON

def program_header():
    return [urwid.Text("LVM DAR Backup"), urwid.Divider()]


def show_loader():
    subprocess.call([bin_clear])
    subprocess.call([bin_echo,'Please wait...'])


def raise_root():
    euid = os.geteuid()
    if euid != 0:
        print('Script not started as root. Running sudo..')
        args = ['sudo', sys.executable] + sys.argv + [os.environ]
        # the next line replaces the currently-running process with the sudo
        os.execlpe('sudo', *args)


def exit_program(button):
    raise urwid.ExitMainLoop()


def get_directories():
    working_dir = get_config_param('working_dir')
    current_dir = os.getcwd()
    try:
        os.chdir(working_dir)
    except:
        working_dir = current_dir
    finally:
        os.chdir(working_dir)
    return [current_dir, working_dir]


def run_and_log(cmd, log_file):
    if os.path.isfile(log_file) is False:
        log = open(log_file, 'w')
        log.close()
    log = open(log_file, 'a')

    if cmd[0] is not bin_echo:
        log.write('[Exec] ' + subprocess.list2cmdline(cmd))
        print('[Exec] '+ subprocess.list2cmdline(cmd))

    proc = subprocess.Popen(cmd,stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    for line in proc.stdout:
        print(line.strip())
        log.write(line)
    proc.wait()

    log.write('\n')
    log.close()


def save_working_dir(button, working_dir):
    set_config_param('working_dir', working_dir)
    body = program_header()
    text = urwid.Text('Directory:\n    "' + working_dir +
                      '"\nsaved as working directory')
    body.append(urwid.AttrMap(text, None, focus_map='reversed'))
    back = urwid.Button('Back')
    urwid.connect_signal(back, 'click', main_screen_2)
    body.append(urwid.AttrMap(back, None, focus_map='reversed'))
    main.original_widget = urwid.ListBox(urwid.SimpleFocusListWalker(body))


def save_excludes(button, exclude_list):
    exclude_string = ''
    for e in exclude_list.split('\n'):
        if e.strip() is not '':
            exclude_string += e.strip() + '|'
    exclude_string = exclude_string[:-1]  # remove last delimiter
    set_config_param('exclude_list', exclude_string)


def get_file_list(directory):
    files = glob.glob("*.dar")
    files.sort()
    filelist = []
    for file in files:
        filelist.append(file)
    return filelist


def check_bins(programs):
    import shutil
    bins = []
    for program in programs:
        binary_path = shutil.which(program)
        if binary_path is not None:
            bins.append(binary_path)
        else:
            print(program +' not found')
            exit()
    return bins



# MAIN PROGRAM

log_file = get_config_param('log_file')
raise_root()
(bin_dar, bin_clear, bin_echo, 
 bin_tee, bin_rm, 
 bin_awk, bin_grep,
 bin_mount, bin_umount, 
 bin_lvcreate, bin_lvdisplay, bin_lvremove
)  =               check_bins((
                             'dar','clear','echo',
                             'tee', 'rm', 
                             'awk', 'grep',
                             'mount','umount',
                             'lvcreate','lvdisplay','lvremove'
                             ))

guiTitle = program_header()[1]
main = urwid.Padding(main_screen(), left=2, right=8)
top = urwid.Overlay(main, urwid.SolidFill(u'\N{MEDIUM SHADE}'),
                    align='center', width=('relative', 60),
                    valign='middle', height=('relative', 60),
                    min_width=20, min_height=9)

main_loop = urwid.MainLoop(top, palette=[('reversed', 'standout', '')])
main_loop.run()
