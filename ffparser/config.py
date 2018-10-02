import json
import os
import platform
import glob
import argparse



system = platform.system().lower()
if system not in ('linux','windows'):
    raise Exception("Unknown OS. Must be Linux or Windows")

CONF_DIR = {
    "linux": "/etc/ffparser",
    "windows": "C:\\Program Files (x86)\\Maissa\\ffparser\\conf"}
DATA_DIR = {
    "linux": "/var/lib/ffparser/",
    "windows": "C:\\Program Files (x86)\\Maissa\\ffparser\\conf"}

CONF_DATA_TYPES = ['plugins', 'structures', 'schemas']

GLOBAL_CONFIG_PATH = os.path.join(CONF_DIR[system], "global_config.json")
TEST_CONFIGS_PATH = os.path.join(DATA_DIR[system], "test_configs.json")
SCHEMAS = ['csv','pos']


def build_global_conf_file(path=GLOBAL_CONFIG_PATH):
    """
    Build global_config file from constants defined above. This function is meant to be used during the install
    :param path: (optional) path where the global config file should be installed. By default the config directory
    defined in the constants
    :return: a dictionary with the content of the global_config file
    """
    content = dict()
    content['conf_dir'] = CONF_DIR[system]
    content['test_configs'] = TEST_CONFIGS_PATH
    for type in CONF_DATA_TYPES:
        content[type + "_dir"] = os.path.join(DATA_DIR[system], type)
    content['schemas'] = {}
    for schema in SCHEMAS:
        content['schemas'][schema] = schema + "_schema.json"

    with open(path, "w") as global_config_file:
        json.dump(content, global_config_file, sort_keys=True, indent=4, separators=(',', ': '))

    return content


def create_conf_dirs():
    """
    Create the config directories according to the constants
    :return: None
    """
    conf_directory = CONF_DIR[system]

    if not os.path.exists(conf_directory):
        os.makedirs(conf_directory)

    for data in CONF_DATA_TYPES:
        data_dir = os.path.join(DATA_DIR[system], data)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)


class GlobalConfig:
    """
    Describe the structure of the global config
    """
    def __init__(self, file_path):
        self.file_path = file_path
        with open(file_path, "r") as conf_file:
            cfg = json.load(conf_file)

        self.conf_directory = cfg['conf_dir']
        self.plugin_dir = cfg['plugins_dir']
        self.structures_dir = cfg['structures_dir']
        self.schemas_dir = cfg['schemas_dir']
        self.test_configs = cfg['test_configs']


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check a csv file structure')
    parser.add_argument('structdir', metavar='FILES',
                        help='Directory where the file structures can be found')
    parser.add_argument('--pattern', metavar='PATTERN', nargs='+',
                        help='Pattern name of the structure files', default = 'struct_*.json')
    args = parser.parse_args()

    struct_filenames = glob.glob(os.path.join(args.structdir, args.pattern))
    cmd = ""

    while cmd != "exit":
        cmd = input("->")
        args = cmd.split(' ')
        func = args[0]
        args = args[1:]
        result =commands_lookup_table[func](*args)
        print(result)
