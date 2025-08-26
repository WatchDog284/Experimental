# main_app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime, timedelta

# --- Page Configuration ---
st.set_page_config(
    page_title="Sales Funnel Analytics",
    page_icon=" funnel",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Helper Functions ---
def get_df_from_file(uploaded_file):
    """
    Reads an uploaded file and returns a pandas DataFrame.
    Supports CSV and Excel formats.
    """
    try:
        file_extension = os.path.splitext(uploaded_file.name)[1]
        if file_extension == '.csv':
            return pd.read_csv(uploaded_file)
        elif file_extension in ['.xls', '.xlsx']:
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names
            # Always show sheet selector in sidebar if it's an Excel file
            sheet_name = st.sidebar.selectbox("Select a sheet from your workbook", sheet_names)
            return pd.read_excel(uploaded_file, sheet_name=sheet_name)
        else:
            st.error(f"Unsupported file format: {file_extension}")
            return None
    except Exception as e:
        st.error(f"An error occurred while reading the file: {e}")
        return None

def process_sales_data(df, column_map):
    """
    Processes the dataframe to calculate funnel metrics based on user-provided column mappings.
    """
    # Convert date columns to datetime objects
    for stage, col_name in column_map.items():
        if col_name != "None" and 'Date' in stage:
            df[col_name] = pd.to_datetime(df[col_name], errors='coerce')

    # Calculate time deltas between stages (in days)
    if column_map.get('SDL Date') != "None" and column_map.get('SDL First Touch Date') != "None":
        df['Days to First Touch'] = (df[column_map['SDL First Touch Date']] - df[column_map['SDL Date']]).dt.days
    if column_map.get('SDL First Touch Date') != "None" and column_map.get('SQL Date') != "None":
        df['Days First Touch to SQL'] = (df[column_map['SQL Date']] - df[column_map['SDL First Touch Date']]).dt.days

    return df

def find_default_column(columns, keywords, default="None"):
    """Tries to find a default column based on a list of keywords."""
    for col in columns:
        if any(keyword.lower() in col.lower() for keyword in keywords):
            return col
    return default

# --- Sidebar ---
with st.sidebar:
    st.title(" funnel Sales Funnel Analytics")
    st.info("Upload your sales lead data to generate a custom performance dashboard.")

    uploaded_file = st.file_uploader(
        "Upload your data file",
        type=['csv', 'xlsx', 'xls'],
        help="Supports CSV and Excel files."
    )
    
    column_map = {}
    date_range = None
    df = None

    if uploaded_file:
        df = get_df_from_file(uploaded_file)
        if df is not None:
            st.markdown("---")
            st.header("1. Map Your Columns")
            st.write("Tell the app which columns represent your funnel stages.")
            
            cols = ["None"] + df.columns.tolist()

            column_map['Lead ID'] = st.selectbox("Lead ID Column", cols, index=cols.index(find_default_column(cols, ['lead id', 'leadid'])))
            column_map['SDL Date'] = st.selectbox("Lead Creation Date (SDL)", cols, index=cols.index(find_default_column(cols, ['sdl date', 'creation date'])))
            column_map['SDL First Touch Date'] = st.selectbox("SDL First Touch Date", cols, index=cols.index(find_default_column(cols, ['clarification date', 'first touch'])))
            column_map['SQL Date'] = st.selectbox("Sales Qualified Date (SQL)", cols, index=cols.index(find_default_column(cols, ['sql date'])))
            column_map['Disqualified Date'] = st.selectbox("Disqualified Date", cols, index=cols.index(find_default_column(cols, ['disqualified date'])))
            column_map['Disqualification Reason'] = st.selectbox("Disqualification Reason", cols, index=cols.index(find_default_column(cols, ['disqualification reason', 'reason'])))
            
            st.markdown("---")
            st.header("2. Select Date Range")
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=4)
            
            date_range = st.date_input("Select the week for analysis", (start_of_week, end_of_week))


# --- Main Application ---
st.header("Sales Performance Dashboard")

