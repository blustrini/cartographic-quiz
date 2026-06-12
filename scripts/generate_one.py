from cartographic_quiz import __main__ as carto_main

def main(name: str):
    rounds = carto_main._build_round_profiles([name], force_rescrape_all=True, force_rescrape_bad=True)

    print(rounds)
    

if __name__ == "__main__":
    name = "Joan of Arc"
    main(name)