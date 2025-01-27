import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup
from io import StringIO
import urllib.parse
import json
import os
import re
from scipy.ndimage import uniform_filter1d

###################################################################################################

# Set page config
st.set_page_config(page_title="Tesla Performance Analysis", page_icon=":racing_car:", layout="wide")

# Metadata cache file
METADATA_FILE = "metadata_cache.json"

# Load metadata cache
def load_metadata_cache():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            return json.load(f)
    return {}

# Save metadata cache
def save_metadata_cache(metadata):
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f)

metadata_cache = load_metadata_cache()

# Function to scan the root folder and classify the subfolders
@st.cache_data(ttl=600)
def scan_and_classify_folders(base_url):
    def parse_directory(url):
        response = requests.get(url)
        if response.status_code != 200:
            st.error(f"Failed to access {url}")
            return []
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
                             r"(?P<tuning>[^_]+)_"
                             r"(?P<acceleration_mode>[^/]+)")
        match = pattern.match(folder_name)
        if match:
            classified = match.groupdict()
            classified['tuning'] = urllib.parse.unquote(classified['tuning'])
            classified['acceleration_mode'] = urllib.parse.unquote(classified['acceleration_mode'])
            return classified
        else:
            return None

    classified_folders = []
    dirs = parse_directory(base_url)
    for d in dirs:
        full_path = urllib.parse.urljoin(base_url, d)
        classification = classify_folder(d.strip('/'))
        if classification:
            classification['path'] = full_path
            classified_folders.append(classification)
    return classified_folders

# Base URL for scanning the root folder
BASE_URL = "https://nginx.eivissacopter.com/smt/"

# Scan and classify folders
classified_folders = scan_and_classify_folders(BASE_URL)

# Check if any classified folders were found
if not classified_folders:
    st.error("The directory structure is empty. No options available.")
    st.stop()

# Create dynamic filters based on the classified information
def get_unique_values(classified_folders, key, filters={}):
    values = set()
    for folder in classified_folders:
        match = all(folder[k] in v for k, v in filters.items() if k in folder)
        if match and key in folder:
            values.add(folder[key])
    return sorted(values)

selected_filters = {}

###################################################################################################

# Add the main header picture with emojis
st.markdown(
    """
    <style>
        .header {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            padding: 0rem 0;
            margin-bottom: 0rem; /* Adjust the margin bottom to reduce space */
        }
        .header img {
            width: 100%;
            height: auto;
        }
        .header h1 {
            margin: 0;
            padding-top: 1rem;
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
        }
        .header h1 span {
            margin: 0 10px;
        }
    </style>
    <div class="header">
        <img src="https://uploads.tff-forum.de/original/4X/5/2/3/52397973df71db6122c1eda4c5c558d2ca70686c.jpeg" alt=":racing_car: Tesla Performance Analysis :racing_car:">
        <h1><span>🚀</span> Tesla Performance Analysis <span>🚀</span></h1>
    </div>
    """,
    unsafe_allow_html=True
)

###################################################################################################

# Prefill function
def prefill_filter(options, label):
    if len(options) == 1:
        return st.sidebar.multiselect(label, options, default=options)
    return st.sidebar.multiselect(label, options)

# Model and Variant filters
col1, col2 = st.sidebar.columns(2)
models = get_unique_values(classified_folders, 'model')
selected_model = col1.multiselect("Model", models, default=models if len(models) == 1 else [])
if selected_model:
    selected_filters['model'] = selected_model

variants = get_unique_values(classified_folders, 'variant', selected_filters)
selected_variant = col2.multiselect("Variant", variants, default=variants if len(variants) == 1 else [])
if selected_variant:
    selected_filters['variant'] = selected_variant

# Model Year and Battery filters
col3, col4 = st.sidebar.columns(2)
model_years = get_unique_values(classified_folders, 'model_year', selected_filters)
selected_model_year = col3.multiselect("Model Year", model_years, default=model_years if len(model_years) == 1 else [])
if selected_model_year:
    selected_filters['model_year'] = selected_model_year

