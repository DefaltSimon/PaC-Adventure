# coding=utf-8
from pac import PaCInterpreter

pac = PaCInterpreter(
    name="Down the Street",
    desc="Save game demo",
    autosave=True  # FYI: defaults to true anyway
)


room1 = pac.createRoom(
    name="street",
    desc="I can see a dim light at the end of the street.",
    starting=True

)

room2 = pac.createRoom(
    name="front wall of library",
    desc="I'm standing in the front of a library.",

)

room3 = pac.createRoom(
    name="inside library",
    desc="I'm inside the library, where everything is silent. What happened?",

)

pac.linkroom(room1, room2, True)
pac.linkroom(room2, room3, True)

pac.setStartingMessage("Save-game demo\n--------------\nType 'save' to save the current game. (autosave is done every 4 actions.")

pac.start()