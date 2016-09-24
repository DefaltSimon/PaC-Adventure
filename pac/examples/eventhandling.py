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
room1 = pac.create_room(
                name="bedroom",
                desc="This is where I sleep every night.",
                starting=True)

room2 = pac.create_room(
                name="hall",
                desc="I'm in the hall of my apartment.",
                starting=False)

pac.link_room(room1, room2, True)

# Items
item1 = pac.create_item(
                name="phone",
                desc="It's my phone. It's battery is at 5%. I must charge it.",
                on_use="I need to plug in the charger.",
                on_pickup="You pick up the phone. Still need to charge it...",
                failed_pickup="I need to find my charger first.",
                failed_use="I need a charger first.")

pac.set_default_use_fail_message("Hmmm.....")
pac.set_default_pick_up_fail_message("I can't do that. Really.")
pac.set_default_combine_fail_message("Can't do that...")


pac.put_item(room1, item1, "There is a phone on the desk.")

pac.set_starting_message("This example features event registering and handling.\nA custom message will be printed when you move from room to room.")


# PaC-Adventure also has an event handling module (implemented in 0.3)
events = EventDispatcher()

@events.START
def on_start():
    print("Game has started.")

@events.ENTER
def on_enter(**kwargs):
    print("Went from {} to {} (First time: {}).".format(kwargs.get("fr").name, kwargs.get("to").name, kwargs.get("first_time")))

# Available events: PICKUP, COMBINE, START, ENTER, USE_ITEM, USE_OBJECT, MUSIC_CHANGE
# events._registerEvent(START, onstart) # Events can also be registered this way, but above with decorators is much more intuitive

# Starts the game
pac.start()