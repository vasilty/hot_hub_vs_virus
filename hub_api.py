from functools import wraps

import requests
from flask import Blueprint, g, request

import config
from models import (
    HelpRequest, HelpRequestStatuses, Volunteer, VolunteerAction,
    VolunteerActionTypes, VolunteerStatuses)
from utils import now

hub_api = Blueprint('hub_api', __name__)


def api_key_required(view):
    @wraps(view)
    def view_wrapper(*args, **kwargs):
        try:
            api_key = request.form['api_key']
            g.source = api_key_source_map()[api_key]
        except KeyError:
            return 'Bad api key', 403
        return view(*args, **kwargs)
    return view_wrapper


def api_key_source_map():
    return {data['api_key']: name for name, data in config.SOURCES.items()}


@hub_api.route('/volunteers/', methods=['POST'])
@api_key_required
def create_volunteer():
    try:
        id_at_source = request.form['id_at_source']
        postal_code = request.form['postal_code']
        status = request.form['status']
    except KeyError:
        return 'Missing required POST data', 400
    if status not in VolunteerStatuses.values():
        return 'Invalid status', 400
    Volunteer.create(
        source=g.source,
        id_at_source=id_at_source,
        postal_code=postal_code,
        status=status,
    )
    return {}, 201


@hub_api.route('/volunteers/<id_at_source>/', methods=['PUT', 'DELETE'])
@api_key_required
def manage_volunteer(id_at_source):
    if request.method == 'PUT':
        return update_volunteer(id_at_source)
    else:
        return delete_volunteer(id_at_source)


def delete_volunteer(id_at_source):
    Volunteer.delete().where(Volunteer.source == g.source,
                             Volunteer.id_at_source == id_at_source).execute()
    return {}, 204


@config.DATABASE.atomic()
def update_volunteer(id_at_source):
    try:
        postal_code = request.form['postal_code']
        status = request.form['status']
    except KeyError:
        return 'Missing required POST data', 400
    if status not in VolunteerStatuses.values():
        return 'Invalid status', 400
    try:
        volunteer = Volunteer.get(source=g.source, id_at_source=id_at_source)
    except Volunteer.DoesNotExist:
        return 'The requested volunteer does not exist', 404
    volunteer.postal_code = postal_code
    volunteer.status = status
    volunteer.save()
    return {}, 204


@hub_api.route('/help_requests/<int:help_request_id>/', methods=['POST'])
@config.DATABASE.atomic()
@api_key_required
def perform_volunteer_action(help_request_id):
    try:
        action = request.form['action']
    except KeyError:
        return 'Missing required POST data', 400
    try:
        help_request = HelpRequest.get(id=help_request_id)
    except HelpRequest.DoesNotExist:
        return 'The help request does not exist', 404
    if help_request.status == HelpRequestStatuses.PENDING:
        if action == VolunteerActionTypes.ACCEPT:
            status = HelpRequestStatuses.ACCEPTED
        elif action == VolunteerActionTypes.DECLINE:
            status = HelpRequestStatuses.OPEN
        else:
            return 'Invalid volunteer action', 400
    elif help_request.status == HelpRequestStatuses.ACCEPTED:
        if action == VolunteerActionTypes.FULFILL:
            status = HelpRequestStatuses.FULFILLED
        elif action == VolunteerActionTypes.DECLINE:
            status = HelpRequestStatuses.OPEN
        else:
            return 'Invalid volunteer action', 400
    else:
        return 'Volunteer actions cannot be performed on this help request', 400
    help_request.status_changed_at = now()
    help_request.status = status
    help_request.save()
    VolunteerAction.create(
        help_request=help_request,
        volunteer=help_request.volunteer,
        action=action,
        happened_at=now(),
    )
    if status == HelpRequestStatuses.OPEN:
        handle_open_help_request(help_request)
    return {}, 200


@config.DATABASE.atomic()
def handle_open_help_request(help_request):
    # ToDo: Handle errors/no matches properly. Might need a task instead that
    # handles open help requests
    if help_request.status != HelpRequestStatuses.OPEN:
        return
    volunteer = help_request.find_volunteer()
    help_request.volunteer = volunteer
    if volunteer:
        help_request.status = HelpRequestStatuses.PENDING
        help_request.status_changed_at = now()
    help_request.save()

    if volunteer:
        source_callback = config.SOURCES[volunteer.source]['pending_help_request_callback']
        if source_callback:
            requests.get(source_callback, data={'id': help_request.id})
