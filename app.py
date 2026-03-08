import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & AAP CUSTOM CSS
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Mukhyamantri Tirath Yatra Dashboard", page_icon="🚌", layout="wide", initial_sidebar_state="expanded")

# AAP Color Palette: Navy Blue (#0066A4) and Broom Yellow (#F2B200)
st.markdown("""
    <style>
    /* Nuke the useless top space */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        margin-top: 0rem !important;
    }
    
    footer {visibility: hidden;}
    
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
    VENDOR_SHEETS = {
        "EaseMyTrip": "1ejxAeYp0RFiXGq07A2VJbasOatfNCB_y3PTY5v4ct0g",
        "MachConferences": "1gBabD_as3WvaSq4JUX_Si5dJBGxQNTuxY3_ILDEVbEs",
        "Zenith": "1gQwS1Uy4RuBpAL4kO39LqmxxIAHKDv_N3Wz7bULARgg"
    }
    
    all_dataframes = []
    
    for vendor_name, sheet_id in VENDOR_SHEETS.items():
        if sheet_id:
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
            try:
                df = pd.read_csv(csv_url)
                df = df.dropna(subset=['Date', 'Yatri Name'], how='all')
                df['Vendor'] = vendor_name 
                all_dataframes.append(df)
            except Exception as e:
                st.warning(f"⚠️ Could not load data for {vendor_name}.")
    
    if all_dataframes:
        master_df = pd.concat(all_dataframes, ignore_index=True)
        master_df['Date'] = pd.to_datetime(master_df['Date'], format='%d/%m/%Y', errors='coerce')
        
        master_df['LGD Code'] = master_df['LGD Code'].fillna('').astype(str).str.replace(r'\.0$', '', regex=True)
        master_df['Village Name'] = master_df['Village Name'].fillna('').astype(str)
        
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

min_date, max_date = data['Date'].min(), data['Date'].max()
if pd.notna(min_date) and pd.notna(max_date):
    start_date, end_date = st.sidebar.date_input("Select Date Range", value=[min_date, max_date], min_value=min_date, max_value=max_date)
else:
    start_date, end_date = None, None

vendors = ["All"] + list(data['Vendor'].dropna().unique())
selected_vendor = st.sidebar.selectbox("Select Vendor Agency", vendors)

districts = ["All"] + list(data['District'].dropna().unique())
selected_district = st.sidebar.selectbox("Select District", districts)

if selected_district != "All":
    halkas = ["All"] + list(data[data['District'] == selected_district]['Halka'].dropna().unique())
else:
    halkas = ["All"] + list(data['Halka'].dropna().unique())
selected_halka = st.sidebar.selectbox("Select Halka", halkas)

lgd_options = ["All"] + sorted([str(x) for x in data['LGD_Village'].dropna().unique()])
selected_lgd = st.sidebar.selectbox("Select LGD Code - Village", lgd_options)

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
# 4. DASHBOARD HEADER & BULLETPROOF KPIs
# -----------------------------------------------------------------------------
st.title("🚌 Mukhyamantri Tirath Yatra")

total_yatras = len(filtered_df) 
districts_covered = filtered_df['District'].nunique()
halkas_covered = filtered_df['Halka'].nunique()
avg_age = filtered_df['Age'].mean()

# Pure HTML/CSS function to guarantee KPIs render perfectly and look amazing
def create_kpi_card(title, value):
    return f"""
    <div style="background: linear-gradient(135deg, #0066A4 0%, #002244 100%); 
                padding: 20px 10px; border-radius: 10px; border-bottom: 5px solid #F2B200;
                box-shadow: 0px 4px 10px rgba(0,0,0,0.1); text-align: center; margin-bottom: 15px;">
        <p style="color: #F2B200; font-size: 1.1rem; font-weight: bold; margin-bottom: 5px; text-transform: uppercase;">{title}</p>
        <h2 style="color: #FFFFFF; font-size: 2.5rem; font-weight: 800; margin: 0;">{value}</h2>
    </div>
    """

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.markdown(create_kpi_card("Total Yatras", f"{total_yatras:,}"), unsafe_allow_html=True)
kpi2.markdown(create_kpi_card("Districts Covered", f"{districts_covered:,}"), unsafe_allow_html=True)
kpi3.markdown(create_kpi_card("Halkas Covered", f"{halkas_covered:,}"), unsafe_allow_html=True)
kpi4.markdown(create_kpi_card("Average Age", f"{avg_age:.1f} yrs" if pd.notna(avg_age) else "0 yrs"), unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 5. VISUALIZATIONS (DIFFERENTIATED WITH BORDERS)
# -----------------------------------------------------------------------------
if total_yatras > 0:
    col1, col2, col3, col4 = st.columns(4)

    # 1. Gender Pie Chart
    with col1:
        with st.container(border=True): # Adds a distinct box around the chart
            st.markdown("👥 **Gender Distribution**")
            gender_counts = filtered_df['Gender'].value_counts().reset_index()
            gender_counts.columns = ['Gender', 'Count']
            fig_gender = px.pie(gender_counts, values='Count', names='Gender', hole=0.4,
                                color_discrete_sequence=['#0066A4', '#F2B200'])
            fig_gender.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig_gender, use_container_width=True)

    # 2. Yatras Line Chart
    with col2:
        with st.container(border=True):
            st.markdown("📈 **Yatras Over Time**")
            daily_yatras = filtered_df.groupby('Date').size().reset_index(name='Yatras')
            fig_trend_yatras = px.line(daily_yatras, x='Date', y='Yatras', markers=True,
                                       line_shape='spline', color_discrete_sequence=['#F2B200'])
            fig_trend_yatras.update_traces(marker=dict(color='#0066A4', size=6))
            fig_trend_yatras.update_layout(margin=dict(t=10, b=10, l=10, r=10), xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_trend_yatras, use_container_width=True)

    # 3. Turnout Bar Chart
    with col3:
        with st.container(border=True):
            st.markdown("📍 **Turnout by District**")
            dist_counts = filtered_df['District'].value_counts().reset_index()
            dist_counts.columns = ['District', 'Turnout']
            fig_dist = px.bar(dist_counts, x='District', y='Turnout')
            fig_dist.update_traces(marker_color='#0066A4')
            fig_dist.update_layout(margin=dict(t=10, b=10, l=10, r=10), xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_dist, use_container_width=True)

    # 4. Yatris Line Chart
    with col4:
        with st.container(border=True):
            st.markdown("👤 **Yatris Over Time**")
            daily_yatris = filtered_df.groupby('Date').size().reset_index(name='Yatris')
            fig_trend_yatris = px.line(daily_yatris, x='Date', y='Yatris', markers=True,
                                       line_shape='spline', color_discrete_sequence=['#0066A4']) 
            fig_trend_yatris.update_traces(marker=dict(color='#F2B200', size=6)) 
            fig_trend_yatris.update_layout(margin=dict(t=10, b=10, l=10, r=10), xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_trend_yatris, use_container_width=True)

    # -------------------------------------------------------------------------
    # 6. RAW DATA TABLE
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("📝 **Raw Yatri Manifest**")
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

# ----------------------------------------------------------------------------------------------------------------------------------------------------------

# import streamlit as st
# import pandas as pd
# import plotly.express as px

# # -----------------------------------------------------------------------------
# # 1. PAGE CONFIGURATION & AAP CUSTOM CSS
# # -----------------------------------------------------------------------------
# st.set_page_config(page_title="Mukhyamantri Tirath Yatra Dashboard", page_icon="🚌", layout="wide", initial_sidebar_state="expanded")

# # AAP Color Palette: Navy Blue (#0066A4) and Broom Yellow (#F2B200)
# st.markdown("""
#     <style>
#     footer {visibility: hidden;}
    
#     /* Branded Metric Cards */
#     div[data-testid="metric-container"] {
#         background-color: #f8f9fa;
#         border: 1px solid #e0e0e0;
#         border-top: 4px solid #0066A4; /* AAP Blue Accent */
#         padding: 5% 10% 5% 10%;
#         border-radius: 10px;
#         box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
#     }
    
#     /* Make the metric numbers AAP Blue */
#     div[data-testid="stMetricValue"] {
#         color: #0066A4 !important;
#     }
    
#     @media (prefers-color-scheme: dark) {
#         div[data-testid="metric-container"] {
#             background-color: #1e1e1e;
#             border: 1px solid #333;
#             border-top: 4px solid #F2B200; /* AAP Yellow for Dark Mode */
#         }
#         div[data-testid="stMetricValue"] {
#             color: #F2B200 !important; /* Yellow text for Dark Mode */
#         }
#     }
    
#     .minute-footer {
#         position: fixed;
#         bottom: 0;
#         left: 0;
#         width: 100%;
#         text-align: center;
#         font-size: 10px;
#         color: #888888;
#         background-color: #ffffff;
#         padding: 10px 0px;
#         z-index: 999;
#     }
#     @media (prefers-color-scheme: dark) {
#         .minute-footer { background-color: #0e1117; }
#     }
#     </style>
# """, unsafe_allow_html=True)

# # -----------------------------------------------------------------------------
# # 2. DATA CONNECTION (Fetching all 3 Vendors)
# # -----------------------------------------------------------------------------
# @st.cache_data(ttl=10) # Refreshes every 10 seconds
# def load_data():
#     VENDOR_SHEETS = {
#         "EaseMyTrip": "1ejxAeYp0RFiXGq07A2VJbasOatfNCB_y3PTY5v4ct0g",
#         "MachConferences": "1gBabD_as3WvaSq4JUX_Si5dJBGxQNTuxY3_ILDEVbEs",
#         "Zenith": "1gQwS1Uy4RuBpAL4kO39LqmxxIAHKDv_N3Wz7bULARgg"
#     }
    
#     all_dataframes = []
    
#     for vendor_name, sheet_id in VENDOR_SHEETS.items():
#         if sheet_id:
#             csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
#             try:
#                 df = pd.read_csv(csv_url)
#                 df = df.dropna(subset=['Date', 'Yatri Name'], how='all')
#                 df['Vendor'] = vendor_name 
#                 all_dataframes.append(df)
#             except Exception as e:
#                 st.warning(f"⚠️ Could not load data for {vendor_name}.")
    
#     if all_dataframes:
#         master_df = pd.concat(all_dataframes, ignore_index=True)
#         master_df['Date'] = pd.to_datetime(master_df['Date'], format='%d/%m/%Y', errors='coerce')
        
#         # Format LGD Code gracefully
#         master_df['LGD Code'] = master_df['LGD Code'].fillna('').astype(str).str.replace(r'\.0$', '', regex=True)
#         master_df['Village Name'] = master_df['Village Name'].fillna('').astype(str)
        
#         # Create the combined LGD - Village column
#         master_df['LGD_Village'] = master_df.apply(
#             lambda x: f"{x['LGD Code']} - {x['Village Name']}" if x['LGD Code'] and x['Village Name'] else x['LGD Code'] + x['Village Name'],
#             axis=1
#         )
#         master_df['LGD_Village'] = master_df['LGD_Village'].replace('', pd.NA)
        
#         return master_df
#     else:
#         return pd.DataFrame() 

# try:
#     data = load_data()
# except Exception as e:
#     st.error(f"⚠️ Fatal error compiling master database: {e}")
#     st.stop()

# # -----------------------------------------------------------------------------
# # 3. SIDEBAR FILTERS
# # -----------------------------------------------------------------------------
# st.sidebar.image("Aam_Aadmi_Party_logo_(English).svg.png", width=150)
# st.sidebar.header("Filter Data")

# if data.empty:
#     st.warning("Awaiting data from vendors...")
#     st.stop()

# min_date, max_date = data['Date'].min(), data['Date'].max()
# if pd.notna(min_date) and pd.notna(max_date):
#     start_date, end_date = st.sidebar.date_input("Select Date Range", value=[min_date, max_date], min_value=min_date, max_value=max_date)
# else:
#     start_date, end_date = None, None

# vendors = ["All"] + list(data['Vendor'].dropna().unique())
# selected_vendor = st.sidebar.selectbox("Select Vendor Agency", vendors)

# districts = ["All"] + list(data['District'].dropna().unique())
# selected_district = st.sidebar.selectbox("Select District", districts)

# if selected_district != "All":
#     halkas = ["All"] + list(data[data['District'] == selected_district]['Halka'].dropna().unique())
# else:
#     halkas = ["All"] + list(data['Halka'].dropna().unique())
# selected_halka = st.sidebar.selectbox("Select Halka", halkas)

# lgd_options = ["All"] + sorted([str(x) for x in data['LGD_Village'].dropna().unique()])
# selected_lgd = st.sidebar.selectbox("Select LGD Code - Village", lgd_options)

# # Apply Filters
# filtered_df = data.copy()

# if start_date and end_date:
#     filtered_df = filtered_df[(filtered_df['Date'].dt.date >= start_date) & (filtered_df['Date'].dt.date <= end_date)]
# if selected_vendor != "All":
#     filtered_df = filtered_df[filtered_df['Vendor'] == selected_vendor]
# if selected_district != "All":
#     filtered_df = filtered_df[filtered_df['District'] == selected_district]
# if selected_halka != "All":
#     filtered_df = filtered_df[filtered_df['Halka'] == selected_halka]
# if selected_lgd != "All":
#     filtered_df = filtered_df[filtered_df['LGD_Village'] == selected_lgd]

# # -----------------------------------------------------------------------------
# # 4. DASHBOARD HEADER & KPIs
# # -----------------------------------------------------------------------------
# st.title("🚌 Mukhyamantri Tirath Yatra")

# total_yatras = len(filtered_df) 
# total_yatris = len(filtered_df) 
# districts_covered = filtered_df['District'].nunique()
# halkas_covered = filtered_df['Halka'].nunique()
# avg_age = filtered_df['Age'].mean()

# kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
# kpi1.metric(label="Total Yatras", value=f"{total_yatras:,}")
# kpi2.metric(label="Total Yatris", value=f"{total_yatris:,}")
# kpi3.metric(label="Districts Covered", value=districts_covered)
# kpi4.metric(label="Halkas Covered", value=halkas_covered)
# kpi5.metric(label="Average Age", value=f"{avg_age:.1f} yrs" if pd.notna(avg_age) else "0 yrs")

# st.markdown("---")

# # -----------------------------------------------------------------------------
# # 5. VISUALIZATIONS (Strictly AAP Branded)
# # -----------------------------------------------------------------------------
# if total_yatris > 0:
#     # ROW 1: Gender and Yatras Over Time
#     col1, col2 = st.columns(2)

#     with col1:
#         st.subheader("Gender Distribution")
#         gender_counts = filtered_df['Gender'].value_counts().reset_index()
#         gender_counts.columns = ['Gender', 'Count']
#         fig_gender = px.pie(gender_counts, values='Count', names='Gender', hole=0.4,
#                             color_discrete_sequence=['#0066A4', '#F2B200']) # AAP Blue & Yellow
#         fig_gender.update_layout(margin=dict(t=0, b=0, l=0, r=0))
#         st.plotly_chart(fig_gender, use_container_width=True)

#     with col2:
#         st.subheader("Yatras Over Time")
#         daily_yatras = filtered_df.groupby('Date').size().reset_index(name='Yatras')
#         fig_trend_yatras = px.line(daily_yatras, x='Date', y='Yatras', markers=True,
#                                    line_shape='spline', color_discrete_sequence=['#F2B200']) # AAP Yellow Line
#         fig_trend_yatras.update_traces(marker=dict(color='#0066A4', size=8)) # AAP Blue Dots
#         fig_trend_yatras.update_layout(margin=dict(t=0, b=0, l=0, r=0))
#         st.plotly_chart(fig_trend_yatras, use_container_width=True)

#     st.markdown("<br>", unsafe_allow_html=True)
    
#     # ROW 2: Turnout by District and Yatris Over Time
#     col3, col4 = st.columns(2)
    
#     with col3:
#         st.subheader("Turnout by District")
#         dist_counts = filtered_df['District'].value_counts().reset_index()
#         dist_counts.columns = ['District', 'Turnout']
#         fig_dist = px.bar(dist_counts, x='District', y='Turnout', text='Turnout')
#         fig_dist.update_traces(marker_color='#0066A4', textposition='outside') # STRICT AAP Blue
#         fig_dist.update_layout(margin=dict(t=0, b=0, l=0, r=0))
#         st.plotly_chart(fig_dist, use_container_width=True)

#     with col4:
#         st.subheader("Yatris Over Time")
#         daily_yatris = filtered_df.groupby('Date').size().reset_index(name='Yatris')
#         fig_trend_yatris = px.line(daily_yatris, x='Date', y='Yatris', markers=True,
#                                    line_shape='spline', color_discrete_sequence=['#0066A4']) # AAP Blue Line
#         fig_trend_yatris.update_traces(marker=dict(color='#F2B200', size=8)) # AAP Yellow Dots
#         fig_trend_yatris.update_layout(margin=dict(t=0, b=0, l=0, r=0))
#         st.plotly_chart(fig_trend_yatris, use_container_width=True)


#     # -------------------------------------------------------------------------
#     # 6. RAW DATA TABLE
#     # -------------------------------------------------------------------------
#     st.markdown("---")
#     st.subheader("Raw Yatri Manifest")
#     display_df = filtered_df.copy()
#     display_df['Date'] = display_df['Date'].dt.strftime('%d/%m/%Y')
    
#     cols = ['Vendor', 'Date', 'District', 'Halka', 'Block Name', 'LGD_Village', 'Booth No.', 'Guide Name', 'Guide Contact No.', 'Yatri Name', 'Gender', 'Age', 'Yatri Contact No.', 'Voter ID No.']
#     display_df = display_df[[c for c in cols if c in display_df.columns]]
    
#     st.dataframe(display_df, use_container_width=True, hide_index=True)

# else:
#     st.warning("No Yatra data available for the selected filters.")

# # -----------------------------------------------------------------------------
# # 7. FOOTER
# # -----------------------------------------------------------------------------
# st.markdown('<div class="minute-footer">made with ❤️ by Jay Joshi</div>', unsafe_allow_html=True)

