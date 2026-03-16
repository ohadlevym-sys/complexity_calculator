import streamlit as st
import pandas as pd
import plotly.express as px
import economist as engine
import Main as main

# 1. Page Configuration
st.set_page_config(initial_sidebar_state="expanded", layout="wide")

# Custom CSS to ensure the sidebar is wide enough for the management buttons
st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 400px !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session States
if 'all_inventories' not in st.session_state:
    st.session_state.all_inventories = {}
if "editing_name" not in st.session_state:
    st.session_state.editing_name = None

# --- SIDEBAR: Inventory Management ---
with st.sidebar:
    st.header("Saved Inventories")

    if not st.session_state.all_inventories:
        st.info("No inventories added yet.")
    else:
        # Use list() to allow dictionary modification during the loop
        for name in list(st.session_state.all_inventories.keys()):
            cols = st.columns([4, 1])
            
            with cols[0]:
                if st.session_state.editing_name == name:
                    # Rename Input
                    new_name = st.text_input("New Name", value=name, key=f"edit_input_{name}", label_visibility="collapsed")
                    if new_name != name and new_name.strip() != "":
                        st.session_state.all_inventories[new_name] = st.session_state.all_inventories.pop(name)
                        st.session_state.editing_name = None
                        st.rerun()
                else:
                    # Normal Display
                    with st.expander(f"📦 {name}"):
                        st.write(", ".join(st.session_state.all_inventories[name]))

            with cols[1]: # Delete Button
                if st.button("🗑️", key=f"del_{name}"):
                    del st.session_state.all_inventories[name]
                    if st.session_state.editing_name == name:
                        st.session_state.editing_name = None
                    st.rerun()

        st.markdown("---")
        if st.button("Clear All", use_container_width=True):
            st.session_state.all_inventories = {}
            st.rerun()

# --- MAIN UI: Inventory Setup ---
st.title("IPA Feature Complexity Calculator")
st.subheader("Inventory Setup")

raw_input = st.text_area("Enter IPA segments:", help="Separate with spaces or commas")
inv_name = st.text_input("Name for this inventory (optional):")

can_add = False
clean_list = []

if raw_input:
    input_list = [s.strip() for s in raw_input.replace(',', ' ').split()]
    clean_list, _ = engine.input_inv(raw_input)
    missing = [s for s in input_list if s not in clean_list]

    if missing:
        st.warning(f"Unrecognized symbols: {', '.join(missing)}")
        if st.checkbox("Proceed without unrecognized segments?", key="confirm_err"):
            can_add = True
    elif len(clean_list) < 2:
        st.error("Please enter at least two recognized IPA symbols.")
    else:
        can_add = True

if st.button("Add to Database"):
    if not raw_input:
        st.error("Cannot add empty inventory.")
    elif can_add:
        name = inv_name if inv_name else str(len(st.session_state.all_inventories) + 1)
        st.session_state.all_inventories[name] = clean_list
        st.success(f"Inventory '{name}' saved!")
        st.rerun()

# --- ANALYSIS SECTION ---
st.markdown("---")
st.subheader("Analysis & Actions")
tab1, tab2, tab3 = st.tabs(["Calculate Complexity & Economy", "Feature Tables", "Graphing"])

with tab1:
    st.write("Run complexity and economy models on your saved inventories.")

    # 1. Metrics Selection
    selected_metrics = []
    st.subheader("Metrics to Calculate")
    c1, c2 = st.columns(2)
    with c1:
        if st.checkbox("Complexity"): selected_metrics.append(2)
    with c2:
        if st.checkbox("Economy"): selected_metrics.append(1)

    st.divider()

    # 2. Model Selection with Bidirectional Sync Logic
    st.subheader("Select Models to Run")
    model_keys = ["check_r", "check_f", "check_e"]

    # Callback when "Select All" is clicked
    def on_master_change():
        for k in model_keys:
            st.session_state[k] = st.session_state.master_select

    # Callback when an individual box is clicked
    def on_child_change():
        # Check if all are currently True in state
        all_on = all(st.session_state.get(k, False) for k in model_keys)
        st.session_state.master_select = all_on

    st.checkbox("Select All Models", key="master_select", on_change=on_master_change)

    col_a, col_b = st.columns(2)
    selected_model_codes = []

    with col_a:
        if st.checkbox("Relative (r)", key="check_r", on_change=on_child_change):
            selected_model_codes.append("r")
        if st.checkbox("Exploitation (e)", key="check_e", on_change=on_child_change):
            selected_model_codes.append("e")
    with col_b:
        if st.checkbox("Frugality (f)", key="check_f", on_change=on_child_change):
            selected_model_codes.append("f")

    if st.button("Calculate All Scores", type="primary"):
        if not st.session_state.all_inventories:
            st.error("Please add at least one inventory first.")
        elif not selected_model_codes or not selected_metrics:
            st.warning("Please select at least one metric AND one model.")
        else:
            with st.spinner("Calculating..."):
                all_dfs = []
                for metric in selected_metrics:
                    results, _ = main.get_multi_score(
                        inputdict=st.session_state.all_inventories, 
                        selected_models=selected_model_codes,
                        calc_type=metric
                    )
                    df = pd.DataFrame(results).T
                    if len(selected_metrics) > 1:
                        label = "Complexity" if metric == 2 else "Economy"
                        df.columns = [f"{col} ({label})" for col in df.columns]
                    all_dfs.append(df)
                
                final_df = pd.concat(all_dfs, axis=1)
                st.write("### Comparison Results")
                st.dataframe(final_df)

