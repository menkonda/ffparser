from ffparser.testlib.common import *


def mdm_to_space_check_quotes(flat_file_object):
    """
    Check if field defined as
    :param flat_file_object:
    :return:
    """
    result = TestCaseResult()
    for idx, row in enumerate(flat_file_object.rows):
        row_type = row[flat_file_object.structure.type_pos - 1]
        row_struct = get_row_structure_from_type(flat_file_object.structure.row_structures, row_type)
        alpha_fields = [field for field in range(row_struct.length) if(field not in row_struct.digit_fields and field not in row_struct.decimal_fields)]
        for alpha_field in alpha_fields:
            field_content = row[alpha_field - 1]
            if not(field_content[0] == "\"" and field_content[-1] == "\"") or len(field_content) <= 1:
                step_result = TestCaseStepResult(idx + 1, False, 'FIELD_FORMAT_ERROR',
                                                 "Missing quote at field " + str(alpha_field),
                                                 os.path.basename(flat_file_object.filename))
                result.steps.append(step_result)
    return result
