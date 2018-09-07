import json
import os
import platform


def get_conf_directory():
    """
    This function returns the configuration directory depending on the OS
    :return:
    """
    system = platform.system()
    if system == "Windows":
        return os.path.normpath(os.getenv("USERPROFILE")) + "\\AppData\\Local\\Maissa\\ffparser"
    elif system == "Linux":
        return "/etc/ffparser"
    else:
        raise Exception("Unknown OS. Must be Linux or Windows")


def get_csv_file_struct_from_dict(fs_name, fs_dict):
    """
    Returns a csv file structure object given a dictionary with correct information. Usually loaded from a JSON.
    :param fs_name: name of the file structure.
    :param fs_dict: dictionary loaded from a json holding the file structure
    :return: a CsvFlatFileStructure object
    """
    conf_type = fs_dict['conf_type']
    type_pos = fs_dict['type_pos']
    date_fmt = fs_dict['date_fmt']
    decimal_sep = fs_dict['decimal_sep']
    file_pattern = fs_dict['file_pattern']
    tests = fs_dict['tests']
    sep = fs_dict['sep']
    quotechar = fs_dict['quotechar']
    encoding = fs_dict['encoding']
    carriage_return = fs_dict['carriage_return']
    row_structures = []
    for row_structure in fs_dict['row_structures']:
        structure = CsvRowStructure(row_structure['type'], row_structure['length'],
                                    row_structure['date_fields'], row_structure['key_pos'],
                                    row_structure['optional_fields'], row_structure['decimal_fields'],
                                    row_structure['digit_fields'], row_structure["fixed_lengths"])
        row_structures.append(structure)

    return CsvFlatFileStructure(fs_name, conf_type, type_pos, date_fmt,  row_structures, decimal_sep, file_pattern,
                                tests, sep, encoding, quotechar,carriage_return)


def get_pos_file_struct_from_dict(fs_name, fs_dict):
    """
    Returns a pos file structure object given a dictionary with correct information. Usually loaded from a JSON.
    :param fs_name: name of the file structure.
    :param fs_dict: dictionary loaded from a json holding the file structure
    :return: a PosFlatFileStructure object
    """
    conf_type = fs_dict['conf_type']
    type_pos = fs_dict['type_pos']
    date_fmt = fs_dict['date_fmt']
    decimal_sep = fs_dict['decimal_sep']
    file_pattern = fs_dict['file_pattern']
    tests = fs_dict['tests']
    quotechar = fs_dict['quotechar']
    encoding = fs_dict['encoding']
    carriage_return = fs_dict['carriage_return']
    row_structures = []
    for row_structure in fs_dict['row_structures']:
        structure = PosRowStructure(row_structure['type'], row_structure['lengths'],
                                    row_structure['date_fields'], row_structure['key_pos'],
                                    row_structure['optional_fields'], row_structure['decimal_fields'],
                                    row_structure['digit_fields'])
        row_structures.append(structure)
    return PosFlatFileStructure(fs_name, conf_type, type_pos, date_fmt,
                                row_structures, decimal_sep, file_pattern, tests, encoding, quotechar, carriage_return)


CONFIG_FILE = os.path.join(get_conf_directory(), "config.json")
GLOBAL_CONFIG_FILE = os.path.join(get_conf_directory(), "global_config.json")


class CsvRowStructure(object):
    """
    Structure of a row in a csv flat file
    """
    def __init__(self, row_type, length, date_fields, key_pos, optional_fields, decimal_fields, digit_fields,
                 fixed_lengths):
        """
        Instantiate a new row structure.
        :param row_type: The type of the row. Usuallly, a row type is a letter. For example "E" for "En-tête", "L" for
        Line rows. (string)
        :param length: number of fields in the row. (integer)
        :param date_fields: fields containing dates. Used to check date formats. array(integer)
        :param key_pos: Several line types can be related. For example, for an invoice, you may have a header line,
        then several detail lines, detailing the content of the invoice. They are related through a common invoice ID.
        This ID is the key to group the lines and treat them together. The key_pos parameter sets, for given line type,
        the position of the field where this key can be found. (integer)
        :param optional_fields: the fields with optional parameters. Used to check the required fields.array(integer)
        :param decimal_fields: the fields with decimal values. Used to check the decimal format and separator.
        array(integer)
        :param digit_fields: the fields containing digits. array(integer)
        :param fixed_lengths: A list of pairs. [(5,8),(2,4)] meaning that filed 5 must be 8 chars and 2 must be 4 chars
        """
        self.type = row_type
        self.length = length
        self.key_pos = key_pos
        self.optional_fields = optional_fields
        self.decimal_fields = decimal_fields
        self.digit_fields = digit_fields
        self.date_fields = date_fields
        self.fixed_lengths = fixed_lengths


