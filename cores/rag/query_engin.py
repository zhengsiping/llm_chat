import json
import os
import urllib.request

from haystack import Pipeline, Document
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.retrievers import InMemoryEmbeddingRetriever
from haystack.components.converters import TextFileToDocument
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.embedders import OpenAIDocumentEmbedder, OpenAITextEmbedder
from haystack.components.writers import DocumentWriter
from haystack.components.builders import PromptBuilder, ChatPromptBuilder
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage
from haystack.utils import Secret

from utils.constants import Region
from utils.utils import get_project_root


INDEX_FOLDER = f"{get_project_root()}/data/index"
os.makedirs(INDEX_FOLDER, exist_ok=True)


def index_doc(file_paths: list[str],
              region: str) -> InMemoryDocumentStore:
    # Check index file is in INDEX_FOLDER
    index = f"{INDEX_FOLDER}/indexed_docs.json"
    if os.path.exists(index):
        document_store = InMemoryDocumentStore.load_from_disk(index)
        print(f"read index from {index}")
        return document_store

    doc_folder = f"{get_project_root()}/data/docs"
    updated_file_paths = [f"{doc_folder}/{file_path}" for file_path in file_paths]

    document_store = InMemoryDocumentStore()

    text_file_converter = TextFileToDocument()
    cleaner = DocumentCleaner()
    splitter = DocumentSplitter()

    if region == Region.CHINA:
        embedder = OpenAIDocumentEmbedder(
            api_key=Secret.from_token(os.environ["DASHSCOPE_API_KEY"]),
            model="text-embedding-v1",
            api_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    else:
        embedder = OpenAIDocumentEmbedder()

    writer = DocumentWriter(document_store)

    indexing_pipeline = Pipeline()
    indexing_pipeline.add_component("converter", text_file_converter)
    indexing_pipeline.add_component("cleaner", cleaner)
    indexing_pipeline.add_component("splitter", splitter)
    indexing_pipeline.add_component("embedder", embedder)
    indexing_pipeline.add_component("writer", writer)

    indexing_pipeline.connect("converter.documents", "cleaner.documents")
    indexing_pipeline.connect("cleaner.documents", "splitter.documents")
    indexing_pipeline.connect("splitter.documents", "embedder.documents")
    indexing_pipeline.connect("embedder.documents", "writer.documents")
    indexing_pipeline.run(data={"sources": updated_file_paths})

    document_store.save_to_disk(index)

    return document_store


def query_with_datastore(document_store: InMemoryDocumentStore, query: str,
                         region: str) -> str:
    if region == Region.CHINA:
        text_embedder = OpenAITextEmbedder(
            api_key=Secret.from_token(os.environ["DASHSCOPE_API_KEY"]),
            model="text-embedding-v1",
            api_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    else:
        text_embedder = OpenAITextEmbedder()

    retriever = InMemoryEmbeddingRetriever(document_store)
    prompt_template = [
        ChatMessage.from_user(
          """
          根据以下文档 回答问题
          文档:
          {% for doc in documents %}
              {{ doc.content }}
          {% endfor %}
          问题: {{query}}
          答案:
          """
        ),
        ChatMessage.from_system('你是一个温州雁荡山的旅游向导，你将回答任何关于雁荡山的问题，默认用户的问题是关于雁荡山的.'
                                      '但如果用户的问题实在跟雁荡山没有关系，回复说不知道。 回答稍微简洁点'
                                      )
    ]
    prompt_builder = ChatPromptBuilder(template=prompt_template)
    if region == Region.CHINA:
        llm = OpenAIChatGenerator(
            api_key=Secret.from_token(os.environ["DASHSCOPE_API_KEY"]),
            model="deepseek-r1",
            api_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
    else:
        llm = OpenAIChatGenerator()

    rag_pipeline = Pipeline()
    rag_pipeline.add_component("text_embedder", text_embedder)
    rag_pipeline.add_component("retriever", retriever)
    rag_pipeline.add_component("prompt_builder", prompt_builder)
    rag_pipeline.add_component("llm", llm)

    rag_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
    rag_pipeline.connect("retriever.documents", "prompt_builder.documents")
    rag_pipeline.connect("prompt_builder", "llm")

    result = rag_pipeline.run(data={"prompt_builder": {"query":query}, "text_embedder": {"text": query}})

    print(result["llm"]["replies"][0].text)
    return result["llm"]["replies"][0].text
