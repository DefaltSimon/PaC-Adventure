# coding=utf-8
"""
This is an example of what can the interpreter do. Not everything is covered, but most for the 0.2 version is.

It all works like this:

Create rooms, items, static objects and link them together.
Add requirements, custom messages, blueprints, ...
and use start() method to start the "Adventure", the rest is left to the TextInterface
"""

# Interpreter import
from pac import PaCInterpreter

# Instance of the interpreter
pac = PaCInterpreter()

# Rooms
room1 = pac.createRoom(
                name="dining room",
                desc="This is where we eat everyday.",
                starting=True)

room2 = pac.createRoom(
                name="living room",
                desc="This is where we can sit and talk to each other together in peace.",
                onfirstenterdesc="Oh. The living room.")

room3 = pac.createRoom(
                name="outside",
                desc="In front of you there is a park, all covered in snow. You shiver. It's cold.",
                onfirstenterdesc="You step outside.")

room4 = pac.createRoom(
                name="park",
                desc="You have visited this park many times, yet now that it's snowing, it's even more beautiful.",
                onfirstenterdesc="You enter the park. It's a little bit darker, but that just adds to it's mysteriousness.")

room5 = pac.createRoom(
                name="street",
                desc="It's an empty street.\n\nYou have reached the end goal of this demo. It shows most of the capabilities of PaC Adventure Creator.\n- Thank you for playing this short demo, DefaltSimon",
                onfirstenterdesc="You enter the street. It's darker than where you just came from.")

# Items
item1 = pac.createItem(
                name="phone",
                desc="It's my phone. It's battery is at 5%. I must charge it.",
                onuse="I need to plug in the charger.",
                onpickup="You pick up the phone. Still need to charge it...",
                failedpickup="I need to find my charger first.",
                faileduse="I need a charger first.")

item2 = pac.createItem(
                name="charger",
                desc="It's my charger.",
                onuse="What am I supposed to do with this?",
                onpickup="You pick up the charger.",
                failedpickup="Um wat.",
                faileduse="What am I supposed to do with this?")


item3 = pac.createItem(
                name="charged phone",
                desc="It's my phone, charged.",
                onuse="It's my phone, charged.",
                onpickup=None,
                failedpickup=None,
                faileduse=None,
                craftable=True,
                craftingdesc="I charge my phone. It's now at 100%. Damn, this charger speed nowadays...")

item4 = pac.createItem(
                name="remote",
                desc="It's the remote for the TV")

# Static objects

static1 = pac.createStaticItem(
                name="television",
                display="A television sits in the far edge of the room.",
                onuse="You turn on the television, but there is nothing interesting playing at the moment.",
                faileduse="You can't turn on the TV.")


# Links, requirements, objects in rooms and starting inv

room5.addItemRequirement(item3, "I need to charge my phone before I embark.")  # room5 = street
room5.addVisitRequirement(room4, "I must visit the park first.")

# pac.addMusic("somemusic.wav", room2)  # winsound sadly supports only wav.
# Add your music!

#object1.addUseRequirement(object2)  # Commented out, but this pretty much means that you need to have that item (item2 - charger) before you can pick it up/use it (item1 - phone)
#object1.addPickUpRequirement(object2)

pac.setDefaultUseFailMessage("Hmmm.....")
pac.setDefaultPickUpFailMessage("I can't do that. Really.")
pac.setDefaultCombineFailMessage("Can't do that...")

#pac.putIntoInv(object1)  # Just to show that you can put items into inventory as well.


pac.createBlueprint(item1, item2, item3) # phone + charger = charged phone (item names can also be used as args)

pac.linkroom(room1, room2, True)  # True indicates that the path should be two-way

pac.linkroom(room2, room3, True)

pac.linkroom(room3, room4, True)

pac.linkroom(room3, room5, True)


pac.putitem(room1, item1, "There is a phone on the table.")  # You must also add a description that will be displayed when this item is in the room.
pac.putitem(room2, item2, "Your charger is in the half-open drawer.")
pac.putitem(room2, item4, "The remote is on the table.")

pac.putstaticobject(room2, static1)  # Description is not needed, it's the static objects display parameter
static1.addItemBlueprint(item4, "You use the remote to turn on the television.")

pac.setStartingMessage("'The Story of a Man' (demo)\n---------------------------\n\nYou are in the dining room. You can smell the scent of washed dishes.\nYour family is out for this evening.")

# Starts the game
pac.start()