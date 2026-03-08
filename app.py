import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & CUSTOM CSS
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Mukhyamantri Tirath Yatra Dashboard", page_icon="🚌", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    footer {visibility: hidden;}
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        padding: 5% 10% 5% 10%;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    @media (prefers-color-scheme: dark) {
        div[data-testid="metric-container"] {
            background-color: #1e1e1e;
            border: 1px solid #333;
        }
    }
    .minute-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        text-align: center;
        font-size: 10px;
        color: #888888;
        background-color: #ffffff;
        padding: 10px 0px;
        z-index: 999;
    }
    @media (prefers-color-scheme: dark) {
        .minute-footer { background-color: #0e1117; }
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. DATA CONNECTION (Fetching all 3 Vendors)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=10) # Refreshes every 10 seconds
def load_data():
    # 👉 PASTE YOUR 3 EXACT GOOGLE SHEET IDs HERE 👈
    VENDOR_SHEETS = {
        "EaseMyTrip": "1ejxAeYp0RFiXGq07A2VJbasOatfNCB_y3PTY5v4ct0g",
        "MachConferences": "1gBabD_as3WvaSq4JUX_Si5dJBGxQNTuxY3_ILDEVbEs",
        "Zenith": "1gQwS1Uy4RuBpAL4kO39LqmxxIAHKDv_N3Wz7bULARgg"
    
    all_dataframes = []
    
    for vendor_name, sheet_id in VENDOR_SHEETS.items():
        if sheet_id and sheet_id != "PASTE_..._SHEET_ID_HERE" and not sheet_id.startswith("PASTE"):
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
            try:
                df = pd.read_csv(csv_url)
                df = df.dropna(subset=['Date', 'Yatri Name'], how='all')
                df['Vendor'] = vendor_name 
                all_dataframes.append(df)
            except Exception as e:
                st.warning(f"⚠️ Could not load data for {vendor_name}. Please check the Sheet ID and sharing settings.")
    
    if all_dataframes:
        master_df = pd.concat(all_dataframes, ignore_index=True)
        master_df['Date'] = pd.to_datetime(master_df['Date'], format='%d/%m/%Y', errors='coerce')
        
        # Format LGD Code gracefully (removing .0 if it read it as a float)
        master_df['LGD Code'] = master_df['LGD Code'].fillna('').astype(str).str.replace(r'\.0$', '', regex=True)
        master_df['Village Name'] = master_df['Village Name'].fillna('').astype(str)
        
        # Create the combined LGD - Village column
        master_df['LGD_Village'] = master_df.apply(
            lambda x: f"{x['LGD Code']} - {x['Village Name']}" if x['LGD Code'] and x['Village Name'] else x['LGD Code'] + x['Village Name'],
            axis=1
        )
        master_df['LGD_Village'] = master_df['LGD_Village'].replace('', pd.NA)
        
        return master_df
    else:
        return pd.DataFrame() 

try:
    data = load_data()
except Exception as e:
    st.error(f"⚠️ Fatal error compiling master database: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 3. SIDEBAR FILTERS
# -----------------------------------------------------------------------------
st.sidebar.image("Aam_Aadmi_Party_logo_(English).svg.png", width=150)
st.sidebar.header("Filter Data")

if data.empty:
    st.warning("Awaiting data from vendors...")
    st.stop()

# Date Filter
min_date, max_date = data['Date'].min(), data['Date'].max()
if pd.notna(min_date) and pd.notna(max_date):
    start_date, end_date = st.sidebar.date_input("Select Date Range", value=[min_date, max_date], min_value=min_date, max_value=max_date)
else:
    start_date, end_date = None, None

# Vendor Filter
vendors = ["All"] + list(data['Vendor'].dropna().unique())
selected_vendor = st.sidebar.selectbox("Select Vendor Agency", vendors)

# District Filter
districts = ["All"] + list(data['District'].dropna().unique())
selected_district = st.sidebar.selectbox("Select District", districts)

# Halka Filter
if selected_district != "All":
    halkas = ["All"] + list(data[data['District'] == selected_district]['Halka'].dropna().unique())
else:
    halkas = ["All"] + list(data['Halka'].dropna().unique())
selected_halka = st.sidebar.selectbox("Select Halka", halkas)

# LGD Code - Village Filter (NEW)
lgd_options = ["All"] + sorted([str(x) for x in data['LGD_Village'].dropna().unique()])
selected_lgd = st.sidebar.selectbox("Select LGD Code - Village", lgd_options)


# Apply All Filters
filtered_df = data.copy()

if start_date and end_date:
    filtered_df = filtered_df[(filtered_df['Date'].dt.date >= start_date) & (filtered_df['Date'].dt.date <= end_date)]
if selected_vendor != "All":
    filtered_df = filtered_df[filtered_df['Vendor'] == selected_vendor]
if selected_district != "All":
    filtered_df = filtered_df[filtered_df['District'] == selected_district]
if selected_halka != "All":
    filtered_df = filtered_df[filtered_df['Halka'] == selected_halka]
if selected_lgd != "All":
    filtered_df = filtered_df[filtered_df['LGD_Village'] == selected_lgd]

# -----------------------------------------------------------------------------
# 4. DASHBOARD HEADER & KPIs
# -----------------------------------------------------------------------------
st.title("🚌 Mukhyamantri Tirath Yatra Operations")
st.markdown("Live tracking and demographic breakdown of the Yatra initiative across Punjab.")

# Metric Calculations
total_yatras = len(filtered_df) # As requested, each row = 1 Yatra
total_yatris = len(filtered_df) # Passengers count
districts_covered = filtered_df['District'].nunique()
halkas_covered = filtered_df['Halka'].nunique()
avg_age = filtered_df['Age'].mean()

# 5 Responsive KPI Columns
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric(label="Total Yatras", value=f"{total_yatras:,}")
kpi2.metric(label="Total Yatris", value=f"{total_yatris:,}")
kpi3.metric(label="Districts Covered", value=districts_covered)
kpi4.metric(label="Halkas Covered", value=halkas_covered)
kpi5.metric(label="Average Age", value=f"{avg_age:.1f} yrs" if pd.notna(avg_age) else "0 yrs")

st.markdown("---")

# -----------------------------------------------------------------------------
# 5. VISUALIZATIONS
# -----------------------------------------------------------------------------
if total_yatris > 0:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Gender Distribution")
        gender_counts = filtered_df['Gender'].value_counts().reset_index()
        gender_counts.columns = ['Gender', 'Count']
        fig_gender = px.pie(gender_counts, values='Count', names='Gender', hole=0.4,
                            color_discrete_sequence=['#FF9999', '#66B2FF'])
        fig_gender.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_gender, use_container_width=True)

    with col2:
        # Yatras over time replacing Age Demographics
        st.subheader("Yatras Over Time")
        daily_counts = filtered_df.groupby('Date').size().reset_index(name='Yatras')
        fig_trend = px.line(daily_counts, x='Date', y='Yatras', markers=True,
                            line_shape='spline', color_discrete_sequence=['#ff7f0e'])
        fig_trend.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Turnout by District now spans the entire width for better readability
    st.subheader("Turnout by District")
    dist_counts = filtered_df['District'].value_counts().reset_index()
    dist_counts.columns = ['District', 'Yatras']
    fig_dist = px.bar(dist_counts, x='District', y='Yatras', text='Yatras',
                      color='Yatras', color_continuous_scale='Blues')
    fig_dist.update_traces(textposition='outside')
    fig_dist.update_layout(margin=dict(t=0, b=0, l=0, r=0), coloraxis_showscale=False)
    st.plotly_chart(fig_dist, use_container_width=True)

    # -------------------------------------------------------------------------
    # 6. RAW DATA TABLE
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("Raw Yatri Manifest")
    display_df = filtered_df.copy()
    display_df['Date'] = display_df['Date'].dt.strftime('%d/%m/%Y')
    
    cols = ['Vendor', 'Date', 'District', 'Halka', 'Block Name', 'LGD_Village', 'Booth No.', 'Guide Name', 'Guide Contact No.', 'Yatri Name', 'Gender', 'Age', 'Yatri Contact No.', 'Voter ID No.']
    display_df = display_df[[c for c in cols if c in display_df.columns]]
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

else:
    st.warning("No Yatra data available for the selected filters.")

# -----------------------------------------------------------------------------
# 7. FOOTER
# -----------------------------------------------------------------------------
st.markdown('<div class="minute-footer">made with ❤️ by Jay Joshi</div>', unsafe_allow_html=True)
        
