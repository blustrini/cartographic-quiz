from .biography import BiographyData

def override_biography(bio: BiographyData | None, verbose: bool) -> None:
    if bio is None:
        return
    name = bio.formatted_name

    matched = True
    match name:
        case "Antoine_de_Saint-Exupéry":
           bio.death_lat = 40
           bio.death_lon = 5.4
        case _:
            matched = False

    if verbose and matched:
        print(f"Matched and overridden: {name}")