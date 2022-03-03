"""
rapid_dem
"""

# ============ Packages ================
import os
import subprocess
import sys
import csv
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd 
import seaborn as sns
from collections import defaultdict

import grass.script as gs
import grass.jupyter as gj
# ============ Functions ===============


def u16bitTou8bit(band, output):
    """
    Cover 16-bit PlanetScope red, blue, green, nir band to 8-bit

    Parameters
    ==========
    band (str): Name of raster containing PlantScope band.
    output (str): Name of output raster.
    
    Returns
    =======
    output
    
    """
    univar = gs.parse_command("r.univar", map=band, flags="ge")
    min_val = float(univar["min"])
    max_val = float(univar["max"])
    gs.mapcalc(f'{output} = (({band} - {min_val}) * 255) / ({max_val} - {min_val}) + 0')
    gs.run_command("r.colors", map=output, color="grey255", flags="e")
    return output

def binary_change(before, after, binary_change="binary_change", binary_change_mask="binary_change_mask", thres=-2.5):
    """
    Calculates a binary change mask between two images with a thershold set at -2.5 times the std dev.
    
    Parameters
    ==========
    before (str): A string name of the before image raster.
    after (str): A string name of the after image raster.
    binary_change (str): (optional) A string name of the output binary change raster.
    binary_change_mask (str): (optional) A string name of the output binary change mask.
    thres (float): (optional) Value used to scale the change threshold by multiplying the standard deviation.
    
    Returns
    =======
    binary_change, binary_change_mask
    """
    gs.mapcalc(f"{binary_change} = {before} - {after}")
    gs.run_command("r.colors", map=binary_change, color="differences", flags="")
    univar = gs.parse_command("r.univar", map=binary_change, flags="ge")
    mean = float(univar["mean"])
    print(f"Mean: {mean}")
    stddev = float(univar["stddev"])
    print(f"Std: {stddev}")
    threshold = mean + (stddev * thres) if thres < 0 else mean - (stddev * thres)
    print(f"Change Threshold: {threshold}")
    gs.mapcalc(f"{binary_change_mask} = if({binary_change} <= {threshold}, 1,null())")
    
def calc_bsi(red, green, blue, nir, output):
    """
    Calculate bare soils index.
    
    Parameters
    ==========
    red (str): Name of red band raster.
    green (str): Name of green band raster.
    blue (str): Name of blue band raster.
    nir (str): Name of near-infrared band raster.
    output: Name of output BSI raster.
    
    Returns
    =======
    output
    """
    gs.mapcalc(f"{output} = (({red} + {green}) - ({red} + {blue}))/ (({nir} + {green}) + ({red} + {blue})) * 100 + 100")
    return output
    
def calc_ndci(nir, green, output):
    """
    Calculates Normalized Concrete Index.
    
    Parameters
    ==========
    nir (str): Name of near infrared band
    green (str): Name of green band
    output (str): Name of output NDCI raster
    
    Returns
    =======
    output
    """
    gs.mapcalc(f"{output} = ({nir}-{green})/({nir} + {green})")
    return output
    

def zscore(rast, output, log=False):
    """
    Calculates the zscore of an input raster.
    
    Parameters
    ==========
    rast (str): Name of the input raster.
    output (str): Name of the output raster.
    log (bool): (optional) Set true if the data is skewed and requires log normalization.
    
    Returns
    =======
    output
    
    
    """
    if log:
        tmp_log = "tmp_log"
        gs.mapcalc(f"{tmp_log} = log({rast})")
        univar = gs.parse_command("r.univar", map=tmp_log, flags="ge")
        mean = float(univar["mean"])
        stddev = float(univar["stddev"])
        gs.mapcalc(f"{output} = ({tmp_log} - {mean}) / {stddev}")
    else:
        univar = gs.parse_command("r.univar", map=rast, flags="ge")
        mean = float(univar["mean"])
        stddev = float(univar["stddev"])
        gs.mapcalc(f"{output} = ({rast} - {mean}) / {stddev}")
        
    return output


"""
Display Functions
=================

"""

def shadedRelief(elevation, relief, output, shade_only=False):
    """
    Add shaded releif elevation data
    @param elevation : string : Name of existing elevation raster
    @param relief : string : Name of newly created relief raster
    @param output : string: Name of shaded relief raster
    @param shade_only : Bool : Applied shading to exisiting releif map where elevation works as a color
    """
    if shade_only:
        gs.run_command("r.shade", shade=relief, color=elevation, output=output, overwrite=True)
    else:
        gs.run_command("r.relief", input=elevation, output=relief, overwrite=True)
        gs.run_command("r.shade", shade=relief, color=elevation, output=output, overwrite=True)
        
