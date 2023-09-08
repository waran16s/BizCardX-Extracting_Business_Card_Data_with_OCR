import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
import psycopg2
import cv2
import os
import matplotlib.pyplot as plt
import re

# database Connection
conn=psycopg2.connect(host='localhost',user='postgres',password='password',database='database')
cursor=conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS card_details
               (card_holder TEXT,
               company_name TEXT,               
               designation TEXT,
               mobile_number varchar(50) PRIMARY KEY,
               email TEXT,
               website TEXT,
               area TEXT,
               city TEXT,
               state TEXT,
               pin_code VARCHAR(10)
               )""")
conn.commit()

#easyocr class intiation
reader = easyocr.Reader(['en'])

def ogimg(image):
    fig= plt.subplots(figsize=(8, 8))
    plt.axis('off')
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

def image_preview(image, res):
  fig, ax = plt.subplots(figsize=(12, 12))
  for (bbox, text, prob) in res:
        (tl, tr, br, bl) = bbox
        tl = (int(tl[0]), int(tl[1]))
        tr = (int(tr[0]), int(tr[1]))
        br = (int(br[0]), int(br[1]))
        bl = (int(bl[0]), int(bl[1]))
        cv2.rectangle(image, tl, br, (0, 255, 0), 2)
        ax.annotate(text, (tr[0], tr[1]), fontsize=10, color='white', backgroundcolor='red')
  plt.axis('off')
  plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))


def img_to_binary(file):
    # Convert image data to binary format
    with open(file, 'rb') as file:
            binaryData = file.read()
    return binaryData

def get_data(res):
    for ind, i in enumerate(res):

        # To get WEBSITE_URL
        if "www " in i.lower() or "www." in i.lower():
                data["website"].append(i)
        elif "WWW" in i:
                data["website"] = res[4] + "." + res[5]

        # To get EMAIL ID
        elif "@" in i:
            data["email"].append(i)

        # To get MOBILE NUMBER
        elif "-" in i:
            data["mobile_number"].append(i)
            if len(data["mobile_number"]) == 2:
                data["mobile_number"] = " & ".join(data["mobile_number"])

        # To get COMPANY NAME
        if ind == len(res) - 1:
            data["company_name"].append(i)
        
        # To get CARD HOLDER NAME
        elif ind == 0:
            data["card_holder"].append(i)

        # To get DESIGNATION
        elif ind == 1:
            data["designation"].append(i)

        # To get AREA
        if re.findall('^[0-9].+, [a-zA-Z]+', i):
            data["area"].append(i.split(',')[0])
        elif re.findall('[0-9] [a-zA-Z]+', i):
            data["area"].append(i)

        # To get CITY NAME
        match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
        match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
        match3 = re.findall('^[E].*', i)
        if match1:
            data["city"].append(match1[0])
        elif match2:
            data["city"].append(match2[0])
        elif match3:
            data["city"].append(match3[0])

        # To get STATE
        state_match = re.findall('[a-zA-Z]{9} +[0-9]', i)
        if state_match:
            data["state"].append(i[:9])
        elif re.findall('^[0-9].+, ([a-zA-Z]+);', i):
            data["state"].append(i.split()[-1])
        if len(data["state"]) == 2:
            data["state"].pop(0)

        # To get PINCODE
        if len(i) >= 6 and i.isdigit():
            data["pin_code"].append(i)
        elif re.findall('[a-zA-Z]{9} +[0-9]', i):
            data["pin_code"].append(i[10:])
        #st.write(i)
    df = pd.DataFrame(data)
    return df
    #st.write(df)

def insert_data():
    try:
          for _, row in df.iterrows():
            insert_query = '''
                    INSERT INTO card_details (card_holder, company_name, designation, mobile_number, 
                    email, website, area, city, state, pin_code)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)

            '''
            values = (
                    row['card_holder'],
                    row['company_name'],
                    row['designation'],
                    row['mobile_number'],
                    row['email'],
                    row['website'],
                    row['area'],
                    row['city'],
                    row['state'],
                    row['pin_code'],
                    #row['image']
                )
            cursor.execute(insert_query,values)
            conn.commit()
            st.success("Data uploaded Successfully !")
    except:
        conn.rollback()
        st.success("Data already exists !")


def show_data():
    try:
        cursor.execute("select card_holder,company_name,designation,mobile_number,email,website,area,city,state,pin_code from card_details")
        conn.commit()
        table=cursor.fetchall()
        st.write(pd.DataFrame(table, columns=['Card Holder', 'Company Name', 'Designation','Mobile Number', 'Email', 'Website', 'Area', 'City',
                                            'State', 'Pin Code']))
    except:
        conn.rollback()
        cursor.execute("select card_holder,company_name,designation,mobile_number,email,website,area,city,state,pin_code from card_details")
        conn.commit()
        table=cursor.fetchall()
        st.write(pd.DataFrame(table, columns=['Card Holder', 'Company Name', 'Designation','Mobile Number', 'Email', 'Website', 'Area', 'City',
                                            'State', 'Pin Code']))

def fetch_data():
    try:
        cursor.execute('select * from card_details')
        rows=cursor.fetchall()
        columns_names =[desc[0] for desc in cursor.description]
        conn.commit
    except:
        conn.rollback()
        cursor.execute('select * from card_details')
        rows=cursor.fetchall()
        columns_names=[desc[0] for desc in cursor.description]
        conn.commit

    data_dict={}
    for row in rows:
            data_dict[row[0]]=row[0:]

    return data_dict, columns_names

# function to update data in postgres Sql
def update_data(selected_option,updated_values,columns_names):
        try:
            update_query=f"UPDATE card_details set {','.join([f'{columns_names}=%s' for columns_names in columns_names])} WHERE card_holder = %s"
            cursor.execute(update_query,updated_values + [selected_option])
            conn.commit()
        except:
            conn.rollback()
            update_query=f"UPDATE card_details set {','.join([f'{columns_names}=%s' for columns_names in columns_names])} WHERE card_holder = %s"
            cursor.execute(update_query,updated_values + [selected_option])
            conn.commit()

def delete_data():
    try:
        delete_query="DELETE FROM card_details WHERE card_holder = %s"
        cursor.execute(delete_query,[selected_option])
        conn.commit()
    except:
       conn.rollback
       delete_query="DELETE FROM card_details WHERE card_holder = %s"
       cursor.execute(delete_query,[selected_option])
       conn.commit()

#-----------------------------------------------------------------------------------streamlit--------------------------------------------------------------------------------#
st.set_page_config(layout="wide")

st.markdown(f""" <style>.stApp {{
background:url("https://images.pexels.com/photos/19670/pexels-photo.jpg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1.jpg");
                    background-size: cover}}
                    </style>""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #6495ED;'>BizCardX: Extracting Business Card Data with OCR</h1>",
            unsafe_allow_html=True)

