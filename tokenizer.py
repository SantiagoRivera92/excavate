import re
from datetime import datetime

equivalences = {
    'a': 'attribute',
    'atk': 'atk',
    'def': 'def',
    'l': 'level',
    'lv': 'level',
    'lvl': 'level',
    'level': 'level',
    'rank': 'level',
    'link': 'level',
    'rating': 'level',
    't': 'typeline',
    'type': 'typeline',
    'c': 'card_type',
    's': 'scale',
    'card_type': 'card_type',
    'o':'text',
    'text':'text',
    'archetype':'archetype',
    'd':'date'
}

handtrap_ids = [87126721,35112613,98777036,4810828,
                20450925,23002292,8233522,15693423,
                67750322,58655504,34267821,14558127, 
                19665973,72656408,6637331,33854624, 
                60242223, 87170768, 24508238, 91800273, 
                40366667, 97045737, 94145021, 97268402, 
                14124483, 78661338, 80978111, 73642296, 
                52038441, 59438930, 62015408, 60643553, 
                44330098, 21074344, 17266660, 94689635, 
                37742478, 10045474, 23434538, 42141493, 
                84192580, 27204311, 75425043, 2810642, 
                74203495, 1697104, 38814750, 46502744, 
                18964575, 60943118, 73602965, 34976176, 
                90179822,50078320, 81109178, 2511, 
                37629703, 74018812, 25726386, 38572779,
                88392300, 19096726, 37961969, 25926710,
                38339996]

known_formats = ["Advanced", "OCG", "Common Charity", "Master Duel", "Duel Links", "Traditional", "MD", "DL", "CC"]
equivalent_formats = {
    "Master Duel":"MD",
    "Duel Links":"DL",
    "CC": "Common Charity"
}

comparison_operators = [">=", ">", "<=", "<", "=", ":"]

numeric_fields = ["atk", "def", "level", "scale"]

is_categories = ["main", "extra", "handtrap", "dllim1", "dllim2", "dllim3"]