batteries = get_unique_values(classified_folders, 'battery', selected_filters)
selected_battery = col4.multiselect("Battery", batteries, default=batteries if len(batteries) == 1 else [])
if selected_battery:
    selected_filters['battery'] = selected_battery

# Front Motor and Rear Motor filters
col5, col6 = st.sidebar.columns(2)
front_motors = get_unique_values(classified_folders, 'front_motor', selected_filters)
selected_front_motor = col5.multiselect("Front Motor", front_motors, default=front_motors if len(front_motors) == 1 else [])
if selected_front_motor:
    selected_filters['front_motor'] = selected_front_motor

rear_motors = get_unique_values(classified_folders, 'rear_motor', selected_filters)
selected_rear_motor = col6.multiselect("Rear Motor", rear_motors, default=rear_motors if len(rear_motors) == 1 else [])
if selected_rear_motor:
    selected_filters['rear_motor'] = selected_rear_motor

# Tuning filter
tunings = get_unique_values(classified_folders, 'tuning', selected_filters)
selected_tuning = st.sidebar.multiselect("Tuning", tunings, default=tunings if len(tunings) == 1 else [])
if selected_tuning:
    selected_filters['tuning'] = selected_tuning

# Acceleration Mode filter with custom order
acceleration_modes = get_unique_values(classified_folders, 'acceleration_mode', selected_filters)
acceleration_modes_ordered = ["Chill", "Standard", "Sport"]
selected_acceleration_mode = st.sidebar.multiselect("Acceleration Mode", acceleration_modes_ordered, default=acceleration_modes_ordered if len(acceleration_modes_ordered) == 1 else [])
if selected_acceleration_mode:
    selected_filters['acceleration_mode'] = selected_acceleration_mode

###################################################################################################

# Function to fetch CSV headers and first valid values
def fetch_csv_headers_and_first_valid_values(url):
    # Use cached metadata if available
    if url in metadata_cache:
        return metadata_cache[url]['headers'], metadata_cache[url]['SOC'], metadata_cache[url]['Cell temp mid']

    response = requests.get(url)
    content = response.content.decode('utf-8')
    df = pd.read_csv(StringIO(content))

    # Check if the required columns are present
    if 'SOC' not in df.columns or 'Cell temp mid' not in df.columns:
        headers = df.columns.tolist()
        metadata_cache[url] = {'headers': headers, 'SOC': None, 'Cell temp mid': None}
        return headers, None, None

    # Scan entire DataFrame until valid values are found
    df['SOC'] = df['SOC'].ffill().bfill()
    df['Cell temp mid'] = df['Cell temp mid'].ffill().bfill()

    # Filter invalid values
    df = df[(df['SOC'] >= -5) & (df['SOC'] <= 101) & (df['Cell temp mid'] >= -30) & (df['Cell temp mid'] <= 70)]

    # Find the first valid values
    for index, row in df.iterrows():
        soc_value = row['SOC']
        cell_temp_mid_value = row['Cell temp mid']
        if pd.notna(soc_value) and pd.notna(cell_temp_mid_value):
            headers = df.columns.tolist()
            metadata_cache[url] = {'headers': headers, 'SOC': round(soc_value), 'Cell temp mid': round(cell_temp_mid_value)}
            return headers, round(soc_value), round(cell_temp_mid_value)

    headers = df.columns.tolist()
    metadata_cache[url] = {'headers': headers, 'SOC': None, 'Cell temp mid': None}
    return headers, None, None

# Filter folders based on selections
filtered_folders = [f for f in classified_folders if
                    all(f[k] in v for k, v in selected_filters.items() if k in f)]

# Initialize an empty list to collect file information
file_info = []

