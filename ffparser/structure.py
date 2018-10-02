import json
import glob
import os.path
import re

CSV_FILE_STRUCT_MANDATORY_PROPS = ["name","conf_type","sep","quotechar","encoding","type_pos","date_fmt","decimal_sep","tests","file_pattern","carriage_return","row_structures"]
CSV_ROW_MANDATORY_PROPS = ['length', 'date_fields', 'key_pos', 'optional_fields', 'decimal_fields', 'digit_fields',
                           'fixed_lengths', 'fixed_values']

POS_FILE_STRUCT_MANDATORY_PROPS = ["name","conf_type","encoding","type_pos","date_fmt","decimal_sep","tests","file_pattern","carriage_return","row_structures"]
POS_ROW_MANDATORY_PROPS = ['lengths','date_fields', 'key_pos', 'decimal_fields', 'digit_fields', 'fixed_values']


class StructureParseException(Exception):
    def __init__(self, msg, src_file):
        Exception.__init__(self, msg)
        self.src_file = src_file


class RowStructureParseException(Exception):
    def __init__(self,  msg, src_file = ""):
        Exception.__init__(self, msg)
        self.msg = msg
        self.src_file = src_file


class RowStructure(object):
    """
    Structure of a row in a csv flat file
    """
    def __init__(self, row_struct_dict, filetype):
        """
        Instantiate a new row structure from a dictionary object
        """
        if filetype == 'csv':
            mandatory_props = CSV_ROW_MANDATORY_PROPS
        elif filetype == 'pos':
            mandatory_props = POS_ROW_MANDATORY_PROPS
        else:
            raise RowStructureParseException("filetype must be 'pos' or 'csv' instead of " + filetype)

        keys = [key for key in row_struct_dict]
        if 'type' not in keys:
            raise RowStructureParseException("'type' property is mandatory in row structure")
        row_type = row_struct_dict['type']
        if not set(mandatory_props).issubset(keys):
            missing_props = [prop for prop in mandatory_props if prop not in keys]
            raise RowStructureParseException("Missing following properties in row structure for type'" + row_type
                                             + "' : " + ", ".join(missing_props) + ".")

        for key in keys:
            self.__dict__[key] = row_struct_dict[key]
        if 'type' not in row_struct_dict:
            raise RowStructureParseException("'type' property is mandatory in row structure")


class FlatFileStructure(object):
    """
    Structure of a csv flat file
    """
    def __init__(self, flat_file_struct_dict):
        """
        Instantiate a new flat file structure from a dictionnary
        """
        keys = [key for key in flat_file_struct_dict]
        if 'conf_type' not in keys:
            raise RowStructureParseException("'conf_type' property is mandatory in flat file structure")

        filetype = flat_file_struct_dict['conf_type']

        if filetype == 'csv':
            mandatory_props = CSV_FILE_STRUCT_MANDATORY_PROPS
        elif filetype == 'pos':
            mandatory_props = POS_FILE_STRUCT_MANDATORY_PROPS
        else:
            raise RowStructureParseException("filetype must be 'pos' or 'csv' instead of " + filetype)

        keys = [key for key in flat_file_struct_dict]

        if not set(mandatory_props).issubset(keys):
            missing_props = [prop for prop in mandatory_props if prop not in keys]
            raise RowStructureParseException("Missing following properties in file structure '"
                                             + flat_file_struct_dict['name'] + "' : "
                                             + ", ".join(missing_props) + ".")

        for key in keys:
            self.__dict__[key] = flat_file_struct_dict[key]

        self.row_structures = []
        row_structures_array = flat_file_struct_dict['row_structures']
        for row_struct_dict in row_structures_array:
            try:
                row_structure = RowStructure(row_struct_dict, filetype)
            except RowStructureParseException as err:
                print("Row structure error in structure", "'" + self.name + "'",err.msg)
                raise err

            if filetype == 'pos':
                row_structure.length = len(row_structure.lengths)
            self.row_structures.append(row_structure)

    def __str__(self):
        result = ""
        for att in self.__dict__:
            if att != "row_structures":
                result += str(att) + " : " + str(self.__dict__[att]) + "\r\n"
        for row_structure in self.row_structures:
            result += "Row structure type : " +  str(row_structure.type) + "\r\n"
            for att in row_structure.__dict__:
                result += "\t-" + att + " : " + str(row_structure.__dict__[att]) + "\r\n"

        return result


def get_structure_from_json(file_path):
    try:
        with open(file_path, 'r') as struct_file:
            structure_dict = json.load(struct_file)
    except json.JSONDecodeError as err:
        msg = "ERROR: Could not decode " + file_path + " configuration file due to following error : " \
              + err.msg + " line " + str(err.lineno) + " column " + str(err.colno)
        raise StructureParseException(msg, file_path)

    result = FlatFileStructure(structure_dict)

    return result


def get_structures_from_dir(structures_dir_path, pattern ="struct_*.json"):
    """
    Instantiates a new config object
    :param structures_dir_path: path to a directory containing jsons with following structure
    """
    structures = {}
    structure_filenames = glob.glob(os.path.join(structures_dir_path, pattern))

    for structure_filename in structure_filenames:
        structure = get_structure_from_json(structure_filename)
        structures[structure.name] = structure
    return structures


def get_struct_from_pattern(structures, filepath):
    """
    Search in the configuration object for a file structure matching the pattern of the file
    :param conf_obj: CsvParserConfig object
    :param filepath: path to the file to parse
    :return: A CsvFlatFileStructure object
    """
    basename = os.path.basename(filepath)
    structures = [structures[struct_name] for struct_name in structures
                  if re.match(structures[struct_name].file_pattern, basename)]

    if len(structures) == 0:
        return None
    if len(structures) != 1:
        raise Exception("More than one structure found for this pattern")

    return structures[0]