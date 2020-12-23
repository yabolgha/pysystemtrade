"""
This is a futures system

A system consists of a system, plus a config

"""
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
from sysdata.configdata import Config

from systems.forecasting import Rules
from systems.basesystem import System
from systems.forecast_combine import ForecastCombine
from systems.forecast_scale_cap import ForecastScaleCap
from systems.futures.rawdata import FuturesRawData
from systems.positionsizing import PositionSizing
from systems.portfolio import Portfolios
from systems.account import Account


def futures_system(data=None, config=None, trading_rules=None, log_level="on"):
    """

    :param data: data object (defaults to reading from csv files)
    :type data: sysdata.data.simData, or anything that inherits from it

    :param config: Configuration object (defaults to futuresconfig.yaml in this directory)
    :type config: sysdata.configdata.Config

    :param trading_rules: Set of trading rules to use (defaults to set specified in config object)
    :type trading_rules: list or dict of TradingRules, or something that can be parsed to that

    :param log_level: How much logging to do
    :type log_level: str


    >>> system=futures_system(log_level="off")
    >>> system
    System with stages: accounts, portfolio, positionSize, rawdata, combForecast, forecastScaleCap, rules
    >>> system.rules.get_raw_forecast("EDOLLAR", "ewmac2_8").dropna().head(2)
                ewmac2_8
    1983-10-10  0.695929
    1983-10-11 -0.604704

                ewmac2_8
    2015-04-21  0.172416
    2015-04-22 -0.477559
    >>> system.rules.get_raw_forecast("EDOLLAR", "carry").dropna().head(2)
                   carry
    1983-10-10  0.952297
    1983-10-11  0.854075

                   carry
    2015-04-21  0.350892
    2015-04-22  0.350892
    """

    if data is None:
        data = csvFuturesSimData()

    if config is None:
        config = Config(
            "systems.provided.futures_chapter15.futuresconfig.yaml")

    rules = Rules(trading_rules)

    system = System(
        [
            Account(),
            Portfolios(),
            PositionSizing(),
            FuturesRawData(),
            ForecastCombine(),
            ForecastScaleCap(),
            rules,
        ],
        data,
        config,
    )

    system.set_logging_level(log_level)

    return system


if __name__ == "__main__":
    import doctest

    doctest.testmod()
