import PySimpleGUI as sg
import sqlite3
from enum import Enum
import numpy
import difflib

import BarManagerDatabase as db

recipe_mapping = {}

class Key(Enum):
    SEARCH_TERM = "-RECIPE SEARCH TERM-"
    SEARCH = "-RECIPE SEARCH-"
    CLEAR = "-CLEAR SEARCH-"
    RECIPE_DISPLAY = "-RECIPE DISPLAY-"
    INGREDIENT_SELECT = "-INGREDIENT SELECT-"
    RECIPE_SELECT = "-RECIPE SELECT-"
    TITLE_SEARCH_TERM = "-TITLE SEARCH TERM-"
    INGREDIENT_SEARCH_TERM = "-INGREDIENT SEARCH TERM-"
    CLEAR_SELECTIONS = "-CLEAR SELECTIONS-"

def set_recipe_select_metadata(recipes):
    recipe_list = []
    for recipe in recipes:
        title = recipe.title
        if title in recipe_mapping.keys():
            dup_num = 1
            temp_title = title
            while temp_title in recipe_mapping.keys():
                temp_title = title + " (" + str(dup_num) + ")"
                dup_num = dup_num+1
            title = temp_title
        recipe_list.append(title)
        recipe_mapping[title] = recipe

    recipe_list.sort()
    window[Key.RECIPE_SELECT].update(recipe_list)

def set_ingredient_select(recipes):
    ingredient_mapping = {}
    for title, recipe in recipe_mapping.items():
        for ingredient in recipe.ingredients:
            if ingredient.name.capitalize() not in list(ingredient_mapping.keys()):
                ingredient_mapping[ingredient.name.capitalize()] = []
            ingredient_mapping[ingredient.name.capitalize()].append(title)

    window[Key.INGREDIENT_SELECT].metadata = ingredient_mapping
    window[Key.INGREDIENT_SELECT].update(sorted(list(ingredient_mapping.keys())))

sg.theme('DarkAmber')

search_titles_column = [
    [
        sg.Text("Recipe Search")
    ],
    [
        sg.Text("Title Search")
    ],
    [
        sg.Text("Ingredient Search")
    ]
]

search_column = [
    [
        sg.In(size=(80, 1), key=Key.SEARCH_TERM)
    ],
    [
        sg.In(size=(80, 1), key=Key.TITLE_SEARCH_TERM)
    ],
    [
        sg.In(size=(80, 1), enable_events=True, key=Key.INGREDIENT_SEARCH_TERM)
    ]
]

search_buttons_row = [
    [
        sg.Button("Clear", key=Key.CLEAR),
        sg.Button("Search", bind_return_key=True, key=Key.SEARCH)
    ]
]

# The row layout for searching recipes
recipe_search_rows = [
    [
        sg.Column(search_titles_column),
        sg.Column(search_column)
    ],
    [
        sg.Column(search_buttons_row, justification="right")
    ]
]

recipe_select = [
    [
        sg.Listbox(
            values=[], enable_events=True, select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED, size=(40, 20), key=Key.RECIPE_SELECT
        )
    ]
]

ingredient_select = [
    [
        sg.Listbox(
            values=[], enable_events=True, select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED, size=(30, 20), key=Key.INGREDIENT_SELECT
        )
    ]
]

recipe_display = [
    [
        sg.Multiline(
            default_text="", size=(50, 25), key=Key.RECIPE_DISPLAY
        )
    ]
]

# Full layout
layout = [
    [
        sg.Column(recipe_search_rows, justification="center"),
    ],
    [
        sg.Column(recipe_select),
        sg.Column(ingredient_select),
        sg.Column(recipe_display),
    ],
    [
        sg.Button("Clear Selections", key=Key.CLEAR_SELECTIONS)
    ]
]

try:
    connection = sqlite3.connect("cocktailbar.db")
    cursor = connection.cursor()

    window = sg.Window("Bar Manager", layout)

    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break

        if event == Key.SEARCH:
            recipe_mapping = {}
            search_term = values[Key.SEARCH_TERM]
            all_results = db.search_all(cursor, search_term)
            search_term = values[Key.TITLE_SEARCH_TERM]
            title_results = db.title_search(cursor, search_term)
            recipes = list(numpy.intersect1d(title_results, all_results))

            order = {n: i for i, n in enumerate(title_results)}
            recipes = sorted(recipes, key=lambda x: order.get(x, len(title_results)))

            set_recipe_select_metadata(recipes)
            set_ingredient_select(recipes)
        elif event == Key.INGREDIENT_SEARCH_TERM:
            if values[Key.INGREDIENT_SELECT]:
                filter_term = values[Key.INGREDIENT_SEARCH_TERM]
                ingredients = list(window[Key.INGREDIENT_SELECT].metadata.keys())

                if not filter_term:
                    window[Key.INGREDIENT_SELECT].update(ingredients)
                else:
                    filtered_ingredients = [ingredient for ingredient in ingredients if filter_term in ingredient]
                    window[Key.INGREDIENT_SELECT].update(filtered_ingredients)
        elif event == Key.CLEAR:
            window[Key.SEARCH_TERM].update("")
            window[Key.TITLE_SEARCH_TERM].update("")
            window[Key.INGREDIENT_SEARCH_TERM].update("")
            window[Key.RECIPE_SELECT].update("")
            window[Key.INGREDIENT_SELECT].update("")
            window[Key.RECIPE_DISPLAY].update("")
        elif event == Key.RECIPE_SELECT:
            recipes = [recipe_mapping[recipe_name] for recipe_name in values[Key.RECIPE_SELECT]]
            string = ""
            for recipe in recipes:
                string += str(recipe)
                string += "\n"
            window[Key.RECIPE_DISPLAY].update(string)
        elif event == Key.INGREDIENT_SELECT:
            if values[Key.INGREDIENT_SELECT]:
                recipes = list(recipe_mapping.keys())
                for selection in values[Key.INGREDIENT_SELECT]:
                    ingredient_recipes = window[Key.INGREDIENT_SELECT].metadata[selection]
                    recipes = list(numpy.intersect1d(recipes, ingredient_recipes))
                    if not recipes:
                        break

                recipes.sort()
                window[Key.RECIPE_SELECT].update(recipes)
        elif event == Key.CLEAR_SELECTIONS:
            window[Key.RECIPE_SELECT].SetValue([])
            window[Key.INGREDIENT_SELECT].SetValue([])
            window[Key.RECIPE_DISPLAY].update("")
            set_recipe_select_metadata(list(recipe_mapping.values()))

except sqlite3.Error as error:
    print("Error while connecting to sqlite: ", error)
    traceback.print_exc()
finally:
    if connection:
        connection.close()
        print("The SQLite connection is closed")
    window.close()
