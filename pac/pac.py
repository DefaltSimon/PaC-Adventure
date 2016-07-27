# coding=utf-8

# This is the PaC Interpreter

# Imports
from pygame import mixer
import threading
import time
import os

__author__ = "DefaltSimon"
__version__ = "0.3.1"

# Constants
PICKUP = "pickup"
USE_ITEM = "use-item"
USE_OBJECT = "use-object"
COMBINE = "combine"
START = "start"
ENTER = "enter"
MUSIC_CHANGE = "music"


# For simple threading

def threaded(fn):
    def wrapper(*args, **kwargs):
        threading.Thread(target=fn, args=args, kwargs=kwargs).start()
    return wrapper

# Exception classes


class MissingParameters(Exception):
    """
    Thrown when some parameters are missing.
    """
    def __init__(self, *args, **kwargs):
        pass


class InvalidParameters(Exception):
    """
    To be expected when an invalid variable type was passed.
    """
    def __init__(self, *args, **kwargs):
        pass


class NotLinked(Exception):
    """
    Thrown when a room you tried to enter is not liked to the current room.
    """
    def __init__(self, *args, **kwargs):
        pass


class AlreadyExists(Exception):
    """
    Raised when an Item or Room with the same name already exist.
    """
    def __init__(self, *args, **kwargs):
        pass

# Music player
class Music:
    """
    Represents the Music that is played when entering a room or interacting with an object.
    """
    def __init__(self, path):
        """
        Inits the Music.
        :param path: path to file
        :return: None
        """
        if not os.path.isfile(path):
            print("[ERROR] {} is not a file or does not exist!".format(path))

        self.path = str(path)
        self._keepalive = threading.Event()
        self.isstarted = False

    def start(self, repeat=True):
        """
        Starts playing the music (threading is now not needed).
        :param repeat: optional, defaults to True; specifies if the sound file should be repeatedly played.
        :return: None
        """
        if repeat:
            mixer.music.load(self.path)
            mixer.music.play(-1)
        else:
            mixer.music.load(self.path)
            mixer.music.play()

        time.sleep(0.1)


    def stop(self):
        """
        Sets a flag (Event) to True so the thread quits on next iteration (max time for next iteration: 0.1 s)
        :return: None
        """
        mixer.music.fadeout(500)  # Quits the thread when Event is set to True
        return

# Room Object


