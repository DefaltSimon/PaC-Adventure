# coding=utf-8

# This is the PaC Interpreter
import logging
import pickle
import threading
import time
import os
import textwrap

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# Imports
try:
    from pygame import mixer
except ImportError:
    mixer = None
    logging.warn("pygame is not installed, music will NOT work.")

__author__ = "DefaltSimon"
__version__ = "0.4.1dev"

# Constants
PICKUP = "pickup"
USE_ITEM = "use-item"
USE_OBJECT = "use-object"
COMBINE = "combine"
START = "start"
ENTER = "enter"
MUSIC_CHANGE = "music"

# Total length of the room name header
PADDING = 65

# For simple threading


def threaded(fn):
    def wrapper(*args, **kwargs):
        threading.Thread(target=fn, args=args, kwargs=kwargs).start()
    return wrapper


def update_textwrap():
    global tw
    tw = textwrap.TextWrapper(width=PADDING, break_long_words=False, replace_whitespace=False)

update_textwrap()


def wraptext(s):
    if tw.width != PADDING:
        update_textwrap()

    print(textwrap.fill(s, PADDING))


def get_wrap(s):
    if tw.width != PADDING:
        update_textwrap()

    return textwrap.fill(s, PADDING)


def save(fn):
    fn.__self__.save.save(fn.__self__.currentroom, fn.__self__.roombeforethisone, fn.__self__.inv)
    return fn

# Exception classes


class InterpreterException(Exception):
    """
    General exception class, other exceptions are subclassed to this.
    """
    pass


class MissingParameters(InterpreterException):
    """
    Thrown when some parameters are missing.
    """
    pass


class InvalidParameters(InterpreterException):
    """
    To be expected when an invalid variable type was passed.
    """
    pass


class NotLinked(InterpreterException):
    """
    Thrown when a room you tried to enter is not liked to the current room.
    """
    pass


class AlreadyExists(InterpreterException):
    """
    Raised when an Item or Room with the same name already exist.
    """
    pass

