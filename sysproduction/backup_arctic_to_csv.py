import pandas as pd
from syscore.objects import missing_data
from syscore.pdutils import check_df_equals, check_ts_equals
from sysdata.private_config import get_private_then_default_key_value

from sysproduction.data.get_data import dataBlob
from sysproduction.data.strategies import get_list_of_strategies
import os


def backup_arctic_to_csv():
    data = dataBlob(log_name="backup_arctic_to_csv")
    backup_object = backupArcticToCsv(data)
    backup_object.backup_arctic_to_csv()

    return None


class backupArcticToCsv:
    def __init__(self, data):
        self.data = data

    def backup_arctic_to_csv(self):
        data = get_data_and_create_csv_directories(self.data.log_name)
        backup_fx_to_csv(data)
        backup_futures_contract_prices_to_csv(data)
        backup_multiple_to_csv(data)
        backup_adj_to_csv(data)
        backup_strategy_position_data(data)
        backup_contract_position_data(data)
        backup_historical_orders(data)
        backup_capital(data)
        backup_contract_data(data)
        backup_instrument_data(data)
        backup_optimal_positions(data)
        backup_roll_state_data(data)


def get_backup_dir():
    return get_private_then_default_key_value("csv_backup_directory")


def get_data_and_create_csv_directories(logname):

    backup_dir = get_backup_dir()

    class_paths = dict(
        csvFuturesContractPriceData="contract_prices",
        csvFuturesAdjustedPricesData="adjusted_prices",
        csvFuturesMultiplePricesData="multiple_prices",
        csvFxPricesData="fx_prices",
        csvContractPositionData="contract_positions",
        csvStrategyPositionData="strategy_positions",
        csvBrokerHistoricOrdersData="broker_orders",
        csvContractHistoricOrdersData="contract_orders",
        csvStrategyHistoricOrdersData="strategy_orders",
        csvCapitalData="capital",
        csvFuturesContractData="contracts_data",
        csvFuturesInstrumentData="instrument_data",
        csvOptimalPositionData="optimal_positions",
        csvRollParametersData="roll_parameters",
        csvRollStateData="roll_state",
    )

    for class_name, path in class_paths.items():
        dir_name = "%s/%s/" % (backup_dir, path)
        class_paths[class_name] = dir_name
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)

    data = dataBlob(
        csv_data_paths=class_paths, keep_original_prefix=True, log_name=logname
    )

    data.add_class_list(
        "csvFuturesContractPriceData csvFuturesAdjustedPricesData \
                        csvFuturesMultiplePricesData csvFxPricesData \
                        csvContractPositionData csvStrategyPositionData \
                        csvBrokerHistoricOrdersData csvContractHistoricOrdersData csvStrategyHistoricOrdersData \
                        csvCapitalData csvOptimalPositionData csvFuturesInstrumentData \
                        csvRollStateData csvFuturesContractData"
    )

    data.add_class_list(
        "arcticFuturesContractPriceData arcticFuturesMultiplePricesData \
                        arcticFuturesAdjustedPricesData arcticFxPricesData \
                        mongoContractPositionData mongoStrategyPositionData \
                        mongoBrokerHistoricOrdersData mongoContractHistoricOrdersData mongoStrategyHistoricOrdersData \
                        mongoCapitalData mongoFuturesContractData mongoFuturesInstrumentData \
                        mongoOptimalPositionData mongoRollParametersData mongoRollStateData"
    )

    return data


# Write function for each thing we want to backup
# Think about how to check for duplicates (data frame equals?)


# Futures contract data
def backup_futures_contract_prices_to_csv(data):
    instrument_list = (
        data.arctic_futures_contract_price.get_instruments_with_price_data()
    )
    for instrument_code in instrument_list:
        contract_dates = data.arctic_futures_contract_price.contract_dates_with_price_data_for_instrument_code(
            instrument_code)

        for contract_date in contract_dates:
            arctic_data = data.arctic_futures_contract_price.get_prices_for_instrument_code_and_contract_date(
                instrument_code, contract_date)

            csv_data = data.csv_futures_contract_price.get_prices_for_instrument_code_and_contract_date(
                instrument_code, contract_date)

            if check_df_equals(arctic_data, csv_data):
                # No updated needed, move on
                print("No update needed")
            else:
                # Write backup
                try:
                    data.csv_futures_contract_price.write_prices_for_instrument_code_and_contract_date(
                        instrument_code, contract_date, arctic_data, ignore_duplication=True, )
                    data.log.msg(
                        "Written backup .csv of prices for %s %s"
                        % (instrument_code, contract_date)
                    )
                except BaseException:
                    data.log.warn(
                        "Problem writing .csv of prices for %s %s"
                        % (instrument_code, contract_date)
                    )


