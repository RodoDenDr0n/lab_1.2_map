"""FILM LOCATIONS"""
import pandas
import argparse
import folium
from geopy.geocoders import Nominatim
import re
from geopy.distance import geodesic
from folium.plugins import MarkerCluster


def argument_parsing():
    """
    This function parses year, latitude, longitude and path to dataset
    """
    parser = argparse.ArgumentParser(description="Parse year, latitude, longitude and way to file")

    parser.add_argument("year", type=int, help="Year when film was taken")
    parser.add_argument("latitude", type=float, help="Latitude of user's coordinate")
    parser.add_argument("longitude", type=float, help="Longitude of user's coordinate")
    parser.add_argument("path_to_dataset", type=str, help="Path to dataset")

    arguments = parser.parse_args()

    year = arguments.year
    latitude = arguments.latitude
    longitude = arguments.longitude
    path_to_dataset = arguments.path_to_dataset

    return year, latitude, longitude, path_to_dataset


def read_data(file, user_year):
    """
    This function reads data from file, chooses films that were filmed in certain year
    and turns them into the dataframe

    >>> read_data("for_doctest.txt", 2006)
       Film Name                Coordinates
    0  #1 Single  (34.0536909, -118.242766)
    >>> read_data("for_doctest.txt", 2016)
    Empty DataFrame
    Columns: [Film Name, Coordinates]
    Index: []
    """
    lines_list = []

    with open(file, "r", encoding="unicode_escape") as file:  # reads file and writes info in list
        for line in file:
            lines_list.append(line.split("\t"))

    for i in range(14):  # removes first 14 lines that do not contain necessary information
        lines_list.pop(0)

    lines_list.pop(len(lines_list)-1)  # removes last line that does not contain necessary information

    for i in range(len(lines_list)):  # removes "\n" from line and whitespaces from list
        lines_list[i][-1] = lines_list[i][-1].rstrip()
        space_number = lines_list[i].count("")
        for j in range(space_number):
            lines_list[i].remove("")

        if len(lines_list[i]) == 3:  # removes info given in brackets after the location
            lines_list[i].pop(2)

    lines_list = location_identifier(lines_list, user_year)

    # creates dataframe with name of the film, country it was filmed in and coordinates
    dataframe = pandas.DataFrame(lines_list, columns=["Film Name", "Coordinates"])
    return dataframe


def location_identifier(lines_list, user_year):
    """
    This function selects only needed information from the lines_list by year,
    edits the film name by removing the year it was taken in
    changes lines_list by replacing location with coordinates of this location

    >>> location_identifier([['"#1 Single" (2006)', 'Los Angeles, California, USA']], 2006)
    [['#1 Single', (34.0536909, -118.242766)]]
    """
    locations_list = []
    counter = 0
    for i in range(len(lines_list)):
        # identifies the year in which film was taken
        try:
            year = int(re.findall("\(\d\d\d\d\)", lines_list[counter][0])[0].replace("(", "").replace(")", ""))

            if year == user_year:  # checks if film's year is the same as chosen by user
                film_name = re.findall("\"(.*?)\"", lines_list[counter][0])[0]  # identifies film's name
                lines_list[counter][0] = film_name  # changes first element in list into film's name
                locations_list.append(lines_list[counter][1])
                counter += 1
            else:
                lines_list.pop(counter)

        except IndexError:
            lines_list.pop(counter)

    for i in range(len(locations_list)):  # splits the location sequence into elements
        locations_list[i] = locations_list[i].split(",")

    for i in range(len(locations_list)):  # searches the coordinates of locations
        for j in range(len(locations_list[i])):
            place_coordinates = locate_place(locations_list[i][j])

            if place_coordinates is None:  # if location doesn't exist checks next element in location list
                continue
            else:
                lines_list[i].pop(1)  # removes location
                lines_list[i].append((place_coordinates[0], place_coordinates[1]))  # appends coordinates of location
                break

    return lines_list


def locate_place(place):
    """
    This function locates the place and
    returns coordinates of it

    >>> locate_place('Los Angeles')
    (34.0536909, -118.242766)
    >>> locate_place('Lviv')
    (49.841952, 24.0315921)
    >>> locate_place('Kyiv')
    (50.4500336, 30.5241361)
    >>> locate_place('London')
    (51.5073219, -0.1276474)
    """
    place_locator = Nominatim(user_agent="place_locator")

    try:  # if place is not found rises exception
        location = place_locator.geocode(place)
    except:
        location = None

    if location is None:  # if location exists returns coordinates
        return None
    else:
        return location.latitude, location.longitude


