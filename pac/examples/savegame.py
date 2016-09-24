# coding=utf-8
from pac import PaCInterpreter

pac = PaCInterpreter(
    name="Down the Street",
    desc="Save game demo",
    autosave=True  # FYI: defaults to true anyway
)


room1 = pac.create_room(
    name="street",
    desc="I can see a dim light at the end of the street.",
    starting=True

)

room2 = pac.create_room(
    name="front wall of library",
    desc="I'm standing in the front of a library.",

)

room3 = pac.create_room(
    name="inside library",
    desc="I'm inside the library, where everything is silent. What happened?",

)

pac.link_room(room1, room2, True)
pac.link_room(room2, room3, True)

pac.set_starting_message("Save-game demo\n--------------\nType 'save' to save the current game. (autosave is done every 5 actions, but can be turned off")

pac.start()