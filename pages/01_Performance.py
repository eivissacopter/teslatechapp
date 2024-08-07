import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup
from io import StringIO
import urllib.parse
import re

# Set page config
st.set_page_config(page_title="Tesla Performance Analysis", page_icon=":racing_car:", layout="wide")

# Function to scan the root folder and classify the subfolders
@st.cache_data(ttl=600)
def scan_and_classify_folders(base_url):
    def parse_directory(url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        dirs = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('/')]
        return dirs

    def classify_folder(folder_name):
        pattern = re.compile(r"(?P<manufacturer>[^_]+)_"
                             r"(?P<model>[^_]+)_"
                             r"(?P<variant>[^_]+)_"
                             r"(?P<model_year>\d+)_"
                             r"(?P<battery>[^_]+)_"
                             r"(?P<front_motor>[^_]+)_"
                             r"(?P<rear_motor>[^_]+)_"
                             r"(?P<tuning>[^/]+)")
        match = pattern.match(folder_name)
        if match:
            return match.groupdict()
        else:
            return None

    root_structure = {}
    classified_folders = []
    dirs = parse_directory(base_url)
    for d in dirs:
        full_path = urllib.parse.urljoin(base_url, d)
        classification = classify_folder(d)
        if classification:
            classification['path'] = full_path
            classified_folders.append(classification)
    return classified_folders

# Base URL for scanning the root folder
BASE_URL = "https://nginx.eivissacopter.com/smt/"

# Scan and classify folders
classified_folders = scan_and_classify_folders(BASE_URL)

# Create dynamic filters based on the classified information
manufacturers = list(set([f['manufacturer'] for f in classified_folders]))
models = list(set([f['model'] for f in classified_folders]))
variants = list(set([f['variant'] for f in classified_folders]))
model_years = list(set([f['model_year'] for f in classified_folders]))
batteries = list(set([f['battery'] for f in classified_folders]))
front_motors = list(set([f['front_motor'] for f in classified_folders]))
rear_motors = list(set([f['rear_motor'] for f in classified_folders]))
tunings = list(set([f['tuning'] for f in classified_folders]))

# Sidebar filters
st.sidebar.header("Filter Options")
selected_manufacturer = st.sidebar.multiselect("Select Manufacturer", manufacturers)
selected_model = st.sidebar.multiselect("Select Model", models)
selected_variant = st.sidebar.multiselect("Select Variant", variants)
selected_model_year = st.sidebar.multiselect("Select Model Year", model_years)
selected_battery = st.sidebar.multiselect("Select Battery", batteries)
selected_front_motor = st.sidebar.multiselect("Select Front Motor", front_motors)
selected_rear_motor = st.sidebar.multiselect("Select Rear Motor", rear_motors)
selected_tuning = st.sidebar.multiselect("Select Tuning", tunings)

# Filter folders based on selections
filtered_folders = [f for f in classified_folders if
                    (not selected_manufacturer or f['manufacturer'] in selected_manufacturer) and
                    (not selected_model or f['model'] in selected_model) and
                    (not selected_variant or f['variant'] in selected_variant) and
                    (not selected_model_year or f['model_year'] in selected_model_year) and
                    (not selected_battery or f['battery'] in selected_battery) and
                    (not selected_front_motor or f['front_motor'] in selected_front_motor) and
                    (not selected_rear_motor or f['rear_motor'] in selected_rear_motor) and
                    (not selected_tuning or f['tuning'] in selected_tuning)]

# Display selected path
if filtered_folders:
    st.sidebar.write("Filtered Paths:")
    for folder in filtered_folders:
        st.sidebar.write(folder['path'])
else:
    st.sidebar.write("No folders match the selected filters.")

# Fetch and process CSV files based on filtered folders
dfs = []
for folder in filtered_folders:
    response = requests.get(folder['path'])
    soup = BeautifulSoup(response.content, 'html.parser')
    files = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.csv')]
    for file in files:
        file_url = urllib.parse.urljoin(folder['path'], file)
        try:
            response = requests.get(file_url)
            csv_content = response.content.decode('utf-8')
            df = pd.read_csv(StringIO(csv_content))
            df = df.fillna(method='ffill', limit=100)
            df = df.fillna(method='bfill', limit=100)
            if 'Accelerator Pedal' in df.columns:
                df = df[df['Accelerator Pedal'] == 100]
            dfs.append(df)
        except Exception as e:
            st.error(f"Error fetching {file_url}: {e}")

# Concatenate all dataframes
if dfs:
    data = pd.concat(dfs, ignore_index=True)
    st.write(data.head())
else:
    st.write("No CSV files found or no data available after filtering.")

# Ensure required columns are available for plotting
if 'SOC' in data.columns and 'pdelta' in data.columns and 'Cell temp mid' in data.columns:
    # Plot the data
    fig = px.scatter(
        data,
        x='SOC',
        y='pdelta',
        color='Cell temp mid',
        color_continuous_scale='bwr',
        labels={'SOC': 'SOC [%]', 'pdelta': 'Pdelta [kW]', 'Cell temp mid': 'Cell Temp'},
        title='Panasonic 3L 82kWh - Pdelta'
    )

    fig.update_layout(
        coloraxis_colorbar=dict(
            title="Cell Temp"
        ),
        xaxis=dict(
            autorange='reversed'
        ),
        template="plotly_dark"
    )

    # Add watermark
    fig.add_annotation(
        text="@eivissacopter",
        font=dict(size=50, color="gray"),
        align="center",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        opacity=0.2,
        showarrow=False
    )

    # Plot the figure
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Required columns are missing in the data.")

# Placeholder for performance meter screenshots
st.sidebar.header("Performance Meter Screenshots")
performance_meter_images = st.sidebar.file_uploader("Upload Performance Meter Screenshots", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

# Display performance meter screenshots
if performance_meter_images:
    st.header("Performance Meter Screenshots")
    cols = st.columns(len(performance_meter_images))
    for i, image in enumerate(performance_meter_images):
        with cols[i]:
            st.image(image, use_column_width=True)
