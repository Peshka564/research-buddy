from flask import Blueprint, request, jsonify
from services import metadata_vector_store, llm
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from routes.utils.search import smart_search
from typing import Optional

search_bp = Blueprint('search', __name__)


@search_bp.route('/search', methods=['GET'])
def search_papers():
    """ Top K Document Retrieval"""
    
    # { "query": string, "k": int }
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({"message": "Missing 'query' field in payload"}), 400
    
    query_text = data['query']
    k_results = data.get('k', 5)
    
    try:
        results = metadata_vector_store.similarity_search_with_score(query_text, k=k_results)
        
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

@search_bp.route('/smart_search', methods=['GET'])
def smart_search_route():
    """ Top K Document Retrieval but smarter"""
    
    query_input = request.args.get('query')
    k_input = request.args.get('k')

    if not query_input or not k_input:
        return jsonify({"message": "Missing 'query' field in payload"}), 400
    
    query_text = query_input
    k_results = int(k_input)

    try:
        relevant_papers, interpreted_query, _ = smart_search(query_text, k_results)
        return jsonify({
            "original_query": query_text,
            "interpreted_intent": interpreted_query,
            "results": relevant_papers
        })

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500