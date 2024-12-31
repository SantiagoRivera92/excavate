import random
import datetime
import traceback
import math
import json
from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_pymongo import PyMongo
from tokenizer import Tokenizer

app = Flask(__name__)

# region Config

with open("config/config.json", "r", encoding="utf-8") as config_file:
    config = json.load(config_file)
    app.config["MONGO_URI"] = config["mongo_uri"]
    app.config['STATIC_VERSION'] = config['static_version']
    staging = config.get("staging", True)

# endregion

# region DB setup

mongo = PyMongo(app)
db = mongo.db

if staging:
    cards_db = db.StagingCards
    card_ids_db = db.StagingCardIds
    formats_db = db.StagingFormats
    decks_db = db.StagingDecks
else:
    cards_db = db.Cards
    card_ids_db = db.CardIds
    formats_db = db.Formats
    decks_db = db.Decks

# endregion

# region Utility

def get_card(card_id):
    if not isinstance(card_id, int):
        return None
    mongo_query = {"konami_id": card_id}
    return cards_db.find_one(mongo_query)

def get_tokenizer():
    return Tokenizer(get_formats())

def get_formats():
    return list(formats_db.find({}).sort("date", 1))

def get_format(name):
    # Get the format document from the formats table
    tw_format = formats_db.find_one({"name": name})
    
    if tw_format:
        # Extract the card names from the format document
        forbidden_cards = tw_format.get('forbidden', [])
        limited_cards = tw_format.get('limited', [])
        semilimited_cards = tw_format.get('semilimited', [])
        unlimited_cards = tw_format.get('unlimited', [])
        
        # Query the Cards collection for these card names
        card_names = forbidden_cards + limited_cards + semilimited_cards + unlimited_cards
        
        # Retrieve all matching cards based on the names
        card_objects = list(cards_db.find({"name": {"$in": card_names}}))
        
        # Create a dictionary to map card names to card objects
        card_dict = {card['name']: card for card in card_objects}
        
        # Replace the card names in the format document with the corresponding Card objects
        tw_format['forbidden'] = [card_dict[name] for name in forbidden_cards]
        tw_format['limited'] = [card_dict[name] for name in limited_cards]
        tw_format['semilimited'] = [card_dict[name] for name in semilimited_cards]
        tw_format['unlimited'] = [card_dict[name] for name in unlimited_cards]
        
        return tw_format
    else:
        return None



def check_if_or_in_tokens(tokens):
    for token in tokens:
        if isinstance(tokens, list):
            if check_if_or_in_tokens(token):
                return True
        if token == "OR":
            return True
    return False

def get_cards_of_the_day():
    card_ids = list(card_ids_db.find({}, {"_id":0}))
    
    today = datetime.datetime.combine(datetime.datetime.today(), datetime.time.min)
    today_unix = int(today.timestamp())
    random.seed(today_unix)
    count = len(card_ids)
    index1, index2 = random.sample(range(count), 2)
    card_id1, card_id2 = card_ids[index1]["card_id"], card_ids[index2]["card_id"]
    
    results = list(cards_db.find({"card_id": {"$in": [card_id1, card_id2]}}).sort("name", 1))
    return results

def get_random_card():
    result = cards_db.aggregate([{"$sample": {"size": 1}}])
    return next(result, None)

def execute_query(mongo_query, page, page_size):
    total_results = cards_db.count_documents(mongo_query)
    results = list(cards_db.find(mongo_query, {"_id": 0}).sort("name", 1).skip((page - 1) * page_size).limit(page_size))
    return results, total_results

def get_results(query, page, page_size, escape_regex=False):
    if not query or len(query)==0:
        return [], 0
    
    mongo_query = get_tokenizer().excavate_query_to_mongo(query, escape_regex)
    return execute_query(mongo_query, page, page_size)

