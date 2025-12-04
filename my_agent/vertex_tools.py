import os
from typing import List
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core.client_options import ClientOptions

def search_knowledge_base(query: str) -> dict:
    """Searches the knowledge base (Vertex AI Search) for relevant information.
    
    Args:
        query (str): The search query.
        
    Returns:
        dict: status and result (search results) or error msg.
    """
    project_id = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION") or "europe-west4"
    data_store_id = os.getenv("VERTEX_SEARCH_DATA_STORE_ID")
    
    if not project_id or not data_store_id:
        return {
            "status": "error",
            "error_message": "GCP_PROJECT_ID or VERTEX_SEARCH_DATA_STORE_ID not configured."
        }

    try:
        client_options = (
            ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
            if location != "global"
            else None
        )
        
        client = discoveryengine.SearchServiceClient(client_options=client_options)
        
        serving_config = client.serving_config_path(
            project=project_id,
            location=location,
            data_store=data_store_id,
            serving_config="default_config",
        )
        
        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=3,
        )
        
        response = client.search(request)
        
        results = []
        for result in response.results:
            data = result.document.derived_struct_data
            # Extract relevant fields, this depends on the data schema
            # Common fields for unstructured data:
            title = data.get("title", "No Title")
            snippets = data.get("snippets") or data.get("extractive_answers") or []
            snippet = ""
            if isinstance(snippets, list) and snippets:
                first = snippets[0]
                if isinstance(first, dict):
                    snippet = first.get("snippet") or first.get("content", "")
                else:
                    snippet = str(first)
            link = data.get("link", "")
            results.append(f"Title: {title}\nSnippet: {snippet}\nLink: {link}")
            
        return {
            "status": "success",
            "report": "\n\n".join(results) if results else "No results found."
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Search failed: {str(e)}"
        }
