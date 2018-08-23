import csv
from ffparser import config
import ffparser.testlib
import ffparser.testlib.common
import pkgutil
import importlib
import os.path
import re
import argparse
import sys
import glob

GLOBAL_CONFIG = config.GlobalConfig(config.GLOBAL_CONFIG_FILE)

def get_struct_from_pattern(conf_obj, filepath):
    """
    Search in the configuration object for a file structure matching the pattern of the file
    :param conf_obj: CsvParserConfig object
    :param filepath: path to the file to parse
    :return: A CsvFlatFileStructure object
    """
    basename = os.path.basename(filepath)
    conf_structures = conf_obj.file_structures

    structures = [conf_structures[struct_name] for struct_name in conf_structures
                  if re.match(conf_structures[struct_name].file_pattern, basename)]

    if len(structures) == 0:
        return None
    if len(structures) != 1:
        raise Exception("More than one structure found for this pattern")

    return structures[0]


class CsvFlatFile(object):
    def __init__(self, file, structure):
        self.structure = structure
        self.filename = file.name
        rows = list(csv.reader(file, delimiter=self.structure.sep, quotechar="\""))
        self.rows = rows

    def parse_groups(self):
        """
        Parses a group of a rows with a give common key
        :returns: an array og rows with the same key
        """
        groups = {}
        for idx, row in enumerate(self.rows):
            row_type = row[self.structure.type_pos - 1]
            keys = [struct.key_pos for struct in self.structure.row_structures if row_type == struct.type]
            if len(keys) == 0:
                raise Exception("Could not find key for line type" + row_type + ". Row " + str(idx) + " of file "
                                + self.filename)
            key_pos = keys[0]
            row_key = row[key_pos - 1]
            if row_key not in groups:
                groups[row_key] = []
            groups[row_key].append(row)

        return groups

    def run_test_case(self, test_name):
        """
        Run the test test_name. It must be implemented in a submodule within the testlib module
        :param test_name: name of the test. If two test have the same name, the first will be uesed
        :return: the result of the test inside a TestCaseResult object
        """
        for importer, modname, ispkg in pkgutil.iter_modules(ffparser.testlib.__path__):
            module = importlib.import_module("ffparser.testlib." + modname)
            if test_name in dir(module):
                test_function = getattr(module, test_name)
                del module
                return test_function(self)
            del module

        for importer, modname, ispkg in pkgutil.iter_modules([GLOBAL_CONFIG.plugin_dir]):
            module = importer.find_spec(modname).loader.load_module()
            if test_name in dir(module):
                test_function = getattr(module, test_name)
                del module
                return test_function(self)
            del module
        raise Exception("Could not find the test in modules")

    def run_test_suite(self, test_list):
        suite_result = ffparser.testlib.common.TestSuiteResult()
        for test in test_list:
            tc_result = self.run_test_case(test)
            suite_result.tcs.append(tc_result)
        return suite_result

    def run_defined_tests(self):
        return self.run_test_suite(self.structure.tests)

    def list_keys(self):
        return self.parse_groups().keys()


class ImpRecFlatFile(CsvFlatFile):
    def __init__(self, file, config_object):
        structure = config_object.file_structures['imp_rec']
        CsvFlatFile.__init__(self, file, structure)

    def get_reception_by_id(self, reception_id):
        return self.parse_groups()[reception_id]


def main():
    parser = argparse.ArgumentParser(description='Check a csv file structure')
    parser.add_argument('csv_files', metavar='FILES', nargs='+',
                        help='Files to be checked')
    parser.add_argument('--config_file', metavar='CONFIG_FILE', help='Configuration file with the file structures.'
                                                                     ' By default the file is ' + config.CONFIG_FILE,
                        default=config.CONFIG_FILE)
    parser.add_argument('--file_structure', metavar='STRUCT_NAME', help='Name of the file structure to use,'
                                                                        ' by default csvchecker detects the '
                                                                        'file structure from filename pattern')
    parser.add_argument('--output-dir', metavar='OUTPUT_DIR', help='Defines the output directory. By default the '
                                                                   'directory is current directory')
    parser.add_argument('--no-output', action='store_true', help='If enabled no csv result file')
    parser.add_argument('-v', '--verbose', action='store_true', help='If enabled results will be prompted with more '
                                                                     'verbosity')
    parser.add_argument('-q', '--quiet', action='store_true', help='If enabled no result will be prompted on screen')

    args = parser.parse_args()
    # print(args)

    config_obj = config.CsvParserConfig(args.config_file)

    if args.file_structure is not None and args.file_structure not in config_obj.file_structures:
        print("Error : Could not load '" + args.file_structure + " structure from config file ")
        sys.exit(1)

    if args.file_structure:
        file_structure = config_obj.file_structures[args.file_structure]

    if not args.output_dir:
        args.output_dir = os.getcwd()

    csv_files = []
    for csv_file in args.csv_files:
        csv_files += glob.glob(csv_file)

    for csv_filename in csv_files:
        if not args.quiet:
            print("Checking file " + csv_filename)
        if args.file_structure is None:
            file_structure = get_struct_from_pattern(config_obj, csv_filename)
        csv_file = open(csv_filename, "r", encoding=file_structure.encoding)
        flat_file = CsvFlatFile(csv_file, file_structure)
        result = flat_file.run_defined_tests()
        if not args.quiet and args.verbose:
            print(result)
        if not args.quiet:
            print("Found " + str(result.count_failed()) + " errors in file " + csv_filename)
        output_filename = os.path.join(args.output_dir, "test_" + str(os.path.basename(csv_filename)))
        if not args.no_output:
            with open(output_filename, "w", newline='') as output_file:
                result.to_csv(output_file)
            if not args.quiet:
                print("Results logged in file " + output_filename)


if __name__ == "__main__":
    main()
