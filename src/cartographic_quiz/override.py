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
           bio.death_place = "Mediterranean Sea, off the coast of Marseilles"
           bio.death_lat = 42
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
            bio.birth_place = "Kagoshima"
            bio.birth_lat = 31.5967
            bio.birth_lon = 130.5578
            bio.birth_date = "c. 1500s"

            bio.death_place = "Coimbra"
            bio.death_date = "February 1557"
            bio.death_lat = 40.2089
            bio.death_lon = -8.4191
        case "Sejong_the_Great":
            bio.birth_lat = 37.56
            bio.birth_lon = 126.99
            bio.death_lat = bio.birth_lat
            bio.death_lon = bio.birth_lon
        case "Abraham":
            # Using traditional biblical chronology / Bronze Age approximations
            bio.birth_date = "c. 1813 B.C." 
            bio.birth_lat = 30.9633
            bio.birth_lon = 46.1031
            bio.birth_place = "Ur of the Chaldees (Tell el-Muqayyar, Iraq)"

            # The Cave of the Patriarchs in Hebron
            bio.death_date = "c. 1638 B.C."
            bio.death_lat = 31.5247
            bio.death_lon = 35.1107
            bio.death_place = "Hebron, Canaan (West Bank)"

        case "Ea-nāṣir":
            # Dilmun copper trade era / Babylonian chronology
            bio.birth_date = "c. 1800 B.C."
            bio.birth_lat = 26
            bio.birth_lon = 50.2
            bio.birth_place = "Dilmun (?)"

            # The city where his house (and his complaint tablet room) was excavated
            bio.death_date = "c. 1740 B.C."
            bio.death_lat = 30.9633
            bio.death_lon = 46.1031
            bio.death_place = "Ur, Sumer (Tell el-Muqayyar, Iraq)"

        case "Zheng_He":
            bio.death_date = "c. 1433"
            bio.death_lat = 9
            bio.death_lon = 73.2
            bio.death_place = "off the coast of Calicut (Kozhikode)"

        case "Rudolf_Nureyev":
            bio.birth_place = "Trans-Siberian train near Lake Baikal"

        case "Mahomet_Weyonomon":
            bio.birth_place = "Mohegan territory, Connecticut Colony"
            bio.birth_lat = 41.4
            bio.birth_lon = -73.3

        case "Ibn_al-Haytham":
            bio.birth_date = "c. 965"

        case "Willem_Barentsz":
            bio.death_place = "Barents Sea"
            bio.death_lat = 76.8
            bio.death_lon = 64

        case "Cyrus_the_Great":
            bio.death_place = "Along the Syr Darya River basin"
            bio.death_lat = 45.0
            bio.death_lon = 64.0

        case "Theodoric_the_Great":
            bio.birth_place = "Carnuntum"
            bio.birth_lat = 48.1133
            bio.birth_lon = 16.8614

        case "Sergei_Rachmaninoff":
            bio.birth_lat = 57.916
            bio.birth_lon = 31.750


        case "Tupaia_(navigator)":
            bio.birth_lon = 360 - 151.44

        case "Gaiseric":
            bio.birth_place = "Near Lake Balaton"

        case "Muhammad_Ali_of_Egypt":
            bio.birth_lat = 41.1
            bio.birth_lon = 20

        case _:
            matched = False

    if verbose and matched:
        print(f"Matched and overridden: {name}")