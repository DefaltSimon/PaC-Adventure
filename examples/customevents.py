# coding=utf-8
"""
For more examples with explanations, take a look at the other example(s).
This one focuses on inserting your code into events that happen in the game.
"""

# Interpreter import
from pac import PaCInterpreter

import threading
import time

# Instance of the interpreter
pac = PaCInterpreter()

# Rooms
room1 = pac.createRoom(
                name="bedroom",
                desc="This is where I sleep every night.",
                starting=True)

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

# Starts the game in a thread, effectively not blocking your code
thr = threading.Thread(target=pac.start).start()

#
# HERE GOES YOUR CODE!
#   \/ \/ \/ \/ \/

# Demonstrates some possibilities
while True:

    if item1.pickedup:  # Waits until the phone gets picked up
        print(time.time())
        break
    else:
        time.sleep(0.1)