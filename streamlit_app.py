import streamlit as st
from openai import AzureOpenAI
import os

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

 

    # Ask the user for a question via `st.text_area`.
    question = st.text_area(
        "Ask your question here! (demo purposes only, responses may contain factual errors or omissions)",
        placeholder="How can I help you?")


    if question:

        # Process the uploaded file and question.
        
        messages = [
            {
                "role": "system",
                "content": f"You are a public health call center worker, assigned to answer messages from the public. Be gracious, be kind, and try to instill a sense of calm in your user. At the end, list your cited documents by id and url.",
            },
            {
                "role": "user",
                "content": f"Use only the data sources provided. Here's a question:{question}.  At the end, list your cited documents by title, id, or url.",
            }
        ]
        #get the key from the codespace secret
        search_key = os.getenv("AZURE_SEARCH_KEY")
        # Generate an answer using the OpenAI API.
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            stream=True, 
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
                        "index_name": "prms_content",
                        "endpoint": "https://dupcontensearch.search.windows.net",  
                        "semantic_configuration": "prms-search",
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

        # Stream the response to the app using `st.write_stream`.
        st.write_stream(stream)
