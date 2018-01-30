from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from flask import Blueprint, request, jsonify
import requests
from rasa_core.channels.channel import UserMessage
from rasa_core.channels.direct import CollectingOutputChannel
from rasa_core.channels.rest import HttpInputComponent

from rasa_core.trackers import DialogueStateTracker
from rasa_core.slots import Slot, TextSlot
from rasa_core.events import SlotSet

logger = logging.getLogger(__name__)


class SimpleWebChannel(HttpInputComponent):
	"""A simple web bot that listens on a url and responds."""

	def blueprint(self, on_new_message):
		custom_webhook = Blueprint('custom_webhook', __name__)

		@custom_webhook.route("/", methods=['GET'])
		def health():
			return jsonify({"status": "ok"})

		@custom_webhook.route("/webhook", methods=['POST'])
		def webhook():

			# get variable from post
			sender_id = request.form.get("sender")
			text = request.form.get("message")
			print(text)
			currentURL = request.form.get("currentURL")
			print(currentURL)

			# get tracker state
			# t_store = TrackerStore()
			# txt_slot = TextSlot('url')
			# tracker = DialogueStateTracker(sender_id=sender_id, slots=[txt_slot])
			# print(tracker.current_state())
			SlotSet('url', 'currentURL')
			# print(tracker.current_state())

			# send the bot response
			out = CollectingOutputChannel()
			on_new_message(UserMessage(text, out, sender_id))
			return jsonify([{"r": r[1]} for r in out.messages])

		return custom_webhook