def generate_elevation_figure(elev, filename):
    """
    Generates a shade png image of an elevation (DTM, DSM)
    @param elev : string : Name of raster
    @param filename: string: Name of file
    """
    relief = f"{elev}_relief"
    shaded_relief = f"{elev}_shaded_relief"
    # shadedRelief(elevation=elev,relief=relief, output=shaded_relief)
    output = f"output/{filename}.png"
    print(f"Image Save Location: {output}")
    elev_map = gj.GrassRenderer(height=900, width=1400, filename=output)
    elev_map.d_erase()
    elev_map.d_rast(map=shaded_relief)
    elev_map.d_legend(raster=elev, at=(14,50,10,12), title="Elevation (m)",font="FreeSans", title_fontsize=18, fontsize=16, flags="tb", border_color='none')
    elev_map.d_barscale(at=(8,10,10,12), units="meters", flags="n",font="FreeSans", fontsize=24)
    elev_map.d_grid(size="00:58:40", flags="dw", width=1, color="black",text_color="black")

    return elev_map.show()


def generate_uas_elevation_figures(elev, filename):
    """
    Generates a shade png image of an elevation (DTM, DSM)
    @param elev : string : Name of raster
    @param filename: string: Name of file
    """
    relief = f"{elev}_relief"
    shaded_relief = f"{elev}_shaded_relief"
    shadedRelief(elevation=elev,relief=relief, output=shaded_relief)
    output = f"output/{filename}.png"
    print(f"Image Save Location: {output}")
    elev_map = gj.GrassRenderer(height=900, width=900, filename=output)
    elev_map.d_erase()
    elev_map.d_rast(map=shaded_relief)
    # elev_map.d_vect(map="fenton_pq_boundary", fill_color="none", color="white", width="1", legend_label="Fenton (White Area)")
    elev_map.d_legend(raster=elev, at=(70,90,67,70), title="Elevation (m)",font="FreeSans", title_fontsize=18, fontsize=16, flags="tb", border_color='none')
    elev_map.d_barscale(at=(16,7), units="meters", flags="n",font="FreeSans", fontsize=24)
    elev_map.d_grid(size="00:0:56", flags="dw", width=1, color="black",text_color="black",fontsize=12)

    return elev_map.show()


def generate_fusion_elevation_figure(elev, filename):
    """
    Generates a shade png image of an elevation (DTM, DSM)
    @param elev : string : Name of raster
    @param filename: string: Name of file
    """
    relief = f"{elev}_relief"
    shaded_relief = f"{elev}_shaded_relief"
    shadedRelief(elevation=elev,relief=relief, output=shaded_relief)
    output = f"output/{filename}.png"
    print(f"Image Save Location: {output}")
    elev_map = gj.GrassRenderer(height=900, width=1400, filename=output)
    elev_map.d_erase()
    elev_map.d_rast(map=shaded_relief)
    elev_map.d_legend(raster=elev, at=(5,30,3,5),
                      title="Elevation (m)",font="FreeSans", border_color="none",
                      title_fontsize=16, fontsize=14, 
                      flags="bt")
    elev_map.d_barscale(at=(18,7), units="meters", flags="n",font="FreeSans")
    elev_map.d_grid(size="00:00:58", flags="dw", width=1, color="black",text_color="black",fontsize=16)

    return elev_map.show()

def generate_ortho_figure(ortho, filename):
    output = f"output/{filename}.png"
    print(f"Image Save Location: {output}")
    ortho_composite_map = gj.GrassRenderer(height=900, width=900,filename=output)
    ortho_composite_map.d_erase()
    ortho_composite_map.d_rast(map=ortho)
    ortho_composite_map.d_barscale(at=(16,7), units="meters", flags="n",font="FreeSans", fontsize=24)
    ortho_composite_map.d_grid(size="00:0:56", flags="dw", width=1, color="black",text_color="black",fontsize=12)
    return ortho_composite_map.show()

def generate_uas_footprint(elev, output, overwrite=False):
    """
    Creates a footprint of the UAS flight area
    """
    gs.mapcalc(f"{output} = if(isnull({elev}), null(), 1)")
    gs.run_command("r.to.vect", input=output, output=output, type="area", overwrite=overwrite)
    
def create_flight_figure(input_1,title_1, input_2, title_2, input_3, title_3, filename):
    from PIL import Image

    fig = plt.figure(figsize=(25, 30))
    
    ax = fig.add_subplot(1, 3, 1)
    fig.subplots_adjust(hspace=0, wspace=0.1)
    ax.set_axis_off()
    img1 = Image.open(f"output/{input_1}.png")
    imgplot = plt.imshow(img1)
    ax.set_title(title_1,{"fontsize":24, "fontweight":"bold"})

    ax = fig.add_subplot(1, 3, 2)
    ax.set_axis_off()
    img2 = Image.open(f"output/{input_2}.png")
    imgplot = plt.imshow(img2)
    ax.set_title(title_2,{"fontsize":24, "fontweight":"bold"})

    ax = fig.add_subplot(1, 3, 3)
    ax.set_axis_off()

    img3 = Image.open(f"output/{input_3}.png")
    imgplot = plt.imshow(img3)
    # imgplot.set_clim(0.0, 0.7)
    ax.set_title(title_3,{"fontsize":24, "fontweight":"bold"})
    
    output = f"output/{filename}.png"
    print(f"Image Save Location: {output}")
    
    plt.tight_layout()
    return plt.savefig(output,bbox_inches='tight',dpi=300)
    
    