# Collect SOC and Cell temp mid values
if filtered_folders:
    for folder in filtered_folders:
        response = requests.get(folder['path'])
        soup = BeautifulSoup(response.content, 'html.parser')
        files = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.csv')]
        for file in files:
            file_url = urllib.parse.urljoin(folder['path'], file)
            headers, soc_value, cell_temp_mid_value = fetch_csv_headers_and_first_valid_values(file_url)
            if 'SOC' not in headers or 'Cell temp mid' not in headers:
                continue  # Skip the file if it doesn't have the required columns
            if soc_value is not None and cell_temp_mid_value is not None:
                # Create a short name for the file
                short_name = file.split('/')[-1].replace('.csv', '')
                file_info.append({
                    'path': file_url,
                    'SOC': soc_value,
                    'Cell temp mid': cell_temp_mid_value,
                    'name': short_name,
                    'folder': folder  # Add folder info for legend
                })
else:
    st.warning("No folders found matching the selected criteria.")
    st.stop()

# Save metadata cache
save_metadata_cache(metadata_cache)

if not file_info:
    st.warning("No data files found after applying the filters.")
    st.stop()

####################################################################################################

# Sidebar sliders for SOC and Cell temp mid
min_soc = min(info['SOC'] for info in file_info)
max_soc = max(info['SOC'] for info in file_info)
min_temp = min(info['Cell temp mid'] for info in file_info if info['Cell temp mid'] is not None)
max_temp = max(info['Cell temp mid'] for info in file_info if info['Cell temp mid'] is not None)

if min_soc == max_soc:
    st.sidebar.write(f"Only one SOC value available: {min_soc}")
    selected_soc_range = (min_soc, max_soc)
else:
    selected_soc_range = st.sidebar.slider("State Of Charge [%]", min_soc, max_soc, (95, 100))

if min_temp == max_temp:
    st.sidebar.write(f"Only one Cell Temp value available: {min_temp}")
    selected_temp_range = (min_temp, max_temp)
else:
    selected_temp_range = st.sidebar.slider("Battery Temperature [°C]", min_temp, max_temp, (min_temp, max_temp))

# Filter files based on selected ranges
filtered_file_info = [
    info for info in file_info
    if selected_soc_range[0] <= info['SOC'] <= selected_soc_range[1]
    and (min_temp is None or selected_temp_range[0] <= info['Cell temp mid'] <= selected_temp_range[1])
]

if not filtered_file_info:
    st.warning("No data files match the selected SOC and temperature ranges.")
    st.stop()

####################################################################################################

columns_to_plot = {
    "Max Discharge Power [kW]": "Max discharge power",
    "Battery Power [kW]": "Battery power",
    "Battery Current [A]": "Battery current",
    "Battery Voltage [V]": "Battery voltage",
    "Front/Rear Motor Power [kW]": ["F power", "R power"],
    "Combined Motor Power [kW]": ["F power", "R power"],
    "Front/Rear Motor Torque [Nm]": ["F torque", "R torque"],
    "Combined Motor Torque [Nm]": ["F torque", "R torque"]
}
selected_columns = []
for label in columns_to_plot.keys():
    if st.sidebar.checkbox(label, key=f"y_{label}"):
        selected_columns.append(label)

if not selected_columns:
    st.warning("Please select at least one column to plot.")
    st.stop()

# X-Axis selection
selected_x_axis = "Speed"

####################################################################################################

# Initialize plot data
plot_data = []

# Predefined list of colors for different cars
predefined_colors = ['#0000FF', '#FF0000', '#FFA500', '#008000', '#800080', '#A52A2A', '#FFC0CB', '#808080', '#808000', '#00FFFF']

