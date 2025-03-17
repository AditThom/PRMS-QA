import requests
import streamlit as st
from openai import AzureOpenAI
import os
import pandas as pd
import io
import bs4
from bs4 import BeautifulSoup

# Load PRs into dataframe from csv file
csv_file_path = "/workspaces/PRMS-QA/data/PR_SourceList.csv"
prs_df = pd.read_csv(csv_file_path,encoding='1252',header=0,names=['ID','Content','Question','Source'])

# Show title and description.
st.image("https://www.cdc.gov/TemplatePackage/5.0/img/logo/cdc-logo-tag-right.svg")
st.title("CDC-INFO AIChat (POC)")

st.write(
    "Ask a question below and our friendly assistant will try and answer it! "
)

# Ask user for their OpenAI API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management
openai_api_key = st.text_input("Azure OpenAI API Key", type="password",value=os.getenv("AZURE_OPENAI_KEY"))
if not openai_api_key:
    st.info("Please add your Azure OpenAI API key to continue.", icon="🗝️")
else:

    # Create an OpenAI client.
    client = AzureOpenAI(
        api_key = openai_api_key,
        api_version = "2024-02-01",
        azure_endpoint ="https://openai-thom.openai.azure.com/" 
 )

    # Function to read the body of a web page into a text version

    def read_web_page(url):
        response = requests.get(url)
        if response.status_code == 200:
            res = requests.get(url)
            html_page = res.content
            soup = BeautifulSoup(html_page, 'html.parser')
            text = soup.find_all('p')

            output = ''
            blacklist = [
                '[document]',
                'noscript',
                'header',
                'footer'
                'html',
                'meta',
                'head', 
                'input',
                'script',
                'style'
                # there may be more elements you don't want, such as "style", etc.
            ]

            for t in text:
                if t.parent.name not in blacklist:
                    output += '{} '.format(t)

            return output
        else:
            st.error(f"Failed to retrieve the web page. Status code: {response.status_code}")
            return ""

    # Example usage
    web_page_url = st.text_input("Enter the URL of the web page to add to the PR data.")
    if web_page_url:
        document_content = read_web_page(web_page_url)
        st.text_area("Web Page Content", document_content, height=300)
    else:
        document_content = None

    # Ask the user for a question via `st.text_area`.
    question = st.text_area(
        "Ask your question here! (demo purposes only, responses may contain factual errors or omissions)",
        placeholder="How can I help you?")


    if question:

        # Process the uploaded file and question.
        if document_content:
            messages = [
                {
                    "role": "system",
                    "content": f"You are a public health call center worker, assigned to answer messages from the public. Be gracious, be kind, and try to instill a sense of calm in your user. At the end, list your cited documents in a numbered list by title.",
                },
                {
                    "role": "user",
                    "content": f"Use only the data sources provided. Be kind and gentle with the user! Here's a question:{question}.  At the end, list your cited documents in a numbered list by title.  Also consider the information below: {document_content}. If you do use the information, please cite the source as \"User information provided\".",
                }
            ]
        else:
            messages = [
                {
                    "role": "system",
                    "content": f"You are a public health call center worker, assigned to answer messages from the public. Be gracious, be kind, and try to instill a sense of calm in your user. At the end, list your cited documents in a numbered list by title.",
                },
                {
                    "role": "user",
                    "content": f"Use only the data sources provided. Be kind and gentle with the user! Here's a question:{question}.  At the end, list your cited documents in a numbered list by title",
                }
            ]
        #get the key from the codespace secret
        search_key = os.getenv("AZURE_SEARCH_KEY")
        # Generate an answer using the OpenAI API.
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            stream=False, 
            max_tokens=800,  
            temperature=0.7,  
            top_p=0.95,  
            frequency_penalty=0,  
            presence_penalty=0,  
            stop=None,  
            extra_body={  
                "data_sources": [
                {  
                    "type": "azure_search",
                    "parameters": { 
                        "index_name": "cdccontentindex",
                        "endpoint": "https://dupcontensearch.search.windows.net",  
                        "semantic_configuration": "cdccontentsemcon",
                        "query_type": "semantic",
                        "fields_mapping": {},
                        "in_scope": True,
                        "role_information": "You are a public health call center worker, assigned to answer messages from the public. Be gracious, be kind, and try to instill a sense of calm in your user. Cite your sources.",
                        "filter": None,
                        "strictness": 5,
                        "top_n_documents": 5,
                        "authentication":{  
                            "type":"api_key",
                            "key":f"{search_key}"
                        }
                    } 
                } 
            ]}
        )

        responseContent = response.choices[0].message.content
        # Stream the response to the app using `st.write_stream`.
        st.write(responseContent)       

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<H2>Source Text from Application Data<H2>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        for i,row in prs_df.iterrows():
            if( (('AGENT' in str(row['Question'])) 
                or 'SPECIALIST' in str(row['Question']) 
                or 'GENERALIST' in str(row['Question']) 
                or 'WORKFLOW' in str(row['Question']) 
                or 'CTA' in str(row['Question']) 
                or 'CALL TO ACTION' in str(row['Question']) 
                or 'EMAIL' in str(row['Question']) 
                or 'LOG CALL' in str(row['Question'])
                or str(row['Question']).strip().endswith('?')) 
                and str(row["Question"])in responseContent):
                    st.write("\nPR:" + str(row['ID']) + '-' + str(row['Question']))
                    st.write(str(row['Content']) + "\n")
                    st.markdown("<br>", unsafe_allow_html=True)