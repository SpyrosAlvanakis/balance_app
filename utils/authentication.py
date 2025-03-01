import hmac
import streamlit as st

@st.dialog("Login")
def check_password_widget():
    # Show input for password.
    user = st.text_input("Username", type="default", key="username")
    if user in st.secrets["passwords"]:
        roles = []
        for role in st.secrets.roles:
            if user in st.secrets.roles[role]:
                roles.append(role)

        if roles == []:
            st.error(f"User {user} does not have a role")
            st.session_state['user'] =  None
            st.stop()

        password =st.text_input("Password", type="password", key="password")
        if st.button("Login"):
            if hmac.compare_digest(password, st.secrets["passwords"][user]):
                st.success("Password correct")
                st.session_state['user'] =  {"user":user, "roles":roles}
                st.rerun()
            else:
                st.error("😕 Password incorrect")
                st.session_state['user'] =  None
                st.stop()
    else:
        st.error("No such user name exists") 
        st.session_state['user'] =  None
        st.stop()