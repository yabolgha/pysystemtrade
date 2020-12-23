import pandas as pd

from syscore.objects import arg_not_supplied
from syscore.pdutils import merge_newer_data_no_checks, spike_check_merged_data

def manual_price_checker(
    old_data_passed,
    new_data_passed,
    column_to_check=arg_not_supplied,
    delta_columns=arg_not_supplied,
    type_new_data=pd.DataFrame,
):
    """
    Allows a user to manually merge old and new data, checking any usually large changes and overwriting

    Old and new data could be FX prices, futures per contract prices, or anything really

    For data frames eg futures per contract prices, any rows where a manual intervention is required are nan'd out

    Returns new_data

    :param old_data:
    :param new_data:
    :return: new_data with no spike issues
    """

    old_data = pd.DataFrame(old_data_passed)
    new_data = pd.DataFrame(new_data_passed)

    column_to_check, total_msg_str = _resolve_and_check_columns(
        old_data, column_to_check=column_to_check, delta_columns=delta_columns
    )

    if len(old_data) > 0:
        original_last_date_of_old_data = old_data.index[-1]
    else:
        original_last_date_of_old_data = new_data.index[0]

    # Iterate:
    data_iterating = True
    while data_iterating:

        merge_status, first_date_in_new_data, merged_data = merge_newer_data_no_checks(
            old_data, new_data)
        spike_present, first_spike = spike_check_merged_data(
            merge_status,
            first_date_in_new_data,
            merged_data,
            column_to_check=column_to_check,
        )

        if not spike_present:
            # No issues, we can go home
            data_iterating = False
            break

        position_of_spike_in_newdata = list(new_data.index).index(first_spike)
        position_of_spike_in_mergedata = list(
            merged_data.index).index(first_spike)

        original_value = merged_data[column_to_check][position_of_spike_in_mergedata]
        previous_value = merged_data[column_to_check][
            position_of_spike_in_mergedata - 1
        ]

        # Get input
        _show_last_bit_of_data(merged_data, position_of_spike_in_mergedata)
        value_to_use, adjust_old_and_new_data = _get_new_value(
            original_value,
            previous_value,
            col_date_str="%s on %s" % (column_to_check, first_spike),
            total_msg_str=total_msg_str,
        )

        # Replace original value in new data
        new_data.loc[first_spike, column_to_check] = value_to_use

        if delta_columns is not arg_not_supplied:
            # 'Delta columns' adjust eg delta_columns=['OPEN', 'HIGH', 'LOW'] in line with change to key column
            new_data = _adjust_delta_columns(
                new_data,
                value_to_use,
                original_value,
                first_spike,
                delta_columns)

        if adjust_old_and_new_data:
            # Change old_data so it now includes the spike checked bit
            old_data, new_data = _adjust_old_and_new_data(
                old_data, new_data, position_of_spike_in_newdata
            )
            if len(new_data) == 0:
                data_iterating = False
                break

    # At this point we have old data, containing all stuff checked plus original old data
    # and new data that may have shrunk to nothing

    # One last merge
    _, _, merged_data = merge_newer_data_no_checks(old_data, new_data)

    old_data = merged_data[
        :original_last_date_of_old_data
    ]  # Not used, but for tidiness
    new_data = merged_data[original_last_date_of_old_data:][1:]
    new_data_as_input_type = type_new_data(new_data)

    return new_data_as_input_type


def _show_last_bit_of_data(merged_data, position_of_spike_in_mergedata):
    start_with_row = max(1, position_of_spike_in_mergedata - 5)
    data_to_show = merged_data[start_with_row: position_of_spike_in_mergedata + 1]
    print(data_to_show)

    return None


def _get_new_value(
        original_value,
        previous_value,
        col_date_str="",
        total_msg_str=""):
    """

    :param original_value:
    :param previous_value:
    :param first_spike:
    :param column_to_check:
    :param total_msg_str:
    :return: tuple: float value, bool if need to adjust
    """
    waiting_for_valid_input = True
    while waiting_for_valid_input:
        print("\n")
        print(
            "Value %f of %s is a big change from previous value of %f"
            % (original_value, col_date_str, previous_value)
        )
        print(
            "<return> to accept, <space><return> for previous value,  <float><return> for a new value"
        )
        print(total_msg_str)

        result = input()

        # If adjust_old_and_new_data is True, then we move old data forward to encompass the revised new data
        # Otherwise we leave the new_data and old_data as they are, which means the new_data will be rechecked for spikes
        # We do this for user input

        adjust_old_and_new_data = None

        if result == "":
            # Accept result
            print("\nAccepting original value of %f \n" % original_value)
            value_to_use = original_value
            adjust_old_and_new_data = True
            waiting_for_valid_input = False
        elif result == " ":
            # Replace with previous value
            print("\nUsing previous value of %f \n" % previous_value)
            value_to_use = previous_value
            adjust_old_and_new_data = True
            waiting_for_valid_input = False
        else:
            # User input
            # NOTE: user input will get checked by spike checker, so if we
            # screw up that's fine
            try:
                value_to_use = float(result)
                waiting_for_valid_input = False
                print(
                    "\nUsing new value of %f: if this is still a spike from prior value, will be rechecked \n" %
                    value_to_use)

            except ValueError:
                # Not a valid float
                waiting_for_valid_input = True
                print("\n %s is not a valid input \n" % str(value_to_use))

    return value_to_use, adjust_old_and_new_data


def _adjust_old_and_new_data(old_data, new_data, position_of_spike_in_newdata):
    checked_new_data = new_data[: position_of_spike_in_newdata + 1]
    unchecked_new_data = new_data[position_of_spike_in_newdata + 1:]
    _, _, merge_of_old_and_checked_new_data = merge_newer_data_no_checks(
        old_data, checked_new_data
    )

    old_data = merge_of_old_and_checked_new_data
    new_data = unchecked_new_data

    return old_data, new_data


def _adjust_delta_columns(
    new_data, value_to_use, original_value, first_spike, delta_columns
):
    delta_to_old = value_to_use - original_value
    original_delta_values = new_data.loc[first_spike, delta_columns]
    new_data.loc[first_spike,
                 delta_columns] = original_delta_values + delta_to_old

    return new_data


def _resolve_and_check_columns(
    old_data, column_to_check=arg_not_supplied, delta_columns=arg_not_supplied
):
    if column_to_check is arg_not_supplied:
        column_to_check = old_data.columns[0]

    other_cols = list(old_data.columns)
    other_cols.remove(column_to_check)
    if delta_columns is not arg_not_supplied:
        delta_col_str = "%s will be adjusted in line with change to %s" % (
            str(delta_columns),
            column_to_check,
        )
        for colname in delta_columns:
            other_cols.remove(colname)
    else:
        delta_col_str = " "

    if len(other_cols) > 0:
        other_col_str = "%s will be left unchanged" % str(other_cols)
    else:
        other_col_str = " "

    total_msg_str = " ".join([delta_col_str, other_col_str])

    return column_to_check, total_msg_str
