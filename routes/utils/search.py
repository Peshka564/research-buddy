from services import metadata_vector_store, llm
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Optional

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
**Category Rules:**
- If the user mentions a specific ArXiv code (e.g., 'cs.LG'), use it.
- If the user mentions a broad field (e.g., 'math', 'cs', 'physics', 'stats'), treat it as a category code.
- Example: "math papers" -> category="math", query_content="mathematics"
- Example: "machine learning" -> category="cs", query_content="machine learning" (optional inference)
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

def smart_search(query_text: str, k_results: int):
    analysis = analyzer_chain.invoke({"input": query_text})
    print(f"Analysis Result: {analysis}")

    filters = []
    if analysis.year_start:
        filters.append({"year": {"$gte": str(analysis.year_start)}})
    if analysis.year_end:
        filters.append({"year": {"$lt": analysis.year_end}})
        
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
    relevant_papers = metadata_vector_store.similarity_search_with_score(
        search_query, 
        k=k_results * 4, 
        filter=chroma_filter
    )

    scored_papers = []

    for doc, score in relevant_papers:
        meta = doc.metadata
        
        # Filter by authors
        if analysis.author:
            stored_authors = doc.metadata.get("authors") or ""
            if analysis.author.lower() not in stored_authors.lower():
                continue
                
        # Filter by category
        if analysis.category:
            stored_cats = meta.get("Categories") or meta.get("categories") or ""
            if analysis.category.lower() not in stored_cats.lower():
                continue

        # If we passed all filters, add to results
        scored_papers.append({
            "id": meta.get("id"),
            "title": doc.page_content.split('\n')[0].replace("Title: ", ""),
            "abstract": meta.get("abstract", "No abstract available"),
            "authors": meta.get("authors"),
            "year": meta.get("year"),
            "similarity_score": float(score),
            "categories": meta.get("categories")
        })

        if len(scored_papers) >= k_results:
            break
            
    return scored_papers, analysis.model_dump(), hypothetical_abstract