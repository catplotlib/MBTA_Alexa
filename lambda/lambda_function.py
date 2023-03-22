

# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.

import requests
import json
import datetime
from dateutil import tz

import logging
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)
    
    def handle(self, handler_input):
        speak_output = "Please say your station Name and eastbound or westbound to get the next train arrival time."
        reprompt = "Please say eastbound or westbound."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt)
                .response
        )


def get_station_id(station_name):
    # Replace with your own MBTA API key
    api_key = '7bca808b3fb14701a50dc4a656d830d3'
    headers = {'x-api-key': api_key}

    # URL to search for the station by its name
    url = f'https://api-v3.mbta.com/stops?filter[route_type]=0'

    # Make the API request to fetch the station data
    response = requests.get(url, headers=headers)

    # Parse the JSON response
    data = json.loads(response.text)
    stations = data['data']  # Replace this with the list of station dictionaries from the API
    search_name = station_name.lower()

    found_station = None
    for station in stations:
        if (station['attributes']['name']).lower() == search_name:
            found_station = station
            break

    if found_station:
        station_id=found_station['relationships']['parent_station']['data']['id']
        return station_id


def get_next_train_arrival(stationName,station_id,direction):
    # Replace with your own MBTA API key
    api_key = '7bca808b3fb14701a50dc4a656d830d3'
    headers = {'x-api-key': api_key}
    # Get the current time in ISO format
    current_time = datetime.datetime.now(tz.tzutc())
    # Set the filter parameters based on the station and direction
    if direction == 'eastbound':
        url = f'https://api-v3.mbta.com/predictions?filter[stop]={station_id}&filter[route_type]=0&filter[direction_id]=0&sort=arrival_time&include=stop,trip&fields[trip]=destination_name,name,headsign&fields[stop]=name'
    elif direction == 'westbound':
        url = f'https://api-v3.mbta.com/predictions?filter[stop]={stationName}&filter[route]=Green-B&filter[direction_id]=1&sort=arrival_time&include=stop,trip&fields[trip]=destination_name,name,headsign&fields[stop]=name'
    else:
        return "Invalid direction. Please specify 'eastbound' or 'westbound'."
    # Make the API request to fetch the train schedule data
    response = requests.get(url, headers=headers)
    
    # Parse the JSON response and extract the next train arrival time
    data = json.loads(response.text)
    
    # Filter out past predictions
    future_predictions = [p for p in data['data'] if datetime.datetime.fromisoformat(p['attributes']['arrival_time']) >= current_time]
    
    try:
        next_arrival_time = future_predictions[0]['attributes']['arrival_time']
        # Parse the string into a datetime object
        dt_obj = datetime.datetime.fromisoformat(next_arrival_time)
        # Format the datetime object as a 12-hour time string
        time_string = dt_obj.strftime("%I:%M %p")
        return time_string
    except IndexError:
        return f"No upcoming train arrivals found."


class NextTrainArrivalIntentHandler(AbstractRequestHandler):
    """Handler for Next Train Arrival Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("NextTrainArrivalIntent")(handler_input)

    def handle(self, handler_input):
        # Get the direction slot value
        direction = ask_utils.get_slot(handler_input, "Direction").value
        stationName= ask_utils.get_slot(handler_input, "stationname").value
        logger.info(f"Direction: {direction}")
        logger.info(f"Station Name: {stationName}")
        
        stationID = get_station_id(stationName)
        # Call the get_next_train_arrival function
        next_arrival_time = get_next_train_arrival(stationName,stationID,direction)
        
        # Create the speak output
        speak_output = f"The next train at {stationName} in the {direction} direction will arrive at {next_arrival_time}."
        #speak_output="Hello"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )



class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, I'm not sure. You can say Hello or Help. What would you like to do?"
        reprompt = "I didn't catch that. What can I help you with?"

        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = str(logger.error(exception, exc_info=True))

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(NextTrainArrivalIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
# sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()

