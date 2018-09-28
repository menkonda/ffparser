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
import time
import traceback

GLOBAL_CONFIG = config.GlobalConfig(config.GLOBAL_CONFIG_PATH)


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


class RowStructException(Exception):
    def __init__(self,  message):
        self.message = message


class TestExecException(Exception):
    def __init__(self, msg, filename, test_name):
        Exception.__init__(self, msg)
        self.msg = msg
        self.filename = filename
        self.test_name = test_name


class FlatFile(object):
    def __init__(self, file, structure):
        """
        Object holding the data and the file structure of a flat file. According to the file type "csv" or "pos"
        the lines are parsed with different methods
        :param file: file object of the file to be treated
        :param structure: file structure used to parse the file
        ..todo::create a mother class and use inheritance to manage different file type
        """
        self.structure = structure
        self.filename = file.name
        if structure.conf_type == 'csv':
            rows = list(csv.reader(file, delimiter=self.structure.sep, quotechar="\""))
        elif structure.conf_type == 'pos':
            raw_rows = [line.rstrip() for line in file]
            rows = []
            for idx, raw_row in enumerate(raw_rows):
                row = []
                index = 0
                row_type = raw_row[self.structure.type_limits[0] - 1:self.structure.type_limits[1]]
                row_structure = self.get_row_structure_from_type(row_type)
                for length in row_structure.lengths:
                    row.append(raw_row[index:index + length])
                    index = index + length
                rows.append(row)
        else:
            raise Exception("Structure conf_type must be 'pos' or 'csv'. Not " + structure.conf_type)

        self.rows = rows

    def get_row_structure_from_type(self, row_type):
        if len(self.structure.row_structures) == 0:
            raise RowStructException("No row structures")
        if len(self.structure.row_structures) == 1:
            return self.structure.row_structures[0]
        matching_row_structure = [row_struct for row_struct in self.structure.row_structures
                         if re.match(row_struct.type, row_type)]

        if len(matching_row_structure) == 0:
            return "Could not find row structure matching structure '" + row_type + "'"
        if len(matching_row_structure) > 1:
            return "More than one row structure matching structure '" + row_type + "'"

        return matching_row_structure[0]

    def parse_groups(self):
        """
        Parses a group of a rows with a give common key
        :returns: an array of grouped rows with the same key
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
        Run the test test_name. It must be implemented in a submodule within the testlib module or in a module within
        the plugin directory defined in the global config file
        :param test_name: name of the test. If two test have the same name, the first will be uesed
        :return: the result of the test inside a TestCaseResult object
        """
        for importer, modname, ispkg in pkgutil.iter_modules(ffparser.testlib.__path__):
            module = importlib.import_module("ffparser.testlib." + modname)
            if test_name in dir(module):
                test_function = getattr(module, test_name)
                del module
                try:
                    test_result = test_function(self)
                    return test_result
                except Exception as err:
                    msg = err.args[0] + ". Error during execution of test " + test_name
                    raise TestExecException(msg, self.filename, test_name)
            del module

        for importer, modname, ispkg in pkgutil.iter_modules([GLOBAL_CONFIG.plugin_dir]):
            module = importer.find_spec(modname).loader.load_module()
            if test_name in dir(module):
                test_function = getattr(module, test_name)
                del module
                try:
                    test_result = test_function(self)
                    return test_result
                except Exception as err:
                    msg = err.args[0] + ". Error during execution of test " + test_name
                    raise TestExecException(msg, self.filename, test_name)
            del module
        raise Exception("Could not find the test " + test_name + " in modules")

    def run_test_suite(self, test_list):
        """
        Run a set of tests with given names (dev)
        :param test_list: list of tests
        :return:
        """
        suite_result = ffparser.testlib.common.TestSuiteResult()
        for test in test_list:
            tc_result = self.run_test_case(test)
            suite_result.tcs.append(tc_result)
        return suite_result

    def run_defined_tests(self):
        return self.run_test_suite(self.structure.tests)

    def list_keys(self):
        return self.parse_groups().keys()


