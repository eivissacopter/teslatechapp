import streamlit as st
import plotly.express as px
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import plotly.graph_objects as go
import plotly.io as pio


# Set page config as the first Streamlit command
st.set_page_config(page_title="Tesla Battery Analysis", page_icon=":battery:", layout="wide")

# Set default Plotly template and color sequence
pio.templates.default = "plotly"
color_sequence = [
    "#0068c9",
    "#83c9ff",
    "#ff2b2b",
    "#ffabab",
    "#29b09d",
    "#7defa1",
    "#ff8700",
    "#ffd16a",
    "#6d3fc0",
    "#d5dae5",
]

# Function to fetch data from Google Sheets
@st.cache_data
def fetch_data():
    # Google Sheets API setup
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Fetching credentials from Streamlit secrets
    creds_dict = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"]
    }

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    # Define the URL of the Google Sheets
    url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    spreadsheet = client.open_by_url(url)
    sheet = spreadsheet.worksheet("Database")  # Open the 'Database' worksheet

    # Fetch all data from the sheet, including the header row
    data = sheet.get_all_values()

####################################################################################################################

    # Filter out columns with empty headers or headers starting with an underscore
    header = data[0]
    filtered_header = []
    keep_indices = []
    stop_index = None
    
    for i, col in enumerate(header):
        col = col.strip()
        if col and not col.startswith('_'):
            filtered_header.append(col)
            keep_indices.append(i)
        if col == "DC Ratio":
            stop_index = i
            break

    if stop_index is not None:
        keep_indices = keep_indices[:stop_index + 1]

    # Filter the data based on the kept indices
    filtered_data = [[row[i] for i in keep_indices] for row in data]

    # Fix duplicate headers
    unique_header = []
    for col in filtered_header:
        col = col.strip()  # Trim whitespace
        if col not in unique_header:
            unique_header.append(col)
        else:
            # Add a suffix to make the header unique
            suffix = 1
            new_col = f"{col}_{suffix}"
            while new_col in unique_header:
                suffix += 1
                new_col = f"{col}_{suffix}"
            unique_header.append(new_col)

    # Convert data to DataFrame
    df = pd.DataFrame(filtered_data[1:], columns=unique_header)

     # Handle 'Age' column conversion
    df['Age'] = df['Age'].str.replace(" Months", "").str.replace(",", ".").replace('', np.nan).astype(float)

    # Clean up the 'Odometer' column to ensure it is numeric
    df['Odometer'] = df['Odometer'].str.replace(',', '').str.extract('(\d+)').astype(float)
    
    # Replace all commas with dots in all columns
    df = df.apply(lambda x: x.str.replace(',', '.') if x.dtype == "object" else x)

    # Add negative sign to specific columns if they exist
    columns_to_negate = ['Degradation']
    for col in columns_to_negate:
       if col in df.columns:
           df[col] = '-' + df[col]

    # Replace '0,0%' in 'Degradation' with NaN
    df['Degradation'] = df['Degradation'].replace('-0.0%', float('NaN'))

    # Clean 'Rated Range' and 'Capacity Net Now' columns
    df['Rated Range'] = df['Rated Range'].str.replace(' km', '')
    df['Rated Range'] = pd.to_numeric(df['Rated Range'], errors='coerce')

    df['Capacity Net Now'] = df['Capacity Net Now'].str.replace(' kWh', '').str.replace(',', '.')
    df['Capacity Net Now'] = pd.to_numeric(df['Capacity Net Now'], errors='coerce')

    # Convert Degradation to numeric
    df['Degradation'] = pd.to_numeric(df['Degradation'].str.replace('%', ''), errors='coerce')

    # Clean 'Daily SOC Limit' and 'DC Ratio' columns
    df['Daily SOC Limit'] = df['Daily SOC Limit'].str.replace('%', '').replace('', np.nan).astype(float)
    df['DC Ratio'] = df['DC Ratio'].str.replace('%', '').replace('', np.nan).astype(float)

    return df

# Fetch the data using the caching function
df = fetch_data()

####################################################################################################################

