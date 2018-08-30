import time
import os.path
import csv

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

    def get_test_status (self):
        if len(self.tcs) == 0:
            return None
        for line in self.tcs :
            if not line.status :
                return False
        return True

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


def get_row_structure_from_type(row_structures, row_type):
    if len(row_structures) == 0:
        raise Exception("No row structures")
    if len(row_structures) == 1:
        return row_structures[0]

    row_struct = [struct for struct in row_structures if row_type == struct.type][0]

    if not row_struct:
        raise Exception("Could not find row structure of type '" + row_type + "'")

    return row_struct


def check_dates(flat_file_object):
    """
    Check the date format of a given csv according to its structure
    :param flat_file_object: the oCsvFlatFile object containing the content of the flat file and file structure
    :return: a TesCaseResult object with all the lines and position containing date format error
    """
    result = TestCaseResult()
    for idx, row in enumerate(flat_file_object.rows):
        row_type = row[flat_file_object.structure.type_pos - 1]
        #print("DEBUG check_dates :" + str(idx) + " " + str(row_type))
        row_struct = get_row_structure_from_type(flat_file_object.structure.row_structures, row_type)
        for pos in row_struct.date_fields:
            date_string = row[pos - 1]
            if date_string == '':
                continue
            try:
                date = time.strptime(date_string, flat_file_object.structure.date_fmt)
            except ValueError:
                step_result = TestCaseStepResult(idx + 1, False, 'DATE_FORMAT', "DATE format is incorrect at position "
                                                 + str(pos) + " should be " + flat_file_object.structure.date_fmt,
                                                 os.path.basename(flat_file_object.filename))
                result.steps.append(step_result)
    return result


def check_required(flat_file_object):
    """
    Check the required fields according to file
    :param flat_file_object: the CsvFlatFile object containing the content of the flat file and file structure
    :return: a TesCaseResult object with all the lines and position containing missing fields
    """
    result = TestCaseResult()
    for idx, row in enumerate(flat_file_object.rows):
        row_type = row[flat_file_object.structure.type_pos - 1]
        row_struct = get_row_structure_from_type(flat_file_object.structure.row_structures, row_type)
        for pos in range(0, row_struct.length):
            if (pos + 1) in row_struct.optional_fields:
                continue
            if row[pos] == '':
                step_result = TestCaseStepResult(idx + 1, False, 'REQUIRED_FIELD', "Missing required field at position "
                                             + str(pos + 1), os.path.basename(flat_file_object.filename))
                result.steps.append(step_result)
    return result


def check_field_lengths(flat_file_object):
    """
    Check the lengths of mandatory fields is csv files
    :param flat_file_object:
    :return:
    """
    result = TestCaseResult()
    for idx, row in enumerate(flat_file_object.rows):
        row_type = row[flat_file_object.structure.type_pos - 1]
        row_struct = get_row_structure_from_type(flat_file_object.structure.row_structures, row_type)
        for fixed_length in row_struct.fixed_lengths:
            field_content = row[fixed_length[0] - 1]
            if field_content == '':
                continue
            if len(field_content) != fixed_length[1]:
                step_result = TestCaseStepResult(idx + 1, False, 'FIELD_LENGTH_ERROR', "Wrong field length at position "
                                                 + str(field_content), os.path.basename(flat_file_object.filename))
                result.steps.append(step_result)
    return result


def check_digit_fields(flat_file_object):
    result = TestCaseResult()
    for idx, row in enumerate(flat_file_object.rows):
        row_type = row[flat_file_object.structure.type_pos - 1]
        row_struct = get_row_structure_from_type(flat_file_object.structure.row_structures, row_type)
        for digit_field in row_struct.digit_fields:
            field_content = row[digit_field - 1]
            if field_content == '':
                continue
            if not field_content.isdigit():
                step_result = TestCaseStepResult(idx + 1, False, 'FIELD_FORMAT_ERROR',
                                                 "Field should be numeric at field " + str(digit_field) + " : "
                                                 + field_content, os.path.basename(flat_file_object.filename))
                result.steps.append(step_result)
    return result