selected = option_menu(None,["HOME", "EXTRACT", "MODIFY"],
                       icons=["house", "cloud-upload","pencil-square"],
                       default_index=0,
                       orientation="horizontal",
                       styles={"nav-link": {"font-size": "20px", "text-align": "centre", "margin": "-2px","color":"#00FFF7", "--hover-color": "#0c457d"},
                               "icon": {"font-size": "35px","color":"#00FFF7"},
                               "container" : {"max-width": "3000px","border-radius": "0px","background-color": "#F0F9FB"},
                               "nav-link-selected": {"background-color": "#6495ED"}})

if selected == "HOME":
    st.write("Project Overview: BizCardX is a project that aims to simplify the process of extracting valuable information from business cards. It utilizes OCR technology to extract text and data from uploaded business card images. The extracted data is then processed and organized into a structured format, which can be stored in a PostgreSQL database for easy access and retrieval.")
    col1,col2=st.columns(2)
    with col1:
        st.image("https://www.comidor.com/wp-content/uploads/2022/08/ocr-55-e1661521818617-1024x569.png")
    with col2:
        st.image("https://miro.medium.com/v2/resize:fit:1400/1*hVxkXe35kRcAht3QpJylyg.gif") 

if selected == "EXTRACT":
    uploaded_card = st.file_uploader("upload here", label_visibility="collapsed", type=["png", "jpeg", "jpg"])

    if uploaded_card is not None:
        uploaded_cards_dir = os.path.join(os.getcwd(), "uploaded_cards")
        os.makedirs(uploaded_cards_dir, exist_ok=True)  # Create the directory if it doesn't exist
        with open(os.path.join(uploaded_cards_dir, uploaded_card.name), "wb") as f:
                f.write(uploaded_card.getbuffer())

        st.set_option('deprecation.showPyplotGlobalUse', False)
        saved_img = os.getcwd() + "\\" + "uploaded_cards" + "\\" + uploaded_card.name
        image = cv2.imread(saved_img)
        res = reader.readtext(saved_img)
        col1,col2=st.columns([0.4,0.6])
        with col1:
             st.markdown("***ORIGINAL IMAGE***")
             st.pyplot(ogimg(image))
        with col2:
            st.markdown("***PROCESSED IMAGE***")
            st.pyplot(image_preview(image, res))

        saved_img = os.getcwd() + "\\" + "uploaded_cards" + "\\" + uploaded_card.name
        result = reader.readtext(saved_img, detail=0, paragraph=False)

        data = {"card_holder": [],
            "company_name": [],
            "designation": [],
            "mobile_number": [],
            "email": [],
            "website": [],
            "area": [],
            "city": [],
            "state": [],
            "pin_code": [],
            "image": img_to_binary(saved_img)
            }
        
        df=get_data(result)
        st.dataframe(df)
        if st.button("Upload to Database"):
            insert_data()

        if st.button("View Data"):
            show_data()

