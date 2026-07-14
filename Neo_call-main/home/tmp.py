import torch
from PIL import Image
import os
import fitz  # PyMuPDF
import faiss
import pickle
import numpy as np
import pytesseract


# Hugging Face and model imports
from transformers.utils.import_utils import is_flash_attn_2_available
from colpali_engine.models import ColQwen2, ColQwen2Processor
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from sentence_transformers import SentenceTransformer

text_embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Convert PDF to Imagescd ls
def pdf_to_images(pdf_path, dpi=96):# dpi=150):
    images = []
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat,alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images


def page_has_visual(image):
    """Heuristic to detect diagrams or mixed content."""
    gray = np.array(image.convert("L"))
    h, w = gray.shape

    # Get OCR boxes
    ocr_data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
    n_boxes = len(ocr_data['level'])

    # Calculate total text area
    total_text_area = 0
    for i in range(n_boxes):
        (x, y, bw, bh) = (ocr_data['left'][i], ocr_data['top'][i],
                          ocr_data['width'][i], ocr_data['height'][i])
        total_text_area += bw * bh

    page_area = h * w
    text_ratio = total_text_area / page_area

    # If OCR text covers less than 30% of the page ? assume visual
    return text_ratio < 0.3

#FAISS Indexing Functions
def save_to_faiss(embeddings, images, db_dir="faiss_db"):
    # save embedding to db
    os.makedirs(db_dir, exist_ok=True)
    # embeddings shape: (batch_size, dim)
    print(f"Embeddings shape before saving: {embeddings.shape}")
    if embeddings.dim() != 2:
        raise ValueError(f"Expected 2D embeddings for FAISS, got shape: {embeddings.shape}")
    # embeddings = embeddings.mean(dim=1)  # shape: (num_embeddings, dim)
    embeddings_np = embeddings.cpu().to(torch.float32).numpy()
    print(f"Embeddings shape after saving: {embeddings.shape}")
    dim = embeddings_np.shape[1]
    index = faiss.IndexFlatL2(dim)
    print("----index----",index)
    index.add(embeddings_np)

    # Use IVF index for better scalability and fast retirive
    # nlist = min(100, len(embeddings_np))
    # quantizer = faiss.IndexFlatL2(dim)
    # index = faiss.IndexIVFFlat(quantizer, dim, nlist, faiss.METRIC_L2)
    # index.train(embeddings_np)
    # index.add(embeddings_np)

    # Save FAISS index
    faiss.write_index(index, os.path.join(db_dir, "index.bin"))

    # Save metadata and images
    metadata = {
        "image_paths": [f"page_{i}.png" for i in range(len(images))]
    }

    with open(os.path.join(db_dir, "metadata.pkl"), "wb") as f:
        pickle.dump(metadata, f)

    # Save images
    img_dir = os.path.join(db_dir, "images")
    os.makedirs(img_dir, exist_ok=True)
    for i, img in enumerate(images):
        img.save(os.path.join(img_dir, f"page_{i}.png"))

    print(f"Saved {len(images)} pages to FAISS DB at '{db_dir}'")


def load_from_faiss(rag, db_dir="faiss_db"):
    """Load FAISS index and corresponding images into the RAG object."""
    index_path = os.path.join(db_dir, "index.bin")
    meta_path = os.path.join(db_dir, "metadata.pkl")
    img_dir = os.path.join(db_dir, "images")

    if not os.path.exists(index_path) or not os.path.exists(meta_path):
        raise FileNotFoundError(f"FAISS DB not found in '{db_dir}'")

    # Load FAISS index
    index = faiss.read_index(index_path)
    embeddings_np = index.xb
    rag.indexed_embeddings = torch.tensor(embeddings_np).to(rag.retriever_model.device)

    # Load metadata
    with open(meta_path, "rb") as f:
        metadata = pickle.load(f)

    # Load images
    rag.indexed_images = [
        Image.open(os.path.join(img_dir, img_file)) for img_file in metadata["image_paths"]
    ]

    print(f"Loaded {len(rag.indexed_images)} pages from FAISS DB")


