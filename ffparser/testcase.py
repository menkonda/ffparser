import csv
import pkgutil
import importlib
import ffparser.testlib
from ffparser.config import GlobalConfig, GLOBAL_CONFIG_PATH
import inspect
import json


class TestExecException(Exception):
    def __init__(self, msg, filename, test_name):
        Exception.__init__(self, msg)
        self.msg = msg
        self.filename = filename
        self.test_name = test_name


def list_available_tests(plugin_dirs=None):
    """
    Lists all available test cases
    :param plugin_dirs:
    :return: Test names as a list of strings
    """
    tests = []
    for importer, modname, ispkg in pkgutil.iter_modules(ffparser.testlib.__path__):
        module = importlib.import_module("ffparser.testlib." + modname)
        tests += [attribute for attribute in dir(module) if callable(getattr(module, attribute))
                  and not inspect.isclass(getattr(module, attribute))]
        del module

    if plugin_dirs:
        for importer, modname, ispkg in pkgutil.iter_modules(plugin_dirs):
            module = importer.find_spec(modname).loader.load_module()
            tests += [attribute for attribute in dir(module) if callable(getattr(module, attribute))
                      and not inspect.isclass(getattr(module, attribute))]
            del module

    return list(set(tests))


def get_test_callable_by_name(test_name, plugin_dirs=None):
    if test_name not in (list_available_tests(plugin_dirs)):
        raise Exception("Could not find the test " + test_name + " in modules")

    for importer, modname, ispkg in pkgutil.iter_modules(ffparser.testlib.__path__):
        module = importlib.import_module("ffparser.testlib." + modname)
        if test_name in dir(module):
            test_callable = getattr(module, test_name)
            del module
            return test_callable
        del module

    if plugin_dirs:
        for importer, modname, ispkg in pkgutil.iter_modules(plugin_dirs):
            module = importer.find_spec(modname).loader.load_module()
            if test_name in dir(module):
                test_callable = getattr(module, test_name)
                return test_callable
            del module

    raise Exception("Could not find the test " + test_name + " in modules")


def get_test_case_config_from_name(test_name):
    global_config = GlobalConfig(GLOBAL_CONFIG_PATH)
    test_confs_path = global_config.test_configs
    with open(test_confs_path, 'r') as test_confs_file:
        test_confs_dict = json.load(test_confs_file)['configs']

    if test_name not in [conf['test_conf_name'] for conf in test_confs_dict]:
        test_conf_dict = [conf for conf in test_confs_dict if conf['test_conf_name'] == 'default'][0]
    else:
        test_conf_dict = [conf for conf in test_confs_dict if conf['test_conf_name'] == test_name][0]

    return TestCaseConf(test_conf_dict)
    

class TestCaseConf:
    def __init__(self, tc_conf_dict):
        required_keys = ['test_conf_name','allowed_file_types','allowed_structures','required_structure_fields','required_row_fields']
        available_keys = [key for key in tc_conf_dict]

        if not set(required_keys).issubset(available_keys):
            missing_fields  = ["'" + key + "'"for key in required_keys if key not in available_keys]
            msg = "Missing " + ", ".join(missing_fields) + " information to build test case configuration."
            raise Exception(msg)

        for key in available_keys:
            self.__dict__ [key] = tc_conf_dict[key]


class TestCase:
    def __init__(self, test_name, conf_obj, plugin_dirs=None):
        self.test_method = get_test_callable_by_name(test_name, plugin_dirs)
        self.test_name = test_name
        self.test_conf_name = conf_obj.test_conf_name
        self.allowed_file_types = conf_obj.allowed_file_types
        self.allowed_structures = conf_obj.allowed_structures
        self.required_structure_fields = conf_obj.required_structure_fields
        self.required_row_fields = conf_obj.required_row_fields

    def run(self, flat_file_object):
        if self.allowed_structures != 'all' and (flat_file_object.structure.name not in self.allowed_structures):
            msg = "Test '" + self.test_name + "' is not allowed for file structure '" \
                  + flat_file_object.structure.name + "'"
            raise TestExecException(msg, flat_file_object.filename, self.test_name)

        if self.allowed_file_types != 'all' and flat_file_object.structure.conf_type not in self.allowed_file_types:
            msg = "Test '" + self.test_name + "' is not allowed for file type '" \
                  + flat_file_object.structure.conf_type + "'"
            raise TestExecException(msg, flat_file_object.filename, self.test_name)

        structure_keys = [key for key in flat_file_object.structure.__dict__]

        if self.required_structure_fields != 'none' and not set(self.required_structure_fields).issubset(structure_keys):
            missing_fields = [field for field in self.required_structure_fields if field not in structure_keys]
            msg = "Test '" + self.test_name + "' requires missing fields : " + ",".join(missing_fields) +"."
            raise TestExecException(msg, flat_file_object.filename, self.test_name)

        row_structures = flat_file_object.structure.row_structures

        for row_structure in row_structures:
            row_structure_keys = [key for key in row_structure.__dict__]
            if self.required_row_fields != 'none' and not set(self.required_row_fields).issubset(row_structure_keys):
                missing_fields = [field for field in self.required_row_fields if field not in row_structure_keys]
                quoted_missing_fields = ["'" + field + "'" for field in missing_fields]
                msg = "Test '" + self.test_name + "' requires missing field(s) " + ", ".join(quoted_missing_fields) \
                      + " on row structure type '" + row_structure.type + "' for structure '" \
                      + flat_file_object.structure.name + "'"
                raise TestExecException(msg, flat_file_object.filename, self.test_name)

        try:
            tc_result = self.test_method(flat_file_object)
        except Exception as err:
            msg = err.args[0] + ". Error during execution of test " + self.test_name
            raise TestExecException(msg, flat_file_object.filename, self.test_name)

        return tc_result


class TestCaseStepResult(object):
    def __init__(self, line_number, status, error_type, message, filename=""):
        self.status = status
        self.error_type = error_type
        self.message = message
        self.filename = filename
        self.line_number = line_number

    def __str__(self):
        return self.filename + ";line " + str(self.line_number) + ";" + str(self.status) + ";" \
               + self.error_type + ";" + self.message


class TestCaseResult(object):
    def __init__(self):
        self.status = None
        self.steps = []

    def set_status(self):
        if len(self.steps) == 0:
            self.status = None
            return None

        for step in self.steps :
            if not step.status :
                self.status = False
                return False

        self.status = True
        return True

    def __str__(self):
        return "\n".join([step.__str__() for step in self.steps])

    def count_passed(self):
        return len([step for step in self.steps if step.status])

    def count_failed(self):
        return len([step for step in self.steps if not step.status])


class TestSuiteResult(object):
    def __init__(self):
        self.status = None
        self.tcs = []

    def set_test_status (self):
        """
        Set the status of the test suite according to the test cases result
        :return: The status of the test suite
        """
        if len(self.tcs) == 0:
            self.status = None
        for line in self.tcs :
            if not line.status :
                self.status = False
        self.status = True
        return self.status

    def count_passed(self):
        return sum([tc.count_passed() for tc in self.tcs])

    def count_failed(self):
        return sum([tc.count_failed() for tc in self.tcs])

    def __str__(self):
        return "\n".join([tc.__str__() for tc in self.tcs])

    def to_csv(self, file):
        csv_writer = csv.writer(file, delimiter=';', quotechar="\"")
        for tc in self.tcs:
            for step in tc.steps:
                csv_writer.writerow([step.filename, str(step.line_number),  str(step.status),
                                     step.error_type, step.message])