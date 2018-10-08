from ffparser.testcase import TestCaseStepResult, TestCaseResult
import os.path


def tpi30_check_ean_length(flat_file_object):
    """
    Check that all the fields containing CUGs have the correct length (6 or 9)
    :param flat_file_object:
    :return: all the lines and positions within the file where the length of the CUG is not 6 or 9
    """
    result = TestCaseResult()
    available_ean_lengths = [13]
    cug_ean_fields = [4]
    for idx, row in enumerate(flat_file_object.rows):
        if len(row) != 70:
            step_result = TestCaseStepResult(idx + 1, False, 'ROW_STRUCT_ERROR', "Wrong number or fields for this row. "
                                             + str(len(row)) + " fields instead of " + str(70),
                                             os.path.basename(flat_file_object.filename))
            result.steps.append(step_result)

        for field_nr in cug_ean_fields:
            fied_content = row[field_nr - 1].strip()
            if fied_content == '':
                continue
            if len(fied_content) not in available_ean_lengths:
                step_result = TestCaseStepResult(idx + 1, False, 'FIELD_FORMAT_ERROR',
                                                 "Field " + str(field_nr) + " should contain EAN with length "
                                                 + " or ".join([str(length) for length in available_ean_lengths]) +
                                                 ". Instead of'" + fied_content + "'.",
                                                 os.path.basename(flat_file_object.filename))
                result.steps.append(step_result)
    return result


def tpi30_check_cug_length(flat_file_object):
    """
    Check that all the fields containing CUGs have the correct length (6 or 9)
    :param flat_file_object:
    :return: all the lines and positions within the file where the length of the CUG is not 6 or 9
    """
    result = TestCaseResult()
    available_cug_lengths = [6, 9]
    cug_field_nrs = [3]
    for idx, row in enumerate(flat_file_object.rows):
        if len(row) != 70:
            step_result = TestCaseStepResult(idx + 1, False, 'ROW_STRUCT_ERROR', "Wrong number or fields for this row. "
                                             + str(len(row)) + " fields instead of " + str(70),
                                             os.path.basename(flat_file_object.filename))
            result.steps.append(step_result)

        for field_nr in cug_field_nrs:
            field_content = row[field_nr - 1].strip()
            if field_content == '':
                continue
            if len(field_content) not in available_cug_lengths:
                step_result = TestCaseStepResult(idx + 1, False, 'FIELD_FORMAT_ERROR',
                                                 "Field " + str(field_nr) + " should contain CUG with length "
                                                 + " or ".join([str(length) for length in available_cug_lengths]) +
                                                 ". Instead of'" + field_content + "'.",
                                                 os.path.basename(flat_file_object.filename))
                result.steps.append(step_result)
    return result
