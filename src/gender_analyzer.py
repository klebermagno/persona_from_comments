import json
import requests
from . import settings


class GenderAnalyzer:

    def get_names_genders(self, full_name_list) -> str:
        genders = {}
        for name_dict in full_name_list:
            # Assuming each item in full_name_list is a dict with an 'author' key
            author_name = name_dict.get("id", "")
            if author_name:
                genders[author_name] = "male"

        return genders
