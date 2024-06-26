from typing import Any, List

from beanie import Document, PydanticObjectId
from pydantic import BaseModel


class Database:
    def __init__(self, model: Document):
        self.model = model

    async def create(self, document: Document) -> Document:
        doc = await document.create()
        return doc

    async def get(self, id: PydanticObjectId) -> Document | bool:
        doc = await self.model.get(id)
        if doc:
            return doc
        else:
            return False

    async def get_all(self) -> List[Document]:
        docs = await self.model.find_all().to_list()
        return docs

    async def update(self, id: PydanticObjectId, body: BaseModel) -> Document:
        doc = await self.get(id)
        if not doc:
            return False

        des_body = body.model_dump()
        des_body = {key: value for key, value in des_body.items() if value is not None}

        update_query = {"$set": {field: value for field, value in des_body.items()}}

        await doc.update(update_query)
        return doc

    async def delete(self, id: PydanticObjectId) -> bool:
        doc = await self.get(id)
        if not doc:
            return False
        await doc.delete()
        return True
