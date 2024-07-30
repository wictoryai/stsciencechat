import streamlit as st
import openai
from llama_index.llms.openai import OpenAI
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
import weaviate
import weaviate.classes as wvc
import os
import requests
import json
from weaviate.classes.init import Auth
from llama_index.vector_stores.weaviate import WeaviateVectorStore
import re
import ast

st.set_page_config(page_title="Chat with the Streamlit docs, powered by LlamaIndex", page_icon="w", layout="centered", initial_sidebar_state="auto", menu_items=None)
openai.api_key = "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"
st.title("Chat with sports and excercise science papers 💬🦙")
st.info("powered by wictory.ai", icon="📃")

# Example NodeWithScore class (adjust based on your actual class definition)
class NodeWithScore:
    def __init__(self, node, score):
        self.node = node
        self.score = score


# Function to extract file_name and page_label
def extract_file_info(source_nodes):
    file_info = []

    for item in source_nodes:
        # Extract file_name and page_label from the node's metadata
        metadata = item.node.get('metadata', {})
        file_name = metadata.get('file_name', 'Unknown')
        page_label = metadata.get('page_label', 'Unknown')
        file_info.append((file_name, page_label))
    
    return file_info

# Simulate parsing the complex string response
def parse_item(item_str):
    # Extract file_name and page_label from a complex string
    import re
    file_name = re.search(r"file_name': '([^']*)'", item_str)
    page_label = re.search(r"page_label': '([^']*)'", item_str)
    return (file_name.group(1) if file_name else 'Unknown',
            page_label.group(1) if page_label else 'Unknown')


from llama_index.core import StorageContext

wcd_url = "https://gsnv1etrtccnkieya2vuw.c0.europe-west3.gcp.weaviate.cloud"
wcd_api_key = "4v5NU76VwO5dnABjpKlE2e77xEYAmrt5GeXT"
openai_api_key = "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"

os.environ["OPENAI_APIKEY"] = "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"
os.environ["WEAVAIATE_API_KEY"] = "4v5NU76VwO5dnABjpKlE2e77xEYAmrt5GeXT"
os.environ["WCD_DEMO_URL"] = "https://gsnv1etrtccnkieya2vuw.c0.europe-west3.gcp.weaviate.cloud"

cluster_url = "https://gsnv1etrtccnkieya2vuw.c0.europe-west3.gcp.weaviate.cloud"
api_key = "4v5NU76VwO5dnABjpKlE2e77xEYAmrt5GeXT"

client = weaviate.connect_to_wcs(
    cluster_url=cluster_url,
    auth_credentials=weaviate.auth.AuthApiKey(api_key),
)


@st.cache_resource(show_spinner=False)
def load_data():
    """
    get latest research from weaviate database
    """

    
    vector_store = WeaviateVectorStore(
    weaviate_client=client, index_name="PersonalPeakDocuments"
    )
    
    loaded_index = VectorStoreIndex.from_vector_store(vector_store)
    
    return loaded_index


if "messages" not in st.session_state.keys():  # Initialize the chat messages history
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Ask me a question about the most recent research in sports and exercise pyhsiology!",
        }
    ]


index = load_data()

if "chat_engine" not in st.session_state.keys():  # Initialize the chat engine
    st.session_state.chat_engine = index.as_chat_engine(
        chat_mode="condense_question", verbose=True, streaming=True
    )

if prompt := st.chat_input(
    "Ask a question"
):  # Prompt for user input and save to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages:  # Write message history to UI
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        response_stream = st.session_state.chat_engine.stream_chat(prompt)
        st.write_stream(response_stream.response_gen)
        source_list = []
        for item in response_stream.source_nodes:
            source = item.node.metadata.get('file_name', 'unknown source')
            st.write("Source: ", source)
            source_list.append(source)
            


        message = {"role": "assistant", "content": response_stream.response}
        source_message = {"role": "assistant", "content": source_list}
        # Add response to message history
        st.session_state.messages.append(message)
        st.session_state.messages.append(source_message)
        

