import numpy as np
import requests
import fitz

from sklearn.metrics.pairwise import cosine_distances

def get_chunks_with_coords(temp_filename: str, pdf_url: str):
    response = requests.get(pdf_url)
    with open(temp_filename, "wb") as f:
        f.write(response.content)

    # Get paragraphs with bounding boxes
    doc = fitz.open(temp_filename)
    chunks_with_coords = []
    all_text_content = []
    
    for page_num, page in enumerate(doc):
        # 'blocks' gives us paragraphs with their bounding box
        blocks = page.get_text("blocks") 
        
        for b in blocks:
            x0, y0, x1, y1, text, _, block_type = b
            
            # Filter out noise (images, tiny headers)
            if block_type != 0 or len(text) < 50: 
                continue
            
            clean_text = text.replace("\n", " ").strip()
            
            chunks_with_coords.append({
                "page": page_num + 1,        # 1-based index for React-PDF
                "bbox": [x0, y0, x1, y1],    # PDF Point Coordinates
                "text": clean_text
            })
            all_text_content.append(clean_text)

    # We close because a second query for this paper will break everything
    doc.close()

    return chunks_with_coords, all_text_content



def semantically_chunk(vectors: list[list[float]]) -> list[int]:
    distances = []
    for i in range(len(vectors) - 1):
        # 0.0 = Identical, 1.0 = Opposite
        dist = cosine_distances([vectors[i]], [vectors[i+1]])[0][0]
        distances.append(dist)

    # Calculate Dynamic Threshold
    # If the paper flows very smoothly, the threshold is low.
    # If the paper jumps topics rapidly, the threshold is high.
    if distances:
        avg_dist = np.mean(distances)
        std_dist = np.std(distances)
        threshold = avg_dist + (0.5 * std_dist) 
    else:
        threshold = 0.5

    labels = [0] * len(vectors)
    current_cluster_id = 0
    
    for i in range(len(distances)):
        # If the next chunk is too different from the current one, start new cluster
        if distances[i] > threshold:
            current_cluster_id += 1
        
        labels[i+1] = current_cluster_id
    
    return labels