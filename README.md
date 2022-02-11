# lab_1.2_map
## Goal of the Project
The goal of the project was to create a map with a couple of layers of markers, which would show:

  - location of places where the films were filmed
  - coordinates of those places
  - marker clusters, which would show the number of places in certain area

Every layer of markers may be controlled trough the layer control, which may be found in the upper right corner of the map. This project is designed for people who are keen to watch films and want to find out more about films that were filmed around their homeplace or place of interest.

## Coded functions
There is a number of functions that were coded to complete the project. All in all there are 7 functions:

``` python
main()
argumnet_parsing()
read_data()
location_identifier()
locate_place()
create_map()
calculate_distance()
```
In order to understand the way project works we need to understand what each function is responsible for.

## main()
The main function that contains the whole program. This function is responsible to trasmit data entered by user to functions

```python
def main():
    user_year, latitude, longitude, path_to_dataset = argument_parsing()
    user_coordinates = (latitude, longitude)
    dataframe = read_data(path_to_dataset, user_year)
    create_map(dataframe, user_coordinates)
```

## argumnet_parsing()
This function is responsible for parsing the inforamtion about year, when film was taken in, latitude and longitude around which 10 closest locations of filming will be found, path to film's data and returning it.

``` python
year = arguments.year
latitude = arguments.latitude
longitude = arguments.longitude
path_to_dataset = arguments.path_to_dataset

return year, latitude, longitude, path_to_dataset
```

Later on this function will be called first in the ```main()``` function:

```python
user_year, latitude, longitude, path_to_dataset = argument_parsing()
```

-- in order to assign the values it returns to the variables, which will be used in another functions.

Parsing the data into program should look loke this:

```bash
python main.py 2000 49.83826 24.02324 path_to_dataset
```

## read_data()
This function takes arguments of the path to database and year in which films were taken and returns the dataframe of films' names and coordinates they were taken in:

```python
def read_data(file, user_year):
  <...>
  dataframe = pandas.DataFrame(lines_list, columns=["Film Name", "Coordinates"])
  return dataframe
```
This function reads the file and appends the lines from it into the list:

``` python
lines_list = []

    with open(file, "r", encoding="unicode_escape") as file:  # reads file and writes info in list
        for line in file:
            lines_list.append(line.split("\t"))
```

Working with given database was rather challenging due to the variable amount of spaces and tabs between the chunks with needed information. Thus, it was important to delete unnecessary information and clear the information from the results of individual fragments of program code:

```python
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
```
Later on this function calls ```location_identifier()``` function in order to get necessary films based on year user have entered before and clear information even more (see the ```location_identifier()``` function explanation):

```python
lines_list = location_identifier(lines_list, user_year)
```

After getting list with necessary information, function finnaly creates and returns data base:

```python
dataframe = pandas.DataFrame(lines_list, columns=["Film Name", "Coordinates"])
return dataframe
```

## location_identifier()
This function takes argumnets with list of data and user's year, modifies it based on chosen user's year and returns it

```python
def location_identifier(lines_list, user_year):
  <...>
  return lines_list
```

There were two challenging things while developing this function:
  - choosing only information with year chosen by user
  - searching locations (there were some that don't exist)

The first problem was handled by creating the ```counter``` which let us effectively edit only necessary information by accessing the index of it in list:

```python
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
```

Couter increases as the necessary information is found, thus leaving the valid element in the list and letting us to work with the next element. If the element is not valid it is deleted by taking into account the index of it. There is also a try-except expression that helps to identify not valid information.

In order to solve the problem with searching the place, we needed to get place information and split it by ```,```:

```python
for i in range(len(locations_list)):  # splits the location sequence into elements
        locations_list[i] = locations_list[i].split(",")
```

-- in this way we will be able to get information about the street, town/city, state and country separately, so if we don't manage to find the street, we will look for town/city, state etc.

In order to locate the place, we call the ```locate_place()``` function, which is responsible for finding place (see the ```locate_place()``` function explanation):
```python
    for i in range(len(locations_list)):  # searches the coordinates of locations
        for j in range(len(locations_list[i])):
            place_coordinates = locate_place(locations_list[i][j])

            if place_coordinates is None:  # if location doesn't exist checks next element in location list
                continue
            else:
                lines_list[i].pop(1)  # removes location
                lines_list[i].append((place_coordinates[0], place_coordinates[1]))  # appends coordinates of location
                break
```

If the place is found the cycle breaks, if not - it continues until found

## locate_place()
This function takes the name of place, coordinates of which need to be found, and if the place is found returns the latitude and longitude of the place, else it's retuns None

```python
def locate_place(place):

    place_locator = Nominatim(user_agent="place_locator")

    try:  # if place is not found rises exception
        location = place_locator.geocode(place)
    except:
        location = None

    if location is None:  # if location exists returns coordinates
        return None
    else:
        return location.latitude, location.longitude
```

## create_map()
This function takes the dataframe and user coordinates merged in the ```main()``` function, creates the map with the zoom on user's coordinates, places markers, shows marker clusters and adds layer control.

```python
def create_map(dataframe, user_coordinates):
    <...>
    feature_group = folium.FeatureGroup(name="Films Location")
    location_feature_group = folium.FeatureGroup(name="Location Coordinates")
    <...>
    distance_dict = calculate_distance(user_coordinates, film_names_by_coordinates_dict)

    locations = list(distance_dict.keys())  # list of coordinates
    marker_cluster = MarkerCluster(locations, name="Marker Cluster")  # creates marker cluster
    marked_map.add_child(marker_cluster)  # adds marker cluster to map
    <...>
    marked_map.add_child(feature_group)  # adds feature group with film names
    marked_map.add_child(location_feature_group)  # adds feature group with location coordinates
    marked_map.add_child(folium.LayerControl())  # adds the ability to control layers
    marked_map.save('Map_1.html')  # saves map
```

This function also calls the ```calculate_distance()``` function (see ```calculate_distance()``` function description) and adds markers with film names filmed in that location.
There are also markers with film coordinates that are added in order for user to know the exact location of the town/city if it is necessary. 
In order for user to have certain control of needed information the layer control was added, so that user can decide for him/herself what he/she wants to be informed about

## calculate_distance()
This function takes values of user coordinates and location coordinates, then calcutes the distance between entered user coordinates and coordinates of where films were taken, and chooses the 10 closest to the user's one and adds them to dictionary

```python
def calculate_distance(user_coordinates, location_coordinates):
    <...>
    return distance_dict
```
The sequence of tasks this function performs is next:
1) calculates distance and appends the tuple with distance, coordinate and film name to the list
2) sorts the list of elements from the smallest to biggest by distance and chooses the smallest ones
3) creates dictionary where key is the coordinates where film was taken and value is names of films taken in those coordinates and returns it

## "for_doctest.txt" file purpose
Beside the file with program itself there is a file which was designed for doctests in the program. It is used in doctests of ```read_data``` and ```create_map``` functions:
```
>>> read_data("for_doctest.txt", 2006)
       Film Name                Coordinates
    0  #1 Single  (34.0536909, -118.242766)

>>> read_data("for_doctest.txt", 2016)
Empty DataFrame
Columns: [Film Name, Coordinates]
Index: []

>>> create_map(read_data("for_doctest.txt", 2006), (49.83826, 24.02324))
    ...
```
# Good luck exploring my project!
