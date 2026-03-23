import streamlit as st
import openai
import pandas as pd
from datetime import datetime
import json

# ============================================
# CONFIGURATION - Replace with your API key
# ============================================
# For Ollama (local), or OpenAI/Claude via API
# Option 1: OpenAI
# openai.api_key = "your-key-here"

# Option 2: Ollama (if running locally)
import requests
def call_ollama(prompt, model="llama2"):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False}
    )
    return response.json()["response"]

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(page_title="Maker Assistant", layout="wide")
st.title("🛠️ Local Maker Assistant")
st.markdown("Turn your product idea into a manufacturable prototype plan")

# ============================================
# SIDEBAR - Local Constraints (Makers Profile)
# ============================================
st.sidebar.header("📋 Local Maker Profile")

# Load or initialize maker profile
if "maker_profile" not in st.session_state:
    st.session_state.maker_profile = {
        "tools_available": [],
        "materials_available": [],
        "skill_level": "intermediate",
        "budget": 50,
        "location": ""
    }

# Tool inputs
tools = st.sidebar.multiselect(
    "Tools you have access to",
    ["Welding", "3D Printer", "Woodworking", "Sewing Machine", "Soldering Iron", 
     "Basic Hand Tools", "CNC Router", "Laser Cutter", "Electronics Kit"]
)

materials = st.sidebar.multiselect(
    "Materials readily available",
    ["Wood", "Metal Sheets", "Plastic", "Fabric", "Electronics Components", 
     "Recycled Materials", "3D Filament", "Adhesives"]
)

skill_level = st.sidebar.selectbox(
    "Maker Skill Level",
    ["beginner", "intermediate", "advanced"]
)

budget = st.sidebar.number_input("Budget (USD)", min_value=0, value=50)

location = st.sidebar.text_input("Location/City", placeholder="e.g., Cape Town")

if st.sidebar.button("Save Maker Profile"):
    st.session_state.maker_profile = {
        "tools_available": tools,
        "materials_available": materials,
        "skill_level": skill_level,
        "budget": budget,
        "location": location
    }
    st.sidebar.success("Profile saved!")

# Display current profile
with st.sidebar.expander("Current Profile"):
    st.json(st.session_state.maker_profile)

# ============================================
# MAIN CONTENT - Product Idea Input
# ============================================
st.header("💡 What do you want to make?")

product_idea = st.text_area(
    "Describe your product idea",
    placeholder="e.g., A solar-powered phone charger that can be made from recycled materials",
    height=100
)

col1, col2 = st.columns(2)
with col1:
    priority = st.selectbox(
        "Priority",
        ["low-cost", "durable", "easy-to-repair", "balanced"]
    )
with col2:
    model_choice = st.selectbox(
        "LLM Model",
        ["llama2", "mistral", "gpt-3.5-turbo"]  # Add your available models
    )

# ============================================
# PROMPT CONSTRUCTION
# ============================================
def build_prompt(idea, profile, priority):
    return f"""
You are a local manufacturing assistant helping makers in {profile['location'] or 'a community setting'}.

**Maker's Resources:**
- Tools: {', '.join(profile['tools_available']) if profile['tools_available'] else 'Limited tools available'}
- Materials: {', '.join(profile['materials_available']) if profile['materials_available'] else 'Limited materials available'}
- Skill Level: {profile['skill_level']}
- Budget: ${profile['budget']}
- Priority: {priority}

**Product Idea:** {idea}

Generate a practical prototype plan with:

1. **2-3 Prototype Variants**:
   - Variant A (Low-cost): minimal materials, basic tools
   - Variant B (Durable): robust materials, moderate complexity
   - Variant C (Easy-to-repair): modular design, common parts

2. **For each variant, provide**:
   - Materials needed (with estimated local cost)
   - Tools required
   - Step-by-step instructions (max 8 steps)
   - Estimated time to build
   - Difficulty level

3. **Maintenance & Repair Guide**:
   - Most common failure points
   - How to fix them
   - Where to find spare parts

4. **Cost Summary**:
   - Total estimated cost breakdown

Format your answer clearly with sections and bullet points.
"""

# ============================================
# GENERATE BUTTON
# ============================================
if st.button("🚀 Generate Prototype Plan", type="primary"):
    if not product_idea:
        st.error("Please describe your product idea first")
    else:
        with st.spinner("Generating your prototype plan..."):
            prompt = build_prompt(
                product_idea, 
                st.session_state.maker_profile,
                priority
            )
            
            # Call LLM (choose your method)
            try:
                # Option 1: Ollama
                response = call_ollama(prompt, model=model_choice)
                
                # Option 2: OpenAI (uncomment and add key)
                # response = openai.ChatCompletion.create(
                #     model="gpt-3.5-turbo",
                #     messages=[{"role": "user", "content": prompt}]
                # )["choices"][0]["message"]["content"]
                
                st.session_state.last_response = response
                st.session_state.last_idea = product_idea
                
            except Exception as e:
                st.error(f"Error: {e}")
                st.info("Try using Ollama locally or check your API key")

# ============================================
# DISPLAY RESULTS
# ============================================
if "last_response" in st.session_state:
    st.divider()
    st.header("📐 Your Prototype Plan")
    
    # Display the LLM output
    st.markdown(st.session_state.last_response)
    
    # ============================================
    # FEEDBACK SECTION
    # ============================================
    st.divider()
    st.header("📝 Feedback")
    st.markdown("Help us improve this plan for real makers like you")
    
    feedback_col1, feedback_col2 = st.columns(2)
    
    with feedback_col1:
        manufacturable = st.radio(
            "Is this plan manufacturable with your resources?",
            ["Yes, realistic", "Partially", "No, unrealistic"]
        )
        
        unrealistic_parts = st.text_area(
            "What parts seem unrealistic?",
            placeholder="e.g., I don't have access to a 3D printer, materials too expensive..."
        )
    
    with feedback_col2:
        cost_accuracy = st.select_slider(
            "Cost estimate accuracy",
            options=["Too low", "About right", "Too high"],
            value="About right"
        )
        
        suggestions = st.text_area(
            "Suggestions for improvement",
            placeholder="What would make this more usable?"
        )
    
    if st.button("Submit Feedback"):
        # Save feedback to CSV
        feedback_data = {
            "timestamp": datetime.now().isoformat(),
            "product_idea": st.session_state.last_idea,
            "tools": ", ".join(st.session_state.maker_profile["tools_available"]),
            "materials": ", ".join(st.session_state.maker_profile["materials_available"]),
            "skill": st.session_state.maker_profile["skill_level"],
            "budget": st.session_state.maker_profile["budget"],
            "manufacturable": manufacturable,
            "unrealistic_parts": unrealistic_parts,
            "cost_accuracy": cost_accuracy,
            "suggestions": suggestions
        }
        
        # Append to CSV file
        try:
            df = pd.read_csv("feedback.csv")
        except FileNotFoundError:
            df = pd.DataFrame()
        
        new_row = pd.DataFrame([feedback_data])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv("feedback.csv", index=False)
        
        st.success("✅ Feedback saved! Thank you for helping improve this tool.")

# ============================================
# EXPORT OPTIONS
# ============================================
st.sidebar.divider()
st.sidebar.header("📤 Export")
if "last_response" in st.session_state:
    st.sidebar.download_button(
        label="Download Prototype Plan",
        data=st.session_state.last_response,
        file_name="prototype_plan.txt",
        mime="text/plain"
    )
    
    st.sidebar.download_button(
        label="Download Maker Profile",
        data=json.dumps(st.session_state.maker_profile, indent=2),
        file_name="maker_profile.json",
        mime="application/json"
    )