if selected == "MODIFY":
   
        data_dict, column_names = fetch_data()

        # Create a dropdown box and populate it with the card holders
        selected_option = st.selectbox("Select a Card Holder:", ["None"] + list(data_dict.keys()))

        tab_1, tab_2 = st.tabs(["Edit Uploaded Data", "Delete Uploaded Data"])

        with tab_1:
        # Display text boxes for each column of the selected card holder
                if selected_option != "None":
                        st.write("You selected:", selected_option)
                        if selected_option in data_dict:
                                st.write("Modify the data:")
                                updated_values = list(data_dict[selected_option])  # Create a list of the original values
                                for i, column_name in enumerate(column_names):
                                        new_value = st.text_input(column_name, data_dict[selected_option][i])
                                        updated_values[i] = new_value  # Update the corresponding value
                                        st.write(f"Updated {column_name}: {new_value}")

                                # Add a button to save the updated data
                                if st.button("Update"):
                                        update_data(selected_option, updated_values, column_names)
                                        st.success("Data has been updated.")

                        else:
                                st.write("Option not found in data")
                else:
                        st.write("No card holder selected")

                #viewing the updated data
                if st.button("View Edited Data"):
                                show_data()

        with tab_2:
                if selected_option != "None":
                        st.write("You selected:", selected_option)
                        if selected_option in data_dict:
                                query = 'SELECT * FROM card_details WHERE card_holder = %s'
                                cursor.execute(query, (selected_option,))
                                conn.commit()
                                df = cursor.fetchall()
                                st.write(pd.DataFrame(df, columns=['Card Holder','Company Name', 'Designation','Mobile Number', 'Email', 
                                                                        'Website', 'Area', 'City','State', 'Pin Code']))
                                st.write("The Data Of This Card Holder Will Be Deleted")
                                if st.button("Delete"):
                                        delete_data()
                                        st.success("Data Successfully deleted!!")
                if st.button("View"):
                                show_data()  
