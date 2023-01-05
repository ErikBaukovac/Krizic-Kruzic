import math
import time as t
import random as r
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from spade.message import Message
from spade import quit_spade

mreza = [['', '', ''], ['', '', ''], ['', '', '']]
igrac = ""
protivnik = ""
pametan = False

ocjene = {
    'X': 10,
    'O': -10,
    'Nerjeseno': 0
}


def PretvoriMrezu(temp):
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


def IzracunPoteza():

    global igrac
    najboljaOcjenaX = -math.inf
    najboljaOcjenaO = math.inf

    pokretI = 0
    pokretJ = 0

    for i in range(3):
        for j in range(3):

            if mreza[i][j] == '':
                mreza[i][j] = igrac

                if igrac == "X":
                    ocjena = MinMax(mreza, 0, False)
                    mreza[i][j] = ''

                    if ocjena > najboljaOcjenaX:
                        najboljaOcjenaX = ocjena
                        pokretI = i
                        pokretJ = j
                else:
                    ocjena = MinMax(mreza, 0, True)
                    mreza[i][j] = ''

                    if ocjena < najboljaOcjenaO:
                        najboljaOcjenaO = ocjena
                        pokretI = i
                        pokretJ = j

    mreza[pokretI][pokretJ] = igrac


def MinMax(mreza, dubinaRekurzije, maksimiziraDobit):

    rezultat = ProvjeraPobjednika()

    if rezultat is not None:
        return ocjene[rezultat]

    if maksimiziraDobit:
        najboljaOcjena = -math.inf

        for i in range(3):
            for j in range(3):

                if mreza[i][j] == '':
                    mreza[i][j] = 'X'
                    ocjena = MinMax(mreza, dubinaRekurzije + 1, False)
                    mreza[i][j] = ''
                    najboljaOcjena = max(ocjena, najboljaOcjena)

        return najboljaOcjena

    else:
        najboljaOcjena = math.inf

        for i in range(3):
            for j in range(3):

                if mreza[i][j] == '':
                    mreza[i][j] = 'O'
                    ocjena = MinMax(mreza, dubinaRekurzije + 1, True)
                    mreza[i][j] = ''
                    najboljaOcjena = min(ocjena, najboljaOcjena)

        return najboljaOcjena


def GlupiPotez():
    odigrano = False

    while odigrano == False:

        ri = r.randint(0, 2)
        rj = r.randint(0, 2)

        if mreza[ri][rj] == '':
            mreza[ri][rj] = igrac
            odigrano = True


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


class AgentTwo(Agent):

    class KrizicKruzicIgrac(FSMBehaviour):

        async def on_start(self):
            print("Zapocinjem ponašanje!")

        async def on_end(self):
            print("Završavam ponašanje!")
            await self.agent.stop()

    class Prijava(State):
        async def run(self):

            msg = Message(
                to="agent@localhost",
                body="agentTwo@localhost",
                metadata={
                    "intent": "Prijava"})
            await self.send(msg)

            self.set_next_state("Postavke")

    class Postavke(State):
        async def run(self):

            global igrac
            global protivnik

            msg = await self.receive(timeout=60)

            if (msg.get_metadata("intent") == "Poredak" and msg.body == "Igras"):

                print("Ti si X igrac")
                igrac = "X"
                protivnik = "O"

                temp = msg.get_metadata("mreza")

                PretvoriMrezu(temp)

                broj = r.randint(0, 4)
                if broj == 0:
                    mreza[0][0] = 'X'
                elif broj == 1:
                    mreza[2][0] = 'X'
                elif broj == 2:
                    mreza[0][2] = 'X'
                else:
                    mreza[2][2] = 'X'

                msg = Message(
                    to="agent@localhost",
                    body="Potez",
                    metadata={
                        "intent": "Potez",
                        "mreza": str(mreza)})
                await self.send(msg)

                self.set_next_state("Cekaj")

            elif (msg.get_metadata("intent") == "Poredak" and msg.body == "Neigras"):

                print("Ti si O igrac")
                igrac = "O"
                protivnik = "X"
                self.set_next_state("Cekaj")

            else:
                self.set_next_state("Postavke")

    class Cekaj(State):
        async def run(self):

            msg = await self.receive(timeout=60)

            if (msg.get_metadata("intent") == "Nastavak"):

                temp = msg.get_metadata("mreza")
                PretvoriMrezu(temp)
                self.set_next_state("Igraj")

            elif (msg.get_metadata("intent") == "Kraj"):

                if (msg.get_metadata("pobjednik") == igrac):
                    print("WOHOOOO!!!!")
                    self.set_next_state("Ugasi")

                elif(msg.get_metadata("pobjednik") == protivnik):
                    print("OH NEEEEEEE :'(")
                    self.set_next_state("Ugasi")
                    
                else:
                    print("Dobra igra!")
                    self.set_next_state("Ugasi")

            else:
                self.set_next_state("Cekaj")

    class Igraj(State):
        async def run(self):

            if pametan == True:
                IzracunPoteza()
            else:
                GlupiPotez()

            msg = Message(
                to="agent@localhost",
                body="Potez",
                metadata={
                    "intent": "Potez",
                    "mreza": str(mreza)})
            await self.send(msg)

            self.set_next_state("Cekaj")

    class Ugasi(State):
        async def run(self):
            print("Bilo mi je drago igrati :D")

    async def setup(self):

        fsm = self.KrizicKruzicIgrac()

        fsm.add_state(name="Prijava", state=self.Prijava(), initial=True)
        fsm.add_state(name="Postavke", state=self.Postavke())
        fsm.add_state(name="Cekaj", state=self.Cekaj())
        fsm.add_state(name="Igraj", state=self.Igraj())
        fsm.add_state(name="Ugasi", state=self.Ugasi())

        fsm.add_transition(source="Prijava", dest="Postavke")
        fsm.add_transition(source="Postavke", dest="Cekaj")
        fsm.add_transition(source="Cekaj", dest="Igraj")
        fsm.add_transition(source="Cekaj", dest="Cekaj")
        fsm.add_transition(source="Igraj", dest="Cekaj")
        fsm.add_transition(source="Cekaj", dest="Ugasi")

        self.add_behaviour(fsm)


if __name__ == '__main__':

    if input("Zna li agent razmišljati? (Y/N)") == 'N':
        pametan = False
    else:
        pametan = True

    agent = AgentTwo("agentTwo@localhost", "agenttwo")
    agentRunning = agent.start()
    agentRunning.result()

    while agent.is_alive():
        try:
            t.sleep(1)
        except KeyboardInterrupt:
            print("Zatvaram program...")
            break

    agent.stop()

    quit_spade()
