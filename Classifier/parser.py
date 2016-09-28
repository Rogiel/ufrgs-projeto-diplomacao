import sys

from s2protocol.mpyq import mpyq
from s2protocol import protocol15405

import build_order
import game_data
import utils

def parse(replay_file, truncate=True):
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

    playerIndex = 1
    for player in details['m_playerList']:
        # bos[playerIndex] = build_order.BuildOrder(player['m_race'])
        players[playerIndex] = {
            'Name': player['m_name'],
            'BuildOrder': build_order.BuildOrder(player['m_race']),
            'Race': player['m_race']
        }
        bos[playerIndex] = players[playerIndex]['BuildOrder']
        bos[playerIndex].worker_kills = 0
        playerIndex += 1

    gameLoopOffset = 0

    contents = archive.read_file('replay.tracker.events')
    for event in protocol.decode_replay_tracker_events(contents):
        eventName = event['_event']

        gameLoop = event['_gameloop']
        if truncate and utils.convert_gameloops_to_seconds(gameLoop) > 6 * 60:
            break

        if eventName == 'NNet.Replay.Tracker.SPlayerStatsEvent':
            playerID = event['m_playerId']
            stats[playerID] = event

        if eventName == 'NNet.Replay.Tracker.SUnitBornEvent' or eventName == 'NNet.Replay.Tracker.SUnitInitEvent' or eventName == 'NNet.Replay.Tracker.SUpgradeEvent':
            if eventName != 'NNet.Replay.Tracker.SUpgradeEvent':
                unitTags[event['m_unitTagIndex']] = event

            if gameLoop == 0:
                continue
            if gameLoopOffset == 0:
                gameLoopOffset = gameLoop
            gameLoop = gameLoop - gameLoopOffset
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

            valid_units = game_data.races[buildOrder.race]
            if unit not in valid_units:
                continue

            buildOrder.add_action(utils.convert_gameloops_to_seconds(gameLoop), build_order.BuildUnitAction(playerStats['m_stats'], unit))

        # if eventName == 'NNet.Replay.Tracker.SUpgradeEvent':
        #     print event
        #     exit()

        # if truncate and eventName == 'NNet.Replay.Tracker.SUnitDiedEvent':
        #     if event['m_unitTagIndex'] not in unitTags:
        #         continue
        #     killedUnit = unitTags[event['m_unitTagIndex']]
        #
        #     playerID = killedUnit['m_upkeepPlayerId']
        #     unit = killedUnit['m_unitTypeName']
        #     if playerID not in bos:
        #         continue
        #     buildOrder = bos[playerID]
        #     valid_units = game_data.races[buildOrder.race]
        #
        #     if unit in game_data.workers:
        #         continue
        #     if unit not in valid_units:
        #         continue
        #     if unit in game_data.ignore_killed:
        #         continue
        #
        #     buildOrder.worker_kills += 1
        #     if buildOrder.worker_kills < 15:
        #         continue
        #
        #     break

    return players
