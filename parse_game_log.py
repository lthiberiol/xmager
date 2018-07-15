#!/usr/bin/env python2
#coding: utf-8

import re
from mtgsdk import Card
import os
import copy

class log:

    def __init__(self):
        self.winning_player = []
        self.cards_in_decks = {}

    def assess_log(self, log_file):
    #
    # create main structure to save mined data
        players = {}

        with open(log_file) as handle:
            #
            # remove all HTML tags from log text
            txt = re.sub('<.*?>', '', handle.read())
            #
            # capture player names
            for player_name in re.findall('\d{2}:\d{2} [AP]M: (\S+)[\n\s]+has joined the game', txt):
                players[player_name] = dict(land_drop=[], cast=[], starting_hand=7)

            #
            # split log file into turns using timestamp of each turn
            turns = re.split('\d{2}:\d{2}\s[AP]M:\sTurn\s\d+\s+', txt)

            #
            # determine starting player ...
            for player_name in players.keys():
                if turns[1].startswith(player_name):
                    players[player_name]['on play'] = True
                    break

            #
            # check, and count, number of mulligans...
            linearized = ' '.join(turns[0].split())
            for player_name in players.keys():
                players[player_name]['starting_hand'] -= len(re.findall('{player} decides to take mulligan'.format(player=player_name), linearized))

            #
            # ignore 1st list position, it is
            for turn in turns[1:]:
                #
                # determine turn's active player...
                active_player = turn.strip().split()[0]

                #
                # consider that all spells are cast at sorcery speed, let's start simple
                players[active_player]['cast'].append([])

                #
                # remove linebreaks to simplify regexes
                linearized = ' '.join(turn.split())

                #
                # assess land drop frequencies...
                land_drop_check = re.search('{player} puts ([^:]+?)(?:\s\[\S+?\])? from hand onto the Battlefield'.format(player=active_player),
                                            linearized)
                #
                # if land drop observed, specified land played
                if land_drop_check:
                    players[active_player]['land_drop'].append(land_drop_check.group(1))
                #
                # otherwise just add a zero...
                else:
                    players[active_player]['land_drop'].append(0)

                #
                # search for spells cast this turn
                for player_name in players:
                    cast_check = re.findall('{player} casts ([^:]+?)\s\[\S+?\]'.format(player=player_name),
                                            linearized)
                    if cast_check:
                        players[player_name]['cast'][-1].extend(cast_check)

        #
        # check if player 1 name is stated as winner
        for player_name in players:
            if re.search('\d\d:\d\d [AP]M: {player} has won the game'.format(player=player_name), linearized, re.M):
                winning_player = player_name

        if winning_player in self.winning_player:
            self.winning_player = winning_player
        else:
            self.winning_player.append(winning_player)

        for player_name in players:
            if player_name not in self.cards_in_decks:
                self.cards_in_decks[player_name] = set().union(players[player_name]['land_drop'], *players[player_name]['cast'])
            else:
                self.cards_in_decks[player_name].update(players[player_name]['land_drop'], *players[player_name]['cast'])

            if 0 in self.cards_in_decks[player_name]:
                self.cards_in_decks[player_name].remove(0)

        return players, winning_player

    def get_winning_player(self):
        if type(self.winning_player) is str:
            return self.winning_player
        else:
            return tuple(self.winning_player)

    def check_legalities(self, should_be_legal_in='modern'):
        for player_name, cards in self.cards_in_decks.items():
            for card in cards:
                legal_in = Card.where(name=card).all()[0]
                legal = False
                for legality in legal_in.legalities:
                    if legality['format'].lower() == should_be_legal_in.lower() and legality['legality'].lower() == 'legal':
                        legal = True

                if not legal:
                    break
            if not legal:
                break

        if not legal:
            return False
        return True
