from copy import copy
from syscore.objects import arg_not_supplied
from sysdata.mongodb.mongo_connection import (
    mongoConnection,
    MONGO_ID_KEY,
    mongo_clean_ints,
)

from syscore.objects import missing_data, missingData, existingData


class mongoDataWithSingleKey(object):
    """
    Read and write data class to get data from a mongo database

    """


    def __init__(self, collection_name, key_name, mongo_db=arg_not_supplied):
        self.init_mongo(collection_name, key_name, mongo_db=mongo_db)

    def init_mongo(self, collection_name: str, key_name: str, mongo_db =arg_not_supplied,):
        mongo_object = mongoConnection(collection_name, mongo_db=mongo_db)

        self._mongo = mongo_object
        self._key_name = key_name

        # this won't create the index if it already exists
        # if a different index exists (FIX ME WILL HAPPEN UNTIL NEW DATA READY)...
        try:
            self._mongo.create_index(self.key_name)
        except:
            pass
            ## no big deal


    def __repr__(self):
        return self.name


    @property
    def key_name(self) -> str:
        return self._key_name


    @property
    def name(self) -> str:
        mongo_object = self._mongo
        name = (
            "mongoData connection for %s, mongodb %s/%s @ %s -p %s " %
            (mongo_object.collection_name,
            mongo_object.database_name,
             mongo_object.collection_name,
             mongo_object.host,
             mongo_object.port,
             ))

        return name

    def get_list_of_keys(self)->list:
        cursor = self._mongo.collection.find()
        key_name = self.key_name
        key_list = [db_entry[key_name] for db_entry in cursor]

        return key_list


    def get_result_dict_for_key(self, key: str) ->dict:
        key_name = self.key_name
        result_dict = self._mongo.collection.find_one(
            {key_name:key}
        )
        if result_dict is None:
            return missing_data

        result_dict.pop(MONGO_ID_KEY)

        return result_dict

    def get_result_dict_for_key_without_key_value(self, key: str) ->dict:
        key_name = self.key_name
        result_dict = self.get_result_dict_for_key(key)
        if result_dict is missing_data:
            return missing_data

        result_dict.pop(key_name)

        return result_dict

    def key_is_in_data(self, key: str):
        result = self.get_result_dict_for_key(key)
        if result is missing_data:
            return False
        else:
            return True

    def delete_data_without_any_warning(
            self, key: str):
        key_name = self.key_name

        if not self.key_is_in_data(key):
            raise missingData("%s:%s not in data %s" % (key_name, key, self.name))

        self._mongo.collection.remove({key_name: key})

    def add_data(self, key: str, data_dict: dict, allow_overwrite = False, clean_ints = True):
        if clean_ints:
            cleaned_data_dict = mongo_clean_ints(data_dict)
        else:
            cleaned_data_dict = copy(data_dict)

        if self.key_is_in_data(key):
            if allow_overwrite:
                self._update_existing_data_with_cleaned_dict(key, cleaned_data_dict)
            else:
                raise existingData("Can't overwite existing data %s/%s for %s" % (self.key_name, key, self.name))
        else:
            self._add_new_cleaned_dict(key, cleaned_data_dict)

    def _update_existing_data_with_cleaned_dict(self, key, cleaned_data_dict):

        key_name = self.key_name
        self._mongo.collection.update_one({key_name:key}, {"$set":cleaned_data_dict})

    def _add_new_cleaned_dict(self, key, cleaned_data_dict):
        key_name = self.key_name
        cleaned_data_dict[key_name] = key
        self._mongo.collection.insert_one(cleaned_data_dict)

class mongoDataWithMultipleKeys(object):
    """
    Read and write data class to get data from a mongo database

    Use this if you aren't using a specific key as the index

    """


    def __init__(self, collection_name: str, mongo_db=arg_not_supplied):
        self.init_mongo(collection_name, mongo_db=mongo_db)

    def init_mongo(self, collection_name: str, mongo_db =arg_not_supplied,):
        mongo_object = mongoConnection(collection_name, mongo_db=mongo_db)

        self._mongo = mongo_object


    def __repr__(self):
        return self.name

    @property
    def name(self) -> str:
        mongo_object = self._mongo
        name = (
            "mongoData connection for %s, mongodb %s/%s @ %s -p %s " %
            (mongo_object.collection_name,
            mongo_object.database_name,
             mongo_object.collection_name,
             mongo_object.host,
             mongo_object.port,
             ))

        return name

    def get_list_of_all_dicts(self)->list:
        cursor = self._mongo.collection.find()
        dict_list = [db_entry for db_entry in cursor]
        _ = [dict_item.pop(MONGO_ID_KEY) for dict_item in dict_list]

        return dict_list


    def get_result_dict_for_dict_keys(self, dict_of_keys: dict) ->dict:
        result_dict = self._mongo.collection.find_one(
            dict_of_keys
        )
        if result_dict is None:
            return missing_data

        result_dict.pop(MONGO_ID_KEY)

        return result_dict

    def get_list_of_result_dicts_for_dict_keys(self, dict_of_keys: dict) -> list:
        cursor_of_result_dicts = self._mongo.collection.find(
            dict_of_keys
        )

        if cursor_of_result_dicts is None:
            return []

        list_of_result_dicts = list(cursor_of_result_dicts
                                    )
        _ = [result_dict.pop(MONGO_ID_KEY) for result_dict in list_of_result_dicts]

        return list_of_result_dicts


    def key_dict_is_in_data(self, dict_of_keys: dict) -> bool:
        result = self.get_result_dict_for_dict_keys(dict_of_keys)
        if result is missing_data:
            return False
        else:
            return True

    def add_data(self, dict_of_keys: dict, data_dict: dict, allow_overwrite = False, clean_ints = True):
        if clean_ints:
            cleaned_data_dict = mongo_clean_ints(data_dict)
        else:
            cleaned_data_dict = copy(data_dict)

        if self.key_dict_is_in_data(dict_of_keys):
            if allow_overwrite:
                self._update_existing_data_with_cleaned_dict(dict_of_keys, cleaned_data_dict)
            else:
                raise existingData("Can't overwite existing data %s for %s" % (str(dict_of_keys), self.name))
        else:
            self._add_new_cleaned_dict(dict_of_keys, cleaned_data_dict)

    def _update_existing_data_with_cleaned_dict(self, dict_of_keys: dict, cleaned_data_dict: dict):

        self._mongo.collection.update_one(dict_of_keys, {"$set":cleaned_data_dict})

    def _add_new_cleaned_dict(self, dict_of_keys: dict, cleaned_data_dict: dict):
        dict_with_both_keys_and_data= {}
        dict_with_both_keys_and_data.update(cleaned_data_dict)
        dict_with_both_keys_and_data.update(dict_of_keys)

        self._mongo.collection.insert_one(dict_with_both_keys_and_data)

    def delete_data_without_any_warning(
            self, dict_of_keys):

        self._mongo.collection.remove(dict_of_keys)
