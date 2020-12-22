import sqlite3
import traceback
import re
from enum import Enum
import readline
from BarManagerStructures import Ingredient
from BarManagerStructures import Recipe
from BarManagerStructures import Recipe_Ingredient

class Method(Enum):
    QUIT = "q"
    SEARCH = "s"
    TITLE_SEARCH = "t"
    INGREDIENT_SEARCH = "i"
    NONE = ""

def string_found(string1, string2):
    if re.search(r"\b" + re.escape(string1) + r"\b", string2):
        return True
    return False

def string_front_found(string1, string2):
    if re.search(r"^" + re.escape(string1) + r"\b", string2):
        return True
    return False

def get_ingredients_from_recipe_ids(cursor, recipe_ids):
    if len(recipe_ids) == 0:
        print("No recipes specified")
        return {}

    where_statement = "recipe_recipe_ingredient.recipe_id = ? OR " * len(recipe_ids)
    where_statement = where_statement[:-3]
    query = """SELECT recipe_recipe_ingredient.recipe_id, recipe_ingredient.amount, unit.name,
        ingredient.name, type.name,recipe_ingredient.notes FROM recipe_recipe_ingredient
        JOIN recipe_ingredient ON recipe_ingredient.rowid = recipe_recipe_ingredient.recipe_ingredient_id
        JOIN ingredient ON ingredient.rowid = recipe_ingredient.ingredient
        JOIN unit ON unit.rowid = recipe_ingredient.unit
        JOIN type ON type.rowid = recipe_ingredient.type
        WHERE """ + where_statement + """;"""
    ingredient_rows = cursor.execute(query, recipe_ids)
    ingredient_rows = list(ingredient_rows)

    recipe_ingredients = {}
    for ingredient in ingredient_rows:
        if ingredient[0] not in recipe_ingredients:
            recipe_ingredients[ingredient[0]] = []
        amount = ingredient[1]
        unit = ingredient[2]
        name = ingredient[3]
        itype = ingredient[4]
        notes = ingredient[5]
        recipe_ingredients[ingredient[0]].append(Recipe_Ingredient(name, amount, unit, itype, notes))
    return recipe_ingredients

def get_recipes_from_ids(cursor, ids):
    if len(ids) == 0:
        print("No recipes specified")
        return []

    where_statement = "recipe.rowid = ? OR " * len(ids)
    where_statement = where_statement[:-3]
    query = """SELECT recipe.rowid, recipe.title, category.name, GROUP_CONCAT(flavor.name, ';'),
        glass.name, recipe.instructions, recipe.information
        FROM recipe
        JOIN recipe_flavor ON recipe.rowid = recipe_flavor.recipe_id
        JOIN flavor ON flavor.rowid = recipe_flavor.flavor_id
        JOIN glass ON recipe.glass = glass.rowid
        JOIN category ON recipe.category = category.rowid
        WHERE """ + where_statement + """ GROUP BY recipe.rowid;"""
    recipe_rows = cursor.execute(query, ids)
    recipe_rows = list(recipe_rows)

    ingredients = get_ingredients_from_recipe_ids(cursor, ids)

    recipes = []
    for row in recipe_rows:
        title = row[1]
        category = row[2]
        flavors = row[3].split(';')
        glass = row[4]
        instructions = row[5]
        information = row[6]
        recipe_ingredients = ingredients[row[0]]
        recipes.append(Recipe(title, category, flavors, glass, recipe_ingredients, instructions, information))

    return recipes

def search_all(cursor, search_terms):
    searches = search_terms.split('"')
    phrases = searches[1::2]
    phrases = sum([[phrase.strip()] for phrase in phrases], [])
    words = searches[0::2]
    words = sum([word.strip().split() for word in words], [])
    searches = phrases + words

    rows = cursor.execute("SELECT rowid FROM recipe;")

    ids = []
    for row in rows:
        ids.append(row[0])

    all_recipes = get_recipes_from_ids(cursor, ids)
    recipes = []
    for recipe in all_recipes:
        if all(search.lower() in str(recipe).lower() for search in searches):
            recipes.append(recipe)

    if len(recipes) == 0:
        print("No recipes found with search '%s'" % ' '.join(searches))
        return []

    return recipes