"""
Priority Queue Functions
=================
"""

### Test to generate detailed land change transition map
def land_change_action(output):
    """
    X0 - primary class
    XF0 - New Feature
    X0F - Demolision
    X07 - Flooding
    X00F - Noise 
    
    10 - Roadway ( Base Class)
    20 - Building
    30 - Developed
    40 - Barren 
    50 - Grass
    60 - Forest
    70 - Water
    
    #
    0 - Static Feature
    1 - New Road
    2 - New Building
    3 - New Developed 
    4 - New Pond
    5 - Dug Up Road Road
    6 - Demolished Building
    7 - Demolished Developed
    8 - Forest Clearing
    """
   
    land_use_change = {
        ### Base Classes
        "road to road": {"class": 10, "label": "Roadway", "color":"217:146:130","action":"","priority": 0},
        "building to building": {"class": 20, "label": "Building", "color":"171:0:0","action":"","priority": 0}, # 7 # Building
        "developed to developed": {"class": 30, "label": "Developed", "color":"222:197:197","action":"","priority": 0}, # Developed
        "barren to barren": {"class": 40, "label": "Barren","color":"179:172:159","action":"","priority": 0}, # Barren
        "grass to grass": {"class": 50, "label": "Grass","color":"133:199:126","action":"","priority": 0}, # Grass
        "forest to forest":{"class": 60, "label": "Forest","color":"104:171:95","action":"","priority": 0}, # Forest
        "water to water": {"class": 70, "label": "Water","color":"70:107:159","action":"","priority": 0},
        
        # Added Features
        
        # New Road (Purple)
        "developed to road": {"class": 310, "label": "New Road", "color":"45:0:75", "action": 1, "priority": 3}, # New Road
        "barren to road": {"class": 410, "label": "New Road", "color": "45:0:75", "action": 1, "priority": 3}, # New Roadway
        
        # New Building (Teal)
        "developed to building": {"class": 320, "label": "New Building", "color":"1:102:94", "action": 2, "priority": 7}, # New Building
        "barren to building": {"class": 420, "label": "New Building","color": "1:102:94", "action": 2, "priority": 7}, # New Building
        "grass to building": {"class": 520, "label": "New Building", "color":"1:102:94", "action": 2, "priority": 7}, # New Building
       
        # New Developed Area (Light Purple
        "barren to developed": {"class": 430,"label": "New Developed Area", "color":"128:115:172", "action": 3, "priority": 5}, # New Developed Area
        "grass to developed": {"class": 530, "label": "New Developed Area", "color":"128:115:172", "action": 3, "priority": 5}, # New Developed Area (Grass to Developed)

        # New Pond (Light Blue)
        "barren to water": {"class": 470, "label": "New Pond/Flooding", "color":"166:206:227", "action": 4, "priority": 0}, # New Pond/Flooding
        
        
        ### Removed Features ()
        "road to barren": {"class": 104, "label": "Dug Up Roadway", "color":"179:88:6", "action": 5, "priority":4}, # Dark Orange Brown
        "building to barren": {"class": 204, "label": "Demolished Building", "color": "224:130:20", "action": 6, "priority": 7}, # Orange Brown
        "developed to barren": {"class": 304, "label": "Demolished Developed", "color":"253:184:99", "action": 7, "priority": 7}, # Light Orange Brown
        "forest to developed": {"class": 630, "label": "Forest Clearing", "color":"197:27:125", "action": 8, "priority": 7}, # Dark Pink
        "forest to barren": {"class": 640, "label": "Forest Clearing", "color":"197:27:125","action":8, "priority": 7}, # (Seasonal forest to Road)
        
        # Flooded Features
        "road to water": {"class": 107, "label": "Flooded Roadway", "color":"","action":"", "priority":0}, # 
        "building to water": {"class": 207, "label": "Flooded Building", "color":"","action":"", "priority": 0}, # 10, # 
        "developed to water": {"class": 307, "label": "Flooded Developed", "color":"","action":"", "priority": 0}, # Flooding
        "grass to water":{"class": 507, "label": "Flooded Field", "color":"","action":"", "priority": 0},# Flooded Field
  
        #Noise
        "road to building": {"class": 1002, "label": "Noise (Roadway to Building)", "color":"", "action": "","priority":1}, # High Priority queue (7)...same not sure why this is a 7
        "road to grass": {"class": 1005, "label": "Noise (Road to Grass)", "color":"","action":"","priority":1},  
        "road to forest": {"class": 1006, "label": "Noise (Road to Forest)", "color":"","action":"", "priority":1},
        "road to developed": {"class": 1003, "label": "Noise (Road to Developed)", "color":"","action":"", "priority": 4},
           
        "building to road": {"class": 20001, "label": "Noise (Building to Road)", "color":"","action":"", "priority":1}, 
        "building to forest": {"class": 2002, "label": "Noise (Building to Forest)", "color":"","action":"", "priority": 3},  
        "building to developed": {"class": 2003, "label": "Noise (Building to Developed)", "color":"","action":"", "priority": 5},  
        "building to grass": {"class": 2005, "label": "Noise (Building to Grass)", "color":"","action":"", "priority": 3}, 
        
        "developed to grass": {"class": 3005, "label": "Noise ( Developed to Grass)", "color":"","action":"","priority": 3}, # Reclaimed Grass
        "developed to forest": {"class": 3006, "label": "Noise (Developed to Forest)", "color":"","action":"","priority": 3}, # Reclaimed Forest
        
        "barren to grass": {"class": 4005, "label": "Noise (Barren to Grass)", "color":"","action":"", "priority": 2}, 
        "barren to forest": {"class": 4006, "label": "Noise (Barren to Forest)", "color":"","action":"", "priority": 2},
        
        "grass to road": {"class": 5001, "label": " Noise (Grass to Road)", "color":"","action":"", "priority": 3}, 
        "grass to barren": {"class": 5004, "label": " Noise (Field/Barren)", "color":"","action":"", "priority": 3}, 
        "grass to forest": {"class": 5006, "label": "Noise (Grass to Forest)", "color":"","action":"", "priority": 3}, 
        
        "forest to road": {"class": 6001, "label": "Nosie (Seasonal forest to Road)", "color":"","action":"","priority": 3}, 
        "forest to building": {"class": 6002, "label": "Nosie (Seasonal forest to Road)", "color":"", "action": "", "priority": 1}, # I dont know why I made this a 7,might be an error..
       
        "forest to grass": {"class": 6005, "label": "Noise (Forest to Grass)", "color":"","action":"","priority": 3}, 
        "forest to water": {"class": 6007, "label": "Noise (Forest to Water)", "color":"","action":"", "priority": 0},
       
        "water to road": {"class": 7001, "label": "Noise (Water to Road)", "color":"","action":"", "priority": 0},  
        "water to building": {"class": 7002, "label": "Noise (Water to Building)", "color":"","action":"", "priority": 0},  
        "water to developed": {"class": 7003, "label": "Noise (Water to Developed)", "color":"","action":"", "priority": 0},  
        "water to barren": {"class": 7004, "label": "Noise (Water to Barren)", "color":"","action":"", "priority": 0}, 
        "water to grass": {"class": 7005, "label": "Noise (Water to Grass)", "color":"","action":"", "priority": 0},  
        "water to forest": {"class": 7006, "label": "Noise (Water to Forest)", "color":"","action":"", "priority": 0},  
        
        
    }
    
    # Create Color Table
    with open("grass_config/land_change_action_colors.txt","w") as f:
        for k, feature in land_use_change.items():
            klass = feature['class']
            kolor = feature['color']
            if kolor != "":
                print(f"{klass} {kolor}", file=f)  
                
        print("nv 255:255:255", file=f)
        print("default 255:255:255", file=f)
        
    # Create Reclass Tabel
    with open("grass_config/land_change_reclass.txt","w") as f:
        for k, feature in land_use_change.items():
            klass = feature['class']
            label = feature['label']
            if klass and label != "":
                print(f"{klass} = {klass} {label}", file=f)  
                
        print("* = NULL", file=f)
    
    # Create Reclass Tabel
    with open("grass_config/land_change_action_reclass.txt","w") as f:
        for k, feature in land_use_change.items():
            klass = feature['class']
            aklass = feature['action']
            label = feature['label']
            if klass and aklass and label != "":
                print(f"{klass} = {aklass} {label}", file=f)  
                
        print("* = NULL", file=f)
        
    with open("grass_config/land_change_basic_action_colors.txt","w") as f:
        for k, feature in land_use_change.items():
            klass = feature['action']
            kolor = feature['color']
            if kolor and klass != "":
                print(f"{klass} {kolor}", file=f)  
                
        print("nv 255:255:255", file=f)
        print("default 255:255:255", file=f)
        
    with open("grass_config/land_change_zonal_action_reclass.txt","w") as f:
        for k, feature in land_use_change.items():
            klass = feature['class']
            aklass = feature['action']
            label = feature['label']
            if klass and aklass and label != "":
                print(f"{aklass} = {aklass} {label}", file=f)  
                
        print("* = NULL", file=f)
    
    
    def expression_builder(from_val, to_val, priority):
            return f"if(classified_before_30m_recl == {from_val} && classified_after_30m_recl == {to_val}, {priority}," # if({new_expression}))"
    
   
    class_list = range(0,7)
    classnames = ["road", "building", "barren", "forest", "grass", "water", "developed"]
    expression = ""
    closing = ""
    for from_class in class_list:
        for to_class in class_list:
            k = f"{from_class} to {to_class}"
            change_key = f"{classnames[from_class]} to {classnames[to_class]}"
            change_dict = land_use_change[change_key]
            change_value = change_dict['class']
            expression += expression_builder(from_class,to_class,change_value)
            closing += ")"
    expression+= "0"         
    expression+= closing
    
    gs.mapcalc(f"{output} = {expression}")
    gs.run_command("r.reclass", input=output, rules="grass_config/land_change_reclass.txt", title="Land Change Classes",output="land_change_30m")
    gs.run_command("r.colors", map="land_change_30m", rules="grass_config/land_change_action_colors.txt")
    
    gs.run_command("r.reclass", input=output, rules="grass_config/land_change_action_reclass.txt", title="Land Change Actions",output="land_change_basic_actions_30m")
    gs.run_command("r.colors", map="land_change_basic_actions_30m", rules="grass_config/land_change_basic_action_colors.txt")


