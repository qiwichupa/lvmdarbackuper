#!/usr/bin/env python3
# ver 0.02.1

import configparser
import datetime
import glob
import os
import psutil
import re
import sys
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
    merge_button = urwid.Button("To merge")
    urwid.connect_signal(merge_button, 'click', files_screen)
    body.append(urwid.AttrMap(merge_button, None, focus_map='reversed'))
    create_backup_button = urwid.Button("Create Backup")
    urwid.connect_signal(create_backup_button, 'click', show_lvm)
    body.append(urwid.AttrMap(create_backup_button, None, focus_map='reversed'))
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
    os.system(bin_clear + ' &&  ' + bin_dar + '  -ak -+ "' + current_file + '" -A "' + previous_file + '" -@ "' + current_file + '" && ' + bin_rm + ' -f "' + previous_fileFull + '" ; read -p "Press any key to continue"; ' + bin_clear)
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
    #
    os.system(bin_clear)
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
    log_file = '/tmp/darlvmbackup.log'
    os.system(bin_clear)
    print('Logging to: ' + log_file)
    for n in backup_volumes_list:
        v_g_name, l_v_name, l_v_path = n.split("|")
        timestamp = '{0:%Y-%m-%d_%H-%M-%S}'.format(datetime.datetime.now())
        backup_filename = v_g_name + '_' + l_v_name + '_' + timestamp
        backup_vol_name = 'backupvol'
        backup_vol_path = l_v_path.replace(l_v_name, backup_vol_name)
        backup_tmp_mountpoint = '/tmp/darlvmbak_' + backup_filename

        nocompress_ext  = list(filter(None, get_config_param('nocompress_ext').split('|')))
        nocompress_string = ''.join([ '-Z \'*.{}\' '.format(ex) for ex in nocompress_ext ])

        exclude_list =  list(filter(None, get_config_param('exclude_list').split('|')))
        exclude_string = ''.join([ '-P {} '.format(ex) for ex in exclude_list ])

        file_mask = v_g_name + '_' + l_v_name + '_' + '*dar'
        files = glob.glob(file_mask)
        files.sort()
        filelist = []
        for file in files:
            filelist.append(file)

        os.system(bin_echo + ' ${volgroup}_${volume} >> ' + log_file)
        os.system(bin_echo + ' "\n\n======\n' + timestamp + '  ' +
                  v_g_name + ' ' + l_v_name + '" | ' + bin_tee + ' -a ' + log_file)
        os.makedirs(backup_tmp_mountpoint)
        os.system(bin_lvcreate + ' -L2G -s -n "' + backup_vol_name + '"  "' + l_v_path + '" | '+ bin_tee + ' -a ' + log_file)
        os.system(bin_mount + ' "' + backup_vol_path + '" "' + backup_tmp_mountpoint + '"')
        try:
            if len(filelist) > 0:
                lastBackupName = filelist[len(filelist)-1].split('.')[0]
                print('dar -zbzip2:9 -D -R "' + backup_tmp_mountpoint + '" -c ' + '"./' + backup_filename +
                      '" ' + exclude_string + ' ' + nocompress_string + ' -A "' + lastBackupName + '"')
                print('\nThis operation can take a long time. Press CTRL+C once to abort\n')
                os.system(bin_dar + ' -zbzip2:9 -D -R "' + backup_tmp_mountpoint + '" -c ' + '"./' + backup_filename + '" ' +
                          exclude_string + ' ' + nocompress_string + ' -A "' + lastBackupName + '" | ' + bin_tee + ' -a ' + log_file)
            else:
                print(bin_dar + ' -zbzip2:9 -D -R "' + backup_tmp_mountpoint + '" -c ' + '"./' + backup_filename + '" ' + exclude_string + ' ' + nocompress_string)
                print('\nThis operation can take a long time. Press CTRL+C once to abort\n')
                os.system('dar -zbzip2:9 -D -R "' + backup_tmp_mountpoint + '" -c ' + '"./' + backup_filename + '" ' + exclude_string + ' ' + nocompress_string + ' | tee -a ' + log_file)
        except KeyboardInterrupt:
            pass
        os.system(bin_umount + ' "' + backup_tmp_mountpoint + '"')
        os.system(bin_echo + ' y | ' + bin_lvremove  + ' "' + l_v_path + '" | ' +  bin_tee + ' -a ' + log_file)
        if os.path.ismount(backup_tmp_mountpoint) is not True:
            os.rmdir(backup_tmp_mountpoint)
    #input("Press Enter to continue...")
    show_lvm(button)


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
    os.system('clear ; echo "Please wait..."')


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