# Prepare plot data with fixed colors for each unique subfolder
folder_colors = {}
for i, info in enumerate(filtered_file_info):
    folder_path = info['folder']['path']
    legend_label = f"{info['folder']['model']} {info['folder']['variant']} {info['folder']['model_year']} {info['folder']['battery']} {info['folder']['rear_motor']} {info['folder']['acceleration_mode']}"
    if legend_label not in folder_colors:
        folder_colors[legend_label] = predefined_colors[len(folder_colors) % len(predefined_colors)]

    response = requests.get(info['path'])
    content = response.content.decode('utf-8')
    df = pd.read_csv(StringIO(content))

    # Fill forward and backward to handle NaN values
    df = df.ffill().bfill()

    # Filter invalid values
    df = df[(df['SOC'] >= 0) & (df['SOC'] <= 101) & (df['Cell temp mid'] >= 0) & (df['Cell temp mid'] <= 70)]

    # Filter rows where speed is between 0 kph and 210 kph
    if 'Speed' in df.columns:
        df = df[(df['Speed'] >= 0) & (df['Speed'] <= 210)]

    # Ensure speed values are strictly increasing
    df = df[df['Speed'].diff().fillna(1) > 0]

    # Collect subset columns for dropna
    subset_columns = [selected_x_axis]

    # Collect columns based on user selection and their existence in df.columns
    for column in selected_columns:
        y_cols = columns_to_plot[column]
        if isinstance(y_cols, list):
            subset_columns.extend(y_cols)
        else:
            subset_columns.append(y_cols)

    # Filter subset_columns to include only those present in df.columns
    subset_columns = [col for col in subset_columns if col in df.columns]

    # Check if subset_columns is not empty
    if subset_columns:
        # Drop rows with NaN in the required columns
        df.dropna(subset=subset_columns, inplace=True)
    else:
        # Handle the case where none of the selected columns are present
        st.warning(f"No valid columns found in the data for selected options in file {info['name']}. Skipping this file.")
        continue  # Skip to the next file

    # Plot selected columns
    for column in selected_columns:
        y_cols = columns_to_plot[column]

        if isinstance(y_cols, list):
            # For columns that involve multiple sub-columns
            available_cols = [col for col in y_cols if col in df.columns]
            missing_cols = [col for col in y_cols if col not in df.columns]

            if column in ["Combined Motor Power [kW]", "Combined Motor Torque [Nm]"]:
                if not available_cols:
                    st.warning(f"No motor data available for {column} in file {info['name']}. Skipping.")
                    continue
                combined_value = df[available_cols].sum(axis=1, skipna=True)
                # Apply filters if needed
                if column == "Combined Motor Power [kW]":
                    combined_value = combined_value[combined_value >= 20]  # Filter combined motor power values below 20 kW
                smoothed_y = combined_value
                plot_data.append(pd.DataFrame({
                    'X': df[selected_x_axis].loc[smoothed_y.index],
                    'Y': smoothed_y,
                    'Label': f"{legend_label} - Combined Motor {'Power' if 'Power' in column else 'Torque'}",
                    'Color': folder_colors[legend_label]
                }))
                if missing_cols:
                    st.info(f"Columns {missing_cols} not found. Summing available motor data for {info['name']}.")
            else:
                # For individual motor power or torque
                for sub_col in available_cols:
                    smoothed_y = df[sub_col]
                    plot_data.append(pd.DataFrame({
                        'X': df[selected_x_axis].loc[smoothed_y.index],
                        'Y': smoothed_y,
                        'Label': f"{legend_label} - {sub_col}",
                        'Color': folder_colors[legend_label]
                    }))
                if missing_cols:
                    st.info(f"Columns {missing_cols} not found in data for {info['name']}. Skipping those.")
        else:
            # For single-column entries
            if y_cols not in df.columns:
                st.warning(f"Column {y_cols} not found in data for {info['name']}. Skipping.")
                continue
            smoothed_y = df[y_cols]
            if 'Battery power' in y_cols:
                smoothed_y = smoothed_y[smoothed_y >= 40]  # Filter battery power values below 40 kW
            plot_data.append(pd.DataFrame({
                'X': df[selected_x_axis].loc[smoothed_y.index],
                'Y': smoothed_y,
                'Label': f"{legend_label} - {column}",
                'Color': folder_colors[legend_label]
            }))

