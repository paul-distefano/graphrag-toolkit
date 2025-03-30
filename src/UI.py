import streamlit as st
from graphrag_toolkit import LexicalGraphQueryEngine
from graphrag_toolkit.storage import GraphStoreFactory
from graphrag_toolkit.storage import VectorStoreFactory

import nest_asyncio
nest_asyncio.apply()

NO_RAG = 'No Rag'
VECTOR_RAG = 'Vector Rag'
GRAPH_RAG = 'Graph Rag'

# sidebar
with st.sidebar:
    st.title("GraphRAG POC")

    model = st.radio(
    'Select LLM',
    ['anthropic.claude-3-sonnet-20240229-v1:0', 'amazon.nova-lite-v1:0'])

    mode = st.radio(
    'Select Mode',
    [NO_RAG, VECTOR_RAG, GRAPH_RAG])

    sb_status = st.status("POC Initializing", expanded=True)

if 'initialized' not in st.session_state:
    st.session_state['initialized'] = True

    sb_status.write("attaching to graph DB")
    graph_store = GraphStoreFactory.for_graph_store(
        'neptune-db://db-neptune-pjd-graphrag.cluster-ro-cfotohhmiwj9.us-east-1.neptune.amazonaws.com')
    st.session_state['graph_store'] = graph_store

    sb_status.write("attaching to vector DB")
    vector_store = VectorStoreFactory.for_vector_store(
        'aoss://https://fdkekmuzcfbzpruy8954.us-east-1.aoss.amazonaws.com')
    st.session_state['vector_store'] = vector_store

    sb_status.write("instantiating query engines")
    graph_rag_query_engine = LexicalGraphQueryEngine.for_semantic_guided_search(
         graph_store,
         vector_store
    )
    st.session_state['graph_rag_query_engine'] = graph_rag_query_engine

    sb_status.update(label="POC Initialized")
    sb_status.update(state="complete")
    sb_status.update(expanded=False)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("user entry"):

    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    response = f"{st.session_state['query_engine'].query(prompt)}"

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
