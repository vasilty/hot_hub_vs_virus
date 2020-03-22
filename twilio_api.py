import logging

from flask import Blueprint, request, url_for
from twilio.twiml.voice_response import VoiceResponse

from config import cache
from hub_api import handle_open_help_request
from models import HelpRequest, HelpRequestStatuses
from utils import now

logger = logging.getLogger(__name__)

twilio_api = Blueprint('twilio_api', __name__)


@twilio_api.route('/voice')
def voice_call_start():
    call_sid = request.args['CallSid']
    phone_number = request.args.get('From')
    postal_code = request.args.get('FromZip')
    logger.debug(f'Incoming call from phone number {phone_number} in {postal_code}')
    cache.set(call_sid, {'phone_number': phone_number, 'postal_code': postal_code})

    if not postal_code:
        return voice_request_postal_code(call_sid)
    elif not phone_number:
        return voice_request_phone_number(call_sid)
    return voice_request_confirmation(call_sid, postal_code, phone_number)


def voice_request_postal_code(call_sid):
    response = VoiceResponse()
    response.say('Hallo, damit ich einen Kontakt finden kann, geben Sie bitte '
                 'Ihre Postleitzahl ein? Und bestätigen Sie mit #',
                 voice='woman', language='de-DE')
    response.gather(numDigits="5",
                    action=url_for('twilio_api.voice_get_postal_code', call_sid=call_sid))
    return str(response)


def voice_request_phone_number(call_sid):
    response = VoiceResponse()
    response.say('Bitte geben sie jetzt ihre Rückrufnummer ein'
                 'und bestätigen Sie mit #',
                 voice='woman', language='de-DE')
    response.gather(action=url_for('twilio_api.voice_get_phone_number', call_sid=call_sid))
    return str(response)


def voice_request_confirmation(call_sid, postal_code, phone_number):
    response = VoiceResponse()
    response.say(f"Jemand in der Nähe von {postal_code} ruft sie bald unter "
                 f"{phone_number} an. Bitte bestätigen mit 1 Korrektur Postleitzahl "
                 f"mit 2 Korrektur Telefonnummer mit 3",
                 voice='woman', language='de-DE')
    response.gather(action=url_for('twilio_api.voice_confirm', call_sid=call_sid))
    return str(response)


@twilio_api.route('/call/<call_sid>/postal_code', methods=['POST'])
def voice_get_postal_code(call_sid):
    call_data = cache.get(call_sid)
    phone_number = call_data['phone_number']
    postal_code = request.values['Digits']
    # ToDo: check if valid postal_code

    call_data['postal_code'] = postal_code
    cache.set(call_sid, call_data)
    if not phone_number:
        return voice_request_phone_number(call_sid)
    return voice_request_confirmation(call_sid, postal_code, phone_number)


@twilio_api.route('/call/<call_sid>/phone_number', methods=['POST'])
def voice_get_phone_number(call_sid):
    postal_code = cache.get(call_sid)['postal_code']
    phone_number = request.values['Digits']
    return voice_request_confirmation(call_sid, postal_code, phone_number)


@twilio_api.route('/call/<call_sid>/confirm', methods=['POST'])
def voice_confirm(call_sid):
    confirm_code = request.values['Digits']
    response = VoiceResponse()
    if confirm_code != '1':
        response.say("Bitte rufen Sie nocheinmal an!",
                     voice='woman', language='de-DE')
    else:
        call_data = cache.get(call_sid)
        help_request = HelpRequest.create(
            postal_code=call_data['postal_code'],
            phone_number=call_data['phone_number'],
            status=HelpRequestStatuses.OPEN,
            status_changed_at=now(),
            created_at=now(),
        )
        handle_open_help_request(help_request)
        response.say("Vielen Dank! Es ruft bald jemand an.",
                     voice='woman', language='de-DE')
    return str(response)
