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
