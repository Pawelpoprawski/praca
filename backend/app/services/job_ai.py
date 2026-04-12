"""Job AI constants.

Swiss canton mappings and category slugs used across the job processing pipeline.
The actual AI processing logic lives in job_processor.py.
"""

SWISS_CANTONS_MAP = {
    "zurich": ["zurich", "zurych", "zürich", "zh"],
    "bern": ["bern", "berno", "berne", "be"],
    "luzern": ["luzern", "lucerna", "lucerne", "lu"],
    "uri": ["uri", "ur"],
    "schwyz": ["schwyz", "sz"],
    "obwalden": ["obwalden", "ow"],
    "nidwalden": ["nidwalden", "nw"],
    "glarus": ["glarus", "gl"],
    "zug": ["zug", "zg"],
    "fribourg": ["fribourg", "fryburg", "freiburg", "fr"],
    "solothurn": ["solothurn", "solura", "so"],
    "basel-stadt": ["basel-stadt", "basel stadt", "bazylea-miasto", "bazylea miasto", "basel city", "bs"],
    "basel-landschaft": ["basel-landschaft", "basel landschaft", "bazylea-okręg", "bazylea okrag", "bl"],
    "schaffhausen": ["schaffhausen", "szafuza", "sh"],
    "appenzell-ausserrhoden": ["appenzell-ausserrhoden", "appenzell ausserrhoden", "ar"],
    "appenzell-innerrhoden": ["appenzell-innerrhoden", "appenzell innerrhoden", "ai"],
    "st-gallen": ["st-gallen", "st gallen", "st. gallen", "sg"],
    "graubunden": ["graubunden", "graubünden", "gryzonia", "grisons", "gr"],
    "aargau": ["aargau", "argowia", "ag"],
    "thurgau": ["thurgau", "turgowia", "tg"],
    "ticino": ["ticino", "tessin", "ti"],
    "vaud": ["vaud", "waadt", "vd"],
    "valais": ["valais", "wallis", "vs"],
    "neuchatel": ["neuchatel", "neuchâtel", "neuenburg", "ne"],
    "geneve": ["geneve", "genève", "genewa", "geneva", "genf", "ge"],
    "jura": ["jura", "ju"],
}

CATEGORY_SLUGS = [
    "budownictwo",
    "gastronomia",
    "opieka",
    "transport",
    "it",
    "sprzatanie",
    "produkcja",
    "handel",
    "finanse",
    "administracja",
    "rolnictwo",
    "inne",
]
