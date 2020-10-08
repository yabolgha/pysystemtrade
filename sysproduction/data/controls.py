import datetime
import socket

from sysproduction.data.get_data import dataBlob
from sysproduction.data.strategies import diagStrategiesConfig
from sysdata.private_config import get_private_then_default_key_value
from syscore.objects import arg_not_supplied, missing_data
from syscore.genutils import str2Bool


class dataLocks(object):
    def __init__(self, data=arg_not_supplied):
        # Check data has the right elements to do this
        if data is arg_not_supplied:
            data = dataBlob()

        data.add_class_list("mongoLockData")
        self.data = data

    def is_instrument_locked(self, instrument_code):
        return self.data.db_lock.is_instrument_locked(instrument_code)

    def add_lock_for_instrument(self, instrument_code):
        return self.data.db_lock.add_lock_for_instrument(instrument_code)

    def remove_lock_for_instrument(self, instrument_code):
        return self.data.db_lock.remove_lock_for_instrument(instrument_code)

    def get_list_of_locked_instruments(self):
        return self.data.db_lock.get_list_of_locked_instruments()


class dataTradeLimits(object):
    def __init__(self, data=arg_not_supplied):
        # Check data has the right elements to do this
        if data is arg_not_supplied:
            data = dataBlob()

        data.add_class_list("mongoTradeLimitData")
        self.data = data

    def what_trade_is_possible(
            self,
            strategy_name,
            instrument_code,
            proposed_trade):
        return self.data.db_trade_limit.what_trade_is_possible(
            strategy_name, instrument_code, proposed_trade
        )

    def add_trade(self, strategy_name, instrument_code, trade):
        return self.data.db_trade_limit.add_trade(
            strategy_name, instrument_code, trade)

    def remove_trade(self, strategy_name, instrument_code, trade):
        return self.data.db_trade_limit.remove_trade(
            strategy_name, instrument_code, trade
        )

    def get_all_limits(self):
        return self.data.db_trade_limit.get_all_limits()

    def update_instrument_limit_with_new_limit(
        self, instrument_code, period_days, new_limit
    ):
        self.data.db_trade_limit.update_instrument_limit_with_new_limit(
            instrument_code, period_days, new_limit
        )

    def reset_instrument_limit(self, instrument_code, period_days):
        self.data.db_trade_limit.reset_instrument_limit(
            instrument_code, period_days)

    def update_instrument_strategy_limit_with_new_limit(
        self, strategy_name, instrument_code, period_days, new_limit
    ):
        self.data.db_trade_limit.update_instrument_strategy_limit_with_new_limit(
            strategy_name, instrument_code, period_days, new_limit)

    def reset_instrument_strategy_limit(
        self, strategy_name, instrument_code, period_days
    ):
        self.data.db_trade_limit.reset_instrument_strategy_limit(
            strategy_name, instrument_code, period_days
        )


class diagOverrides(object):
    def __init__(self, data=arg_not_supplied):
        # Check data has the right elements to do this
        if data is arg_not_supplied:
            data = dataBlob()

        data.add_class_list("mongoOverrideData")
        self.data = data

    def get_dict_of_all_overrides(self):
        return self.data.db_override.get_dict_of_all_overrides()

    def get_cumulative_override_for_strategy_and_instrument(
        self, strategy_name, instrument_code
    ):
        return (
            self.data.db_override.get_cumulative_override_for_strategy_and_instrument(
                strategy_name,
                instrument_code))


class updateOverrides(object):
    def __init__(self, data=arg_not_supplied):
        # Check data has the right elements to do this
        if data is arg_not_supplied:
            data = dataBlob()

        data.add_class_list("mongoOverrideData")
        self.data = data

    def update_override_for_strategy(self, strategy_name, new_override):
        self.data.db_override.update_override_for_strategy(
            strategy_name, new_override)

    def update_override_for_strategy_instrument(
        self, strategy_name, instrument_code, new_override
    ):
        self.data.db_override.update_override_for_strategy_instrument(
            strategy_name, instrument_code, new_override
        )

    def update_override_for_instrument(self, instrument_code, new_override):
        self.data.db_override.update_override_for_instrument(
            instrument_code, new_override
        )

    def update_override_for_instrument_and_contractid(
        self, instrument_code, contract_id, new_override
    ):

        self.data.db_override.update_override_for_instrument_and_contractid(
            instrument_code, contract_id, new_override
        )


