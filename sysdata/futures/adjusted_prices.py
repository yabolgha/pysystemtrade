"""
Adjusted prices:

- back-adjustor
- just adjusted prices

"""

import pandas as pd
import numpy as np
from sysdata.data import baseData

def panama_stitch(multiple_prices):
    """
    Do a panama stich for adjusted prices

    :param multiple_prices:  futuresMultiplePrices
    :return: pd.Series of adjusted prices
    """
    previous_row = multiple_prices.iloc[0, :]
    adjusted_prices_values = [previous_row.PRICE]

    for dateindex in multiple_prices.index[1:]:
        current_row = multiple_prices.loc[dateindex, :]

        if current_row.PRICE_CONTRACT == previous_row.PRICE_CONTRACT:
            # no roll has occured
            # we just append the price
            adjusted_prices_values.append(current_row.PRICE)
        else:
            # A roll has occured
            # This is the sort of code you will need to change to adjust the roll logic
            # The roll differential is from the previous_row
            roll_differential = previous_row.FORWARD - previous_row.PRICE
            if np.isnan(roll_differential):
                raise Exception(
                    "On this day %s which should be a roll date we don't have prices for both %s and %s contracts"
                    % (str(dateindex), previous_row.PRICE_CONTRACT, previous_row.FORWARD_CONTRACT))

            # We add the roll differential to all previous prices
            adjusted_prices_values = [adj_price + roll_differential for adj_price in adjusted_prices_values]

            # note this includes the price for the previous row, which will now be equal to the forward price
            # We now add todays price. This will be for the new contract

            adjusted_prices_values.append(current_row.PRICE)

        previous_row = current_row

    # it's ok to return a DataFrame since the calling object will change the type
    adjusted_prices = pd.Series(adjusted_prices_values, index = multiple_prices.index)

    return adjusted_prices

class futuresAdjustedPrices(pd.Series):
    """
    adjusted price information
    """

    def __init__(self, data):

        super().__init__(data)

        self._is_empty=False

    @classmethod
    def create_empty(futuresContractPrices):
        """
        Our graceful fail is to return an empty, but valid, dataframe
        """

        data = pd.Series()

        futures_contract_prices = futuresContractPrices(data)

        futures_contract_prices._is_empty = True
        return futures_contract_prices

    def empty(self):
        return


    @classmethod
    def stich_multiple_prices(futuresAdjustedPrices, multiple_prices):
        """
        Do backstitching of multiple prices using panama method

        If you want to change then override this method

        :param multiple_prices:
        :return: futuresAdjustedPrices
        """

        adjusted_prices = panama_stitch(multiple_prices)

        return futuresAdjustedPrices(adjusted_prices)

USE_CHILD_CLASS_ERROR = "You need to use a child class of futuresAdjustedPricesData"

class futuresAdjustedPricesData(baseData):
    """
    Read and write data class to get adjusted prices

    We'd inherit from this class for a specific implementation

    """

    def __repr__(self):
        return USE_CHILD_CLASS_ERROR

    def keys(self):
        return self.get_list_of_instruments()

    def get_list_of_instruments(self):
        raise NotImplementedError(USE_CHILD_CLASS_ERROR)

    def get_adjusted_prices(self, instrument_code):
        if self.is_code_in_data(instrument_code):
            return self._get_adjusted_prices_without_checking(instrument_code)
        else:
            return futuresAdjustedPrices.create_empty()

    def _get_adjusted_prices_without_checking(self, instrument_code):
        raise NotImplementedError(USE_CHILD_CLASS_ERROR)

    def __getitem__(self, instrument_code):
        return self.get_adjusted_prices(instrument_code)

    def delete_adjusted_prices(self, instrument_code, are_you_sure=False):
        self.log.label(instrument_code=instrument_code)

        if are_you_sure:
            if self.is_code_in_data(instrument_code):
                self._delete_adjusted_prices_without_any_warning_be_careful(instrument_code)
                self.log.terse("Deleted adjusted price data for %s" % instrument_code)

            else:
                ## doesn't exist anyway
                self.log.warn("Tried to delete non existent adjusted prices for %s" % instrument_code)
        else:
            self.log.error("You need to call delete_adjusted_prices with a flag to be sure")

    def _delete_adjusted_prices_without_any_warning_be_careful(instrument_code):
        raise NotImplementedError(USE_CHILD_CLASS_ERROR)

    def is_code_in_data(self, instrument_code):
        if instrument_code in self.get_list_of_instruments():
            return True
        else:
            return False

    def add_adjusted_prices(self, instrument_code, adjusted_price_data, ignore_duplication=False):
        self.log.label(instrument_code=instrument_code)
        if self.is_code_in_data(instrument_code):
            if ignore_duplication:
                pass
            else:
                self.log.error("There is already %s in the data, you have to delete it first" % instrument_code)

        self._add_adjusted_prices_without_checking_for_existing_entry(instrument_code, adjusted_price_data)

        self.log.terse("Added data for instrument %s" % instrument_code)

    def _add_adjusted_prices_without_checking_for_existing_entry(self, instrument_code, adjusted_price_data):
        raise NotImplementedError(USE_CHILD_CLASS_ERROR)