def priority_change_calc(before_landcover, after_landcover, output):
    """
    Maps Thematic Land Cover Maps into the priority change map.
    
    Parameters
    ==========
    before_landcover (str): Before land cover input raster.
    after_landcover (str): After land cover input raster.
    output (str): Priority Queue Raster.
    
    Returns
    =======
    output
    
    """

    
    change_priority = {
        "No Change": 0,
        "road to building": 7,#7,
        "road to barren": 4,
        "road to water": 0,
        "road to grass": 1,
        "road to forest": 1,
        "road to developed": 4,
        "building to road": 1,
        "building to barren": 7,
        "building to water": 0,
        "building to grass": 3,
        "building to forest": 3,
        "building to developed": 5,
        "barren to road": 3,
        "barren to building": 7,
        "barren to water": 0,
        "barren to grass": 2,
        "barren to forest": 2,
        "barren to developed": 5,
        "water to road": 0,
        "water to building": 0,
        "water to barren": 0,
        "water to grass": 0,
        "water to forest": 0,
        "water to developed": 0,
        "grass to road": 3,
        "grass to building": 7,
        "grass to barren": 3,
        "grass to water":0,
        "grass to forest": 3,
        "grass to developed": 5,
        "forest to road": 3,
        "forest to building": 7, #7,
        "forest to barren": 7,
        "forest to water": 0,
        "forest to grass": 3,
        "forest to developed": 7,
        "developed to road": 3,
        "developed to building": 7,
        "developed to barren": 7,
        "developed to water": 0,
        "developed to grass": 3,
        "developed to forest": 3
    }
    
    
    def expression_builder(from_val, to_val, priority):
            return f"if({before_landcover} == {from_val} && {after_landcover} == {to_val}, {priority}," # if({new_expression}))"
    
   
    class_list = range(0,7)
    classnames = ["road", "building", "barren", "forest", "grass", "water", "developed"]
    expression = ""
    closing = ""
    for from_class in class_list:
        for to_class in class_list:
            if from_class != to_class:
                change_key = f"{classnames[from_class]} to {classnames[to_class]}"
                change_value = change_priority[change_key]
                expression += expression_builder(from_class,to_class,change_value)
                closing += ")"
    expression+= "0"  
    expression+= closing
    gs.mapcalc(f"{output} = {expression}")
    gs.run_command("r.colors", map=output, color="plasma")
  