# Streamlit app setup

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
        <img src="https://uploads.tff-forum.de/original/4X/5/2/3/52397973df71db6122c1eda4c5c558d2ca70686c.jpeg" alt="Tesla Battery Analysis">
        <h1><span>🔋</span> Tesla Battery Analysis <span>🔋</span></h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Add Google Forms logo with text and correctly placed animated arrows with increased spacing
st.markdown(
    """
    <style>
        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.05); opacity: 0.9; }
            100% { transform: scale(1); opacity: 1; }
        }
        .google-form-logo {
            display: block;
            margin: 0rem auto; /* Centers the logo horizontally below the header */
            width: 300px;  /* Adjust the width of the logo as necessary */
            height: auto;
            animation: pulse 2s infinite ease-in-out;
        }
        .arrow-text {
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 24px;
            font-weight: bold;
            margin-top: 20px;
        }
        .arrow {
            animation: blinker 3s linear infinite;
            font-size: 24px;
            margin: 0 20px; /* Increased spacing from text */
        }
        @keyframes blinker {
            50% {
                opacity: 0;
            }
        }
    </style>
    <div class="arrow-text">
        <span>Add your data here</span>
        <span class="arrow">🡢</span>
        <a href="https://forms.gle/WtFayqANSr9kwKv39" target="_blank">
            <img src="https://i.ibb.co/YZvSDRm/google-forms-400x182-removebg-preview.png" class="google-form-logo" alt="Google Forms Survey">
        </a>
        <span class="arrow">🡠</span>
        <span>Add your data here</span>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)

####################################################################################################################

# Sidebar setup

# Initialize the filtered dataframe
if "filtered_df" not in st.session_state:
    st.session_state.filtered_df = df.copy()

# Get the latest row
latest_row = df.iloc[-3:]

# Display the latest row at the top
st.markdown(
    """
    <div>
        Latest Entries
    </div>
    """,
    unsafe_allow_html=True
)

st.write(latest_row)

############################################################

# Create filter for Tesla
tesla = st.sidebar.multiselect(":red_car: Tesla", df["Tesla"].unique())
if not tesla:
    df2 = df.copy()
else:
    df2 = df[df["Tesla"].isin(tesla)]

# Create filter for Version based on selected Tesla
version = st.sidebar.multiselect(":vertical_traffic_light: Version", df2["Version"].unique())
if not version:
    df3 = df2.copy()
else:
    df3 = df2[df2["Version"].isin(version)]

# Create filter for Battery based on selected Tesla and Version
battery = st.sidebar.multiselect(":battery: Battery", df3["Battery"].unique())

# Apply combined filters to update the session state
if not tesla and not version and not battery:
    st.session_state.filtered_df = df.copy()
else:
    conditions = []
    if tesla:
        conditions.append(df["Tesla"].isin(tesla))
    if version:
        conditions.append(df["Version"].isin(version))
    if battery:
        conditions.append(df["Battery"].isin(battery))
    
    condition = conditions[0]
    for cond in conditions[1:]:
        condition &= cond

    st.session_state.filtered_df = df[condition]

############################################################

# Create filter for Minimum Age and Maximum Age side by side
col3, col4 = st.sidebar.columns(2)
min_age = col3.number_input(":clock630: MIN Age (months)", min_value=0, value=int(st.session_state.filtered_df["Age"].min()))
max_age = col4.number_input(":clock12: MAX Age (months)", min_value=0, value=int(st.session_state.filtered_df["Age"].max()))

# Create filter for Minimum ODO and Maximum ODO side by side
col5, col6 = st.sidebar.columns(2)
min_odo = col5.number_input(":arrow_forward: MIN ODO (km)", min_value=0, value=int(st.session_state.filtered_df["Odometer"].min()), step=10000)
max_odo = col6.number_input(":fast_forward: MAX ODO (km)", min_value=0, value=int(st.session_state.filtered_df["Odometer"].max()), step=10000)

# Columns layout for Y-axis and X-axis selection
col7, col8 = st.sidebar.columns(2)

# Radio buttons for Y-axis data selection
y_axis_data = col7.radio(":arrow_up_down: Y-axis Data", ['Degradation', 'Capacity', 'Rated Range'], index=0)

# Radio buttons for X-axis data selection
x_axis_data = col8.radio(":left_right_arrow: X-axis Data", ['Age', 'Odometer', 'Cycles'], index=0)

# Apply filters for Age and Odometer
st.session_state.filtered_df = st.session_state.filtered_df[(st.session_state.filtered_df["Age"] >= min_age) & (st.session_state.filtered_df["Age"] <= max_age)]
st.session_state.filtered_df = st.session_state.filtered_df[(st.session_state.filtered_df["Odometer"] >= min_odo) & (st.session_state.filtered_df["Odometer"] <= max_odo)]

# Determine Y-axis column name based on selection
if y_axis_data == 'Degradation':
    y_column = 'Degradation'
    y_label = 'Degradation [%]'
elif y_axis_data == 'Capacity':
    y_column = 'Capacity Net Now'  # This should match the original column name
    y_label = 'Capacity [kWh]'
else:  # 'Rated Range'
    y_column = 'Rated Range'
    y_label = 'Rated Range [km]'

# Determine X-axis label based on selection
if x_axis_data == 'Age':
    x_column = 'Age'
    x_label = 'Age [months]'
elif x_axis_data == 'Odometer':
    x_column = 'Odometer'
    x_label = 'Odometer [km]'
else:  # 'Cycles'
    x_column = 'Cycles'
    x_label = 'Cycles [n]'

# Toggle switch for trend line
add_trend_line = st.sidebar.checkbox(":chart_with_downwards_trend: Add Trend Line", value=False)

# Add a checkbox for Polynomial Regression in the sidebar
if add_trend_line:
    trend_line_type = st.sidebar.selectbox(
        "Trend Line Type", 
        ['Linear Regression', 'Logarithmic Regression', 'Polynomial Regression (3rd Degree)']
    )

# Add checkboxes for additional filters
show_daily_soc_limit = st.sidebar.checkbox(":battery: Set Daily SOC", value=False)
if show_daily_soc_limit:
    col1, col2 = st.sidebar.columns(2)
    daily_soc_limit_values = st.session_state.filtered_df["Daily SOC Limit"].dropna().astype(float)
    daily_soc_min = col1.number_input("Min SOC Limit", value=float(daily_soc_limit_values.min()), step=10.0, min_value=50.0, max_value=100.0, key="daily_soc_min")
    daily_soc_max = col2.number_input("Max SOC Limit", value=float(daily_soc_limit_values.max()), step=10.0, min_value=50.0, max_value=100.0, key="daily_soc_max")
    st.session_state.filtered_df = st.session_state.filtered_df[
        (st.session_state.filtered_df["Daily SOC Limit"].astype(float) >= daily_soc_min) & 
        (st.session_state.filtered_df["Daily SOC Limit"].astype(float) <= daily_soc_max)
    ]

show_dc_ratio = st.sidebar.checkbox(":fuelpump: Set AC/DC Ratio", value=False)
if show_dc_ratio:
    col3, col4 = st.sidebar.columns(2)
    dc_ratio_values = st.session_state.filtered_df["DC Ratio"].dropna().astype(float)
    dc_ratio_min = col3.number_input("Min DC Ratio", value=float(dc_ratio_values.min()), step=25.0, min_value=0.0, max_value=100.0, key="dc_ratio_min")
    dc_ratio_max = col4.number_input("Max DC Ratio", value=float(dc_ratio_values.max()), step=25.0, min_value=0.0, max_value=100.0, key="dc_ratio_max")
    st.session_state.filtered_df = st.session_state.filtered_df[
        (st.session_state.filtered_df["DC Ratio"].astype(float) >= dc_ratio_min) & 
        (st.session_state.filtered_df["DC Ratio"].astype(float) <= dc_ratio_max)
    ]

# Filter the data based on the user-selected criteria
st.session_state.filtered_df = st.session_state.filtered_df[(st.session_state.filtered_df["Age"] >= min_age) & (st.session_state.filtered_df["Age"] <= max_age)]
st.session_state.filtered_df = st.session_state.filtered_df[(st.session_state.filtered_df["Odometer"] >= min_odo) & (st.session_state.filtered_df["Odometer"] <= max_odo)]

# Show number of rows in filtered data
st.sidebar.write(f"Filtered Data Rows: {st.session_state.filtered_df.shape[0]}")

# Reset filters button
# if st.sidebar.button("Reset Filters"):
#     # Reset the displayed data to the original dataframe
#     st.session_state.filtered_df = df.copy()

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
        <a href="https://tff-forum.de/t/wiki-akkuwiki-model-3-model-y-cybertruck/107641?u=eivissa" target="_blank">
            <div>
                <img src="https://i.ibb.co/vBvVFTg/TFF-Logo-ohne-Schrift-removebg-preview.png" class="akku-wiki" alt="Akku Wiki">
                <div class="text">Akku Wiki</div>
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

####################################################################################################################

# Ensure the 'Cycles' column is numeric
st.session_state.filtered_df[x_column] = pd.to_numeric(st.session_state.filtered_df[x_column], errors='coerce')

# Filter out non-positive values from the x_column and rows with NaNs in x_column or y_column
filtered_df = st.session_state.filtered_df[(st.session_state.filtered_df[x_column] > 0) & st.session_state.filtered_df[x_column].notna() & st.session_state.filtered_df[y_column].notna()]

# Sort the filtered_df by the x_column
filtered_df = filtered_df.sort_values(by=x_column)

# Create scatterplot with watermark and color sequence
fig = px.scatter(
    filtered_df, x=x_column, y=y_column, color='Battery',
    labels={x_column: x_label, y_column: y_label},
    color_discrete_sequence=color_sequence,
    title=""
)

# Add trend line if selected
if add_trend_line:
    if trend_line_type == 'Linear Regression':
        fig = px.scatter(
            st.session_state.filtered_df, x=x_column, y=y_column, color='Battery',
            labels={x_column: x_label, y_column: y_label},
            trendline='ols',
            color_discrete_sequence=color_sequence,
            title=""
        )
    elif trend_line_type == 'Logarithmic Regression':
        # Perform logarithmic regression for each battery type
        batteries = filtered_df['Battery'].unique()
        for battery in batteries:
            battery_df = filtered_df[filtered_df['Battery'] == battery]
            X = np.log(battery_df[x_column].values.reshape(-1, 1))
            y = battery_df[y_column].values.reshape(-1, 1)
            
            log_reg = LinearRegression()
            log_reg.fit(X, y)
            
            # Generate values for plotting the trendline
            x_range = np.linspace(X.min(), X.max(), 100)
            y_pred = log_reg.predict(x_range.reshape(-1, 1))
            
            # Get the color of the corresponding scatter points
            battery_color = fig.data[filtered_df['Battery'].unique().tolist().index(battery)].marker.color
            
            # Add the trendline trace with the corresponding color
            battery_trace = go.Scatter(x=np.exp(x_range).flatten(), y=y_pred.flatten(), mode='lines', name=f"{battery} Logarithmic Trendline", line=dict(color=battery_color))
            fig.add_trace(battery_trace)
    elif trend_line_type == 'Polynomial Regression (3rd Degree)':
        from sklearn.preprocessing import PolynomialFeatures
        
        # Perform polynomial regression for each battery type
        batteries = filtered_df['Battery'].unique()
        for battery in batteries:
            battery_df = filtered_df[filtered_df['Battery'] == battery]
            X = battery_df[x_column].values.reshape(-1, 1)
            y = battery_df[y_column].values.reshape(-1, 1)
            
            poly = PolynomialFeatures(degree=3)
            X_poly = poly.fit_transform(X)
            
            poly_reg = LinearRegression()
            poly_reg.fit(X_poly, y)
            
            # Generate values for plotting the trendline
            x_range = np.linspace(X.min(), X.max(), 100).reshape(-1, 1)
            x_range_poly = poly.transform(x_range)
            y_pred = poly_reg.predict(x_range_poly)
            
            # Get the color of the corresponding scatter points
            battery_color = fig.data[filtered_df['Battery'].unique().tolist().index(battery)].marker.color
            
            # Add the trendline trace with the corresponding color
            battery_trace = go.Scatter(x=x_range.flatten(), y=y_pred.flatten(), mode='lines', name=f"{battery} 3rd Degree Polynomial Trendline", line=dict(color=battery_color))
            fig.add_trace(battery_trace)

# Add watermark to the plot
fig.add_annotation(
    text="@eivissacopter",
    font=dict(size=20, color="lightgrey"),
    align="center",
    xref="paper",
    yref="paper",
    x=0.5,
    y=0.5,
    opacity=0.05,
    showarrow=False
)

# Plot the figure
st.plotly_chart(fig, use_container_width=True)

# Add download button for the scatterplot
img_bytes = fig.to_image(format="png", engine="kaleido", scale=3)  # Ensure scaling for better resolution
st.download_button(label="Download Chart", data=img_bytes, file_name="tesla_battery_analysis.png", mime="image/png")

####################################################################################################################

# Determine the denominator column based on the X-axis selection
if x_axis_data == 'Age':
    denominator_column = 'Age'
    x_label = 'Month'
    divisor = 1  # No additional scaling
elif x_axis_data == 'Odometer':
    denominator_column = 'Odometer'
    x_label = '1000km]'
    divisor = 1000  # Scale Odometer to 1,000 km
else:  # 'Cycles'
    denominator_column = 'Cycles'
    x_label = 'Cycle'
    divisor = 1  # No additional scaling

# Convert Degradation and the selected denominator column to numeric, coerce errors to NaN and drop rows with NaN values
st.session_state.filtered_df['Degradation'] = pd.to_numeric(st.session_state.filtered_df['Degradation'], errors='coerce')
st.session_state.filtered_df[denominator_column] = pd.to_numeric(st.session_state.filtered_df[denominator_column], errors='coerce')
st.session_state.filtered_df = st.session_state.filtered_df.dropna(subset=['Degradation', denominator_column])

# Calculate degradation per selected X-axis value
st.session_state.filtered_df['DegradationPerX'] = st.session_state.filtered_df['Degradation'] / (st.session_state.filtered_df[denominator_column] / divisor)

# Filter out rows where DegradationPerX is NaN, 0, or infinite
st.session_state.filtered_df = st.session_state.filtered_df.replace([np.inf, -np.inf], np.nan).dropna(subset=['DegradationPerX'])
st.session_state.filtered_df = st.session_state.filtered_df[st.session_state.filtered_df['DegradationPerX'] != 0]

# Group by Battery and calculate the average degradation per selected X-axis value
avg_degradation_per_x = st.session_state.filtered_df.groupby('Battery')['DegradationPerX'].mean().reset_index()

# Sort values from low to high
avg_degradation_per_x = avg_degradation_per_x.sort_values(by='DegradationPerX', ascending=True)

# Create horizontal bar chart with color sequence
bar_fig = px.bar(
    avg_degradation_per_x, x='DegradationPerX', y='Battery', orientation='h',
    labels={'DegradationPerX': f'Average Degradation / {x_label}'},
    color_discrete_sequence=color_sequence,
    title=f'Average Degradation per {x_label}'
)

# Invert the x-axis
bar_fig.update_xaxes(autorange='reversed')

# Position the text at the end of each bar and format as percentage
bar_fig.update_traces(texttemplate='%{x:.2f}%', textposition='outside')

# Add watermark to the bar chart
bar_fig.add_annotation(
    text="@eivissacopter",
    font=dict(size=20, color="lightgrey"),
    align="center",
    xref="paper",
    yref="paper",
    x=0.5,
    y=0.5,
    opacity=0.05,
    showarrow=False
)

# Plot the bar chart
st.plotly_chart(bar_fig, use_container_width=True)

# Add download button for the bar chart
bar_img_bytes = bar_fig.to_image(format="png", engine="kaleido", scale=5)  # Ensure scaling for better resolution
st.download_button(label="Download Chart", data=bar_img_bytes, file_name="average_degradation_per_x.png", mime="image/png")
