# rapid-dem-binder

A collection of jupyter notebooks containing the data analysis of the manuscript ["Rapid-DEM: Rapid Topographic Updates through Satellite Change Detection and UAS Data Fusion" (White et al., 2022)](https://www.mdpi.com/2072-4292/14/7/1718).

![https://www.mdpi.com/remotesensing/remotesensing-14-01718/article_deploy/html/images/remotesensing-14-01718-ag.png](https://www.mdpi.com/remotesensing/remotesensing-14-01718/article_deploy/html/images/remotesensing-14-01718-ag.png)

## Abstract

As rapid urbanization occurs in cities worldwide, the importance of maintaining updated digital elevation models (DEM) will continue to increase. However, due to the cost of generating high-resolution DEM over large spatial extents, the temporal resolution of DEMs is coarse in many regions. Low-cost unmanned aerial vehicles (UAS) and DEM data fusion provide a partial solution to improving the temporal resolution of DEM but do not identify which areas of a DEM require updates. We present Rapid-DEM, a framework that identifies and prioritizes locations with a high likelihood of an urban topographic change to target UAS data acquisition and fusion to provide up-to-date DEM. The framework uses PlanetScope 3 m satellite imagery, Google Earth Engine, and OpenStreetMap for land cover classification. GRASS GIS generates a contextualized priority queue from the land cover data and outputs polygons for UAS flight planning. Low-cost UAS fly the identified areas, and WebODM generates a DEM from the UAS survey data. The UAS data is fused with an existing DEM and uploaded to a public data repository. To demonstrate Rapid-DEM a case study in the Walnut Creek Watershed in Wake County, North Carolina is presented. Two land cover classification models were generated using random forests with an overall accuracy of 89% (kappa 0.86) and 91% (kappa 0.88). The priority queue identified 109 priority locations representing 1.5% area of the watershed. Large forest clearings were the highest priority locations, followed by newly constructed buildings. The highest priority site was a 0.5 km2 forest clearing that was mapped with UAS, generating a 15 cm DEM. The UAS DEM was resampled to 3 m resolution and fused with USGS NED 1/9 arc-second DEM data. Surface water flow was simulated over the original and updated DEM to illustrate the impact of the topographic change on flow patterns and highlight the importance of timely DEM updates.

## Workflow Notebooks

1. **gee_change_detection**: Google Earth Engine change detection workflow. (Needs Clean Up)
2. **gee_import_planet**: Creates PlanetScope order using Planet API and creates Google Earth Engine ImageCollection. (Needs Clean Up)
3. **odm**: ODM SFM Configuration (TODO)
4. **priority_queue**: Workflow to develop the priority queue from land cover data. (Ready)
5. **analysis**: UAS processing, DEM fusion, and surface water modeling. (Ready)

## Scripts

- **rapid_dem.py**: Helper scripts used in Notebooks.
- **gee_helpers.py**: Google Earth Engine helper scripts used in Notebooks.

## Project Data

[https://osf.io/yg6h8/](https://osf.io/yg6h8/)

## Citation

White, C.T.; Reckling, W.; Petrasova, A.; Meentemeyer, R.K.; Mitasova, H. Rapid-DEM: Rapid Topographic Updates through Satellite Change Detection and UAS Data Fusion. Remote Sens. 2022, 14, 1718. [https://doi.org/10.3390/rs14071718](https://doi.org/10.3390/rs14071718)

## License

Apache 2.0