"""
Import UAS Data 
=================
"""

def import_uas_data(dtm_input, dtm_output, dsm_input, dsm_output, ortho_input, ortho_output, ortho_composite, laz_input, laz_output, laz_dsm, res=0.5, memory=300, nprocs=1, overwrite=False):
    """
    Imports DSM, DTM, Ortho, and point cloud data exported from WebDOM into GRASS GIS.
    @param dtm_input : string : file location (.tif)
    @param dtm_output : string : Output file name
    @param dsm_input : string : file location (.tif)
    @param dsm_output : string : Output file name
    @param ortho_input : string : file location (.tif)
    @param ortho_output : string : Output file name
    @param ortho_composite: string :  Output file name of composite image
    @param laz_input : string : file location (.laz)
    @param laz_output : string : Output file name
    @param laz_dsm : Output file name of point cloud derived DSM
    @param laz_be_pc : DOES NOT WORK Output file name of bare earth point cloud
    @param laz_dem : DOES NOT WORK Output file name of point cloud derived DEM
    @param res : The the import resolution (Dfault = 0.5)
    @param memory : Allocate memeory for import steps (Default = 300) 
    @param nprocs : Allocate total processes used during interpolation (Default = 1) 
    @param overwrite : Overwrite existing files (Default = False)
    
    """
    print("*" * 100)
    print("Starting UAS Import")
    print(f"Setting Region with {res} resolution")
    gs.run_command("g.region", res=res, flags="ap")
    
    print(f"Importing DTM: {dtm_output}")

    gs.run_command("r.import",
                   input=dtm_input, 
                   memory=memory,
                   output=dtm_output,
                   resample="bilinear",
                   overwrite=overwrite
                  )
    gs.run_command("r.colors", map=dtm_output, color="elevation", flags="e")


    print(f"Importing DSM: {dsm_output}")
    gs.run_command("r.import",
                   input=dsm_input, 
                   memory=memory,
                   output=dsm_output,
                   resample="bilinear",
                   overwrite=overwrite
                  )

    print(f"Importing Ortho: {ortho_output}")
    gs.run_command("r.import",
                   input=ortho_input, 
                   memory=memory,
                   output=ortho_output,
                   resample="nearest",
                   overwrite=overwrite
                  )

    print(f"Creating Ortho: {ortho_composite}")
    gs.run_command("g.region", raster=f"{ortho_output}.1", res=res, flags="ap")

    gs.run_command("r.composite",
                red=f"{ortho_output}.1",
                green=f"{ortho_output}.2",
                blue=f"{ortho_output}.3",
                output=ortho_composite,
                overwrite=overwrite
            )
    
