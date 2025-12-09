import streamlit as st
import mysql.connector
import boto3
import json
import re  # For email validation
from typing import Dict, Any, Optional

# NOTE: For production, use a library like bcrypt for password hashing.
# Placeholder function for demonstration purposes.
def hash_password(password: str) -> str:
    """Placeholder: In a real application, use bcrypt or similar for hashing."""
    return f"HASHED_{password}_SECURELY"


# --------------------------------------------------------
# -------------------- CSS (Green Theme) ------------------
# --------------------------------------------------------

def inject_css():
    """Injects custom CSS for the signup page styling."""
    CSS = """
    <style>
    /* Hide Streamlit Menu and Footer */
    #MainMenu, footer { visibility: hidden; }

    .signup-box {
        background: #ffffff;
        width: 420px;
        padding: 40px;
        margin: auto;
        margin-top: 50px;
        border-radius: 18px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.08);
        border: 1px solid #e6e6e6;
    }
    .center { text-align:center; }
    .title-header {
        font-size: 30px;
        font-weight: 700;
        color: #222;
        margin-bottom: 5px;
    }
    .subtitle {
        font-size: 16px;
        color: #666;
        margin-bottom: 25px;
    }
    .stTextInput > label {
        display: none; /* Hides the default Streamlit label */
    }
    .stTextInput input {
        border-radius: 10px !important;
        border: 1px solid #cccccc !important;
        padding: 12px 14px !important;
        font-size: 16px !important;
        margin-bottom: 5px; /* Add small margin below inputs */
    }
    .stTextInput input:focus {
        border-color: #28a745 !important;
        box-shadow: 0px 0px 0px 2px rgba(40, 167, 69, 0.25) !important;
    }
    .stButton>button {
        background-color: #28a745 !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 12px !important;
        border: none !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        transition: background-color 0.3s ease;
        margin-top: 20px;
    }
    .stButton>button:hover {
        background-color: #1f7a38 !important;
    }
    </style>
    """
    st.markdown(CSS, unsafe_allow_html=True)

# --------------------------------------------------------
# ---------------- AWS Secrets Manager & DB ----------------
# --------------------------------------------------------

# NOTE: It is best practice to use st.secrets in Streamlit, 
# but keeping the boto3 fetching logic as per the original requirement.
AWS_REGION = "ap-south-1"
SECRET_ARN = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:salesbuddy/secrets-0xh2TS"

@st.cache_resource
def get_db_credentials() -> Dict[str, str]:
    """Fetches and maps DB credentials from AWS Secrets Manager."""
    try:
        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        resp = client.get_secret_value(SecretId=SECRET_ARN)
        raw = json.loads(resp["SecretString"])

        creds = {
            "DB_HOST": raw["host"],
            "DB_USER": raw["username"],
            "DB_PASSWORD": raw["password"],
            "DB_NAME": raw["dbname"]
        }
        return creds

    except Exception as e:
        st.error("Configuration Error: Failed to load database credentials.")
        st.stop()
        # Raise RuntimeError(f"Failed to load DB secrets: {e}")


@st.cache_resource
def get_connection() -> mysql.connector.connection.MySQLConnection:
    """Establishes and returns a persistent MySQL database connection."""
    creds = get_db_credentials()
    try:
        conn = mysql.connector.connect(
            host=creds["DB_HOST"],
            user=creds["DB_USER"],
            password=creds["DB_PASSWORD"],
            database=creds["DB_NAME"],
            charset="utf8mb4",
            autocommit=False # Better control over transactions
        )
        return conn

    except mysql.connector.Error as e:
        st.error(f"Database Connection Error: Could not connect to MySQL.")
        st.stop()
        # Raise RuntimeError(f"MySQL Connection Error: {e}")


# --------------------------------------------------------
# ------------------ INPUT VALIDATION ---------------------
# --------------------------------------------------------

def validate_signup_inputs(data: Dict[str, str]) -> Optional[str]:
    """Validates user input fields and returns an error message if invalid."""
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not all(data.values()):
        return "All fields are required."
    
    if data['password'] != data['confirm_password']:
        return "Passwords do not match!"
    
    if len(data['password']) < 8:
        return "Password must be at least 8 characters long."

    if not re.match(email_regex, data['email']):
        return "Please enter a valid email address."
    
    # Simple check for mobile number (can be enhanced)
    if not data['mobile'].isdigit() or len(data['mobile']) < 10:
        return "Please enter a valid mobile number."

    return None # Returns None if validation passes


# --------------------------------------------------------
# ------------------ SIGNUP PAGE RENDER -------------------
# --------------------------------------------------------

def render(navigate: Any):
    """
    Renders the user signup form and handles submission logic.

    :param navigate: A function to change the application view (e.g., navigate("login")).
    """
    inject_css()

    st.markdown("<div class='signup-box'>", unsafe_allow_html=True)

    st.markdown("""
        <div style='text-align:center;'>
            <img src="https://cdn-icons-png.flaticon.com/512/149/149071.png"
            width="70"
            style="background-color:#28a745; border-radius:50%; padding:10px;">
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<h2 class='title-header center'>Create Your Account</h2>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle center'>Join Sales Buddy today</p>", unsafe_allow_html=True)

    # Use a Streamlit form for cleaner input handling
    with st.form(key='signup_form'):
        # Input fields
        full_name = st.text_input("Full Name", placeholder="Full Name")
        email = st.text_input("Email", placeholder="Email Address")
        company = st.text_input("Company", placeholder="Company Name")
        mobile = st.text_input("Mobile", placeholder="Mobile Number")
        password = st.text_input("Password", type="password", placeholder="Password (Min 8 characters)")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm Password")

        submitted = st.form_submit_button("Sign Up", use_container_width=True)

        if submitted:
            user_data = {
                'full_name': full_name.strip(),
                'email': email.strip(),
                'company': company.strip(),
                'mobile': mobile.strip(),
                'password': password,
                'confirm_password': confirm_password
            }
            
            error_message = validate_signup_inputs(user_data)

            if error_message:
                st.error(error_message)
            else:
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    
                    # NOTE: Always hash the password before storing!
                    hashed_password = hash_password(password)

                    query = """
                        INSERT INTO users(full_name, email, company, mobile, password)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    # Use the HASHED password in the execute call
                    cur.execute(query, (user_data['full_name'], user_data['email'], 
                                        user_data['company'], user_data['mobile'], 
                                        hashed_password))
                    
                    conn.commit()
                    st.success("Account Created Successfully! Redirecting to login...")
                    navigate("login")

                except mysql.connector.IntegrityError:
                    # Handles duplicate entry (e.g., email already exists)
                    st.error("An account with this email address already exists.")
                except mysql.connector.Error as err:
                    conn.rollback() # Rollback transaction on error
                    st.error(f"Database Error: Could not complete registration. Please try again.")
                except Exception as e:
                    st.exception(f"An unexpected error occurred: {e}")
                finally:
                    # Close connection cursor only, the connection object is cached
                    if 'conn' in locals() and conn.is_connected():
                         cur.close()

    st.markdown("</div>", unsafe_allow_html=True)