def print_selected_recipes(recipes):
    for i, recipe in enumerate(recipes):
        print("(%i) %s" % (i, recipe.title))

    print("Which recipe(s) do you want to view? Insert 'c' for cancel")
    search = input("> ")
    print()

    if search == "":
        for recipe in recipes:
            print(recipe)
        return

    if search[0].lower() == 'c':
        return

    numbers = list(map(int, re.findall(r'\d+', search)))
    if len(numbers) == 0:
        print("Not a valid selection")
        return
    else:
        for index in numbers:
            if index >= len(recipes) or index < 0:
                print("%i was not a valid selection. Skipping" % index)
            else:
                print(recipes[index])

def print_recipes_from_rowid_title(cursor, rowid_title):
    result_ids = []

    if len(rowid_title) == 0:
        print("No results found")
        return
    if len(rowid_title) == 1:
        recipes = get_recipes_from_ids(cursor, [rowid_title[0][0]])
        for recipe in recipes:
            print(recipe)
        return

    for index, row in enumerate(rowid_title):
        print("(%i) %s" % (index, row[1]))
        result_ids.append(row[0])

    print("Which recipe(s) do you want to show results? Insert 'c' for cancel")
    search = input("> ")
    print()

    if search == "":
        recipes = get_recipes_from_ids(cursor, result_ids)
        for recipe in recipes:
            print(recipe)
        return
    elif search[0].lower() == 'c':
        return

    numbers = list(map(int, re.findall(r'\d+', search)))
    if len(numbers) == 0:
        print("Not a valid selection")
        return
    else:
        valid_indices = []
        for index in numbers:
            if index >= len(result_ids) or index < 0:
                print("%i was not a valid selection. Skipping" % index)
            else:
                valid_indices.append(result_ids[index])
        recipes = get_recipes_from_ids(cursor, valid_indices)
        for recipe in recipes:
            print(recipe)

def title_search(cursor, search_term):
    front_results = []
    middle_results = []
    back_results = []
    any_results = []
    recipe_ids = []
    all_rows = cursor.execute("""SELECT rowid, title FROM recipe""")
    for row in all_rows:
        if search_term.lower() == row[1].lower():
            front_results.append(row)
        elif string_front_found(search_term.lower(), row[1].lower()):
            middle_results.append(row)
        elif string_found(search_term.lower(), row[1].lower()):
            back_results.append(row)
        elif search_term.lower() in row[1].lower():
            any_results.append(row)

    row_sort = lambda row : row[1]
    front_results.sort(key=row_sort)
    middle_results.sort(key=row_sort)
    back_results.sort(key=row_sort)
    any_results.sort(key=row_sort)
    recipe_ids.extend([result[0] for result in front_results])
    recipe_ids.extend([result[0] for result in middle_results])
    recipe_ids.extend([result[0] for result in back_results])
    recipe_ids.extend([result[0] for result in any_results])

    return get_recipes_from_ids(cursor, recipe_ids)

def get_recipes_from_ingredient_ids(cursor, ingredient_ids):
    if len(ingredient_ids) == 0:
        print("No ingredients specified")
        return []
    elif len(ingredient_ids) == 1:
        all_rows = cursor.execute("""SELECT DISTINCT recipe.rowid, recipe.title FROM recipe_ingredient
            JOIN recipe_recipe_ingredient ON recipe_recipe_ingredient.recipe_ingredient_id = recipe_ingredient.rowid
            JOIN recipe ON recipe.rowid = recipe_recipe_ingredient.recipe_id
            WHERE ingredient = ?""", ingredient_ids)
        results = []
        for row in all_rows:
            results.append(row)
        print_recipes_from_rowid_title(cursor, results)
        return []
    else:
        where_statement = "recipe_ingredient.ingredient = ? OR " * len(ingredient_ids)
        where_statement = where_statement[:-3]
        ingredient_ids.append(len(ingredient_ids))
        query = """SELECT DISTINCT recipe.rowid, recipe.title
            FROM recipe
            JOIN (SELECT DISTINCT recipe_recipe_ingredient.recipe_id as recipe_id, COUNT(DISTINCT(ingredient.rowid)) as ingredient_count
                FROM recipe_recipe_ingredient
                JOIN recipe_ingredient ON recipe_ingredient.rowid = recipe_recipe_ingredient.recipe_ingredient_id
                JOIN ingredient ON ingredient.rowid = recipe_ingredient.ingredient WHERE """ + where_statement + """
                GROUP BY recipe_recipe_ingredient.recipe_id HAVING COUNT(*) > 1
            ) as ingredients ON ingredients.recipe_id = recipe.rowid
            WHERE ingredients.ingredient_count = ?;"""

        all_rows = cursor.execute(query, ingredient_ids)
        results = []
        for row in all_rows:
            results.append(row)
        print_recipes_from_rowid_title(cursor, results)

