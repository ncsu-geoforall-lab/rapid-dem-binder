def add_ee_layer(self, eeImageObject, visParams, name):
    """
    Define a method for displaying Earth Engine image tiles to folium map.
    """
    mapID = ee.Image(eeImageObject).getMapId(visParams)
    folium.raster_layers.TileLayer(
        tiles = mapID['tile_fetcher'].url_format,
        attr = "Map Data © Google Earth Engine",
        name = name,
        overlay = True,
        control = True
    ).add_to(self)
    

def createNDVI(image):
    ndvi = image.normalizedDifference(['b4', 'b3']).select(["nd"],["ndvi"])
    return ndvi

    
def createNDWI(image):
    ndwi = image.normalizedDifference(['b1', 'b4']).select(["nd"], ["ndwi"])
    return ndwi


def createNDCI(image):
    ndci = image.normalizedDifference(['b4', 'b2']).select(["nd"], ["ndci"])
    return ndci


def createBSI(image):
    #https://openprairie.sdstate.edu/cgi/viewcontent.cgi?article=4165&context=etd
    bsi = image.expression(
    '((RED + GREEN) - (RED + BLUE))/ ((NIR + GREEN) + (RED + BLUE)) * 100 + 100' , {
      'NIR': image.select('b4'),
      'RED': image.select('b3'),
      'BLUE': image.select('b1'),
      'GREEN': image.select('b2')
    }).select(['b3'],['bsi'])
    return bsi


def createDSBI(image):
    #Lingjia GuLingjia 2018
    dsbi = image.expression(
    '0.5 * (BLUE - RED) +0.5*(BLUE - GREEN)' , {
      'NIR': image.select('b4'),
      'RED': image.select('b3'),
      'BLUE': image.select('b1'),
      'GREEN': image.select('b2')
    }).select(['constant'],['dsbi'])
    return dsbi


def createBSI_NDVI_index(image_bsi, image_ndvi):
    image = image_bsi.addBands(image_ndvi)
    ndbsvi = image.normalizedDifference(['bsi', 'ndvi']).select(["nd"], ["ndbsiv"])
    return ndbsvi


def createFeatureImportanceBarChart(classifier, label=""):
    fig, ax = plt.subplots(figsize=(9, 6))
    classifier_dict = classifier.explain()
    variable_importance = ee.Feature(None, ee.Dictionary(classifier_dict).get('importance'))
  
    print("Variable Importance")
    props = variable_importance.getInfo()["properties"]
    data = [{"feature":v, "value":props[v]} for v in props]
    df_variable_importance = pd.DataFrame(data)
    plt.title('%s Feature Importance' % label.capitalize(), fontsize=14) 
    sns.barplot(x="value", y="feature", data=df_variable_importance.sort_values("value", ascending=False),
            label="Feature Importance", color="b")
    plt.savefig(os.path.join(figures_save_location,label + "_FeatImportance"))
    return df_variable_importance.sort_values("value", ascending=False)['feature']

def generateFromToExpression(landclasses):
    """
    Generates thematic change expression and labeling dictionary
    @param landclasses land_class dictionary 
    """
    output = ""
    from_to_labels = {"No Change": 0}
    for form_value_key in land_classes:
        from_value = land_classes[form_value_key]
        for to_value_key in land_classes:
            to_value = land_classes[to_value_key]
            if from_value != to_value:
                change_class_value = str(from_value) + str(to_value)
                change_class_key = "%s to %s" % (form_value_key, to_value_key)
                from_to_labels[change_class_key] = change_class_value
                base_text = "(b('classification') == {0} && b('classification_1') == {1}) ? {2} :".format(from_value, to_value, change_class_value)
                output = output + base_text
        
    output = output + " 0"
    return({"labels": from_to_labels, "expression": output})


def generateThematicChangeImage(from_image, to_image, expression):
    """
    Add classified bands to same image
    """
    temp = from_image.addBands(to_image)
    change_image = temp.expression(expression)
    return change_image


