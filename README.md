# water-quality-drought
Study on water quality prediction across Contiguous United States
water-quality-drought/
├── README.md
├── LICENSE
├── environment.yml
├── .gitignore
├── config/
│   └── study_settings.yml
├── scripts/
│   ├── 01_download_gagesii.py
│   ├── 02_download_water_quality.py
│   ├── 03_clean_water_quality.py
│   ├── 04_build_daily_targets.py
│   ├── 05_screen_data_availability.py
│   ├── 06_select_agricultural_basins.py
│   ├── 07_download_streamflow.py
│   ├── 08_check_streamflow_coverage.py
│   ├── 09_calculate_ssi.py
│   ├── 10_extract_watershed_boundaries.py
│   ├── 11_download_gridmet.py
│   └── 12_prepare_model_inputs.py
├── models/
│   └── [training scripts added when completed]
├── evaluation/
│   └── [evaluation scripts added when completed]
├── figures/
│   └── plot_study_area.py
├── notebooks/
│   └── example_workflow.ipynb
└── data/
    ├── README.md
    ├── metadata/
    └── example/