with tab2:
    st.subheader("Feature Table Explorer")
    
    if not st.session_state.all_inventories:
        st.info("Please add an inventory first to explore its features.")
    else:
        # 1. בחירת האינבנטורי
        selected_inv_name = st.selectbox("Select Inventory:", list(st.session_state.all_inventories.keys()), key="tab2_inv_sel")
        current_segments = st.session_state.all_inventories[selected_inv_name]

        if current_segments:
            # 2. קריאה לפונקציה שלך
            raw_data = engine.create_dicts(current_segments) 
            
            if raw_data:
                # 3. המרה ל-DataFrame - פנדס יודע לקרוא רשימת מילונים באופן טבעי
                full_feature_df = pd.DataFrame(raw_data)
                
                # הגדרת עמודת הסגמנט כאינדקס (כדי שהיא תהיה השורה הראשונה בצד)
                # וודא ש-SEGMENT_ID_COL הוא השם שמופיע בטבלה (למשל 'segment' או 'IPA')
                if engine.SEGMENT_ID_COL in full_feature_df.columns:
                    full_feature_df = full_feature_df.set_index(engine.SEGMENT_ID_COL)
                
                # 4. בחירת סגמנטים ופיצ'רים
                all_segments = full_feature_df.index.tolist()
                all_features = full_feature_df.columns.tolist()

                chosen_segments = st.multiselect("Select Segments:", all_segments, default=all_segments)
                chosen_features = st.multiselect("Select Features:", all_features, default=all_features[:15])

                if chosen_segments and chosen_features:
                    # 5. הצגת הטבלה המסוננת
                    filtered_df = full_feature_df.loc[chosen_segments, chosen_features]
                    st.write(f"### Feature Matrix: {selected_inv_name}")
                    st.dataframe(filtered_df, width='stretch')
                else:
                    st.warning("Please select at least one segment and one feature.")
            else:
                st.warning("No data found for these segments.")

with tab3:
    st.subheader("Visual Analysis: Complexity & Economy")
    
    if not st.session_state.all_inventories:
        st.info("Add at least two inventories to compare them visually.")
    else:
        # 1. UI Setup: Metrics and Graph Type
        col_type, col_chart = st.columns(2)
        with col_type:
            metric_label = st.radio("Metric:", ["Complexity", "Economy"], horizontal=True)
            calc_type = 2 if metric_label == "Complexity" else 1
        with col_chart:
            chart_type = st.radio("Chart Style:", ["Bar Chart", "Line Graph"], horizontal=True)

        st.divider()

        # 2. Model Selection (Same logic as Tab 1)
        st.write("**Select Models to Plot**")
        plot_keys = ["plot_r", "plot_f", "plot_e"]
        
        # Sync Logic for Tab 3
        def toggle_all_plot():
            for k in plot_keys:
                st.session_state[k] = st.session_state.master_plot
        
        def on_plot_child_change():
            st.session_state.master_plot = all(st.session_state.get(k, False) for k in plot_keys)

        st.checkbox("Select All Models", key="master_plot", on_change=toggle_all_plot)

        p_col1, p_col2 = st.columns(2)
        selected_plot_codes = []
        
        with p_col1:
            if st.checkbox("Relative (r)", key="plot_r", on_change=on_plot_child_change):
                selected_plot_codes.append("r")
            if st.checkbox("Exploitation (e)", key="plot_e", on_change=on_plot_child_change):
                selected_plot_codes.append("e")
        with p_col2:
            if st.checkbox("Frugality (f)", key="plot_f", on_change=on_plot_child_change):
                selected_plot_codes.append("f")

        if selected_plot_codes:
            with st.spinner("Refining visualization..."):
                # 3. Calculation
                results, _ = main.get_multi_score(
                    inputdict=st.session_state.all_inventories,
                    selected_models=selected_plot_codes,
                    calc_type=calc_type
                )
                
                # 4. Data Transformation for Plotly
                # We melt the data so Plotly can handle multiple series easily
                df_plot = pd.DataFrame(results).T.reset_index()
                df_plot = df_plot.rename(columns={'index': 'Inventory'})
                df_melted = df_plot.melt(id_vars='Inventory', var_name='Model', value_name='Score')

                # 5. Rendering with Plotly (Fixed Aspect Ratio)
                if chart_type == "Bar Chart":
                    fig = px.bar(
                        df_melted, x='Inventory', y='Score', color='Model', 
                        barmode='group', height=450,
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                else:
                    fig = px.line(
                        df_melted, x='Inventory', y='Score', color='Model', 
                        markers=True, height=450
                    )

                fig.update_layout(
                    margin=dict(l=20, r=20, t=20, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )

                st.plotly_chart(fig, use_container_width=True)
                
        else:
            st.warning("Please select at least one model to view the chart.")