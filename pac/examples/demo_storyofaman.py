# coding=utf-8
"""
This is an example of what can the interpreter do. Not everything is covered, but most for the 0.4.1 version is.

It all works like this:

Create rooms, items, static objects and link them together.
Add requirements, custom messages, blueprints, music ...
register events,
and use start() method to start the "Adventure", the rest is left to the TextInterface

For more advanced examples see eventhandling.py
"""

# Interpreter import
from pac import PaCInterpreter


# Instance of the interpreter with name and description (only the name is required)
pac = PaCInterpreter(
    name="Story of a Man",
    desc="Engine demo",
    version="0.3"
)

# Rooms
room1 = pac.create_room(
                name="dining room",
                desc="This is where we eat everyday.",
                starting=True)

room2 = pac.create_room(
                name="living room",
                desc="This is where we can sit and talk to each other together in peace.",
                on_first_enter="Oh. The living room.")

room3 = pac.create_room(
                name="outside",
                desc="In front of you there is a park, all covered in snow. You shiver. It's cold.",
                on_first_enter="You step outside.")

room4 = pac.create_room(
                name="park",
                desc="You have visited this park many times, yet now that it's snowing, it's even more beautiful.",
                on_first_enter="You enter the park. It's a little bit darker, but that just adds to it's mysteriousness.")

room5 = pac.create_room(
                name="street",
                desc="It's an empty street.\n\nYou have reached the end goal of this demo. It shows most of the capabilities of PaC Adventure Creator.\n- Thank you for playing this short demo, DefaltSimon",
                on_first_enter="You enter the street. It's darker than where you just came from.")

# Items
item1 = pac.create_item(
                name="phone",
                desc="It's my phone. It's battery is at 5%. I must charge it.",
                on_use="I need to plug in the charger.",
                on_pickup="You pick up the phone. Still need to charge it...",
                failed_pickup="I need to find my charger first.",
                failed_use="I need a charger first.")

item2 = pac.create_item(
                name="charger",
                desc="It's my charger.",
                on_use="What am I supposed to do with this?",
                on_pickup="You pick up the charger.",
                failed_pickup="Um wat.",
                failed_use="What am I supposed to do with this?")


item3 = pac.create_item(
                name="charged phone",
                desc="It's my phone, charged.",
                on_use="It's my phone, charged.",
                on_pickup=None,
                failed_pickup=None,
                failed_use=None,
                is_craftable=True,
                crafting_desc="I charge my phone. It's now at 100%. Damn, this charger speed nowadays...")

item4 = pac.create_item(
                name="remote",
                desc="It's the remote for the TV")

# Static objects

static1 = pac.create_static_item(
                name="television",
                display="A television sits in the far edge of the room.",
                on_use="You turn on the television, but there is nothing interesting playing at the moment.",
                failed_use="You can't turn on the TV.")


# Links, requirements, objects in rooms and starting inv

room5.add_item_requirement(item3, "I need to charge my phone before I embark.")  # room5 = street
room5.add_visit_requirement(room4, "I must visit the park first.")

# Add your music!

# pac.add_music("DemoMusic2.wav", room3)  # Supported file formats: mp3, ogg, wav, mid

# pac.add_music("DemoMusic.wav", room2)  # Music can be added to either Room or StaticObject objects

#object1.addUseRequirement(object2)  # Commented out, but this pretty much means that you need to have that item (item2 - charger) before you can pick it up/use it (item1 - phone)
#object1.addPickUpRequirement(object2)

pac.set_default_use_fail_message("Hmmm.....")
pac.set_default_pick_up_fail_message("I can't do that. Really.")
pac.set_default_combine_fail_message("Can't do that...")

#pac.putIntoInv(object1)  # Just to show that you can put items into inventory as well.


pac.create_blueprint(item1, item2, item3) # phone + charger = charged phone (item names can also be used as args)


pac.link_room(room1, room2, two_way=True)  # True indicates that the path should be two-way

pac.link_room(room2, room3, True)

pac.link_room(room3, room4, True)

pac.link_room(room3, room5, True)


pac.put_item(room1, item1, "There is a phone on the table.")  # You must also add a description that will be displayed when this item is in the room.
pac.put_item(room2, item2, "Your charger is in the half-open drawer.")
pac.put_item(room2, item4, "The remote is on the table.")

pac.put_static_item(room2, static1)  # Description is not needed, it's the static objects display parameter
static1.add_item_blueprint(item4, "You turn on the television with the remote.")

pac.set_starting_message("'The Story of a Man' (demo)\n---------------------------\n\nYou are in the dining room. You can smell the scent of washed dishes.\nYour family is out for this evening.")

# Starts the game (blocking call)
pac.start()