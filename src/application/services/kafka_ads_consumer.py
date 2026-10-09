import logging
import typing

from aiokafka import AIOKafkaConsumer, ConsumerRecord

from src.application.ports.usecases import IndexAdPort, RemoveAdPort
from src.application.tracing import (
    KAFKA_TRACE_ID_HEADER,
    normalize_trace_id,
    trace_context,
)

logger = logging.getLogger(__name__)


def extract_trace_id(msg: ConsumerRecord) -> str | None:
    for key, value in msg.headers or ():
        if key == KAFKA_TRACE_ID_HEADER and value is not None:
            return normalize_trace_id(value.decode("utf-8", errors="replace"))
    return None


class KafkaAdsConsumer:
    def __init__(
        self,
        consumer: AIOKafkaConsumer,
        index_ad: IndexAdPort,
        remove_ad: RemoveAdPort,
    ) -> None:
        self._consumer = consumer
        self._index_ad = index_ad
        self._remove_ad = remove_ad

    async def run(self) -> None:
        async for msg in self._consumer:
            # The whole loop runs in one task, so the id must be set and reset
            # per message; otherwise it would leak into the next one.
            with trace_context(extract_trace_id(msg)):
                try:
                    await self._handle(msg.value)
                except Exception:
                    logger.exception("failed to handle message %s", msg)
                    continue
                await self._consumer.commit()

    async def _handle(self, value: dict[str, typing.Any]) -> None:
        event = value.get("event")
        payload = value.get("payload") or {}
        ad_id = payload.get("ad_id")
        if not isinstance(ad_id, int):
            logger.warning("skip message without ad_id: %s", value)
            return

        logger.info("received %s ad_id=%s", event, ad_id)
        if event in ("ad.created", "ad.updated"):
            await self._index_ad.execute(ad_id)
        elif event == "ad.deleted":
            await self._remove_ad.execute(ad_id)
        else:
            logger.warning("unknown event type: %s", event)
