import time as t
import random as r
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from spade.message import Message
from spade import quit_spade

mreza = [['', '', ''], ['', '', ''], ['', '', '']]
igraci = []
zadnjiIgrao = " "


def ProvjeraJednakosti(a, b, c):
    return a == b and b == c and a != ''


def ProvjeraPobjednika():

    pobjednik = None

    for i in range(3):
        if (ProvjeraJednakosti(mreza[i][0], mreza[i][1], mreza[i][2])):
            pobjednik = mreza[i][0]

    for i in range(3):
        if (ProvjeraJednakosti(mreza[0][i], mreza[1][i], mreza[2][i])):
            pobjednik = mreza[0][i]

    if (ProvjeraJednakosti(mreza[0][0], mreza[1][1], mreza[2][2])):
        pobjednik = mreza[0][0]

    if (ProvjeraJednakosti(mreza[2][0], mreza[1][1], mreza[0][2])):
        pobjednik = mreza[2][0]

    praznaMjesta = 0
    for i in range(3):
        for j in range(3):
            if (mreza[i][j] == ''):
                praznaMjesta += 1

    if (pobjednik == None and praznaMjesta == 0):
        return 'Nerjeseno'
    else:
        return pobjednik


def pretvoriMrezu(temp):
    temp = temp.replace("[", "")
    temp = temp.replace("]", "")
    temp = temp.replace("'", "")
    temp = temp.replace(" ", "")
    temp = temp.split(",")

    mreza[0][0] = temp[0]
    mreza[0][1] = temp[1]
    mreza[0][2] = temp[2]
    mreza[1][0] = temp[3]
    mreza[1][1] = temp[4]
    mreza[1][2] = temp[5]
    mreza[2][0] = temp[6]
    mreza[2][1] = temp[7]
    mreza[2][2] = temp[8]


def crtanje():
    print(' {:^3}  | {:^3}  | {:^3} '.format(
        mreza[0][0], mreza[0][1], mreza[0][2]))
    print('-------------------')
    print(' {:^3}  | {:^3}  | {:^3} '.format(
        mreza[1][0], mreza[1][1], mreza[1][2]))
    print('-------------------')
    print(' {:^3}  | {:^3}  | {:^3} \n\n'.format(
        mreza[2][0], mreza[2][1], mreza[2][2]))


class Master(Agent):

    class KrizicKruzic(FSMBehaviour):

        async def on_start(self):
            print("Pripremam igru!")

        async def on_end(self):
            print("Igra gotova!")
            await self.agent.stop()

    class Inicijalizacija(State):
        async def run(self):

            global zadnjiIgrao

            msg = await self.receive(timeout=60)

            if (msg.get_metadata("intent") == "Prijava"):
                msg = msg.body
                igraci.append(msg)

            if (len(igraci) == 2):

                if r.randint(0, 10) % 2:
                    zadnjiIgrao = "0"

                    msg = Message(
                        to=igraci[0],
                        body="Igras",
                        metadata={
                            "intent": "Poredak",
                            "mreza": str(mreza)})

                    await self.send(msg)

                    msg = Message(
                        to=igraci[1],
                        body="Neigras",
                        metadata={
                            "intent": "Poredak"})

                    await self.send(msg)

                    self.set_next_state("Zapocni")

                else:
                    zadnjiIgrao = "1"

                    msg = Message(
                        to=igraci[1],
                        body="Igras",
                        metadata={
                            "intent": "Poredak",
                            "mreza": str(mreza)})
                    await self.send(msg)

                    msg = Message(
                        to=igraci[0],
                        body="Neigras",
                        metadata={
                            "intent": "Poredak"})

                    await self.send(msg)
                    self.set_next_state("Zapocni")

            elif len(igraci) > 2:
                igraci.clear
                self.set_next_state("Inicijalizacija")

            else:
                self.set_next_state("Inicijalizacija")

    class Zapocni(State):

        async def run(self):
            print("Inicijaliziram ploču")
            crtanje()
            self.set_next_state("Obrada")

    class Obrada(State):
        async def run(self):

            msg = await self.receive(timeout=60)

            if (msg.get_metadata("intent") == "Potez"):

                temp = msg.get_metadata("mreza")
                pretvoriMrezu(temp)
                crtanje()

                pobjednik = ProvjeraPobjednika()

                if pobjednik is None:
                    self.set_next_state("NastavakIgre")
                else:
                    self.set_next_state("ZavrsiIgru")

            else:
                self.set_next_state("Obrada")

    class NastavakIgre(State):
        async def run(self):

            global zadnjiIgrao

            if zadnjiIgrao == "1":
                zadnjiIgrao = "0"

                msg = Message(
                    to=igraci[0],
                    body="Igras",
                    metadata={
                        "intent": "Nastavak",
                        "mreza": str(mreza)})
                await self.send(msg)

            else:
                zadnjiIgrao = "1"

                msg = Message(
                    to=igraci[1],
                    body="Igras",
                    metadata={
                        "intent": "Nastavak",
                        "mreza": str(mreza)})
                await self.send(msg)

            self.set_next_state("Obrada")

    class ZavrsiIgru(State):
        async def run(self):

            pobjednik = ProvjeraPobjednika()

            if pobjednik == "Nerjeseno":
                print("Rezultat je nerjesen")
            else:
                print("Pobjedio je {}".format(pobjednik))
                
            for igrac in igraci:
                msg = Message(
                    to=igrac,
                    body="Gotova igra!",
                    metadata={
                        "intent": "Kraj",
                        "pobjednik": pobjednik})
                await self.send(msg)


    async def setup(self):

        print("Inicijalizacija igre!")

        fsm = self.KrizicKruzic()

        fsm.add_state(name="Inicijalizacija",
                      state=self.Inicijalizacija(), initial=True)
        fsm.add_state(name="Zapocni", state=self.Zapocni())
        fsm.add_state(name="Obrada", state=self.Obrada())
        fsm.add_state(name="NastavakIgre", state=self.NastavakIgre())
        fsm.add_state(name="ZavrsiIgru", state=self.ZavrsiIgru())

        fsm.add_transition(source="Inicijalizacija", dest="Inicijalizacija")
        fsm.add_transition(source="Inicijalizacija", dest="Zapocni")
        fsm.add_transition(source="Zapocni", dest="Obrada")
        fsm.add_transition(source="Obrada", dest="Obrada")
        fsm.add_transition(source="Obrada", dest="NastavakIgre")
        fsm.add_transition(source="NastavakIgre", dest="Obrada")
        fsm.add_transition(source="Obrada", dest="ZavrsiIgru")

        self.add_behaviour(fsm)


if __name__ == '__main__':

    master = Master("agent@localhost", "tajna")
    masterRunning = master.start()
    masterRunning.result()

    while master.is_alive():
        try:
            t.sleep(1)
        except KeyboardInterrupt:
            print("Prisilno gasenje!")
            break

    master.stop()

    quit_spade()
