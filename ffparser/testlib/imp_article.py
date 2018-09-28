from ffparser.testlib.common import *


def imp_article_filename_field(flat_file_object):
    """
    Check that all the fields YNOMFIC are correctly filled
    :param flat_file_object:
    :return: all the lines and positions within thh file where the field YNOMFIC is not the name of the flat file
    """
    result = TestCaseResult()
    for idx, row in enumerate(flat_file_object.rows):
        if row[23] == '':
            continue
        if row[23] != os.path.basename(flat_file_object.filename).split('.')[0]:
            step_result = TestCaseStepResult(idx + 1, False, 'FIELD_FORMAT_ERROR',
                                             "Field should contain the name of the parsed file ",
                                             os.path.basename(flat_file_object.filename))
            result.steps.append(step_result)
    return result

def imp_article_check_cug_length(flat_file_object):
    """
    Check that all the fields containing CUGs have the correct length (6 or 9)
    :param flat_file_object:
    :return: all the lines and positions within the file where the length of the CUG is not 6 or 9
    """
    result = TestCaseResult()
    available_cug_lengths = [6, 9]
    cug_field_nrs = [4, 6]
    for idx, row in enumerate(flat_file_object.rows):
        for field_nr in cug_field_nrs:
            fied_content = row[field_nr - 1]
            if fied_content == '':
                continue
            if len(fied_content) not in available_cug_lengths:
                step_result = TestCaseStepResult(idx + 1, False, 'FIELD_FORMAT_ERROR',
                                                 "Field " + str(field_nr) + " should contain CUG with length "
                                                 + " or ".join([str(length) for length in available_cug_lengths]) +
                                                 ". Instead of'" + fied_content + "'.",
                                                 os.path.basename(flat_file_object.filename))
                result.steps.append(step_result)
    return result

def imp_article_check_ean_length(flat_file_object):
    """
    Check that all the fields containing CUGs have the correct length (6 or 9)
    :param flat_file_object:
    :return: all the lines and positions within the file where the length of the CUG is not 6 or 9
    """
    result = TestCaseResult()
    available_ean_lengths = [13]
    cug_ean_fields = [7]
    for idx, row in enumerate(flat_file_object.rows):
        for field_nr in cug_ean_fields:
            fied_content = row[field_nr - 1]
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