def get_golf_hint():
    secure_random = random.SystemRandom()
    hints = [
        'You can do partial matches for card type.<br/><br/>"c:m" matches Monster but not Spell or Trap.<br/><br/>"c:l" matches Spell but not Monster or Trap.<br/><br/>"c:a" matches Trap but not Monster or Spell.<br/><br/>"c:s" matches Monster and Spell but not Trap.<br/><br/>"c:t" matches Monster and Trap but not Spell.<br/><br/>Just like Royal Tribute, "c:p" discards all Monsters.',
        'You can do partial matches for Attribute.<br/><br/>"a:e" will match Fire, Earth and Water since all of them contain "e".<br/><br/>"a:ar" will match Earth and Dark since both contain "ar".',
        'The "t" filter includes the entire typeline.<br/><br/>"t:l" will not only include Reptiles, Spellcasters, Plants and Illusions, but also Flip, Normal, Link, Pendulum and Ritual monsters.',
        'Pro tip: You can use quoted strings such as o:"destroy 1 monster".<br/><br/>You can optimize this further by removing characters in the beginning or end.<br/><br/>o:"destroy 1 monster" and o:"oy 1 mon" return the same amount of results.',
        'Pro tip: If you use a quoted string such as o:"destroy 1", the last " separates that token from the next. Instead of doing l=4 o:"destroy 1", try o:"destroy 1"l=4.',
        'Still using "level" in your queries? "level=4" and "l=4" are equivalent and you save 4 characters!',
        'Still using stuff like "date>2008" in your queries? Try d>08 instead!',
        'Dates work for any printing of the card.<br/><br/>d=24 will return cards that were reprinted in Quarter Century Bonanza, not just cards that were initially printed in 2024!'
    ]
    return secure_random.choice(hints)

# endregion

# region API

@app.route("/api/v1/cards", methods=['GET'])
def cards_api():
    try:
        query = request.args.get('q', 'date<9999')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 60))
        if limit > 100:
            limit = 100
        results, count = get_results(query, page, limit)
        pages = math.ceil(count / limit)
        return jsonify({"pages":pages, "cards":results})
    except Exception as e:
        return jsonify({"error": str(e), "pages":0, "cards":[]})

@app.route("/api/v1/decks", methods=['GET'])
def decks_api():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 60))
        if limit > 100:
            limit = 100
        results = list(decks_db.find({"ocg": {"$ne": True}}, {"_id": 0}).sort("created", -1).skip((page - 1) * limit).limit(limit))
        count = decks_db.count_documents({"ocg": {"$ne": True}})
        pages = math.ceil(count / limit)
        return jsonify({"pages":pages, "decks":results})
    except Exception as e:
        return jsonify({"error": str(e), "pages":0, "decks":[]})


# endregion

# region template filters

@app.template_filter('format_card_name')
def format_card_name(text, card_name):
    if text is None:
        return ""
    formatted_text = text
    bold_terms = [
        "(Quick Effect)", 
        "Once per turn", 
        f"You can only use 1 \"{card_name}\" effect per turn, and only once that turn",
        f"You can only use each effect of \"{card_name}\" once per turn",
        f"You can only use the effect of \"{card_name}\" once per turn",
        f"You can only activate 1 \"{card_name}\" per turn", 
        f"You can only use 1 {card_name} once per turn",
        "Normal Summon",
        "Special Summon",
        "Ritual Summon",
        "Fusion Summon",
        "Xyz Summon",
        "Pendulum Summon",
        "Link Summon",
        "Draw Phase",
        "Standby Phase",
        "Main Phase",
        "Battle Phase",
        "End Phase",
        "Pendulum Zone",
        "Main Monster Zone",
        "Extra Monster Zone",
        "Extra Deck",
        "Face-up",
        "Face-down",
        "face-up",
        "face-down",
        "Banish",
        "banish",
        "Destroy",
        "destroy",
        "GY",
        "Draw",
        "draw"
    ]
    for term in bold_terms:
        formatted_text = formatted_text.replace(term, f"<strong>{term}</strong>")
        
    suffixes = ["ed", "s", "(s)", "es", ":", ",", ";", ".", " 1.", " 1,", " 1:", " 1;", " 2.", " 2,", " 2:", " 2;"]
    
    for suffix in suffixes:
        formatted_text = formatted_text.replace(f"</strong>{suffix}", f"{suffix}</strong>")
    
    corrections = [
        ["Normal or<strong>Special Summoned</strong>", "<strong>Normal or Special Summoned</strong>"],
    ]
    
    for correction in corrections:
        formatted_text = formatted_text.replace(correction[0], correction[1])
    return formatted_text

# endregion

# region endpoints

