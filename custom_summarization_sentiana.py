import os
import streamlit as st
from langchain.chains import LLMChain
from langchain.chat_models import AzureChatOpenAI
from langchain.callbacks import get_openai_callback
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import Docx2txtLoader
from langchain import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from nltk_senana import sentiment
from voice import record_voice
from definitions_abk import (
    CHAT_OPENAI_API_TYPE,
    CHAT_OPENAI_API_VERSION,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_KEY,
    CHAT_AZURE_DEPLOYMENT
)

os.environ["OPENAI_API_TYPE"] = CHAT_OPENAI_API_TYPE
os.environ["OPENAI_API_VERSION"] = CHAT_OPENAI_API_VERSION
os.environ["OPENAI_API_BASE"] = AZURE_OPENAI_ENDPOINT
os.environ["OPENAI_API_KEY"] = AZURE_OPENAI_API_KEY


model = AzureChatOpenAI(deployment_name=CHAT_AZURE_DEPLOYMENT,temperature=0)
                    
print (model)

def language_selector():
    lang_options = ["ar", "de", "en", "es", "fr", "it", "ja", "nl", "pl", "pt", "ru", "zh"]
    with st.sidebar:
        return st.selectbox("Speech Language", ["en"] + lang_options)

def print_chat_message(message):
    text = message["content"]

def custom_summary_pdf(docs,llm, custom_prompt, chain_type, num_summaries):
    custom_prompt = custom_prompt + """:\n\n {text}"""
    COMBINE_PROMPT = PromptTemplate(template=custom_prompt, input_variables=["text"])
    MAP_PROMPT = PromptTemplate(template="Summarize:\n\n{text}", input_variables=["text"])
    if chain_type == "map_reduce":
        chain = load_summarize_chain(llm=model, chain_type=chain_type, 
                                    map_prompt=MAP_PROMPT, combine_prompt=COMBINE_PROMPT)
    else:
        chain = load_summarize_chain(llm=model, chain_type=chain_type)
    summaries = []
    for i in range(num_summaries):
        summary_output = chain({"input_documents": docs}, return_only_outputs=True)["output_text"]
        summaries.append(summary_output)
    
    return summaries

def custom_summary_doc(docs,llm, custom_prompt, chain_type, num_summaries):
    custom_prompt = custom_prompt + """:\n\n {text}"""
    COMBINE_PROMPT = PromptTemplate(template=custom_prompt, input_variables=["text"])
    MAP_PROMPT = PromptTemplate(template="Summarize:\n\n{text}", input_variables=["text"])
    if chain_type == "map_reduce":
        chain = load_summarize_chain(llm=model, chain_type=chain_type, 
                                    map_prompt=MAP_PROMPT, combine_prompt=COMBINE_PROMPT)
    else:   
        chain = load_summarize_chain(llm=model, chain_type=chain_type)
    summaries = []
    for i in range(num_summaries):
        summary_output = chain({"input_documents": docs}, return_only_outputs=True)["output_text"]
        summaries.append(summary_output)
            
    return summaries

@st.cache_data
def setup_documents_pdf(pdf_file_path, chunk_size, chunk_overlap):
    loader = PyPDFLoader(pdf_file_path)
    docs_raw = loader.load()
    docs_raw_text = [doc.page_content for doc in docs_raw]
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs = text_splitter.create_documents(docs_raw_text)
    return docs

@st.cache_data
def setup_documents_doc(doc_file_path, chunk_size, chunk_overlap):
    loader =  Docx2txtLoader(doc_file_path)
    docs_raw = loader.load()
    docs_raw_text = [doc.page_content for doc in docs_raw]
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs = text_splitter.create_documents(docs_raw_text)
    return docs

@st.cache_data
def color_chunks(text: str, chunk_size: int, overlap_size: int) -> str:
    overlap_color = "#808080" # Light gray for the overlap
    chunk_colors = ["#a8d08d", "#c6dbef", "#e6550d", "#fd8d3c", "#fdae6b", "#fdd0a2"] # Different shades of green for chunks

    colored_text = ""
    overlap = ""
    color_index = 0

    for i in range(0, len(text), chunk_size-overlap_size):
        chunk = text[i:i+chunk_size]
        if overlap:
            colored_text += f'<mark style="background-color: {overlap_color};">{overlap}</mark>'
        chunk = chunk[len(overlap):]
        colored_text += f'<mark style="background-color: {chunk_colors[color_index]};">{chunk}</mark>'
        color_index = (color_index + 1) % len(chunk_colors)
        overlap = text[i+chunk_size-overlap_size:i+chunk_size]

    return colored_text

