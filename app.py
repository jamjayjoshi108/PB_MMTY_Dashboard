import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & CUSTOM CSS (State-of-the-art look)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Mukhyamantri Tirath Yatra Dashboard", page_icon="🚌", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for minute footer and cleaner metric cards
st.markdown("""
    <style>
    /* Metric Card Styling */
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        padding: 5% 10% 5% 10%;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    
    /* Dark mode adjustments for metrics */
    @media (prefers-color-scheme: dark) {
        div[data-testid="metric-container"] {
            background-color: #1e1e1e;
            border: 1px solid #333;
        }
    }

    /* Minute Footer Styling */
    .minute-footer {
        text-align: center;
        font-size: 10px;
        color: #888888;
        padding-top: 50px;
        padding-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. DATA CONNECTION & FETCHING
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# 2. DATA CONNECTION & FETCHING (Public Sheet Method)
# -----------------------------------------------------------------------------
# ttl=10 acts as your trigger: Streamlit will automatically fetch fresh data 
# from the Google Sheet every 10 seconds, making it essentially real-time!
@st.cache_data(ttl=10) 
def load_data():
    # Replace with your actual Google Sheet ID
    SHEET_ID = "YOUR_EXACT_SHEET_ID_HERE"
    
    # Create the public export URL
    csv_url = f"https://docs.google.com/spreadsheets/d/1ejxAeYp0RFiXGq07A2VJbasOatfNCB_y3PTY5v4ct0g/export?format=csv&gid=0"
    
    # Read directly using Pandas (No st.connection or secrets required!)
    df = pd.read_csv(csv_url)
    
    # Clean up empty rows
    df = df.dropna(subset=['Date', 'Yatri Name'], how='all')
    
    # Convert Date column to datetime format
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
    
    return df

try:
    data = load_data()
except Exception as e:
    st.error(f"⚠️ Error fetching data from Google Sheets: {e}")
    st.stop()


# -----------------------------------------------------------------------------
# 3. SIDEBAR FILTERS
# -----------------------------------------------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Aam_Aadmi_Party_logo_%28English%29.svg/1200px-Aam_Aadmi_Party_logo_%28English%29.svg.png", width=150)
st.sidebar.header("Filter Data")

# Date Filter
min_date = data['Date'].min()
max_date = data['Date'].max()

if pd.notna(min_date) and pd.notna(max_date):
    start_date, end_date = st.sidebar.date_input(
        "Select Date Range",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
else:
    start_date, end_date = None, None

# District Filter
districts = ["All"] + list(data['District'].dropna().unique())
selected_district = st.sidebar.selectbox("Select District", districts)

# Halka Filter
if selected_district != "All":
    halkas = ["All"] + list(data[data['District'] == selected_district]['Halka'].dropna().unique())
else:
    halkas = ["All"] + list(data['Halka'].dropna().unique())
selected_halka = st.sidebar.selectbox("Select Halka", halkas)

# Apply Filters
filtered_df = data.copy()

if start_date and end_date:
    filtered_df = filtered_df[(filtered_df['Date'].dt.date >= start_date) & (filtered_df['Date'].dt.date <= end_date)]

if selected_district != "All":
    filtered_df = filtered_df[filtered_df['District'] == selected_district]

if selected_halka != "All":
    filtered_df = filtered_df[filtered_df['Halka'] == selected_halka]


# -----------------------------------------------------------------------------
# 4. DASHBOARD HEADER & KPIs
# -----------------------------------------------------------------------------
st.title("🚌 Mukhyamantri Tirath Yatra Operations")
st.markdown("Live tracking and demographic breakdown of the Yatra initiative across Punjab.")

# Calculate KPIs
total_yatris = len(filtered_df)
districts_covered = filtered_df['District'].nunique()
halkas_covered = filtered_df['Halka'].nunique()
avg_age = filtered_df['Age'].mean()

# Display KPIs in responsive columns
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric(label="Total Yatris", value=f"{total_yatris:,}")
kpi2.metric(label="Districts Covered", value=districts_covered)
kpi3.metric(label="Halkas Covered", value=halkas_covered)
kpi4.metric(label="Average Age", value=f"{avg_age:.1f} yrs" if pd.notna(avg_age) else "0 yrs")

st.markdown("---")


# -----------------------------------------------------------------------------
# 5. VISUALIZATIONS
# -----------------------------------------------------------------------------
if total_yatris > 0:
    col1, col2 = st.columns(2)

    with col1:
        # GENDER PIE CHART
        st.subheader("Gender Distribution")
        gender_counts = filtered_df['Gender'].value_counts().reset_index()
        gender_counts.columns = ['Gender', 'Count']
        fig_gender = px.pie(gender_counts, values='Count', names='Gender', hole=0.4,
                            color_discrete_sequence=['#FF9999', '#66B2FF', '#99FF99'])
        fig_gender.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_gender, use_container_width=True)

    with col2:
        # AGE HISTOGRAM
        st.subheader("Age Demographics")
        fig_age = px.histogram(filtered_df, x="Age", nbins=10, 
                               color_discrete_sequence=['#1f77b4'],
                               labels={'Age': 'Age Bracket'})
        fig_age.update_layout(yaxis_title="Number of Yatris", margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_age, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        # YATRIS PER DISTRICT BAR CHART
        st.subheader("Turnout by District")
        dist_counts = filtered_df['District'].value_counts().reset_index()
        dist_counts.columns = ['District', 'Yatris']
        fig_dist = px.bar(dist_counts, x='District', y='Yatris', text='Yatris',
                          color='Yatris', color_continuous_scale='Blues')
        fig_dist.update_traces(textposition='outside')
        fig_dist.update_layout(margin=dict(t=0, b=0, l=0, r=0), coloraxis_showscale=False)
        st.plotly_chart(fig_dist, use_container_width=True)

    with col4:
        # TIME SERIES TREND
        st.subheader("Yatris Over Time")
        daily_counts = filtered_df.groupby('Date').size().reset_index(name='Yatris')
        fig_trend = px.line(daily_counts, x='Date', y='Yatris', markers=True,
                            line_shape='spline', color_discrete_sequence=['#ff7f0e'])
        fig_trend.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_trend, use_container_width=True)

    # -------------------------------------------------------------------------
    # 6. RAW DATA TABLE
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("Raw Yatri Manifest")
    # Format the date back to readable string for the table
    display_df = filtered_df.copy()
    display_df['Date'] = display_df['Date'].dt.strftime('%d/%m/%Y')
    st.dataframe(display_df, use_container_width=True, hide_index=True)

else:
    st.warning("No Yatra data available for the selected filters.")

# -----------------------------------------------------------------------------
# 7. THE MINUTE FOOTER
# -----------------------------------------------------------------------------
st.markdown('<div class="minute-footer">made with ❤️ by Jay Joshi</div>', unsafe_allow_html=True)
