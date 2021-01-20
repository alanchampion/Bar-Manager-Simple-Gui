import PySimpleGUI as sg
import sqlite3
from enum import Enum
import numpy
import difflib

import BarManagerDatabase as db
import BarManagerStructures as bms

recipe_mapping = {}
categories = []
flavors = []
glasses = []

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
    ADD_RECIPE = "-ADD RECIPE-"
    NEW_TITLE = "-NEW NAME-"
    NEW_CATEGORY = "-NEW CATEGORY-"
    NEW_FLAVOR_1 = "-NEW FLAVOR 1-"
    NEW_FLAVOR_2 = "-NEW FLAVOR 2-"
    NEW_GLASS = "-NEW GLASS-"
    NEW_INGREDIENT = "-NEW INGREDIENT: "
    NEW_INSTRUCTIONS = "-NEW INSTRUCTIONS"
    NEW_NOTES = "-NEW NOTES-"
    COMMIT_RECIPE = "-COMMIT RECIPE-"
    CANCEL = "-CANCEL-"

def set_recipe_mapping(recipes):
    recipe_mapping.clear()
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
        sg.Column([[sg.Button("Clear Selections", key=Key.CLEAR_SELECTIONS)]], justification="left"),
        sg.Column([[]], expand_x=True),
        sg.Column([[sg.Button("Add Recipe", key=Key.ADD_RECIPE)]], justification="right")
    ]
]

def add_recipe():
    # Add recipe layout
    new_recipe_labels = [
        [sg.Text("Name"),],
        [sg.Text("Category"),],
        [sg.Text("Flavors"),],
        [sg.Text("Glass"),],
        [sg.Text("Ingredients"),],
        [sg.Text("", size=(1, 4))],
        [sg.Text("Instructions"),],
        [sg.Text("", size=(1, 5))],
        [sg.Text("Notes"),],
        [sg.Text("", size=(1, 1))],
    ]

    new_recipe_input = [
        [sg.In(size=(60, 1), key=Key.NEW_TITLE),],
        [sg.Combo(categories, size=(58, 1), default_value="My Drinks", key=Key.NEW_CATEGORY),],
        [sg.Combo(flavors, size=(27, 1), default_value="none", key=Key.NEW_FLAVOR_1), sg.Combo(flavors, size=(27, 1), default_value="none", key=Key.NEW_FLAVOR_2)],
        [sg.Combo(glasses, size=(58, 1), default_value="none", key=Key.NEW_GLASS),],
        [sg.Multiline(size=(58, 6), key=Key.NEW_INGREDIENT),],
        [sg.Multiline(size=(58, 7), key=Key.NEW_INSTRUCTIONS),],
        [sg.Multiline(size=(58, 3), key=Key.NEW_NOTES),],
    ]

    add_recipe_layout = [
        [
            sg.Column(new_recipe_labels, element_justification="right"),
            sg.Column(new_recipe_input, justification="center")
        ],
        [
            sg.Column([[sg.Button("Cancel", key=Key.CANCEL), sg.Button("Add", key=Key.COMMIT_RECIPE)]], justification="right")
        ]
    ]
    return sg.Window("New Recipe", add_recipe_layout, finalize=True)

try:
    connection = sqlite3.connect("cocktailbar.db")
    cursor = connection.cursor()

    categories = db.get_categories(cursor)
    flavors = db.get_flavors(cursor)
    glasses = db.get_glasses(cursor)

    main_window = sg.Window("Bar Manager", layout, finalize=True)
    add_recipe_window = None

    while True:
        window, event, values = sg.read_all_windows()
        if window == sg.WIN_CLOSED or event == "Exit":
            break
        if event == "Exit" or event == sg.WIN_CLOSED:
            window.close()
            if window == main_window:
                main_window = None
                if add_recipe_window:
                    add_recipe_window.close()
                    add_recipe_window = None
            if window == add_recipe_window:
                add_recipe_window = None

        if event == Key.SEARCH:
            recipe_mapping.clear()
            search_term = values[Key.SEARCH_TERM]
            all_results = db.search_all(cursor, search_term)
            search_term = values[Key.TITLE_SEARCH_TERM]
            title_results = db.title_search(cursor, search_term)
            recipes = list(numpy.intersect1d(title_results, all_results))

            order = {n: i for i, n in enumerate(title_results)}
            recipes = sorted(recipes, key=lambda x: order.get(x, len(title_results)))

            set_recipe_mapping(recipes)
            window[Key.RECIPE_SELECT].update(sorted(recipe_mapping.keys()))
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
            set_recipe_mapping(list(recipe_mapping.values()))
            window[Key.RECIPE_SELECT].update(sorted(recipe_mapping.keys()))
        elif event == Key.ADD_RECIPE:
            print("Adding new recipe")
            add_recipe_window = add_recipe()
        elif event == Key.CANCEL:
            add_recipe_window.close()
            add_recipe_window = None
        elif event == Key.COMMIT_RECIPE:
            title = values[Key.NEW_TITLE]
            category = values[Key.NEW_CATEGORY]
            flavor_1 = values[Key.NEW_FLAVOR_1]
            flavor_2 = values[Key.NEW_FLAVOR_2]
            glass = values[Key.NEW_GLASS]
            ingredients = values[Key.NEW_INGREDIENT]
            instructions = values[Key.NEW_INSTRUCTIONS]
            notes = values[Key.NEW_NOTES]

            print(title)
            print(category)
            print(flavor_1)
            print(flavor_2)
            print(glass)
            print(ingredients)
            print(instructions)
            print(notes)

except sqlite3.Error as error:
    print("Error while connecting to sqlite: ", error)
    traceback.print_exc()
finally:
    if connection:
        connection.close()
        print("The SQLite connection is closed")
    if main_window:
        main_window.close()
    if add_recipe_window:
        add_recipe_window.close()
