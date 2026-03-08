# Research Buddy
An AI-powered RAG app which allows you to easily understand, reason about, and explore STEM papers

### Features:
- Search for papers functionality which allows the user to query the database of ArXiv papers (https://www.kaggle.com/datasets/Cornell-University/arxiv/data) for the most relevant results <br>
It consists of a structured LLM which extracts different filters from the user query (like search after a specific year or a specified set of authors) <br>
After that, HyDE embeddings are applied which expand short user queries into queries that contain more key words and can return more results from the vector DB<br>
A vector database (ChromaDB) is used to embed the metadata of all papers (including the abstract) and search by that<br>
The reranker is used by casting a wide net of similarity results and using <b>HuggingFace CrossEncoder</b> to reason about how they actually match with the user query and intention and select the top k choices
<img width="1152" height="345" alt="image" src="https://github.com/user-attachments/assets/dbefad7d-55e7-463a-a0cf-537eb69e2da9" />
- Paper study mode which allows for the user to select a specific paper, and reason with a chatbot about different sections of the paper (much like DeepWiki but for papers)<br>
Using a React.js frontend, the selected paper PDF is visualized to the user<br>
Automatically, the paper is segmented into semantically similar chunks<br>
For each chunk, the user can open a chat and ask the chatbot about the chunk or how it fits with other parts of the paper<br>
<br>
The chatbot is a ReAct style agent with a couple of tools and a specified workflow in the system prompt:
- First, it searches for information in the specific chunk that the user has asked about
- If it does not find the information there, it search through all chunks in the paper (this is a separate tool)
- If that also does not work, it searches through the whole database for information in the papers (this is a separate tool) much like the user search functionality above
<img width="872" height="557" alt="image" src="https://github.com/user-attachments/assets/6ab74302-1133-4d36-8f10-95f371819ec0" />