class PosRowStructure(object):
    """
    Structure of a row in a positional flat file
    """
    def __init__(self, row_type, lengths, date_fields, key_pos, optional_fields, decimal_fields, digit_fields):
        """
        Instantiate a new row structure.
        :param row_type: The type of the row. Usuallly, a row type is a letter. For example "E" for "En-tête", "L" for
        Line rows. (string)
        :param lengths: lengths of the fields
        :param date_fields: fields containing dates. Used to check date formats. array(integer)
        :param key_pos: Several line types can be related. For example, for an invoice, you may have a header line,
        then several detail lines, detailing the content of the invoice. They are related through a common invoice ID.
        This ID is the key to group the lines and treat them together. The key_pos parameter sets, for given line type,
        the position of the field where this key can be found. (integer)
        :param optional_fields: the fields with optional parameters. Used to check the required fields.array(integer)
        :param decimal_fields: the fields with decimal values. Used to check the decimal format and separator.
        array(integer)
        :param digit_fields: the fields containing digits. array(integer)
        """
        self.type = row_type
        self.lengths = lengths
        self.key_pos = key_pos
        self.optional_fields = optional_fields
        self.decimal_fields = decimal_fields
        self.digit_fields = digit_fields
        self.date_fields = date_fields


class CsvFlatFileStructure(object):
    """
    Describes the structure of csv flat file
    """
    def __init__(self, name, conf_type, type_pos, date_fmt, row_structures,decimal_sep, file_pattern, tests, sep,
                 encoding, quotechar, carriage_return):
        """
        Constructor of a csv flat file structure
        :param name: name of thh structure. It should be defined in the configuration file
        :param conf_type: type of configuration. Can be 'csv' or 'pos'
        :param type_pos: position of the field in which the line type can be found. Start at 1
        :param date_fmt: date format https://docs.python.org/3.6/library/datetime.html#strftime-and-strptime-behavior
        :param row_structures: list of structures as CsvRowStructure objects
        :param decimal_sep: default decimal separator
        :param tests: tests associated with the file structure. The name of the tests are the name of the functions in
        the test_lib module
        :param sep: CSV separator
        :param encoding: encoding used for decryption
        :param quotechar: quotechar
        """
        self.name = name
        self.conf_type = conf_type
        self.type_pos = type_pos
        self.date_fmt = date_fmt
        self.row_structures = row_structures
        self.decimal_sep = decimal_sep
        self.file_pattern = file_pattern
        self.tests = tests
        self.sep = sep
        self.encoding = encoding
        self.quotechar = quotechar
        self.carriage_return = carriage_return


class PosFlatFileStructure(object):
    """
    Describes the structure of positional flat file
    """
    def __init__(self, name, conf_type, type_pos, date_fmt, row_structures,decimal_sep, file_pattern, tests,
                 encoding, quotechar, carriage_return):
        """
        Constructor of a positional flat file structure
        :param name: name of thh structure. It should be defined in the configuration file
        :param conf_type: type of configuration. Can be 'csv' or 'pos'
        :param type_pos: position of the field in which the line type can be found. Start at 1
        :param date_fmt: date format https://docs.python.org/3.6/library/datetime.html#strftime-and-strptime-behavior
        :param row_structures: list of structures as CsvRowStructure objects
        :param decimal_sep: default decimal separator
        :param tests: tests associated with the file structure. The name of the tests are the name of the functions in
        the test_lib module
        :param encoding: encoding used for decryption
        :param quotechar: quotechar
        """
        self.name = name
        self.conf_type = conf_type
        self.type_pos = type_pos
        self.date_fmt = date_fmt
        self.row_structures = row_structures
        self.decimal_sep = decimal_sep
        self.file_pattern = file_pattern
        self.tests = tests
        self.encoding = encoding
        self.quotechar = quotechar
        self.carriage_return = carriage_return


class ParserConfig(object):
    """
    Object containing the configuration of the parser. Among other, a list of available
    """
    def __init__(self, file_path):
        """
        Instantiates a new config object
        :param file_path: path to a json with following structure
        """
        self.file_path = file_path
        self.file_structures = {}
        conf_file = open(file_path, "r")
        cfg = json.load(conf_file)

        for file_structure_name in cfg['file_structures']:
            file_structure_dict = cfg['file_structures'][file_structure_name]
            if file_structure_dict['conf_type'] == "csv":
                self.file_structures[file_structure_name] = get_csv_file_struct_from_dict(file_structure_name,
                                                                                          file_structure_dict)
            if file_structure_dict['conf_type'] == "pos":
                self.file_structures[file_structure_name] = get_pos_file_struct_from_dict(file_structure_name,
                                                                                          file_structure_dict)


class GlobalConfig:
    def __init__(self, file_path):
        self.file_path = file_path
        conf_file = open(file_path, "r")
        cfg = json.load(conf_file)

        self.conf_directory = cfg['conf_directory']
        self.plugin_dir = cfg['plugin_dir']

