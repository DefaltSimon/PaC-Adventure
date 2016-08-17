# coding=utf-8
"""
For simpler examples with explanations, take a look at the other example(s) or demos.
This one focuses on inserting your code into events that happen in the game.
"""

# Interpreter import
from pac import PaCInterpreter, EventDispatcher


# Instance of the interpreter
pac = PaCInterpreter(
    name="Event Handling demo"
)

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

pac.setStartingMessage("This example features event registering and handling.\nA custom message will be printed when you move from room to room.")


# PaC-Adventure also has an event handling module (implemented in 0.3)
events = EventDispatcher()

@events.START
def onstart():
    print("Game has started.")

@events.ENTER
def onenter(**kwargs):
    print("Went from {} to {} (First time: {}).".format(kwargs.get("fr").name, kwargs.get("to").name, kwargs.get("first_time")))

# Available events: PICKUP, COMBINE, START, ENTER, USE_ITEM, USE_OBJECT, MUSIC_CHANGE
# events._registerEvent(START, onstart) # Events can also be registered this way, but above with decorators is much more intuitive

# Starts the game
pac.start()