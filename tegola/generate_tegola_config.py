import sys
import yaml
import toml
from collections import defaultdict

default_map = "openinframap"

map_layers = defaultdict(list)

if len(sys.argv) != 5:
    print("Usage:", sys.argv[0], "<tegola.yml> <layers.yml>")
    sys.exit(1)

with open(sys.argv[1], "r") as f:
    conf = yaml.load(f, Loader=yaml.SafeLoader)

# add layers into the providers's first element of conf
conf["providers"][0]["layers"] = list()
# add maps into conf
conf["maps"] = list()
provider_name = conf["providers"][0]["name"]

with open(sys.argv[2], "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)


def build_field(name, val):
    nl_char = "\n"
    if ":" in name:
        name = '"' + name + '"'

    if val is None:
        return name
    else:
        return f"{val.strip().replace(nl_char,'')} AS {name}"


def get_field_sets(names):
    data = []
    for name in names:
        data += config["field_sets"][name]
    return data


def build_sql(data):
    nl_char = "\n"
    sql = "SELECT "

    geometry_type = data.get("geometry_type")
    if geometry_type == "LineString":
        print("geometry type is line string")

    # Note on ID fields:
    # The OSM ID generated by imposm3 can be negative (for relation IDs), however
    # MVT feature IDs cannot be negative, and tegola/mvt_postgis seems to enforce this by
    # coalescing negative IDs to null, although no errors are generated.
    #
    # The ID field is not required by the MVT spec, but it does seem to be required by
    # tegola/mvt_postgis.
    #
    # Here we alias the ID for use as the feature ID, and also include the ID as a
    # separate field, which can be negative.

    if "id_field" in data and data["id_field"] not in [
        f["name"] for f in data.get("fields", [])
    ]:
        sql += data["id_field"] + " AS mvt_id_field, " + data["id_field"] + ", "
   
    fields = data.get("fields", [])
    fields_sets = get_field_sets(data.get("field_sets", []))
    all_fields = fields + fields_sets

    # fields = data.get("fields", [])
    # fields_sets = get_field_sets(data.get("field_sets", []))
    # all_fields = fields + fields_sets

    sql += ", ".join(
        build_field(f["name"], f.get("sql"))
        for f in get_field_sets(data.get("field_sets", [])) + data.get("fields", [])
    )
    sql += f" FROM {data['from']}"
    if "where" in data:
        sql += f" WHERE {data['where'].strip().replace(nl_char,'')}"
    if "order_by" in data:
        sql += f" ORDER BY {data['order_by'].strip().replace(nl_char,'')}"
    return sql


# Iterate through each layer in the config(layers.yml)
for layer in config["layers"]:
    # Get the map name from the layer, no this attribute for now,use default_map.
    layer_maps = layer.get("map")
    # If there is no map name, set the map name to the default map
    if "map" not in layer:
        layer_maps = [default_map]

    # Iterate through each map name
    for map_name in layer_maps:
        # Add the map name to the map layers
        map_layers[map_name].append(
            {
                # Set the min zoom to the layer's min zoom, or 2 if it is not set
                "min_zoom": layer.get("min_zoom", 2),
                # Set the max zoom to the layer's max zoom, or 17 if it is not set
                "max_zoom": layer.get("max_zoom", 17),
                # Set the provider layer to the provider name and layer name
                "provider_layer": provider_name + "." + layer["name"],
            }
        )

    # Create a layer config
    layer_config = {
        # Set the name to the layer name
        "name": layer["name"],
        # Set the sql to the built sql
        "sql": build_sql(layer),
        # Set the geometry type to the layer's geometry type
        "geometry_type": layer["geometry_type"],
    }

    # If the layer has an id field, set the id field name to mvt_id_field
    if layer["id_field"]:
        layer_config["id_fieldname"] = "mvt_id_field"

    # Add the layer config to the conf
    conf["providers"][0]["layers"].append(layer_config)


for name, layers in map_layers.items():
    conf["maps"].append({"name": name, "layers": layers, "center": [0.0, 0.0, 2.0]})

print(toml.dumps(conf))