class Room(object):
    """
    Represents a room that the player can move into and interact with its objects, etc...
    """
    def __init__(self, name, desc, enterdesc=None, starting=False):
        self.name = str(name)

        self.desc = str(desc)
        self.onfirstenterdesc = enterdesc

        self.isdefault = bool(starting)
        self.firstenter = False

        self.items = {}
        self.itemdescs = {}

        self.statics = {}
        self.staticdescs = {}

        self.requirements = {
            "items" : [],
            "visited" : [],
        }
        self.music = None

    def description(self):
        """
        :return: Room description string
        """
        return self.desc

    def putitem(self, item, description):
        """
        Puts an Item into the room.
        :param item: Item object to put in the room
        :param description: string to display when the item is in the room.
        :return: None
        """

        if not isinstance(item, Item):
            raise InvalidParameters

        self.items[item.name] = item

        self.itemdescs[item.name] = str(description)

    def putstatic(self, obj, description):
        """
        Places a StaticObject into the room.
        :param obj: StaticObject object to place into the room
        :param description: string to display when the object is in the room
        :return: None
        """
        if not isinstance(obj, StaticObject):
            raise InvalidParameters

        self.statics[obj.name] = obj

        self.staticdescs[obj.name] = str(description)

    def enter(self):
        """
        :return: Room description, includes 'first enter description' if it is the first time entering the room. Also includes any items found in the room.
        """

        # Build item descriptions if they exists (if there are any items in the room)
        if self.itemdescs:
            itms = "\n" + " ".join(self.itemdescs.values())
        else:
            itms = ""

        # Builds static objects descrptions if they exist in the room
        if self.staticdescs:
            statics = " " + " ".join(self.staticdescs.values())
        else:
            statics = ""

        if not self.firstenter:
            self.firstenter = True

            if self.onfirstenterdesc:
                return str(self.onfirstenterdesc + statics + "\n" + self.desc + itms)
            else:
                return self.desc + statics + itms

        else:
            return self.desc + statics + itms

    def getItems(self):
        """
        :return: A list of items in the room
        """
        return list(self.items.values())

    def getStatics(self):
        """
        :return: A list of static objects in the room
        """
        return list(self.statics.values())

    def useItem(self, item):
        """
        :param item: Item object to use
        :return: Item onuse string
        """
        # Converts string to Item if needed
        if isinstance(item, Item):
            pass

        else:
            item = self.items[item]

        desc = item.use()
        self.items.pop(item.name)
        self.itemdescs.pop(item.name)

        return desc

    def pickUpItem(self, item):
        """
        :param item: Item object or string (item name)
        :return: Item onpickup string
        """
        # Converts string to Item if needed and checks if the item exists in the room
        if isinstance(item, Item):
            try:
                it = self.items[item.name]
                del it
            except KeyError:
                return False

        else:
            try:
                item = self.items[item.name]
            except KeyError:
                return False

        desc = item.pickUp()
        self.items.pop(item.name)

        return desc

    def addVisitRequirement(self, room, ondenymessage):
        """
        Adds a room visit requirement to the room.
        :param room: Room object or room name
        :param ondenymessage: string
        :return: None
        """
        if not isinstance(room, Room):
            raise InvalidParameters

        else:
            self.requirements["visited"].append((room, ondenymessage))  # Tuple

    def addItemRequirement(self, item, ondenymessage):
        """
        Adds an item requirement to the room.
        :param item: Item object
        :param ondenymessage: Message to be printed when not trying to enter the room and not having the item.
        :return: None
        """
        if not isinstance(item, Item):
            raise InvalidParameters

        self.requirements["items"].append((item, ondenymessage))  # Tuple

    def hasVisitRequirement(self, visitedrooms):
        """
        Indicates if the room has all room visit requirements.
        :param visitedrooms: A list of Room objects that the player has visited
        :return: 1 if has all requirements, str of required messages joined with \n otherwise.
        """
        if not isinstance(visitedrooms, list):
            raise InvalidParameters


        # Build room list
        rms = []
        for this in self.requirements["visited"]:
            rms.append(this[0])

        for element in rms:
            if element not in visitedrooms:

                places = []
                for item in self.requirements["visited"]:
                    places.append(item[1])

                return "\n".join(places)

        return 1

    def hasItemRequirements(self, items):
        """
        Indicates if the room has all Item requirements.
        :param items: A list of Item objects (in the player's inventory)
        :return: 1 if has all requirements, str of required messages joined with \n otherwise.
        """
        if not isinstance(items, list):
            raise InvalidParameters

        nit = self.requirements["items"]

        for el in nit:
            if el[0] not in items:

                ls = []
                for item in nit:
                    ls.append(item[1])

                return "\n".join(ls)

        return 1

    def addMusic(self, music):
        """
        Adds a Music object that will start playing when the player enters.
        :param music: path or Music
        :return: None
        """

        if not isinstance(music, Music):
            raise InvalidParameters

        self.music = music

# Item in the room or inventory


class Item(object):
    """
    An item that the player can pick up, use, combine, etc.
    """
    def __init__(self, name, desc, onuse, faileduse, failedpickup, onpickup=None, craftable=False, craftingdesc=None):
        self.name = str(name)
        self.desc = str(desc)

        self.used = False
        self.pickedup = False
        self.crafted = False

        self.onuse = str(onuse)
        self.onpickup = onpickup

        self.craftable = bool(craftable)
        self.crafttingdesc = craftingdesc

        self.onfaileduse = faileduse
        self.onfailedpickup = failedpickup

        self.pickuprequires = []
        self.userequires = []

    def description(self):
        """
        :return: Item description string
        """
        return self.desc

    def wasused(self):
        """
        :return: A bool indicating if the Item has been used.
        """
        return bool(self.used)

    def use(self):
        """
        "Uses" the item, settings its used property to True.
        :return: Item onuse string
        """
        # Must use hasUseRequirements!
        self.used = True

        return self.onuse

    def pickUp(self):
        """
        "Picks up" the item
        :return: Item onpickup string
        """
        # Must use hasPickUpRequirements!
        self.pickedup = True

        return self.onpickup

    def craft(self):
        if not self.craftable:
            return False

        else:
            self.crafted = True
            return self.crafttingdesc

    def hasPickUpRequirements(self, items):
        """
        Checks if you have the proper items to pick up this one.
        :param items: A list of Item objects (usually your inventory)
        :return: Bool indicating the result
        """
        if isinstance(items, list):
            hasitems = True

            for item in self.pickuprequires:
                try:
                    items.index(item)
                except ValueError:
                    hasitems = False

            return bool(hasitems)

    def hasUseRequirements(self, items):
        """
        Checks if you have the proper items to use this one.
        :param items: A list of Item objects (usually your inventory)
        :return: Bool indicating the result
        """
        if isinstance(items, list):
            hasitems = True

            for item in self.userequires:
                try:
                    items.index(item)
                except ValueError:
                    hasitems = False

            return bool(hasitems)

    def addPickUpRequirement(self, item):
        """
        Adds a pick up requirement for this item.
        :param item: Item object
        :return: None
        """
        if not isinstance(item, Item):
            raise InvalidParameters

        self.pickuprequires.append(item)

    def addUseRequirement(self, item):
        """
        Adds a use requirement for this item.
        :param item: Item object
        :return: None
        """
        if not isinstance(item, Item):
            raise InvalidParameters

        self.userequires.append(item)

