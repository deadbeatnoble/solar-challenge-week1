import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set page config
st.set_page_config(
    page_title="Solar Energy Dashboard",
    page_icon="☀️",
    layout="wide"
)

# Title
st.title("☀️ Solar Energy Dashboard - West Africa Comparison")
st.markdown("Interactive visualization of solar potential across Benin, Sierra Leone, and Togo")

# Load data (these would be your actual cleaned CSV files)
@st.cache_data
def load_data():
    try:
        # Replace with actual file paths
        benin_df = pd.read_csv('..\\data\\benin_clean.csv')
        sierra_leone_df = pd.read_csv('..\\data\\sierraleone_bumbuna_qc_clean.csv')
        togo_df = pd.read_csv('..\\data\\togo_dapaong_qc_clean.csv')
        
        # Add country identifier
        benin_df['Country'] = 'Benin'
        sierra_leone_df['Country'] = 'Sierra Leone'
        togo_df['Country'] = 'Togo'
        
        # Combine datasets
        all_data = pd.concat([benin_df, sierra_leone_df, togo_df], ignore_index=True)
        return all_data
    except FileNotFoundError:
        # Create sample data if files don't exist
        st.warning("Sample data loaded - Replace with actual cleaned CSV files")
        dates = pd.date_range(start='2023-01-01', periods=1000, freq='H')
        countries = ['Benin', 'Sierra Leone', 'Togo']
        data = []
        
        for country in countries:
            country_data = {
                'Timestamp': dates,
                'GHI': np.random.normal(250, 100, 1000),
                'DNI': np.random.normal(300, 120, 1000),
                'DHI': np.random.normal(150, 80, 1000),
                'Tamb': np.random.normal(28, 5, 1000),
                'WS': np.random.normal(3, 1.5, 1000),
                'Country': country
            }
            # Ensure positive values for solar irradiance
            country_data['GHI'] = np.abs(country_data['GHI'])
            country_data['DNI'] = np.abs(country_data['DNI'])
            country_data['DHI'] = np.abs(country_data['DHI'])
            
            df = pd.DataFrame(country_data)
            data.append(df)
        
        all_data = pd.concat(data, ignore_index=True)
        return all_data

# Load the data
df = load_data()

# Sidebar filters
st.sidebar.header("Filters")

# Country selection
countries = st.sidebar.multiselect(
    'Select Countries',
    options=df['Country'].unique(),
    default=df['Country'].unique()
)

# Date range selection
if 'Timestamp' in df.columns:
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    min_date = df['Timestamp'].min().date()
    max_date = df['Timestamp'].max().date()
    
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        mask = (df['Timestamp'].dt.date >= start_date) & (df['Timestamp'].dt.date <= end_date)
        df = df.loc[mask]

# Filter data based on country selection
if countries:
    df_filtered = df[df['Country'].isin(countries)]
else:
    df_filtered = df

# Main dashboard layout
col1, col2, col3 = st.columns(3)

# KPI Cards
with col1:
    avg_ghi = df_filtered['GHI'].mean() if 'GHI' in df_filtered.columns else 0
    st.metric(label="Average GHI (W/m²)", value=f"{avg_ghi:.2f}")

with col2:
    avg_tamb = df_filtered['Tamb'].mean() if 'Tamb' in df_filtered.columns else 0
    st.metric(label="Average Temperature (°C)", value=f"{avg_tamb:.2f}")

with col3:
    avg_ws = df_filtered['WS'].mean() if 'WS' in df_filtered.columns else 0
    st.metric(label="Average Wind Speed (m/s)", value=f"{avg_ws:.2f}")

# Country comparison plots
st.header("Country Comparison")

# Boxplot of GHI by country
if 'GHI' in df_filtered.columns:
    fig = px.box(df_filtered, x='Country', y='GHI', 
                 title='Distribution of Global Horizontal Irradiance (GHI) by Country',
                 color='Country')
    st.plotly_chart(fig, use_container_width=True)

# Time series plot
st.header("Time Series Analysis")

if 'Timestamp' in df_filtered.columns and 'GHI' in df_filtered.columns:
    time_series_data = df_filtered.groupby(['Timestamp', 'Country'])['GHI'].mean().reset_index()
    
    fig = px.line(time_series_data, x='Timestamp', y='GHI', color='Country',
                  title='GHI Over Time by Country')
    st.plotly_chart(fig, use_container_width=True)

# Correlation heatmap
st.header("Correlation Analysis")

numeric_cols = df_filtered.select_dtypes(include=[np.number]).columns.tolist()
if len(numeric_cols) > 1:
    # Limit to relevant solar metrics
    solar_cols = [col for col in ['GHI', 'DNI', 'DHI', 'Tamb', 'WS'] if col in numeric_cols]
    if len(solar_cols) > 1:
        corr_matrix = df_filtered[solar_cols].corr()
        
        fig = px.imshow(corr_matrix, 
                        title='Correlation Heatmap of Solar Variables',
                        text_auto=True,
                        aspect="auto")
        st.plotly_chart(fig, use_container_width=True)

# Scatter plot
st.header("Relationship Analysis")

if 'GHI' in df_filtered.columns and 'Tamb' in df_filtered.columns:
    fig = px.scatter(df_filtered, x='Tamb', y='GHI', color='Country',
                     title='Temperature vs GHI by Country',
                     hover_data=['Country'])
    st.plotly_chart(fig, use_container_width=True)

# Top regions table
st.header("Top Solar Potential Regions")

if 'GHI' in df_filtered.columns:
    top_regions = df_filtered.groupby('Country')['GHI'].agg(['mean', 'median', 'std']).round(2)
    top_regions.columns = ['Average GHI', 'Median GHI', 'Std Deviation']
    top_regions = top_regions.sort_values('Average GHI', ascending=False)
    
    st.dataframe(top_regions, use_container_width=True)

# Summary statistics
st.header("Summary Statistics")

if 'GHI' in df_filtered.columns:
    summary_stats = df_filtered.groupby('Country')['GHI'].agg(['count', 'mean', 'median', 'std', 'min', 'max']).round(2)
    summary_stats.columns = ['Count', 'Mean', 'Median', 'Std', 'Min', 'Max']
    st.dataframe(summary_stats, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("💡 **Tip**: Use the filters in the sidebar to customize your view and explore specific countries or time periods.")