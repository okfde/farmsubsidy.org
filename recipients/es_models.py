from django.conf import settings
from elasticsearch_dsl import (
    Document, Date, Nested, Double,
    analyzer, InnerDoc, Keyword, Text,
    Index
)
from elasticsearch_dsl import connections


connections.create_connection(hosts=[settings.ES_URL], timeout=20)

eufs_analyzer = analyzer(
    'eufs_analyzer',
    tokenizer="standard",
    filter=["standard", "asciifolding", "lowercase"],
)

farmsubsidy_recipients = Index('farmsubsidy_recipients')
farmsubsidy_recipients.settings(
    number_of_shards=1,
    number_of_replicas=0
)


class Payment(InnerDoc):
    year = Date()
    amount = Double()
    scheme = Text(analyzer=eufs_analyzer)
    country = Keyword()

    amount_original = Double()
    currency_original = Keyword()


@farmsubsidy_recipients.document
class Recipient(Document):
    country = Keyword()
    slug = Keyword()
    name = Text(fields={'raw': Keyword()}, analyzer=eufs_analyzer)

    address = Text(analyzer=eufs_analyzer)
    postcode = Text(analyzer=eufs_analyzer)
    location = Text(analyzer=eufs_analyzer)
    recipient_country = Keyword()
    total_amount = Double()

    payments = Nested(Payment)

    class Index:
        name = 'farmsubsidy_recipients'


farmsubsidy_recipients.analyzer(eufs_analyzer)


def _destroy_index():
    farmsubsidy_recipients.delete()


def init_es():
    if not farmsubsidy_recipients.exists():
        farmsubsidy_recipients.create()

    Recipient.init()
