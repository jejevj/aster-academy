"""Opaque references for URLs; database integer keys remain internal."""
from repositories.public_reference_repository import by_id, by_token

def ref_for(conn, kind, object_id):
    return by_id(conn,kind,object_id)

def resolve_ref(conn, kind, token):
    return by_token(conn,kind,token)