def ingredient_search(cursor, search_term):
    recipes = []

    front_results = []
    middle_results = []
    back_results = []
    all_other_results = []
    results = []
    result_ids = []
    all_rows = cursor.execute("""SELECT rowid, name FROM ingredient""")
    for row in all_rows:
        if search_term.lower() == row[1].lower():
            front_results.append(row)
        elif string_front_found(search_term.lower(), row[1].lower()):
            middle_results.append(row)
        elif string_found(search_term.lower(), row[1].lower()):
            back_results.append(row)
        elif search_term.lower() in row[1].lower():
            all_other_results.append(row)

    row_sort = lambda row : row[1]
    front_results.sort(key=row_sort)
    middle_results.sort(key=row_sort)
    back_results.sort(key=row_sort)
    all_other_results.sort(key=row_sort)
    results.extend([result[0] for result in front_results])
    results.extend([result[0] for result in middle_results])
    results.extend([result[0] for result in back_results])
    results.extend([result[0] for result in all_other_results])

    return get_ingredients_from_ids(cursor, results)

# Currently broken
def get_ingredients_from_ids(cursor, ingredient_ids):
    if len(ingredient_ids) == 0:
        print("No results found")
        return []
    if len(ingredient_ids) == 1:
        recipes = get_recipes_from_ingredient_ids(cursor, [ingredient_ids[0]])
        return

    for index, ingredient_id in enumerate(ingredient_ids):
        print("(%i) %s" % (index, ingredient_id))
        result_ids.append(ingredient_id)

    print("Which ingredient do you want to search on? Insert 'c' for cancel")
    search = input("> ")
    print()

    if search[0].lower() == 'c':
        return

    numbers = list(map(int, re.findall(r'\d+', search)))
    if len(numbers) == 0:
        print("Not a valid selection")
        return
    else:
        temp = []
        for index in numbers:
            if index >= len(result_ids) or index < 0:
                print("%i was not a valid selection. Skipping" % index)
            else:
                temp.append(results[index][0])
        if len(temp) == 0:
            print("No valid ingredients selected")
            return
        get_recipes_from_ingredient_ids(cursor, temp)

def main():
    print("What do you want to do?")
    print("(S)earch")
    print("(T)itle Search")
    print("(I)ngredient Search")
    print("(Q)uit")
    selection = input('> ').lower()

    try:
        return Method(selection)
    except ValueError as error:
        print("Invalid option")
        return Method.NONE

def cli():
    try:
        connection = sqlite3.connect("../cocktailbar.db")
        cursor = connection.cursor()

        while(True):
            print('============================================================')
            method = main()
            print()
            if method == Method.QUIT:
                print('============================================================')
                break
            elif method == Method.SEARCH:
                print("What do you want to search for? Use \"quotes\" to search phrases.")
                searches = input("> ")
                print()

                recipes = search_all(cursor, search)
                print_selected_recipes(recipes)
            elif method == Method.TITLE_SEARCH:
                print("What recipe title do you want to search for?")
                search = input("> ")
                print()
                recipes = title_search(cursor, search_term)
                print_selected_recipes(recipes)
            elif method == Method.INGREDIENT_SEARCH:
                print("What ingredient do you want to search for?")
                search_term = input("> ")
                print()
                ingredient_ids = ingredient_search(cursor)

            elif method == Method.NONE:
                pass
            else:
                print("How did you get here?")
            print('============================================================')
            print()

        cursor.close()
    except sqlite3.Error as error:
        print("Error while connecting to sqlite: ", error)
        traceback.print_exc()
    finally:
        if (connection):
            connection.close()
            print("The SQLite connection is closed")

# cli()
