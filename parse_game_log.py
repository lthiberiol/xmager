#!/usr/bin/env python2
#coding: utf-8

import os
import re
import copy

class log:

    def __init__(self):
        self.winning_player = []
        self.cards_in_decks = [set(),set()]

    def assess_log(self, log_file):
    #
    # create main structure to save mined data
        players = [dict(name='', land_drop=[], cast=[], starting_hand=7),
                   dict(name='', land_drop=[], cast=[], starting_hand=7)]

        with open(log_file) as handle:
            #
            # remove all HTML tags from log text
            txt = re.sub('<.*?>', '', handle.read())
            #
            # capture player names
            players[0]['name'], players[1]['name'] = re.findall('\d{2}:\d{2} [AP]M: (\S+)[\n\s]+has joined the game', txt)

            #
            # split log file into turns using timestamp of each turn
            turns = re.split('\d{2}:\d{2}\s[AP]M:\sTurn\s\d+\s+', txt)

            #
            # determine starting player ...
            if turns[1].startswith(players[0]['name']):
                on_play = 0
                on_draw = 1
            elif turns[1].startswith(players[1]['name']):
                on_play = 1
                on_draw = 0

            #
            # check, and count, number of mulligans...
            linearized = ' '.join(turns[0].split())
            players[0]['starting_hand'] -= len(re.findall('{player} decides to take mulligan'.format(player=players[0]['name']), linearized))
            players[1]['starting_hand'] -= len(re.findall('{player} decides to take mulligan'.format(player=players[1]['name']), linearized))

            #
            # ignore 1st list position, it is
            for turn in turns[1:]:
                #
                # determine turn's active player...
                if turn.startswith(players[0]['name']):
                    active_player = 0
                elif turn.startswith(players[1]['name']):
                    active_player = 1

                #
                # consider that all spells are cast at sorcery speed, let's start simple
                players[active_player]['cast'].append([])

                #
                # remove linebreaks to simplify regexes
                linearized = ' '.join(turn.split())

                #
                # assess land drop frequencies...
                land_drop_check = re.search('{player} puts ([^:]+?)(?:\s\[\S+?\])? from hand onto the Battlefield'.format(player=players[active_player]['name']),
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
                for player in players:
                    cast_check = re.findall('{player} casts ([^:]+?)\s\[\S+?\]'.format(player=player['name']),
                                            linearized)
                    if cast_check:
                        player['cast'][-1].extend(cast_check)

        #
        # check if player 1 name is stated as winner
        if   re.search('\d\d:\d\d [AP]M: {player} has won the game$'.format(player=players[0]['name']), linearized, re.M):
            winning_player = 0
        #
        # if not, check if player 2 name is stated as winner
        elif re.search('\d\d:\d\d [AP]M: {player} has won the game$'.format(player=players[1]['name']), linearized, re.M):
            winning_player = 1

        if winning_player in self.winning_player:
            self.winning_player = winning_player
        else:
            self.winning_player.append(winning_player)

        return players

    def compile_observed_cards(self, game_data):
        for i,j in zip(self.cards_in_decks, game_data):
            i.update(j['land_drop'], *j['cast'])

    def get_winning_player(self):
        if len(self.winning_player) == 1:
            return self.winning_player[0]
        else:
            return tuple(self.winning_player)