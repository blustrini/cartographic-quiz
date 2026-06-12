from .models import BiographyData

def override_biography(bio: BiographyData | None, verbose: bool) -> None:
    if bio is None:
        return
    name = bio.formatted_name

    print(name)

    matched = True
    match name:
        case "Antoine_de_Saint-Exupéry":
           bio.death_lat = 40
           bio.death_lon = 5.4
        case "Josephus":
            bio.death_lat = 41.9028
            bio.death_lon = 12.4964
            bio.death_place = "Rome"
        case _:
            matched = False

    if verbose and matched:
        print(f"Matched and overridden: {name}")