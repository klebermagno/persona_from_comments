import json
import requests
import settings

class GenderAnalyzer:
    
    def get_names_genders(self, full_name_list) -> str:
        url = "https://v2.namsor.com/NamSorAPIv2/api2/json/genderFullBatch"

        payload = {
            "personalNames": full_name_list
        }
        headers = {
            "X-API-KEY": settings.NAMSOR_KEY,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        response = requests.request("POST", url, json=payload, headers=headers)
        items = json.loads(response.text)

        genders = {}
        for item in items["personalNames"]:
            genders[item["id"]] = item["likelyGender"]

        return genders