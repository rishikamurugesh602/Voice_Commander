"""
ui_helpers.py
--------------
Reusable rendering functions for the Streamlit UI.
Keeps app.py clean by moving repeated HTML/markdown generation here.
"""

import streamlit as st
import os


def load_css():
    """Inject the custom stylesheet into the Streamlit app."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    css_path = os.path.join(base_dir, "assets", "style.css")
    with open(css_path, "r") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_header():
    st.markdown("""
        <div class="app-header">
            <div>
                <div class="app-title">🛒 EchoCart</div>
                <div class="app-subtitle">Your voice-powered shopping assistant</div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_feedback(success, message):
    """Toast-style feedback banner after a command executes."""
    css_class = "feedback-success" if success else "feedback-error"
    icon = "✅" if success else "⚠️"
    st.markdown(f"""
        <div class="{css_class}">{icon} {message}</div>
    """, unsafe_allow_html=True)


def render_shopping_list(items):
    """Render the shopping list grouped by category, or an empty state."""
    if not items:
        st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">🛒</div>
                <div>Your list is empty. Try saying "Add milk" to get started.</div>
            </div>
        """, unsafe_allow_html=True)
        return

    # Group items by category
    categories = {}
    for item in items:
        cat = item["category"]
        categories.setdefault(cat, []).append(item)

    for category, cat_items in categories.items():
        st.markdown(f'<div class="category-label">{category}</div>', unsafe_allow_html=True)
        for item in cat_items:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"""
                    <div class="item-card">
                        <strong>{item['product_name']}</strong> — Qty: {item['quantity']}
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("Remove", key=f"remove_{item['id']}"):
                    from services import db_service
                    db_service.remove_item(item['product_name'])
                    st.rerun()


def render_search_results(products):
    """Render product search results as a card grid."""
    if not products:
        st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <div>No products found. Try a different search.</div>
            </div>
        """, unsafe_allow_html=True)
        return

    cols = st.columns(3)
    for idx, product in enumerate(products):
        with cols[idx % 3]:
            st.markdown(f"""
                <div class="product-card">
                    <div><strong>{product['name']}</strong></div>
                    <div class="product-brand">{product['brand']}</div>
                    <div class="product-price">₹{product['price']}</div>
                </div>
            """, unsafe_allow_html=True)
def render_suggestions(suggestions):
    """Render smart suggestion cards (frequency-based + seasonal)."""
    frequency = suggestions.get("frequency", [])
    seasonal = suggestions.get("seasonal", [])

    if not frequency and not seasonal:
        return  # nothing to show, skip the section entirely

    st.markdown("### Smart Suggestions")

    if frequency:
        st.markdown('<div class="category-label">Based on your habits</div>', unsafe_allow_html=True)
        cols = st.columns(min(len(frequency), 4))
        for idx, sug in enumerate(frequency):
            with cols[idx % len(cols)]:
                st.markdown(f"""
                    <div class="product-card">
                        <div><strong>{sug['item']}</strong></div>
                        <div class="product-brand">{sug['reason']}</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"Add {sug['item']}", key=f"sugg_freq_{sug['item']}"):
                    from services import db_service, command_handler
                    command_handler.execute(f"Add {sug['item']}")
                    st.rerun()

    if seasonal:
        st.markdown('<div class="category-label">In season this month</div>', unsafe_allow_html=True)
        cols = st.columns(min(len(seasonal), 4))
        for idx, item in enumerate(seasonal):
            with cols[idx % len(cols)]:
                st.markdown(f"""
                    <div class="product-card">
                        <div><strong>{item}</strong></div>
                        <div class="product-brand">Seasonal pick</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"Add {item}", key=f"sugg_season_{item}"):
                    from services import command_handler
                    command_handler.execute(f"Add {item}")
                    st.rerun()