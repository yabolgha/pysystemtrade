from syscore.objects import missing_contract

from sysobjects.contract_dates_and_expiries import contractDate, expiryDate
from sysobjects.contracts import futuresContract, listOfFuturesContracts
from sysobjects.instruments import futuresInstrument
from sysobjects.rolls import contractDateWithRollParameters

from sysdata.data_blob import dataBlob
from sysproduction.data.prices import diagPrices
from sysproduction.data.contracts import diagContracts, updateContracts
from sysproduction.data.broker import dataBroker


def update_sampled_contracts():
    """
    Update the active contracts, according to what is available in IB for a given instrument

    These are stored in mongoDB

    The active contracts list is used to see what contracts have historical data sampled for

    It does not tell you what the current priced, forward, or carry contract are - that is in multiple prices (DRY)

    However we base the list of theoretical active contracts on the current priced, forward, and carry contracts

    We will end up adding to this list when we roll; this will change the current priced, forward, and carry contract

    When we add a new contract (because one has become available), we get the exact expiry date from IB and save this with the
       contract data.

    We do not sample contracts on the list when they have passed their expiry date

    Contracts are never deleted from the database

    We don't check IB for contracts; since we can't reverse engineer a YYYYMM identifier from a YYYYMMDD

    :returns: None
    """
    with dataBlob(log_name="Update-Sampled_Contracts") as data:
        update_contracts_object = updateSampledContracts(data)
        update_contracts_object.update_sampled_contracts()


class updateSampledContracts(object):
    def __init__(self, data):
        self.data = data

    def update_sampled_contracts(self):
        data = self.data
        update_active_contracts_with_data(data)

def update_active_contracts_with_data(data: dataBlob):
    diag_prices = diagPrices(data)
    list_of_codes_all = diag_prices.get_list_of_instruments_in_multiple_prices()
    for instrument_code in list_of_codes_all:
        update_active_contracts_for_instrument(
            instrument_code, data)


def update_active_contracts_for_instrument(
        instrument_code: str, data: dataBlob):
    # Get the list of contracts we'd want to get prices for, given current
    # roll calendar
    required_contract_chain = get_contract_chain(data, instrument_code)

    # Make sure contract chain and database are aligned
    update_contract_database_with_contract_chain(
        instrument_code, required_contract_chain, data
    )

    # Now to check if expiry dates are resolved
    update_expiries_of_sampled_contracts(instrument_code, data)

    # mark expired as no longer sampling
    stop_expired_contracts_sampling(instrument_code, data)


def get_contract_chain(data: dataBlob, instrument_code: str) -> listOfFuturesContracts:

    furthest_out_contract = get_furthest_out_contract_with_roll_parameters(data, instrument_code)
    contract_object_chain = create_contract_object_chain(furthest_out_contract, instrument_code)

    return contract_object_chain

def get_furthest_out_contract_with_roll_parameters(data: dataBlob,
                                                   instrument_code: str) \
                                                -> contractDateWithRollParameters:

    furthest_out_contract_date = get_furthest_out_contract_date(data, instrument_code)
    furthest_out_contract = create_furthest_out_contract_with_roll_parameters_from_contract_date(data,
                                                                                                 instrument_code,
                                                                                                 furthest_out_contract_date)

    return furthest_out_contract

def get_furthest_out_contract_date(data: dataBlob,
                                   instrument_code: str) -> str:

    diag_prices = diagPrices(data)

    # Get the last contract currently being used
    multiple_prices = diag_prices.get_multiple_prices(instrument_code)
    current_contract_dict = multiple_prices.current_contract_dict()
    furthest_out_contract_date = current_contract_dict.furthest_out_contract_date()

    return furthest_out_contract_date

def create_furthest_out_contract_with_roll_parameters_from_contract_date(data: dataBlob, instrument_code: str,
                                                                         furthest_out_contract_date: str):

    diag_contracts = diagContracts(data)
    roll_parameters = diag_contracts.get_roll_parameters(instrument_code)

    furthest_out_contract = contractDateWithRollParameters(
        contractDate(furthest_out_contract_date), roll_parameters
    )

    return furthest_out_contract

def create_contract_object_chain(furthest_out_contract: contractDateWithRollParameters,
                                  instrument_code: str) -> listOfFuturesContracts:

    contract_date_chain = create_contract_date_chain(furthest_out_contract)
    contract_object_chain = create_contract_object_chain_from_contract_date_chain(instrument_code, contract_date_chain)

    return contract_object_chain

def create_contract_date_chain(furthest_out_contract: contractDateWithRollParameters) ->list:
    # To give us wiggle room, and ensure we start collecting the new forward a
    # little in advance
    final_contract = furthest_out_contract.next_priced_contract()

    ## this will pick up contracts from 6 months ago, to deal with any gaps
    ## however if these have expired they are marked as finished sampling later
    contract_date_chain = (
        final_contract.get_contracts_from_recently_to_contract_date()
    )

    return contract_date_chain

def create_contract_object_chain_from_contract_date_chain(instrument_code: str,
                                                          contract_date_chain: list) \
                                                    -> listOfFuturesContracts:

    # We have a list of contract_date objects, need futureContracts
    # create a 'bare' instrument object
    instrument_object = futuresInstrument(instrument_code)

    contract_object_chain_as_list = [
        futuresContract(instrument_object, contract_date)
        for contract_date in contract_date_chain
    ]

    contract_object_chain = listOfFuturesContracts(
        contract_object_chain_as_list)

    return contract_object_chain

