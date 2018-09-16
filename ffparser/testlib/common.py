import time
import os.path
import csv
import ffparser.csvchecker

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


def check_dates(flat_file_object):
    """
    Check the date format of a given csv according to its structure
    :param flat_file_object: the FlatFile object containing the content of the flat file and file structure
    :return: a TesCaseResult object with all the lines and position containing date format error
    """
    result = TestCaseResult()
    for idx, row in enumerate(flat_file_object.rows):
        row_type = row[flat_file_object.structure.type_pos - 1]
        row_struct = flat_file_object.get_row_structure_from_type(row_type)



        # DISGUSTING : to be handled with custom exceptions in method get_row_structure_from_type
        if type(row_struct).__name__ == 'str':
            step_result = TestCaseStepResult(idx + 1, False, 'ROW_STRUCT_ERROR', row_struct,
                                             os.path.basename(flat_file_object.filename))
            result.steps.append(step_result)
            continue

        if len(row) != row_struct.length:
            step_result = TestCaseStepResult(idx + 1, False, 'ROW_STRUCT_ERROR', "Wrong number or fields for this row",
                                             os.path.basename(flat_file_object.filename))
            result.steps.append(step_result)
            continue

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
    :param flat_file_object: the FlatFile object containing the content of the flat file and file structure
    :return: a TesCaseResult object with all the lines and position containing missing fields
    """
    result = TestCaseResult()
    for idx, row in enumerate(flat_file_object.rows):
        row_type = row[flat_file_object.structure.type_pos - 1]
        row_struct = flat_file_object.get_row_structure_from_type(row_type)
        if type(row_struct).__name__ == 'str':
            step_result = TestCaseStepResult(idx + 1, False, 'ROW_STRUCT_ERROR', row_struct,
                                             os.path.basename(flat_file_object.filename))
            result.steps.append(step_result)
            continue

        if len(row) != row_struct.length:
            step_result = TestCaseStepResult(idx + 1, False, 'ROW_STRUCT_ERROR', "Wrong number or fields for this row",
                                             os.path.basename(flat_file_object.filename))
            result.steps.append(step_result)
            continue

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
    :param flat_file_object: the FlatFile object containing the content of the flat file and file structure
    :return:a TesCaseResult object with all the lines and position with wrong field length
    """
    result = TestCaseResult()
    for idx, row in enumerate(flat_file_object.rows):
        row_type = row[flat_file_object.structure.type_pos - 1]
        row_struct = flat_file_object.get_row_structure_from_type(row_type)
        if type(row_struct).__name__ == 'str':
            step_result = TestCaseStepResult(idx + 1, False, 'ROW_STRUCT_ERROR', row_struct,
                                             os.path.basename(flat_file_object.filename))
            result.steps.append(step_result)
            continue

        if len(row) != row_struct.length:
            step_result = TestCaseStepResult(idx + 1, False, 'ROW_STRUCT_ERROR', "Wrong number or fields for this row",
                                             os.path.basename(flat_file_object.filename))
            result.steps.append(step_result)
            continue

        for fixed_length in row_struct.fixed_lengths:
            field_content = row[fixed_length[0] - 1]
            if field_content == '':
                continue
            if len(field_content) != fixed_length[1]:
                step_result = TestCaseStepResult(idx + 1, False, 'FIELD_LENGTH_ERROR', "Wrong field length at position "
                                                 + str(fixed_length[0]) + ". Should be " + str(fixed_length[1]), os.path.basename(flat_file_object.filename))
                result.steps.append(step_result)
    return result


def check_digit_fields(flat_file_object):
    """
    Check if fields defined as numeric are only made of digits
    :param flat_file_object: he FlatFile object containing the content of the flat file and file structure
    :return: a TesCaseResult object with all the lines and position containing alpha instead of digit fields
    """
    result = TestCaseResult()
    for idx, row in enumerate(flat_file_object.rows):
        row_type = row[flat_file_object.structure.type_pos - 1]
        row_struct = flat_file_object.get_row_structure_from_type(row_type)
        if type(row_struct).__name__ == 'str':
            step_result = TestCaseStepResult(idx + 1, False, 'ROW_STRUCT_ERROR', row_struct,
                                             os.path.basename(flat_file_object.filename))
            result.steps.append(step_result)
            continue

        if len(row) != row_struct.length:
            step_result = TestCaseStepResult(idx + 1, False, 'ROW_STRUCT_ERROR', "Wrong number or fields for this row",
                                             os.path.basename(flat_file_object.filename))
            result.steps.append(step_result)
            continue

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


def check_carriage_return(flat_file_object):
    """
    Check if field defined as
    :param flat_file_object:
    :return:
    """
    result = TestCaseResult()
    carriage_return = flat_file_object.structure.carriage_return
    with open(flat_file_object.filename, "r", newline='', encoding='utf8') as file:
        lines = file.readlines()
    for idx, line in enumerate(lines):
        if line.endswith("\r\n"):
            if line[-2:] != carriage_return:
                step_result = TestCaseStepResult(idx + 1, False, 'CARRIAGE_RETURN_ERROR', "Wrong carriage return." +
                                                 " Should be " + repr(carriage_return),
                                                 os.path.basename(flat_file_object.filename))
                result.steps.append(step_result)
        else:
            if line[-1:] != carriage_return:
                step_result = TestCaseStepResult(idx + 1, False, 'CARRIAGE_RETURN_ERROR', "Wrong carriage return." +
                                                 " Should be " + repr(carriage_return),
                                                 os.path.basename(flat_file_object.filename))
                result.steps.append(step_result)
    return result