# Updated VisualRAG Class
class VisualRAG:
    def __init__(self, retriever_model, retriever_processor, vl_model, vl_processor):
        self.retriever_model = retriever_model
        self.retriever_processor = retriever_processor
        self.vl_model = vl_model
        self.vl_processor = vl_processor
        self.indexed_embeddings = None
        self.indexed_images = []

    def index_documents(self, input_path):
        """Index documents from a folder of images or a PDF file"""
        self.indexed_images = []
        db_dir = "./faiss_db"

        if os.path.isdir(input_path):
            supported_exts = ('.png', '.jpg', '.jpeg')
            self.indexed_images = [Image.open(os.path.join(input_path, f)).convert("RGB")
                      for f in os.listdir(input_path) if f.lower().endswith(supported_exts)]
            # self.indexed_images = images
        elif os.path.isfile(input_path) and input_path.lower().endswith('.pdf'):
            print(f"Converting PDF '{input_path}' to images...")
            self.indexed_images = pdf_to_images(input_path)
            # self.indexed_images = images
        else:
            raise ValueError("Input must be a directory of images or a PDF file.")

        batch_size = 8
        all_embeddings = []

        for i in range(0, len(self.indexed_images), batch_size):
            if page_has_visual(self.indexed_images[i]):
                # Use VLM (Colpali)
                batch_images = self.indexed_images[i:i + batch_size]
                processed_images = self.retriever_processor.process_images(batch_images).to(self.retriever_model.device)

                with torch.no_grad():
                    outputs = self.retriever_model(**processed_images)

                # ensure all output in correct shape(batch_size,seq_len,dim)
                if isinstance(outputs,tuple):
                    embeddings = outputs[0]
                else:
                    embeddings = outputs
                print(f"raw embeddings shape: {embeddings.shape}")

                # make sure embeddings have 3D tensor
                if embeddings.dim() != 3:
                    raise ValueError(f"except 3d embeddings but got shape: {embeddings.shape}")
                # pool over the sequence demension
                embeddings = embeddings.mean(dim=1)
                print("Mixed/Visual page ? Colpali VLM embedding")
            else:
                # Use fast text embedding
                ocr_text = pytesseract.image_to_string(self.indexed_images[i])
                text_embedding_np = text_embedder.encode(ocr_text, convert_to_numpy=True)
                embeddings = torch.tensor(text_embedding_np).unsqueeze(0)
                print("Text-only page ? SentenceTransformer embedding")

            all_embeddings.append(embeddings)


        # Combine embeddings
        if len(all_embeddings) > 1:
            self.indexed_embeddings = torch.cat(all_embeddings, dim=0)
        else:
            self.indexed_embeddings = all_embeddings[0]
        save_to_faiss(self.indexed_embeddings,self.indexed_images,db_dir)
        return len(self.indexed_images)

    def retrieve(self, query, k=1):
        db_dir = "./faiss_db"
        """Retrieve top-k similar document pages based on FAISS search."""
        if self.indexed_embeddings is None:
            raise ValueError("No documents have been indexed yet")

        # Process query
        processed_query = self.retriever_processor.process_queries([query]).to(self.retriever_model.device)

        with torch.no_grad():
            query_embeddings = self.retriever_model(**processed_query)
        if query_embeddings.dim() == 3:
            query_embeddings = query_embeddings.mean(dim=1)

        # convert numpy to float32
        embeddings_np = query_embeddings.float().cpu().numpy()
        # embeddings_np = self.indexed_embeddings.cpu().numpy()
        print(f'query embeddings shape before Faiss: {embeddings_np.shape}')

        # ensure query is 2d like (1,dim)
        if embeddings_np.ndim == 1:
            embeddings_np = embeddings_np.reshape(1,-1) #reshape from (dim,) to (1,dim)

        # query_np = embeddings_np.float().cpu().numpy()
        # embeddings_np = self.indexed_embeddings.float().cpu().numpy()

        # Build FAISS index for retrieval
        #index = faiss.IndexFlatL2(embeddings_np.shape[1])
        #index.add(embeddings_np)
        index = faiss.read_index(os.path.join(db_dir,'index.bin'))
        D, I = index.search(embeddings_np, k)

        results = []
        for i in range(k):
            idx = I[0][i]
            score = float(D[0][i])
            results.append({
                "page_image": self.indexed_images[idx],
                "score": score
            })

        return results

    def answer_query(self, query, k=1):
        """Retrieve and generate an answer."""
        retrieved_results = self.retrieve(query, k=k)

        # Prepare messages
        messages = [{
            "role": "user",
            "content": [{"type": "text", "text": f"I have a question about some documents: {query}"}]
        }]

        for result in retrieved_results:
            messages[0]["content"].append({"type": "image", "image": result["page_image"]})

        messages[0]["content"].append({
            "type": "text",
            "text": "Based on the document images provided, please answer my question in detail."
        })

        # Tokenize and generate
        text = self.vl_processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self.vl_processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt"
        ).to(self.vl_model.device)

        generated_ids = self.vl_model.generate(**inputs, max_new_tokens=512)
        generated_ids_trimmed = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
        output_text = self.vl_processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]

        return {
            "answer": output_text,
            "retrieved_documents": retrieved_results
        }


#Main Function
def main():
    # Load models
    print("Loading ColQwen2 for embedding extraction...")
    # retriever_model = ColQwen2.from_pretrained(
    #     "vidore/colqwen2-v1.0",
    #     torch_dtype=torch.bfloat16,
    #     device_map="cpu",
    #     attn_implementation="flash_attention_2" if is_flash_attn_2_available() else None,
    # ).eval()
    retriever_model = ColQwen2.from_pretrained(
        "vidore/colqwen2-v1.0",
        torch_dtype=torch.float32,
        device_map="cpu",
        attn_implementation="flash_attention_2" if is_flash_attn_2_available() else None,
    ).eval()
    retriever_processor = ColQwen2Processor.from_pretrained("vidore/colqwen2-v1.0")

    print("Loading Qwen2.5-VL for answering...")
    vl_model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        "Qwen/Qwen2.5-VL-3B-Instruct",
        torch_dtype=torch.bfloat16,
        device_map="auto",
        attn_implementation="flash_attention_2" if is_flash_attn_2_available() else None,
    )
    vl_processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-3B-Instruct")

    # Create RAG instance
    visual_rag = VisualRAG(retriever_model, retriever_processor, vl_model, vl_processor)

    # Set path to PDF or image folder
    input_path = "/user/ashish_kumar/Downloads/diagram.pdf"
    db_dir = "./faiss_db"

    # Option A: Index and save to FAISS
    print("Indexing document...")
    visual_rag.index_documents(input_path)
    save_to_faiss(visual_rag.indexed_embeddings, visual_rag.indexed_images, db_dir=db_dir)

    # Option B: Or load from FAISS later
    # load_from_faiss(visual_rag, db_dir=db_dir)

    # Query
    query = "Explain the diagram from pdf?"
    result = visual_rag.answer_query(query, k=1)

    print("\nAnswer:", result["answer"])
    print("\nRetrieved Documents:")
    for i, doc in enumerate(result["retrieved_documents"]):
        print(f"Page {i+1} - Score: {doc['score']:.4f}")
        doc["page_image"].save(f"retrieved_page_{i+1}.png")

if __name__ == "__main__":
    main()