@app.route("/search", methods=['GET'])
def search():
    page_size = 60
    query = request.args.get('q', '')
    page = int(request.args.get('p', 1))
    if len(query) == 0:
        return render_template('results.html.jinja', query="", title="You didn't enter anything to search for.", page=1, total_pages=0)
    try:
        results, count = get_results(query, page, page_size)
    except ValueError as e:
        return render_template('error.html.jinja', query=query, error=str(e))
    except Exception as e:
        return render_template('error.html.jinja', query=query, error=f"Invalid query ({str(e)}\n{traceback.format_exc()})")
    if count == 0:
        title = f"No results for \"{query}\"."
    elif count == 1:
        result = results[0]
        return redirect(url_for('card', id=result["konami_id"]))
    elif count <= page_size:
        title = f"Displaying {count} results."
    else:
        title = f"Displaying results {(page-1)*page_size + 1} - {min((page)*page_size, count)} out of {count}."
        
    total_pages = (count + page_size - 1) // page_size
    return render_template('results.html.jinja', query=query, results=results, title=title, page=page, total_pages=total_pages)

@app.route("/card", methods=['GET'])
def card():
    try:
        card_id_as_string = request.args.get('id', 0)
        card_id = int(card_id_as_string)
        result = get_card(card_id)
        if result:
            time_wizard_formats = get_formats()
            sorted_sets = sorted(result["sets"], key=lambda x: x["print_date"])    
            return render_template('card.html.jinja',card=result, show_all=True, prints=sorted_sets, formats = time_wizard_formats)
        return render_template('error.html.jinja', error=f"We couldn't find a card with id {card_id}.")
    except ValueError:
        return redirect(url_for('search', q=card_id_as_string))

@app.route("/golf", methods=['GET'])
def golf():
    page_size = 100
    query = request.args.get('q', '')
    
    hint = get_golf_hint()
    
    cards_of_the_day = get_cards_of_the_day()

    page = int(request.args.get('p', 1))
    try:
        if len(query) == 0:
            return render_template(
                'golf.html.jinja', 
                query=query, 
                title="Insert a query to try and match only these two cards without using \"or\". Aim for the shortest query!", 
                cards=cards_of_the_day,
                hint=hint
            )
        elif check_if_or_in_tokens(get_tokenizer().turn_to_tokens(query)):
            return render_template(
                'golf.html.jinja', 
                query=query, 
                title="You're not allowed to use \"or\" in the query for the golf game!", 
                cards=cards_of_the_day,
                hint=hint
            )
        results, count = get_results(query, page, 99999, escape_regex=True)
    except ValueError as e:
        return render_template(
            'golf.html.jinja', 
            query=query, 
            title=str(e),
            cards=cards_of_the_day,
            hint=hint
        )
    except Exception as e:
        return render_template('golf.html.jinja', query=query, title=f"Invalid query ({str(e)})", cards=cards_of_the_day, hint=hint)
    
    card_1 = cards_of_the_day[0]
    card_2 = cards_of_the_day[1]
    result_1 = None
    result_2 = None
    for result in results:
        if card_1["card_id"] == result["card_id"]:
            result_1 = result
        if card_2["card_id"] == result["card_id"]:
            result_2 = result
        if result_1 is not None and result_2 is not None:
            break
    if result_1 is not None:
        results.remove(result_1)
    if result_2 is not None:
        results.remove(result_2)

    if count == 2:
        if result_1 is not None and result_2 is not None:
            return render_template(
                'golf.html.jinja',
                title=f"Congratulations! You won today's challenge in {len(query)} characters.", 
                query=query,
                cards=cards_of_the_day, 
                results=results,
                hint=hint
            )
    if count == 0:
        return render_template(
            'golf.html.jinja', 
            query=query, 
            cards=cards_of_the_day, 
            title='No results.',
            hint=hint
        )

    if result_1 is not None and result_2 is not None:
        if count <= page_size:
            title = f"Displaying {count} results. Both cards are still in the query!"
        else:
            title = f"Displaying 100 results out of {count}. Both cards are still in the query!"
            results = results[:page_size]
        return render_template('golf.html.jinja', query=query, results=results, title=title, cards=cards_of_the_day, hint=hint)
    elif result_1 is not None:
        title = f"{card_2['name']} is not in the query! Try something else."
    elif result_2 is not None:
        title = f"{card_1['name']} is not in the query! Try something else."
    else:
        title = "Neither of the cards are in the query! Try something else."

    if count >= page_size:
        results = results[:page_size]

    return render_template('golf.html.jinja', query=query, results=results, title=title, cards=cards_of_the_day, hint=hint)

@app.route("/random", methods=['GET'])
def random_card():
    result = get_random_card()
    card_id = result["konami_id"]
    return redirect(url_for('card', id=card_id))

@app.route("/syntax", methods=['GET'])
def syntax():
    return render_template('syntax.html.jinja')

@app.route("/", methods=['GET'])
def main():
    return render_template('main.html.jinja')

# endregion

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)