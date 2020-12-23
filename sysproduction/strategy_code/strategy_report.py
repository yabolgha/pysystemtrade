from sysproduction.data.strategies import diagStrategiesConfig
from syscore.objects import resolve_function

default_reporting_method = (
    "sysproduction.strategy_code.report_system_classic.report_system_classic"
)


def get_reporting_function_instance_for_strategy_name(data, strategy_name):
    reporting_function = get_reporting_function_for_strategy_name(
        data, strategy_name)
    reporting_function_instance = resolve_function(reporting_function)

    return reporting_function_instance


def get_reporting_function_for_strategy_name(data, strategy_name):
    try:
        diag_strategy_config = diagStrategiesConfig(data)
        config_for_strategy = diag_strategy_config.get_strategy_dict_for_strategy(
            strategy_name)
        reporting_config = config_for_strategy["reporting_code"]
        reporting_function = reporting_config["function"]
    except BaseException:
        data.log.warn(
            "Something went wrong for reporting with strategy %s, using default function %s" %
            (strategy_name, default_reporting_method))
        reporting_function = default_reporting_method

    return reporting_function
