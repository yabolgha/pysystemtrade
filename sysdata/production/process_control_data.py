import datetime

from syscontrol.data_objects import dictOfControlProcesses, controlProcess, was_running_pid_notok_closed
from syscore.objects import missing_data, _named_object, success
from sysdata.base_data import baseData
from syslogdiag.log import logtoscreen


class controlProcessData(baseData):
    def __init__(self, log=logtoscreen("controlProcessData")):
        super().__init__(log=log)
        self._control_store = dict()

    def get_dict_of_control_processes(self) ->dictOfControlProcesses:
        list_of_names = self.get_list_of_process_names()
        output_dict = dict([(process_name, self.get_control_for_process_name(
            process_name)) for process_name in list_of_names])
        output_dict = dictOfControlProcesses(output_dict)

        return output_dict

    def get_list_of_process_names(self) ->list:
        return list(self._control_store.keys())

    def get_control_for_process_name(self, process_name) -> controlProcess:
        control = self._get_control_for_process_name_without_default(
            process_name)
        if control is missing_data:
            return controlProcess()
        else:
            return control

    def _get_control_for_process_name_without_default(self, process_name) -> controlProcess:
        control = self._control_store.get(process_name, missing_data)
        return control

    def _update_control_for_process_name(
            self, process_name, new_control_object):
        existing_control = self._get_control_for_process_name_without_default(
            process_name
        )
        if existing_control is missing_data:
            self._add_control_for_process_name(
                process_name, new_control_object)
        else:
            self._modify_existing_control_for_process_name(
                process_name, new_control_object
            )

    def _add_control_for_process_name(self, process_name, new_control_object):
        self._control_store[process_name] = new_control_object

    def _modify_existing_control_for_process_name(
        self, process_name, new_control_object
    ):
        self._control_store[process_name] = new_control_object

    def check_if_okay_to_start_process(self, process_name: str) -> _named_object:
        """

        :param process_name: str
        :return:  success, or if not okay: process_no_run, process_stop, process_running
        """
        original_process = self.get_control_for_process_name(process_name)
        result = original_process.check_if_okay_to_start_process()

        return result

    def start_process(self, process_name: str) -> _named_object:
        """

        :param process_name: str
        :return:  success, or if not okay: process_no_run, process_stop, process_running
        """
        original_process = self.get_control_for_process_name(process_name)
        result = original_process.start_process()
        if result is success:
            self._update_control_for_process_name(
                process_name, original_process)

        return result

    def check_if_pid_running_and_if_not_finish_all_processes(self):

        list_of_names = self.get_list_of_process_names()
        list_of_results = [self.check_if_pid_running_and_if_not_finish(process_name) for process_name in list_of_names]

        return list_of_results


    def check_if_pid_running_and_if_not_finish(self, process_name: str):
        original_process = self.get_control_for_process_name(process_name)
        PID = original_process.process_id
        result = original_process.check_if_pid_running_and_if_not_finish_return_status()

        if result is was_running_pid_notok_closed:
            self.log.critical("Process %s with PID %d appears to have crashed, marking as finished: you may want to restart" % (process_name, PID))
            self._update_control_for_process_name(process_name, original_process)


    def finish_all_processes(self):

        list_of_names = self.get_list_of_process_names()
        _ = [self.finish_process(process_name) for process_name in list_of_names]

        return success

    def finish_process(self, process_name: str) -> _named_object:
        """

        :param process_name: str
        :return: sucess or failure if can't finish process (maybe already running?)
        """
        original_process = self.get_control_for_process_name(process_name)
        result = original_process.finish_process()
        if result is success:
            self._update_control_for_process_name(
                process_name, original_process)

        return result

    def check_if_process_status_stopped(self, process_name: str) -> bool:
        """

        :param process_name: str
        :return: bool
        """
        original_process = self.get_control_for_process_name(process_name)
        result = original_process.check_if_process_status_stopped()

        return result

    def has_process_finished_in_last_day(self, process_name:str) -> bool:
        """

        :param process_name: str
        :return: bool
        """
        original_process = self.get_control_for_process_name(process_name)
        result = original_process.has_process_finished_in_last_day()

        return result

    def change_status_to_stop(self, process_name: str):
        original_process = self.get_control_for_process_name(process_name)
        original_process.change_status_to_stop()
        self._update_control_for_process_name(process_name, original_process)

    def change_status_to_go(self, process_name: str):
        original_process = self.get_control_for_process_name(process_name)
        original_process.change_status_to_go()
        self._update_control_for_process_name(process_name, original_process)

    def change_status_to_no_run(self, process_name: str):
        original_process = self.get_control_for_process_name(process_name)
        original_process.change_status_to_no_run()
        self._update_control_for_process_name(process_name, original_process)

    def log_start_run_for_method(self, process_name: str, method_name: str):
        original_process = self.get_control_for_process_name(process_name)
        original_process.log_start_run_for_method(method_name)
        self._update_control_for_process_name(process_name, original_process)

    def log_end_run_for_method(self, process_name: str, method_name: str):
        original_process = self.get_control_for_process_name(process_name)
        original_process.log_end_run_for_method(method_name)
        self._update_control_for_process_name(process_name, original_process)

    def when_method_last_started(self, process_name: str, method_name: str) -> datetime.datetime:
        original_process = self.get_control_for_process_name(process_name)
        return original_process.when_method_last_started(method_name)

    def when_method_last_ended(self, process_name: str, method_name: str) -> datetime.datetime:
        original_process = self.get_control_for_process_name(process_name)
        return original_process.when_method_last_ended(method_name)

    def method_currently_running(self, process_name: str, method_name: str) -> bool:
        original_process = self.get_control_for_process_name(process_name)
        return original_process.method_currently_running(method_name)