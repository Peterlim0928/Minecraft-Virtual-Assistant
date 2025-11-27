import os
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import faiss


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)


def embed_texts(texts: list[str], model="text-embedding-ada-002"):
    """
    Generate embeddings for a list of texts using OpenAI's embedding model.

    Args:
        texts (list of str): The texts to embed.
        model (str): The embedding model to use.

    Returns:
        list of np.ndarray: The embeddings for the input texts.
    """
    response = client.embeddings.create(model=model, input=texts)
    embeddings = [np.array(data_point.embedding) for data_point in response.data]
    return embeddings


def create_faiss_index(embeddings: list[np.ndarray]):
    """
    Create a FAISS index from the given embeddings.

    Args:
        embeddings (list of np.ndarray): The embeddings to index.
        dimension (int): The dimensionality of the embeddings.

    Returns:
        faiss.Index: The FAISS index containing the embeddings.
    """
    dimension = embeddings[0].shape[0] if embeddings else 0
    index = faiss.IndexFlatL2(dimension)
    embedding_matrix = np.vstack(embeddings).astype("float32")
    index.add(embedding_matrix)
    return index
