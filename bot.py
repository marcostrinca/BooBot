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
from rasa_core.interpreter import RasaNLUInterpreter
from rasa_core.policies.keras_policy import KerasPolicy
from rasa_core.policies.memoization import MemoizationPolicy

logger = logging.getLogger(__name__)

import pymysql.cursors

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
        val_field = tracker.get_slot("field")

        # checo se tenho URL
        if val_url is not None:

            b_id = 0;

            with connection.cursor() as cursor:
                # SQL 
                sql = "INSERT INTO bookmarks (url, fk_user_id) values (%s, %s)"
                cursor.execute(sql, (val_url, 1))
                connection.commit()

                #armazeno o id deste insert
                b_id = cursor.lastrowid

                # checo se tenho tags
                if val_field is not None:
                    # SQL 
                    sql = "INSERT INTO tags (tag) values (%s)"
                    cursor.execute(sql, (val_field))
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
            description = "hmm, eu não vejo nenhuma URL pra salvar"

        dispatcher.utter_message(description)
        return []

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
        
        with connection.cursor() as cursor:
              
            # SQL 
            sql = "SELECT * FROM bookmarks"
            
            # Execute query.
            cursor.execute(sql)
            for row in cursor:
                print ("row: ", row['url'])
        
        dispatcher.utter_message("isso foi o que eu achei")
        return []

class MyCustomPolicy(KerasPolicy):
    def model_architecture(self, num_features, num_actions, max_history_len):
        """Build a Keras model and return a compiled model."""
        from keras.layers import LSTM, Activation, Masking, Dense
        from keras.models import Sequential

        n_hidden = 80  # size of hidden layer in LSTM
        # Build Model
        batch_shape = (None, max_history_len, num_features)

        model = Sequential()
        model.add(Masking(-1, batch_input_shape=batch_shape))
        model.add(LSTM(n_hidden, batch_input_shape=batch_shape))
        model.add(Dense(input_dim=n_hidden, output_dim=num_actions))
        model.add(Activation('softmax'))

        model.compile(loss='categorical_crossentropy',
                      optimizer='adam',
                      metrics=['accuracy'])

        logger.debug(model.summary())
        return model


def train_dialogue(domain_file="domain.yml",
                   model_path="models/dialogue",
                   training_data_file="data/stories.md"):
    # agent = Agent(domain_file, policies=[MemoizationPolicy()])
    agent = Agent(domain_file, policies=[MemoizationPolicy(), MyCustomPolicy()])

    agent.train(
            training_data_file,
            max_history=12,
            epochs=100,
            batch_size=60,
            augmentation_factor=30,
            validation_split=0.2
    )

    agent.persist(model_path)
    return agent


def train_nlu():
    from rasa_nlu.converters import load_data
    from rasa_nlu.config import RasaNLUConfig
    from rasa_nlu.model import Trainer

    training_data = load_data('data/nlu.md')
    trainer = Trainer(RasaNLUConfig("nlu_model_config.json"))
    trainer.train(training_data)
    model_directory = trainer.persist('models/nlu/', fixed_model_name="current")

    return model_directory


def run(serve_forever=True):
    agent = Agent.load("models/dialogue",
                       interpreter=RasaNLUInterpreter("models/nlu/default/current"))

    if serve_forever:
        agent.handle_channel(ConsoleInputChannel())
    return agent


if __name__ == '__main__':
    logging.basicConfig(level="INFO")

    parser = argparse.ArgumentParser(
            description='acordando o bot')

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
