import signal
import sys
from dataclasses import dataclass
from typing import Any
from termcolor import colored

import pickle

# File we persist our data in (using pickling).
DATA_FILE = "zoo.dat"

"""This is an animal guessing game that learns as it runs.

Copyright © 2019 Andrew Lighten

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License."""


@dataclass
class Node:
    """
    This class represents a generic node.
    """

    # Our parent node.
    parent: Any


@dataclass
class Guess(Node):
    """
    This class represents a guess at what animal the user is thinking of.
    """

    # The animal name we guess.
    animal_name: str

    def __str__(self):
        """Generate string representation."""
        return f"Guess({self.animal_name})"


@dataclass
class Question(Node):
    """
    This class represents a question that we'll ask to get closer to
    guessing what the user is thinking of.
    """

    # The question we ask
    question: str

    # The next
    positive: Node
    negative: Node

    def __str__(self):
        """Generate string representation."""
        return f"Question({self.question})"


def get_yes_or_no(question: str) -> bool:
    """
    Ask the user a question and get a “yes” or “no” answer.

    :param question: The question to ask.

    :return: True if the user answered yes, or False if they answered no.
    """

    # Run until we get a good answer
    while True:

        # Show the question
        print(question + " ", end="")

        # Get the answer
        answer = input().strip().lower()

        # Yes or no?
        if 'yes'.startswith(answer):
            return True
        elif 'no'.startswith(answer):
            return False

        # Wrong, try again
        print("Please answer \"Yes\" or \"No\".")


def do_guess(guess: Guess):
    """
    Make a guess.

    :param guess: The guess to make.
    """

    # Ask the user if we've guessed right.
    new_question = "Is your animal a " + guess.animal_name + "?"
    if get_yes_or_no(new_question):
        print()
        print(colored("Yay! I guessed right!", "green"))
        return

    # Is this the root question?
    is_root = guess.parent is None

    # We got it wrong.
    new_question, new_guess = add_new_question(guess)

    # Split the parent.
    if is_root:
        global root_node
        root_node = new_question

    # Save to disk.
    save_data()


def add_new_question(old_guess: Guess) -> (Question, Guess):
    """
    Ask the user what question can be used to distinguish between our
    last guess and the animal they're thinking of.

    :param old_guess: The guess we made.

    :return: The new question and guess nodes.
    """

    # Get the user's animal
    print()
    print(colored("Ok, so it's not a " + old_guess.animal_name + ". I give up.", "red"))
    print()
    new_animal_name = get_new_animal_name()

    # Ask how we can distinguish between the old guess and the animal
    # the user was thinking of
    question = get_question(old_guess.animal_name, new_animal_name)

    # Create the new question node
    new_guess = Guess(parent=None, animal_name=new_animal_name)
    new_question = Question(parent=None, question=question,
                            positive=new_guess, negative=old_guess)

    # Replace the question's negative path with the new question
    if old_guess.parent and isinstance(old_guess.parent, Question):
        parent = old_guess.parent
        if parent.negative == old_guess:
            old_guess.parent.negative = new_question
        elif parent.positive == old_guess:
            old_guess.parent.positive = new_question

    # Update parents
    new_guess.parent = new_question
    old_guess.parent = new_question

    # Done
    return new_question, new_guess


def get_question(old_animal_name: str, new_animal_name: str) -> str:
    """
    Get a question that can distinguish the old animal guess from the
    new one.

    :param old_animal_name: The old animal name.
    :param new_animal_name: The new animal name.

    :return: The question.
    """
    print("")
    print(
        f"I need to know how to tell the difference between \"{new_animal_name}\" and \"{old_animal_name}\".")
    while True:
        print(
            f"What statement would be TRUE for \"{new_animal_name}\" but NOT TRUE for \"{old_animal_name}\"? ", end="")
        question = input().strip()
        if not question:
            continue
        question = question.lower().capitalize()
        if question[-1] == '?':
            question = question[:-1]

        print("")
        print(
            f"So if I asked you \"{question}?\", your answer would be true for \"{new_animal_name}\", but false for \"{old_animal_name}\".")

        if get_yes_or_no("Is that right?"):
            return question


def get_new_animal_name() -> str:
    while True:
        print("What animal were you thinking of? ", end="")
        animal_name = input().strip().lower()
        if not animal_name:
            continue
        if get_yes_or_no("Your animal was \"" + animal_name + "\"?"):
            return animal_name


def do_question(question: Question) -> Node:
    """
    Ask the user a question. If they answer "yes", we follow the
    positive child node, otherwise, we follow the negative child node.

    :param question: The question node.

    :return: The new node.
    """
    if get_yes_or_no(question.question + "?"):
        return question.positive
    else:
        return question.negative


def play(node: Node):
    """
    Play the game, starting at the nominated node.

    :param node: The next node to ask the user about.
    """

    # Process this node.
    if isinstance(node, Guess):
        do_guess(node)
    elif isinstance(node, Question):
        play(do_question(node))
    else:
        print("Don't know how to deal with node!")


def dump_nodes(node: Node, prefix: str, depth: int):
    """
    Dump a node and its child nodes.

    :param node: The node to dump.
    :param prefix: The prefix to show before the node.
    :param depth: The depth of our dump, used to indent the display.
    """
    indent = " " * (depth * 2) + prefix
    if isinstance(node, Guess):
        print(f"{indent}Guess(animal_name={node.animal_name})")
    elif isinstance(node, Question):
        print(f"{indent}Question(question={node.question})")
        dump_nodes(node.positive, "Positive", depth + 1)
        dump_nodes(node.negative, "Negative", depth + 1)


def save_data():
    """
    Save our data to a file.
    """
    with open(DATA_FILE, mode="wb") as f:
        pickle.dump(root_node, f)


def load_data() -> Node:
    """
    Load our data from a file.
    """

    try:
        with open(DATA_FILE, mode="rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return Guess(parent=None, animal_name='dog')


def sigint_handler(signum: int, _):
    """
    Handle an interrupt signal by terminating the python interpreter.

    :param signum: The signal number.
    :param _: The stack trace (ignored).
    """
    print("")
    print("")
    print(colored("Ok, bye for now.", "blue"))
    print("")
    sys.exit(0)


# Setup the initial guss.
root_node = load_data()
# dump_nodes(root_node, '', 0)

# Register Ctrl-C handler
signal.signal(signal.SIGINT, sigint_handler)

# Run the game.
print("")
print("------------------------------------------------------")
print("Think of an animal, and I'll try and guess what it is.")
play(root_node)