# Singleton class


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


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
        if not mixer:
            return

        if not os.path.isfile(path):
            print("[ERROR] {} is not a file or does not exist!".format(path))

        self.path = str(path)
        # self._keep_alive = threading.Event()
        self.is_started = False

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

    @staticmethod
    def stop():
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
    def __init__(self, name, desc, enter_description=None, starting=False):
        self.name = str(name)

        self.desc = str(desc)
        self.on_first_enter = enter_description

        self.is_default = bool(starting)
        self.entered = False

        self.items = {}
        self.item_descriptions = {}

        self.statics = {}
        self.static_obj_descriptions = {}

        self.requirements = {
            "items": [],
            "visited": [],
        }
        self.music = None

    def description(self):
        """
        :return: Room description string
        """
        return self.desc

    def put_item(self, item, description):
        """
        Puts an Item into the room.
        :param item: Item object to put in the room
        :param description: string to display when the item is in the room.
        :return: None
        """

        if not isinstance(item, Item):
            raise InvalidParameters

        self.items[item.name] = item

        self.item_descriptions[item.name] = str(description)

    def put_static_obj(self, obj, description):
        """
        Places a StaticObject into the room.
        :param obj: StaticObject object to place into the room
        :param description: string to display when the object is in the room
        :return: None
        """
        if not isinstance(obj, StaticObject):
            raise InvalidParameters

        self.statics[obj.name] = obj

        self.static_obj_descriptions[obj.name] = str(description)

    def enter(self):
        """
        :return: Room description, includes 'first enter description' if it is the first time entering the room. Also includes any items found in the room.
        """

        # Build item descriptions if they exists (if there are any items in the room)
        items = ("\n" if self.item_descriptions.values() else "") + "\n".join(self.item_descriptions.values())

        # Builds static objects descriptions if they exist in the room
        statics = (" " if self.static_obj_descriptions.values() else "") + " ".join(self.static_obj_descriptions.values())

        if not self.entered:
            self.entered = True

            if self.on_first_enter:
                return str(self.on_first_enter + statics + "\n" + self.desc + items)
            else:
                return self.desc + statics + items

        else:
            return self.desc + statics + items

    def get_items(self):
        """
        :return: A list of items in the room
        """
        return list(self.items.values())

    def get_static_items(self):
        """
        :return: A list of static objects in the room
        """
        return list(self.statics.values())

    def use_item(self, item):
        """
        :param item: Item object to use
        :return: Item on_use string
        """
        # Converts string to Item if needed
        if isinstance(item, Item):
            pass

        else:
            item = self.items[item]

        desc = item.use()
        self.items.pop(item.name)
        self.item_descriptions.pop(item.name)

        return desc

    def pick_up_item(self, item):
        """
        :param item: Item object or string (item name)
        :return: Item on_pickup string
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

        desc = item.pick_up()
        self.items.pop(item.name)
        self.item_descriptions.pop(item.name)

        return desc

    def add_visit_requirement(self, room, on_deny):
        """
        Adds a room visit requirement to the room.
        :param room: Room object or room name
        :param on_deny: string
        :return: None
        """
        if not isinstance(room, Room):
            raise InvalidParameters

        else:
            self.requirements["visited"].append((room, on_deny))  # Tuple

    def add_item_requirement(self, item, on_deny):
        """
        Adds an item requirement to the room.
        :param item: Item object
        :param on_deny: Message to be printed when not trying to enter the room and not having the item.
        :return: None
        """
        if not isinstance(item, Item):
            raise InvalidParameters

        self.requirements["items"].append((item, on_deny))  # Tuple

    def has_visit_requirement(self, visited_rooms):
        """
        Indicates if the room has all room visit requirements.
        :param visited_rooms: A list of Room objects that the player has visited
        :return: 1 if has all requirements, str of required messages joined with \n otherwise.
        """
        if not isinstance(visited_rooms, list):
            raise InvalidParameters

        # Build room list
        rms = [this[0] for this in self.requirements.get("visited")]

        for element in rms:
            if element not in visited_rooms:

                places = []
                for item in self.requirements["visited"]:
                    places.append(item[1])

                return "\n".join(places)

        return 1

    def has_item_requirements(self, items):
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

    def add_music(self, music):
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
    def __init__(self, name, desc, on_use, on_failed_use, on_failed_pickup, on_pickup=None, is_craftable=False, crafting_description=None):
        self.name = str(name)
        self.desc = str(desc)

        self.used = False
        self.picked_up = False
        self.crafted = False

        self.on_use = str(on_use)
        self.on_pickup = on_pickup

        self.is_craftable = bool(is_craftable)
        self.crafting_description = crafting_description

        self.on_failed_use = on_failed_use
        self.on_failed_pickup = on_failed_pickup

        self.pickup_requires = []
        self.use_requires = []

    def description(self):
        """
        :return: Item description string
        """
        return self.desc

    def was_used(self):
        """
        :return: A bool indicating if the Item has been used.
        """
        return bool(self.used)

    def use(self):
        """
        "Uses" the item, settings its used property to True.
        :return: Item on_use string
        """
        # Must use hasUseRequirements!
        self.used = True

        return self.on_use

    def pick_up(self):
        """
        "Picks up" the item
        :return: Item on_pickup string
        """
        # Must use hasPickUpRequirements!
        self.picked_up = True

        return self.on_pickup

    def craft(self):
        if not self.is_craftable:
            return False

        else:
            self.crafted = True
            return self.crafting_description

    def has_pick_up_requirements(self, items):
        """
        Checks if you have the proper items to pick up this one.
        :param items: A list of Item objects (usually your inventory)
        :return: Bool indicating the result
        """
        if isinstance(items, list):
            has_items = True

            for item in self.pickup_requires:
                try:
                    items.index(item)
                except ValueError:
                    has_items = False

            return bool(has_items)

    def has_use_requirements(self, items):
        """
        Checks if you have the proper items to use this one.
        :param items: A list of Item objects (usually your inventory)
        :return: Bool indicating the result
        """
        if isinstance(items, list):
            has_items = True

            for item in self.use_requires:
                try:
                    items.index(item)
                except ValueError:
                    has_items = False

            return bool(has_items)

    def add_pick_up_requirement(self, item):
        """
        Adds a pick up requirement for this item.
        :param item: Item object
        :return: None
        """
        if not isinstance(item, Item):
            raise InvalidParameters

        self.pickup_requires.append(item)

    def add_use_requirement(self, item):
        """
        Adds a use requirement for this item.
        :param item: Item object
        :return: None
        """
        if not isinstance(item, Item):
            raise InvalidParameters

        self.use_requires.append(item)


class StaticObject(object):
    def __init__(self, name, display, on_use, on_failed_use):
        self.name = str(name)
        self.display = str(display)

        self.on_use = str(on_use)
        self.used = False

        self.on_failed_use = on_failed_use

        self.item_requirements = []
        self.item_blueprints = {}

        self.music = None

    def was_used(self):
        """
        :return: Bool indicating if the StaticObject was used.
        """
        return bool(self.used)

    def use(self):
        """
        :return: on_use string
        """
        return self.on_use

    def use_with_item(self, item):
        """
        Uses the Item on the StaticObject if a blueprint for it exists
        :param item: Item
        :return: Description defined with addItemBlueprint
        """
        if not isinstance(item, Item):
            raise InvalidParameters

        if item.name in self.item_blueprints:
            return self.item_blueprints[item.name]

        else:
            return False

    def take_notice(self):
        """
        Don't mind the name.
        :return: display string
        """
        return self.display

    def has_item_requirements(self, items):
        """
        Checks if you have the proper items to pick up this one.
        :param items: A list of Item objects (usually your inventory)
        :return: Bool indicating the result
        """
        if isinstance(items, list):
            has_items = True

            for item in self.item_requirements:
                try:
                    items.index(item)
                except ValueError:
                    has_items = False

            return bool(has_items)

        else:
            return False

    def add_item_requirement(self, item):
        """
        Adds a pick up requirement for this item.
        :param item: Item object
        :return: None
        """
        if not isinstance(item, Item):
            raise InvalidParameters

        self.item_requirements.append(item)

    def add_item_blueprint(self, item, description):
        """
        Add the Item to the list of usable items for this StaticObject.
        :param item: Item object
        :param description: string to display when using this item on this static object
        :return: None
        """
        if not isinstance(item, Item):
            raise InvalidParameters

        self.item_blueprints[item.name] = str(description)

    def add_music(self, music):
        """
        Adds a Music object that will start playing when the player enters.
        :param music: path or Music
        :return: None
        """

        if not isinstance(music, Music):
            raise InvalidParameters

        self.music = music


class EventDispatcher(metaclass=Singleton):
        """
        The event handler/dispatcher for PaC
        """
        def __init__(self):
            self.events = {
                "pickup": [],
                "use-item": [],
                "use-object": [],
                "start": [],
                "combine": [],
                "enter": [],
                "music": []
            }

        def _register_event(self, event_type, fn):
            """
            Should not be used directly, use decorators instead
            :param event_type: one of below
            :param fn: function's reference ('doit' NOT 'doit()')
            :return: None
            """
            if event_type == PICKUP:
                self.events.get(PICKUP).append(fn)

            elif event_type == USE_ITEM:
                self.events.get(USE_ITEM).append(fn)

            elif event_type == USE_OBJECT:
                self.events.get(USE_OBJECT).append(fn)

            elif event_type == START:
                self.events.get(START).append(fn)

            elif event_type == COMBINE:
                self.events.get(COMBINE).append(fn)

            elif event_type == ENTER:
                self.events.get(ENTER).append(fn)

            elif event_type == MUSIC_CHANGE:
                self.events.get(MUSIC_CHANGE).append(fn)

        def dispatch_event(self, event_type, **kwargs):
            """
            Runs the registered functions for the event type
            :param event_type: one of the events
            :return: None
            """
            for fn in self.events.get(event_type):

                if not kwargs:
                    fn()

                else:
                    fn(**kwargs)

        # @decorators for fast event registering
        def ENTER(self, fn):
            self._register_event(ENTER, fn)
            return fn

        def PICKUP(self, fn):
            self._register_event(PICKUP, fn)
            return fn

        def USE_ITEM(self, fn):
            self._register_event(USE_ITEM, fn)
            return fn

        def USE_OBJECT(self, fn):
            self._register_event(USE_OBJECT, fn)
            return fn

        def COMBINE(self, fn):
            self._register_event(COMBINE, fn)
            return fn

        def START(self, fn):
            self._register_event(START, fn)
            return fn

        def MUSIC_CHANGE(self, fn):
            self._register_event(MUSIC_CHANGE, fn)
            return fn


class SaveGame:
    """
    A module that allows you to save the game.
    """
    def __init__(self, name, version):
        """
        Initializes the SaveGame.
        :param name: name of the current game
        :return: None
        """
        self.game_name = str(name)
        self.game_version = str(version)

    def save(self, data):
        """
        Saves the current state to save/name_divided_by_.save.
        :param data: a tuple or list - current room, previous room, inventory (list)
        :return: None
        """
        path = "save/{}.save".format(str(self.game_name).replace(" ", "_"))

        if not os.path.isdir("save"):
            os.makedirs("save")

        log.debug("Saving game...")

        pickle.dump(data, open(path, "wb"), pickle.HIGHEST_PROTOCOL)

    def load(self):
        """
        Loads the save if it exists.
        :return: a tuple in order: current room, previous room, inventory (list)
        """
        path = "save/{}.save".format(self.game_name.replace(" ", "_"))

        if not os.path.isfile(path):
            return None

        with open(path, "rb") as file:
            data = pickle.load(file)

        if not str(data.get("game_info").get("version")) == self.game_version:
            return None

        return data

    def has_valid_save(self):
        """
        Indicates if a valid save is present.
        :return: bool
        """
        path = "save/{}.save".format(self.game_name.replace(" ", "_"))

        if os.path.isfile(path):
            with open(path, "rb") as file:
                d = pickle.load(file)

                a = bool(d.get("game_info").get("version") == self.game_version)
                b = bool(d.get("game_info").get("name") == self.game_name)

                return bool(a is True and b is True)

        else:
            return False

# TextInterface handles player interaction


class TextInterface(metaclass=Singleton):
    """
    The basic Text interface that the player interacts with.
    """
    def __init__(self, autosave=True):
        self.running = True

        self.autosave = autosave
        self.save_count = 0

    def begin_adventure(self, pac):
        """
        Prints the starting message and begins the while True loop, starting user interaction : the game.
        :param pac: PaCInterpreter created by user
        :return: None
        """
        def get_room_header(room):
            if isinstance(room, Room):
                room = room.name

            else:
                room = str(room)

            wys = ", ".join(pac.ways())

            ti = int( (PADDING-len(room)) / 2)

            hd = ("-" * ti) + room + ("-" * ti) + "\n" + "You can go to: " + wys + "\n"  # Header

            return hd

        def text_adventure():
            inp = str(input(">"))

            if inp == "help" or inp == "what to do":
                commands = ["go", "pick up", "use", "inv", "where", "combine", "save", "settings", "exit"]
                wraptext(", ".join(commands))

            # Displays possible ways out of the room (DEPRECATED!)
            elif inp.startswith(("ways", "path", "paths", "way")):
                wraptext("You can go to: " + ", ".join(pac.ways()))

            elif inp.startswith(("settings", "preferences")):
                print("1. autosave : {}\n2. exit".format("enabled" if self.autosave else "disabled"))

                ce = str(input())

                if ce.startswith(("1", "autosave")):
                    ce = str(input("Do you want to turn Autosaving On or Off? "))

                    if ce.startswith(("on", "ON", "True", "turn it on")):
                        self.autosave = True
                        print("Autosaving: enabled")
                    else:
                        self.autosave = False
                        print("Autosaving: disabled")

            # Gives you a list of items in the room (DEPRECATED!)
            elif inp.startswith(("items", "objects", "items in the room", "what items are in the room")):
                object_list = pac.get_current_room().get_items()

                objects = []
                for obj in object_list:
                    # Just for the correct grammar jk
                    if str(obj.name).startswith(("a", "e", "i", "o", "u")):
                        um = "an"
                    else:
                        um = "a"

                    objects.append(str(um + " " + obj.name))

                # Correct prints
                if len(objects) == 0:
                    print("There are no items here.")

                elif len(objects) == 1:

                    print("In the room there is " + objects[0] + "\n")

                else:
                    wraptext("In the room there are " + ", ".join(objects))

            # Moves the player back to the previous room.
            elif inp.startswith("go back"):

                try:
                    insert = str(pac.previous_room.name)
                    # Stores room before calling go_back() method where the room gets changed

                    desc = pac.go_back()

                except NotImplementedError or NotLinked or AttributeError:
                    return

                if not isinstance(desc, list):
                    print(get_room_header(pac.current_room))
                    wraptext(desc)

                else:
                    wraptext(desc[0])

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

                # Printed when you did "walk [somethingthatisnothere]"
                else:
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
                except NotImplementedError or NotLinked:
                    return

                if not isinstance(desc, list):
                    print(get_room_header(pac.current_room))
                    wraptext(desc)

                else:
                    wraptext(desc[0])

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

                on_use = pac.pick_up_item(on)
                if not on_use:
                    pass

                else:
                    wraptext(on_use)

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
                    desc = pac.use_item(pac.get_item_by_name(on))

                except NotImplementedError:
                    spl = on.split(" with ")

                    if len(spl) == 1:
                        spl = on.split(" on ")

                        if len(spl) == 1:
                            print("What do you want to use?")
                            return

                    try:
                        desc = pac.use_static_object(pac.get_static_object_by_name(spl[1]), pac.get_item_by_name(spl[0]))
                    except NotImplementedError:
                        return

                if not desc:
                    return

                wraptext(desc)

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
                    crafting_desc = pac.combine(sr[0].strip(" "), sr[1].strip(" "))
                except NotImplementedError:
                    return

                if not crafting_desc:
                    wraptext(pac.d_failed_combine)
                    return

                wraptext(crafting_desc)

            # Displays items in your inventory
            elif inp.startswith(("inventory", "inv")):
                # Converts items to a list of names
                items = []
                for it in pac.get_inventory():

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
                    wraptext("You have " + items[0] + " and " + items[1])

                else:
                    wraptext("You have " + ", ".join(items))

            # Tells you what room you are currently in
            elif inp.startswith(("where am i", "where", "room")):
                wraptext("You are in the " + str(pac.get_current_room().name))

            # Saves the game
            elif inp.startswith(("save", "save game", "do a save", "gamesave")):
                pac._save_game()
                print("Game has been saved.")

            # Option to quit game
            elif inp.startswith(("exit", "quit", "q")):
                n = str(input("Are you sure?"))

                if str(n).lower().startswith(("yes", "yup", "ye", "sure", "y")):
                    ce = str(input("Would you like to save your current game? y/n "))
                    if ce.lower() == "y":
                        pac._save_game()
                        print("Game saved, bye!")

                    else:
                        print("Bye!")
                    self.running = False
                    return

                elif n.lower().startswith(("no", "nope", "n", "not sure")):
                    return


        # Prints the starting message and the usual for the starting room and then enters the 'infinite' loop.

        pac._init_save()  # creates SaveGame instance at pac.saving

        if pac.saving.has_valid_save():
            doit = str(input("A save has been found. Do you want to load the save? y/n "))

            if doit.lower() == "y" or not doit:
                pac._load_game()

                # Start music if the room has it
                if pac.current_room.music:
                    pac._start_music_thread(pac.currentroom.music)

                print("Save loaded.")

            # Require confirmation
            elif doit.lower() == "n" or doit:
                c = input("Are you sure? With next save all your progress will be lost. y (continue) / n (load save anyway) ")
                if c.lower() == "n":
                    pac._load_game()

                    if pac.currentroom.music:
                        pac._start_music_thread(pac.currentroom.music)

                    print("Save loaded.")

                else:
                    pass

            else:
                log.warn("Got unexpected response.")

        print(pac.starting_message + "\n" + get_room_header(pac.current_room.name))
        wraptext(pac.current_room.enter())

        while self.running:  # Defaults to True, creates an infinite loop until exiting

            if self.save_count >= 4 and self.autosave is True:
                pac._save_game()
                self.save_count = 0

            text_adventure()
            self.save_count += 1

        # Code never reaches this point... probably (except when quitting)

# Main class


class PaCInterpreter(metaclass=Singleton):
    """
    The interpreter, linking together all objects and your code.
    PaC stands for point and click (adventure) ;)
    """

    def __init__(self, name=None, desc=None, version=None, autosave=True):
        # Game info vars
        self.name = name
        self.description = desc
        self.version = version

        self.saving = None

        # Game engine stuff
        self.rooms = {}
        self.items = {}
        self.statics = {}
        self.blueprints = []

        self.inv = []

        self.visits = []
        self.links = {}

        self.current_room = None
        self.previous_room = None

        self.starting_room = None
        self.starting_message = None

        self.running = False

        # Defaults (default pick up is defined in createItem)
        self.d_use = "Hmm..."
        self.d_failed_use = "Hmm..."
        self.d_failed_pickup = "I can't do that."
        self.d_failed_combine = "Can't do that..."

        self.music_thread = None
        self.events = None

        self.autosave = autosave

    def _set_event_dispatcher(self, event_dispatcher):
        """
        !DEPRECATED!
        EventDispatcher is now a singleton so setting one is not needed
        Associates the instance of EventDispatcher with PacInterpreter
        :param event_dispatcher: an instance of EventDispatcher (optional)
        :return: None
        """
        if not isinstance(event_dispatcher, EventDispatcher):
            raise InvalidParameters

        self.events = event_dispatcher

    def start(self, ask_for_save=True):
        """
        Starts the adventure with you in the default room and the starting message.
        If you have not defined a starting room or message, MissingParameters will be raised.
        :return: None
        """
        self.running = True
        self.current_room = self.starting_room

        mixer.init()  # Inits the mixer module (for Music)

        if not self.events:
            self.events = EventDispatcher()

        self.events.dispatch_event(START)

        if not self.starting_room or not self.starting_message:
            raise MissingParameters

        self.visits.append(self.current_room)

        # Instances the TextInterface class (no need for it to be class-wide for now)
        text_interface = TextInterface(autosave=self.autosave)

        # If the starting room has music, start playing.
        if self.starting_room.music:
            self._start_music_thread(self.starting_room.music)

        # With this the TextInterface has the access to the class - the 'story'.
        # Prints the starting message and begins the while True loop.

        text_interface.begin_adventure(self)

    def set_default_use_fail_message(self, message):
        """
        Sets the default message to return when not being able to use an item (when not overridden by Item specific fail message).
        :param message: string
        :return: None
        """
        self.d_failed_use = str(message)

    def set_default_pick_up_fail_message(self, message):
        """
        Sets the default message to return when not being able to pick up an item (when not overridden by Item specific fail message).
        :param message: string
        :return: None
        """
        self.d_failed_pickup = str(message)

    def set_default_combine_fail_message(self, message):
        """
        Sets the default message for when failed to combine.
        :param message: string
        :return: None
        """
        self.d_failed_combine = str(message)

    def set_default_use_message(self, message):
        """
        Sets the default message for when using an item (when not overridden by item specific use message)
        :param message:
        :return:
        """
        self.d_use = str(message)

    def set_starting_message(self, message):
        """
        Sets the starting message. Necessary before calling start().
        :param message: string
        :return: None
        """
        self.starting_message = str(message)

    @staticmethod
    def set_textwrap_length(length):
        """
        Defaults to 65.
        :param length: int
        :return: None
        """
        global PADDING
        PADDING = int(length)

    def set_autosave(self, action):
        """
        Enables or disabled autosave.
        :param action: bool
        :return: None
        """
        self.autosave = bool(action)


    def get_rooms(self):
        """
        Returns a dictionary of rooms created.
        {room name : Room object, ...}
        :return: dict of rooms
        """
        return self.rooms

    def get_current_room(self):
        """
        Returns the current room.
        :return: Room object
        """
        if not self.current_room:
            raise NotImplementedError

        return self.current_room

    def get_inventory(self):
        """
        Returns a list of Items in the players inventory.
        :return: list of Items
        """
        return list(self.inv)

    def get_room_by_name(self, name):
        """
        Returns the Room by its name.
        :param name: room name string
        :return: Room object
        """
        return self.rooms[str(name)]

    def get_item_by_name(self, item):
        """
        Returns the Item by its name. Raises NotImplementedError if the item does not exist.
        :param item: item name string
        :return: Item object
        """
        try:
            return self.items[item]
        except KeyError:
            raise NotImplementedError

    def get_static_object_by_name(self, obj):
        """
        Returns the StaticObject by its name. Raises NotImplementedError if the item does not exist
        :param obj: object name string
        :return: StaticObject object
        """
        try:
            return self.statics[obj]
        except KeyError:
            raise NotImplementedError


    def create_room(self, name, desc, on_first_enter=None, starting=False):
        """
        Creates a Room with supplied properties.
        :param name: room name
        :param desc: room description
        :param on_first_enter: description to be displayed when entering the room for the first time
        :param starting: bool indicating if the room should be the starting one
        :return: created Room object
        """
        if not name:
            raise MissingParameters

        if name in self.rooms:
            raise AlreadyExists

        room = Room(name, desc, on_first_enter, starting)
        self.rooms[str(name)] = room

        if starting:
            self.starting_room = room

        return room

    def create_item(self, name, desc, on_use=None, failed_use=None, failed_pickup=None, on_pickup=None, is_craftable=False, crafting_desc=None):
        """
        Creates an Item with supplied properties. All parameters have to be strings.
        If on_use is not supplied, the item is 'kinda' unusable, printing "hmmm..." on use.
        :param name: item name
        :param desc: item description
        :param on_use: string to be displayed when using the item
        :param failed_use: string to be displayed when not being able to use the item
        :param failed_pickup: string to be displayed when not being able to pick up the item
        :param on_pickup: string to be displayed when picking up the item
        :param is_craftable: bool
        :param crafting_desc: str to display when this item is crafted
        :return: created Item object
        """
        if not name or not desc:
            raise InvalidParameters

        if not on_use:
            on_use = self.d_use

        if not on_pickup:
            on_pickup = "You picked up {}".format(str(name))

        if not failed_use:
            failed_use = self.d_failed_use

        if not failed_pickup:
            failed_pickup = self.d_failed_pickup

        if not crafting_desc:
            crafting_desc = "By combining you created a {}".format(str(name))

        obj = Item(name, desc, on_use, failed_use, failed_pickup, on_pickup, is_craftable, crafting_desc)

        # 'Registers' the object for getItemByName()
        self.items[obj.name] = obj
        return obj

    def create_blueprint(self, item1, item2, final_item):
        """
        Creates a blueprint for combining two items together to make another item which also has to be the Item object.
        The order does not matter.
        :param item1: First Item object to combine
        :param item2: Second Item object to combine
        :param final_item: Item object that will be the result
        :return: None
        """
        # Converts from str to Item objects if needed
        if not isinstance(item1, Item):
            item1 = self.get_item_by_name(item1)

        if not isinstance(item2, Item):
            item2 = self.get_item_by_name(item2)

        if not isinstance(final_item, Item):
            final_item = self.get_item_by_name(final_item)

        # Done converting, now append the blueprint to self.blueprints in the form of tuple
        app = (item1, item2, final_item)
        self.blueprints.append(app)

    def create_static_item(self, name, display, on_use=None, failed_use=None):
        """
        Creates a StaticObject that can 'sit' in the room and be interacted with.
        It can not be picked up, but can be used with/without special items.
        :param name: object name
        :param display: string that will be displayed when the object is in the room
        :param on_use: string that will be displayed when using the object without special items.
        :param failed_use: displayed when not able to use the object
        :return: StaticObject object
        """
        if not name or not display:
            raise InvalidParameters

        if not on_use:
            on_use = self.d_use

        if not failed_use:
            failed_use = self.d_failed_use

        obj = StaticObject(name, display, on_use, failed_use)
        self.statics[name] = obj

        return obj

    def combine(self, item1, item2):
        """
        Combines two items together is there is a blueprint for the combination.
        :param item1: Item object or item name
        :param item2: Item object or item name
        :return: Combined item (Item)
        """
        # Converts to Item objects if needed
        if not isinstance(item1, Item):
            item1 = self.get_item_by_name(item1)

        if not isinstance(item2, Item):
            item2 = self.get_item_by_name(item2)

        # Checks existence in inventory
        if not ((item1 in self.inv) and (item2 in self.inv)):
            return False

        # Shifts through blueprints
        for c, blue in enumerate(self.blueprints):
            item1 = blue[0]
            item2 = blue[1]

            if (item1 == item1 and item2 == item2) or (item1 == item2 and item2 == item1):
                result = blue[2]
                self.inv.pop(c)
                self.inv.pop(c)

                self.put_into_inv(result)

                # Dispatch event
                self.events.dispatch_event(COMBINE, item1=item1, item2=item2, result=result)

                return result.craft()

        return False


    def link_room(self, room1, room2, two_way=False):
        """
        Links two rooms together (one-way or two-way).
        :param room1: Room to link from
        :param room2: Room to link to
        :param two_way: Defaults to False, indicates of the path should be two-way
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

        # Second link, if two_way is True
        if two_way:
            try:
                self.links[room2.name].append(room1.name)

            except KeyError:
                self.links[room2.name] = []
                self.links[room2.name].append(room1.name)

    @staticmethod
    def put_item(room, item, description):
        """
        Puts an item into a room.
        :param room: Room to put the Item into
        :param item: Item to put in the Room
        :param description: string to display when an item is in the room
        :return: None
        """
        if not isinstance(room, Room) or not isinstance(item, Item):
            raise InvalidParameters

        room.put_item(item, description)

    @staticmethod
    def put_static_item(room, obj):
        """
        Puts a StaticObject into a room. (description is provided by StaticObject.display string)
        :param room: Room to put the StaticObject into
        :param obj: StaticObject to put in the Room
        :return: None
        """
        if not isinstance(room, Room) or not isinstance(obj, StaticObject):
            raise InvalidParameters

        room.put_static_obj(obj, obj.display)

    def put_into_inv(self, item):
        """
        Puts an Item into your inventory.
        :param item: Item to put
        :return: None
        """
        if not isinstance(item, Item):
            raise InvalidParameters

        self.inv.append(item)

    def pick_up_item(self, item):
        """
        Picks up the item in the current room.
        :param item:
        :return: False if failed, item on_pickup string if successful.
        """
        # Converts string to Item if needed
        if not isinstance(item, Item):

            try:
                item = self.items[item]
            except KeyError:
                return False

        if not item == self.current_room.items.get(item.name):
            return False

        if not item.has_pick_up_requirements(self.inv):
            if item.onfaileduse is not None:
                return str(item.on_failed_pickup)
            else:
                return self.d_failed_pickup

        it = self.current_room.pick_up_item(item)
        self.events.dispatch_event(PICKUP, item=item, desc=it)

        that_item = self.items[item.name]
        self.put_into_inv(that_item)

        return it

    def use_item(self, item):
        """
        Uses an Item in your inventory
        :param item: Item to use
        :return: False if failed, Item on_use string is successful
        """
        if not isinstance(item, Item):
            raise InvalidParameters

        if item not in self.inv:
            return False

        else:
            if not item.has_use_requirements(self.inv):

                if item.on_failed_use is not None:
                    return str(item.on_failed_use)
                else:
                    return self.d_failed_use

            desc = item.use()
            self.events.dispatch_event(USE_ITEM, item=item, desc=desc)
            return desc

    def use_static_object(self, obj, item=None):
        """
        Uses the StaticObject in the room.
        :param obj: StaticObject
        :param item: Item to use with (optional)
        :return: StaticObject display string
        """
        if not isinstance(obj, StaticObject):
            raise InvalidParameters

        if obj not in self.current_room.get_static_items():
            return False

        else:
            if not obj.has_item_requirements(self.inv):

                if obj.on_failed_use is not None:
                    return str(obj.on_failed_use)
                else:
                    return self.d_failed_use

            if not item:
                if obj.music:
                    self._start_music_thread(obj.music)
                desc = obj.use()
            else:
                if obj.music:
                    self._start_music_thread(obj.music)
                desc = obj.use_with_item(item)

            self.events.dispatch_event(USE_OBJECT, object=obj, desc=desc)
            return desc

    def walk(self, room):
        """
        Walks the user from the current room to the specified one.
        Raises NotImplementedError if the room does not exist and NotLinked if the room is not linked.
        :param room: Room to go to
        :return: Room onenter string if everything is okay, a list with one item in a string of not
        """

        # Gets the Room object if needed
        if not isinstance(room, Room):
            try:
                room = self.rooms[str(room)]
            except KeyError:
                raise NotImplementedError

        # Starts the music if the room has one
        if room.music:
            if not self.music_thread == room.music:
                self._start_music_thread(room.music)

        # Raise NotLinked if the room does not have a link to the specified one
        if room.name not in self.links.get(self.current_room.name):
            raise NotLinked

        # Processes requirements
        itemr = room.has_item_requirements(self.inv)
        roomr = room.has_visit_requirement(self.visits)

        if itemr or roomr:
            self.events.dispatch_event(ENTER, fr=self.current_room, to=room, first_time=not room.entered)

        if itemr == 1:
            if roomr == 1:  # Only if everything is fulfilled, return room description
                desc = room.enter()

                # Sets current room and the one you were just in
                self.previous_room = self.current_room
                self.current_room = room

                self.visits.append(room)

                return desc

            else:  # Return room deny message
                return [roomr]

        else:  # Item is not correct, branch out

            if roomr == 1:  # If room requirements are okay, return only item deny message
                return [itemr]

            else:  # Both are not fulfilled, return str of both
                return [str(str(itemr) + "\n" + str(roomr))]

    def go_back(self):
        """
        Moves the player back to the previous room.
        :return: Same as walk() method (Room on_enter string if everything is okay, a list with one item in a string of not)
        """
        if not self.previous_room:
            raise NotImplementedError

        return self.walk(self.previous_room)

    def ways(self):
        """
        Returns a list of links (ways/paths) from the current room.
        :return - list of links
        """
        room = self.current_room

        if not self.current_room or not isinstance(self.current_room, Room):
            raise MissingParameters

        try:
            return self.links[room.name]
        except KeyError:
            return []

    def add_music(self, music, place):
        """
        Adds music to be played when entering a room or interacting with a StaticObject.
        Music does NOT stop playing when moving to a room without music!
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

        place.add_music(music)

    @threaded
    def _start_music_thread(self, music, repeat=True):
        """
        Starts the music, stopping any existing threads.
        :param music: Music
        :return: None
        """
        if not isinstance(music, Music):
            raise InvalidParameters

        try:
            self.music_thread.stop()
        except AttributeError:
            pass

        self.music_thread = music
        self.last_music_thread = music
        self.music_thread.__init__(self.music_thread.path)

        self.events.dispatch_event(MUSIC_CHANGE, music=music, path=music.path)
        self.music_thread.start(repeat)

    def _save_game(self):
        """
        Saves the current state of the game to save/name_of_the_game.save
        :return: None
        """
        if not self.saving:
            self._init_save()

        rooms = {k: r for k, r in self.rooms.items()}
        items = {k: r for k, r in self.items.items()}
        statics = {k: r for k, r in self.statics.items()}

        inv = self.inv
        visited = self.visits

        data = {
            "state": {"rooms": rooms, "items": items, "statics": statics, "inventory": inv, "visits": visited},
            "game_info": {"name": self.name, "version": self.version}
        }

        self.saving.save(data)

    def _init_save(self):
        self.saving = SaveGame(self.name, self.version)

    def _load_game(self):
        if not self.saving:
            self._init_save()

        if self.saving.has_valid_save():
            data = self.saving.load()

            # has_valid_save() should check for this, but we check again
            if data.get("game_info").get("version") != self.version:
                log.warning("Game version is not the same even though has_valid_save() reported so! Not loading the save!")
                return

            game_info = data.get("game_info")
            game_state = data.get("state")

            if not game_info or not game_state:
                log.error("Game save is corrupt.")
                # User should delete the save him/herself.
                return

            self.rooms = game_state.get("rooms")
            self.items = game_state.get("items")
            self.statics = game_state.get("statics")

            self.inv = game_state.get("inventory")
            self.visits = game_state.get("visits")

            self.current_room = game_state.get("rooms").get(self.current_room.name)

            try:
                self.previous_room = game_state.get("rooms").get(self.previous_room.name)
            except AttributeError:
                pass