#     print(f"Importing Point Cloud (DSM): {laz_output}")
#     gs.run_command("v.in.pdal",
#                  input=laz_input,
#                  output=laz_output,
#                  flags="w",
#                  # input_srs="EPSG:4326",
#                  overwrite=overwrite
#               )
#     # Set  computaional region to imported raster data
#     gs.run_command("g.region", raster=ortho_composite, res=res, flags="ap")
    
#     print(f"Generating DSM: {laz_output}")
#     gs.run_command("v.surf.rst",
#                  input=laz_output,
#                  elevation=laz_dsm,
#                  npmin=120,
#                  segmax=25,
#                  tension=100,
#                  smooth=0.5,
#                  dmin=1,
#                  mask=ortho_composite,
#                  nprocs=nprocs,
#                  overwrite=overwrite
#               )
    
    print("Import Complete")
    print("*" * 100)
    
def resample_uas_data(dtm, dtm_output, dsm, dsm_output, ortho, ortho_output,red,red_output,green,green_output,blue,blue_output,nir,nir_output, res, overwrite=False):
    """
    Resamples UAS data into another resolution.
    
    
    Parameters
    ==========
    dtm (str): Input DTM raster name.
    dtm_output (str): Output DTM raster name.
    dsm (str): Input DSM raster name.
    dsm_output (str): Output DSM raster name.
    ortho (str): Input orthoimage name.
    ortho_output (str): Output orthoimage name.
    red (str): Input image red band raster name.
    red_output (str): Output image red band raster name.
    green (str): Input image green band raster name.
    green_output (str): Output image green band raster name.
    blue (str): Input image blue band raster name.
    blue_output (str): Output image blue band raster name.
    nir (str): Input image nir band raster name.
    nir_output (str): Output image nir band raster name.
    res (int): Resolution to resample data to
    overwrite (bool): Overwrite existing files
    
    Returns
    =======
    dtm_output,dsm_output,ortho_output,red_output,green_output,blue_output,nir_output
    """
    # Resample DTM
    gs.run_command("g.region", raster=dtm, res=res, flags="ap")
    gs.run_command("r.resamp.interp", input=dtm, output=dtm_output, overwrite=overwrite)
    # Resample DSM
    gs.run_command("g.region", raster=dsm, res=res, flags="ap")
    gs.run_command("r.resamp.interp", input=dsm, output=dsm_output, overwrite=overwrite)
    # Resample Ortho
    gs.run_command("g.region", raster=ortho, res=3, flags="ap")
    gs.run_command("r.resamp.interp", input=ortho, output=ortho_output, method="nearest", overwrite=True)
    gs.run_command("r.resamp.interp", input=red, output=red_output, method="nearest", overwrite=True)
    gs.run_command("r.resamp.interp", input=green, output=green_output, method="nearest", overwrite=True)
    gs.run_command("r.resamp.interp", input=blue, output=blue_output, method="nearest", overwrite=True)
    gs.run_command("r.resamp.interp", input=nir, output=nir_output, method="nearest", overwrite=True)
    # Set DTM an DSM color tables
    gs.run_command("r.colors", map=f"{dtm_output},{dsm_output}", color="elevation", flags="e")
    
    return dtm_output,dsm_output,ortho_output,red_output,green_output,blue_output,nir_output
    
    
"""
Profile DEM data
=================
"""
    
def profile_dem(dem, output, coords):
    out = f"output/{output}.csv"
    gs.run_command("r.profile", flags="gc", input=dem, coordinates=coords, output=out,null_value="0", overwrite=True)
    gs.run_command("v.in.ascii", input=out, output=output, separator="space", columns="x double,y double,profile double,diff double, color varchar", overwrite=True)
    # !v.univar map=profile_fenton_shift column=diff
    df = pd.read_csv(out,delimiter=" ", names=['x','y','profile','diff','color'])
    return df


