import numpy as np
import requests
import fitz
import base64

from langchain_core.messages import HumanMessage
from sklearn.metrics.pairwise import cosine_distances
from services import vlm

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def get_image_description(base64_image, prompt: str):
    try:
        message = HumanMessage(
            content=[
                {
                    "type": "text", 
                    "text": prompt
                },
                {
                    "type": "image_url", 
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                }
            ]
        )
        
        response = vlm.invoke([message])
        return response.content
    except Exception as e:
        print(f"Vision Error: {e}")
        return ""

def extract_text(chunks: list, text_content: list, page, page_num):
    # Paragraphs with their bounding box
    text_blocks = page.get_text("blocks") 
    
    for b in text_blocks:
        x0, y0, x1, y1, text, _, block_type = b
        
        # Filter out noise (images, tiny headers)
        if block_type != 0 or len(text) < 50: 
            continue
        
        clean_text = text.replace("\n", " ").strip()
        
        chunks.append({
            "page": page_num + 1,        # 1-based index for React-PDF
            "bbox": [x0, y0, x1, y1],    # PDF Point Coordinates
            "text": clean_text,
            "type": "text"
        })
        text_content.append(clean_text)

def extract_images(chunks: list, text_content: list, page, page_num, doc):
    image_list = page.get_images(full=True)
    
    for _, img in enumerate(image_list):
        xref = img[0]

        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        
        # Skip tiny icons/lines
        if len(image_bytes) < 2000: continue 
        
        b64_img = encode_image(image_bytes)
        
        description = get_image_description(b64_img, prompt='Analyze this image from a scientific paper and describe it.')
        
        if not description or len(description) < 10: continue

        # Get bounding box of the image
        rects = page.get_image_rects(xref)
        if not rects: continue
        rect = rects[0]

        chunk_text = f"[IMAGE ANALYSIS] {description}"
        
        chunks.append({
            "page": page_num + 1,
            "bbox": [rect.x0, rect.y0, rect.x1, rect.y1],
            "text": chunk_text,
            "type": "image"
        })
        text_content.append(chunk_text)

def merge_close_rects(rects, threshold=50):
    """ Iteratively merge intersecting rectangles """
    if not rects:
        return []

    merged = True
    while merged:
        merged = False
        new_rects = []
        
        while rects:
            current = rects.pop(0)
            was_merged = False
            
            for i, existing in enumerate(new_rects):
                # Make the rectangle a little bit bigger
                expanded = fitz.Rect(
                    existing.x0 - threshold, existing.y0 - threshold,
                    existing.x1 + threshold, existing.y1 + threshold
                )
                
                # Merge
                if expanded.intersects(current):
                    new_rects[i] = existing | current 
                    was_merged = True
                    merged = True
                    break
            
            if not was_merged:
                new_rects.append(current)
                
        rects = new_rects
        
    return rects

def extract_diagrams(chunks: list, text_content: list, page, page_num):
    paths = page.get_drawings()
    path_rects = []
    page_area = page.rect.get_area()
    
    for p in paths:
        r = p["rect"]
        # Filter noise
        if r.width < 5 or r.height < 5: continue 
        if (r.width * r.height) > (page_area * 0.9): continue
        path_rects.append(r)
        
    diagram_regions = merge_close_rects(path_rects)
    
    for _, rect in enumerate(diagram_regions):
        # Ignore tiny diagrams
        if rect.width < 100 or rect.height < 100:
            continue
            
        # Render the region
        # Zoom=2 for better OCR
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=rect)
        img_bytes = pix.tobytes("png")
        
        b64_img = encode_image(img_bytes)
        description = get_image_description(
            b64_img, 
            prompt='You are a data compressor. Analyze this scientific diagram/chart. Output max 20 words about the diagram.'
                # 'Analyze this diagram. 1. Title? 2. What are the axes/labels? 3. Summarize the data trend or system flow.'
        )
        chunk_text = f"[DIAGRAM] {description}"
        
        chunks.append({
            "page": page_num + 1,
            "bbox": [rect.x0, rect.y0, rect.x1, rect.y1],
            "text": chunk_text,
            "type": "diagram",
        })
        text_content.append(chunk_text)

def get_chunks_with_coords(temp_filename: str, pdf_url: str):
    response = requests.get(pdf_url)
    with open(temp_filename, "wb") as f:
        f.write(response.content)

    # Get paragraphs with bounding boxes
    doc = fitz.open(temp_filename)
    chunks_with_coords = []
    all_text_content = []
    
    for page_num, page in enumerate(doc):
        extract_text(chunks_with_coords, all_text_content, page, page_num)
        extract_images(chunks_with_coords, all_text_content, page, page_num, doc)
        extract_diagrams(chunks_with_coords, all_text_content, page, page_num)

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