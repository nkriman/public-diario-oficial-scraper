from .db_connection import CompanyRecord
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from utils.helpers import retry_on_request


@retry_on_request
def upload_to_db(engine, dict_entities, batch_id):
    try:
        with Session(engine) as session:
            record = CompanyRecord(json_payload=dict_entities, batch_id=batch_id)
            session.add(record)
            session.commit()
    except OperationalError:
        print(f"Failed to upload batch_id {batch_id} to the database.")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise
