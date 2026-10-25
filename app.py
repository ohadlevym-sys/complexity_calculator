import streamlit as st
import pandas as pd
import plotly.express as px
import economist as engine
import scores as scores
from languages_dict import phoible_languages
import Data_normalization as dn
import Tree_building_logic as TBL

def has_tones(segment_list):
    """
    בודק אם רשימת הסגמנטים מכילה תווי טון אופייניים של IPA.
    """
    tone_chars = ['˥', '˦', '˧', '˨', '˩', '↓']
    for segment in segment_list:
        if any(tone_char in str(segment) for tone_char in tone_chars):
            return True
    return False


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
                    with st.expander(f"{name}"):
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
# --- MAIN UI: Inventory Setup ---
st.title("IPA Feature Complexity Calculator")
st.markdown("---")

# שימוש בשתי עמודות כדי לחסוך מקום ולהציג את שתי אפשרויות ההזנה זו לצד זו
col_manual, col_db = st.columns(2)

with col_manual:
    st.subheader("📝 Manual Input")
    raw_input = st.text_area("Enter IPA segments:", help="Separate with spaces or commas", height=100)
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

    if st.button("Add Manual Inventory",type="primary", use_container_width=True):
        if not raw_input:
            st.error("Cannot add empty inventory.")
        elif can_add:
            name = inv_name if inv_name else f"Custom_{len(st.session_state.all_inventories) + 1}"
            st.session_state.all_inventories[name] = clean_list
            st.success(f"Inventory '{name}' saved!")
            st.rerun()

with col_db:
    st.subheader("🌍 Import from PHOIBLE")
    display_to_original = {}
    for lang_name, segments in phoible_languages.items():
        if has_tones(segments):
            # מוסיף סמל או טקסט (למשל סמל של תו מוזיקלי או [T])
            display_name = f"{lang_name}                    (T)" 
        else:
            display_name = lang_name
            
        display_to_original[display_name] = lang_name

    selected_display_langs = st.multiselect(
        "Search and select languages:", 
        options=list(display_to_original.keys()),
        help="Start typing a language name to see suggestions. Languages with 🎵 (T) have tonal segments."
    )
    
    # ריווח קטן כדי שהכפתור יהיה בערך באותו גובה כמו בצד של ההזנה הידנית
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("Add Selected Languages", type="primary", use_container_width=True):
        if not selected_display_langs:
            st.warning("Please select at least one language.")
        else:
            added_count = 0
            with st.spinner("Importing and cleaning segments..."):
                for lang in selected_display_langs:
                    # המרה למחרוזת אחת עם רווחים כדי להריץ במנוע
                    raw_segments = " ".join(phoible_languages[lang])
                    clean_list, _ = engine.input_inv(raw_segments)
                    
                    if len(clean_list) >= 2:
                        st.session_state.all_inventories[lang] = clean_list
                        added_count += 1
            
            if added_count > 0:
                st.success(f"Successfully added {added_count} languages to your database!")
                st.rerun()
            else:
                st.error("None of the selected languages had enough recognized segments.")