def main():
    st.set_page_config(layout="wide")
    st.title("Custom Summarization App")
    chain_type = st.sidebar.selectbox("Chain Type", ["map_reduce", "stuff", "refine"])
    chunk_size = st.sidebar.slider("Chunk Size", min_value=100, max_value=10000, step=100, value=1900)
    chunk_overlap = st.sidebar.slider("Chunk Overlap", min_value=100, max_value=10000, step=100, value=200)
    
    if st.sidebar.checkbox("Debug chunk size"):
        st.header("Interactive Text Chunk Visualization")

        text_input = st.text_area("Input Text", "This is a test text to showcase the functionality of the interactive text chunk visualizer.")

        # Set the minimum to 1, the maximum to 5000 and default to 100
        html_code = color_chunks(text_input, chunk_size, chunk_overlap)
        st.markdown(html_code, unsafe_allow_html=True)
    
    else:
        user_prompt = st.text_input("Enter the user prompt")
        question = record_voice(language=language_selector())
        pdf_file_path = st.text_input("Enter the pdf file path")
        doc_file_path = st.text_input("Enter the doc file path") 
        temperature = st.sidebar.number_input("ChatGPT Temperature", min_value=0.0, max_value=1.0, step=0.1, value=0.0)
        num_summaries = st.sidebar.number_input("Number of Summaries", min_value=1, max_value=10, step=1, value=1)
        
        # make the choice of llm to select from a selectbox
        llm = st.sidebar.selectbox("LLM", ["GPT4", "ChatGPT", ""])
        if llm == "GPT4":
            llm = AzureChatOpenAI(model_name="model", temperature=temperature)
        elif llm == "ChatGPT":
            llm = AzureChatOpenAI(model_name="model",temperature=temperature)
        
        if pdf_file_path != "":
            docs = setup_documents_pdf(pdf_file_path, chunk_size, chunk_overlap)
            st.write("Pdf was loaded successfully")
          
            if st.button("Summarize"):
               result = custom_summary_pdf(docs,llm, user_prompt, chain_type, num_summaries)
               st.write("summaries:")
               for summary in result:
                   st.write(summary)
               #st.button("Perform Sentiment Analysis")
       # Perform sentiment analysis using the sentiment function
               sentiment_result = sentiment(result)
               if sentiment_result =='Positive':
                     style = positive_style
               elif sentiment_result == "Negative" :
                     style = negative_style
               else:
                     style = ""

        # Display the sentiment analysis result
               st.subheader("Sentiment Analysis Result:")
               st.markdown(f"**Sentiment:** <span style='{style}'>{sentiment_result}</span>", unsafe_allow_html=True)
        
        if pdf_file_path != "" and question:
             user_message = {"role": "user", "content": question}
             print_chat_message(user_message)

             user_prompt_1= st.text_input("Enter some text here", question )
             if st.button("Summarize_audio_pdf"):
                result = custom_summary_pdf(docs,llm,user_prompt_1,chain_type, num_summaries)
                st.write("summaries:")
                for summary in result:
                    st.write(summary)
                sentiment_result = sentiment(result)
                if sentiment_result =='Positive':
                     style = positive_style
                elif sentiment_result == "Negative" :
                     style = negative_style
                else:
                     style = ""

        # Display the sentiment analysis result
                st.subheader("Sentiment Analysis Result:")
                st.markdown(f"**Sentiment:** <span style='{style}'>{sentiment_result}</span>", unsafe_allow_html=True)

        if doc_file_path != "":
            docs = setup_documents_doc(doc_file_path, chunk_size, chunk_overlap)
            st.write("Doc was loaded successfully")

            if st.button("Summarize"):
               result = custom_summary_doc(docs,llm, user_prompt, chain_type, num_summaries)
               st.write("summaries:")
               for summary in result:
                   st.write(summary)
               #st.button("Perform Sentiment Analysis")
       # Perform sentiment analysis using the sentiment function
               sentiment_result = sentiment(result)
               if sentiment_result =='Positive':
                     style = "a"
               elif sentiment_result == "Negative" :
                     style = "b"
               else:
                     style = ""

        # Display the sentiment analysis result
               st.subheader("Sentiment Analysis Result:")
               st.markdown(f"**Sentiment:** <span style='{style}'>{sentiment_result}</span>", unsafe_allow_html=True)

        if doc_file_path != "" and question:
             user_message = {"role": "user", "content": question}
             print_chat_message(user_message)

             user_prompt_1= st.text_input("Enter some text here", question )
             if st.button("Summarize_audio_doc"):
                result = custom_summary_doc(docs,llm,user_prompt_1,chain_type, num_summaries)
                st.write("summaries:")
                for summary in result:
                    st.write(summary)
                sentiment_result = sentiment(result)
                if sentiment_result =='Positive':
                     style = positive_style
                elif sentiment_result == "Negative" :
                     style = negative_style
                else:
                     style = ""

        # Display the sentiment analysis result
                st.subheader("Sentiment Analysis Result:")
                st.markdown(f"**Sentiment:** <span style='{style}'>{sentiment_result}</span>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