def calculate_distance(user_coordinates, location_coordinates):
    """
    This function takes the values of user's coordinates and location coordinates,
    calculates the distance between user's coordinates and location coordinates,
    chooses 10 closest locations to the user's coordinates
    and returns dictionary with films by coordinates where they were taken

    >>> calculate_distance((49.83826, 24.02324), {(34.0536909, -118.242766):['Doctest']})
    {(34.0536909, -118.242766): ['Doctest']}
    """
    distance_list = []
    distance_dict = {}

    for key, element in location_coordinates.items():

        try:
            distance = geodesic(user_coordinates, key).kilometers  # calculates distance
            distance_list.append((distance, (key, element)))  # appends distance, coordinate and film name tuple
        except ValueError:
            continue

    distance_list.sort(key=lambda x: x[0])  # sorts by distance
    del distance_list[10:]  # takes first 10 elements

    for i in range(len(distance_list)):  # creates dictionary --> key:coordinates, value:film_names
        coordinates = distance_list[i][1][0]
        films = distance_list[i][1][1]
        temporary_dictionary = {}
        temporary_dictionary.setdefault(coordinates, films)
        distance_dict.update(temporary_dictionary)

    return distance_dict


def create_map(dataframe, user_coordinates):
    """
    This function gets information about film names and coordinates,
    creates map with 3 layers:

        first - film names
        second - location coordinates
        third - cluster of markers

    that may be controlled

    >>> create_map(read_data("for_doctest.txt", 2006), (49.83826, 24.02324))
    ...
    """
    # creates map with zoom on users coordinates
    marked_map = folium.Map(tiles="Stamen Terrain",
                            location=[user_coordinates[0],
                                      user_coordinates[1]],
                            zoom_start=5)

    # creates feature group with film names
    feature_group = folium.FeatureGroup(name="Films Location")
    # creates feature group with location coordinates
    location_feature_group = folium.FeatureGroup(name="Location Coordinates")

    film_name = dataframe["Film Name"]  # gets information about film names from dataframe
    coordinates = dataframe["Coordinates"]  # gets information about location coordinates from dataframe

    # creates list with tuples with film name and location coordinates
    film_names_by_coordinates = list(zip(film_name, coordinates))
    film_names_by_coordinates_dict = {}

    for element in film_names_by_coordinates:

        if element[1] in list(film_names_by_coordinates_dict.keys()):  # if coordinates are in dictionary keys
            film_names_by_coordinates_dict[element[1]].append(element[0])  # appends film name to values
        else:  # else adds key and value to dictionary
            film_names_by_coordinates_dict.setdefault(element[1], [])
            film_names_by_coordinates_dict[element[1]].append(element[0])

    # create dictionary based on distance
    distance_dict = calculate_distance(user_coordinates, film_names_by_coordinates_dict)

    locations = list(distance_dict.keys())  # list of coordinates
    marker_cluster = MarkerCluster(locations, name="Marker Cluster")  # creates marker cluster
    marked_map.add_child(marker_cluster)  # adds marker cluster to map

    for coordinates, films in distance_dict.items():
        films = ",\n".join(films)  # turns list to text

        try:
            # adds icons with film names
            feature_group.add_child(folium.Marker(location=[coordinates[0], coordinates[1]],
                                                  popup="Фільми, що знімали в локації:\n" + films,
                                                  icon=folium.Icon()))
            # adds icons with location coordinates
            location_feature_group.add_child(folium.Marker(location=[coordinates[0], coordinates[1]],
                                                           popup="Координати локації:\n"
                                                           + str(f"{coordinates[0]}, {coordinates[1]}"),
                                                           icon=folium.Icon(color="red")))
        except ValueError:
            continue

    marked_map.add_child(feature_group)  # adds feature group with film names
    marked_map.add_child(location_feature_group)  # adds feature group with location coordinates
    marked_map.add_child(folium.LayerControl())  # adds the ability to control layers
    marked_map.save('Map_1.html')  # saves map


def main():
    """
    The main function which is responsible for identifying
    user year, latitude, longitude, path to dataset
    """
    user_year, latitude, longitude, path_to_dataset = argument_parsing()
    user_coordinates = (latitude, longitude)
    dataframe = read_data(path_to_dataset, user_year)
    create_map(dataframe, user_coordinates)


main()
