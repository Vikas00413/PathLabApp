import os
import sys
import uuid
import json
import streamlit as st
from PIL import Image
from langchain_core.runnables import RunnableConfig

# Ensure current script directory is in sys.path so app_graph imports reliably from anywhere
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from app_graph import lab_app, LAB_CATALOG
except ImportError:
    from .app_graph import lab_app, LAB_CATALOG  # pyrefly: ignore [missing-import] # type: ignore


# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI Diagnostic Booking & Human-in-the-Loop Validation",
    page_icon="🩺",
    layout="wide"
)

st.title("🩺 Diagnostic Lab AI Validation & Booking Dashboard")
st.caption("Prevent booking errors with Vision AI document analysis & Human-in-the-Loop approval.")

# ---------------------------------------------------------
# Sidebar: Upload Prescription / Document & Notes
# ---------------------------------------------------------
with st.sidebar:
    st.header("📄 Upload Customer Document")
    uploaded_file = st.file_uploader(
        "Select Prescription / Requisition (PDF or Image)", 
        type=["pdf", "jpg", "png", "jpeg", "webp"]
    )
    
    additional_desc = st.text_area(
        "Optional Customer / Operator Notes", 
        placeholder="e.g. Pre-employment requirement for 10-panel drug screen"
    )
    
    start_btn = st.button("🚀 Process Document with AI", type="primary", use_container_width=True)

# ---------------------------------------------------------
# Session State Setup
# ---------------------------------------------------------
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "is_running" not in st.session_state:
    st.session_state.is_running = False

thread_config: RunnableConfig = {
    "configurable": {
        "thread_id": st.session_state.thread_id
    }
}
# ---------------------------------------------------------
# Main UI Dashboard Layout
# ---------------------------------------------------------
col_graph, col_execution = st.columns([1, 1])

# Left Column: Graph Visualization
with col_graph:
    st.subheader("📊 Agentic Workflow Graph")
    try:
        # Draw Mermaid diagram of the StateGraph
        graph_png = lab_app.get_graph().draw_mermaid_png()
        st.image(graph_png, caption="LangGraph Workflow with Interrupt Middleware", use_container_width=True)
    except Exception as e:
        st.info("StateGraph Workflow Active.")

# Right Column: Live Execution & Human-in-the-Loop Gate
with col_execution:
    st.subheader("🤖 Live Execution & Human-in-the-Loop Gate")
    
    # 1. User Clicks "Process Document with AI"
    if start_btn:
        if not uploaded_file:
            st.error("Please upload a PDF or Image prescription file first!")
        else:
            # Save temporary file locally
            temp_filename = f"temp_{uploaded_file.name}"
            with open(temp_filename, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Reset thread ID for a fresh run
            st.session_state.thread_id = str(uuid.uuid4())
            thread_config = {"configurable": {"thread_id": st.session_state.thread_id}}
            
            initial_state = {
                "file_path": temp_filename,
                "additional_description": additional_desc,
                "extracted_req": None,
                "matched_product": None,
                "is_available": False,
                "human_decision": None,
                "operator_selected_sku": "",
                "booking_status": "STARTED"
            }
            
            with st.spinner("Analyzing document visual markings & searching catalog..."):
                lab_app.invoke(initial_state, config=thread_config)
            
            st.session_state.is_running = True
            st.rerun()

    # 2. Check Graph State at Interrupt Point
    current_snapshot = lab_app.get_state(thread_config)
    
    # If the graph is paused before human_review
    if current_snapshot.next:
        values = current_snapshot.values
        
        st.info("⏸️ **GRAPH PAUSED AT HUMAN-IN-THE-LOOP INTERRUPT GATE**")
        
        # Display Extracted Data
        if values.get("extracted_req"):
            with st.expander("🔍 AI Extracted Document Requirements", expanded=True):
                st.json(values["extracted_req"])
        
        # Display Catalog Match Status
        if values.get("is_available"):
            matched_prod = values["matched_product"]
            st.success(
                f"✅ **AI Catalog Match Found**: `{matched_prod['sku_id']}` - {matched_prod['product_name']} "
                f"(₹{matched_prod['price_inr']})"
            )
            default_sku = matched_prod["sku_id"]
        else:
            st.error("⚠️ **WARNING**: Requested test was NOT found automatically in Lab's catalog!")
            default_sku = ""

        st.markdown("---")
        st.subheader("👤 Human Operator Decision Form")
        
        with st.form("human_input_form"):
            human_decision = st.radio("Confirm test booking?", ["YES", "NO"], index=0)
            
            selected_sku = st.text_input(
                "Verify or enter exact Catalog SKU:", 
                value=default_sku,
                help="If test was not found, enter custom SKU code here."
            )
            
            submit_btn = st.form_submit_button("Submit Decision & Resume Workflow", type="primary")
            
            if submit_btn:
                # Update State with Human Input
                lab_app.update_state(
                    thread_config,
                    {
                        "human_decision": human_decision,
                        "operator_selected_sku": selected_sku
                    }
                )
                
                # Resume Workflow
                with st.spinner("Resuming workflow..."):
                    final_output = lab_app.invoke(None, config=thread_config)
                
                st.markdown("---")
                if "CONFIRMED" in final_output["booking_status"]:
                    st.balloons()
                    st.success(f"🎉 **{final_output['booking_status']}**")
                else:
                    st.error(f"❌ **{final_output['booking_status']}**")
    
    elif current_snapshot.values and current_snapshot.values.get("booking_status") != "STARTED":
        # Completed state
        status = current_snapshot.values.get("booking_status", "")
        if "CONFIRMED" in status:
            st.success(f"🎉 **{status}**")
        else:
            st.info(f"ℹ️ Status: {status}")

# Footer catalog reference
with st.expander("📚 View Lab Product Catalog Reference"):
    st.table([prod.model_dump() for prod in LAB_CATALOG.values()])