if uploaded_file and df is not None and column_map.get('Lead ID') != 'None':
    
    # --- Exclude rows with "Not Found" in any ID column ---
    df_filtered = df.copy()
    id_cols_to_check = [col for col in df_filtered.columns if 'id' in col.lower()]
    
    if id_cols_to_check:
        initial_rows = len(df_filtered)
        for id_col in id_cols_to_check:
            # Ensure case-insensitive comparison by converting column to string and lowercasing
            df_filtered = df_filtered[df_filtered[id_col].astype(str).str.lower() != 'not found']
        
        rows_removed = initial_rows - len(df_filtered)
        if rows_removed > 0:
            st.success(f"Data Cleaning: Removed {rows_removed} rows where an ID column contained 'Not Found'.")

    df_processed = process_sales_data(df_filtered, column_map)
    
    tab1, tab2, tab3 = st.tabs(["Funnel Overview", "Weekly Performance", "Disqualification Analysis"])

    # --- Tab 1: Funnel Overview ---
    with tab1:
        st.subheader("Funnel Conversion Comparison")
        col1, col2 = st.columns(2)

        # --- Overall Funnel Chart ---
        with col1:
            st.markdown("#### Overall Funnel (All Time)")
            total_leads = df_processed[column_map['Lead ID']].nunique() if column_map['Lead ID'] != 'None' else 0
            first_touch_leads = df_processed[column_map['SDL First Touch Date']].notna().sum() if column_map['SDL First Touch Date'] != 'None' else 0
            sql_leads = df_processed[column_map['SQL Date']].notna().sum() if column_map['SQL Date'] != 'None' else 0
            
            funnel_stages, funnel_counts = [], []
            if total_leads > 0: funnel_stages.append('Total Leads (SDL)'); funnel_counts.append(total_leads)
            if first_touch_leads > 0: funnel_stages.append('SDL First Touch'); funnel_counts.append(first_touch_leads)
            if sql_leads > 0: funnel_stages.append('Sales Qualified (SQL)'); funnel_counts.append(sql_leads)

            if len(funnel_stages) > 1:
                fig_funnel = go.Figure(go.Funnel(y=funnel_stages, x=funnel_counts, textposition="inside", textinfo="value+percent initial"))
                fig_funnel.update_layout(title_text="Overall Conversion")
                st.plotly_chart(fig_funnel, use_container_width=True)
            else:
                st.warning("Not enough data to build overall funnel.")

        # --- Weekly Cohort Funnel Chart ---
        with col2:
            st.markdown("#### This Week's Funnel")
            if date_range and len(date_range) == 2 and column_map['SDL Date'] != 'None':
                start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
                
                # Filter for the weekly cohort based on SDL date
                weekly_cohort_df = df_processed[df_processed[column_map['SDL Date']].dt.normalize().between(start_date, end_date)]
                
                if not weekly_cohort_df.empty:
                    weekly_total = weekly_cohort_df[column_map['Lead ID']].nunique()
                    weekly_first_touch = weekly_cohort_df[column_map['SDL First Touch Date']].notna().sum() if column_map['SDL First Touch Date'] != 'None' else 0
                    weekly_sql = weekly_cohort_df[column_map['SQL Date']].notna().sum() if column_map['SQL Date'] != 'None' else 0

                    weekly_stages, weekly_counts = [], []
                    if weekly_total > 0: weekly_stages.append('Total Leads (SDL)'); weekly_counts.append(weekly_total)
                    if weekly_first_touch > 0: weekly_stages.append('SDL First Touch'); weekly_counts.append(weekly_first_touch)
                    if weekly_sql > 0: weekly_stages.append('Sales Qualified (SQL)'); weekly_counts.append(weekly_sql)

                    if len(weekly_stages) > 1:
                        fig_weekly_funnel = go.Figure(go.Funnel(y=weekly_stages, x=weekly_counts, textposition="inside", textinfo="value+percent initial"))
                        fig_weekly_funnel.update_layout(title_text=f"Weekly Cohort ({start_date.strftime('%b %d')} - {end_date.strftime('%b %d')})")
                        st.plotly_chart(fig_weekly_funnel, use_container_width=True)
                    else:
                        st.info("Not enough data in this week's cohort to build a funnel.")
                else:
                    st.info("No new leads were created in the selected week.")
            else:
                st.warning("Select a date range and map the 'SDL Date' column to see the weekly funnel.")

    # --- Tab 2: Weekly Performance ---
    with tab2:
        st.subheader("Weekly Performance Analysis")
        if date_range and len(date_range) == 2:
            start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
            st.write(f"Analyzing activity between **{start_date.strftime('%Y-%m-%d')}** and **{end_date.strftime('%Y-%m-%d')}**")

            # --- Total Activity This Week ---
            st.markdown("#### Total Activity This Week")
            kpi_data = {}
            for stage, col_name in column_map.items():
                if col_name != "None" and 'Date' in stage:
                    count = df_processed[df_processed[col_name].dt.normalize().between(start_date, end_date)].shape[0]
                    kpi_data[f"{stage.replace(' Date', '')}s"] = count
            
            kpi_cols = st.columns(len(kpi_data))
            for i, (stage_name, count) in enumerate(kpi_data.items()):
                kpi_cols[i].metric(stage_name, count)

            st.markdown("---")
            
            # --- Cohort Analysis for New Leads Created This Week ---
            st.markdown("#### Progress of New Leads Created This Week")
            
            sdl_col = column_map['SDL Date']
            if sdl_col != 'None':
                weekly_cohort_df = df_processed[df_processed[sdl_col].dt.normalize().between(start_date, end_date)].copy()
                
                if not weekly_cohort_df.empty:
                    first_touch_col = column_map['SDL First Touch Date']
                    sql_col = column_map['SQL Date']
                    disq_col = column_map['Disqualified Date']

                    first_touch_in_cohort = weekly_cohort_df[weekly_cohort_df[first_touch_col].dt.normalize().between(start_date, end_date)] if first_touch_col != 'None' else pd.DataFrame()
                    sql_in_cohort = weekly_cohort_df[weekly_cohort_df[sql_col].dt.normalize().between(start_date, end_date)] if sql_col != 'None' else pd.DataFrame()
                    disq_in_cohort = weekly_cohort_df[weekly_cohort_df[disq_col].dt.normalize().between(start_date, end_date)] if disq_col != 'None' else pd.DataFrame()

                    # Display Cohort KPIs
                    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                    kpi1.metric("New SDLs", len(weekly_cohort_df))
                    kpi2.metric("First Touch from Cohort", len(first_touch_in_cohort))
                    kpi3.metric("SQLs from Cohort", len(sql_in_cohort))
                    kpi4.metric("Disqualified from Cohort", len(disq_in_cohort))
                else:
                    st.info("No new leads (SDLs) were created in the selected date range.")
            else:
                st.warning("Map the 'SDL Date' column to see the new lead cohort analysis.")
        else:
            st.warning("Please select a valid date range to begin the weekly analysis.")

    # --- Tab 3: Disqualification Analysis ---
    with tab3:
        st.subheader("Disqualification Analysis")
        reason_col = column_map.get('Disqualification Reason')
        disq_date_col = column_map.get('Disqualified Date')
        sdl_date_col = column_map.get('SDL Date')

        if date_range and len(date_range) == 2:
            start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
            
            # --- Chart 1: Top reasons for ALL leads disqualified this week ---
            st.markdown(f"#### Top Disqualification Reasons This Week (All Leads)")
            if reason_col != 'None' and disq_date_col != 'None':
                weekly_disq_df = df_processed[df_processed[disq_date_col].dt.normalize().between(start_date, end_date)]
                
                if not weekly_disq_df.empty:
                    reason_counts = weekly_disq_df[reason_col].value_counts().nlargest(10)
                    fig = px.bar(reason_counts, y=reason_counts.index, x=reason_counts.values, orientation='h', title="Top 10 Reasons (All Leads)", text_auto=True)
                    fig.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Number of Leads", yaxis_title="Reason")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No leads were disqualified in the selected date range.")
            else:
                st.info("Select 'Disqualification Reason' and 'Disqualified Date' columns to see this chart.")

            st.markdown("---")

            # --- Chart 2: Reasons for THIS WEEK'S NEW LEADS that were disqualified ---
            st.markdown(f"#### Disqualification Reasons for New Leads Created This Week")
            if reason_col != 'None' and disq_date_col != 'None' and sdl_date_col != 'None':
                # Get the cohort of new leads
                weekly_cohort_df = df_processed[df_processed[sdl_date_col].dt.normalize().between(start_date, end_date)]
                # From that cohort, find the ones disqualified
                cohort_disq_df = weekly_cohort_df[weekly_cohort_df[disq_date_col].notna()]

                if not cohort_disq_df.empty:
                    cohort_reason_counts = cohort_disq_df[reason_col].value_counts().nlargest(10)
                    fig_cohort = px.bar(cohort_reason_counts, y=cohort_reason_counts.index, x=cohort_reason_counts.values, orientation='h', title="Top 10 Reasons (New Leads Only)", text_auto=True)
                    fig_cohort.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Number of Leads", yaxis_title="Reason")
                    st.plotly_chart(fig_cohort, use_container_width=True)
                else:
                    st.info("None of the new leads from this week have been disqualified yet.")
            else:
                st.info("Select 'SDL Date', 'Disqualified Date', and 'Disqualification Reason' columns to see this cohort analysis.")

        else:
            st.warning("Please select a valid date range to begin analysis.")

elif not uploaded_file:
    st.info("👆 Upload your sales lead data to get started!")
    st.subheader("Analyze Your Sales Funnel")
    st.markdown("""
    This dashboard is designed to help you understand your sales process by analyzing:
    - **Conversion Rates:** See how many leads make it through each stage.
    - **Weekly Performance:** Track all activity and the progress of new lead cohorts.
    - **Disqualification Reasons:** Identify the main reasons for losing potential deals.
    """)
else:
    st.warning("Please select the required columns in the sidebar to begin the analysis.")
