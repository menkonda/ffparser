import json
import os
import platform


def get_conf_directory():
    system = platform.system()
    if system == "Windows":
        return os.path.normpath(os.getenv("USERPROFILE")) + "\\AppData\\Local\\Maissa\\ffparser"
    elif system == "Linux":
        return "/etc/ffparser"
    else:
        raise Exception("Unknown OS. Must be Linux or Windows")


CONFIG_FILE = os.path.join(get_conf_directory(), "config.json")
GLOBAL_CONFIG_FILE = os.path.join(get_conf_directory(), "global_config.json")

class CsvRowStructure(object):
    """
    Structure of a row in a csv flat file
    """
    def __init__(self, type, length, date_fields, key_pos, optional_fields, decimal_fields, digit_fields,
                 fixed_lengths):
        """
        Instantiate a new row structure.
        :param type: The type of the row. Usuallly, a row type is a letter. For example "E" for "En-tête", "L" for Line
        rows. (string)
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
        self.type = type
        self.length = length
        self.key_pos = key_pos
        self.optional_fields = optional_fields
        self.decimal_fields = decimal_fields
        self.digit_fields = digit_fields
        self.date_fields = date_fields
        self.fixed_lengths = fixed_lengths


class CsvFlatFileStructure(object):
    """
    Describes the structure of csv flat file
    """
    def __init__(self, name, conf_type, type_pos, date_fmt, row_structures,decimal_sep, file_pattern, tests, sep,
                 encoding, quotechar):
        """
        Constructor of a flat file structure
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


class CsvParserConfig(object):
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

        for file_struct_name in cfg['file_structures']:
            file_structure = cfg['file_structures'][file_struct_name]
            conf_type = file_structure['conf_type']
            type_pos = file_structure['type_pos']
            date_fmt = file_structure['date_fmt']
            decimal_sep = file_structure['decimal_sep']
            file_pattern = file_structure['file_pattern']
            tests = file_structure['tests']
            sep = file_structure['sep']
            quotechar = file_structure['quotechar']
            encoding = file_structure['encoding']
            row_structures = []
            for row_structure in file_structure['row_structures']:
                structure = CsvRowStructure(row_structure['type'], row_structure['length'],
                                            row_structure['date_fields'], row_structure['key_pos'],
                                            row_structure['optional_fields'], row_structure['decimal_fields'],
                                            row_structure['digit_fields'],row_structure["fixed_lengths"])
                row_structures.append(structure)
            self.file_structures[file_struct_name]=CsvFlatFileStructure(file_struct_name, conf_type, type_pos, date_fmt,
                                                                        row_structures, decimal_sep, file_pattern,
                                                                        tests, sep, encoding, quotechar)



class GlobalConfig:
    def __init__(self, file_path):
        self.file_path = file_path
        conf_file = open(file_path, "r")
        cfg = json.load(conf_file)

        self.conf_directory = cfg['conf_directory']
        self.plugin_dir = cfg['plugin_dir']
