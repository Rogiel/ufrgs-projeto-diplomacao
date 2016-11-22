import sys

from s2protocol.mpyq import mpyq
from s2protocol import protocol15405

import build_order
import game_data
import utils

def parse(replay_file, truncate=True, lastedTime=False):
    archive = mpyq.MPQArchive(replay_file)

    # Read the protocol header, this can be read with any protocol
    contents = archive.header['user_data_header']['content']
    header = protocol15405.decode_replay_header(contents)

    # The header's baseBuild determines which protocol to use
    baseBuild = header['m_version']['m_baseBuild']
    try:
        protocol = __import__('s2protocol.protocol%s' % (baseBuild,), fromlist=['s2protocol'])
    except:
        print >> sys.stderr, 'Unsupported base build: %d' % baseBuild
        sys.exit(1)

    bos = dict()
    stats = dict()
    players = dict()

    contents = archive.read_file('replay.details')
    details = protocol.decode_replay_details(contents)

    unitTags = dict()
    userIdMap = dict()

    playerIndex = 1
    for player in details['m_playerList']:
        # bos[playerIndex] = build_order.BuildOrder(player['m_race'])
        players[playerIndex] = {
            'Name': player['m_name'],
            'BuildOrder': build_order.BuildOrder(player['m_race']),
            'Race': player['m_race'],
            'SurvivedUntil': 0.0
        }
        bos[playerIndex] = players[playerIndex]['BuildOrder']
        bos[playerIndex].worker_kills = 0
        if player['m_result'] == 1:
            players[playerIndex]['Win'] = True
        else:
            players[playerIndex]['Win'] = False
        playerIndex += 1

    gameLoopOffset = 0

    contents = archive.read_file('replay.tracker.events')
    for event in protocol.decode_replay_tracker_events(contents):
        eventName = event['_event']

        gameLoop = event['_gameloop']
        if 'm_playerId' in event:
            players[event['m_playerId']]['SurvivedUntil'] = utils.convert_gameloops_to_seconds(gameLoop)
        if truncate and utils.convert_gameloops_to_seconds(gameLoop) > 6 * 60:
            continue

        if eventName == 'NNet.Replay.Tracker.SPlayerSetupEvent':
            playerID = event['m_playerId']
            userId = event['m_userId']
            userIdMap[userId] = playerID

        if eventName == 'NNet.Replay.Tracker.SPlayerStatsEvent':
            playerID = event['m_playerId']
            stats[playerID] = event

            if gameLoopOffset == 0:
                gameLoopOffset = gameLoop
            gameLoop = gameLoop - gameLoopOffset

        if eventName == 'NNet.Replay.Tracker.SUnitBornEvent' or eventName == 'NNet.Replay.Tracker.SUnitInitEvent' or eventName == 'NNet.Replay.Tracker.SUpgradeEvent':
            if eventName != 'NNet.Replay.Tracker.SUpgradeEvent':
                unitTags[event['m_unitTagIndex']] = event

            if gameLoop == 0:
                continue
            # exit()

            if eventName == 'NNet.Replay.Tracker.SUpgradeEvent':
                unit = event['m_upgradeTypeName']
                playerID = event['m_playerId']
            else:
                unit = event['m_unitTypeName']
                playerID = event['m_upkeepPlayerId']

            if playerID not in stats:
                continue
            playerStats = stats[playerID]
            buildOrder = bos[playerID]

            if buildOrder.race not in game_data.races:
                continue

            valid_units = game_data.races[buildOrder.race]
            if unit not in valid_units:
                continue

            buildOrder.add_action(utils.convert_gameloops_to_seconds(gameLoop), build_order.BuildUnitAction(playerStats['m_stats'], unit))

    # if lastedTime is True:
    #     contents = archive.read_file('replay.game.events')
    #     for event in protocol.decode_replay_game_events(contents):
    #         eventName = event['_event']
    #         if eventName == 'NNet.Game.SGameUserLeaveEvent':
    #             if not event['_userid']['m_userId'] in userIdMap:
    #                 continue
    #
    #             gameLoop = event['_gameloop']
    #             eventPlayerID = userIdMap[event['_userid']['m_userId']]
    #             for (playerID, player) in players.iteritems():
    #                 if player['SurvivedUntil'] == 0:
    #                     player['SurvivedUntil'] = utils.convert_gameloops_to_seconds(gameLoop)
    #
    #             # print bos[event['_userid']['m_userId']]['Name']
    #             # exit()

    return players