# --- ANALYSIS SECTION ---
st.markdown("---")
st.subheader("Analysis & Actions")
tab1, tab2, tab3, tab4 = st.tabs(["Calculate Complexity & Economy", "Feature Tables", "Graphing", "Feature Geometry Trees"])

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
                error_occurred = False 
                
                for metric in selected_metrics:
                    try:
                        results, _ = scores.get_multi_score(
                            inputdict=st.session_state.all_inventories, 
                            selected_models=selected_model_codes,
                            calc_type=metric
                        )
                        
                        df = pd.DataFrame(results).T
                        if len(selected_metrics) > 1:
                            label = "Complexity" if metric == 2 else "Economy"
                            df.columns = [f"{col} ({label})" for col in df.columns]
                        all_dfs.append(df)
                        
                    except engine.IdenticalSegmentsError:
                        error_occurred = True
                        st.error("Calculation aborted: We found segments that cannot be distinguished.")
                        
                        # -- מציאת ההגאים הבעייתיים --
                        # עוברים על כל האינבנטוריז השמורים כדי למצוא למי מהם יש כפילות
                        for inv_name_check, segments_list in st.session_state.all_inventories.items():
                            raw_data = engine.create_dicts(segments_list)
                            err_df = pd.DataFrame(raw_data)
                            
                            # מגדירים את הסגמנט כאינדקס כדי שהפונקציה תדפיס את השם שלו
                            if dn.SEGMENT_ID_COL in err_df.columns:
                                err_df = err_df.set_index(dn.SEGMENT_ID_COL)
                            
                            # שולחים לפונקציית העזר שלנו - היא תדפיס שגיאה רק אם יש כפילות!
                            #show_identical_segments_error(err_df, inv_name_check)
                        
                        break # עוצר את המשך החישובים!
                
                # מוודא שאין שגיאה *וגם* שיש טבלאות לאחד (מונע את ה-ValueError)
                if not error_occurred and len(all_dfs) > 0:
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
            # כפתור ה-Toggle לכלכלה
            show_minimal = st.toggle("Show Minimal Contrastive Matrix only", value=False)
            
            # 2. תמיד נייצר קודם את המטריצה המלאה
            raw_data = engine.create_dicts(current_segments) 
            
            if raw_data:
                # 3. המרה ל-DataFrame 
                full_feature_df = pd.DataFrame(raw_data)
                
                # הגדרת עמודת הסגמנט כאינדקס (השורות של הטבלה)
                # וודא שהשם פה תואם למשתנה שלך (engine.SEGMENT_ID_COL או dn.SEGMENT_ID_COL)
                if dn.SEGMENT_ID_COL in full_feature_df.columns:
                    full_feature_df = full_feature_df.set_index(dn.SEGMENT_ID_COL)
                
                # --- החיתוך המינימלי מתבצע כאן ---
                if show_minimal:
                    try:
                        # קריאה לפונקציה האמיתית שלך! (משער שהיא מחזירה רשימה ואורך)
                        minimal_features_list, minimal_inventory_size = engine.feature_economist(l_seg = current_segments)
                        
                        # אנחנו שומרים מתוך הטבלה רק את העמודות שנמצאות ברשימה שהפונקציה החזירה
                        cols_to_keep = [col for col in full_feature_df.columns if col in minimal_features_list]
                        full_feature_df = full_feature_df[cols_to_keep]
                        
                        st.info(f"Showing {(minimal_inventory_size)} feature minimal contrastive set.")
                        
                    except engine.IdenticalSegmentsError: # או כל שגיאה אחרת שהפונקציה שלך זורקת
                        st.error("Cannot compute minimal matrix: 2 or more segments cannot be distinguished.")
                
                # 4. הכנת אפשרויות הבחירה (Multiselect) - עכשיו זה מעודכן אוטומטית למלא או למינימלי
                all_segments = full_feature_df.index.tolist()
                all_features = full_feature_df.columns.tolist()

                chosen_segments = st.multiselect("Select Segments:", all_segments, default=all_segments)
                chosen_features = st.multiselect("Select Features:", all_features, default=all_features)

                if chosen_segments and chosen_features:
                    # 5. הצגת הטבלה המסוננת
                    filtered_df = full_feature_df.loc[chosen_segments, chosen_features]
                    
                    matrix_title = "Minimal Feature Matrix" if show_minimal else "Full Feature Matrix"
                    st.write(f"### {matrix_title}: {selected_inv_name}")
                    
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
                results, _ = scores.get_multi_score(
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


with tab4: 
    st.subheader("Feature Geometry Tree Generator")
    
    if not st.session_state.all_inventories:
        st.info("Please add at least one inventory to explore feature trees.")
    else:
        # 1. בחירת האינבנטורי מתוך מה ששמור
        selected_inv_for_tree = st.selectbox(
            "Select Inventory:", 
            list(st.session_state.all_inventories.keys()), 
            key="tab3_inv_sel"
        )
        current_segments = st.session_state.all_inventories[selected_inv_for_tree]

        if current_segments:
            selected_segment = st.selectbox(
                "Select a Segment:", 
                current_segments,
                key="tab3_seg_sel"
            )
                
        st.markdown("---") # הוספתי קו הפרדה קטן ליופי בין הבחירה לעץ
                
            # 3. הצגת העץ (שורה שלישית, מתחת לבחירה)
        if selected_segment:
            with st.spinner(f"Generating Feature Geometry for /{selected_segment}/..."):
                try:
                    # 3. כאן אתה קורא לפונקציה מהמנוע שלך שמייצרת עץ לסגמנט בודד
                    # שנה את הקריאה הזו לפונקציה המדויקת שיש לך במנוע!
                    my_tree = TBL.build_tree_by_symbol(selected_segment, dn.df)
                    
                    # 4. המרת העץ לאובייקט הציור של Graphviz
                    dot_graph = TBL.generate_tree_graph(my_tree.root)
                    
                    # 5. ציור ישיר על המסך של Streamlit!
                    st.graphviz_chart(dot_graph, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Could not generate tree for {selected_segment}. Error: {e}")
    