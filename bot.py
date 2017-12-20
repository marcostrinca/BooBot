'''
created by: Marcos Trinca
email: trinca@posteo.net
date: November 2017

Thanks to the RasaHQ team to provide code samples used on this project
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import logging

import sys
import warnings

from rasa_core.actions.action import Action
from rasa_core.agent import Agent
from rasa_core.channels.console import ConsoleInputChannel
from rasa_core.channels.rest import HttpInputChannel
from rasa_core.interpreter import RasaNLUInterpreter
from rasa_core.policies.sklearn_policy import SklearnPolicy

import pymysql.cursors
logger = logging.getLogger(__name__)

from CustomInput import SimpleWebChannel

# Connect to the database.
connection = pymysql.connect(host='104.131.139.15',
							 user='trinca',
							 password='Mrctrinca@23',                             
							 db='boobot',
							 charset='utf8',
							 cursorclass=pymysql.cursors.DictCursor)
print ("connect successful!!")

class ActionSaveBookmark(Action):
	def name(self):
		return 'action_save_bookmark'

	def run(self, dispatcher, tracker, domain):
		val_url = tracker.get_slot("url")
		val_tag = tracker.get_slot("tag")

		# checo se tenho URL
		if val_url is not None:

			b_id = 0; # variavel pra guardar id do bookmark assim que gravar no BD

			with connection.cursor() as cursor:

				# checo se já tenho o bookmark
				sql = "SELECT COUNT(*) FROM bookmarks WHERE url = {}".format(val_url)
				cursor.execute(sql)
				result = cursor.fetchone()
				
				# se não tenho nada então eu gravo
				if result[0] == 0:

					# SQL 
					sql = "INSERT INTO bookmarks (url, fk_user_id) \
					SELECT * FROM (SELECT %s, %s) AS tmp \
					WHERE NOT EXISTS ( \
					    SELECT url FROM bookmarks WHERE url = %s \
					) LIMIT 1"
					# sql = "INSERT INTO bookmarks (url, fk_user_id) values (%s, %s)"
					cursor.execute(sql, (val_url, 1, val_url))
					connection.commit()

					#armazeno o id deste insert
					b_id = cursor.lastrowid
					print("id da URL: {}".format(b_id))

					# checo se tenho tags
					if val_tag is not None:
						# SQL 
						sql = "INSERT INTO tags (tag) values (%s)"
						cursor.execute(sql, (val_tag))
						connection.commit()

						# armazendo o id do tag insert
						t_id = cursor.lastrowid

						# se tenho o então crio o relacionamento
						if t_id is not 0:
							sql = "INSERT INTO rel_bookmark_tag (fk_bookmark_id, fk_tag_id) values (%s, %s)"
							cursor.execute(sql, (b_id, t_id))
							connection.commit()

						description = "ok, salvei a url com as categorias"
					else:
						description = "ok, salvei a url {}".format(val_url)

				else:
					description = "você já tem esta página guardada nos teus favoritos"

		else:
			description = "hmm, eu não vejo nenhuma URL pra salvar"

		dispatcher.utter_message(description)
		return []


class ActionUpdateBookmark(Action):
	def name(self):
		return 'action_update_bookmark'

	def run(self, dispatcher, tracker, domain):
		dispatcher.utter_message('atualizado, mo querido')
		return[]


class ActionOpenBookmark(Action):
	def name(self):
		return 'action_open_bookmark'

	def run(self, dispatcher, tracker, domain):
		val = tracker.get_slot("url")
		dispatcher.utter_message("abrindo")
		return []


class ActionListBookmarks(Action):
	def name(self):
		return 'action_list_bookmarks'

	def run(self, dispatcher, tracker, domain):

		text_answer = ""		# text answer
		where_clause = None 	# where clause

		# se eu tenho alguma tag então seleciono apenas as URLs desta tag
		val_tag = tracker.get_slot('tag')
		if val_tag is not None:
			where_clause = "left join rel_bookmark_tag on bookmarks.id = fk_bookmark_id \
							left join tags on rel_bookmark_tag.fk_tag_id = tags.id \
							WHERE tags.tag = '{}'".format(val_tag)

		with connection.cursor() as cursor:
			
			sql = "SELECT * FROM bookmarks {}".format(where_clause)
			cursor.execute(sql)

			for row in cursor:
				text_answer = text_answer + row['url'] + "\n"
				# print ("row: ", row['url'])
		
			text_answer = text_answer + "isso foi o que eu achei"

		dispatcher.utter_message(text_answer)
		return []


def train_dialogue(domain_file="domain.yml", model_path="models/dialogue", training_data_file="data/stories.md"):
	print("Dialogue Trainer")
	agent = Agent(domain_file, policies=[SklearnPolicy()])

	agent.train(
			training_data_file,
			max_history=12
	)

	agent.persist(model_path)
	return agent

def train_nlu():
	print("NLU Trainer")
	from rasa_nlu.converters import load_data
	from rasa_nlu.config import RasaNLUConfig
	from rasa_nlu.model import Trainer

	training_data = load_data('data/nlu.md')
	trainer = Trainer(RasaNLUConfig("nlu_model_config.json"))
	trainer.train(training_data)
	model_directory = trainer.persist('models/nlu/', fixed_model_name="current")

	return model_directory


def run(serve_forever=True):
	model_u = "models/nlu/default/current"
	model_d = "models/dialogue"
	agent = Agent.load(model_d, interpreter=RasaNLUInterpreter(model_u))

	if serve_forever: 
		# agent.handle_channel(ConsoleInputChannel())
		agent.handle_channel(HttpInputChannel(8080, "", SimpleWebChannel()))
	return agent


if __name__ == '__main__':
	logging.basicConfig(level="DEBUG")

	parser = argparse.ArgumentParser(description='bot')
	parser.add_argument(
			'task',
			choices=["train-nlu", "train-dialogue", "run"],
			help="o que o bot tem que fazer - e.g. run or train?")
	task = parser.parse_args().task

	# decide what to do based on first parameter of the script
	if task == "train-nlu":
		train_nlu()
	elif task == "train-dialogue":
		train_dialogue()
	elif task == "run":
		run()
	else:
		warnings.warn("Você precisa passar 'train-nlu', 'train-dialogue' ou "
					  "'run' pra inicializar o bot.")
		exit(1)
