from syscontrol.run_process import processToRun
from sysproduction.clean_truncate_backtest_states import cleanTruncateBacktestStates
from sysproduction.clean_truncate_echo_files import cleanTruncateEchoFiles
from sysproduction.clean_truncate_log_files import cleanTruncateLogFiles
from sysdata.data_blob import dataBlob


def run_cleaners():
    process_name = "run_cleaners"
    data = dataBlob(log_name=process_name)
    list_of_timer_names_and_functions = get_list_of_timer_functions_for_cleaning()
    cleaning_process = processToRun(
        process_name, data, list_of_timer_names_and_functions
    )
    cleaning_process.main_loop()


def get_list_of_timer_functions_for_cleaning():
    data_backtests = dataBlob(log_name="clean_backtest_states")
    data_echos = dataBlob(log_name="clean_echo_files")
    data_logs = dataBlob(log_name="clean_log_files")

    backtest_clean_object = cleanTruncateBacktestStates(data_backtests)
    log_clean_object = cleanTruncateLogFiles(data_logs)
    echo_clean_object = cleanTruncateEchoFiles(data_echos)

    list_of_timer_names_and_functions = [
        ("clean_backtest_states", backtest_clean_object),
        ("clean_echo_files", echo_clean_object),
        ("clean_log_files", log_clean_object),
    ]

    return list_of_timer_names_and_functions