# Convert plot data to a DataFrame
if plot_data:
    plot_df = pd.concat(plot_data)

    # Filter out rows where 'X' or 'Y' have NaN values to prevent lines from connecting back to the start
    plot_df.dropna(subset=['X', 'Y'], inplace=True)

    # Create a color map for each label
    unique_labels = plot_df['Label'].unique()
    color_map = {label: folder_colors[label.split(" - ")[0]] for label in unique_labels}

    # Slider for smoothing
    smoothing_value = st.sidebar.slider("Line Smoothing", min_value=0, max_value=20, value=20)

    # Apply smoothing if smoothing_value is greater than 0
    if smoothing_value > 0:
        for label in unique_labels:
            y_values = plot_df.loc[plot_df['Label'] == label, 'Y'].values
            if len(y_values) >= smoothing_value:
                smoothed_values = uniform_filter1d(y_values, size=smoothing_value)
                plot_df.loc[plot_df['Label'] == label, 'Y'] = smoothed_values

    fig = px.line(plot_df, x='X', y='Y', color='Label', labels={'X': 'Speed [kph]', 'Y': 'Values'}, color_discrete_map=color_map)

    # Apply the colors and make the lines wider
    for trace in fig.data:
        trace.update(line=dict(width=3))  # Set base line width

    # Add watermark
    fig.add_annotation(
        text="@eivissacopter",
        font=dict(size=20, color="lightgrey"),
        align="center",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        opacity=0.15,
        showarrow=False
    )

    # Move legend inside the chart and remove the "Label, Line Style"
    fig.update_layout(
        showlegend=True,
        xaxis_title='Speed [kph]',
        yaxis_title="Values" if len(selected_columns) > 1 else selected_columns[0],
        width=800,  # Adjust width as needed
        height=800,  # Adjust height as needed
        margin=dict(l=50, r=50, t=50, b=50),  # Adjust margin
        legend=dict(
            orientation="h",  # Horizontal legend
            yanchor="top",
            y=1.1,  # Position the legend above the plot
            xanchor="center",
            x=0.5,
            title=None  # Remove title "Label, Line Style"
        )
    )

    # Add dropdown to select colors for each line
    for label in unique_labels:
        color = st.sidebar.color_picker(f"Pick a color for {label}", color_map[label])
        color_map[label] = color

    # Update the color in the plot
    fig.for_each_trace(lambda trace: trace.update(line_color=color_map.get(trace.name, trace.line.color)))

    st.plotly_chart(fig, use_container_width=True)

else:
    st.write("No data available to plot with the selected options.")

####################################################################################################

# Animated Banner with logo and link
st.sidebar.markdown(
    """
    <style>
        .sidebar-content {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0rem;
        }
        .sidebar-content img {
            height: auto;
        }
        .sidebar-content .akku-wiki {
            width: 90px;  /* Set specific width for Akku Wiki logo */
        }
        .sidebar-content .buy-me-coffee {
            width: 240px;  /* Set specific width for Buy Me a Coffee logo */
        }
        .sidebar-content .follow-on-x {
            width: 110px;  /* Set specific width for Follow on X logo */
        }
        .sidebar-content .text {
            text-align: center;
            font-size: 12px;  /* Default font size for text */
        }
        .sidebar-content a {
            color: white;
            text-decoration: none;
            font-weight: bold;
        }
    </style>
    <div class="sidebar-content">
        <a href="https://www.tesla.com/de_de/referral/julien95870" target="_blank">
            <div>
                <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/Tesla_T_symbol.svg/482px-Tesla_T_symbol.svg.png" class="akku-wiki" alt="Akku Wiki">
                <div class="text">Referral</div>
            </div>
        </a>
        <a href="https://buymeacoffee.com/eivissa" target="_blank">
            <img src="https://media.giphy.com/media/o7RZbs4KAA6tvM4H6j/giphy.gif" class="buy-me-coffee" alt="Buy Me a Coffee">
        </a>
        <a href="https://x.com/eivissacopter" target="_blank">
            <img src="https://i.ibb.co/xLhFQNn/c23e7825a07e5e998bd361f9c991e12c-400x400-removebg-preview.png" class="follow-on-x" alt="Follow on X">
        </a>
    </div>
    """,
    unsafe_allow_html=True
)
