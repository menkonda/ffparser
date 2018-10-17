import csv
from ffparser import config, structure, testcase
from ffparser.testcase import TestExecException
import ffparser.testlib
import ffparser.testlib.common
import os.path
import re
import argparse
import sys
import glob
import time


GLOBAL_CONFIG = config.GlobalConfig(config.GLOBAL_CONFIG_PATH)


class FlatFile(object):
    def __init__(self, file, file_structure):
        """
        Object holding the data and the file structure of a flat file. According to the file type "csv" or "pos"
        the lines are parsed with different methods
        :param file: file object of the file to be treated
        :param file_structure: file structure used to parse the file
        """
        if type(file).__name__ == 'str':
            self.file = open(file, 'r', encoding=file_structure.encoding)
        else:
            self.file = file
        self.structure = file_structure
        self.filename = self.file.name
        # if the file structure is not csv
        if file_structure.conf_type == 'csv':
            rows = list(csv.reader(self.file, delimiter=self.structure.sep, quotechar="\""))
        elif file_structure.conf_type == 'pos':
            rows = self.get_rows_from_pos()
        else:
            raise Exception("Structure conf_type must be 'pos' or 'csv'. Not " + file_structure.conf_type)

        self.rows = rows

    def get_rows_from_pos(self):
        raw_rows = [line.rstrip() for line in self.file]
        rows = []
        for idx, raw_row in enumerate(raw_rows):
            row = []
            line_index = 0
            # to correctly cut the fields we need to refer to the correct row structure. For this we use a line type
            # whom start and stop positions are defined in the structure object
            row_type = raw_row[self.structure.type_limits[0] - 1:self.structure.type_limits[1]]
            row_structure = self.get_row_structure_from_type(row_type)
            if type(row_structure).__name__ == 'str':
                raise structure.RowStructureParseException(row_structure)

            for length in row_structure.lengths:
                # appends a field starting with the current position and ending at field length
                row.append(raw_row[line_index:line_index + length])
                line_index = line_index + length
            rows.append(row)
        return rows

    def get_row_structure_from_type(self, row_type):
        """
        Finds a row structure with the correct type within row structures available in the FlatFile object
        :param row_type: row type as a string. Regex can be used
        :return: a RowStructure object
        """
        if len(self.structure.row_structures) == 0:
            raise structure.RowStructureParseException("No row structures")
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
        global_config = config.GlobalConfig(config.GLOBAL_CONFIG_PATH)
        tc_config = testcase.get_test_case_config_from_name(test_name)
        tc = testcase.TestCase(test_name, tc_config, [global_config.plugin_dir])
        return tc.run(self)

    def run_test_suite(self, test_list):
        """
        Run a set of tests with given names
        :param test_list: list of tests
        :return:
        """
        suite_result = ffparser.testcase.TestSuiteResult()
        for test in test_list:
            tc_result = self.run_test_case(test)
            suite_result.tcs.append(tc_result)
        return suite_result

    def run_defined_tests(self):
        return self.run_test_suite(self.structure.tests)

    def list_keys(self):
        return self.parse_groups().keys()


class ImpArticleFlatFile(FlatFile):
    TCLCOD = 1
    ITMSTA = 2
    ITMREF = 3
    DES1A01 = 4
    SEAKEY = 5
    EANCOD = 6
    EECGES = 7
    CUSREF = 8
    TSICOD1 = 9
    TSICOD2 = 10
    STOMGTCOD = 11
    STU = 12
    WEU = 13
    ITMWEI = 14
    EEU = 15
    EEUSTUCOE = 16
    VACITM1 = 17
    CCE2 = 18
    DIE2 = 19
    RCPFLG = 20
    STAFED = 21
    YSISOURCE = 22
    YNOMFIC = 23
    YDATFIC = 24

    def __init__(self, file, file_structure=None):
        if file_structure is None:
            gconf = config.GlobalConfig(config.GLOBAL_CONFIG_PATH)
            file_structure = structure.get_structure_from_json(os.path.join(gconf.structures_dir, 'struct_IMP_ARTICLE.json'))

        super().__init__(file, file_structure)

    def list_skus(self):
        return [row[self.ITMREF] for row in self.rows]

    def get_rows_by_sku(self, sku):
        return [row for row in self.rows if row[self.ITMREF] == str(sku)]

    def get_rows_by_ean(self, ean):
        return [row for row in self.rows if row[self.EANCOD] == str(ean)]

    def get_rows_by_parent_sku(self, parent_sku):
        return [row for row in self.rows if row[self.SEAKEY] == str(parent_sku)]


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

    # default output is current directory
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
        config_obj = structure.get_structures_from_dir(args.config_dir)
    except (structure.StructureParseException, structure.RowStructureParseException) as err:
        output_csv.writerow([err.src_file, '', 'False', 'JSON_STRUCTURES_ERROR', err.args[0]])
        print(err.args[0])
        return -1

    if args.file_structure and args.file_structure not in config_obj.file_structures:
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
            args.file_structure = structure.get_struct_from_pattern(config_obj, csv_filename)

        if args.file_structure is None:
            if not args.quiet:
                print("Could not find any file structure for file '" + csv_filename + "'. Skipping")
            continue

        csv_file = open(csv_filename, "r", encoding=args.file_structure.encoding)
        flat_file = FlatFile(csv_file, args.file_structure)
        try:
            test_result = flat_file.run_defined_tests()
        except TestExecException as err:
            output_csv.writerow([err.filename, '', 'False', 'TEST_EXEC_ERROR_' + err.test_name, err.msg])
            if not args.quiet and args.verbose:
                print("Error while executing test " + err.test_name + " on file " + err.filename
                      + ". Skipping testing of file " + err.filename + ".")
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
        args.file_structure = None

    output_file.close()
    return 0


if __name__ == "__main__":
    result = main()
    sys.exit(result)