class Tokenizer:

    def __init__(self, formats):
        self.tw_formats = []
        for _format in formats:
            self.tw_formats.append(_format["name"])

    def generate_is_query(self, category):
        if category in is_categories:
            if category == "main":
                return {'$and': [{'$nor': [{'typeline': {'$options': 'i', '$regex': 'xyz'}}]}, {'$nor': [{'typeline': {'$options': 'i', '$regex': 'synchro'}}]}, {'$nor': [{'typeline': {'$options': 'i', '$regex': 'fusion'}}]}, {'$nor': [{'typeline': {'$options': 'i', '$regex': 'link'}}]}]}
            if category == "extra":
                return {'$or': [{'typeline': {'$options': 'i', '$regex': 'xyz'}}, {'typeline': {'$options': 'i', '$regex': 'synchro'}}, {'typeline': {'$options': 'i', '$regex': 'fusion'}}, {'typeline': {'$options': 'i', '$regex': 'link'}}]}
            if category == "handtrap":
                return {"card_id": {"$in": handtrap_ids}}
            if category == "dllim1":
                return {"status.DL": "Limited 1"}
            if category == "dllim2":
                return {"status.DL": "Limited 2"}
            if category == "dllim3":
                return {"status.DL": "Limited 3"}
        raise ValueError(f"\"is:{category}\" is an unknown property.")
            

    def generate_format_query(self, format_name:str):
        if format_name.lower() == "traditional":
            return {"$or": [{ "status.Advanced": "Limited" },{ "status.Advanced": "Semi-Limited" },{ "status.Advanced": "Unlimited" },{ "status.Advanced": "Forbidden"}]}
        for known_format in known_formats:
            if format_name.lower() == known_format.lower():
                if known_format in equivalent_formats:
                    known_format = equivalent_formats[known_format]
                if known_format != "DL":
                    return {"$or": [{ f"status.{known_format}": "Limited" },{ f"status.{known_format}": "Semi-Limited" },{ f"status.{known_format}": "Unlimited" }]}
                
                return {"$or": [{ f"status.{known_format}": "Limited 1" },{ f"status.{known_format}": "Limited 2" }, { f"status.{known_format}": "Limited 3" },{ f"status.{known_format}": "Unlimited" }]}
        for known_tw_format in self.tw_formats:
            if format_name.lower() == known_tw_format.lower():
                return {"$or": [{ f"status.tw.{known_tw_format}": "Limited" },{ f"status.tw.{known_tw_format}": "Semi-Limited" },{ f"status.tw.{known_tw_format}": "Unlimited" }]}
        raise ValueError(f"\"{format_name}\" is an unsupported format.")
    
    def generate_banlist_query(self, format_name:str):
        if format_name.lower() == "traditional":
            # Traditional has no banlist lmao
            return {}
        for known_format in known_formats:
            if format_name.lower() == known_format.lower():
                if known_format in equivalent_formats:
                    known_format = equivalent_formats[known_format]
                return {f"status.{known_format}": "Forbidden"}
        for known_tw_format in self.tw_formats:
            if format_name.lower() == known_tw_format.lower():
                return {f"status.tw.{known_tw_format}": "Forbidden"}
        raise ValueError(f"\"{format_name}\" is an unsupported format.")
            
    def generate_limited_query(self, format_name:str):
        if format_name.lower() == "traditional":
            return {"$or": [{ "status.Advanced": "Limited" },{ "status.Advanced": "Forbidden"}]}
        for known_format in known_formats:
            if format_name.lower() == known_format.lower():
                if known_format in equivalent_formats:
                    known_format = equivalent_formats[known_format]
                if known_format != "DL":
                    return {f"status.{known_format}": "Limited"}
                raise ValueError('Duel Links uses a different form of banlist. Use <a href="/search?q=is:dllim1">is:dllim1<a>, <a href="/search?q=is:dllim2">is:dllim2<a> and <a href="/search?q=is:dllim3">is:dllim3<a> instead of limited:dl or semi:dl. You can still use <a href="/search?q=forbidden:dl">forbidden:dl<a> to find cards that are Forbidden in Duel Links.')
        for known_tw_format in self.tw_formats:
            if format_name.lower() == known_tw_format.lower():
                return {f"status.tw.{known_tw_format}": "Limited"}
        raise ValueError(f"\"{format_name}\" is an unsupported format.")
            
    def generate_semilimited_query(self, format_name:str):
        if format_name.lower() == "traditional":
            return {"status.Advanced": "Semi-Limited"}
        for known_format in known_formats:
            if format_name.lower() == known_format.lower():
                if known_format in equivalent_formats:
                    known_format = equivalent_formats[known_format]
                if known_format != "DL":
                    return {f"status.{known_format}": "Semi-Limited"}
                raise ValueError('Duel Links uses a different form of banlist. Use <a href="/search?q=is:dllim1">is:dllim1<a>, <a href="/search?q=is:dllim2">is:dllim2<a> and <a href="/search?q=is:dllim3">is:dllim3<a> instead of limited:dl or semi:dl. You can still use <a href="/search?q=forbidden:dl">forbidden:dl<a> to find cards that are Forbidden in Duel Links.')
        for known_tw_format in self.tw_formats:
            if format_name.lower() == known_tw_format.lower():
                return {f"status.tw.{known_tw_format}": "Semi-Limited"}
        raise ValueError(f"\"{format_name}\" is an unsupported format.")
    
    def generate_set_query(self, set_name:str):
        name = set_name.upper() # Sets are always uppercase
        response = {"sets": {"$elemMatch": {"set_number": { "$regex": f"^{name}" }}}}
        return response

    def generate_date_query(self, date: str, operator: str) -> dict:
        # Normalize operator to MongoDB compatible symbols
        operator_map = {":": "$eq","=": "$eq","<": "$lt","<=": "$lte",">": "$gt",">=": "$gte"}
        if operator not in operator_map:
            raise ValueError(f"{operator} is an unknown operator.")
        mongo_operator = operator_map[operator]
        # Check if the date is in YYYY format (just a year) or YYYY-MM-DD
        try:
            if len(date) == 2: # YY format
                int(date)
                if mongo_operator == "$eq":  # Find between the start and end of the year
                    start_date = f"20{date}-01-01"
                    end_date = f"{date}-12-31"
                    return {'sets': {'$elemMatch': {'print_date': {'$gte': start_date,'$lte': end_date}}}}
                elif mongo_operator in ["$gt", "$lte"]:
                    # Use the end of the year as the boundary date
                    boundary_date = f"20{date}-12-31"
                    return {"sets.print_date": { mongo_operator: boundary_date }}
                elif mongo_operator in ["$lt", "$gte"]:
                    # Use the start of the year as the boundary date
                    boundary_date = f"20{date}-01-01"
                    return {"sets.print_date": { mongo_operator: boundary_date }}
            if len(date) == 4:  # YYYY format
                int(date)
                if mongo_operator == "$eq":  # Find between the start and end of the year
                    start_date = f"{date}-01-01"
                    end_date = f"{date}-12-31"
                    return {'sets': {'$elemMatch': {'print_date': {'$gte': start_date,'$lte': end_date}}}}
                elif mongo_operator in ["$gt", "$lte"]:
                    # Use the end of the year as the boundary date
                    boundary_date = f"{date}-12-31"
                    return {"sets.print_date": { mongo_operator: boundary_date }}
                elif mongo_operator in ["$lt", "$gte"]:
                    # Use the start of the year as the boundary date
                    boundary_date = f"{date}-01-01"
                    return {"sets.print_date": { mongo_operator: boundary_date }}
            elif len(date) == 10:  # YYYY-MM-DD format
                # Validate that it's a correct date format
                datetime.strptime(date, "%Y-%m-%d")
                return {"sets.print_date": { mongo_operator: date }}
            raise ValueError("Dates must be formatted as either YYYY or YYYY-MM-DD")
        except ValueError as e:
            raise ValueError("Dates must be formatted as either YYYY or YYYY-MM-DD") from e

    def turn_to_tokens(self, query, escape_regex=False):
        tokens = []
        stack = []
        i = 0
        print(f"Query: {query}")
        length = len(query)
        
        while i < length:
            char = query[i]
            if char.isspace():
                # Skip whitespace
                i += 1
                continue
            
            elif char == "\"":
                # Handle quoted strings with "
                i += 1
                start = i
                while i < length and query[i] != "\"":
                    i += 1
                if i < length and query[i] == "\"":
                    tokens.append(query[start:i])
                    i += 1
                else:
                    raise ValueError("Unclosed quotation")

            elif char == "{":
                # Handle quoted strings with {}
                i += 1
                start = i
                while i < length and query[i] != "}":
                    i += 1
                if i < length and query[i] == "}":
                    tokens.append(query[start:i])
                    i += 1
                else:
                    raise ValueError("Unclosed curly quotation")

            elif char == '-' and i + 1 < length and (query[i + 1].isalnum() or query[i+1] in {'"', '{'}):
                # Handle negated queries
                i += 1
                quoted = False
                if query[i] in {'"', '{'}:
                    if query[i] == "{":
                        quoted = "}"
                    else:
                        quoted = '"'
                    # Skip the opening quotation for now
                    i += 1
                start = i
                # If it's quoted, spaces are fair game
                while i < length and (query[i].isalnum() or (quoted and (query[i] != quoted))):
                    i += 1
                key = query[start:i]
                if quoted and i < length and query[i] == quoted:
                    i += 1  # Close the quoted part

                if i < length and query[i] in {':', '=', "<", ">"}:
                    # Handle key-value negated query
                    operator = query[i]
                    i += 1
                    if i < length and query[i] in {'"', '{'}:
                        if query[i] == "{":
                            quoted = "}"
                        else:
                            quoted = '"'
                        i += 1
                        start = i
                        while i < length and query[i] != quoted:
                            i += 1
                        value = query[start:i]
                        i += 1
                        tokens.append(f"-{key}{operator}{value}")
                    else:
                        start = i
                        while i < length and not query[i].isspace() and query[i] not in '()':
                            i += 1
                        value = query[start:i]
                        tokens.append(f"-{key}{operator}{value}")
                    continue
                else:
                    tokens.append(f"-{key}")
                    continue
            
            elif char.isalnum() or char in '&':
                if char == "&":
                    print("Found &")
                # Handle both key-value pairs, unquoted strings, and 'or'.
                start = i
                while i < length and (query[i].isalnum() or query[i] not in ' :<>=()'):
                    i += 1
                key = query[start:i]
                
                if i < length and query[i] in {':', '=', "<", ">"}:
                    # Key-value pair
                    operator = query[i]
                    i += 1
                    if i < length and query[i] in {'"', '{'}:
                        if query[i] == "{":
                            quoted = "}"
                        else:
                            quoted = '"'
                        i += 1
                        start = i
                        while i < length and query[i] != quoted:
                            i += 1
                        value = query[start:i]
                        i += 1
                        tokens.append(f"{key}{operator}{value}")
                    else:
                        start = i
                        while i < length and not query[i].isspace() and query[i] not in '()':
                            i += 1
                        value = query[start:i]
                        tokens.append(f"{key}{operator}{value}")
                    continue
                else:
                    if key == "or":
                        tokens.append("OR")
                    else:
                        tokens.append(key)
                    continue

            elif char == '(':
                stack.append(len(tokens))  
                tokens.append('(')
                i += 1
            elif char == ')':
                if stack:
                    start_index = stack.pop() 
                    group = tokens[start_index + 1:]
                    tokens = tokens[:start_index]
                    tokens.append(group)
                else:
                    raise ValueError("Unbalanced parentheses")
                i += 1

            elif char in '<>!=:':
                start = i
                if i + 1 < length and query[i + 1] == '=':
                    i += 2  # Two-character operator
                else:
                    i += 1  # Single-character operator
                operator = query[start:i]
                tokens.append(operator)

            else:
                i += 1  # Move forward for any unhandled character

        if stack:
            print(f"stack: {stack}, tokens: {tokens}")
            raise ValueError("Unbalanced parentheses in query")

        if escape_regex:
            return self.escape_tokens(tokens)

        return tokens

    def escape_tokens(self, tokens):
        escaped_tokens = []
        for token in tokens:
            if isinstance(token, list):
                escaped_tokens.append(self.escape_tokens(token))
            else:
                new_token = re.escape(token).replace("\\-", "-")
                escaped_tokens.append(new_token)
        return escaped_tokens        

    def sanitize_tokens(self,tokens):
        sanitized_tokens = []
        is_first_token = True
        last_token_was_or = False
        for token in tokens:
            if is_first_token:
                is_first_token = False
                # We don't care about the first token since it should never be OR
                if isinstance(token, list):
                    sanitized_tokens.append(self.sanitize_tokens(token))
                else:
                    sanitized_tokens.append(token)
                last_token_was_or = False
            elif token == 'OR':
                if not last_token_was_or:
                    # OR can't be a list lol
                    sanitized_tokens.append(token)
                last_token_was_or = True
            elif last_token_was_or:
                #Last token was OR, this token isn't, just append it lol
                if isinstance(token, list):
                    sanitized_tokens.append(self.sanitize_tokens(token))
                else:
                    sanitized_tokens.append(token)
                last_token_was_or = False
            else:
                #Last token wasn't OR and this isn't either: This is an AND situation
                sanitized_tokens.append("AND")
                if isinstance(token, list):
                    sanitized_tokens.append(self.sanitize_tokens(token))
                else:
                    sanitized_tokens.append(token)
                last_token_was_or = False
        return sanitized_tokens
    
    def parse_condition(self, condition):
        """Convert a single condition token to MongoDB query."""
        negated = condition.startswith("-") and len(condition)>1
        if negated:
            condition = condition[1:]
        original_field = ""
        field = ""
        value = {}
        response = {}
        for op in comparison_operators:
            if op in condition:
                field, value = condition.split(op, 1)
                original_field = field.strip()
                value = value.strip()
                # Map user input to database fields based on equivalences
                field = equivalences.get(original_field.lower(), field)
                
                if field == "archetype":
                    response = {
                        "archetypes": {
                            "$regex": re.escape(value), 
                            "$options": "i"
                        }
                    }
                    break
                if field == "f":
                    response = self.generate_format_query(value)
                    break
                if field == "set":
                    response = self.generate_set_query(value)
                    break
                if field == "date":
                    response = self.generate_date_query(value, op)
                    break
                if field == "forbidden":
                    response = self.generate_banlist_query(value)
                    break
                if field == "limited":
                    response = self.generate_limited_query(value)
                    break
                if field == "semi":
                    response = self.generate_semilimited_query(value)
                    break
                if field == "is":
                    response = self.generate_is_query(value)
                    break
                    

                # Determine the type of value to parse (int or str)
                if field in numeric_fields:
                    try:
                        # Attempt to convert to int
                        int_value = int(value)
                        # Construct MongoDB condition based on the operator
                        if op == '>=':
                            response = {field: {"$gte": int_value}}
                        elif op == '>':
                            response = {field: {"$gt": int_value}}
                        elif op == '<=':
                            response = {field: {"$lte": int_value}}
                        elif op == '<':
                            response = {field: {"$lt": int_value}}
                        else:  # '=' case
                            response = {field: int_value}
                        break
                    except ValueError as exc:
                        raise ValueError(f"The key \"{field}\" only works with numerical values.") from exc
                else:
                    response = {
                        field: {
                            "$options": "i",
                            "$regex": value
                        }
                    }  # Treat the value as a string comparison
                    break
        
        if original_field:
            if original_field == "rank":
                response = {
                    "$and":[response , {
                        "type":{
                            "$options":"i",
                            "$regex": "xyz"
                        }
                    }]
                }
            
            if original_field == "link":
                response = {
                    "$and":[response , {
                        "type":{
                            "$options":"i",
                            "$regex": "link"
                        }
                    }]
                }
        if field:
            if field == "text":
                response = {
                    "$or":[
                        response,
                        {
                            "pendulum_effect":{
                                "$options":"i",
                                "$regex": value
                            }
                        }
                    ]
                }
        
        if response:
            if negated:
                return {"$nor": [response]}
            return response
        # If no operator found, treat it as a name search

        response = {
            "name": {
                "$options": "i",
                "$regex": condition
            }
        }
        if negated:
            return {"$nor": [response]}
        return response
    
    def turn_into_query_token_list(self,parsed_tokens):
        query_token_list = []
        for token in parsed_tokens:
            if isinstance(token, list):
                query_token_list.append(self.turn_into_query_token_list(token))
            elif token in ["OR", "AND"]:
                query_token_list.append(token)
            else:
                query_token_list.append(self.parse_condition(token))
        return query_token_list
    
    def simplify_clause(self, parsed_tokens):
        if len(parsed_tokens) == 0:
            return {}
        if len(parsed_tokens) == 1:
            # If it's a list, return its simplified contents. If it's not, return itself.
            if isinstance(parsed_tokens, list):
                return self.simplify_clause(parsed_tokens[0])
            return parsed_tokens

        # If we get here, we gotta deal with a list of clauses. First we determine if it's an AND list, an OR list or a mixed list:
        if "AND" in parsed_tokens and "OR" in parsed_tokens:
            current_operator = None
            simplified_tokens = []
            for token in parsed_tokens:
                if token != "OR" and token != "AND":
                    if isinstance(token, list):
                        simplified_tokens.append(self.simplify_clause(token))
                    else:
                        simplified_tokens.append(token)
                elif token == "OR":
                    if current_operator is None:
                        current_operator = "OR"
                    elif current_operator == "AND":
                        new_clause = {"$and": simplified_tokens}
                        simplified_tokens = [new_clause, token]
                        current_operator = "AND"
                elif token == "AND":
                    if current_operator is None:
                        current_operator = "AND"
                    elif current_operator == "OR":
                        new_clause = {"$or": simplified_tokens}
                        simplified_tokens = [new_clause, token]
                        current_operator = "OR"
            # We have removed the first chain of operands. We keep going until there's only one of them.
            return self.simplify_clause(simplified_tokens)
        elif "OR" in parsed_tokens:
            # OR chain. Create a list of the tokens.
            or_tokens = []
            for token in parsed_tokens:
                if token != "OR":
                    if isinstance(token, list):
                        or_tokens.append(self.simplify_clause(token))
                    else:
                        or_tokens.append(token)
                # Now we have a list of simplified tokens: we wrap this in an OR and are done with it
            return {"$or": or_tokens}
        elif "AND" in parsed_tokens:
            # AND chain
            and_tokens = []
            for token in parsed_tokens:
                if token != "AND":
                    if isinstance(token, list):
                        and_tokens.append(self.simplify_clause(token))
                    else:
                        and_tokens.append(token)
                # Now we have a list of simplified tokens: we wrap this in an OR and are done with it
            return {"$and": and_tokens}
    
    def excavate_query_to_mongo(self, query, escape_regex):
        tokens = self.turn_to_tokens(query, escape_regex)
        sanitized_tokens = self.sanitize_tokens(tokens)
        query_token_list = self.turn_into_query_token_list(sanitized_tokens)
        simplified_query = self.simplify_clause(query_token_list)
        print(simplified_query)
        return simplified_query