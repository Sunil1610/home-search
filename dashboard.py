"""
Home Search Dashboard
Visualize and filter property data from YouTube videos.
"""

import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import os

# Change to script directory
os.chdir(Path(__file__).parent)

# Page config
st.set_page_config(
    page_title="Home Search Dashboard",
    page_icon="🏠",
    layout="wide"
)

# Title
st.title("🏠 Home Search Dashboard")
st.markdown("*Property data extracted from YouTube real estate videos*")


@st.cache_data
def load_properties():
    """Load all properties from the data directory."""
    properties_dir = Path("./data/properties")
    properties = []

    if not properties_dir.exists():
        st.error(f"Properties directory not found: {properties_dir.absolute()}")
        return pd.DataFrame()

    for filepath in properties_dir.glob("*.json"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                prop = json.load(f)

                # Flatten the data
                video_info = prop.get("video_info", {})
                extracted = prop.get("extracted_data", {})
                processing = prop.get("processing_info", {})

                dimensions = extracted.get("dimensions", {}) or {}
                price = extracted.get("price", {}) or {}
                location = extracted.get("location", {}) or {}
                config = extracted.get("configuration", {}) or {}

                flat = {
                    "video_id": video_info.get("video_id", ""),
                    "title": video_info.get("title", ""),
                    "channel": video_info.get("channel", ""),
                    "url": video_info.get("url", ""),
                    "duration": video_info.get("duration_seconds", 0),
                    "views": video_info.get("view_count", 0),
                    "upload_date": video_info.get("upload_date", ""),

                    "property_type": extracted.get("property_type", "unknown"),
                    "plot_area_sqyd": dimensions.get("plot_area_sq_yards"),
                    "built_up_sqft": dimensions.get("built_up_area_sq_ft"),

                    "price": price.get("amount"),
                    "price_lakhs": price.get("amount", 0) / 100000 if price.get("amount") else None,

                    "area": location.get("area", ""),
                    "city": location.get("city", "Hyderabad"),
                    "landmark": location.get("landmark", ""),

                    "bedrooms": config.get("bedrooms"),
                    "bathrooms": config.get("bathrooms"),
                    "floors": config.get("floors"),
                    "facing": config.get("facing", ""),

                    "amenities": ", ".join(extracted.get("amenities", []) or []),
                    "confidence": extracted.get("confidence_score", 0),

                    "processed_at": processing.get("processed_at", ""),
                    "description": prop.get("transcript_summary", "")[:200]
                }
                properties.append(flat)
        except Exception as e:
            st.warning(f"Error loading {filepath}: {e}")

    return pd.DataFrame(properties)


# Load data
df = load_properties()

if df.empty:
    st.warning("No properties found. Run `python3 main.py search` to fetch some data first.")
    st.stop()

# Sidebar filters
st.sidebar.header("🔍 Filters")

# Price range filter
if df["price_lakhs"].notna().any():
    min_price = float(df["price_lakhs"].min() or 0)
    max_price = float(df["price_lakhs"].max() or 500)

    price_range = st.sidebar.slider(
        "Price Range (Lakhs)",
        min_value=0.0,
        max_value=max(max_price, 500.0),
        value=(min_price, max_price),
        step=10.0
    )
else:
    price_range = (0, 10000)

# Area filter
areas = ["All"] + sorted(df["area"].dropna().unique().tolist())
selected_area = st.sidebar.selectbox("Area", areas)

# Property type filter
prop_types = ["All"] + sorted(df["property_type"].dropna().unique().tolist())
selected_type = st.sidebar.selectbox("Property Type", prop_types)

# Bedrooms filter
bedroom_options = ["All"] + sorted([str(int(b)) for b in df["bedrooms"].dropna().unique() if pd.notna(b)])
selected_bedrooms = st.sidebar.selectbox("Bedrooms", bedroom_options)

# Confidence filter
min_confidence = st.sidebar.slider("Min Confidence Score", 0.0, 1.0, 0.0, 0.1)

# Apply filters
filtered_df = df.copy()

# Price filter
if df["price_lakhs"].notna().any():
    filtered_df = filtered_df[
        (filtered_df["price_lakhs"].isna()) |
        ((filtered_df["price_lakhs"] >= price_range[0]) &
         (filtered_df["price_lakhs"] <= price_range[1]))
    ]

# Area filter
if selected_area != "All":
    filtered_df = filtered_df[filtered_df["area"] == selected_area]

# Property type filter
if selected_type != "All":
    filtered_df = filtered_df[filtered_df["property_type"] == selected_type]

# Bedrooms filter
if selected_bedrooms != "All":
    filtered_df = filtered_df[filtered_df["bedrooms"] == int(selected_bedrooms)]

# Confidence filter
filtered_df = filtered_df[filtered_df["confidence"] >= min_confidence]

# Summary metrics
st.header("📊 Summary")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Properties", len(filtered_df))

with col2:
    avg_price = filtered_df["price_lakhs"].mean()
    st.metric("Avg Price", f"₹{avg_price:.0f}L" if pd.notna(avg_price) else "N/A")

with col3:
    avg_area = filtered_df["plot_area_sqyd"].mean()
    st.metric("Avg Plot Size", f"{avg_area:.0f} sq.yd" if pd.notna(avg_area) else "N/A")

with col4:
    high_conf = len(filtered_df[filtered_df["confidence"] >= 0.7])
    st.metric("High Confidence", f"{high_conf}/{len(filtered_df)}")

# Charts
st.header("📈 Visualizations")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    # Price distribution
    price_data = filtered_df[filtered_df["price_lakhs"].notna()]
    if not price_data.empty:
        fig_price = px.histogram(
            price_data,
            x="price_lakhs",
            nbins=20,
            title="Price Distribution (Lakhs)",
            labels={"price_lakhs": "Price (Lakhs)"}
        )
        fig_price.update_layout(showlegend=False)
        st.plotly_chart(fig_price, use_container_width=True)
    else:
        st.info("No price data available for chart")

with chart_col2:
    # Properties by area
    area_counts = filtered_df["area"].value_counts().head(10)
    if not area_counts.empty:
        fig_area = px.bar(
            x=area_counts.index,
            y=area_counts.values,
            title="Properties by Area",
            labels={"x": "Area", "y": "Count"}
        )
        fig_area.update_layout(showlegend=False)
        st.plotly_chart(fig_area, use_container_width=True)
    else:
        st.info("No area data available for chart")

# Price vs Area scatter
st.subheader("Price vs Plot Size")
scatter_data = filtered_df[
    (filtered_df["price_lakhs"].notna()) &
    (filtered_df["plot_area_sqyd"].notna())
]
if not scatter_data.empty:
    fig_scatter = px.scatter(
        scatter_data,
        x="plot_area_sqyd",
        y="price_lakhs",
        color="area",
        hover_data=["title", "bedrooms", "facing"],
        title="Price vs Plot Size",
        labels={
            "plot_area_sqyd": "Plot Area (sq.yd)",
            "price_lakhs": "Price (Lakhs)"
        }
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.info("Not enough data for scatter plot")

# Property listings
st.header("🏘️ Property Listings")

# Display table
display_cols = ["title", "price_lakhs", "plot_area_sqyd", "area", "bedrooms", "property_type", "confidence"]
display_df = filtered_df[display_cols].copy()
display_df.columns = ["Title", "Price (L)", "Area (sq.yd)", "Location", "BHK", "Type", "Conf."]

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)

# Property detail view
st.header("🔎 Property Details")

if not filtered_df.empty:
    selected_idx = st.selectbox(
        "Select a property to view details:",
        range(len(filtered_df)),
        format_func=lambda i: filtered_df.iloc[i]["title"][:80] + "..."
    )

    prop = filtered_df.iloc[selected_idx]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📍 Location & Details")
        st.write(f"**Area:** {prop['area'] or 'N/A'}")
        st.write(f"**City:** {prop['city'] or 'N/A'}")
        st.write(f"**Landmark:** {prop['landmark'] or 'N/A'}")
        st.write(f"**Property Type:** {prop['property_type'] or 'N/A'}")
        st.write(f"**Facing:** {prop['facing'] or 'N/A'}")

    with col2:
        st.subheader("💰 Price & Size")
        if prop['price']:
            st.write(f"**Price:** ₹{prop['price']:,.0f} ({prop['price_lakhs']:.1f} Lakhs)")
        else:
            st.write("**Price:** N/A")
        st.write(f"**Plot Area:** {prop['plot_area_sqyd'] or 'N/A'} sq.yd")
        st.write(f"**Built-up Area:** {prop['built_up_sqft'] or 'N/A'} sq.ft")
        st.write(f"**Config:** {prop['bedrooms'] or '?'} BHK, {prop['floors'] or '?'} floors")

    st.subheader("📺 Video Info")
    st.write(f"**Channel:** {prop['channel']}")
    st.write(f"**Views:** {prop['views']:,}" if prop['views'] else "**Views:** N/A")
    st.markdown(f"[🔗 Watch on YouTube]({prop['url']})")

    if prop['amenities']:
        st.subheader("✨ Amenities")
        st.write(prop['amenities'])

    if prop['description']:
        st.subheader("📝 Description")
        st.write(prop['description'])

    st.caption(f"Confidence Score: {prop['confidence']:.2f} | Processed: {prop['processed_at']}")

# Footer
st.markdown("---")
st.caption("Data extracted from YouTube real estate videos using Whisper + Qwen 2.5 7B")
