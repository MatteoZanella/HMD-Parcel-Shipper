from typing import Any, Text, Dict, List
import requests
import re
import os
from urllib.parse import urlencode
from datetime import date, timedelta
from dotenv import load_dotenv
from rasa_sdk import Action, Tracker, ValidationAction, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet


load_dotenv()


class ValidateShippingForm(FormValidationAction):
    HERE_API_KEY = os.getenv('HERE_API_KEY')
    HERE_ENDPOINT = "https://geocode.search.hereapi.com/v1/geocode?"

    def name(self) -> Text:
        return "validate_shipping_form"

    def validate_sender_full_address(self, slot_value, dispatcher, tracker, domain) -> Dict[Text, Any]:
        url = self.HERE_ENDPOINT + urlencode({"q": slot_value, "lang": "en", "apikey": self.HERE_API_KEY})
        response = requests.request("GET", url, headers={}, data={})
        extracted_slots = {}
        if response.ok and len(response.json()['items']) > 0:
            item = response.json()['items'][0]
            extracted_slots['sender_full_address'] = item['title']
            extracted_slots['sender_country'] = item['address'].get('countryName')
            extracted_slots['sender_city'] = item['address'].get('city')
            extracted_slots['sender_zip'] = item['address'].get('postalCode')
            extracted_slots['sender_street'] = item['address'].get('street')
            extracted_slots['sender_house_num'] = item['address'].get('houseNumber')
        else:
            dispatcher.utter_message('Sorry, something went wrong')
            extracted_slots['sender_full_address'] = None
        return extracted_slots

    def validate_dest_full_address(self, slot_value, dispatcher, tracker, domain) -> Dict[Text, Any]:
        url = self.HERE_ENDPOINT + urlencode({"q": slot_value, "lang": "en", "apikey": self.HERE_API_KEY})
        response = requests.request("GET", url, headers={}, data={})
        extracted_slots = {}
        if response.ok and len(response.json()['items']) > 0:
            item = response.json()['items'][0]
            extracted_slots['dest_full_address'] = item['title']
            extracted_slots['dest_country'] = item['address'].get('countryName')
            extracted_slots['dest_city'] = item['address'].get('city')
            extracted_slots['dest_zip'] = item['address'].get('postalCode')
            extracted_slots['dest_street'] = item['address'].get('street')
            extracted_slots['dest_house_num'] = item['address'].get('houseNumber')
        else:
            dispatcher.utter_message('Sorry, something went wrong')
            extracted_slots['dest_full_address'] = None
        return extracted_slots

    def validate_sender_zip(self, slot_value, dispatcher, tracker, domain) -> Dict[Text, Any]:
        zip_code = re.search(r'(\d\s*){4}\d', slot_value)
        if zip_code is not None:
            zip_code = zip_code.group().replace(" ", "")
        return {'sender_zip': zip_code}

    def validate_dest_zip(self, slot_value, dispatcher, tracker, domain) -> Dict[Text, Any]:
        zip_code = re.search(r'(\d\s*){4}\d', slot_value)
        if zip_code is not None:
            zip_code = zip_code.group().replace(" ", "")
        return {'dest_zip': zip_code}

    def validate_parcel_shape(self, slot_value, dispatcher, tracker, domain):
        """Validate parcel shape value."""
        extracted_slots = {}
        if slot_value in {"box", "envelope", "tube"}:
            extracted_slots["parcel_shape"] = slot_value
        if slot_value == "tube":
            extracted_slots["parcel_size"] = "medium"
        return extracted_slots

    def validate_parcel_size(self, slot_value, dispatcher, tracker, domain) -> Dict[Text, Any]:
        """Validate parcel size value."""
        parcel_shape = tracker.get_slot('parcel_shape')
        extracted_slots = {}
        if parcel_shape == "tube":
            # Should be set automatically
            extracted_slots["parcel_size"] = "medium"
        elif parcel_shape == "envelope":
            if slot_value in {"small", "medium"}:
                extracted_slots["parcel_size"] = "medium"
            elif slot_value == "large":
                extracted_slots["parcel_size"] = slot_value
            else:
                extracted_slots["parcel_size"] = None
        elif parcel_shape == "box":
            extracted_slots["parcel_size"] = slot_value if slot_value in {"small", "medium", "large"} else None
        return extracted_slots

    def validate_sender_confirm(self, slot_value, dispatcher, tracker, domain):
        if slot_value:
            return {'sender_confirm': True}
        else:
            return {
                'sender_full_address': None,
                'sender_country': None,
                'sender_city': None,
                'sender_zip': None,
                'sender_street': None,
                'sender_house_num': None,
                'sender_confirm': None
            }

    def validate_dest_confirm(self, slot_value, dispatcher, tracker, domain):
        if slot_value:
            return {'dest_confirm': True}
        else:
            return {
                'dest_full_address': None,
                'dest_country': None,
                'dest_city': None,
                'dest_zip': None,
                'dest_street': None,
                'dest_house_num': None,
                'dest_confirm': None
            }


