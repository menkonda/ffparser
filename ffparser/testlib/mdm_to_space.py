from ffparser.testcase import TestCaseStepResult, TestCaseResult
import os.path


def mdm_to_space_check_quotes(flat_file_object):
    """
    Check if field defined as a string is quoted, even if it is empty
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


def mdm_to_space_check_weight(flat_file_object):
    """
    Check weights consistency in MDM to space reference files. Triggers an error when dry weight is greater than
    net weight and carton gross weight is lower than carton net weight
    :param flat_file_object:
    :return:
    """
    unitary_net_weigth_field = 48
    product_net_net_weight_field = 49
    unitary_drained_net_weight_field = 50
    outer_carton_net_weight_field = 57
    outer_carton_gross_weight = 58

    result = TestCaseResult()

    for idx, row in enumerate(flat_file_object.rows):
        row_type = row[flat_file_object.structure.type_pos - 1]

        if row_type not in ('01', '02'):
            continue

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

        # Check that weight fields are decimal
        data_type_error_flag = False
        for field in (unitary_net_weigth_field, product_net_net_weight_field, unitary_drained_net_weight_field,
                      outer_carton_net_weight_field, outer_carton_gross_weight):
            if not row[field - 1].replace('.', '', 1).isdigit():
                data_type_error_flag = True
                msg = "Field %s should be a decimal. Instead of '%s'" % (field, row[field - 1])
                error_type = "DATA_TYPE_ERROR"
                step_result = TestCaseStepResult(idx + 1, False, error_type, msg,
                                                 os.path.basename(flat_file_object.filename))
                result.steps.append(step_result)

        if data_type_error_flag:
            continue

        # Check carton weights consistency
        if float(row[outer_carton_net_weight_field - 1]) > float(row[outer_carton_gross_weight - 1]):
            msg = "Weight consistency error. Outer carton net weight is greater than gross weight"
            error_type = 'ROW_CONSISTENCY ERROR'
            step_result = TestCaseStepResult(idx + 1, False, error_type, msg,
                                             os.path.basename(flat_file_object.filename))
            result.steps.append(step_result)

        # Check unitary weights consistency
        if float(row[unitary_drained_net_weight_field - 1]) > float(row[product_net_net_weight_field - 1]):
            msg = "Weight consistency error. Dry net weight is greater than net weight"
            error_type = 'ROW_CONSISTENCY ERROR'
            step_result = TestCaseStepResult(idx + 1, False, error_type, msg,
                                             os.path.basename(flat_file_object.filename))
            result.steps.append(step_result)

    return result