def update_contract_database_with_contract_chain(
    instrument_code: str, required_contract_chain: listOfFuturesContracts, data: dataBlob
):
    """

    :param required_contract_chain: list of contract dates 'yyyymm'
    :param instrument_code: str
    :param data: dataBlob
    :return: None
    """

    current_contract_chain_in_db = get_current_contract_chain_in_db(data, instrument_code)

    missing_from_db = required_contract_chain.difference(
        current_contract_chain_in_db)

    add_missing_contracts_to_database(
         missing_from_db, data)


def get_current_contract_chain_in_db(data: dataBlob, instrument_code:str) -> listOfFuturesContracts:
    diag_contracts = diagContracts(data)

    # Get list of contracts in the database
    all_contracts_in_db = diag_contracts.get_all_contract_objects_for_instrument_code(
        instrument_code)
    current_contract_chain = all_contracts_in_db.currently_sampling()

    return current_contract_chain

def add_missing_contracts_to_database(
     missing_from_db: listOfFuturesContracts, data: dataBlob
):
    """

    :param missing_from_db: list of contract_date objects
    :param data: dataBlob
    :return: None
    """

    for contract_to_add in missing_from_db:
        add_missing_contract_to_database(data, contract_to_add)

    return None

def add_missing_contract_to_database(data: dataBlob, contract_to_add: futuresContract):
    diag_contracts = diagContracts(data)
    update_contracts = updateContracts(data)
    instrument_code = contract_to_add.instrument_code

    contract_date_str = contract_to_add.date_str

    if diag_contracts.is_contract_in_data(instrument_code, contract_date_str):
        contract_to_add = diag_contracts.get_contract_object(
            instrument_code, contract_date_str
        )

    # Mark it as sampling
    contract_to_add.sampling_on()

    # Add it to the database
    # We are happy to overwrite
    update_contracts.add_contract_data(
        contract_to_add, ignore_duplication=True)

    log = data.log.setup(instrument_code=instrument_code)

    log.msg(
        "Contract %s now added to database and sampling" %
        str(contract_to_add))



def update_expiries_of_sampled_contracts(
        instrument_code: str, data: dataBlob):
    """
    # Now to check if expiry dates are resolved
    # For everything in the database which is sampling
    #   - if it hasn't got an IB expiry recorded, then check for the expiry in IB (can fail)
    #    - if expiry found, add expiry to database, and flag in lookup table as found

    :param instrument_code:
    :param data: dataBlob
    :return: None
    """

    diag_contracts = diagContracts(data)

    all_contracts_in_db = diag_contracts.get_all_contract_objects_for_instrument_code(
        instrument_code)
    currently_sampling_contracts = all_contracts_in_db.currently_sampling()

    for contract_object in currently_sampling_contracts:
        update_expiry_for_contract(contract_object, data)

    return None


def update_expiry_for_contract(contract_object: futuresContract, data: dataBlob):
    """
    Get an expiry from IB, check if same as database, otherwise update the database

    :param contract_object: contract object
    :param data: dataBlob
    :param log: log
    :return: None
    """
    log = data.log
    diag_contracts = diagContracts(data)
    data_broker = dataBroker(data)

    contract_date = contract_object.date_str
    instrument_code = contract_object.instrument_code

    log = log.setup(
        instrument_code=instrument_code,
        contract_date=contract_date)
    db_contract = diag_contracts.get_contract_object(
        instrument_code, contract_date)

    db_expiry_date = db_contract.expiry_date
    broker_expiry_date = \
        data_broker.get_actual_expiry_date_for_single_contract(db_contract)

    if broker_expiry_date is missing_contract:
        log.msg(
            "Can't find expiry for %s, could be a connection problem but could be because contract has already expired"
            % (str(contract_object))
        )

        ## don't warn as probably expired we'll remove it from the sampling list
        return None

    if broker_expiry_date == db_expiry_date:
        log.msg(
            "No change to contract expiry %s to %s"
            % (str(contract_object), str(broker_expiry_date))
        )
        return None

    # Different!
    update_contract_object_with_new_expiry_date(data, broker_expiry_date, contract_object)

def update_contract_object_with_new_expiry_date(data: dataBlob,
                                                broker_expiry_date: expiryDate,
                                                contract_object: futuresContract):
    update_contracts = updateContracts(data)

    contract_object.update_single_expiry_date(broker_expiry_date)
    update_contracts.add_contract_data(
        contract_object, ignore_duplication=True)

    data.log.msg(
        "Updated expiry of contract %s to %s"
        % (str(contract_object), str(broker_expiry_date))
    )


def stop_expired_contracts_sampling(instrument_code: str, data: dataBlob):
    ## expiry dates will have been updated and are correct
    current_contract_chain_in_db = get_current_contract_chain_in_db(data, instrument_code)

    diag_contracts = diagContracts(data)
    update_contracts = updateContracts(data)
    log = data.log.setup(instrument_code=instrument_code)

    for contract_date_object in current_contract_chain_in_db:
        contract_date = contract_date_object.date_str

        # Mark it as stop sampling in the database
        contract = diag_contracts.get_contract_object(
            instrument_code, contract_date)
        if contract.expired() and contract.currently_sampling:
            contract.sampling_off()
            update_contracts.add_contract_data(
                contract, ignore_duplication=True)

            log.msg(
                "Contract %s has now stopped sampling" % str(contract),
                contract_date=contract.date_str,
            )