class StaticObject(object):
    def __init__(self, name, display, onuse, faileduse):
        self.name = str(name)
        self.display = str(display)

        self.onuse = str(onuse)

        self.used = False

        self.onfaileduse = faileduse

        self.itemrequirements = []

        self.itemblueprints = {}

        self.music = None

    def wasused(self):
        """
        :return: Bool indicating if the StaticObject was used.
        """
        return bool(self.used)

    def use(self):
        """
        :return: onuse string
        """
        return self.onuse

    def useWithItem(self, item):
        """
        Uses the Item on the StaticObject if a blueprint for it exists
        :param item: Item
        :return: Description defined with addItemBlueprint
        """
        if not isinstance(item, Item):
            raise InvalidParameters

        if item.name in self.itemblueprints:
            return self.itemblueprints[item.name]

        else:
            return False


    def takeNotice(self):
        """
        Don't mind the name.
        :return: display string
        """
        return self.display

    def hasItemRequirements(self, items):
        """
        Checks if you have the proper items to pick up this one.
        :param items: A list of Item objects (usually your inventory)
        :return: Bool indicating the result
        """
        if isinstance(items, list):
            hasitems = True

            for item in self.itemrequirements:
                try:
                    items.index(item)
                except ValueError:
                    hasitems = False

            return bool(hasitems)

        else:
            return False

    def addItemRequirement(self, item):
        """
        Adds a pick up requirement for this item.
        :param item: Item object
        :return: None
        """
        if not isinstance(item, Item):
            raise InvalidParameters

        self.itemrequirements.append(item)

    def addItemBlueprint(self, item, descrption):
        """
        Add the Item to the list of usable items for this StaticObject.
        :param item: Item object
        :param descrption: string to display when using this item on this static object
        :return: None
        """
        if not isinstance(item, Item):
            raise InvalidParameters

        self.itemblueprints[item.name] = str(descrption)

    def addMusic(self, music):
        """
        Adds a Music object that will start playing when the player enters.
        :param music: path or Music
        :return: None
        """

        if not isinstance(music, Music):
            raise InvalidParameters

        self.music = music


class EventDispatcher:
        # todo docstrings
        def __init__(self):
            self.events = {
                "pickup" : [],
                "use-item" : [],
                "use-object" : [],
                "start" : [],
                "combine" : [],
                "enter" : [],
                "music": []
            }

        def _registerEvent(self, type, fn):
            if type == PICKUP:
                self.events.get(PICKUP).append(fn)

            elif type == USE_ITEM:
                self.events.get(USE_ITEM).append(fn)

            elif type == USE_OBJECT:
                self.events.get(USE_OBJECT).append(fn)

            elif type == START:
                self.events.get(START).append(fn)

            elif type == COMBINE:
                self.events.get(COMBINE).append(fn)

            elif type == ENTER:
                self.events.get(ENTER).append(fn)

            elif type == MUSIC_CHANGE:
                self.events.get(MUSIC_CHANGE).append(fn)

        def _dispatchEvent(self, type, data=None):
            for fn in self.events.get(type):

                if not data:
                    fn()

                else:
                    fn(data)

        # @decorators for fast event registering
        def ENTER(self, fn):
            self._registerEvent(ENTER, fn)
            return fn

        def PICKUP(self, fn):
            self._registerEvent(PICKUP, fn)
            return fn

        def USE_ITEM(self, fn):
            self._registerEvent(USE_ITEM, fn)
            return fn

        def USE_OBJECT(self, fn):
            self._registerEvent(USE_OBJECT, fn)
            return fn

        def COMBINE(self, fn):
            self._registerEvent(COMBINE, fn)
            return fn

        def START(self, fn):
            self._registerEvent(START, fn)
            return fn

        def MUSIC_CHANGE(self, fn):
            self._registerEvent(MUSIC_CHANGE, fn)
            return fn

