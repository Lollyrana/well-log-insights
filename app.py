import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import io
import xlsxwriter

# PostgreSQL connection
DATABASE_URL = "postgresql://postgres:Lolly%40sql@localhost:5432/well_log_data"
engine = create_engine(DATABASE_URL)

# Function to load data from the database
def load_data():
    query = "SELECT * FROM well_log_data"
    return pd.read_sql(query, engine)

# Function to load sample data
def load_sample_data():
    # sample_data = {
    #     'depth': [1000, 1500, 2000, 2500],
    #     'rhob': [2.45, 2.55, 2.60, 2.50],
    #     'rild': [120, 95, 105, 130],
    #     'mn': [0.45, 0.50, 0.48, 0.47]
    # }
    df = pd.read_csv("log.csv")
    return df

# Function to plot well log data
def plot_well_log(df, column, label):
    plt.figure(figsize=(5, 8))
    plt.plot(df[column], df['Depth'], label=label)
    plt.gca().invert_yaxis()
    plt.xlabel(label)
    plt.ylabel("Depth")
    plt.grid(True)
    st.pyplot(plt)

# App Title
st.title("Well Log Insights")

# Data Option: Use sample data or upload data
use_sample_data = st.checkbox("Use Sample Data", value=False)

if use_sample_data:
    df = load_sample_data()
    st.success("Using sample data.")
else:
    # Data Upload
    uploaded_file = st.file_uploader("Upload Well Log Data (CSV format)", type="csv")
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        df.to_sql('well_log_data', engine, if_exists='replace', index=False)
        st.success("Data uploaded successfully and stored in PostgreSQL.")
    else:
        st.warning("No data uploaded. Please upload a file or use sample data.")
        df = pd.DataFrame()  # Empty DataFrame if no data is provided

# Display data if it exists
if not df.empty:
    st.subheader("Well Log Data")
    st.dataframe(df)

    # Select column to plot
    selected_log = st.selectbox("Select a log to plot", df.columns[1:], key="log_selection")

    # Plot well log data
    if selected_log:
        plot_well_log(df, selected_log, selected_log)

# Calculate porosity using density log
def calculate_porosity(df):
    rho_m = 2.65  # Matrix density
    rho_f = 1.0   # Fluid density
    df['porosity'] = (rho_m - df['RHOB']) / (rho_m - rho_f)
    return df

if not df.empty:
    df = calculate_porosity(df)

# Identify hydrocarbon zones based on resistivity
def identify_hydrocarbon_zones(df):
    df['hydrocarbon_zone'] = df.apply(lambda x: "Hydrocarbon" if x['RILD'] > 100 else "Water", axis=1)
    return df

if not df.empty:
    df = identify_hydrocarbon_zones(df)
    st.subheader("Hydrocarbon Zones")
    st.dataframe(df[['Depth', 'hydrocarbon_zone']])

# Crossplot of Neutron vs Density
def crossplot_neutron_density(df):
    plt.figure(figsize=(6, 6))
    plt.scatter(df['RHOB'], df['MN'], c='blue', alpha=0.5)
    plt.xlabel("Density (RHOB)")
    plt.ylabel("Neutron (MN)")
    plt.title("Neutron-Density Crossplot")
    st.pyplot(plt)

if not df.empty:
    crossplot_neutron_density(df)

# Data Export and Reporting
st.subheader('Data Export and Reporting')

if st.button('Download Well Log Data as Excel'):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Well Log Data')

    st.download_button(
        label='Download Excel File',
        data=buffer,
        file_name='well_log_data.xlsx',
        mime='application/vnd.ms-excel'
    )
