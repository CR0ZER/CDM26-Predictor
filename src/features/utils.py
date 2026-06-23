TEAM_NAME_MAPPING: dict[str, str] = {
    "Czech Republic": "Czechia",
    "Republic of Ireland": "Ireland",
    "São Tomé and Príncipe": "Sao Tome and Principe",
    "Timor-Leste": "East Timor",
    "United States Virgin Islands": "US Virgin Islands",
    "Macau": "Macao",
    "North Macedonia": "Macedonia",
    "Eswatini": "Swaziland",
}
NON_FIFA_ENTITIES: list[str] = [
    "Abkhazia", "Alderney", "Ambazonia", "American Samoa", "Andalusia",
    "Artsakh", "Barawa", "Basque Country", "Brittany", "Canary Islands",
    "Cascadia", "Catalonia", "Chechnya", "Cilento", "Corsica",
    "Donetsk PR", "East Turkestan", "Elba Island", "Ellan Vannin",
    "Franconia", "Galicia", "Gozo", "Guernsey", "Jersey", "Kernow",
    "Luhansk PR", "Micronesia", "Occitania", "Padania", "Panjab",
    "Parishes of Jersey", "Provence", "Raetia", "Romani people",
    "Ryūkyū", "Réunion", "Saint Barthélemy", "Saint Helena", "Saugeais",
    "Sealand", "Seborga", "Silesia", "South Ossetia", "Surrey",
    "Székely Land", "Sápmi", "Tamil Eelam", "Ticino",
    "United Koreans in Japan", "Vatican City", "West Papua",
    "Ynys Môn", "Yorkshire", "Åland Islands",
]
FOOTBALL_DATA_NAME_MAPPING: dict[str, str] = {
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Cape Verde Islands": "Cape Verde",
    "Congo DR": "DR Congo",
}
HOST_NATIONS = {"United States", "Canada", "Mexico"}

def is_neutral_venue(home_team: str, away_team: str) -> bool:
    home_is_host = home_team in HOST_NATIONS
    away_is_host = away_team in HOST_NATIONS

    if home_is_host and away_is_host:
        return True

    return not (home_is_host or away_is_host)


def resolve_model_orientation(home_team: str, away_team: str) -> tuple[str, str, bool]:
    home_is_host = home_team in HOST_NATIONS
    away_is_host = away_team in HOST_NATIONS

    if home_is_host and away_is_host:
        return home_team, away_team, False

    if away_is_host and not home_is_host:
        return away_team, home_team, True

    return home_team, away_team, False

def normalize_team_name(name: str) -> str:
    return TEAM_NAME_MAPPING.get(name, name)

def normalize_football_data_name(name: str) -> str:
    return FOOTBALL_DATA_NAME_MAPPING.get(name, name)