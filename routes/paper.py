import os
from flask import Blueprint, request, jsonify
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.tools import tool
from services import embeddings, llm, chroma_db_path
from routes.utils.paper import semantically_chunk, get_chunks_with_coords
from routes.utils.search import smart_search
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

paper_bp = Blueprint('paper', __name__)

def get_vector_store(arxiv_id: str):
    """ We create a separate collection for the chunks of each paper """
    return Chroma(
        collection_name=f"paper_{arxiv_id}",
        embedding_function=embeddings,
        persist_directory=chroma_db_path
    )

@paper_bp.route('/process_paper_with_coords/<arxiv_id>', methods=['GET'])
def process_paper_with_coords(arxiv_id):
    print("Chunking paper...")
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    temp_filename = f"./temp/temp_{arxiv_id}.pdf"
    
    try:
        vector_store_for_paper = get_vector_store(arxiv_id)

        chunks_with_coords, all_text_content = get_chunks_with_coords(temp_filename, pdf_url)
        if not all_text_content:
            return jsonify({"error": "No text found"}), 400

        # Store the paper chunks in db
        docs = [Document(page_content=t, metadata={"chunk_index": i}) for i, t in enumerate(all_text_content)]
        vector_store_for_paper.add_documents(docs)

        # Semantically chunk the text
        vectors = embeddings.embed_documents(all_text_content)        
        labels = semantically_chunk(vectors)
        
        final_chunks = []
        for i, chunk in enumerate(chunks_with_coords):
            chunk["cluster_id"] = int(labels[i])
            chunk["id"] = i
            final_chunks.append(chunk)

        return jsonify({
            "chunks": final_chunks
        })

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

@tool
def search_paper_content(query: str, arxiv_id: str):
    """
    Search the full text of the paper.
    CRITICAL: Keep the 'query' extremely brief (max 2 sentences). 
    Do not include long descriptions or context. Just keywords.
    """
    print(f"'search_paper_content' tool called with query {query} and arxiv_id {arxiv_id}")
    try:
        vector_store = get_vector_store(arxiv_id)
        # Perform similarity search
        results = vector_store.similarity_search(query, k=3)
        return "\n\n".join([d.page_content for d in results])
    except Exception as e:
        return f"Error searching paper: {str(e)}"

@tool
def search_all_papers(query: str):
    """
    Search through all papers in the db.
    CRITICAL: Keep the 'query' extremely brief (max 2 sentences). 
    Do not include long descriptions or context.
    """
    print(f"'search_all_papers' tool called with query {query}")

    top_k_papers = 3
    top_k_chunks = 5
    try:
        relevant_papers, _, _ = smart_search(query, k_results=top_k_papers)
        candidate_chunks = []
        for paper in relevant_papers:
            pdf_url = f"https://arxiv.org/pdf/{paper.id}.pdf"
            temp_filename = f"./temp/temp_{paper.id}.pdf"
            _, all_text_content = get_chunks_with_coords(temp_filename, pdf_url)

            chunk_vectors = embeddings.embed_documents(all_text_content)

            query_vector = np.array([query]) 
            chunks_vectors = np.array(chunk_vectors)
        
            scores = cosine_similarity(query_vector, chunks_vectors)[0]
            top_indices = np.argsort(scores)[-1 * top_k_chunks:][::-1]
            for idx in top_indices:
                candidate_chunks.append({
                    "score": scores[idx],
                    "text": all_text_content[idx].text,
                })
            # Remove the papers
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

        candidate_chunks.sort(key=lambda x: x['score'], reverse=True)
        final_selection = candidate_chunks[:top_k_chunks]
        return "\n\n".join([d.text for d in final_selection])
    except Exception as e:
        return f"Error searching paper: {str(e)}"

# ReAct agent singleton
tools = [search_paper_content, search_all_papers]
react_agent = create_agent(llm, tools)

@paper_bp.route('/chat_with_chunk', methods=['POST'])
def chat_with_chunk():
    data = request.get_json()
    chunk_text = data.get('chunk_text')
    chunk_id = data.get('chunk_id')
    question = data.get('question')
    arxiv_id = data.get('arxiv_id')
    history_data = data.get('history', [])

    if not arxiv_id:
        return jsonify({"error": "Arxiv ID required"}), 400
    
    # We append the history across all chats
    chat_history = []
    for msg in history_data:
        content = msg.get('content', '')
        role = msg.get('role', 'user')
        chunk_tag = f"[Chunk {msg.get('chunkId', '?')}] " if 'chunkId' in msg else ""
        
        if role == 'user':
            chat_history.append(HumanMessage(content=f"{chunk_tag}{content}"))
        elif role == 'ai':
            chat_history.append(AIMessage(content=content))

    system_message = f"""
    You are an expert research assistant.
    The user is navigating a paper and has just clicked on a SPECIFIC SEGMENT to focus on.
    
    --- CURRENT CHUNK with ID: {chunk_id} and TEXT:
    {chunk_text}
    -------------------------------------------------------
    
    **CRITICAL PROTOCOLS:**
    1. **DIAGRAM/IMAGE HANDLING:** - If the Focus Segment starts with `[DIAGRAM]` or `[IMAGE ANALYSIS]`, this text is a transcription of the visual content. 
       - **Treat this description as absolute ground truth.**
       - **DO NOT** use tools to "find" the image or its caption. The description provided is sufficient. 
       - Just answer the user's question based on that text description.
       
    2. **SEARCH RULES:**
       - **Priority:** Check the 'ACTIVE SEGMENT' first. If the answer is there, just answer. 
       - **Tool Use:** Only use `search_paper_content` if the answer requires connecting ideas from *other* pages.
       - **Global Search:** Only use `search_all_papers` if the user explicitly asks about "other papers" or "external comparisons".
       
    
    3. **ARGUMENTS:**
       - For `search_paper_content`, always pass `arxiv_id="{arxiv_id}"`.
       - For `search_all_papers`, strictly pass the query string only.
    """

    try:
        response = react_agent.invoke({
            "messages": [
                ("system", system_message),
                *chat_history,
                ("human", question)
            ]},
            # Stop the model from spamming the tool
            config={"recursion_limit": 20}
        )
        final_answer = response["messages"][-1].content
    except Exception as e:
        print(e)
        final_answer = "Something went wrong"    
    return jsonify({"answer": final_answer})
    