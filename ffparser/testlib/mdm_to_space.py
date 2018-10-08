from ffparser.testcase import TestCaseStepResult, TestCaseResult
import os.path


def mdm_to_space_check_quotes(flat_file_object):
    """
    Check if field defined as
    :param flat_file_object:
    :return:
    """
    result = TestCaseResult()
    lines = open(flat_file_object.filename, "r").readlines()
    for idx, row in enumerate(lines):
        row = row.replace(flat_file_object.structure.carriage_return, "")
        row = row.split(flat_file_object.structure.sep)
        row_type = row[flat_file_object.structure.type_pos - 1].replace("\"", "")

        row_struct = flat_file_object.get_row_structure_from_type(row_type)
        if type(row_struct).__name__ == 'str':
            step_result = TestCaseStepResult(idx + 1, False, 'ROW_STRUCT_ERROR', row_struct,
                                             os.path.basename(flat_file_object.filename))
            result.steps.append(step_result)
            continue

        if len(row) != row_struct.length:
            step_result = TestCaseStepResult(idx + 1, False, 'ROW_STRUCT_ERROR', "Wrong number or fields for this row. "
                                             + str(len(row)) + " fields instead of " + str(row_struct.length),
                                             os.path.basename(flat_file_object.filename))
            result.steps.append(step_result)
            continue

        alpha_fields = [field for field in range(1, row_struct.length + 1) if(field not in row_struct.digit_fields
                                                                              and field not in row_struct.decimal_fields
                                                                              and field not in row_struct.date_fields)]
        for i in range(0, row_struct.length):
            field_content = row[i]
            if (i+1) in alpha_fields:
                if len(field_content) < 2 or not(field_content[0] == "\"" and field_content[-1] == "\""):
                    step_result = TestCaseStepResult(idx + 1, False, 'FIELD_FORMAT_ERROR',
                                                     "Missing quote at field " + str(i+1),
                                                     os.path.basename(flat_file_object.filename))
                    result.steps.append(step_result)
            else:
                if len(field_content) > 1 and (field_content[0] == "\"" or field_content[-1] == "\""):
                    step_result = TestCaseStepResult(idx + 1, False, 'FIELD_FORMAT_ERROR',
                                                     "Field " + str(i + 1) + " should not be quoted",
                                                     os.path.basename(flat_file_object.filename))
                    result.steps.append(step_result)
    return result
