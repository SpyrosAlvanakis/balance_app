import hmac
import streamlit as st

def show_login_widget():
    """Show login widget and return authentication status."""
    with st.sidebar:
        st.header("Login")
        with st.form("login_form", clear_on_submit=False):
            user = st.text_input("Username", type="default", key="username")
            password = st.text_input("Password", type="password", key="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if user in st.secrets["passwords"]:
                    if hmac.compare_digest(password, st.secrets["passwords"][user]):
                        # Get user roles
                        roles = []
                        for role in st.secrets.roles:
                            if user in st.secrets.roles[role]:
                                roles.append(role)
                        
                        if not roles:
                            st.error(f"User {user} does not have a role")
                            st.session_state['user'] = None
                            return False
                        
                        st.success("Login successful!")
                        st.session_state['user'] = {"user": user, "roles": roles}
                        return True
                    else:
                        st.error("😕 Password incorrect")
                        st.session_state['user'] = None
                        return False
                else:
                    st.error("No such username exists")
                    st.session_state['user'] = None
                    return False
    
    # If the user clicked the login button, show a modal dialog
    if st.session_state.get("show_login", False):
        # Using expander instead of dialog for compatibility
        with st.expander("Login", expanded=True):
            st.subheader("Login")
            with st.form("login_modal"):
                user = st.text_input("Username", type="default", key="modal_username")
                password = st.text_input("Password", type="password", key="modal_password")
                login_clicked = st.form_submit_button("Login")
                cancel = st.form_submit_button("Cancel")
                
                if cancel:
                    st.session_state["show_login"] = False
                    st.rerun()
                    return False
                
                if login_clicked:
                    if user in st.secrets["passwords"]:
                        if hmac.compare_digest(password, st.secrets["passwords"][user]):
                            # Get user roles
                            roles = []
                            for role in st.secrets.roles:
                                if user in st.secrets.roles[role]:
                                    roles.append(role)
                            
                            if not roles:
                                st.error(f"User {user} does not have a role")
                                st.session_state['user'] = None
                                st.session_state["show_login"] = False
                                return False
                            
                            st.success("Login successful!")
                            st.session_state['user'] = {"user": user, "roles": roles}
                            st.session_state["show_login"] = False
                            st.rerun()
                            return True
                        else:
                            st.error("😕 Password incorrect")
                            return False
                    else:
                        st.error("No such username exists")
                        return False
    
    return False

def is_authenticated():
    """Check if user is authenticated."""
    return 'user' in st.session_state and st.session_state['user'] is not None

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if 'user' not in st.session_state:
        st.session_state['user'] = None
    if 'show_login' not in st.session_state:
        st.session_state['show_login'] = False

def logout():
    """Log out the current user."""
    st.session_state['user'] = None
    st.success("Logged out successfully!")

def auth_sidebar():
    """Add authentication sidebar with login/logout options."""
    initialize_session_state()
    
    with st.sidebar:
        if is_authenticated():
            st.write(f"Logged in as: **{st.session_state['user']['user']}**")
            if st.button("Logout"):
                logout()
                st.rerun()
        else:
            show_login_widget()
