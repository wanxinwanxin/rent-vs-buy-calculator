"""
URL sharing utilities for rent vs buy calculator.
"""
import base64
import json
import urllib.parse
from typing import Dict, Any, Optional
import streamlit as st
from calc.models import UserInputs


def encode_inputs_to_url(user_inputs: UserInputs) -> str:
    """
    Encode user inputs to a URL-safe string for sharing.
    
    Args:
        user_inputs: UserInputs object to encode
        
    Returns:
        URL with encoded parameters
    """
    # Convert to dict, excluding None values
    inputs_dict = user_inputs.model_dump(exclude_none=True)
    
    # Convert to JSON and then base64 encode
    json_str = json.dumps(inputs_dict, sort_keys=True)
    encoded = base64.urlsafe_b64encode(json_str.encode()).decode()
    
    # Get current URL base
    try:
        # Try to get the current URL, fallback to localhost if not available
        current_url = st.context.headers.get("host", "localhost:8501")
        protocol = "https" if "herokuapp" in current_url or "streamlit" in current_url else "http"
        base_url = f"{protocol}://{current_url}"
    except:
        base_url = "http://localhost:8501"
    
    # Create shareable URL
    share_url = f"{base_url}/?shared={encoded}"
    return share_url


def decode_url_to_inputs(encoded_params: str) -> Optional[UserInputs]:
    """
    Decode URL parameters back to UserInputs object.
    
    Args:
        encoded_params: Base64 encoded parameter string
        
    Returns:
        UserInputs object if successful, None if decoding fails
    """
    try:
        # Decode base64 and parse JSON
        decoded_bytes = base64.urlsafe_b64decode(encoded_params.encode())
        inputs_dict = json.loads(decoded_bytes.decode())
        
        # Create UserInputs object with validation
        user_inputs = UserInputs(**inputs_dict)
        return user_inputs
        
    except Exception as e:
        st.error(f"Error decoding shared URL: {e}")
        return None


def check_for_shared_analysis() -> Optional[UserInputs]:
    """
    Check URL parameters for shared analysis data.
    
    Returns:
        UserInputs object if shared data found, None otherwise
    """
    try:
        # Get query parameters from URL
        query_params = st.query_params
        
        if "shared" in query_params:
            encoded_data = query_params["shared"]
            return decode_url_to_inputs(encoded_data)
            
    except Exception as e:
        st.error(f"Error reading shared URL: {e}")
        
    return None


def display_share_button(user_inputs: UserInputs) -> None:
    """
    Display a share button that generates a shareable URL.
    
    Args:
        user_inputs: Current user inputs to share
    """
    if st.button("🔗 Share This Analysis", use_container_width=True):
        try:
            share_url = encode_inputs_to_url(user_inputs)
            
            # Display the shareable URL
            st.success("✅ Shareable URL generated!")
            st.code(share_url, language=None)
            
            st.markdown("""
            **How to share:**
            1. Copy the URL above
            2. Send it to anyone you want to share this analysis with
            3. When they open the link, it will load this exact scenario
            
            💡 *The URL contains all your input parameters but no personal data is stored on our servers.*
            """)
            
            # Option to copy to clipboard using JavaScript
            copy_button_js = f"""
            <script>
            function copyToClipboard() {{
                navigator.clipboard.writeText('{share_url}').then(function() {{
                    alert('URL copied to clipboard!');
                }}, function(err) {{
                    console.error('Could not copy text: ', err);
                }});
            }}
            </script>
            <button onclick="copyToClipboard()" style="
                background-color: #ff4b4b; 
                color: white; 
                border: none; 
                padding: 8px 16px; 
                border-radius: 4px; 
                cursor: pointer;
                font-size: 14px;
                margin-top: 8px;
            ">📋 Copy URL</button>
            """
            
            st.markdown(copy_button_js, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error generating shareable URL: {e}")


def display_shared_analysis_info() -> None:
    """Display info banner when viewing a shared analysis."""
    st.info("""
    📤 **Viewing Shared Analysis**
    
    This analysis was shared with you via URL. The form below has been pre-populated with the shared parameters.
    You can modify any values and re-run the analysis, or share your own version using the "Share This Analysis" button.
    """) 