def getNewBandNames(prefix, bandNames):
    """
    This helper function returns a list of new band names.
    """
    seq = ee.List.sequence(1, len(bandNames))
    z = [prefix + str(ee.Number(b).int().getInfo()) for b in seq.getInfo()]
    return z


def getPrincipalComponents(centered, scale, region):
    """
    This function accepts mean centered imagery, a scale and
    a region in which to perform the analysis.  It returns the
    Principal Components (PC) in the region as a new image.
    """
    #Collapse the bands of the image into a 1D array per pixel.
    arrays = centered.toArray();
    
    #Compute the covariance of the bands within the region.
    covar = arrays.reduceRegion(
      reducer = ee.Reducer.centeredCovariance(), 
      geometry= region,
      scale= scale, 
      maxPixels=1e9, 
      bestEffort=True, 
      tileScale=16)
   
    #Get the 'array' covariance result and cast to an array.
    #This represents the band-to-band covariance within the region.
    covarArray = ee.Array(covar.get('array'))
    
    #Perform an eigen analysis and slice apart the values and vectors.
    eigens = covarArray.eigen().getInfo()
    # print("eigens", eigens)
    #This is a P-length vector of Eigenvalues.
    eigenValues = ee.Array(eigens).slice(1, 0, 1);
    # print("eigenValues", eigenValues)
    #This is a PxP matrix with eigenvectors in rows.
    eigenVectors = ee.Array(eigens).slice(1, 1);
    # print("eigenVectors", eigenVectors)
    #Convert the array image to 2D arrays for matrix computations.
    arrayImage = arrays.toArray(1)
    # print("arrayImage", arrayImage)


    #Left multiply the image array by the matrix of eigenvectors.
    principalComponents = ee.Image(eigenVectors).matrixMultiply(arrayImage)

    #Turn the square roots of the Eigenvalues into a P-band image.
    sdImage = ee.Image(eigenValues.sqrt())
    sdImage = sdImage.arrayProject([0])
    bandNames = centered.bandNames().getInfo()
    sdImage = sdImage.arrayFlatten([getNewBandNames('sd', bandNames)])

    #Turn the PCs into a P-band image, normalized by SD.
    pc = principalComponents.arrayProject([0])#Throw out an an unneeded dimension, [[]] -> [].
    pc = pc.arrayFlatten([getNewBandNames('pc',bandNames)])#Make the one band array image a multi-band image, [] -> image
    pc = pc.divide(sdImage)#Normalize the PCs by their SDs.
    return pc


def createConfusionMatixFigure(testAccuracy, label=""):
    fig, ax = plt.subplots(figsize=(9, 6))
    df_confusion_test = pd.DataFrame(testAccuracy.getInfo(), index=list(land_classes.keys()), columns=list(land_classes.keys()))
    plt.title('%s Confusion Matrix' % label.capitalize(), fontsize=14) 
    sns.heatmap(df_confusion_test, annot=True, fmt="d", linewidths=.5, ax=ax, cmap="Blues")
    plt.savefig(os.path.join(figures_save_location,label + "_ConfMatrix"))
    
    
