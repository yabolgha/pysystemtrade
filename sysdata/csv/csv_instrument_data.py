from syscore.fileutils import get_filename_for_package
from sysdata.futures.instruments import futuresInstrumentData
from syscore.objects import arg_not_supplied
from sysobjects.instruments import futuresInstrument, futuresInstrumentWithMetaData, instrumentMetaData
from syslogdiag.log import logtoscreen
import pandas as pd

INSTRUMENT_CONFIG_PATH = "data.futures.csvconfig"
CONFIG_FILE_NAME = "instrumentconfig.csv"


class csvFuturesInstrumentData(futuresInstrumentData):
    """
    Get data about instruments from a special configuration used for initialising the system

    """

    def __init__(
        self,
        datapath=arg_not_supplied,
        log=logtoscreen("csvFuturesInstrumentData"),
    ):

        super().__init__(log=log)

        if datapath is arg_not_supplied:
            datapath = INSTRUMENT_CONFIG_PATH
        config_file =get_filename_for_package(
            datapath, CONFIG_FILE_NAME)
        self._config_file = config_file

    @property
    def config_file(self):
        return self._config_file


    def _load_instrument_csv_as_df(self) -> pd.DataFrame:
        try:
            config_data = pd.read_csv(self.config_file)
        except BaseException:
            raise Exception("Can't read file %s" % self.config_file)

        try:
            config_data.index = config_data.Instrument
            config_data.drop("Instrument", 1, inplace=True)

        except BaseException:
            raise Exception("Badly configured file %s" % (self._config_file))

        return config_data


    def get_all_instrument_data_as_df(self) -> pd.DataFrame:
        """
        Get configuration information as a dataframe

        :return: dict of config information
        """
        config_data = self._load_instrument_csv_as_df()
        return config_data

    def __repr__(self):
        return "Instruments data from %s" % self._config_file

    def get_list_of_instruments(self) -> list:
        return list(self.get_all_instrument_data_as_df().index)

    def _get_instrument_data_without_checking(self, instrument_code:str) -> futuresInstrumentWithMetaData:
        all_instrument_data = self.get_all_instrument_data_as_df()
        instrument_with_meta_data = get_instrument_with_meta_data_object(all_instrument_data, instrument_code)

        return instrument_with_meta_data

    def _delete_instrument_data_without_any_warning_be_careful(self,
            instrument_code: str):
        raise NotImplementedError("Can't overwrite part of .csv use write_all_instrument_data_from_df")


    def _add_instrument_data_without_checking_for_existing_entry(
        self, instrument_object: futuresInstrumentWithMetaData
    ):
        raise NotImplementedError("Can't overwrite part of .csv use write_all_instrument_data_from_df")


    def write_all_instrument_data_from_df(self, instrument_data_as_df: pd.DataFrame):
        instrument_data_as_df.to_csv(self._config_file, index_label="Instrument")

def get_instrument_with_meta_data_object(all_instrument_data: pd.DataFrame,
                                         instrument_code: str) -> futuresInstrumentWithMetaData:
    config_for_this_instrument = all_instrument_data.loc[instrument_code]
    config_items = all_instrument_data.columns

    meta_data_dict = get_meta_data_dict_for_instrument(config_for_this_instrument, config_items)

    instrument = futuresInstrument(instrument_code)
    meta_data = instrumentMetaData.from_dict(meta_data_dict)

    instrument_with_meta_data = futuresInstrumentWithMetaData(instrument, meta_data)

    return instrument_with_meta_data

def get_meta_data_dict_for_instrument(config_for_this_instrument: pd.DataFrame, config_items: list):
    meta_data = dict(
        [
            (item_name, getattr(config_for_this_instrument, item_name))
            for item_name in config_items
        ]
    )

    return meta_data

