from .models import BiographyData

def override_biography(bio: BiographyData | None, verbose: bool) -> None:
    if bio is None:
        return
    name = bio.formatted_name

    if verbose:
        print(f"Matching name: {name}")

    matched = True
    match name:
        case "Antoine_de_Saint-Exupéry":
           bio.death_lat = 40
           bio.death_lon = 5.4
        case "Josephus":
            bio.death_lat = 41.9028
            bio.death_lon = 12.4964
            bio.death_place = "Rome"
        case "John_Cabot":
            bio.death_date = "c. 1499"
            bio.death_lat = 50 
            bio.death_lon = -35
            bio.death_place = "North Atlantic"
        case "Eugène_Eyraud":
            bio.birth_date = "1820"
            bio.birth_lat = 44.6819
            bio.birth_lon = 6.0764
            bio.birth_place = "Saint-Bonnet-en-Champsaur"
            bio.death_date = "23 August 1868"
            bio.death_lat = -27.12
            bio.death_lon = -109.35
            bio.death_place = "Hanga Roa (Easter Island)"
        case "Eden_(2024_film)": # Baroness Eloise Wagner de Bosquet
            bio.birth_date = "c. 1900"
            bio.birth_place = "Vienna"
            bio.birth_lat = 48.2083
            bio.birth_lon= 16.3725

            bio.death_date = "March 1934"
            bio.death_place = "Floreana Island"
            bio.death_lat = -1.2975
            bio.death_lon = -90.434167
        case "Gudit":
            bio.birth_date = "c. 940 A.D."
            bio.death_place = bio.birth_place
            bio.death_lat = bio.birth_lat
            bio.death_lon = bio.birth_lon
        case "Baldwin_I_of_Jerusalem":
            bio.birth_place = "Lower Lorraine"
            bio.birth_lat = 50.8503
            bio.birth_lon = 4.3517
        case "Glenn_Miller":
            bio.death_place = "English Channel"
            bio.death_lat = 50.2
            bio.death_lon = 0.0
        case "Attila":
            bio.birth_place = "Pannonia (?)"
            bio.birth_lat = 47.45
            bio.birth_lon = 18.6

            bio.death_place = "Alföld (Great Hungarian Plain) (?)"
            bio.death_lat = 47.5
            bio.death_lon = 19.9167
        case "Thales_of_Miletus":
            bio.death_place = bio.birth_place
            bio.death_lat = bio.birth_lat
            bio.death_lon = bio.birth_lon
        case "Zeno_of_Elea":
            bio.death_place = "Syracuse"
        case "Saint_Patrick":
            bio.birth_date = "c. 385"
            bio.birth_lat = 54.2
            bio.birth_lon = -3.0
            bio.birth_place = "(Northwestern) Roman Britain (?)"
            bio.death_date = "17th March c. 461"
            bio.death_lat = 54.325
            bio.death_lon = -5.717
            bio.death_place = "Saul"
        case "Ettore_Majorana":
            bio.death_place = "Tyrrhenian Sea"
            bio.death_date = "25 March 1938 (?)"
            bio.death_lat = 39.5
            bio.death_lon = 13.5
        case "Valerian_(emperor)":
            bio.birth_place = "near Rome"
            bio.birth_lat = 41.8967
            bio.birth_lon = 12.4822
        case "Bernardo_the_Japanese":
            print(bio)
            bio.birth_place = "Kagoshima"
            bio.birth_lat = 31.5967
            bio.birth_lon = 130.5578
            bio.birth_date = "c. 1500s"

            bio.death_place = "Coimbra"
            bio.death_date = "February 1557"
            bio.death_lat = 40.2089
            bio.death_lon = -8.4191

        case _:
            matched = False

    if verbose and matched:
        print(f"Matched and overridden: {name}")