class ActionShippingFormSubmit(Action):

    def name(self) -> Text:
        return "action_shipping_form_submit"

    def run(self, dispatcher, tracker, domain) -> List[Dict[Text, Any]]:
        # Todo: Call to the shipping APIs
        return []


class ActionShippingFormReset(Action):

    def name(self) -> Text:
        return "action_shipping_form_reset"

    def run(self, dispatcher, tracker, domain) -> List[Dict[Text, Any]]:
        return [
            SlotSet('sender_name', None),
            SlotSet('sender_confirm', None),
            SlotSet('dest_full_address', None),
            SlotSet('dest_country', None),
            SlotSet('dest_city', None),
            SlotSet('dest_zip', None),
            SlotSet('dest_street', None),
            SlotSet('dest_house_num', None),
            SlotSet('dest_confirm', None),
            SlotSet('parcel_size', None),
            SlotSet('parcel_shape', None),
            SlotSet('shipping_speed', None),
        ]


class ActionExtractAskedInfo(Action):
    def name(self) -> Text:
        return "action_extract_asked_info"

    def run(self, dispatcher, tracker, domain) -> List[Dict[Text, Any]]:
        requested_slot = tracker.get_slot('requested_slot')
        parcel_shape = tracker.get_slot('parcel_size')
        if requested_slot in {'parcel_shape', 'parcel_size', 'shipping_speed'}:
            entities = list(set(tracker.get_latest_entity_values(requested_slot)))
            if len(entities) == 0:
                if requested_slot == 'parcel_shape':
                    entities = ['envelope', 'box', 'tube']
                elif requested_slot == 'shipping_speed':
                    entities = ['express', 'recommended', 'economic']
                elif requested_slot == 'parcel_size':
                    entities = ['small', 'medium', 'large']
            # Complement the asked sizes with the corresponding shape
            if requested_slot == 'parcel_size' and parcel_shape is not None:
                entities = [f'{parcel_shape}_{size}' for size in entities]
        else:
            entities = None
        return [SlotSet('asked_info', entities)]
        # info_size = set(tracker.get_latest_entity_values('parcel_size'))
        # info_speed = set(tracker.get_latest_entity_values('parcel_size'))
        # parcel_shape = tracker.get_slot('parcel_shape')
        # kb = {
        #     'parcel_shape': {'envelope', 'box', 'tube'},
        #     'parcel_size': {
        #         'envelope': {'medium', 'large'},
        #         'box': {'small', 'medium', 'large'},
        #         'tube': {}
        #     },
        #     'shipping_speed': {'express', 'recommended', 'economic'}
        # }
        # # Outside the corresponding requested_slots
        # if requested_slot not in kb.keys():
        #     pass
        #
        # if requested_slot in kb.keys():
        #     options = kb[requested_slot]
        #     if requested_slot == 'parcel_size':
        #         options = options[parcel_shape]
        #     slot_value = list(filter(lambda v: v in options, slot_value))
        #     if len(slot_value) == 0:
        #         slot_value = list(options)
        #     if requested_slot == 'parcel_size':
        #         slot_value = [(parcel_shape, size) for size in slot_value]
        # else:
        #     slot_value = []
        #
        # print(f'I am called: {slot_value}')
        # return [SlotSet('asked_info', list(slot_value))]
        # return [{'asked_info': slot_value}]


class ActionRespondInfo(Action):

    def __init__(self):
        super().__init__()
        today = date.today()
        express_date = today + timedelta(days=2)
        recommended_date = today + timedelta(days=4)
        economic_date = today + timedelta(days=7)
        self.kb = {
            'envelope': 'Envelopes weigh up to 750 g and are up to 2.5 cm thick.',
            'envelope_medium': 'Regular letters weigh up to 100 g and measure up to 24, 16 and 0.5 cm.',
            'envelope_large': 'Large envelopes weigh up to 750 g and measure up to 35, 25 and 2.5 cm.',
            'box': 'Boxes weigh up to 30 kg and have dimensions of few meters.',
            'box_small': 'Small boxes weigh up to 2 kg and measure up to 45, 35 and 16 cm.',
            'box_medium': 'Medium boxes weigh up to 20 kg and measure up to 61, 46 and 46 cm.',
            'box_large': 'Large boxes weigh up to 30 kg and measure 2 m per side.',
            'tube': 'Tubes are up to 90cm long and 10cm wide.',
            'express': f'Express costs 20€ and will arrive on {express_date.strftime("%B %d")}.',
            'recommended': f'Recommended costs 10€ and will arrive on {recommended_date.strftime("%B %d")}.',
            'economic': f'Economic costs 5€ and will arrive on {economic_date.strftime("%B %d")}.'
        }

    def name(self) -> Text:
        return "action_respond_info"

    def run(self, dispatcher, tracker, domain) -> List[Dict[Text, Any]]:
        asked_info = tracker.get_slot('asked_info')
        # Fake shipping information
        if asked_info is not None and len(asked_info) > 0:
            for info in asked_info:
                if info in self.kb.keys():
                    dispatcher.utter_message(self.kb[info])
        elif asked_info is not None and len(asked_info) == 0:
            dispatcher.utter_message(response='utter_dont_know')
        return []
