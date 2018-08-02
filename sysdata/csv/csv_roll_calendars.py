from sysdata.futures.roll_calendars import rollCalendarData, rollCalendar
from syscore.fileutils import get_filename_for_package, files_with_extension_in_pathname
from syscore.pdutils import pd_readcsv


CSV_ROLL_CALENDAR_DIRECTORY = "data.futures.roll_calendars_csv"
DATE_INDEX_NAME = "DATE_TIME"

# NOTE: can't change calendars here - do we need init?
# common with all other csv objects?

class csvRollCalendarData(rollCalendarData):
    """

    Class for roll calendars write / to from csv
    """
    def __init__(self, datapath=None):

        super().__init__()

        if datapath is None:
            datapath = CSV_ROLL_CALENDAR_DIRECTORY

        self._datapath = datapath

    def __repr__(self):
        return "csvRollCalendarData accessing %s" % self._datapath

    def get_list_of_instruments(self):

        return files_with_extension_in_pathname(self._datapath, ".csv")

    def _get_roll_calendar_without_checking(self, instrument_code):

        try:
            filename = self._filename_given_instrument_code(instrument_code)
            roll_calendar = pd_readcsv(filename, date_index_name=DATE_INDEX_NAME)
        except OSError:
            self.log.warning("Can't find roll calendar file %s" % filename)
            return rollCalendar.create_empty()

        return roll_calendar

    def _delete_roll_calendar_data_without_any_warning_be_careful(instrument_code):
        raise NotImplementedError("You can't delete a roll calendar stored as a csv - Add to overwrite existing or delete file manually")

    def _add_roll_calendar_without_checking_for_existing_entry(self, roll_calendar, instrument_code):
        filename = self._filename_given_instrument_code(instrument_code)
        roll_calendar.to_csv(filename, index_label = DATE_INDEX_NAME)

    def _filename_given_instrument_code(self, instrument_code):
        return get_filename_for_package("%s.%s.csv" %(self._datapath,instrument_code))
