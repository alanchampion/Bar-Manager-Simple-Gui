import re

class Ingredient:
    def __init__(self, name):
        self.name = name

class Recipe_Ingredient:
    def __init__(self, name, amount, unit, itype, notes):
        self.name = name
        self.amount = amount
        self.unit = unit
        self.type = itype
        self.notes = notes

    def __str__(self):
        string = ""
        if self.type and self.type.lower() != "main":
            string += self.type + ": "
        if self.amount:
            string += str(self.amount) + " "
        if self.unit:
            string += self.unit + " "
        if self.name:
            string += self.name + " "
        if self.notes:
            string += "(" + self.notes + ")"
        return string

class Recipe:
    def __init__(self, title, category, flavors, glass, ingredients, instructions, information):
        self.title = title
        self.category = category.lower()
        self.flavors = list(map(lambda x: x.lower(), flavors))
        self.glass = glass.lower()
        self.ingredients = ingredients
        self.instructions = instructions
        self.information = information

    def __str__(self):
        string = "--------------------\n"
        string += self.title + "\n"
        string += "Category: " + self.category + "\n"
        string += "Flavors: " + ", ".join(self.flavors) + "\n"
        # if self.glass.lower() != "none":
        string += "Glass: " + self.glass.capitalize() + "\n"
        for ingredient in self.ingredients:
            string += "\n" + str(ingredient)
        string += "\n\n" + self.instructions + "\n"
        string += "\n" + self.information + "\n"
        string += "--------------------"
        return string

    def __eq__(self, other):
        return str(self) == str(other)
    def __lt__(self, other):
        return str(self) < str(other)
    def __hash__(self):
        return hash(str(self))

def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

Filler_Words = ["of", "with", "fresh", "freshly", "1:1"]
Empty_Brackets = ["()", "/{/}", "[]"]
Division_To_Decimal =  {"1/2": "0.5", "1/3": "0.333", "2/3": "0.667", "1/4": "0.25", "3/4": "0.75",
                        "1/8": "0.125", "3/8": "0.375", "5/8": "0.625", "7/8": "0.875"}

def divide_ingredient(ingredient_text, ingredients, types, units):
    ingredient_text = ingredient_text.lower()
    name = ""
    amount = ""
    unit = ""
    ingredient_type = "main"
    notes = ""

    # Any common fixes that need to be done
    if "mint sprig" in ingredient_text:
        ingredient_text = ingredient_text.replace("mint sprig", "sprig mint")
    if "half " == ingredient_text[0:5]:
        ingredient_text = "0.5 " + ingredient_text[5:]
    if "garnish:" in ingredient_text:
        ingredient_text = ingredient_text.replace("garnish:", "garnish")

    #Try to pull any notes out of the ingredient
    if '[' in ingredient_text and ']' in ingredient_text:
        notes = ingredient_text[ingredient_text.find("[")+1:ingredient_text.find("]")]

    # Split the ingredient
    temp = ingredient_text.split(" ")

    divided_ingredient = []
    # Cuts up stuff like 2.5oz to 2.5 oz
    for item in temp:
        divided_ingredient.extend(re.findall(r"[0-9./]+|[^0-9]+", item))

    # Remove any filler words/brackets
    divided_ingredient = [i for i in divided_ingredient if not i == ""]
    divided_ingredient = [i.lower() for i in divided_ingredient if i not in Empty_Brackets]
    divided_ingredient = [i.lower() for i in divided_ingredient if i not in Filler_Words]
    for index, t in enumerate(divided_ingredient):
        if t in Division_To_Decimal.keys():
            divided_ingredient[index] = Division_To_Decimal[t]

    # Try and pull the type of the ingredient
    for itype in types:
        if itype in divided_ingredient:
            ingredient_type = itype
            divided_ingredient.remove(itype)

    for index, item in enumerate(divided_ingredient):
        if isfloat(item):
            amount = item
            if index+1 < len(divided_ingredient) and divided_ingredient[index+1] in units:
                unit = divided_ingredient[index+1]
            break

    if amount:
        divided_ingredient.remove(amount)
    if unit:
        divided_ingredient.remove(unit)

    combinations = 0
    for inner_index, item in list(enumerate(divided_ingredient)):
        for outer_index in reversed(range(inner_index, len(divided_ingredient))):
            # print("%i:%i" % (inner_index, outer_index + 1), end=" ")
            possible_ingredient = ' '.join(divided_ingredient[inner_index:outer_index+1])
            # print(possible_ingredient)
            if outer_index+1 - inner_index > combinations:
                if possible_ingredient in ingredients:
                    name = possible_ingredient
                    combinations = outer_index+1 - inner_index

    return Recipe_Ingredient(name, amount, unit, ingredient_type, notes)


def get_ingredients(cursor):
    ingredients = []
    ingredient_rows = cursor.execute("SELECT ingredient.name FROM ingredient;")
    for ingredient in ingredient_rows:
        ingredients.append(ingredient[0])
    return ingredients

def get_units(cursor):
    units = []
    unit_rows = cursor.execute("SELECT unit.name FROM unit;")
    for unit in unit_rows:
        units.append(unit[0])
    return units

def get_types(cursor):
    types = []
    type_rows = cursor.execute("SELECT type.name FROM type;")
    for type in type_rows:
        types.append(type[0])
    return types

import sqlite3
connection = sqlite3.connect("cocktailbar.db")
cursor = connection.cursor()

ingredients = get_ingredients(cursor)
types = get_types(cursor)
units = get_units(cursor)
# itext = input("> ")
# i = divide_ingredient(itext, ingredients, types, units)
# print(i)