class dataControlProcess(object):
    def __init__(self, data=arg_not_supplied):
        # Check data has the right elements to do this
        if data is arg_not_supplied:
            data = dataBlob()

        data.add_class_list("mongoControlProcessData")
        self.data = data

    def get_dict_of_control_processes(self):
        return self.data.db_control_process.get_dict_of_control_processes()

    def check_if_okay_to_start_process(self, process_name):
        """

        :param process_name: str
        :return:  success, or if not okay: process_no_run, process_stop, process_running
        """
        return self.data.db_control_process.check_if_okay_to_start_process(
            process_name)

    def start_process(self, process_name):
        """

        :param process_name: str
        :return:  success, or if not okay: process_no_run, process_stop, process_running
        """
        return self.data.db_control_process.start_process(process_name)

    def finish_process(self, process_name):
        """

        :param process_name: str
        :return: sucess or failure if can't finish process (maybe already running?)
        """

        return self.data.db_control_process.finish_process(process_name)

    def check_if_process_status_stopped(self, process_name):
        """

        :param process_name: str
        :return: bool
        """
        return self.data.db_control_process.check_if_process_status_stopped(
            process_name
        )

    def change_status_to_stop(self, process_name):
        self.data.db_control_process.change_status_to_stop(process_name)

    def change_status_to_go(self, process_name):
        self.data.db_control_process.change_status_to_go(process_name)

    def change_status_to_no_run(self, process_name):
        self.data.db_control_process.change_status_to_no_run(process_name)

    def has_process_finished_in_last_day(self, process_name):
        result = self.data.db_control_process.has_process_finished_in_last_day(
            process_name
        )
        return result