"""
Fusion
=================
"""
def geographic_correct_dem(dem,output,row_shift=0, column_shift=0):
    """
    Geographic Registration
    @param dem string Input raster name
    @param output string Output raster name
    @param row_shift int (default=-5)
    @param column_shift int (default=-1)
    @return output Shifted raster name
    """
    print(("#"*25) + " Geographic Shift " + ("#" *25))
    print(f"Inputs: dem:{dem},output: {output},row_shift: {row_shift}, column_shift: {column_shift}")

    gs.mapcalc(f"{output} = if({dem} >= 0, {dem}[{row_shift},{column_shift}], null())")
    return output

def import_dsm(output, output_dir, input_srs, resolution, nprocs):
    gs.run_command(
        "r.in.usgs",
        product="lidar",
        output_name=output,
        output_directory=output_dir,
        input_srs=input_srs,
        resolution=resolution,
        nprocs=nprocs,
        flags="k",
    )

def edge_mask(uas, thres=-1, e=None):
    print(("#"*25) + " Edge Mask " + ("#" *25))
    mask = f"{uas}_mask"
    print(f"UAS Mask: {mask}")
    gs.mapcalc(f"{mask} = if({uas}, 1, null())")
    uas_thin = f"{uas}_thin"
    if e:
        gs.run_command("g.region", raster=uas)
        uas_reg = gs.region(uas)
        e = uas_reg["e"] - e
        gs.run_command("g.region", e=e)

        # gs.run_command("g.region", n=n, e=e, s=s, w=w)
        gs.mapcalc(f"{uas_thin} = if({uas}, {uas}, null())")
    else:
        thin=f"{mask}_thin" # The thinned mask
        print(f"Thin UAS Mask: {thin}")
        gs.run_command("r.grow", overwrite=True, input=mask, output=thin, radius=thres)
        gs.mapcalc(f"{uas_thin} = if({thin}, {uas}, null())")

    print(f"Thin UAS: {uas_thin}")

    return uas_thin

def ground_dem(uas,uas_vert_c, dem, thres=0.1):
    """
    @param uas : UAS Data
    @param uas_vert_c : Vert Correct UAS
    @param dem : DEM Data
    @return ground: 
    """
    print(("#"*25) + " Ground DEM " + ("#" *25))
    ground_dem = "ground_dem"
    gs.mapcalc(f"{ground_dem} = if({uas_vert_c} - {dem} <= {thres}, {uas},null())") # 1ft
    print(f"Output: Uncorrected Ground DEM< (UAS_Vert_Corrected - DEM < {thres}): {ground_dem}")
    ground_dem_point_sample = "ground_dem_point_sample"
    gs.run_command("r.random", flags="d", input=ground_dem, npoints=20, raster=ground_dem_point_sample, seed=1)
    return ground_dem_point_sample

def report_diff_stats(raster):
    univar = gs.parse_command("r.univar", map=raster, flags="ge")
    mean = float(univar["mean"])
    stddev = float(univar["stddev"])
    tb_median = float(univar["median"])
    dmin = float(univar["min"])
    dmax = float(univar["max"])
    print(f"{raster}: Mean: {mean}, STD: {stddev}, Median: {tb_median}, Min: {dmin}, Max: {dmax}")
    return univar


def import_dem(output, output_dir, nprocs):
    gs.run_command(
        "r.in.usgs",
        product="ned",
        ned_dataset="ned19sec",
        output_name=output,
        output_directory=output_dir,
        nprocs=nprocs,
    )


def resample(uas, dem, match_uas=True):
    # resample uas to match lidar, or the other way round?
    print(("#"*25) + " Resample " + ("#" *25))

    resampled = "tmp_resampled"
    uas_ = uas
    dem_ = dem

    if not match_uas:
        print(f"Output Raster: Resampled to Match DEM: {resampled}")
        gs.run_command("g.region", raster=uas, align=dem)
        gs.run_command("r.resamp.interp", input=uas, output=resampled)
        uas_ = resampled
    else:
        print(f"Output Raster: Resampled to Match UAS: {resampled}")
        gs.run_command("g.region", raster=dem, align=uas)
        gs.run_command("r.resamp.interp", input=dem, output=resampled)
        dem_ = resampled

    # TMP_RAST.append(resampled)
    return uas_, dem_

def get_diff(uas, dem, mean_thr, output):
    # compute difference
    print(("#"*25) + " Get Diff " + ("#" *25))
    diff = f"{output}_diff"
    gs.run_command("g.region", raster=uas)
    gs.mapcalc(diff + " = " + uas + " - " + dem)
    print(f"Output Raster: Difference (UAS - DEM): {diff}")
    # TMP_RAST.append(diff)
    univar = gs.parse_command("r.univar", map=diff, flags="ge")
    mean = float(univar["mean"])
    median = float(univar["median"])
    stddev = float(univar["stddev"])
    # print("Difference: {mean:.1f} ± {stddev:.1f}".format(mean=mean, stddev=stddev))
    # test for systematic shift:
    print(f"Difference: Mean:{mean}, STD: {stddev}, Median: {median}")
    _min = float(univar["min"])
    _max = float(univar["max"])
    print(f"Range: Min:{_min}, Max: {_max}")
    if abs(median) > mean_thr:
        print("Vertical shift is likely.")
    return diff, median

