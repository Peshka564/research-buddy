import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from sentence_transformers import CrossEncoder
from pydantic import SecretStr, BaseModel, Field
from typing import Optional

app = Flask(__name__)
CORS(app)

load_dotenv()

chroma_db_path = "./chroma_db_arxiv"
collection_name = "arxiv"
groq_api_key = os.getenv("GROQ_API_KEY")

print("Initializing...")
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

print(f"Connecting to Vector Db...")
if not os.path.exists(chroma_db_path):
    raise RuntimeError(f"Db not found: {chroma_db_path}")

vector_store = Chroma(
    collection_name=collection_name,
    embedding_function=embedding_function,
    persist_directory=chroma_db_path
)

llm = ChatGroq(
    temperature=0, 
    model="llama-3.3-70b-versatile",
    api_key=SecretStr(groq_api_key) if groq_api_key is not None else None
)

# TODO: this + citations
# reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

class SearchIntent(BaseModel):
    query_content: str = Field(description="The core semantic topic of the user's question, stripped of filters.")
    year_start: Optional[int] = Field(description="The start year filter, if mentioned (e.g., 'since 2020').")
    year_end: Optional[int] = Field(description="The end year filter, if mentioned.")
    category: Optional[str] = Field(description="ArXiv category code if mentioned (e.g., 'cs.AI', 'physics').")
    author: Optional[str] = Field(description="Specific author name if mentioned.")
    sort_by: Optional[str] = Field(description="Sorting preference: 'relevance' or 'date'.")

system_prompt = """You are an expert at parsing academic search queries. 
Extract filters (year, author, category) and the core topic from the user's query.
If the user mentions 'recent' or 'newest', set sort_by to 'date'.
ArXiv categories: cs.AI, cs.LG, math.CO, physics, etc.
"""

structured_llm = llm.with_structured_output(SearchIntent)
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}")
])
analyzer_chain = prompt | structured_llm

hyde_template = """Please write a short, scientific abstract (5-6 sentences) that would ideally answer this question: "{query}". 
Do not include any conversational text, just the abstract."""
hyde_prompt = ChatPromptTemplate.from_template(hyde_template)
hyde_chain = hyde_prompt | llm

@app.route('/search', methods=['POST'])
def search_papers():
    """ Top K Document Retrieval"""
    
    # { "query": string, "k": int }
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({"message": "Missing 'query' field in payload"}), 400
    
    query_text = data['query']
    k_results = data.get('k', 5)
    
    try:
        results = vector_store.similarity_search_with_score(query_text, k=k_results)
        
        response_data = []
        for doc, score in results:
            response_data.append({
                "id": doc.metadata.get("id"),
                "title": doc.page_content.split('\n')[0].replace("Title: ", ""),
                "abstract": doc.metadata.get("abstract", "No abstract available"),
                "authors": doc.metadata.get("authors"),
                "year": doc.metadata.get("year"),
                "similarity_score": float(score),
                "categories": doc.metadata.get("categories")
            })
            
        return jsonify({
            "original_query": query_text,
            "interpreted_intent": query_text,
            "results": response_data
        })

    except Exception as e:
        print(f"Error during search: {e}")
        return jsonify({"message": "Internal server error"}), 500

@app.route('/smart_search', methods=['GET'])
def smart_search():
    """ Top K Document Retrieval but smarter"""
    
    query_input = request.args.get('query')
    k_input = request.args.get('k')

    if not query_input or not k_input:
        return jsonify({"message": "Missing 'query' field in payload"}), 400
    
    query_text = query_input
    k_results = int(k_input)

    try:
        analysis = analyzer_chain.invoke({"input": query_text})
        print(f"Analysis Result: {analysis}")

        filters = []
        if analysis.year_start:
            filters.append({"year": {"$gte": str(analysis.year_start)}})
        if analysis.year_end:
            filters.append({"year": {"$lt": analysis.year_end}})
        # if analysis.category:
        #     filters.append({"categories": {"$contains": analysis.category}})
        # if analysis.author:
        #     filters.append({"authors": {"$contains": analysis.author}})
            
        # Combine filters
        if len(filters) > 1:
            chroma_filter = {"$and": filters}
        elif len(filters) == 1:
            chroma_filter = filters[0]
        else:
            chroma_filter = None

        search_query = analysis.query_content
        # Generate a fake abstract to search with
        hypothetical_abstract = hyde_chain.invoke({"query": search_query}).content
        print(f"HyDE Abstract: {hypothetical_abstract[:500]}...")
        search_query = hypothetical_abstract

        # TODO: Handle categories and author strings by manual filter after fetching from db with enough k

        # Note: Chroma allows passing 'filter' to similarity_search
        results = vector_store.similarity_search_with_score(
            search_query, 
            k=k_results, 
            filter=chroma_filter
        )

        response_data = []
        for doc, score in results:
            # print(doc)
            # print(doc.metadata)
            print(doc.metadata)
            print(doc.metadata.get('abstract'))
            print(doc.metadata.get('Abstract'))
            response_data.append({
                "id": doc.metadata.get("id"),
                "title": doc.page_content.split('\n')[0].replace("Title: ", ""),
                "abstract": doc.metadata.get("Abstract", "No abstract available"),
                "authors": doc.metadata.get("authors"),
                "year": doc.metadata.get("year"),
                "similarity_score": float(score),
                "categories": doc.metadata.get("Categories")
            })

        return jsonify({
            "original_query": query_text,
            "interpreted_intent": analysis.model_dump(),
            "results": response_data
        })

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)