def main():
    parser = argparse.ArgumentParser(description='Check a csv file structure')
    parser.add_argument('csv_files', metavar='FILES', nargs='+',
                        help='Files to be checked')
    parser.add_argument('--config-dir',
                        metavar='CONFIG-DIR',
                        help='Directory with the file structures. Default : ' + GLOBAL_CONFIG.structures_dir,
                        default=GLOBAL_CONFIG.structures_dir)
    parser.add_argument('--file-structure', metavar='STRUCT_NAME', help='Name of the file structure to use,'
                                                                        ' by default csvchecker detects the '
                                                                        'file structure from filename pattern')
    parser.add_argument('--output-dir', metavar='OUTPUT_DIR', help='Defines the output directory. By default the '
                                                                   'directory is current directory')
    parser.add_argument('--no-output', action='store_true', help='If enabled no csv result file')
    parser.add_argument('-v', '--verbose', action='store_true', help='If enabled results will be prompted with more '
                                                                     'verbosity')
    parser.add_argument('-q', '--quiet', action='store_true', help='If enabled no result will be prompted on screen')

    args = parser.parse_args()

    if not args.output_dir:
        args.output_dir = os.getcwd()

    output_filename = os.path.join(args.output_dir, "test_" + time.strftime("%Y%m%d%H%M%S") + ".csv")
    try:
        output_file = open(output_filename, "w", newline='')
    except FileNotFoundError as e:
        print("ERROR. Could not open file ", output_filename)
        return -2

    output_csv = csv.writer(output_file, delimiter=';', quotechar="\"")
    output_csv.writerow(['FILENAME', 'LINE_NUMBER', 'STATUS', 'ERROR_TYPE', 'MESSAGE'])

    try:
        config_obj = config.ParserConfig(args.config_dir)
    except config.StructureParseException as err:
        output_csv.writerow([err.src_file,'','False','JSON_STRUCTURES_ERROR', err.args[0]])
        print(err.args[0])
        return -1

    if args.file_structure is not None and args.file_structure not in config_obj.file_structures:
        print("Error : Could not load '" + args.file_structure + " structure from available structures ")
        return 1

    if args.file_structure:
        args.file_structure = config_obj.file_structures[args.file_structure]

    csv_files = []
    for csv_file in args.csv_files:
        csv_files += glob.glob(csv_file)

    for csv_filename in csv_files:
        if not args.quiet:
            print("Checking file " + csv_filename)
        if args.file_structure is None:
            args.file_structure = get_struct_from_pattern(config_obj, csv_filename)

        if args.file_structure is None:
            if not args.quiet:
                print("Could not find any file structure for file '" + csv_filename + "'. Skipping")
            continue

        # print('File structure', args.file_structure.name)
        csv_file = open(csv_filename, "r", encoding=args.file_structure.encoding)
        flat_file = FlatFile(csv_file, args.file_structure)
        try:
            test_result = flat_file.run_defined_tests()
        except TestExecException as err:
            output_csv.writerow([err.filename, '', 'False', 'TEST_EXEC_ERROR_' + err.test_name, err.msg])
            if not args.quiet and args.verbose:
                print("Error while executing test " + err.test_name + " on file " + err.filename
                      + ". Skipping testing of file " + err.filename + ".")
                print(traceback.format_exc())
            continue

        if not args.quiet and args.verbose:
            print(test_result)
        if not args.quiet:
            print("Found " + str(test_result.count_failed()) + " errors in file " + csv_filename)
        if not args.no_output:
            test_result.to_csv(output_file)
            if not args.quiet:
                print("Results logged in file " + output_filename)
        csv_file.close()

    output_file.close()
    return 0


if __name__ == "__main__":
    result = main()
    sys.exit(result)
