import os

from fastapi import APIRouter

from cores.rag.query_engin import index_doc, query_with_datastore
from server.models.request import QueryRequest

router = APIRouter()


@router.post("/query")
def process_query(request: QueryRequest):
    print("User query:", request.user_query)
    ds = index_doc(["雁荡山瞎扯信息.txt"], region=os.environ["Region"])
    response = query_with_datastore(ds, request.user_query, region=os.environ["Region"])

    return {"response": response}