def exportEarthEngineImage(image, desc, imageName, region,scale=3, saveLocation="GoogleDrive"):
    import time
    if (saveLocation == "CloudStorage"):
        imageTask = ee.batch.Export.image.toCloudStorage(
          image=image,
          description=desc,
          fileNamePrefix=imageName,
          bucket="classification-results",
          scale=scale,
          fileFormat='GeoTIFF',
          skipEmptyTiles=True,
          maxPixels=1e12,
          # maxZoom=16,
          crs='EPSG:3857',
          formatOptions= {
          "cloudOptimized": True
          }
        )
    elif (saveLocation == "GoogleDrive"):
        imageTask = ee.batch.Export.image.toDrive(
        image=image,
        folder=figures_save_location,
        description='Image Export %s' % imageName,
        fileNamePrefix=imageName,
        scale=3,
        fileFormat= 'GeoTIFF',
        formatOptions= {"cloudOptimized": True},
        region=region
        )
    elif (saveLocation == "Asset"):
        imageTask = ee.batch.Export.image.toAsset(
          assetId= imageName,
          image=image,
          description='Image Export',
          fileNamePrefix=imageName,
          scale=3,
          fileFormat='GeoTIFF',
          region=region.toGeoJSON()['coordinates']
        )
    else:
        print("Unknown Save Location, must be either 'GoogleDrive','CloudStorage', or 'Asset")
        exit
        
    imageTask.start()
    while imageTask.active():
        print('Polling for task (id: {}).'.format(imageTask.id))
        time.sleep(3)


def exportToDrive(image, imageLabel, resolution=30):
    """
    param: image : ee.Image
    param: imageLabel: string
    param: resolution : export resolution (default = 30)
    """
    ee.batch.Export.image.toDrive(
        image=image,
        folder=figures_save_location,
        description=imageLabel,
        fileNamePrefix=imageLabel,
        scale=resolution,
        fileFormat= 'GeoTIFF',
        region=aoi.geometry(),
        formatOptions= {"cloudOptimized": True}
    ).start()
    
    