# fx
def backup_fx_to_csv(data):
    fx_codes = data.arctic_fx_prices.get_list_of_fxcodes()
    for fx_code in fx_codes:
        arctic_data = data.arctic_fx_prices.get_fx_prices(fx_code)
        csv_data = data.csv_fx_prices.get_fx_prices(fx_code)
        if check_ts_equals(arctic_data, csv_data):
            print("No updated needed")
        else:
            # Write backup
            try:
                data.csv_fx_prices.add_fx_prices(
                    fx_code, arctic_data, ignore_duplication=True
                )
                data.log.msg("Written .csv backup for %s" % fx_code)
            except BaseException:
                data.log.warn("Problem writing .csv backup for %s" % fx_code)


def backup_multiple_to_csv(data):
    instrument_list = data.arctic_futures_multiple_prices.get_list_of_instruments()
    for instrument_code in instrument_list:
        arctic_data = data.arctic_futures_multiple_prices.get_multiple_prices(
            instrument_code
        )
        csv_data = data.csv_futures_multiple_prices.get_multiple_prices(
            instrument_code)

        if check_df_equals(arctic_data, csv_data):
            print("No update needed")
            pass
        else:
            try:
                data.csv_futures_multiple_prices.add_multiple_prices(
                    instrument_code, arctic_data, ignore_duplication=True
                )
                data.log.msg(
                    "Written .csv backup multiple prices for %s" %
                    instrument_code)
            except BaseException:
                data.log.warn(
                    "Problem writing .csv backup multiple prices for %s"
                    % instrument_code
                )


def backup_adj_to_csv(data):
    instrument_list = data.arctic_futures_adjusted_prices.get_list_of_instruments()
    for instrument_code in instrument_list:
        arctic_data = data.arctic_futures_adjusted_prices.get_adjusted_prices(
            instrument_code
        )
        csv_data = data.csv_futures_adjusted_prices.get_adjusted_prices(
            instrument_code)

        if check_ts_equals(arctic_data, csv_data):
            print("No update needed")
            pass
        else:
            try:
                data.csv_futures_adjusted_prices.add_adjusted_prices(
                    instrument_code, arctic_data, ignore_duplication=True
                )
                data.log.msg(
                    "Written .csv backup for adjusted prices %s" %
                    instrument_code)
            except BaseException:
                data.log.warn(
                    "Problem writing .csv backup for adjusted prices %s"
                    % instrument_code
                )


def backup_contract_position_data(data):
    instrument_list = (
        data.mongo_contract_position.get_list_of_instruments_with_any_position())
    for instrument_code in instrument_list:
        contract_list = data.mongo_contract_position.get_list_of_contracts_with_any_position_for_instrument(
            instrument_code)
        for contract in contract_list:
            mongo_data = data.mongo_contract_position.get_position_as_df_for_instrument_and_contract_date(
                instrument_code, contract)
            data.csv_contract_position.write_position_df_for_instrument_and_contract_date(
                instrument_code, contract, mongo_data)
            data.log.msg(
                "Backed up %s %s contract position data" %
                (instrument_code, contract))


def backup_strategy_position_data(data):
    strategy_list = get_list_of_strategies(data)
    instrument_list = (
        data.mongo_contract_position.get_list_of_instruments_with_any_position())
    for strategy_name in strategy_list:
        for instrument_code in instrument_list:
            mongo_data = data.mongo_strategy_position.get_position_as_df_for_strategy_and_instrument(
                strategy_name, instrument_code)
            if mongo_data is missing_data:
                continue
            data.csv_strategy_position.write_position_df_for_instrument_strategy(
                strategy_name, instrument_code, mongo_data)
            data.log.msg(
                "Backed up %s %s strategy position data"
                % (instrument_code, strategy_name)
            )