# TextInterface handles player interaction

class TextInterface:
    """
    The basic Text interface that the player interacts with.
    """
    def __init__(self):
        self.running = True

    def beginAdventure(self, pac):
        """
        Prints the starting message and begins the while True loop, starting user interaction : the game.
        :param pac: PaCInterpreter created by user
        :return: None
        """
        def getRoomHeader(room):
            if isinstance(room, Room):
                room = room.name

            else:
                room = str(room)

            wys = ", ".join(pac.ways())

            totallen = 65  # Total length of the header
            ti = int( (totallen-len(room)) / 2)
            ti2 = int( (totallen-len(wys)) / 2)

            hd = ("-" * ti) + room + ("-" * ti) + "\n" + "You can go to: " + wys + "\n" # Header

            return hd


        def textadventure():
            inp = str(input(">"))

            if inp == "help" or inp == "what to do":
                commands = ["go", "pick up", "use", "inv", "where", "combine", "exit"]
                print(", ".join(commands))

            # Displays possible ways out of the room (DEPRECATED!)
            elif inp.startswith(("ways", "path", "paths", "way")):
                print("You can go to: " + ", ".join(pac.ways()))

            # Gives you a list of items in the room (DEPRECATED!)
            elif inp.startswith(("items", "objects", "items in the room", "what items are in the room")):
                objects = pac.getCurrentRoom().getItems()

                objs = []
                for obj in objects:
                    # Just for the correct grammar jk
                    if str(obj.name).startswith(("a", "e", "i", "o", "u")):
                        um = "an"
                    else:
                        um = "a"

                    objs.append(str(um + " " + obj.name))


                # Correct prints
                if len(objs) == 0:
                    print("There are no items here.")

                elif len(objs) == 1:

                    print("In the room there is " + objs[0])

                else:
                    print("In the room there are " + ", ".join(objs))

            # Moves the player back to the previous room.
            elif inp.startswith("go back"):

                try:
                    insert = str(pac.roombeforethisone.name)  # Stores room before calling goback() method where the room gets changed
                except AttributeError:
                    return

                try:
                    desc = pac.goback()
                except NotImplementedError:
                    return
                except NotLinked:
                    return


                if not isinstance(desc, list):
                    print(getRoomHeader(pac.currentroom))
                    print(desc)

                else:
                    print(desc[0])

            # Moves the player to a different room
            elif inp.startswith(("walk ", "go ", "go to ", "walk to ", "walk down ", "go down")):
                # Properly cuts the string
                if inp.startswith("walk down"):
                    rn = inp[len("walk down "):]

                elif inp.startswith("walk "):
                    rn = inp[len("walk "):]

                elif inp.startswith("go to"):
                    rn = inp[len("go to "):]

                elif inp.startswith("go down"):
                    rn = inp[len("go down "):]

                elif inp.startswith("go "):
                    rn = inp[len("go "):]

                elif inp.startswith("walk to"):
                    rn = inp[len("walk to "):]

                else:
                    rn = None


                if not rn:
                    print("Where do you want to go?")
                    return

                # Resolves a/an/the
                if rn.startswith("a "):
                    rn = rn[len("a "):]

                elif rn.startswith("an "):
                    rn = rn[len("an "):]

                elif rn.startswith("the "):
                    rn = rn[len("the "):]

                # Walks and prints
                try:
                    desc = pac.walk(str(rn))
                except NotImplementedError:
                    return
                except NotLinked:
                    return


                if not isinstance(desc, list):
                    print(getRoomHeader(pac.currentroom))
                    print(desc)

                else:
                    print(desc[0])

            # Picks up the item in the room and puts it into your inventory
            elif inp.startswith("pick up"):
                on = inp[len("pick up "):]

                if not on:
                    print("What do you want to pick up?")

                # Resolves a/an/the
                if on.startswith("a "):
                    on = on[len("a "):]

                elif on.startswith("an "):
                    on = on[len("an "):]

                elif on.startswith("the "):
                    on = on[len("the "):]


                onuse = pac.pickUpItem(on)
                if not onuse:
                    pass

                else:
                    print(onuse)

            # Uses the item in your inventory
            elif inp.startswith("use"):
                on = inp[len("use "):]

                if not on:
                    print("What?")

                # Resolves a/an/the
                if on.startswith("a "):
                    on = on[len("a "):]

                elif on.startswith("an "):
                    on = on[len("an "):]

                elif on.startswith("the "):
                    on = on[len("the "):]

                try:
                    desc = pac.useItem(pac.getItemByName(on))

                except NotImplementedError:
                    spl = on.split(" with ")

                    if len(spl) == 1:
                        spl = on.split(" on ")

                        if len(spl) == 1:
                            print("What do you want to use?")
                            return

                    try:
                        desc = pac.useStaticObject(pac.getStaticObjectByName(spl[1]), pac.getItemByName(spl[0]))
                    except NotImplementedError:
                        return

                if not desc:
                    return

                print(desc)

            elif inp.startswith("combine"):
                # Finds the two Item objects
                sr = inp[len("combine "):]

                if not sr:
                    print("What do you want to combine?")
                    return

                # Does proper splitting with multiple keywords
                sr = sr.split("with")

                if len(sr) == 1:
                    sr = sr[0].split("and")

                if len(sr) == 1:
                    print("Use: combine item1 with item2...")
                    return

                try:
                    craftdesc = pac.combine(sr[0].strip(" "), sr[1].strip(" "))
                except NotImplementedError:
                    return

                if not craftdesc:
                    print(pac.dfailcombine)
                    return

                print(craftdesc)

            # Displays items in your inventory
            elif inp.startswith(("inventory", "inv")):
                # Converts items to a list of names
                items = []
                for it in pac.getInventory():

                    # Just for the correct grammar jk
                    if str(it.name).startswith(("a", "e", "i", "o", "u")):
                        um = "an"
                    else:
                        um = "a"

                    items.append(str(um + " " + it.name))

                # Correct prints
                if len(items) == 0:
                    print("You do not have anything in your inventory.")

                elif len(items) == 1:
                    print("You have " + items[0])

                elif len(items) == 2:
                    print("You have " + items[0] + " and " + items[1])

                else:
                    print("You have " + ", ".join(items))

            # Tells you what room you are currently in
            elif inp.startswith(("where am i", "where", "room")):
                print("You are in the " + str(pac.getCurrentRoom().name))

            # Option to quit game
            elif inp.startswith("exit"):
                n = input("Are you sure?")

                if str(n).lower().startswith(("yes", "yup", "ye", "sure", "y")):
                    print("Bye for now!")
                    self.running = False
                    return

                elif str(n).lower().startswith(("no", "nope", "n", "not sure")):
                    return


        # Prints the starting message and the usual for the starting room and then enters the 'infinite' loop.

        print(pac.startingmessage + "\n\n" + getRoomHeader(pac.startingroom.name) + "\n" + pac.startingroom.enter())

        while self.running:  # Defaults to True
            textadventure()

        # Code never reaches this point... probably (except when quitting)