def vertically_corrected_uas(uas, dem, shift,output):
    print(("#"*25) + " Vertical Correction " + ("#" *25))
    print(f"Shifting {uas} by {shift}m")
    new = f"{output}_vertically_corrected_uas"
    diff = f"{output}_diff_corrected"
    gs.mapcalc(f"{new} = {uas} - {shift}")
    print(f"Output: Vertically Corrected UAS (UAS - Shift): {new}")
    univar = gs.parse_command("r.univar", map=new, flags="ge")
    mean = float(univar["mean"])
    stddev = float(univar["stddev"])
    median = float(univar["median"])
    print(f"Vertically Corrected Stats: Mean: {mean}, STD: {stddev}, Median: {median}")
    # report_diff_stats(new)

    # TMP_RAST.append(new)
    
    gs.mapcalc(diff + " = " + new + " - " + dem)
    print(f"Output: Difference (Vertically Corrected UAS - DEM): {diff}")
    univar = gs.parse_command("r.univar", map=diff, flags="ge")
    mean = float(univar["mean"])
    stddev = float(univar["stddev"])
    median = float(univar["median"])
    print(f"Difference (Vertically Corrected UAS - DEM) Stats: Mean: {mean}, STD: {stddev}, Median: {median}")
    # TMP_RAST.append(diff)

    return new, diff


def patch(uas, dem, output,ps,ta,dr):
    print(("#"*25) + " Patch " + ("#" *25))
    print(f"Inputs: uas:{uas},dem:{dem},output:{output},ps:{ps},ta:{ta},dr{dr}")
    overlap = f"{output}_overlap"
    gs.run_command("g.region", raster=dem)
    gs.run_command(
        "r.patch.smooth", input_a=uas, input_b=dem, output=output, 
        # smooth_dist=10, 
        overlap=overlap,
        parallel_smoothing=ps,
        transition_angle=ta,
        difference_reach=dr,
        # blend_mask="fenton_edge_mask_odm_dtm_3m_pmask",
        flags="s"
    )
    print(f"Output: Overlap: {overlap}")
    print(f"Output: Fused DEM {output}")
    diff = f"{output}_diff"
    gs.mapcalc(f"{diff} = {output} - {dem}")
    print(f"Output: Fused Diff (Fused UAS DEM - DEM) {diff}")

    report_diff_stats(diff)
#     univar = gs.parse_command("r.univar", map=diff, flags="ge")
#     mean = float(univar["mean"])
#     median = float(univar["median"])
#     stddev = float(univar["stddev"])
   
#     print(f"Difference: Mean:{mean}, STD: {stddev}, Median: {median}")
    gs.run_command("r.colors", map=[output, dem, uas], color="elevation")

def fusion(dem, uas, output,ps=5,ta=2,dr=3, offset_value=0, usgs=True, thin=0, smooth=0):
    import grass.script as gs
    import grass.script.array as garray
    # from sklearn.mixture import BayesianGaussianMixture as GMM
    import numpy as np
    from grass.pygrass.modules import Module
    # TMP_RAST = []
    # TMP_VECT = []
    stddev_thr = 5
    mean_thr = 2
    _uas = uas
    buffer = 0.5
    gs.run_command("g.region", raster=uas)
    uas_reg = gs.region(uas)
    avg_wh = ((uas_reg["n"] - uas_reg["s"]) + (uas_reg["e"] - uas_reg["w"])) / 2.0
    n = uas_reg["n"] + avg_wh * buffer
    s = uas_reg["s"] - avg_wh * buffer
    e = uas_reg["e"] + avg_wh * buffer
    w = uas_reg["w"] - avg_wh * buffer
    gs.run_command("g.region", n=n, e=e, s=s, w=w)
    # import_dsm(dem, output_dir='/tmp', input_srs='EPSG:2264', resolution=3, nprocs=4)
    if usgs:
        # import_dsm(dem, output_dir='/tmp', input_srs='EPSG:2264', resolution=3, nprocs=8)
        import_dem(dem,"/tmp", 5)
    gs.use_temp_region()
    uas = geographic_correct_dem(uas, "geo_correct_uas")

    uas, dem = resample(uas, dem, True)
    diff, univar_shift = get_diff(uas, dem, 2,output)
    uas_vert_c, diff = vertically_corrected_uas(uas, dem, univar_shift, output)
    # Reshift to improve vert overap accuracy
    ground = ground_dem(uas, uas_vert_c,dem)
    diff, univar_shift = get_diff(ground, dem, 2,output)
    if (abs(offset_value) > 0):
        print(f"Setting Offset Manaully: {offset_value}")
        univar_shift = offset_value
    uas, diff = vertically_corrected_uas(uas, dem, univar_shift, output)
    patch(uas, dem, output,ps,ta,dr)
    gs.del_temp_region()