class diagProcessConfig:
    def __init__(self, data=arg_not_supplied):
        # Check data has the right elements to do this
        if data is arg_not_supplied:
            data = dataBlob()
        self.data = data

    def get_config_dict(self, process_name):
        previous_process = self.previous_process_name(process_name)
        start_time = self.get_start_time(process_name)
        end_time = self.get_stop_time(process_name)
        machine_name = self.required_machine_name(process_name)
        method_dict = self.get_all_method_dict_for_process_name(process_name)

        result_dict = dict(
            previous_process=previous_process,
            start_time=start_time,
            end_time=end_time,
            machine_name=machine_name,
            method_dict=method_dict,
        )

        return result_dict

    def get_strategy_dict_for_process(self, process_name, strategy_name):
        this_strategy_dict = self.get_strategy_dict_for_strategy(strategy_name)
        this_process_dict = this_strategy_dict[process_name]

        return this_process_dict

    def has_previous_process_finished_in_last_day(self, process_name):
        previous_process = self.previous_process_name(process_name)
        if previous_process is None:
            return True
        control_process = dataControlProcess(self.data)
        result = control_process.has_process_finished_in_last_day(
            previous_process)

        return result

    def is_it_time_to_run(self, process_name):
        start_time = self.get_start_time(process_name)
        stop_time = self.get_stop_time(process_name)
        now_time = datetime.datetime.now().time()

        if now_time >= start_time and now_time < stop_time:
            return True
        else:
            return False

    def is_this_correct_machine(self, process_name):
        required_host = self.required_machine_name(process_name)
        if required_host is None:
            return True

        hostname = socket.gethostname()

        if hostname == required_host:
            return True
        else:
            return False

    def is_it_time_to_stop(self, process_name):
        stop_time = self.get_stop_time(process_name)
        now_time = datetime.datetime.now().time()

        if now_time > stop_time:
            return True
        else:
            return False

    def run_on_completion_only(self, process_name, method_name):
        this_method_dict = self.get_method_configuration_for_process_name(
            process_name, method_name
        )
        run_on_completion_only = this_method_dict.get(
            "run_on_completion_only", False)
        run_on_completion_only = str2Bool(run_on_completion_only)

        return run_on_completion_only

    def frequency_for_process_and_method(
        self, process_name, method_name, use_strategy_config=False
    ):
        frequency, _ = self.frequency_and_max_executions_for_process_and_method(
            process_name, method_name, use_strategy_config=use_strategy_config)
        return frequency

    def max_executions_for_process_and_method(
        self, process_name, method_name, use_strategy_config
    ):
        _, max_executions = self.frequency_and_max_executions_for_process_and_method(
            process_name, method_name, use_strategy_config=use_strategy_config)
        return max_executions

    def frequency_and_max_executions_for_process_and_method(
        self, process_name, method_name, use_strategy_config=False
    ):
        """

        :param process_name:  str
        :param method_name:  str
        :return: tuple of int: frequency (minutes), max executions
        """

        if use_strategy_config:
            # the 'method' here is actually a strategy
            (
                frequency,
                max_executions,
            ) = self.frequency_and_max_executions_for_process_and_method_strategy_dict(
                process_name,
                method_name)
        else:
            (
                frequency,
                max_executions,
            ) = self.frequency_and_max_executions_for_process_and_method_process_dict(
                process_name,
                method_name)

        return frequency, max_executions

    def frequency_and_max_executions_for_process_and_method_strategy_dict(
        self, process_name, strategy_name
    ):
        this_process_dict = self.get_strategy_dict_for_process(
            process_name, strategy_name
        )
        frequency = this_process_dict.get("frequency", 60)
        max_executions = this_process_dict.get("max_executions", 1)

        return frequency, max_executions

    def get_strategy_dict_for_strategy(self, strategy_name):
        diag_strategy_config = diagStrategiesConfig(self.data)
        strategy_dict = diag_strategy_config.get_strategy_dict_for_strategy(
            strategy_name
        )

        return strategy_dict

    def frequency_and_max_executions_for_process_and_method_process_dict(
        self, process_name, method_name
    ):

        this_method_dict = self.get_method_configuration_for_process_name(
            process_name, method_name
        )
        frequency = this_method_dict.get("frequency", 60)
        max_executions = this_method_dict.get("max_executions", 1)

        return frequency, max_executions

    def get_method_configuration_for_process_name(
            self, process_name, method_name):
        all_method_dict = self.get_all_method_dict_for_process_name(
            process_name)
        this_method_dict = all_method_dict.get(method_name, {})

        return this_method_dict

    def get_all_method_dict_for_process_name(self, process_name):
        all_method_dict = self.get_configuration_item_for_process_name(
            process_name, "methods", default={}, use_config_default=False
        )

        return all_method_dict

    def previous_process_name(self, process_name):
        """

        :param process_name:
        :return: str or None
        """
        return self.get_configuration_item_for_process_name(
            process_name, "previous_process", default=None, use_config_default=False)

    def get_start_time(self, process_name):
        """
        Return time object, or 00:01 if none available
        :param process_name:
        :return:
        """
        result = self.get_configuration_item_for_process_name(
            process_name, "start_time", default=None, use_config_default=True
        )
        if result is None:
            result = "00:01"

        result = datetime.datetime.strptime(result, "%H:%M").time()

        return result

    def get_stop_time(self, process_name):
        """
        Return time object, or 00:01 if none available
        :param process_name:
        :return:
        """
        result = self.get_configuration_item_for_process_name(
            process_name, "stop_time", default=None, use_config_default=True
        )
        if result is None:
            result = "23:50"

        result = datetime.datetime.strptime(result, "%H:%M").time()

        return result

    def required_machine_name(self, process_name):
        """

        :param process_name:
        :return: str or None
        """
        result = self.get_configuration_item_for_process_name(
            process_name, "host_name", default=None, use_config_default=False
        )

        return result

    def get_list_of_processes_run_over_strategies(self):
        return self.get_process_configuration_for_item_name(
            "run_over_strategies")

    def get_configuration_item_for_process_name(
        self, process_name, item_name, default=None, use_config_default=False
    ):
        process_config_for_item = self.get_process_configuration_for_item_name(
            item_name
        )
        config_item = process_config_for_item.get(process_name, default)
        if use_config_default and config_item is default:
            config_item = process_config_for_item.get("default", default)

        return config_item

    def get_process_configuration_for_item_name(self, item_name):
        config = getattr(self, "_process_config_%s" % item_name, None)
        if config is None:
            config = get_private_then_default_key_value(
                "process_configuration_%s" % item_name, raise_error=False
            )
            if config is missing_data:
                return {}
            setattr(self, "_process_config_%s" % item_name, config)

        return config