def backup_historical_orders(data):
    data.log.msg("Backing up strategy orders...")
    list_of_orders = [
        data.mongo_strategy_historic_orders.get_order_with_orderid(id)
        for id in data.mongo_strategy_historic_orders.get_list_of_order_ids()
    ]
    data.csv_strategy_historic_orders.write_orders(list_of_orders)
    data.log.msg("Done")

    data.log.msg("Backing up contract orders...")
    list_of_orders = [
        data.mongo_contract_historic_orders.get_order_with_orderid(id)
        for id in data.mongo_contract_historic_orders.get_list_of_order_ids()
    ]
    data.csv_contract_historic_orders.write_orders(list_of_orders)
    data.log.msg("Done")

    data.log.msg("Backing up broker orders...")
    list_of_orders = [
        data.mongo_broker_historic_orders.get_order_with_orderid(id)
        for id in data.mongo_broker_historic_orders.get_list_of_order_ids()
    ]
    data.csv_broker_historic_orders.write_orders(list_of_orders)
    data.log.msg("Done")


def backup_capital(data):
    strategy_list = get_list_of_strategies(data)
    capital_data = dict()
    for strategy_name in strategy_list:
        capital_data[
            strategy_name
        ] = data.mongo_capital.get_capital_pd_series_for_strategy(strategy_name)

    capital_data["TOTAL_total"] = data.mongo_capital.get_total_capital_pd_series()
    capital_data[
        "TOTAL_broker"
    ] = data.mongo_capital.get_broker_account_value_pd_series()
    capital_data["TOTAL_max"] = data.mongo_capital.get_maximum_account_value_pd_series()
    capital_data[
        "TOTAL_pandl"
    ] = data.mongo_capital.get_profit_and_loss_account_pd_series()

    capital_data = pd.concat(capital_data, axis=1)
    capital_data.columns = strategy_list + [
        "TOTAL_total",
        "TOTAL_broker",
        "TOTAL_max",
        "TOTAL_pandl",
    ]
    capital_data = capital_data.ffill()

    data.csv_capital.write_df_of_all_capital(capital_data)
    data.log.msg("Backed up capital data")


def backup_optimal_positions(data):
    strategy_list = get_list_of_strategies(data)
    for strategy_name in strategy_list:
        instrument_list = data.mongo_optimal_position.get_list_of_instruments_for_strategy_with_optimal_position(
            strategy_name)
        for instrument_code in instrument_list:
            mongo_data = data.mongo_optimal_position.get_optimal_position_as_df_for_strategy_and_instrument(
                strategy_name, instrument_code)
            if mongo_data is missing_data:
                continue
            data.csv_optimal_position.write_position_df_for_instrument_strategy(
                strategy_name, instrument_code, mongo_data)
            data.log.msg(
                "Backed up %s %s optimal position data"
                % (instrument_code, strategy_name)
            )


def backup_instrument_data(data):
    instrument_config = data.mongo_futures_instrument.get_all_instrument_data()
    data.csv_futures_instrument.write_all_instrument_data(instrument_config)
    data.log.msg("Backed up instrument config data")


def backup_roll_state_data(data):
    instrument_list = data.mongo_roll_state.get_list_of_instruments()
    roll_state_list = []
    for instrument_code in instrument_list:
        roll_state = data.mongo_roll_state.get_roll_state(instrument_code)
        roll_state_list.append(roll_state)

    roll_state_df = pd.DataFrame(roll_state_list, index=instrument_list)
    roll_state_df.columns = ["state"]
    data.csv_roll_state.write_all_instrument_data(roll_state_df)
    data.log.msg("Backed up roll state")


def backup_contract_data(data):
    instrument_list = data.mongo_futures_instrument.get_list_of_instruments()
    for instrument_code in instrument_list:
        contract_list = (
            data.mongo_futures_contract.get_all_contract_objects_for_instrument_code(
                instrument_code
            )
        )
        data.csv_futures_contract.write_contract_list_as_df(
            instrument_code, contract_list
        )
        data.log.msg("Backed up contract data for %s" % instrument_code)
