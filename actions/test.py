# import requests
# import json
# from urllib.parse import urlencode
#
# API_KEY = "AIzaSyAiJkriD7_Jlua_OMIh6zqOHL4pVCRgXJw"
# params = {
#     "input": "Via Crosera 4A, Farra di Soligo, suite 3",
#     "inputtype": "textquery",
#     "fields": "formatted_address",
#     "language": "en",
#     "key": API_KEY
# }
#
# api_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?"
# url = api_url + urlencode(params)
# print(url)
# url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input=Museum%20of%20Contemporary%20Art%20Australia&inputtype=textquery&fields=formatted_address%2Cname%2Crating%2Copening_hours%2Cgeometry&key=YOUR_API_KEY"
#
# # API_KEY = "bfjoVxr867mh0PwMQm6YX3CeIfDDvlWrKZETTSk5hvI"
# # base_url = "https://geocode.search.hereapi.com/v1/geocode?"
# # query = " Vicolo Giacomo Matteotti 30 Pederobba Treviso"
# # url = base_url + urlencode({"q": query, "lang": "en", "apikey": API_KEY})
#
# print(url)
#
# payload = {}
# headers = {}
#
# response = requests.request("GET", url, headers=headers, data=payload)
#
# if response.ok:
#     print(response.json())
#     item = response.json()['items'][0]
#     print(json.dumps(item, indent=4, sort_keys=True))