def detectOutlires(image, band, scale=3, region=aoi):
    """
    #https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/9ZIUGQ
    """
    # // Tukey's lower and upper fence
    percentiles = image.reduceRegion(
      reducer=ee.Reducer.percentile([10,25,50,75,90]),
      geometry=region,
      scale=scale,
      maxPixels= 1e12)
  
    lowerQuartile = ee.Number(percentiles.get(band+'_p25'))
    median = ee.Number(percentiles.get(band+'_p50'))
    upperQuartile = ee.Number(percentiles.get(band+'_p75'))

    IQR = upperQuartile.subtract(lowerQuartile)
    lowerFence = lowerQuartile.subtract(IQR.multiply(1.5))
    upperFence = upperQuartile.add(IQR.multiply(1.5))
  
    quartiles = image.gt(lowerQuartile).add(image.gt(median)).add(image.gt(upperQuartile)).remap([0,1,2,3],[1,2,3,4]).rename('quartile')
    outliers = image.gt(lowerFence).add(image.gt(upperFence)).remap([0,1,2],[1,0,2])
    tukeys = outliers.updateMask(outliers.neq(0)).rename('fence')
  
  # // Z-score
    mean = ee.Number(image.reduceRegion(
      reducer= ee.Reducer.mean(),
      geometry= region,
      scale= scale,
      maxPixels= 1e12).get(band))

    stdDev = ee.Number(image.reduceRegion(
      reducer= ee.Reducer.stdDev(),
      geometry= region,
      scale= scale,
      maxPixels= 1e12).get(band));
  
    zScore = image.subtract(mean).divide(stdDev).rename('zscore')
  
    # // Modified Z-score
    medAbsDev = image.subtract(median).abs();
  
    medianMedAbsDev = ee.Number(medAbsDev.reduceRegion(
      reducer= ee.Reducer.median(),
      geometry= region,
      scale= scale,
      maxPixels= 1e12).get(band))
  
    zScoreMod = image.subtract(mean).multiply(0.6745).divide(medianMedAbsDev).abs().rename('zscore_mod')
    zScoreModExp = zScoreMod.gt(3.5).multiply(3)
    zScoreModOutliers = zScoreModExp.updateMask(zScoreModExp.eq(3)).rename('zmod_outlier')
  
    # // Lower fence/upper fance + modified s-score outliers
    combined = zScoreModExp.add(outliers).rename('combined_outliers').remap([0,1,2,3,4,5],[0,3,4,5,1,2])
                #  // 0 = none
                #  // 1 = lower fence
                #  // 2 = upper fence
                #  // 3 = modified z-score
                #  // 4 = lower fence + modified z-score
                #  // 5 = upper fence + modified z-score 
    combinedMask = combined.updateMask(combined.neq(0))
      
    # // Geary's C statistic
    clist = [1, 1, 1, 1, 1, 1, 1, 1, 1]
    centerList = [1, 1, 1, 1, 0, 1, 1, 1, 1]
    lists = [clist, clist, clist, clist, centerList, clist, clist, clist, clist]
    kernel = ee.Kernel.fixed(9, 9, lists, -4, -4, False)
    neighs = image.neighborhoodToBands(kernel)
    # import math
    gearys = image.subtract(neighs).pow(2).reduce(ee.Reducer.sum()).divide(9**2)
         
    gearysQuartiles = gearys.reduceRegion(
      reducer=ee.Reducer.percentile([10,25,75,90]),
      geometry= region,
      scale= scale,
      maxPixels= 1e12)
  
  # gearys10 = gearysQuartiles.get('sum_p10').getInfo()
  # print(gearys10)

    gearysLowerQuartile = ee.Number(gearysQuartiles.get('sum_p25'))
    # print(gearysLowerQuartile)
    gearysUpperQuartile = ee.Number(gearysQuartiles.get('sum_p75'))
    gearysIQR = gearysUpperQuartile.subtract(gearysLowerQuartile)
    gearysUpperFence = gearysUpperQuartile.add(gearysIQR.multiply(1.5))
    gearysAccum = gearys.gt(gearysUpperFence).rename('gearys_outlier')
    print('gearysAccum')
    gearysOutlier = gearysAccum.updateMask(gearysAccum.eq(1)).rename('spatial_outlier')
    print('gearysOutlier')
  
    # // Locate pixels ≤ zero
    lteZero = image.lte(0).updateMask(image.lte(0).eq(1))
    print('lteZero')

    # // Layer design values
    zScorePercentiles = zScore.reduceRegion(
      reducer=ee.Reducer.percentile([10,90]),
      geometry= region,
      scale= scale,
      maxPixels= 1e12)
    print('zScorePercentiles')

    zScoreModPercentiles = zScoreMod.reduceRegion(
      reducer=ee.Reducer.percentile([10,90]),
      geometry= region,
      scale= scale,
      maxPixels= 1e12)
  
    print('zScoreModPercentiles')

    raw10 = ee.Number(percentiles.get(band+'_p10')).getInfo()
    print('raw10')
    raw90 = ee.Number(percentiles.get(band+'_p90')).getInfo()
    print('raw90')
    zScore10 = ee.Number(zScorePercentiles.get('zscore_p10')).getInfo()
    print('zScore10')
    zScore90 = ee.Number(zScorePercentiles.get('zscore_p90')).getInfo()
    print('zScore90')
    zScoreMod10 = ee.Number(zScoreModPercentiles.get('zscore_mod_p10')).getInfo()
    print('zScoreMod10')
    zScoreMod90 = ee.Number(zScoreModPercentiles.get('zscore_mod_p90')).getInfo()
    print('zScoreMod90')
    gearys10 = ee.Number(gearysQuartiles.get('sum_p10')).getInfo()
    print('gearys10')
    gearys90 = ee.Number(gearysQuartiles.get('sum_p90')).getInfo()
    print('gearys90')

    # -- Make sure to change the scale to calculate accurate area percentages
    print("AreaImage Start")
    areaImage = image.multiply(0).rename('area')
    print("AreaImage End")
    totalArea = ee.Number(areaImage.add(1).reduceRegion(
      reducer= ee.Reducer.sum(),
      geometry= region,
      scale= scale,
      maxPixels= 1e12).get('area'))

    print("totalArea")

    lfmzArea = ee.Number(areaImage.add(combinedMask.eq(1)).reduceRegion(
      reducer= ee.Reducer.sum(),
      geometry= region,
      scale= scale,
      maxPixels= 1e12).get('area')).divide(totalArea).multiply(100).getInfo() #.toFixed(2) #round(a, 2)
    print("lfmzArea")
    ufmzArea = ee.Number(areaImage.add(combinedMask.eq(2)).reduceRegion(
      reducer= ee.Reducer.sum(),
      geometry= region,
      scale= scale,
      maxPixels= 1e12).get('area')).divide(totalArea).multiply(100).getInfo() #.toFixed(2)
    print("ufmzArea")
    lfArea = ee.Number(areaImage.add(tukeys.eq(1)).reduceRegion(
      reducer= ee.Reducer.sum(),
      geometry= region,
      scale= scale,
      maxPixels= 1e12).get('area')).divide(totalArea).multiply(100).getInfo() #.toFixed(2)
      print("lfArea")

    ufArea = ee.Number(areaImage.add(tukeys.eq(2)).reduceRegion(
      reducer= ee.Reducer.sum(),
      geometry= region,
      scale= scale,
      maxPixels= 1e12).get('area')).divide(totalArea).multiply(100).getInfo() #.toFixed(2)
    print("ufArea")

    mzArea = ee.Number(areaImage.add(zScoreModOutliers.eq(3)).reduceRegion(
      reducer= ee.Reducer.sum(),
      geometry= region,
      scale= scale,
      maxPixels= 1e12).get('area')).divide(totalArea).multiply(100).getInfo() #.toFixed(2)
  
    lteZeroArea = ee.Number(areaImage.add(lteZero.eq(0)).reduceRegion(
      reducer= ee.Reducer.sum(),
      geometry= region,
      scale= scale,
      maxPixels= 1e12).get('area')).divide(totalArea).multiply(100).getInfo() #.toFixed(2)

    # center_map = [region.centroid().getInfo()['coordinates'][1],region.centroid().getInfo()['coordinates'][0]]
    # Create a folium map object.
    myMap = folium.Map(location=center_map, zoom_start=13, height=500)

    # // Add layers to display
    grayscale = ['f7f7f7', 'cccccc', '969696', '525252'];

    myMap.add_ee_layer(image, {'min': raw10, 'max': raw90, 'palette': grayscale}, 'version')

  
    myMap.add_ee_layer(quartiles, {'min': 1, 'max': 4, 'palette': grayscale}, 'Quartiles')


    myMap.add_ee_layer(zScore, {'min': zScore10, 'max': zScore90, 'palette': grayscale}, 'Z-score')

 
    myMap.add_ee_layer(zScoreMod, {'min': zScoreMod10, 'max': zScoreMod90, 'palette': grayscale}, 'Modified Z-score')

    myMap.add_ee_layer(gearys, {'min': gearys10, 'max': gearys90, 'palette': grayscale}, "Geary's C")

 
    myMap.add_ee_layer(tukeys, {'min': 1, 'max': 2, 'palette': ['22a6ff','ffd400']}, "Tukey's outliers")

 
    myMap.add_ee_layer(zScoreModOutliers, {'min': 3, 'max': 3, 'palette': '13e864'}, 'Modified Z-score outlier')

    myMap.add_ee_layer(gearysOutlier, {'min': 1, 'max': 1, 'palette': ['bebebe']}, "Geary's C design layer")
    myMap.add_ee_layer(gearysOutlier, {'min': 1, 'max': 1, 'palette': ['bebebe']}, "Geary's C outlier")
    myMap.add_ee_layer(combinedMask, {'min': 1, 'max': 5, 'palette': ['6713e8','ff225a','22a6ff','ffd400','13e864']}, 'Combined outliers')
    myMap.add_ee_layer(lteZero, {'min': 0, 'max': 0, 'palette': ['202020']}, 'Pixel lte zero')


    myMap.add_child(folium.LayerControl())

    # Display the map.
    display(myMap)  
