import asyncio
import random

import spade
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State

# States

# Logic states
START = "START"
NEXT_ENEMY = "NEXT_ENEMY"
# Combat states
PLAYER_TURN = "PLAYER_TURN"
ENEMY_TURN = "ENEMY_TURN"
CHECK_RESULT = "CHECK_RESULT"
# How the game ends
VICTORY = "VICTORY"
DEFEAT = "DEFEAT"
END = "END"

# States

# Start -> Combat -> Combat -> Shop -> Combat -> Rest -> Boss

class RPGAgent(Agent):
    def __init__(self, jid,password):
        super().__init__(jid,password)

        #Player stats
        self.hero_hp = 100
        self.hero_atk = 10
        self.hero_def = 2
        # Enemy related
        self.enemyArray = []
        self.currentEnemy = None
        self.enemiesDefeated = 0

        self.turn = 0
        self.totalTurns = 0
    async def setup(self):
        fsm = GameFSM()

        fsm.add_state(name=START, state=StartState(), initial=True)
        fsm.add_state(name=NEXT_ENEMY, state=NextEnemyState())
        fsm.add_state(name=PLAYER_TURN, state=PlayerTurnState())
        fsm.add_state(name=ENEMY_TURN, state=EnemyTurnState())
        fsm.add_state(name=CHECK_RESULT, state=CheckResultState())
        fsm.add_state(name=VICTORY, state=VictoryState())
        fsm.add_state(name=DEFEAT, state=DefeatState())
        fsm.add_state(name=END, state=EndState())


        fsm.add_transition(source=START, dest=NEXT_ENEMY)
        fsm.add_transition(source=NEXT_ENEMY, dest=PLAYER_TURN)
        fsm.add_transition(source=PLAYER_TURN, dest=ENEMY_TURN)
        fsm.add_transition(source=PLAYER_TURN, dest=CHECK_RESULT)
        fsm.add_transition(source=ENEMY_TURN, dest=CHECK_RESULT)
        fsm.add_transition(source=CHECK_RESULT, dest=PLAYER_TURN)
        fsm.add_transition(source=CHECK_RESULT, dest=NEXT_ENEMY)
        fsm.add_transition(source=CHECK_RESULT, dest=VICTORY)
        fsm.add_transition(source=CHECK_RESULT, dest=DEFEAT)
        fsm.add_transition(source=VICTORY, dest=END)
        fsm.add_transition(source=DEFEAT, dest=END)

        self.add_behaviour(fsm)

class GameFSM(FSMBehaviour):
    async def on_start(self):
        print("=== The adventure begins ===")

    async def on_end(self):
        # Runs after the final state (END) finishes. Stopping the agent here
        # is what lets wait_until_finished() in main() return, so the program exits.
        print("=== Game over ===")
        await self.agent.stop()



class Enemy:
    def __init__(self, name,hp,atk,defe):
        self.name = name
        self.hp = hp
        self.atk = atk
        self.defe = defe

class StartState(State):
    async def run(self):
        a = self.agent

        goblin = Enemy("Goblin", 15,2,1)
        spider = Enemy("Spider", 10,2,0)
        kobold = Enemy("Kobold",20,3,2)
        rat = Enemy("Rat",5,1,0)
        dragon = Enemy("Dragon", 50,5,5)

        a.enemyArray += [goblin,spider,kobold,rat,dragon]

        self.set_next_state(NEXT_ENEMY)

class NextEnemyState(State):
    async def run(self):
        a = self.agent
        a.currentEnemy = a.enemyArray[0]
        a.enemyArray.pop(0)
        print(f"A wild {a.currentEnemy.name} appears with {a.currentEnemy.hp} HP!")

        self.set_next_state(PLAYER_TURN)

class PlayerTurnState(State):
    async def run(self):
        a = self.agent
        a.turn += 1
        a.totalTurns += 1

        print(f"\n--- Turn {a.turn} --- (Hero HP: {a.hero_hp:.1f}, {a.currentEnemy.name} HP: {a.currentEnemy.hp:.1f})\n\n [1] ATTACK \n\n Enter your choice: ")

        choice = input()
        if choice == "1":
            damage = round(a.hero_atk * random.uniform(0.85,1.2),1)
            trueDamage = damage - a.currentEnemy.defe
            a.currentEnemy.hp -= trueDamage
            print(f"The hero attacks for {damage} damage and dealt {trueDamage:.1f}.")
        else:
            print("Don't")



        # If that attack killed the enemy, skip the enemy's turn.
        if a.currentEnemy.hp <= 0:
            a.enemiesDefeated += 1
            self.set_next_state(CHECK_RESULT)
        else:
            self.set_next_state(ENEMY_TURN)

class EnemyTurnState(State):
    async def run(self):

        a = self.agent
        await asyncio.sleep(1)
        if random.random() < 0.10:
            print(f"The {a.currentEnemy.name} misses!")
        else:
            damage = round(a.currentEnemy.atk * random.uniform(0.75,1.1),1)
            trueDamage = max(1,damage - a.hero_def)
            a.hero_hp -= trueDamage
            print(f"The {a.currentEnemy.name} hits for {damage} damage and dealt {trueDamage:.1f} damage.")
        self.set_next_state(CHECK_RESULT)

class CheckResultState(State):
    async def run(self):
        a = self.agent

        if a.hero_hp <= 0:
            self.set_next_state(DEFEAT)
        elif a.currentEnemy.hp <= 0 and a.enemiesDefeated == 5:
            self.set_next_state(VICTORY)
        elif a.currentEnemy.hp <= 0:
            a.turn = 0
            self.set_next_state(NEXT_ENEMY)
        else:
            self.set_next_state(PLAYER_TURN)

class VictoryState(State):
    async def run(self):
        print(f"\nVICTORY! You have defeated all the enemies!")
        self.set_next_state(END)


class DefeatState(State):
    async def run(self):
        print("\nDEFEAT... the hero has fallen.")
        self.set_next_state(END)

class EndState(State):
    async def run(self):
        print(f"The fight lasted {self.agent.totalTurns} turns.")

async def main():
    hero = RPGAgent("hero@localhost", "123")
    await hero.start()
    # Keeps the program alive until the agent stops itself in on_end().
    await spade.wait_until_finished(hero)


if __name__ == "__main__":
    spade.run(main(), embedded_xmpp_server=True)

