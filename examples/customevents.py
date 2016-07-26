# coding=utf-8
"""
For simpler examples with explanations, take a look at the other example(s) or demos.
This one focuses on inserting your code into events that happen in the game.
"""

# Interpreter import
from pac import PaCInterpreter, EventDispatcher
from pac import PICKUP, COMBINE, START, ENTER, USE_ITEM, USE_OBJECT, MUSIC_CHANGE  # All available events (for now)

# Instance of the interpreter
pac = PaCInterpreter()

# Rooms
room1 = pac.createRoom(
                name="bedroom",
                desc="This is where I sleep every night.",
                starting=True)

room2 = pac.createRoom(
                name="hall",
                desc="I'm in the hall of my apartment.",
                starting=False)

pac.linkroom(room1, room2, True)

# Items
item1 = pac.createItem(
                name="phone",
                desc="It's my phone. It's battery is at 5%. I must charge it.",
                onuse="I need to plug in the charger.",
                onpickup="You pick up the phone. Still need to charge it...",
                failedpickup="I need to find my charger first.",
                faileduse="I need a charger first.")

pac.setDefaultUseFailMessage("Hmmm.....")
pac.setDefaultPickUpFailMessage("I can't do that. Really.")
pac.setDefaultCombineFailMessage("Can't do that...")


pac.putitem(room1, item1, "There is a phone on the desk.")

pac.setStartingMessage("Custom event handling demo. When you pick up the phone, It will print the current time.\nUsing this, you can insert your code to some extent.")


# PaC-Adventure also has an event handling module (implemented in 0.3)
events = EventDispatcher()

def onstart():
    print("Game has started.")

def onenter(data):
    print("Went from {} to {} (First time: {}).".format(data.get("from").name, data.get("to").name, data.get("first-time")))

events.registerEvent(START, onstart)
events.registerEvent(ENTER, onenter)
# etc...

pac.setEventDispatcher(events)  # Needs to be done before start() method.

# Starts the game
pac.start()