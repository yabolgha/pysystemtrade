"""
Read / write and represent instrument data
"""

import pandas as pd
from sysdata.base_data import baseData
from sysobjects.instruments import futuresInstrumentWithMetaData, listOffuturesInstrumentWithMetaData
from syslogdiag.log import logtoscreen

USE_CHILD_CLASS_ERROR = "You need to use a child class of futuresInstrumentData"


class futuresInstrumentData(baseData):
    """
    Read and write data class to get instrument data

    We'd inherit from this class for a specific implementation

    """

    def __repr__(self):
        return "futuresInstrumentData base class - DO NOT USE"

    def __init__(self, log=logtoscreen("futuresInstrumentData")):
        super().__init__(log=log)

    def keys(self) -> list:
        return self.get_list_of_instruments()

    def __getitem__(self, instrument_code: str):
        return self.get_instrument_data(instrument_code)

    def get_all_instrument_data_as_list_of_instrument_objects(self) -> listOffuturesInstrumentWithMetaData:
        all_instrument_codes = self.get_list_of_instruments()
        all_instrument_objects = [
            self.get_instrument_data(instrument_code)
            for instrument_code in all_instrument_codes
        ]
        list_of_instrument_objects = listOffuturesInstrumentWithMetaData(all_instrument_objects)

        return list_of_instrument_objects

    def get_all_instrument_data_as_df(self) -> pd.DataFrame:
        """
        Gets information about all instruments

        Returns dataframe of meta data, indexed by instrument code

        :return: pd.DataFrame
        """

        list_of_instrument_objects = self.get_all_instrument_data_as_list_of_instrument_objects()
        list_as_df = list_of_instrument_objects.as_df()

        return list_as_df

    def get_instrument_data(self, instrument_code: str) ->futuresInstrumentWithMetaData:
        if self.is_code_in_data(instrument_code):
            return self._get_instrument_data_without_checking(instrument_code)
        else:
            return futuresInstrumentWithMetaData.create_empty()


    def delete_instrument_data(self, instrument_code: str, are_you_sure: bool=False):
        self.log.label(instrument_code=instrument_code)

        if are_you_sure:
            if self.is_code_in_data(instrument_code):
                self._delete_instrument_data_without_any_warning_be_careful(
                    instrument_code
                )
                self.log.terse(
                    "Deleted instrument object %s" %
                    instrument_code)

            else:
                # doesn't exist anyway
                self.log.warn("Tried to delete non existent instrument")
        else:
            self.log.error(
                "You need to call delete_instrument_data with a flag to be sure"
            )

    def is_code_in_data(self, instrument_code: str) -> bool:
        if instrument_code in self.get_list_of_instruments():
            return True
        else:
            return False


    def add_instrument_data(self, instrument_object: futuresInstrumentWithMetaData,
                            ignore_duplication:bool=False):
        instrument_code = instrument_object.instrument_code

        self.log.label(instrument_code=instrument_code)

        if self.is_code_in_data(instrument_code):
            if ignore_duplication:
                pass
            else:
                self.log.error(
                    "There is already %s in the data, you have to delete it first" %
                    instrument_code)

        self._add_instrument_data_without_checking_for_existing_entry(
            instrument_object)

        self.log.terse(
            "Added instrument object %s" %
            instrument_object.instrument_code)

    def get_list_of_instruments(self):
        raise NotImplementedError(USE_CHILD_CLASS_ERROR)


    def _get_instrument_data_without_checking(self, instrument_code: str):
        raise NotImplementedError(USE_CHILD_CLASS_ERROR)


    def _delete_instrument_data_without_any_warning_be_careful(self,
            instrument_code: str):
        raise NotImplementedError(USE_CHILD_CLASS_ERROR)


    def _add_instrument_data_without_checking_for_existing_entry(
        self, instrument_object: futuresInstrumentWithMetaData
    ):
        raise NotImplementedError(USE_CHILD_CLASS_ERROR)
