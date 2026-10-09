import logging

from src.application.ports.ad_source import AdSource
from src.application.ports.uow import UnitOfWork
from src.application.ports.usecases import IndexAdPort

logger = logging.getLogger(__name__)


class IndexAd(IndexAdPort):
    def __init__(self, uow: UnitOfWork, ad_source: AdSource) -> None:
        self._uow = uow
        self._ad_source = ad_source

    async def execute(self, ad_id: int) -> None:
        # Fetch before opening the UoW so the DB session isn't held during HTTP.
        snapshot = await self._ad_source.get(ad_id)
        async with self._uow:
            if snapshot is None or snapshot.status != "active":
                await self._uow.search.delete(ad_id)
                logger.info("ad %s is not active, removed from index", ad_id)
            else:
                await self._uow.search.upsert(
                    ad_id=snapshot.ad_id,
                    title=snapshot.title,
                    description=snapshot.description,
                    price=snapshot.price,
                    category=snapshot.category,
                    city=snapshot.city,
                )
                logger.info("ad %s indexed", ad_id)
            await self._uow.commit()
