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