# Main class
class PaCInterpreter:
    """
    The interpreter, linking together all objects and your code.
    PaC stands for point and click (adventure) ;)
    """

    def __init__(self, eventdispatcher=None):
        self.rooms = {}
        self.items = {}
        self.statics = {}
        self.blueprints = []

        self.inv = []

        self.visits = []
        self.links = {}

        self.currentroom = None
        self.roombeforethisone = None

        self.startingroom = None
        self.startingmessage = None

        self.running = False

        # Defaults (default pick up is defined in createItem)
        self.defaultuse = "Hmm..."
        self.defaultfaileduse = "Hmm..."
        self.defaultfailedpickup = "I can't do that."
        self.defaultfailedcombine = "Can't do that..."

        self.musicthread = None
        self.events = eventdispatcher

    def setEventDispatcher(self, eventdispatcher):
        """
        Associates the instance of EventDispatcher with PacInterpreter
        :param eventdispatcher: an instance of EventDispatcher (optional)
        :return: None
        """
        if not isinstance(eventdispatcher, EventDispatcher):
            raise InvalidParameters

        self.events = eventdispatcher

    def start(self):
        """
        Starts the adventure with you in the default room and the starting message. If you have not defined a starting room or message, MissingParameters will be raised.
        :return: None
        """
        self.running = True

        mixer.init()  # Inits the mixer module (for Music)

        if not self.events:
            self.events = EventDispatcher()

        self.events._dispatchEvent(START)

        if not self.startingroom or not self.startingmessage:
            raise MissingParameters

        self.currentroom = self.startingroom

        self.visits.append(self.currentroom)

        # Instances the TextInterface class (no need for it to be class-wide for now)
        textinterface = TextInterface()

        # If the starting room has music, start playing.
        if self.startingroom.music:
            self._startMusicThread(self.startingroom.music)

        # With this the TextInterface has the access to the class - the 'story'. Prints the starting message and begins the while True loop.
        textinterface.beginAdventure(self)

    def setDefaultUseFailMessage(self, message):
        """
        Sets the default message to return when not being able to use an item (when not overridden by Item specific fail message).
        :param message: string
        :return: None
        """
        self.defaultfaileduse = str(message)

    def setDefaultPickUpFailMessage(self, message):
        """
        Sets the default message to return when not being able to pick up an item (when not overridden by Item specific fail message).
        :param message: string
        :return: None
        """
        self.defaultfailedpickup = str(message)

    def setDefaultCombineFailMessage(self, message):
        """
        Sets the default message for when failed to combine.
        :param message: string
        :return: None
        """
        self.defaultfailedcombine = str(message)

    def setDefaultUseMessage(self, message):
        """
        Sets the default message for when using an item (when not overridden by item specific use message)
        :param message:
        :return:
        """
        self.defaultuse = str(message)

    def setStartingMessage(self, message):
        """
        Sets the starting message. Necessary before calling start().
        :param message: string
        :return: None
        """
        self.startingmessage = str(message)


    def getrooms(self):
        """
        Returns a dictionary of rooms created.
        {room name : Room object, ...}
        :return: dict of rooms
        """
        return self.rooms

    def getCurrentRoom(self):
        """
        Returns the current room.
        :return: Room object
        """
        if not self.currentroom:
            raise NotImplementedError

        return self.currentroom

    def getInventory(self):
        """
        Returns a list of Items in the players inventory.
        :return: list of Items
        """
        return list(self.inv)

    def getRoomByName(self, name):
        """
        Returns the Room by its name.
        :param name: room name string
        :return: Room object
        """
        return self.rooms[str(name)]

    def getItemByName(self, item):
        """
        Returns the Item by its name. Raises NotImplementedError if the item does not exist.
        :param item: item name string
        :return: Item object
        """
        try:
            return self.items[item]
        except KeyError:
            raise NotImplementedError

    def getStaticObjectByName(self, obj):
        """
        Returns the StaticObject by its name. Raises NotImplementedError if the item does not exist
        :param obj: object name string
        :return: StaticObject object
        """
        try:
            return self.statics[obj]
        except KeyError:
            raise NotImplementedError


    def createRoom(self, name, desc, onfirstenterdesc=None, starting=False):
        """
        Creates a Room with supplied properties.
        :param name: room name
        :param desc: room description
        :param onfirstenterdesc: descrption to be displayed when entering the room for the first time
        :param starting: bool indicating if the room should be the starting one
        :return: created Room object
        """
        if not name:
            raise MissingParameters

        if name in self.rooms:
            raise AlreadyExists

        room = Room(name, desc, onfirstenterdesc, starting)
        self.rooms[str(name)] = room

        if starting:
            self.startingroom = room

        return room

    def createItem(self, name, desc, onuse=None, faileduse=None, failedpickup=None, onpickup=None, craftable=False, craftingdesc=None):
        """
        Creates an Item with supplied properties. All parameters have to be strings. IF onuse is not supplied, the item is 'literally' unusable, printing "hmmm..." on use.
        :param name: item name
        :param desc: item description
        :param onuse: string to be displayed when using the item
        :param faileduse: string to be displayed when not being able to use the item
        :param failedpickup: string to be displayed when not being able to pick up the item
        :param onpickup: string to be displayed when picking up the item
        :return: created Item object
        """
        if not name or not desc:
            raise InvalidParameters

        if not onuse:
            onuse = self.defaultuse

        if not onpickup:
            onpickup = "You picked up {}".format(str(name))

        if not faileduse:
            faileduse = self.defaultfaileduse

        if not failedpickup:
            failedpickup = self.defaultfailedpickup

        if not craftingdesc:
            craftingdesc = "By combining you created a {}".format(str(name))

        obj = Item(name, desc, onuse, faileduse, failedpickup, onpickup, craftable, craftingdesc)

        # 'Registers' the object for getItemByName()
        self.items[obj.name] = obj
        return obj

    def createBlueprint(self, item1, item2, finalitem):
        """
        Creates a blueprint for combining two items together to make another item which also has to be the Item object. The order does not matter.
        :param item1: First Item object to combine
        :param item2: Second Item object to combine
        :param finalitem: Item object that will be the result
        :return: None
        """
        # Converts from str to Item objects if needed
        if not isinstance(item1, Item):
            item1 = self.getItemByName(item1)

        if not isinstance(item2, Item):
            item2 = self.getItemByName(item2)

        if not isinstance(finalitem, Item):
            finalitem = self.getItemByName(finalitem)

        # Done converting, now append the blueprint to self.blueprints in the form of tuple
        app = (item1, item2, finalitem)
        self.blueprints.append(app)

    def createStaticItem(self, name, display, onuse=None, faileduse=None):
        """
        Creates a StaticObject that can 'sit' in the room and be interacted with. It can not be picked up, but can be used with/without special items.
        :param name: object name
        :param display: string that will be displayed when the object is in the room
        :param onuse: string that will be displayed when using the object without special items.
        :param faileduse: displayed when not able to use the object
        :return: StaticObject object
        """
        if not name or not display:
            raise InvalidParameters

        if not onuse:
            onuse = self.defaultuse

        if not faileduse:
            faileduse = self.defaultfaileduse

        obj = StaticObject(name, display, onuse, faileduse)
        self.statics[name] = obj

        return obj

    def combine(self, itemone, itemtwo):
        """
        Combines two items together is there is a blueprint for the combination.
        :param itemone: Item object or item name
        :param itemtwo: Item object or item name
        :return: Combined item (Item)
        """
        # Converts to Item objects if needed
        if not isinstance(itemone, Item):
            itemone = self.getItemByName(itemone)

        if not isinstance(itemtwo, Item):
            itemtwo = self.getItemByName(itemtwo)

        # Checks existence in inventory
        if not ((itemone in self.inv) and (itemtwo in self.inv)):
            return False

        # Shifts through blueprints
        for c, blue in enumerate(self.blueprints):
            item1 = blue[0]
            item2 = blue[1]

            if (itemone == item1 and itemtwo == item2) or (itemone == item2 and itemtwo == item1):
                result = blue[2]
                self.inv.pop(c)
                self.inv.pop(c)

                self.putIntoInv(result)

                # Dispatch event
                self.events._dispatchEvent(COMBINE, {"item1": item1, "item2": item2, "result": result})

                return result.craft()

        return False


    def linkroom(self, room1, room2, twoway=False):
        """
        Links two rooms together (one-way or two-way).
        :param room1: Room to link from
        :param room2: Room to link to
        :param twoway: Defaults to False, indicates of the path should be two-way
        :return: None
        """
        if not isinstance(room1, Room) or not isinstance(room2, Room):
            raise InvalidParameters

        # First link
        try:
            self.links[room1.name].append(room2.name)

        except KeyError:
            self.links[room1.name] = []
            self.links[room1.name].append(room2.name)

        # Second link, if twoway is True
        if twoway:
            try:
                self.links[room2.name].append(room1.name)

            except KeyError:
                self.links[room2.name] = []
                self.links[room2.name].append(room1.name)

    @staticmethod
    def putitem(room, item, description):
        """
        Puts an item into a room.
        :param room: Room to put the Item into
        :param item: Item to put in the Room
        :param description: string to display when an item is in the room
        :return: None
        """
        if not isinstance(room, Room) or not isinstance(item, Item):
            raise InvalidParameters

        room.putitem(item, description)

    def putstaticobject(self, room, obj):
        """
        Puts a StaticObject into a room. (description is provided by StaticObject.display string)
        :param room: Room to put the StaticObject into
        :param obj: StaticObject to put in the Room
        :return: None
        """
        if not isinstance(room, Room) or not isinstance(obj, StaticObject):
            raise InvalidParameters

        room.putstatic(obj, obj.display)

    def putIntoInv(self, item):
        """
        Puts an Item into your inventory.
        :param item: Item to put
        :return: None
        """
        if not isinstance(item, Item):
            raise InvalidParameters

        self.inv.append(item)

    def pickUpItem(self, item):
        """
        Picks up the item in the current room.
        :param item:
        :return: False if failed, item onpickup string if successful.
        """
        # Converts string to Item if needed
        if not isinstance(item, Item):

            try:
                item = self.items[item]
            except KeyError:
                return False

        if not item == self.currentroom.items.get(item.name):
            return False

        if not item.hasPickUpRequirements(self.inv):
            if item.onfaileduse is not None:
                return str(item.onfailedpickup)
            else:
                return self.defaultfailedpickup

        it = self.currentroom.pickUpItem(item)
        self.events._dispatchEvent(PICKUP, {"item": item, "desc": it})

        thatitem = self.items[item.name]
        self.putIntoInv(thatitem)

        return it

    def useItem(self, item):
        """
        Uses an Item in your inventory
        :param item: Item to use
        :return: False if failed, Item onuse string is successful
        """
        if not isinstance(item, Item):
            raise InvalidParameters

        if item not in self.inv:
            return False

        else:
            if not item.hasUseRequirements(self.inv):

                if item.onfaileduse is not None:
                    return str(item.onfaileduse)
                else:
                    return self.defaultfaileduse

            desc = item.use()
            self.events._dispatchEvent(USE_ITEM, {"item": item, "desc": desc})
            return desc

    def useStaticObject(self, obj, item=None):
        """
        Uses the StaticObject in the room.
        :param obj: StaticObject
        :param item: Item to use with (optional)
        :return: StaticObject display string
        """
        if not isinstance(obj, StaticObject):
            raise InvalidParameters

        if obj not in self.currentroom.getStatics():
            return False

        else:
            if not obj.hasItemRequirements(self.inv):

                if obj.onfaileduse is not None:
                    return str(obj.onfaileduse)
                else:
                    return self.defaultfaileduse

            if not item:
                if obj.music:
                    self._startMusicThread(obj.music)
                desc = obj.use()
            else:
                if obj.music:
                    self._startMusicThread(obj.music)
                desc = obj.useWithItem(item)

            self.events._dispatchEvent(USE_OBJECT, {"object": obj, "desc": desc})
            return desc

    def walk(self, room):
        """
        Walks the user from the current room to the specified one.
        Raises NotImplementedError if the room does not exist and NotLinked if the room is not linked.
        :param room: Room to go to
        :return: Room onenter string if everything is okay, a list with one item in a string of not
        """
        # Gets the Room object
        if isinstance(room, Room):
            pass

        else:
            try:
                room = self.rooms[str(room)]
            except KeyError:
                raise NotImplementedError

        if room.music:
            if not self.musicthread == room.music:
                self._startMusicThread(room.music)

        try:
            if not room.name in self.links[self.currentroom.name]:
                raise NotLinked

        except KeyError:
            raise NotLinked

        except AttributeError:
            raise MissingParameters

        # Processes requirements
        itemr = room.hasItemRequirements(self.inv)
        roomr = room.hasVisitRequirement(self.visits)

        if itemr or roomr:
            self.events._dispatchEvent(ENTER, {"from": self.currentroom, "to": room, "first-time": not room.firstenter})

        if itemr == 1:
            if roomr == 1:  # Only if everything is fulfilled, return room description
                desc = room.enter()

                # Sets current room and the one you were just in
                self.roombeforethisone = self.currentroom
                self.currentroom = room

                self.visits.append(room)

                return desc

            else:  # Return room deny message
                return [roomr]

        else:  # Item is not correct, branch out

            if roomr == 1:  # If room requirements are okay, return only item deny message
                return [itemr]

            else:  # Both are not fulfilled, return str of both
                return [str(str(itemr) + "\n" + str(roomr))]

    def goback(self):
        """
        Moves the player back to the previous room.
        :return: Same as walk() method (Room onenter string if everything is okay, a list with one item in a string of not)
        """
        if not self.roombeforethisone:
            raise NotImplementedError

        return self.walk(self.roombeforethisone)

    def ways(self):
        """
        Returns a list of links (ways/paths) from the current room.
        :return - list of links
        """
        room = self.currentroom

        if not room or not isinstance(room, Room):
            raise MissingParameters

        try:
            return self.links[room.name]
        except KeyError:
            return []

    def addMusic(self, music, place):
        """
        Adds music to be played when entering a room or interacting with a StaticObject. Music does NOT stop playing when moving to a room without music!
        :param music: str or Music
        :param place: Room or StaticObject
        :return: None
        """
        if isinstance(music, str):
            music = Music(music)

        elif isinstance(music, Music):
            pass

        else:
            raise InvalidParameters

        if not (isinstance(place, Room) or isinstance(place, StaticObject)):
            raise InvalidParameters

        place.addMusic(music)

    @threaded
    def _startMusicThread(self, music, repeat=True):
        """
        Starts the music, stopping any existing threads.
        :param music: Music
        :return: None
        """
        if not isinstance(music, Music):
            raise InvalidParameters

        try:
            self.musicthread.stop()
        except AttributeError:
            pass

        self.musicthread = music
        self.lastmusicthread = music
        self.musicthread.__init__(self.musicthread.path)

        self.events._dispatchEvent(MUSIC_CHANGE, {"music": music, "path": music.path})
        self.musicthread.start(repeat)