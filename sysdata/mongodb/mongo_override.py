from syscore.objects import missing_data
from sysdata.production.override import overrideData
from sysobjects.production.override import Override
from sysdata.mongodb.mongo_generic import mongoDataWithMultipleKeys
from syslogdiag.log import logtoscreen

OVERRIDE_STATUS_COLLECTION = "overide_status"
OVERRIDE_TYPE = 'dict_name' # yeah I know but for historical reasons
OVERRIDE_KEY = 'key'
OVERRIDE_VALUE = 'value'

class mongoOverrideData(overrideData):
    """
    Read and write data class to get override state data


    """

    def __init__(self, mongo_db=None, log=logtoscreen("mongoOverrideData")):

        super().__init__(log=log)
        self._mongo_data = mongoDataWithMultipleKeys(OVERRIDE_STATUS_COLLECTION, mongo_db=mongo_db)

    def __repr__(self):
        return "mongoOverrideData %s" % str(self.mongo_data)

    @property
    def mongo_data(self):
        return self._mongo_data

    def _get_override_object_for_type_and_key(self, override_type:str, key:str) ->Override:
        # return missing_data if nothing found
        dict_of_keys = {OVERRIDE_KEY: key, OVERRIDE_TYPE: override_type}
        result_dict = self.mongo_data.get_result_dict_for_dict_keys(dict_of_keys)
        if result_dict is missing_data:
            return self.default_override()

        override = _from_dict_to_override(result_dict)

        return override

    def _update_override(self, override_type:str, key:str, new_override_object:Override):
        if new_override_object.is_no_override():
            self._update_override_to_no_override(override_type, key, new_override_object)
        else:
            self._update_other_type_of_override(override_type, key, new_override_object)

    def _update_override_to_no_override(self, override_type:str, key:str, new_override_object:Override):
        dict_of_keys = {OVERRIDE_KEY: key, OVERRIDE_TYPE: override_type}
        self.mongo_data.delete_data_without_any_warning(dict_of_keys)

    def _update_other_type_of_override(self, override_type:str, key:str, new_override_object:Override):
        dict_of_keys = {OVERRIDE_KEY: key, OVERRIDE_TYPE: override_type}
        new_override_as_dict = _from_override_to_dict(new_override_object)

        self.mongo_data.add_data(dict_of_keys, new_override_as_dict, allow_overwrite=True)


    def _get_dict_of_items_with_overrides_for_type(self, override_type: str) -> dict:
        dict_of_keys = {OVERRIDE_TYPE: override_type}
        results = self.mongo_data.get_list_of_result_dicts_for_dict_keys(dict_of_keys)
        result_dict_of_overrides = dict([(result_dict[OVERRIDE_KEY], _from_dict_to_override(result_dict)) for result_dict in results])

        return result_dict_of_overrides

def _from_dict_to_override(result_dict: dict)-> Override:
    value = result_dict[OVERRIDE_VALUE]
    override = Override.from_numeric_value(value)
    return override

def _from_override_to_dict(override: Override) -> dict:
    override_as_value = override.as_numeric_value()
    override_as_dict = {OVERRIDE_VALUE: override_as_value}

    return override_as_dict