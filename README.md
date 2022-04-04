# rapid-dem-binder

Binder containing submitted results to the "Rapid-DEM: Rapid Topographic Updates through Satellite Change Detection and UAS Data Fusion" (White et al., 2022)

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

White, C.T.; Reckling, W.; Petrasova, A.; Meentemeyer, R.K.; Mitasova, H. Rapid-DEM: Rapid Topographic Updates through Satellite Change Detection and UAS Data Fusion. Remote Sens. 2022, 14, 1718. https://doi.org/10.3390/rs14071718

## License

Apache 2.0
